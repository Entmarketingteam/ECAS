"""
contractor/signals/competitor_watcher.py — Franchise expansion + OSHA citation signals.

Sources:
- Google News RSS for franchise expansion press releases (franchise_new_territory, 70 pts)
- Google News RSS for OSHA citations of competitors (osha_citation, 55 pts)

Schedule: Daily at 6am
"""
import re
import logging
import requests
import feedparser
from datetime import datetime

from contractor.signals._airtable import push_signals, signal_exists

logger = logging.getLogger(__name__)

# Franchise competitors by vertical — expansion = existential pressure on independents
FRANCHISE_MONITORS = {
    "Commercial Janitorial": ["Jan-Pro", "Coverall", "ServiceMaster Clean", "ABM Industries"],
    "Pest Control": ["Rollins", "Orkin", "Terminix", "Rentokil", "Western Pest"],
    "Commercial Roofing": ["Tecta America", "Nations Roof", "Weatherproofing Technologies"],
}

# Google News RSS: franchise expansion search per vertical
GNEWS_FRANCHISE_RSS = (
    "https://news.google.com/rss/search?q={query}+franchise+expansion+OR+new+territory"
    "&hl=en-US&gl=US&ceid=US:en"
)
GNEWS_OSHA_RSS = (
    "https://news.google.com/rss/search?q=OSHA+citation+{vertical_term}+{state}"
    "&hl=en-US&gl=US&ceid=US:en"
)

TARGET_STATES = ["TX", "FL", "GA", "NC", "OH", "TN"]


def fetch_franchise_rss(vertical: str) -> list[dict]:
    """Monitor Google News for franchise expansion announcements in the vertical."""
    competitors = FRANCHISE_MONITORS.get(vertical, [])
    signals = []

    for competitor in competitors:
        url = GNEWS_FRANCHISE_RSS.format(query=competitor.replace(" ", "+"))
        try:
            r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            feed = feedparser.parse(r.content)
        except Exception as e:
            logger.warning("Franchise RSS failed for %s: %s", competitor, e)
            continue

        for entry in (getattr(feed, "entries", []) or []):
            title = entry.get("title", "")
            link = entry.get("link", "")

            # Verify expansion keywords
            if not any(kw in title.lower() for kw in ["franchise", "territory", "expansion", "opens", "new location"]):
                continue

            dedup_key = re.sub(r'[^a-z0-9]', '', (competitor + title[:50]).lower())
            if signal_exists(dedup_key, "franchise_new_territory"):
                continue

            signals.append({
                "company_name": competitor,
                "company_domain": "",
                "vertical": vertical,
                "vertical_type": "contractor",
                "signal_type": "franchise_new_territory",
                "detected_at": datetime.utcnow().isoformat(),
                "source": "Google News RSS",
                "processed": False,
                "raw_data_json": {
                    "competitor": competitor,
                    "headline": title[:200],
                    "url": link,
                },
            })

    logger.info("Franchise RSS %s: %d signals", vertical, len(signals))
    return signals


def fetch_osha_rss(vertical: str) -> list[dict]:
    """Monitor Google News for OSHA citations against competitors in target states."""
    vertical_terms = {
        "Commercial Janitorial": "janitorial+cleaning",
        "Pest Control": "pest+control+exterminator",
        "Commercial Roofing": "roofing+contractor",
    }
    term = vertical_terms.get(vertical, "contractor")
    signals = []

    for state in TARGET_STATES:
        url = GNEWS_OSHA_RSS.format(vertical_term=term, state=state)
        try:
            r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            feed = feedparser.parse(r.content)
        except Exception as e:
            logger.warning("OSHA RSS failed for %s/%s: %s", vertical, state, e)
            continue

        for entry in (getattr(feed, "entries", []) or []):
            title = entry.get("title", "")
            link = entry.get("link", "")
            summary = entry.get("summary", "")

            if "osha" not in (title + summary).lower():
                continue

            # Extract company name — heuristic: first proper noun before "cited", "fined", "violated"
            company_match = re.match(r'^([A-Z][^,\.]+?)\s+(?:cited|fined|penalized)', title, re.IGNORECASE)
            if not company_match:
                continue
            company_name = company_match.group(1).strip()

            dedup_key = re.sub(r'[^a-z0-9]', '', (company_name + state + title[:50]).lower())
            if signal_exists(dedup_key, "osha_citation"):
                continue

            signals.append({
                "company_name": company_name,
                "company_domain": "",
                "vertical": vertical,
                "vertical_type": "contractor",
                "signal_type": "osha_citation",
                "detected_at": datetime.utcnow().isoformat(),
                "source": "Google News RSS",
                "processed": False,
                "raw_data_json": {
                    "headline": title[:200],
                    "url": link,
                    "state": state,
                },
            })

    logger.info("OSHA RSS %s: %d signals", vertical, len(signals))
    return signals


def run_competitor_watcher() -> int:
    """APScheduler entry point."""
    all_signals = []
    for vertical in ["Commercial Janitorial", "Pest Control", "Commercial Roofing"]:
        all_signals.extend(fetch_franchise_rss(vertical))
        all_signals.extend(fetch_osha_rss(vertical))
    pushed = push_signals(all_signals)
    logger.info("Competitor watcher done: %d signals pushed", pushed)
    return pushed
