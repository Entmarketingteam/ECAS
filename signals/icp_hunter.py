"""
signals/icp_hunter.py — Find ICP companies via Apollo org search.

ICP: Mid-tier EPC contractors ($20M-$300M revenue) in power/grid/defense sectors.
     Located in target states. Titles: VP Ops, CEO, President, Director BD, etc.

This module answers: "We know Power & Grid is heating up — WHO are the specific
EPCs we should be calling right now?"

Flow:
  1. Pull current sector heat scores
  2. For each sector above threshold, search Apollo for matching organizations
  3. Score each company (ICP fit + sector heat)
  4. Upsert into Airtable projects with budget window estimates
  5. Log summary
"""

import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import APOLLO_API_KEY, ICP, TARGET_SECTORS

logger = logging.getLogger(__name__)

APOLLO_ORG_SEARCH_URL = "https://api.apollo.io/v1/mixed_companies/search"

# Minimum sector heat score to trigger ICP search for that sector
MIN_SECTOR_HEAT_TO_HUNT = 40.0

# How many companies to pull per sector per run
COMPANIES_PER_SECTOR = 25

# Sector → Apollo industry/keyword tags mapping
SECTOR_KEYWORDS = {
    "Power & Grid Infrastructure": [
        "electrical contractor",
        "epc contractor",
        "power line contractor",
        "substation contractor",
        "transmission contractor",
        "distribution contractor",
        "grid contractor",
        "utility contractor",
        "renewable contractor",
        "electrical construction",
        "power systems",
    ],
    "Defense": [
        "defense contractor",
        "military contractor",
        "government contractor",
        "federal systems integrator",
        "defense systems",
        "aerospace defense",
        "national security",
    ],
    "Uranium & Minerals": [
        "uranium mining",
        "mineral extraction",
        "nuclear fuel",
        "rare earth minerals",
        "critical minerals",
    ],
}

# Employee count ranges as revenue proxy
# $20M-$300M EPC ~ 50-2000 employees
EMPLOYEE_RANGE = ["50,2000"]


def compute_budget_window(phase: str) -> tuple[str, str]:
    """
    Return (start_date, end_date) for expected budget deployment window
    based on sector phase. Dates are YYYY-MM-DD strings.
    """
    today = datetime.utcnow().date()
    phase_offsets = {
        "active_spend":      (0,   30),    # NOW — window open, deploy immediately
        "imminent_unlock":   (30,  90),    # 1-3 months out
        "confirmed_signal":  (90,  180),   # 3-6 months out
        "early_signal":      (180, 270),   # 6-9 months out
    }
    start_days, end_days = phase_offsets.get(phase, (90, 180))
    start = (today + timedelta(days=start_days)).isoformat()
    end = (today + timedelta(days=end_days)).isoformat()
    return start, end


def _icp_fit_score(org: dict) -> str:
    """
    Rate ICP fit as high/medium/low based on available org metadata.
    Checks employee count, keywords, industry match.
    """
    employees = org.get("estimated_num_employees") or 0
    keywords = " ".join([
        org.get("short_description", ""),
        " ".join(org.get("keywords", [])),
        org.get("primary_industry", ""),
    ]).lower()

    icp_keywords = ICP["keywords"]
    keyword_matches = sum(1 for kw in icp_keywords if kw.lower() in keywords)

    in_target_state = org.get("state", "").upper() in ICP.get("states", [])

    score = 0
    if 100 <= employees <= 1500:
        score += 2
    elif 50 <= employees <= 2000:
        score += 1

    score += min(keyword_matches, 3)

    if in_target_state:
        score += 1

    if score >= 5:
        return "high"
    elif score >= 3:
        return "medium"
    return "low"


def search_icp_companies(sector: str, heat_score: float, phase: str) -> list[dict]:
    """
    Search Apollo for EPC companies matching ICP criteria for a given sector.
    Returns list of dicts ready for Airtable upsert.
    """
    if not APOLLO_API_KEY:
        logger.warning("[ICP Hunter] APOLLO_API_KEY not set — skipping search")
        return []

    keywords = SECTOR_KEYWORDS.get(sector, [])
    if not keywords:
        logger.warning(f"[ICP Hunter] No keyword mapping for sector: {sector}")
        return []

    budget_start, budget_end = compute_budget_window(phase)

    try:
        resp = requests.post(
            APOLLO_ORG_SEARCH_URL,
            headers={
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
                "X-Api-Key": APOLLO_API_KEY,
            },
            json={
                "q_organization_keyword_tags": keywords[:5],  # Apollo caps at 5
                "organization_num_employees_ranges": EMPLOYEE_RANGE,
                "organization_locations": ICP.get("states", []),
                "currently_using_any_of_technology_uids": [],
                "page": 1,
                "per_page": COMPANIES_PER_SECTOR,
            },
            timeout=30,
        )

        if resp.status_code == 401:
            logger.error("[ICP Hunter] Apollo 401 — check APOLLO_API_KEY")
            return []
        if resp.status_code == 422:
            logger.warning(f"[ICP Hunter] Apollo 422 for {sector} — relaxing filters")
            # Retry with fewer filters
            resp = requests.post(
                APOLLO_ORG_SEARCH_URL,
                headers={
                    "Content-Type": "application/json",
                    "Cache-Control": "no-cache",
                    "X-Api-Key": APOLLO_API_KEY,
                },
                json={
                    "q_organization_keyword_tags": keywords[:3],
                    "organization_num_employees_ranges": EMPLOYEE_RANGE,
                    "page": 1,
                    "per_page": COMPANIES_PER_SECTOR,
                },
                timeout=30,
            )

        resp.raise_for_status()
        data = resp.json()

        companies = []
        for org in data.get("organizations", []):
            name = org.get("name", "").strip()
            if not name:
                continue

            icp_fit = _icp_fit_score(org)

            # Derive priority from heat score + ICP fit
            if heat_score >= 65 or icp_fit == "high":
                priority = "high"
            elif heat_score >= 45 or icp_fit == "medium":
                priority = "medium"
            else:
                priority = "low"

            companies.append({
                "company_name": name,
                "website": org.get("website_url", ""),
                "linkedin_url": org.get("linkedin_url", ""),
                "employee_count": org.get("estimated_num_employees", 0),
                "city": org.get("city", ""),
                "state": org.get("state", ""),
                "industry": org.get("primary_industry", ""),
                "description": org.get("short_description", "")[:500],
                "sector": sector,
                "heat_score": heat_score,
                "phase": phase,
                "icp_fit": icp_fit,
                "priority": priority,
                "est_budget_unlock_start": budget_start,
                "est_budget_unlock_end": budget_end,
            })

        logger.info(f"[ICP Hunter] {sector}: found {len(companies)} companies from Apollo")
        return companies

    except requests.RequestException as e:
        logger.error(f"[ICP Hunter] Apollo request failed for {sector}: {e}")
        return []


def run_icp_hunt(sector_scores: list[dict] = None) -> dict:
    """
    Main entry point. Pull sector scores, search Apollo per sector,
    upsert into Airtable projects.

    Returns summary dict.
    """
    from storage.airtable import get_client

    if sector_scores is None:
        # Pull fresh scores
        from intelligence.sector_scoring import run_analysis
        sector_scores = run_analysis()

    at = get_client()
    total_found = 0
    total_upserted = 0
    sectors_hunted = []

    for sector_data in sector_scores:
        sector = sector_data.get("sector", "")
        heat_score = sector_data.get("heat_score", 0.0)
        phase = sector_data.get("phase", "early_signal")

        if heat_score < MIN_SECTOR_HEAT_TO_HUNT:
            logger.info(f"[ICP Hunter] {sector}: heat {heat_score} < {MIN_SECTOR_HEAT_TO_HUNT} — skipping")
            continue

        logger.info(f"[ICP Hunter] Hunting {sector} (heat={heat_score}, phase={phase})")
        companies = search_icp_companies(sector, heat_score, phase)
        total_found += len(companies)

        upserted = 0
        for company in companies:
            record_id = at.upsert_project(
                company_name=company["company_name"],
                sector=company["sector"],
                phase=company["phase"],
                heat_score=company["heat_score"],
                icp_fit=company["icp_fit"],
                priority=company["priority"],
                est_budget_unlock_start=company["est_budget_unlock_start"],
                est_budget_unlock_end=company["est_budget_unlock_end"],
                website=company.get("website", ""),
                state=company.get("state", ""),
                employee_count=company.get("employee_count", 0),
                description=company.get("description", ""),
            )
            if record_id:
                upserted += 1

        total_upserted += upserted
        sectors_hunted.append({
            "sector": sector,
            "heat_score": heat_score,
            "companies_found": len(companies),
            "companies_upserted": upserted,
        })
        logger.info(f"[ICP Hunter] {sector}: {upserted}/{len(companies)} upserted to Airtable")

    logger.info(
        f"[ICP Hunter] Hunt complete: {total_found} companies found, "
        f"{total_upserted} upserted across {len(sectors_hunted)} sectors"
    )
    return {
        "sectors_hunted": sectors_hunted,
        "total_companies_found": total_found,
        "total_upserted": total_upserted,
    }


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    import json
    result = run_icp_hunt()
    print(json.dumps(result, indent=2))
