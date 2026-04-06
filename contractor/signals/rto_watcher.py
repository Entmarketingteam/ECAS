"""
contractor/signals/rto_watcher.py — RTO announcements + commercial lease signals.

RTO mandate → offices reopening → urgent janitorial contracts needed.
Commercial lease signed → new tenant → all 3 service verticals need contracts.

Sources: Google News RSS
Schedule: Every 12h
"""
import re
import logging
import requests
import feedparser
from datetime import datetime

from contractor.signals._airtable import push_signals, signal_exists

logger = logging.getLogger(__name__)

TARGET_MARKETS = [
    "Austin, TX", "Dallas, TX", "Houston, TX", "Atlanta, GA",
    "Charlotte, NC", "Nashville, TN", "Columbus, OH", "Tampa, FL",
]

GNEWS_RTO_RSS = (
    "https://news.google.com/rss/search?q=return+to+office+{city}+2026"
    "&hl=en-US&gl=US&ceid=US:en"
)
GNEWS_LEASE_RSS = (
    "https://news.google.com/rss/search?q=commercial+lease+office+{city}"
    "&hl=en-US&gl=US&ceid=US:en"
)

RTO_KEYWORDS = ["return to office", "rto", "back to office", "mandatory in-person", "in-office requirement"]
LEASE_KEYWORDS = ["signs lease", "signed lease", "new office", "sq ft", "sqft", "square feet", "headquarters", "relocates to", "office lease", "commercial lease"]


def fetch_rto_signals(market: str) -> list[dict]:
    city = market.replace(", ", "+").replace(" ", "+")
    signals = []
    try:
        r = requests.get(GNEWS_RTO_RSS.format(city=city), timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        feed = feedparser.parse(r.content)
    except Exception as e:
        logger.warning("RTO RSS failed for %s: %s", market, e)
        return []

    for entry in getattr(feed, "entries", []) or []:
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        combined = (title + " " + summary).lower()

        if not any(kw in combined for kw in RTO_KEYWORDS):
            continue

        company_match = re.match(
            r'^([A-Z][A-Za-z\s&,\.]+?)\s+(?:requires|mandates|announces|orders|tells|asks)',
            title,
            re.IGNORECASE,
        )
        if not company_match:
            continue
        company_name = company_match.group(1).strip()

        dedup_key = re.sub(r'[^a-z0-9]', '', (company_name + market + title[:50]).lower())
        if signal_exists(dedup_key, "rto_announcement"):
            continue

        signals.append({
            "company_name": company_name,
            "company_domain": "",
            "vertical": "Commercial Janitorial",
            "vertical_type": "contractor",
            "signal_type": "rto_announcement",
            "detected_at": datetime.utcnow().isoformat(),
            "source": "Google News RSS",
            "processed": False,
            "raw_data_json": {
                "headline": title[:200],
                "url": entry.get("link", ""),
                "market": market,
            },
        })

    logger.info("RTO signals %s: %d found", market, len(signals))
    return signals


def fetch_lease_signals(market: str) -> list[dict]:
    city = market.replace(", ", "+").replace(" ", "+")
    signals = []
    try:
        r = requests.get(GNEWS_LEASE_RSS.format(city=city), timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        feed = feedparser.parse(r.content)
    except Exception as e:
        logger.warning("Lease RSS failed for %s: %s", market, e)
        return []

    for entry in getattr(feed, "entries", []) or []:
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        combined = (title + " " + summary).lower()

        if not any(kw in combined for kw in LEASE_KEYWORDS):
            continue

        company_match = re.match(
            r'^([A-Z][A-Za-z\s&,\.]+?)\s+(?:signs|signed|leases|moves|relocates|opens)',
            title,
            re.IGNORECASE,
        )
        if not company_match:
            continue
        company_name = company_match.group(1).strip()

        dedup_key = re.sub(r'[^a-z0-9]', '', (company_name + market + title[:50]).lower())
        if signal_exists(dedup_key, "commercial_lease_signed"):
            continue

        signals.append({
            "company_name": company_name,
            "company_domain": "",
            "vertical": "Commercial Janitorial",
            "vertical_type": "contractor",
            "signal_type": "commercial_lease_signed",
            "detected_at": datetime.utcnow().isoformat(),
            "source": "Google News RSS",
            "processed": False,
            "raw_data_json": {
                "headline": title[:200],
                "url": entry.get("link", ""),
                "market": market,
            },
        })

    logger.info("Lease signals %s: %d found", market, len(signals))
    return signals


def run_rto_watcher() -> int:
    """APScheduler entry point."""
    all_signals = []
    for market in TARGET_MARKETS:
        all_signals.extend(fetch_rto_signals(market))
        all_signals.extend(fetch_lease_signals(market))
    pushed = push_signals(all_signals)
    logger.info("RTO watcher done: %d signals pushed", pushed)
    return pushed
