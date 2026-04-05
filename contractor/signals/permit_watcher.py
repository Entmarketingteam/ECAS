"""
contractor/signals/permit_watcher.py — Commercial building permit signal scraper.

Sources: 4 Socrata APIs (Austin/Dallas/Charlotte/Atlanta) from contractor/config.py
Filters to commercial permits > $50K (roofing-scale work).
Schedule: Every 12h
Signal type: commercial_permit_pulled (65 pts)
"""
import logging
import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from contractor.config import PERMIT_SOURCES
from contractor.signals._airtable import push_signals, signal_exists

logger = logging.getLogger(__name__)

PERMIT_MIN_VALUE = 50_000

# Keywords that indicate roofing/commercial relevance in permit description
ROOFING_KEYWORDS = ["roof", "roofing", "membrane", "tpo", "epdm", "modified bitumen", "flashing"]
RELEVANT_KEYWORDS = ROOFING_KEYWORDS + ["commercial", "office", "retail", "industrial", "warehouse"]


def _is_relevant_permit(description: str, value: float) -> bool:
    if value < PERMIT_MIN_VALUE:
        return False
    desc_lower = description.lower()
    return any(kw in desc_lower for kw in RELEVANT_KEYWORDS)


def _extract_value(raw: str) -> float:
    """Parse valuation string to float."""
    try:
        return float(str(raw).replace(",", "").replace("$", "").strip())
    except (ValueError, TypeError):
        return 0.0


def fetch_permits_from_source(source: dict) -> list:
    """
    Fetch recent permits from a Socrata API source.
    Returns list of signal dicts for permits matching commercial/roofing criteria.
    """
    cutoff = (datetime.utcnow() - timedelta(days=14)).strftime("%Y-%m-%dT00:00:00")
    params = {
        "$where": f"issue_date >= '{cutoff}'",
        "$limit": 500,
        "$order": "issue_date DESC",
    }
    try:
        resp = requests.get(source["url"], params=params, timeout=30)
        resp.raise_for_status()
        records = resp.json()
    except Exception as e:
        logger.error("Permit fetch failed for %s: %s", source["city"], e)
        return []

    signals = []
    for rec in records:
        description = rec.get("work_description", rec.get("description", rec.get("permit_type", "")))
        value = _extract_value(rec.get("total_valuation", rec.get("declared_valuation", rec.get("job_value", "0"))))

        if not _is_relevant_permit(description, value):
            continue

        company_name = (
            rec.get("contractor_company") or rec.get("applicant_name") or
            rec.get("owner_name") or rec.get("business_name") or "Unknown"
        ).strip()

        permit_number = rec.get("permit_number", rec.get("permit_num", ""))
        if not permit_number:
            continue
        if signal_exists(permit_number, "commercial_permit_pulled"):
            continue

        signals.append({
            "company_name": company_name,
            "company_domain": "",
            "vertical": "Commercial Roofing",
            "vertical_type": "contractor",
            "signal_type": "commercial_permit_pulled",
            "detected_at": datetime.utcnow().isoformat(),
            "source": f"Socrata-{source['city']}",
            "processed": False,
            "raw_data_json": {
                "permit_number": permit_number,
                "description": description[:200],
                "value": value,
                "address": rec.get("address", rec.get("location_address", "")),
                "city": source["city"],
                "issue_date": rec.get("issue_date", ""),
            },
        })

    logger.info("Permits %s: found %d relevant permits", source["city"], len(signals))
    return signals


def run_permit_watcher() -> int:
    """APScheduler entry point. Scrapes all configured permit sources in parallel."""
    all_signals = []

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(fetch_permits_from_source, s): s for s in PERMIT_SOURCES}
        for future in as_completed(futures):
            try:
                all_signals.extend(future.result())
            except Exception as e:
                logger.error("Permit source failed: %s", e)

    pushed = push_signals(all_signals)
    logger.info("Permit watcher done: %d signals pushed", pushed)
    return pushed
