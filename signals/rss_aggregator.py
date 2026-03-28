"""
signals/rss_aggregator.py
Aggregates grid infrastructure and defense news from RSS feeds.
Filters for capex signals (utility capex announcements, grid investment news).
Pushes to Airtable signals_raw.
"""

import logging
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import RSS_FEEDS, TARGET_SECTORS

logger = logging.getLogger(__name__)

# Keywords that indicate capital expenditure / vendor opportunity
CAPEX_KEYWORDS = [
    "billion", "million", "capex", "capital expenditure", "investment",
    "awarded", "contract", "grid upgrade", "transmission expansion",
    "substation", "interconnection", "modernization", "infrastructure",
    "iija", "inflation reduction act", "doe grant", "federal funding",
    "rate case", "integrated resource plan", "irp", "rfo", "rfp",
    "solicitation", "procurement", "epc", "engineering procurement",
    "construction contract", "expansion plan", "growth plan",
]

# Keywords that indicate a vendor opportunity (more specific)
HIGH_VALUE_KEYWORDS = [
    "billion dollar", "$1b", "$2b", "$3b", "$5b", "$10b",
    "transmission project", "grid modernization project",
    "new substation", "transmission line contract",
    "epc contract awarded", "construction begins",
]


def _score_article(title: str, summary: str, sector: str) -> float:
    """
    Score an article's relevance as a capex signal (0-100).
    Higher = more relevant to ECAS targets.
    """
    text = (title + " " + summary).lower()
    score = 0.0

    # Base sector keyword matches
    for kw in TARGET_SECTORS.get(sector, {}).get("keywords", [])[:10]:
        if kw.lower() in text:
            score += 3.0

    # Capex keyword matches
    for kw in CAPEX_KEYWORDS:
        if kw.lower() in text:
            score += 2.0

    # High-value keyword matches (bonus)
    for kw in HIGH_VALUE_KEYWORDS:
        if kw.lower() in text:
            score += 10.0

    # Dollar amount extraction
    dollar_matches = re.findall(r"\$[\d,.]+ ?(?:billion|million|b\b|m\b)", text, re.IGNORECASE)
    for m in dollar_matches:
        if "billion" in m.lower() or "b" in m.lower().split("$")[-1][:3]:
            score += 15.0
        else:
            score += 5.0

    return min(score, 100.0)


def _parse_feed_date(entry) -> str:
    """Extract a YYYY-MM-DD date string from an RSS entry."""
    pub = entry.get("published_parsed") or entry.get("updated_parsed")
    if pub:
        try:
            return datetime(*pub[:3]).strftime("%Y-%m-%d")
        except Exception:
            pass
    return datetime.now().strftime("%Y-%m-%d")


def _is_recent(entry, cutoff: datetime) -> bool:
    pub = entry.get("published_parsed") or entry.get("updated_parsed")
    if not pub:
        return True  # Include if we can't parse
    try:
        return datetime(*pub[:6]) >= cutoff
    except Exception:
        return True


def poll_feeds(hours_back: int = 48) -> list[dict]:
    """Poll all configured RSS feeds and return scored articles."""
    try:
        import feedparser
    except ImportError:
        logger.error("[RSS] feedparser not installed — run: pip install feedparser")
        return []

    cutoff = datetime.now() - timedelta(hours=hours_back)
    articles = []

    for feed_cfg in RSS_FEEDS:
        name = feed_cfg["name"]
        url = feed_cfg["url"]
        sector = feed_cfg["sector"]

        try:
            feed = feedparser.parse(url)
            count = 0
            for entry in feed.entries:
                if not _is_recent(entry, cutoff):
                    continue

                title = entry.get("title", "")
                summary = entry.get("summary", entry.get("description", ""))
                # Strip HTML tags from summary
                summary_clean = re.sub(r"<[^>]+>", "", summary)

                score = _score_article(title, summary_clean, sector)
                if score < 5.0:
                    continue  # Skip irrelevant articles

                articles.append({
                    "source": name,
                    "title": title,
                    "summary": summary_clean[:2000],
                    "link": entry.get("link", ""),
                    "published_date": _parse_feed_date(entry),
                    "sector": sector,
                    "heat_score": round(score, 1),
                })
                count += 1

            logger.info(f"[RSS] {name}: {count} relevant articles")

        except Exception as e:
            logger.warning(f"[RSS] Error polling {name}: {e}")

    # Sort by score descending
    articles.sort(key=lambda x: x["heat_score"], reverse=True)
    logger.info(f"[RSS] {len(articles)} total relevant articles")
    return articles


def run_aggregator(push_to_airtable: bool = True) -> dict:
    """Poll RSS feeds and push top articles to Airtable."""
    articles = poll_feeds(hours_back=48)

    pushed = 0
    if push_to_airtable and articles:
        from storage.airtable import get_client
        at = get_client()

        # Only push articles with score >= 10
        top_articles = [a for a in articles if a["heat_score"] >= 10.0][:50]
        for article in top_articles:
            # Extract company name from title (best effort).
            # Fall back to sector label (e.g. "Power & Grid Infrastructure Signal")
            # rather than the RSS feed name — feed names like "Canary Media" or
            # "POWER Magazine" are not companies and pollute the signals table.
            company = _extract_company(article["title"], article["summary"])
            if not company:
                company = f"{article['sector']} Signal"
            at.insert_signal(
                signal_type="rss_news",
                source=article["source"],
                company_name=company,
                sector=article["sector"],
                signal_date=article["published_date"],
                raw_content=f"{article['title']}\n\n{article['summary']}",
                heat_score=article["heat_score"],
                notes=article.get("link", ""),
            )
            pushed += 1

    return {
        "articles_found": len(articles),
        "signals_pushed": pushed,
        "top_headlines": [
            {"title": a["title"], "score": a["heat_score"], "source": a["source"]}
            for a in articles[:5]
        ],
    }


def _extract_company(title: str, summary: str) -> str:
    """
    Best-effort company name extraction from headline.
    Returns first matched keyword company or empty string.
    """
    text = (title + " " + summary[:200]).lower()
    for sector_cfg in TARGET_SECTORS.values():
        for kw in sector_cfg.get("keywords", []):
            if kw.lower() in text and len(kw) > 5:
                return kw.title()
    return ""


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import json
    result = run_aggregator(push_to_airtable=False)
    print(json.dumps(result, indent=2))
