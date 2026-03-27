"""
signals/usaspending_hunter.py — Find ICP companies via USASpending.gov API.

USASpending is the complete federal contract database — every award over $25K
to every company by DoD, DoE, Army Corps, etc. Free, no API key required.

Why this beats LinkedIn + Apollo for defense/energy ICP discovery:
  - Dollar amounts = revenue proxy ($40M in federal contracts = ~$80-150M total revenue)
  - Contract type reveals specialization (construction, O&M, design-build)
  - Award history shows which agencies they work with (DoD vs DOE vs Army Corps)
  - CAGE code links directly to SHIELD IDIQ awardees we already have
  - Confirms they're actively winning contracts RIGHT NOW (not just registered in SAM)

Flow:
  1. Search USASpending by NAICS code + award type (contracts only) + date range
  2. Filter to target states
  3. Group by recipient → sum total obligated value (revenue proxy)
  4. Filter to ICP revenue range ($20M-$300M proxy)
  5. Upsert into Airtable projects with contract history as signal context
  6. Push summary signal to signals_raw for sector scoring

Usage:
    python3 signals/usaspending_hunter.py --dry-run
    python3 signals/usaspending_hunter.py --sector defense --limit 100
    python3 signals/usaspending_hunter.py              # all sectors, full run
"""

import argparse
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLES,
    API_CONFIG, ICP, TARGET_SECTORS
)

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

USASPENDING_BASE = API_CONFIG["usaspending_base_url"]

# NAICS codes we care about — EPC contractor specializations
EPC_NAICS = {
    "237130": "Power and Communication Line Construction",
    "238210": "Electrical Contractors",
    "237110": "Water and Sewer Line Construction",
    "236220": "Commercial/Institutional Building Construction",
    "237990": "Other Heavy Civil Engineering",
    "238990": "Other Specialty Trade Contractors",
    "541330": "Engineering Services",
    "237120": "Oil and Gas Pipeline Construction",
    "238220": "Plumbing, Heating, A/C Contractors",
}

# Defense-specific NAICS
DEFENSE_NAICS = {
    "236220": "Military Construction",
    "237990": "Other Heavy and Civil Engineering (MILCON)",
    "238110": "Poured Concrete Foundation",
    "238210": "Electrical (DoD facilities)",
    "541330": "Engineering Services (defense)",
    "541620": "Environmental Consulting",
    "562910": "Remediation Services (DoD sites)",
}

# Award types: A=BPA, B=Purchase Order, C=Delivery Order, D=Definitive Contract
CONTRACT_AWARD_TYPES = ["A", "B", "C", "D"]

# Agencies we care about
TARGET_AGENCIES = {
    "097":  "Department of Defense",
    "089":  "Department of Energy",
    "096":  "Department of Army (Army Corps of Engineers)",
    "017":  "Department of Navy",
    "057":  "Department of Air Force",
}

TARGET_STATES = ICP["states"] + ["OH", "TN", "SC", "AL", "LA", "NM", "AZ", "CO", "WA"]

# Revenue proxy thresholds (total obligated in lookback period → estimate annual revenue)
# Rule of thumb: federal contracts = ~40-60% of mid-tier EPC revenue
REVENUE_PROXY_MIN_M = 5      # $5M+ in federal contracts → likely $10M+ revenue
REVENUE_PROXY_MAX_M = 200    # $200M cap — above this they're too big (Quanta, MasTec tier)


# ── USASpending API ────────────────────────────────────────────────────────────

def search_awards_by_naics(
    naics: str,
    days_back: int = 365,
    limit: int = 100,
    agency_code: str = None,
) -> list[dict]:
    """
    Search USASpending for contract awards by NAICS code.
    Returns raw award records.
    """
    date_start = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    date_end = datetime.utcnow().strftime("%Y-%m-%d")

    payload = {
        "filters": {
            "award_type_codes": CONTRACT_AWARD_TYPES,
            "naics_codes": [naics],
            "time_period": [{"start_date": date_start, "end_date": date_end}],
        },
        "fields": [
            "recipient_name",
            "recipient_uei",
            "recipient_location",
            "award_amount",
            "total_obligation",
            "awarding_agency_name",
            "awarding_sub_agency_name",
            "naics_code",
            "naics_description",
            "period_of_performance_start_date",
            "period_of_performance_current_end_date",
            "description",
            "award_id",
            "cage_code",
        ],
        "sort": "total_obligation",
        "order": "desc",
        "limit": min(limit, 100),
        "page": 1,
    }

    if agency_code:
        payload["filters"]["agencies"] = [
            {"type": "awarding", "tier": "toptier", "toptier_code": agency_code}
        ]

    try:
        resp = requests.post(
            f"{USASPENDING_BASE}/search/spending_by_award/",
            json=payload,
            timeout=30,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        logger.info(f"[USASpending] NAICS {naics}: {len(results)} awards returned")
        return results

    except requests.exceptions.HTTPError as e:
        logger.warning(f"[USASpending] HTTP {e.response.status_code} for NAICS {naics}: {e}")
        return []
    except Exception as e:
        logger.warning(f"[USASpending] Error for NAICS {naics}: {e}")
        return []


def get_recipient_profile(uei: str) -> dict:
    """Get detailed recipient profile from USASpending."""
    try:
        resp = requests.get(
            f"{USASPENDING_BASE}/recipient/{uei}/",
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return {}


def aggregate_by_recipient(awards: list[dict]) -> list[dict]:
    """
    Group awards by company. Sum total obligations.
    Returns list sorted by total contract value (revenue proxy).
    """
    companies = {}

    for award in awards:
        name = (award.get("recipient_name") or "").strip()
        if not name or name in ("UNKNOWN", "REDACTED"):
            continue

        # State filter
        loc = award.get("recipient_location") or {}
        state = loc.get("state_code", "")
        if state and TARGET_STATES and state not in TARGET_STATES:
            continue

        uei = award.get("recipient_uei", "")
        key = uei or name.upper()

        if key not in companies:
            companies[key] = {
                "name": name,
                "uei": uei,
                "cage_code": award.get("cage_code", ""),
                "state": state,
                "city": loc.get("city_name", ""),
                "total_obligated_m": 0.0,
                "award_count": 0,
                "agencies": set(),
                "naics_codes": set(),
                "latest_award_date": "",
                "contract_descriptions": [],
            }

        obligated = float(award.get("total_obligation") or 0)
        companies[key]["total_obligated_m"] += obligated / 1_000_000
        companies[key]["award_count"] += 1

        agency = award.get("awarding_agency_name", "")
        if agency:
            companies[key]["agencies"].add(agency)

        naics = award.get("naics_code", "")
        if naics:
            companies[key]["naics_codes"].add(naics)

        award_date = award.get("period_of_performance_start_date", "")
        if award_date and award_date > companies[key]["latest_award_date"]:
            companies[key]["latest_award_date"] = award_date

        desc = award.get("description", "")
        if desc and len(companies[key]["contract_descriptions"]) < 3:
            companies[key]["contract_descriptions"].append(desc[:100])

    # Convert sets to lists and sort
    result = []
    for c in companies.values():
        c["agencies"] = list(c["agencies"])
        c["naics_codes"] = list(c["naics_codes"])
        result.append(c)

    return sorted(result, key=lambda x: x["total_obligated_m"], reverse=True)


def filter_icp_range(companies: list[dict]) -> list[dict]:
    """Filter to ICP revenue proxy range."""
    filtered = [
        c for c in companies
        if REVENUE_PROXY_MIN_M <= c["total_obligated_m"] <= REVENUE_PROXY_MAX_M
    ]
    logger.info(
        f"[USASpending] ICP filter: {len(companies)} → {len(filtered)} "
        f"(${REVENUE_PROXY_MIN_M}M-${REVENUE_PROXY_MAX_M}M federal contract proxy)"
    )
    return filtered


# ── Sector-specific hunts ──────────────────────────────────────────────────────

def hunt_defense_contractors(days_back: int = 365, limit_per_naics: int = 100) -> list[dict]:
    """
    Find EPC contractors winning DoD/Army Corps contracts.
    These companies are doing MILCON (military construction) — our prime ICP for defense.
    """
    all_awards = []

    # Hit both general EPC + defense-specific NAICS
    combined_naics = {**EPC_NAICS, **DEFENSE_NAICS}
    for naics in list(combined_naics.keys())[:8]:
        # Filter to DoD agencies
        for agency_code in ["097", "096"]:  # DoD + Army Corps
            awards = search_awards_by_naics(
                naics=naics,
                days_back=days_back,
                limit=limit_per_naics,
                agency_code=agency_code,
            )
            all_awards.extend(awards)
            time.sleep(0.5)

    companies = aggregate_by_recipient(all_awards)
    return filter_icp_range(companies)


def hunt_energy_contractors(days_back: int = 365, limit_per_naics: int = 100) -> list[dict]:
    """
    Find EPC contractors winning DoE and utility-related federal contracts.
    Covers grid modernization, power plant construction, transmission.
    """
    all_awards = []

    for naics in list(EPC_NAICS.keys()):
        # DoE awards + broad search (utilities contract through multiple agencies)
        awards = search_awards_by_naics(
            naics=naics,
            days_back=days_back,
            limit=limit_per_naics,
        )
        all_awards.extend(awards)
        time.sleep(0.5)

    companies = aggregate_by_recipient(all_awards)
    return filter_icp_range(companies)


# ── Airtable upsert ────────────────────────────────────────────────────────────

def _build_notes(company: dict, sector: str) -> str:
    agencies_str = ", ".join(company["agencies"][:3]) if company["agencies"] else "Various federal agencies"
    naics_str = ", ".join(company["naics_codes"][:3]) if company["naics_codes"] else ""
    desc_str = " | ".join(company["contract_descriptions"]) if company["contract_descriptions"] else ""

    notes = (
        f"Source: USASpending.gov (federal contract history)\n"
        f"Total federal contracts (est. 12mo): ${company['total_obligated_m']:.1f}M\n"
        f"Contract count: {company['award_count']}\n"
        f"Agencies: {agencies_str}\n"
    )
    if company.get("cage_code"):
        notes += f"CAGE Code: {company['cage_code']}\n"
    if company.get("uei"):
        notes += f"UEI: {company['uei']}\n"
    if naics_str:
        notes += f"NAICS: {naics_str}\n"
    if company.get("city") and company.get("state"):
        notes += f"Location: {company['city']}, {company['state']}\n"
    if company.get("latest_award_date"):
        notes += f"Latest award: {company['latest_award_date']}\n"
    if desc_str:
        notes += f"Contract work: {desc_str[:300]}\n"
    notes += f"\nRevenue proxy: ${company['total_obligated_m']:.1f}M federal = ~${company['total_obligated_m'] * 2:.0f}M total revenue est."

    return notes


def _confidence_from_contracts(company: dict) -> int:
    """Higher federal contract value = higher ICP confidence score."""
    total = company["total_obligated_m"]
    count = company["award_count"]
    score = 50  # Base: confirmed federal contractor

    if total >= 50:
        score += 20
    elif total >= 20:
        score += 12
    elif total >= 10:
        score += 6

    if count >= 10:
        score += 10
    elif count >= 5:
        score += 5

    # DoD = higher priority for defense ICP
    agencies_str = " ".join(company.get("agencies", []))
    if "defense" in agencies_str.lower() or "army" in agencies_str.lower():
        score += 5

    return min(score, 90)


def upsert_companies_to_airtable(companies: list[dict], sector: str, dry_run: bool = False) -> dict:
    """Upsert discovered companies into Airtable projects."""
    if not AIRTABLE_API_KEY:
        logger.warning("[Airtable] No API key — skipping upsert")
        return {"created": 0, "skipped": 0, "errors": 0}

    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLES['projects']}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json",
    }

    results = {"created": 0, "skipped": 0, "errors": 0}

    for company in companies:
        name = company["name"]

        if dry_run:
            print(
                f"  [DRY RUN] {name} | ${company['total_obligated_m']:.1f}M contracts | "
                f"{company['state']} | {', '.join(company['agencies'][:2])}"
            )
            results["created"] += 1
            continue

        # Check existence
        try:
            check = requests.get(
                url,
                headers={"Authorization": f"Bearer {AIRTABLE_API_KEY}"},
                params={"filterByFormula": f"{{owner_company}}='{name.replace(chr(39), '')}'"},
                timeout=15,
            )
            check.raise_for_status()
            if check.json().get("records"):
                results["skipped"] += 1
                logger.debug(f"[Airtable] Already exists: {name}")
                continue
        except Exception:
            pass

        fields = {
            "owner_company": name,
            "sector": sector,
            "stage": "Identified",
            "priority": "High" if company["total_obligated_m"] >= 20 else "Medium",
            "icp_fit": "Strong" if company["total_obligated_m"] >= 20 else "Moderate",
            "notes": _build_notes(company, sector),
            "signal_type": "government_contract",
            "confidence_score": _confidence_from_contracts(company),
        }

        try:
            resp = requests.post(url, headers=headers, json={"fields": fields}, timeout=15)
            resp.raise_for_status()
            results["created"] += 1
            logger.info(f"[Airtable] Created: {name} (${company['total_obligated_m']:.1f}M contracts)")
        except Exception as e:
            logger.error(f"[Airtable] Failed for {name}: {e}")
            results["errors"] += 1

        time.sleep(0.2)

    return results


def push_signal_to_airtable(sector: str, total_companies: int, total_value_m: float) -> None:
    """Push a summary signal to signals_raw for sector scoring."""
    try:
        from storage.airtable import get_client
        at = get_client()
        at.insert_signal(
            signal_type="government_contract",
            source="USASpending.gov",
            company_name="USASpending Summary",
            sector=sector,
            signal_date=datetime.utcnow().strftime("%Y-%m-%d"),
            raw_content=(
                f"USASpending hunt: {total_companies} active EPC contractors found with "
                f"${total_value_m:.0f}M total federal contracts in last 12 months.\n"
                f"These companies are actively winning government contracts in {sector}."
            ),
            heat_score=min(30.0 + (total_companies / 10), 60.0),
        )
        logger.info(f"[USASpending] Pushed summary signal for {sector}")
    except Exception as e:
        logger.warning(f"[USASpending] Could not push signal: {e}")


# ── Main ───────────────────────────────────────────────────────────────────────

def run_usaspending_hunt(
    sector: str = None,
    days_back: int = 365,
    limit_per_naics: int = 100,
    dry_run: bool = False,
) -> dict:
    """
    Run USASpending contractor hunt for one or all sectors.

    Args:
        sector: "defense", "energy", or None (both)
        days_back: lookback window in days
        limit_per_naics: awards to fetch per NAICS code
        dry_run: print results without writing to Airtable

    Returns:
        Summary dict with counts per sector
    """
    results = {}

    sectors_to_run = []
    if sector in (None, "defense"):
        sectors_to_run.append(("Defense", hunt_defense_contractors))
    if sector in (None, "energy"):
        sectors_to_run.append(("Power & Grid Infrastructure", hunt_energy_contractors))

    for sector_name, hunt_fn in sectors_to_run:
        logger.info(f"[USASpending] Hunting {sector_name}...")
        companies = hunt_fn(days_back=days_back, limit_per_naics=limit_per_naics)

        total_value = sum(c["total_obligated_m"] for c in companies)
        logger.info(
            f"[USASpending] {sector_name}: {len(companies)} ICP companies, "
            f"${total_value:.0f}M total contracts"
        )

        if dry_run:
            print(f"\n{'='*60}")
            print(f"DRY RUN — {sector_name}: {len(companies)} companies")
            print(f"{'='*60}")
            airtable_result = upsert_companies_to_airtable(companies, sector_name, dry_run=True)
        else:
            airtable_result = upsert_companies_to_airtable(companies, sector_name, dry_run=False)
            if airtable_result["created"] > 0:
                push_signal_to_airtable(sector_name, len(companies), total_value)

        results[sector_name] = {
            "companies_found": len(companies),
            "total_contract_value_m": round(total_value, 1),
            **airtable_result,
        }

    logger.info(f"[USASpending] Hunt complete: {results}")
    return results


if __name__ == "__main__":
    import logging as _logging
    _logging.basicConfig(level=_logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="ECAS USASpending Hunter")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--sector", choices=["defense", "energy"], default=None)
    parser.add_argument("--days-back", type=int, default=365)
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    result = run_usaspending_hunt(
        sector=args.sector,
        days_back=args.days_back,
        limit_per_naics=args.limit,
        dry_run=args.dry_run,
    )
    print(f"\nResult: {result}")
