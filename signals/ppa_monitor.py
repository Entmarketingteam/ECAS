"""
signals/ppa_monitor.py
Power Purchase Agreement (PPA) Signal Monitor.

PPAs are tier-1 EPC demand signals: when a developer signs a PPA, they need
to build the plant — which means hiring EPC contractors within 3-6 months.

This monitor runs two complementary strategies:

1. RSS BOOST: Re-scores recent rss_news signals already in Airtable.
   Any signal containing PPA keywords gets a +15 confidence_score boost
   and a note marking it as a PPA signal. This surfaces buried PPA news
   that scored below threshold because it lacked capex keywords.

2. DIRECT RSS POLL: Polls PPA-focused RSS feeds (separate from the
   existing rss_aggregator.py feeds) and inserts high-scoring PPA articles
   as "ppa_announcement" signal_type signals with elevated base scores.

Signal type: "ppa_announcement"
Runs every 12h via scheduler.
"""

import logging
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import TARGET_SECTORS

logger = logging.getLogger(__name__)

# ── PPA detection keywords ─────────────────────────────────────────────────────
PPA_KEYWORDS = [
    "power purchase agreement",
    "ppa",
    "offtake agreement",
    "long-term contract",
    "energy supply agreement",
    "virtual power purchase agreement",
    "vppa",
    "merchant agreement",
    "energy offtake",
    "renewable energy credit",
    "rec agreement",
    "corporate ppa",
    "utility ppa",
    "15-year",
    "20-year",
    "25-year",  # Long-term agreements typical of PPAs
]

# Terms that confirm this is a new project (not just commentary)
PROJECT_SIGNALS = [
    "signed", "announced", "awarded", "executed",
    "finalized", "closed", "entered into",
    "will build", "to develop", "construction to begin",
    "groundbreaking", "financial close", "reaches financial",
    "megawatt", "mw", "gw", "gigawatt",
]

# PPA-specific RSS feeds — distinct from rss_aggregator.py feeds
PPA_RSS_FEEDS = [
    {
        "name": "PV Magazine USA",
        "url": "https://www.pv-magazine-usa.com/feed/",
        "sector": "Power & Grid Infrastructure",
        "base_score": 12.0,
    },
    {
        "name": "POWER Magazine",
        "url": "https://www.powermag.com/feed/",
        "sector": "Power & Grid Infrastructure",
        "base_score": 10.0,
    },
    {
        "name": "Energy Monitor",
        "url": "https://www.energymonitor.ai/feed/",
        "sector": "Power & Grid Infrastructure",
        "base_score": 10.0,
    },
    {
        "name": "Canary Media",
        "url": "https://www.canarymedia.com/rss",
        "sector": "Power & Grid Infrastructure",
        "base_score": 10.0,
    },
    {
        "name": "Greentech Media",
        "url": "https://www.greentechmedia.com/articles/feed",
        "sector": "Power & Grid Infrastructure",
        "base_score": 10.0,
    },
    {
        "name": "Nuclear Energy Institute",
        "url": "https://www.nei.org/rss/news",
        "sector": "Nuclear & Critical Minerals",
        "base_score": 12.0,
    },
]

# Score boost applied to existing Airtable signals when PPA keywords found
PPA_BOOST_POINTS = 15.0

# Only boost signals from the last N days (avoid re-boosting old stale signals)
BOOST_LOOKBACK_DAYS = 7

# Minimum base score an article needs to be inserted as a PPA signal
MIN_PPA_ARTICLE_SCORE = 8.0


def _has_ppa_content(text: str) -> tuple[bool, list[str]]:
    """
    Check if text contains PPA-relevant keywords.
    Returns (is_ppa, matched_keywords).
    """
    text_lower = text.lower()
    matched = [kw for kw in PPA_KEYWORDS if kw in text_lower]
    return bool(matched), matched


def _has_project_signal(text: str) -> bool:
    """Check if text also contains signals that this is a real project (not analysis)."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in PROJECT_SIGNALS)


def _score_ppa_article(title: str, summary: str, sector: str, base_score: float) -> float:
    """
    Score a PPA article for Airtable insertion.
    Higher score = clearer signal that an EPC is about to be needed.
    """
    text = (title + " " + summary).lower()
    score = base_score

    # PPA keyword matches
    is_ppa, matched_kws = _has_ppa_content(text)
    if is_ppa:
        score += len(matched_kws) * 3.0

    # Project action signals
    if _has_project_signal(text):
        score += 5.0

    # Sector keyword matches
    for kw in TARGET_SECTORS.get(sector, {}).get("keywords", [])[:10]:
        if kw.lower() in text:
            score += 2.0

    # Dollar amounts
    dollar_matches = re.findall(r"\$[\d,.]+ ?(?:billion|million|b\b|m\b)", text, re.IGNORECASE)
    for m in dollar_matches:
        if "billion" in m.lower():
            score += 12.0
        else:
            score += 4.0

    # MW/GW capacity mentions
    mw_matches = re.findall(r"[\d,]+\s*(?:mw|megawatt|gw|gigawatt)", text, re.IGNORECASE)
    score += min(len(mw_matches) * 3.0, 15.0)

    return min(round(score, 1), 100.0)


def _parse_feed_date(entry) -> str:
    """Extract YYYY-MM-DD from an RSS entry."""
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
        return True
    try:
        return datetime(*pub[:6]) >= cutoff
    except Exception:
        return True


def poll_ppa_feeds(hours_back: int = 48) -> list[dict]:
    """
    Poll PPA-focused RSS feeds for new articles.
    Only returns articles with meaningful PPA content.
    """
    try:
        import feedparser
    except ImportError:
        logger.error("[PPA] feedparser not installed — run: pip install feedparser")
        return []

    cutoff = datetime.now() - timedelta(hours=hours_back)
    articles = []

    for feed_cfg in PPA_RSS_FEEDS:
        name = feed_cfg["name"]
        url = feed_cfg["url"]
        sector = feed_cfg["sector"]
        base_score = feed_cfg["base_score"]

        try:
            feed = feedparser.parse(url)
            if not feed.entries:
                logger.info(f"[PPA RSS] {name}: 0 entries (feed may be unavailable)")
                continue

            count = 0
            for entry in feed.entries:
                if not _is_recent(entry, cutoff):
                    continue

                title = entry.get("title", "")
                summary = entry.get("summary", entry.get("description", ""))
                summary_clean = re.sub(r"<[^>]+>", "", summary)
                full_text = title + " " + summary_clean

                # Only include articles with PPA content OR high base relevance
                is_ppa, matched_kws = _has_ppa_content(full_text)
                score = _score_ppa_article(title, summary_clean, sector, base_score)

                if score < MIN_PPA_ARTICLE_SCORE and not is_ppa:
                    continue

                articles.append({
                    "source": name,
                    "title": title,
                    "summary": summary_clean[:2000],
                    "link": entry.get("link", ""),
                    "published_date": _parse_feed_date(entry),
                    "sector": sector,
                    "heat_score": score,
                    "ppa_keywords": matched_kws,
                    "has_ppa": is_ppa,
                })
                count += 1

            logger.info(f"[PPA RSS] {name}: {count} relevant articles")

        except Exception as e:
            logger.warning(f"[PPA RSS] Error polling {name}: {e}")

    articles.sort(key=lambda x: x["heat_score"], reverse=True)
    logger.info(f"[PPA RSS] {len(articles)} total PPA-relevant articles")
    return articles


def boost_existing_ppa_signals(at) -> int:
    """
    Scan recent rss_news signals in Airtable for PPA keywords.
    Boost confidence_score by PPA_BOOST_POINTS for matches.
    Returns count of boosted records.
    """
    cutoff_date = (datetime.utcnow() - timedelta(days=BOOST_LOOKBACK_DAYS)).strftime(
        "%Y-%m-%dT00:00:00.000Z"
    )

    try:
        records = at._get("signals_raw", {
            "filterByFormula": (
                f"AND({{signal_type}}='rss_news', {{captured_at}} >= '{cutoff_date}', "
                f"NOT({{processed}}))"
            ),
            "maxRecords": 100,
            "sort[0][field]": "captured_at",
            "sort[0][direction]": "desc",
        })
    except Exception as e:
        logger.warning(f"[PPA Boost] Failed to fetch Airtable records: {e}")
        return 0

    boosted = 0
    for record in records:
        fields = record.get("fields", {})
        raw_text = fields.get("raw_text", "")
        current_score = float(fields.get("confidence_score", 0) or 0)
        existing_notes = fields.get("notes", "") or ""

        # Skip if already marked as PPA signal (avoid double-boosting)
        if "PPA signal detected" in existing_notes:
            continue

        is_ppa, matched_kws = _has_ppa_content(raw_text)
        if not is_ppa:
            continue

        new_score = min(current_score + PPA_BOOST_POINTS, 100.0)
        boost_note = f"PPA signal detected: {', '.join(matched_kws[:3])}"
        updated_notes = f"{existing_notes}\n{boost_note}".strip() if existing_notes else boost_note

        try:
            at._patch("signals_raw", record["id"], {
                "confidence_score": round(new_score, 1),
                "notes": updated_notes[:10000],
            })
            boosted += 1
            logger.info(
                f"[PPA Boost] Boosted signal {record['id']}: "
                f"{current_score} → {new_score} | Keywords: {matched_kws[:3]}"
            )
        except Exception as e:
            logger.warning(f"[PPA Boost] Failed to patch record {record['id']}: {e}")

    logger.info(f"[PPA Boost] {boosted} existing signals boosted")
    return boosted


def _extract_company(title: str, summary: str) -> str:
    """Best-effort company extraction from article text."""
    text = (title + " " + summary[:200]).lower()
    for sector_cfg in TARGET_SECTORS.values():
        for kw in sector_cfg.get("keywords", []):
            if kw.lower() in text and len(kw) > 5:
                return kw.title()
    return ""


def run_monitor(push_to_airtable: bool = True) -> dict:
    """
    Run PPA monitor:
    1. Boost existing rss_news signals with PPA keywords
    2. Poll dedicated PPA RSS feeds and insert new signals

    Returns dict with stats.
    """
    boosted = 0
    articles_found = 0
    signals_pushed = 0

    at = None
    if push_to_airtable:
        try:
            from storage.airtable import get_client
            at = get_client()
        except Exception as e:
            logger.error(f"[PPA Monitor] Airtable client error: {e}")
            push_to_airtable = False

    # Step 1: Boost existing signals
    if push_to_airtable and at:
        boosted = boost_existing_ppa_signals(at)

    # Step 2: Poll PPA-focused RSS feeds
    articles = poll_ppa_feeds(hours_back=48)
    articles_found = len(articles)

    # Step 3: Push high-scoring PPA articles to Airtable
    if push_to_airtable and at and articles:
        top_articles = [a for a in articles if a["heat_score"] >= MIN_PPA_ARTICLE_SCORE][:30]

        for article in top_articles:
            company = _extract_company(article["title"], article["summary"])
            ppa_kws = article.get("ppa_keywords", [])
            ppa_note = f"PPA keywords: {', '.join(ppa_kws[:5])}" if ppa_kws else ""
            notes_parts = [article.get("link", ""), ppa_note]
            notes = " | ".join(p for p in notes_parts if p)

            try:
                # Use sector label fallback instead of RSS feed name to avoid
                # polluting signals table with publisher names as companies.
                company_name = company or f"{article['sector']} Signal"
                at.insert_signal(
                    signal_type="ppa_announcement",
                    source=article["source"],
                    company_name=company_name,
                    sector=article["sector"],
                    signal_date=article["published_date"],
                    raw_content=f"{article['title']}\n\n{article['summary']}",
                    heat_score=article["heat_score"],
                    notes=notes,
                )
                signals_pushed += 1
            except Exception as e:
                logger.warning(f"[PPA Monitor] Airtable insert failed: {e}")

    return {
        "articles_found": articles_found,
        "signals_pushed": signals_pushed,
        "existing_signals_boosted": boosted,
        "feeds_polled": len(PPA_RSS_FEEDS),
        "top_headlines": [
            {
                "title": a["title"],
                "score": a["heat_score"],
                "source": a["source"],
                "has_ppa": a["has_ppa"],
            }
            for a in articles[:5]
        ],
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import json
    result = run_monitor(push_to_airtable=False)
    print(json.dumps(result, indent=2))
