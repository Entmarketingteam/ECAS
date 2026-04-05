"""
contractor/signals/fm_job_watcher.py — Facilities Manager job change + posting signals.

Sources:
- Apollo mixed_people search with recent employment title filter (fm_job_change, 75 pts)
- Google News RSS for FM job postings by state (fm_job_posting, 40 pts)

Schedule: Every 8h
"""
import os
import re
import logging
import feedparser
import requests
from datetime import datetime

from contractor.signals._airtable import push_signals, signal_exists

logger = logging.getLogger(__name__)

APOLLO_API_KEY = os.environ.get("APOLLO_API_KEY", "")
APOLLO_BASE = "https://api.apollo.io/v1"

# FM/Operations titles that indicate the person manages facilities (= vendor decisions)
FM_TITLES = [
    "Facilities Manager", "Facility Manager", "Property Manager",
    "Building Manager", "Operations Manager", "Director of Facilities",
    "VP Facilities", "Head of Facilities", "Facilities Director",
    "Property Operations Manager", "Building Operations Manager",
]

TARGET_STATES = ["TX", "FL", "GA", "NC", "VA", "PA", "OH", "TN", "CO"]

# Google News RSS for FM job postings
GNEWS_FM_RSS = (
    "https://news.google.com/rss/search?q=facilities+manager+hiring+{state}"
    "&hl=en-US&gl=US&ceid=US:en"
)


def fetch_apollo_fm_changes() -> list[dict]:
    """
    Query Apollo for people recently hired into FM/Ops roles at target companies.
    Apollo's employment_history tracks job changes — new FM = vendor review window.
    """
    try:
        resp = requests.post(
            f"{APOLLO_BASE}/mixed_people/api_search",
            headers={"Content-Type": "application/json", "x-api-key": APOLLO_API_KEY},
            json={
                "titles": FM_TITLES,
                "person_locations": [f"United States, {s}" for s in TARGET_STATES],
                "currently_using_any_of_following_technologies": [],
                "page": 1,
                "per_page": 50,
                "sort_by_field": "last_updated_at",
                "sort_ascending": False,
            },
            timeout=30,
        )
        resp.raise_for_status()
        people = resp.json().get("people", [])
    except Exception as e:
        logger.error("Apollo FM search failed: %s", e)
        return []

    signals = []
    for person in people:
        org = person.get("organization") or {}
        company_name = org.get("name", "").strip()
        domain = (org.get("website_url") or "").lower().strip()

        if not company_name:
            continue
        if signal_exists(domain or company_name, "fm_job_change"):
            continue

        signals.append({
            "company_name": company_name,
            "company_domain": domain,
            "vertical": "Commercial Janitorial",  # FM change is strongest for janitorial
            "vertical_type": "contractor",
            "signal_type": "fm_job_change",
            "detected_at": datetime.utcnow().isoformat(),
            "source": "Apollo",
            "processed": False,
            "raw_data_json": {
                "contact_name": f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                "title": person.get("title", ""),
                "city": person.get("city", ""),
                "state": person.get("state", ""),
                "employee_count": org.get("employee_count", 0),
            },
        })

    logger.info("Apollo FM changes: %d new signals", len(signals))
    return signals


def fetch_rss_fm_postings(state: str) -> list[dict]:
    """
    Monitor Google News RSS for FM job postings in a state.
    Job posting = company is dissatisfied with current FM setup → vendor review likely.
    """
    url = GNEWS_FM_RSS.format(state=state.replace(" ", "+"))
    try:
        feed = feedparser.parse(url)
    except Exception as e:
        logger.warning("RSS FM fetch failed for %s: %s", state, e)
        return []

    entries = getattr(feed, "entries", []) or []
    signals = []
    for entry in entries:
        title = entry.get("title", "")
        link = entry.get("link", "")

        # Extract company name from title heuristic: "COMPANY hiring/seeks/looking for"
        company_match = re.match(r'^(.+?)\s+(?:hiring|seeks|looking for|is hiring)', title, re.IGNORECASE)
        if not company_match:
            continue
        company_name = company_match.group(1).strip()

        dedup_key = re.sub(r'[^a-z0-9]', '', company_name.lower())
        if not dedup_key:
            continue
        if signal_exists(dedup_key, "fm_job_posting"):
            continue

        signals.append({
            "company_name": company_name,
            "company_domain": "",
            "vertical": "Commercial Janitorial",
            "vertical_type": "contractor",
            "signal_type": "fm_job_posting",
            "detected_at": datetime.utcnow().isoformat(),
            "source": "Google News RSS",
            "processed": False,
            "raw_data_json": {
                "headline": title[:200],
                "url": link,
                "state": state,
            },
        })

    logger.info("RSS FM postings %s: %d signals", state, len(signals))
    return signals


def run_fm_job_watcher() -> int:
    """APScheduler entry point."""
    all_signals = list(fetch_apollo_fm_changes())
    for state in TARGET_STATES:
        all_signals.extend(fetch_rss_fm_postings(state))
    pushed = push_signals(all_signals)
    logger.info("FM job watcher done: %d signals pushed", pushed)
    return pushed
