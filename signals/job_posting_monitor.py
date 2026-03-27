"""
signals/job_posting_monitor.py — EPC company hiring surge detector.

Monitors job postings for EPC contractor hiring signals using SerpAPI.
Why this works: a company posting 5+ estimator/BD/PM jobs is actively winning
more contracts than they can currently staff. That's the exact moment to reach
out — they're in growth mode and open to BD support.

Signal types detected:
  1. Estimator surge — more estimating capacity = bidding more work
  2. BD/Proposal hiring — building a dedicated business development function
  3. Project Manager surge — projects have been awarded, now need to staff them
  4. Pre-construction / VDC — moving upmarket, doing more complex work

These signals run AHEAD of the work — companies hire estimators BEFORE projects
start, making this an early-warning system for pipeline growth.

Flow:
  1. SerpAPI Google Jobs search for target titles + EPC keywords + target states
  2. Extract company name, title, location, posting date
  3. Aggregate: companies with 3+ open roles = surge threshold
  4. Cross-reference against existing Airtable projects (boost confidence score)
  5. Insert new companies not yet in pipeline
  6. Push signals to signals_raw for sector scoring influence
  7. Return summary for scheduler logging

Usage:
    python3 signals/job_posting_monitor.py --dry-run
    python3 signals/job_posting_monitor.py --sector defense
    python3 signals/job_posting_monitor.py              # all sectors
"""

import argparse
import logging
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLES, ICP
)

SERP_API_KEY = __import__("os").environ.get("SERP_API_KEY", "")

logger = logging.getLogger(__name__)

# ── Job search queries ─────────────────────────────────────────────────────────

# Titles that signal EPC contractor growth — in priority order
EPC_SIGNAL_TITLES = [
    # Tier 1 — Direct pipeline signals (these roles = active bidding/winning)
    "estimator electrical",
    "estimator power",
    "estimator substation",
    "proposal manager EPC",
    "business development director electrical contractor",
    "VP business development electrical",
    # Tier 2 — Project execution signals (projects awarded, now staffing)
    "project manager substation",
    "project manager transmission",
    "project manager electrical contractor",
    "superintendent electrical construction",
    # Tier 3 — Growth signals (upmarket movement)
    "preconstruction manager electrical",
    "director of operations electrical contractor",
    "VDC manager construction",
]

# Defense-specific additions
DEFENSE_SIGNAL_TITLES = [
    "estimator MILCON",
    "project manager military construction",
    "proposal manager defense construction",
    "business development defense contractor",
    "estimator government contractor",
    "IDIQ program manager construction",
]

# Qualifier keywords — confirm the company is an EPC/contractor (not a utility)
EPC_QUALIFIER_KEYWORDS = [
    "contractor", "construction", "electric", "electrical", "EPC",
    "substation", "transmission", "infrastructure", "engineering",
]

# Keywords that indicate we found a utility/owner, not an EPC (skip these)
SKIP_COMPANY_KEYWORDS = [
    "duke energy", "dominion", "nextera", "national grid", "pge",
    "con edison", "entergy", "exelon", "staffing", "recruiting",
    "talent", "search firm", "executive search",
]

SURGE_THRESHOLD = 3   # 3+ open roles at same company = surge signal
TARGET_STATES = ICP["states"] + ["OH", "TN", "SC"]


# ── SerpAPI Google Jobs ────────────────────────────────────────────────────────

def search_jobs_serpapi(query: str, location: str = "United States", num: int = 10) -> list[dict]:
    """
    Search Google Jobs via SerpAPI.
    Returns list of job posting dicts.
    """
    if not SERP_API_KEY:
        logger.warning("[JobMonitor] SERP_API_KEY not set — skipping")
        return []

    try:
        resp = requests.get(
            "https://serpapi.com/search",
            params={
                "engine": "google_jobs",
                "q": query,
                "location": location,
                "api_key": SERP_API_KEY,
                "num": num,
                "chips": "date_posted:week",   # Recent postings only
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        jobs = data.get("jobs_results", [])
        logger.debug(f"[SerpAPI] '{query}': {len(jobs)} jobs")
        return jobs

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            logger.warning("[SerpAPI] Rate limited — sleeping 30s")
            time.sleep(30)
        else:
            logger.warning(f"[SerpAPI] HTTP error for '{query}': {e}")
        return []
    except Exception as e:
        logger.warning(f"[SerpAPI] Error for '{query}': {e}")
        return []


def search_jobs_google_organic(query: str) -> list[dict]:
    """
    Fallback: Google organic search for job postings.
    Uses SerpAPI Google engine (cheaper per credit than Google Jobs).
    Returns parsed job data from organic results.
    """
    if not SERP_API_KEY:
        return []

    try:
        resp = requests.get(
            "https://serpapi.com/search",
            params={
                "engine": "google",
                "q": query,
                "api_key": SERP_API_KEY,
                "num": 10,
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()

        jobs = []
        for result in data.get("organic_results", []):
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            link = result.get("link", "")

            # Extract company name from title pattern "Job Title at Company | LinkedIn"
            company = ""
            if " at " in title:
                parts = title.split(" at ", 1)
                company = parts[1].split("|")[0].split("-")[0].strip()
            elif " - " in title:
                parts = title.split(" - ")
                company = parts[-1].strip()

            if company and len(company) > 2:
                jobs.append({
                    "title": title,
                    "company_name": company,
                    "location": "",
                    "description": snippet,
                    "source": "google_organic",
                    "link": link,
                })

        return jobs

    except Exception as e:
        logger.debug(f"[SerpAPI organic] Error: {e}")
        return []


# ── Data extraction + normalization ───────────────────────────────────────────

def _extract_job_data(job: dict) -> dict:
    """Normalize a SerpAPI job result into our schema."""
    # Google Jobs API structure
    company = job.get("company_name", "") or job.get("company", "")
    title = job.get("title", "")
    location = job.get("location", "")
    detected_ext = job.get("detected_extensions", {})
    posted = detected_ext.get("posted_at", "") or job.get("posted_at", "")
    description = job.get("description", "") or job.get("snippet", "")

    # Extract state from location string
    state = ""
    if location:
        for s in TARGET_STATES:
            if f", {s}" in location or f" {s} " in location or location.endswith(f" {s}"):
                state = s
                break

    return {
        "company": company.strip(),
        "title": title.strip(),
        "location": location.strip(),
        "state": state,
        "posted": posted,
        "description": description[:300],
        "source": job.get("source", "google_jobs"),
        "link": job.get("job_link", job.get("link", "")),
    }


def _is_epc_company(company_name: str, description: str = "") -> bool:
    """Rough check: is this an EPC contractor, not a utility/staffing firm?"""
    combined = f"{company_name} {description}".lower()
    if any(kw in combined for kw in SKIP_COMPANY_KEYWORDS):
        return False
    # Allow if company name or job description mentions contractor/construction
    return any(kw in combined for kw in EPC_QUALIFIER_KEYWORDS)


def _classify_signal_strength(job_count: int, titles: list[str]) -> str:
    """Classify surge strength based on volume and title mix."""
    has_bd = any(
        any(kw in t.lower() for kw in ["business development", "bd ", "proposal", "estimator"])
        for t in titles
    )
    if job_count >= 7:
        return "strong"
    elif job_count >= 4 and has_bd:
        return "strong"
    elif job_count >= 3:
        return "moderate"
    else:
        return "weak"


# ── Aggregation ───────────────────────────────────────────────────────────────

def aggregate_company_signals(jobs: list[dict]) -> list[dict]:
    """
    Group jobs by company. Companies with SURGE_THRESHOLD+ open roles
    get flagged as active growth signals.
    """
    by_company = defaultdict(lambda: {
        "jobs": [],
        "titles": [],
        "states": set(),
        "earliest_post": "",
        "latest_post": "",
    })

    for job in jobs:
        company = job["company"]
        if not company or not _is_epc_company(company, job.get("description", "")):
            continue

        by_company[company]["jobs"].append(job)
        by_company[company]["titles"].append(job["title"])
        if job["state"]:
            by_company[company]["states"].add(job["state"])

    surge_companies = []
    for company, data in by_company.items():
        job_count = len(data["jobs"])
        if job_count < SURGE_THRESHOLD:
            continue  # Not enough signal

        signal_strength = _classify_signal_strength(job_count, data["titles"])
        sample_location = data["jobs"][0].get("location", "")

        surge_companies.append({
            "name": company,
            "open_roles": job_count,
            "titles": list(set(data["titles"])),
            "states": list(data["states"]),
            "location": sample_location,
            "signal_strength": signal_strength,
            "signal_type": "hiring_surge",
        })

    return sorted(surge_companies, key=lambda x: x["open_roles"], reverse=True)


# ── Main search runs ───────────────────────────────────────────────────────────

def run_energy_job_scan() -> list[dict]:
    """Scan for power/grid EPC hiring signals."""
    all_jobs = []

    # Primary: Google Jobs API (high quality, structured)
    for title_query in EPC_SIGNAL_TITLES[:8]:  # Top 8 most signal-rich titles
        jobs = search_jobs_serpapi(
            query=f"{title_query} construction company",
            location="United States",
            num=10,
        )
        for job in jobs:
            all_jobs.append(_extract_job_data(job))
        time.sleep(1.5)  # SerpAPI rate limit

    # Secondary: organic search for LinkedIn job listings
    for state in TARGET_STATES[:5]:  # Top 5 target states
        jobs = search_jobs_serpapi(
            query=f"electrical contractor estimator \"business development\" {state}",
            location=state,
            num=10,
        )
        for job in jobs:
            all_jobs.append(_extract_job_data(job))
        time.sleep(1.5)

    return aggregate_company_signals(all_jobs)


def run_defense_job_scan() -> list[dict]:
    """Scan for defense EPC/MILCON contractor hiring signals."""
    all_jobs = []

    for title_query in DEFENSE_SIGNAL_TITLES:
        jobs = search_jobs_serpapi(
            query=f"{title_query}",
            location="United States",
            num=10,
        )
        for job in jobs:
            all_jobs.append(_extract_job_data(job))
        time.sleep(1.5)

    # Also check general EPC titles but filter description for defense context
    for title_query in EPC_SIGNAL_TITLES[:4]:
        jobs = search_jobs_serpapi(
            query=f"{title_query} \"government\" OR \"federal\" OR \"DoD\" OR \"MILCON\"",
            location="United States",
            num=10,
        )
        for job in jobs:
            d = _extract_job_data(job)
            if any(kw in d.get("description", "").lower()
                   for kw in ["government", "federal", "dod", "milcon", "military"]):
                all_jobs.append(d)
        time.sleep(1.5)

    return aggregate_company_signals(all_jobs)


# ── Airtable integration ───────────────────────────────────────────────────────

def _score_from_surge(company: dict) -> int:
    """Confidence score boost from hiring surge."""
    base = 55
    if company["signal_strength"] == "strong":
        base += 15
    elif company["signal_strength"] == "moderate":
        base += 8
    base += min(company["open_roles"] * 2, 15)
    return min(base, 85)


def _build_surge_notes(company: dict, sector: str) -> str:
    titles_str = ", ".join(company["titles"][:5])
    states_str = ", ".join(company["states"]) if company["states"] else company.get("location", "")
    return (
        f"Source: Job posting monitor (Google Jobs / SerpAPI)\n"
        f"Signal: {company['signal_strength'].upper()} hiring surge — "
        f"{company['open_roles']} open roles\n"
        f"Titles: {titles_str}\n"
        f"Location: {states_str}\n"
        f"Sector: {sector}\n\n"
        f"Hiring surge = active pipeline. Companies don't hire estimators and BD "
        f"directors without contracts to bid or projects already awarded. "
        f"High conversion probability — reach out NOW while they're in growth mode."
    )


def boost_existing_project(company_name: str, notes_addition: str, score_boost: int) -> bool:
    """If company already in pipeline, boost their confidence score."""
    if not AIRTABLE_API_KEY:
        return False

    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLES['projects']}"
    try:
        resp = requests.get(
            url,
            headers={"Authorization": f"Bearer {AIRTABLE_API_KEY}"},
            params={"filterByFormula": f"{{owner_company}}='{company_name.replace(chr(39), '')}'"},
            timeout=15,
        )
        resp.raise_for_status()
        records = resp.json().get("records", [])

        if not records:
            return False

        record_id = records[0]["id"]
        existing_score = float(records[0].get("fields", {}).get("confidence_score", 50) or 50)
        existing_notes = records[0].get("fields", {}).get("notes", "")

        new_score = min(existing_score + score_boost, 90)
        new_notes = f"{existing_notes}\n\n--- HIRING SURGE SIGNAL ({datetime.utcnow().strftime('%Y-%m-%d')}) ---\n{notes_addition}"

        requests.patch(
            f"{url}/{record_id}",
            headers={
                "Authorization": f"Bearer {AIRTABLE_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"fields": {"confidence_score": new_score, "notes": new_notes}},
            timeout=15,
        )
        logger.info(f"[JobMonitor] Boosted {company_name}: {existing_score:.0f} → {new_score:.0f}")
        return True

    except Exception as e:
        logger.warning(f"[JobMonitor] Could not boost {company_name}: {e}")
        return False


def upsert_surge_companies(companies: list[dict], sector: str, dry_run: bool = False) -> dict:
    """Upsert hiring surge companies into Airtable, or boost existing records."""
    if not AIRTABLE_API_KEY:
        return {"created": 0, "boosted": 0, "skipped": 0, "errors": 0}

    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLES['projects']}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json",
    }

    results = {"created": 0, "boosted": 0, "skipped": 0, "errors": 0}

    for company in companies:
        name = company["name"]
        notes = _build_surge_notes(company, sector)
        score_boost = 10 if company["signal_strength"] == "moderate" else 20

        if dry_run:
            print(
                f"  [DRY RUN] {name} | {company['open_roles']} open roles | "
                f"{company['signal_strength']} | {', '.join(company['states'])}"
            )
            results["created"] += 1
            continue

        # Try to boost existing record first
        if boost_existing_project(name, notes, score_boost):
            results["boosted"] += 1
            time.sleep(0.2)
            continue

        # New company — create project record
        fields = {
            "owner_company": name,
            "sector": sector,
            "stage": "Identified",
            "priority": "High" if company["signal_strength"] == "strong" else "Medium",
            "icp_fit": "Strong" if company["signal_strength"] == "strong" else "Moderate",
            "notes": notes,
            "signal_type": "hiring_surge",
            "confidence_score": _score_from_surge(company),
        }

        try:
            resp = requests.post(url, headers=headers, json={"fields": fields}, timeout=15)
            resp.raise_for_status()
            results["created"] += 1
            logger.info(f"[Airtable] Created (surge): {name} ({company['open_roles']} roles)")
        except Exception as e:
            logger.error(f"[Airtable] Failed for {name}: {e}")
            results["errors"] += 1

        time.sleep(0.2)

    return results


def push_jobs_signal(sector: str, surge_count: int, total_roles: int) -> None:
    """Push hiring surge summary to signals_raw."""
    try:
        from storage.airtable import get_client
        at = get_client()
        at.insert_signal(
            signal_type="hiring_surge",
            source="Google Jobs / SerpAPI",
            company_name="Job Posting Summary",
            sector=sector,
            signal_date=datetime.utcnow().strftime("%Y-%m-%d"),
            raw_content=(
                f"Job posting scan: {surge_count} EPC companies with active hiring surges "
                f"({total_roles} total open roles) in {sector}.\n"
                f"Hiring estimators + BD = active pipeline. Imminent contract activity."
            ),
            heat_score=min(25.0 + (surge_count * 2), 55.0),
        )
    except Exception as e:
        logger.warning(f"[JobMonitor] Could not push signal: {e}")


# ── Main ───────────────────────────────────────────────────────────────────────

def run_job_monitor(
    sector: str = None,
    dry_run: bool = False,
) -> dict:
    """
    Run job posting monitor for one or all sectors.

    Args:
        sector: "defense", "energy", or None (both)
        dry_run: print results without writing to Airtable

    Returns:
        Summary dict
    """
    if not SERP_API_KEY:
        logger.error("[JobMonitor] SERP_API_KEY not set — cannot run job monitor")
        return {"error": "SERP_API_KEY not configured"}

    results = {}

    runs = []
    if sector in (None, "energy"):
        runs.append(("Power & Grid Infrastructure", run_energy_job_scan))
    if sector in (None, "defense"):
        runs.append(("Defense", run_defense_job_scan))

    for sector_name, scan_fn in runs:
        logger.info(f"[JobMonitor] Scanning {sector_name} hiring signals...")
        companies = scan_fn()

        total_roles = sum(c["open_roles"] for c in companies)
        logger.info(
            f"[JobMonitor] {sector_name}: {len(companies)} companies surging, "
            f"{total_roles} total open roles"
        )

        if dry_run:
            print(f"\n{'='*60}")
            print(f"DRY RUN — {sector_name}: {len(companies)} companies hiring")
            print(f"{'='*60}")
            airtable_result = upsert_surge_companies(companies, sector_name, dry_run=True)
        else:
            airtable_result = upsert_surge_companies(companies, sector_name, dry_run=False)
            if companies:
                push_jobs_signal(sector_name, len(companies), total_roles)

        results[sector_name] = {
            "surge_companies": len(companies),
            "total_open_roles": total_roles,
            **airtable_result,
        }

    return results


if __name__ == "__main__":
    import logging as _logging
    _logging.basicConfig(level=_logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="ECAS Job Posting Monitor")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--sector", choices=["defense", "energy"], default=None)
    args = parser.parse_args()

    result = run_job_monitor(sector=args.sector, dry_run=args.dry_run)
    print(f"\nResult: {result}")
