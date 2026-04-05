"""
contractor/signals/sam_gov_watcher.py — SAM.gov contract award lead signal.

Scrapes recent NAICS-filtered contract awards. A company winning a federal
facilities contract is growing → ICP lead for roofing/janitorial/pest.

API: SAM.gov Opportunities v2 (free, register at sam.gov/api)
Doppler key: SAM_GOV_API_KEY (project: ecas, config: dev)
Schedule: Daily at 5am
"""
import os
import logging
import requests
from datetime import datetime, timedelta

from contractor.signals._airtable import push_signals, signal_exists

logger = logging.getLogger(__name__)

SAM_API_KEY = os.environ.get("SAM_GOV_API_KEY", "DEMO_KEY")
SAM_BASE = "https://api.sam.gov/opportunities/v2/search"
PAGE_SIZE = 100

# NAICS → vertical mapping
NAICS_VERTICAL = {
    "238160": "Commercial Roofing",
    "561720": "Commercial Janitorial",
    "561710": "Pest Control",
}
TARGET_NAICS = ",".join(NAICS_VERTICAL.keys())

# Target states (match geo_focus across verticals)
TARGET_STATES = {"TX", "FL", "GA", "NC", "VA", "PA", "OH", "TN", "CO", "KS", "OK"}


def _vertical_for_naics(naics: str) -> str:
    vertical = NAICS_VERTICAL.get(str(naics))
    if vertical is None:
        logger.warning("Unmapped NAICS code %s — defaulting to Commercial Roofing", naics)
        return "Commercial Roofing"
    return vertical


def fetch_awards_page(offset: int = 0) -> list[dict]:
    """
    Fetch one page of SAM.gov contract award notices.
    Returns list of signal dicts.
    """
    posted_from = (datetime.utcnow() - timedelta(days=30)).strftime("%m/%d/%Y")
    posted_to = datetime.utcnow().strftime("%m/%d/%Y")

    try:
        resp = requests.get(
            SAM_BASE,
            params={
                "api_key": SAM_API_KEY,
                "ptype": "a",               # Award notices
                "ncode": TARGET_NAICS,
                "postedFrom": posted_from,
                "postedTo": posted_to,
                "limit": PAGE_SIZE,
                "offset": offset,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error("SAM.gov fetch failed at offset %d: %s", offset, e)
        return []

    signals = []
    for opp in data.get("opportunitiesData", []):
        award = opp.get("award", {})
        awardee = award.get("awardee", {})
        loc = awardee.get("location", {})
        state = loc.get("state", {}).get("code", "")

        # Filter to target states (SAM.gov doesn't support state filter on awards)
        if TARGET_STATES and state not in TARGET_STATES:
            continue

        company_name = awardee.get("name", "").strip()
        if not company_name:
            continue

        naics = str(opp.get("naicsCode", ""))
        vertical = _vertical_for_naics(naics)

        # Use notice ID as pseudo-domain for dedup (we don't have real domains yet)
        notice_id = opp.get("noticeId", "")
        if not notice_id:
            logger.warning("Skipping signal with empty notice_id — cannot deduplicate")
            continue
        if signal_exists(notice_id, "government_contract_win"):
            continue

        signals.append({
            "company_name": company_name,
            "company_domain": "",  # Apollo enriches this in the orchestrator
            "vertical": vertical,
            "vertical_type": "contractor",
            "signal_type": "government_contract_win",
            "detected_at": datetime.utcnow().isoformat(),
            "source": "SAM.gov",
            "processed": False,
            "raw_data_json": {
                "naics": naics,
                "award_amount": award.get("amount", ""),
                "award_date": award.get("date", ""),
                "city": loc.get("city", {}).get("name", ""),
                "state": state,
                "notice_id": notice_id,
                "title": opp.get("title", ""),
            },
        })

    return signals


def run_sam_gov_watcher() -> int:
    """APScheduler entry point. Paginates SAM.gov awards until empty page."""
    all_signals = []
    offset = 0

    while True:
        page = fetch_awards_page(offset)
        if not page:
            break
        all_signals.extend(page)
        if len(page) < PAGE_SIZE:
            break  # Partial page = last page
        offset += PAGE_SIZE

    pushed = push_signals(all_signals)
    logger.info("SAM.gov watcher done: %d signals pushed", pushed)
    return pushed
