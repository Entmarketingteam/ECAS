"""
signals/doe_grants.py
DOE grant and loan signals — LPO, GDO, EERE + Grants.gov opportunities.

DOE conditional commitments and loan guarantees are tier-1 signals:
when DOE commits capital, EPC contractors get hired to build the project.

Polls 3 DOE RSS feeds + Grants.gov search API for DOE/EPA/DOD/DOT/DOI opportunities.
Stores in SQLite for deduplication. Top signals pushed to Airtable signals_raw.
Runs daily.
"""

import json
import logging
import re
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DB_PATH

logger = logging.getLogger(__name__)

SIGNAL_TYPE = "doe_grant"

# ── DOE RSS Feeds ─────────────────────────────────────────────────────────────
DOE_RSS_FEEDS = [
    {
        "name": "DOE Loan Programs Office",
        "url": "https://www.energy.gov/lpo/news/rss.xml",
        "agency": "DOE-LPO",
    },
    {
        "name": "DOE Grid Deployment Office",
        "url": "https://www.energy.gov/gdo/news/rss.xml",
        "agency": "DOE-GDO",
    },
    {
        "name": "DOE EERE",
        "url": "https://www.energy.gov/eere/news/rss.xml",
        "agency": "DOE-EERE",
    },
]

# ── Grants.gov Config ─────────────────────────────────────────────────────────
GRANTS_SEARCH_URL = "https://www.grants.gov/grantsws/rest/opportunities/search"

GRANTS_AGENCIES = ["DOE", "EPA", "DOD", "DOT", "DOI"]
GRANTS_KEYWORDS = [
    "infrastructure", "construction", "energy", "water",
    "defense", "grid", "transmission", "nuclear",
    "clean energy", "renewable", "hydrogen", "battery",
    "electric vehicle", "broadband", "resilience",
]

# ── Keyword Scoring ───────────────────────────────────────────────────────────
RSS_KEYWORD_SCORES = {
    "conditional commitment": 25.0,
    "loan guarantee": 22.0,
    "grant awarded": 20.0,
    "loan closed": 22.0,
    "funding opportunity announcement": 15.0,
    "foa": 15.0,
    "solicitation": 12.0,
    "request for proposals": 12.0,
    "notice of intent": 10.0,
    "billion": 18.0,
    "million": 8.0,
}

# ── Agency → Sector Mapping ──────────────────────────────────────────────────
AGENCY_SECTOR_MAP = {
    "DOE": "Power & Grid Infrastructure",
    "DOE-LPO": "Power & Grid Infrastructure",
    "DOE-GDO": "Power & Grid Infrastructure",
    "DOE-EERE": "Power & Grid Infrastructure",
    "EPA": "Water & Wastewater Infrastructure",
    "DOD": "Defense",
    "DOT": "Power & Grid Infrastructure",  # EV charging / transit infrastructure
    "DOI": "Nuclear & Critical Minerals",  # Critical minerals on federal lands
}

REQUEST_DELAY = 1.0  # seconds between requests


def _ensure_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS doe_grants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_id TEXT UNIQUE,
            title TEXT,
            description TEXT,
            source_name TEXT,
            agency TEXT,
            link TEXT,
            published_date TEXT,
            dollar_amount REAL,
            heat_score REAL,
            sector TEXT,
            scraped_at TEXT
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_doe_agency ON doe_grants(agency)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_doe_score ON doe_grants(heat_score)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_doe_date ON doe_grants(published_date)")
    conn.commit()
    conn.close()


def _extract_dollar_amount(text: str) -> float:
    """Extract the largest dollar amount mentioned in text."""
    amounts = []

    # Match patterns like "$1.5 billion", "$500 million", "$2.3B", "$100M"
    patterns = [
        (r"\$[\d,.]+ ?billion", 1_000_000_000),
        (r"\$[\d,.]+ ?b\b", 1_000_000_000),
        (r"\$[\d,.]+ ?million", 1_000_000),
        (r"\$[\d,.]+ ?m\b", 1_000_000),
        (r"\$[\d,]+(?:\.[\d]+)?", 1),  # Raw dollar amount
    ]

    text_lower = text.lower()
    for pattern, multiplier in patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for m in matches:
            num_str = re.sub(r"[^\d.]", "", m.split("$")[-1].split()[0] if "$" in m else m)
            try:
                val = float(num_str) * multiplier
                amounts.append(val)
            except (ValueError, IndexError):
                continue

    return max(amounts) if amounts else 0.0


def _score_rss_item(title: str, description: str, dollar_amount: float) -> float:
    """Score an RSS item based on keyword matches and dollar amounts."""
    text = (title + " " + description).lower()
    score = 5.0  # Base score for any DOE news item

    # Keyword scoring — take highest match
    best_kw_score = 0.0
    for keyword, kw_score in RSS_KEYWORD_SCORES.items():
        if keyword in text:
            best_kw_score = max(best_kw_score, kw_score)
    score += best_kw_score

    # Dollar amount bonus
    if dollar_amount >= 1_000_000_000:
        score += 15.0
    elif dollar_amount >= 100_000_000:
        score += 10.0
    elif dollar_amount >= 10_000_000:
        score += 5.0
    elif dollar_amount >= 1_000_000:
        score += 2.0

    return min(score, 60.0)


def _score_grant_opportunity(title: str, description: str, agency: str, dollar_amount: float) -> float:
    """Score a Grants.gov opportunity."""
    text = (title + " " + description).lower()
    score = 8.0  # Base score for a posted opportunity

    # Agency relevance
    if agency in ("DOE", "DOD"):
        score += 3.0
    elif agency in ("EPA", "DOT"):
        score += 2.0

    # Keyword matches from grants keywords
    infra_keywords = [
        "construction", "infrastructure", "grid", "transmission",
        "nuclear", "hydrogen", "battery", "water treatment",
        "defense facility", "military construction",
    ]
    for kw in infra_keywords:
        if kw in text:
            score += 2.0

    # Dollar amount bonus
    if dollar_amount >= 1_000_000_000:
        score += 15.0
    elif dollar_amount >= 100_000_000:
        score += 10.0
    elif dollar_amount >= 10_000_000:
        score += 5.0

    return min(score, 60.0)


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


def poll_doe_rss(days_back: int = 7) -> list[dict]:
    """Poll DOE RSS feeds for grant/loan announcements."""
    try:
        import feedparser
    except ImportError:
        logger.error("[DOE] feedparser not installed — run: pip install feedparser")
        return []

    cutoff = datetime.now() - timedelta(days=days_back)
    items = []

    for feed_cfg in DOE_RSS_FEEDS:
        name = feed_cfg["name"]
        url = feed_cfg["url"]
        agency = feed_cfg["agency"]
        sector = AGENCY_SECTOR_MAP.get(agency, "Power & Grid Infrastructure")

        try:
            time.sleep(REQUEST_DELAY)
            feed = feedparser.parse(url)
            if not feed.entries:
                logger.info(f"[DOE RSS] {name}: 0 entries")
                continue

            count = 0
            for entry in feed.entries:
                if not _is_recent(entry, cutoff):
                    continue

                title = entry.get("title", "")
                summary = entry.get("summary", entry.get("description", ""))
                summary_clean = re.sub(r"<[^>]+>", "", summary)
                link = entry.get("link", "")
                pub_date = _parse_feed_date(entry)

                # Use guid or link as unique ID
                guid = entry.get("id", "") or entry.get("guid", "") or link
                if not guid:
                    continue

                dollar_amount = _extract_dollar_amount(title + " " + summary_clean)
                heat_score = _score_rss_item(title, summary_clean, dollar_amount)

                items.append({
                    "signal_id": f"doe-rss-{hash(guid) & 0xFFFFFFFF:08x}",
                    "title": title,
                    "description": summary_clean[:2000],
                    "source_name": name,
                    "agency": agency,
                    "link": link,
                    "published_date": pub_date,
                    "dollar_amount": dollar_amount,
                    "heat_score": heat_score,
                    "sector": sector,
                })
                count += 1

            logger.info(f"[DOE RSS] {name}: {count} items")

        except Exception as e:
            logger.warning(f"[DOE RSS] Error polling {name}: {e}")

    return items


def poll_grants_gov(days_back: int = 30) -> list[dict]:
    """
    Poll Grants.gov search API for infrastructure-related federal opportunities.
    Filters by target agencies and keywords.
    """
    items = []

    for agency in GRANTS_AGENCIES:
        for keyword in GRANTS_KEYWORDS[:5]:  # Top 5 keywords per agency to limit requests
            params = {
                "keyword": keyword,
                "agency": agency,
                "oppStatus": "posted",
                "rows": 25,
                "sortBy": "openDate|desc",
            }

            try:
                time.sleep(REQUEST_DELAY)
                resp = requests.get(GRANTS_SEARCH_URL, params=params, timeout=30)

                if resp.status_code == 200:
                    data = resp.json()
                else:
                    # Grants.gov API can be flaky — log and continue
                    logger.debug(f"[Grants.gov] {agency}/{keyword}: HTTP {resp.status_code}")
                    continue

                opportunities = data.get("oppHits", [])
                sector = AGENCY_SECTOR_MAP.get(agency, "Power & Grid Infrastructure")

                for opp in opportunities:
                    opp_id = str(opp.get("id", "")) or str(opp.get("number", ""))
                    if not opp_id:
                        continue

                    title = opp.get("title", "")
                    description = opp.get("description", "") or opp.get("synopsis", "") or ""
                    description_clean = re.sub(r"<[^>]+>", "", description)
                    link = f"https://www.grants.gov/search-results-detail/{opp_id}"
                    open_date = opp.get("openDate", "") or ""
                    close_date = opp.get("closeDate", "") or ""

                    # Extract award ceiling as dollar amount
                    award_ceiling = opp.get("awardCeiling", 0) or 0
                    try:
                        dollar_amount = float(award_ceiling)
                    except (ValueError, TypeError):
                        dollar_amount = _extract_dollar_amount(title + " " + description_clean)

                    heat_score = _score_grant_opportunity(title, description_clean, agency, dollar_amount)

                    items.append({
                        "signal_id": f"grants-{agency}-{opp_id}",
                        "title": title,
                        "description": description_clean[:2000],
                        "source_name": f"Grants.gov / {agency}",
                        "agency": agency,
                        "link": link,
                        "published_date": open_date[:10] if open_date else datetime.now().strftime("%Y-%m-%d"),
                        "dollar_amount": dollar_amount,
                        "heat_score": heat_score,
                        "sector": sector,
                    })

            except requests.RequestException as e:
                logger.warning(f"[Grants.gov] Error for {agency}/{keyword}: {e}")
            except json.JSONDecodeError as e:
                logger.warning(f"[Grants.gov] JSON error for {agency}/{keyword}: {e}")

    # Deduplicate by signal_id
    seen = set()
    unique = []
    for item in items:
        if item["signal_id"] not in seen:
            seen.add(item["signal_id"])
            unique.append(item)

    logger.info(f"[Grants.gov] {len(unique)} unique opportunities from {len(GRANTS_AGENCIES)} agencies")
    return unique


def run(push_to_airtable: bool = True) -> dict:
    """
    Run DOE grant signal collector.
    1. Poll DOE RSS feeds (LPO, GDO, EERE)
    2. Poll Grants.gov for federal infrastructure opportunities
    3. Deduplicate, store in SQLite
    4. Push top signals to Airtable

    Returns dict with stats.
    """
    _ensure_db(DB_PATH)

    # Collect from both sources
    rss_items = poll_doe_rss(days_back=7)
    grants_items = poll_grants_gov(days_back=30)

    all_items = rss_items + grants_items
    all_items.sort(key=lambda x: x["heat_score"], reverse=True)

    logger.info(f"[DOE] {len(rss_items)} RSS + {len(grants_items)} Grants.gov = {len(all_items)} total")

    # Store in SQLite
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    inserted = 0
    for item in all_items:
        try:
            c.execute("""
                INSERT OR IGNORE INTO doe_grants
                (signal_id, title, description, source_name, agency, link,
                 published_date, dollar_amount, heat_score, sector, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item["signal_id"], item["title"], item["description"],
                item["source_name"], item["agency"], item["link"],
                item["published_date"], item["dollar_amount"],
                item["heat_score"], item["sector"], datetime.now().isoformat(),
            ))
            if c.rowcount > 0:
                inserted += 1
        except sqlite3.Error as e:
            logger.warning(f"[DOE] DB error: {e}")
    conn.commit()
    conn.close()

    logger.info(f"[DOE] {inserted} new inserts to SQLite")

    # Push top signals to Airtable
    signals_pushed = 0
    if push_to_airtable and all_items:
        try:
            from storage.airtable import get_client
            at = get_client()
        except Exception as e:
            logger.error(f"[DOE] Airtable client error: {e}")
            at = None

        if at:
            top = [item for item in all_items if item["heat_score"] >= 12.0][:40]
            for item in top:
                dollar_str = ""
                if item["dollar_amount"] >= 1_000_000_000:
                    dollar_str = f"${item['dollar_amount'] / 1_000_000_000:.1f}B"
                elif item["dollar_amount"] >= 1_000_000:
                    dollar_str = f"${item['dollar_amount'] / 1_000_000:.1f}M"
                elif item["dollar_amount"] > 0:
                    dollar_str = f"${item['dollar_amount']:,.0f}"

                raw_content = (
                    f"{item['title']}\n\n"
                    f"Agency: {item['agency']}\n"
                    f"Source: {item['source_name']}\n"
                )
                if dollar_str:
                    raw_content += f"Amount: {dollar_str}\n"
                if item["description"]:
                    raw_content += f"\n{item['description'][:1000]}"

                try:
                    at.insert_signal(
                        signal_type=SIGNAL_TYPE,
                        source=item["source_name"],
                        company_name=item["agency"],
                        sector=item["sector"],
                        signal_date=item["published_date"],
                        raw_content=raw_content,
                        heat_score=item["heat_score"],
                        notes=item.get("link", ""),
                    )
                    signals_pushed += 1
                except Exception as e:
                    logger.warning(f"[DOE] Airtable insert failed: {e}")

            logger.info(f"[DOE] Pushed {signals_pushed} signals to Airtable")

    # Agency breakdown
    agency_counts: dict[str, int] = {}
    for item in all_items:
        ag = item.get("agency", "Unknown")
        agency_counts[ag] = agency_counts.get(ag, 0) + 1

    return {
        "rss_items": len(rss_items),
        "grants_items": len(grants_items),
        "total_items": len(all_items),
        "new_inserts": inserted,
        "signals_pushed": signals_pushed,
        "agency_breakdown": agency_counts,
        "top_items": [
            {
                "title": item["title"][:100],
                "agency": item["agency"],
                "score": item["heat_score"],
                "amount": item["dollar_amount"],
            }
            for item in all_items[:5]
        ],
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run(push_to_airtable=False)
    print(json.dumps(result, indent=2))
