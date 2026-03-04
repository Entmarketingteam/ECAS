"""
signals/ferc_poller.py
Polls FERC eLibrary for new interconnection filings and rate case activity.
Pushes relevant filings to Airtable signals_raw as early indicators of
grid infrastructure spend.
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import API_CONFIG, ALERT_THRESHOLDS

logger = logging.getLogger(__name__)

# FERC docket types relevant to grid infrastructure
GRID_DOCKET_TYPES = ["ER", "EL", "EC", "RT", "QF"]
FERC_SEARCH_URL = "https://efts.ferc.gov/LATEST/search-index"

# Keywords that indicate large grid capex
GRID_CAPEX_KEYWORDS = [
    "transmission line", "substation", "interconnection agreement",
    "grid modernization", "transmission upgrade", "high voltage",
    "bulk power", "generator interconnection", "network upgrade",
    "power purchase agreement", "certificate of public convenience",
    "transmission capacity", "energy storage interconnection",
]


def search_ferc_filings(days_back: int = 7) -> list[dict]:
    """
    Query FERC eLibrary for recent filings matching grid infrastructure keywords.
    Returns list of filing metadata dicts.
    """
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")

    results = []
    for keyword in GRID_CAPEX_KEYWORDS[:6]:  # Limit to avoid rate limits
        try:
            resp = requests.get(
                FERC_SEARCH_URL,
                params={
                    "q": keyword,
                    "dateRange": "custom",
                    "startdt": start_date,
                    "enddt": end_date,
                    "sort": "filed_date",
                    "perpage": "20",
                },
                headers={"Accept": "application/json"},
                timeout=30,
            )
            if resp.status_code != 200:
                continue

            data = resp.json()
            hits = data.get("hits", {}).get("hits", [])
            for hit in hits:
                src = hit.get("_source", {})
                filing = {
                    "docket_number": src.get("docket_number", ""),
                    "filer_name": src.get("filer_name", ""),
                    "filing_description": src.get("description", ""),
                    "filed_date": src.get("filed_date", ""),
                    "docket_type": src.get("docket_type", ""),
                    "matched_keyword": keyword,
                }
                if filing["docket_number"] and filing not in results:
                    results.append(filing)

        except Exception as e:
            logger.warning(f"[FERC] Search error for '{keyword}': {e}")

    logger.info(f"[FERC] {len(results)} relevant filings found in last {days_back} days")
    return results


def fetch_ferc_rss(days_back: int = 7) -> list[dict]:
    """
    Fetch FERC news RSS as a fallback signal source.
    """
    # FERC Electric News RSS
    rss_urls = [
        "https://www.ferc.gov/news-events/news?type=all&feed=rss",
    ]
    items = []
    for url in rss_urls:
        try:
            import feedparser
            feed = feedparser.parse(url)
            cutoff = datetime.now() - timedelta(days=days_back)
            for entry in feed.entries:
                pub = entry.get("published_parsed")
                if pub:
                    pub_dt = datetime(*pub[:6])
                    if pub_dt < cutoff:
                        continue
                items.append({
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", ""),
                    "published": entry.get("published", ""),
                    "source": "FERC News",
                })
        except Exception as e:
            logger.warning(f"[FERC RSS] Error: {e}")

    return items


def run_poller(push_to_airtable: bool = True) -> dict:
    """Poll FERC for new grid infrastructure signals."""
    filings = search_ferc_filings(days_back=7)
    rss_items = fetch_ferc_rss(days_back=7)

    signals_pushed = 0
    if push_to_airtable and (filings or rss_items):
        from storage.airtable import get_client
        at = get_client()

        for f in filings:
            if not f.get("filer_name"):
                continue
            at.insert_signal(
                signal_type="ferc_filing",
                source="FERC eLibrary",
                company_name=f["filer_name"],
                sector="Power & Grid Infrastructure",
                signal_date=f.get("filed_date", datetime.now().strftime("%Y-%m-%d")),
                raw_content=(
                    f"Docket: {f['docket_number']} | "
                    f"Type: {f['docket_type']} | "
                    f"Description: {f['filing_description'][:500]}"
                ),
                heat_score=15.0,  # FERC = early signal, low base score
                notes=f"Keyword match: {f['matched_keyword']}",
            )
            signals_pushed += 1

        for item in rss_items[:10]:
            at.insert_signal(
                signal_type="ferc_news",
                source="FERC News RSS",
                company_name="FERC / Grid Sector",
                sector="Power & Grid Infrastructure",
                signal_date=item.get("published", datetime.now().strftime("%Y-%m-%d")),
                raw_content=f"{item['title']}\n\n{item['summary'][:1000]}",
                heat_score=10.0,
                notes=item.get("link", ""),
            )
            signals_pushed += 1

    return {
        "ferc_filings": len(filings),
        "rss_items": len(rss_items),
        "signals_pushed": signals_pushed,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import json
    result = run_poller(push_to_airtable=False)
    print(json.dumps(result, indent=2))
