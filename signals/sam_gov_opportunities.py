"""
signals/sam_gov_opportunities.py
Polls SAM.gov Opportunities API for pre-solicitation, sources sought, and early
notice types — the leading indicators that appear weeks/months before formal RFPs.
Deduplicates via SQLite. Pushes new signals to Airtable signals_raw.
"""

import json
import logging
import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DB_PATH

logger = logging.getLogger(__name__)

SAM_API_KEY = os.environ.get("SAM_GOV_API_KEY", "")
SAM_BASE_URL = "https://api.sam.gov/opportunities/v2/search"

# Notice types: p=pre-sol, s=sources sought, o=solicitation, r=combined, k=special
NOTICE_TYPES = "p,s,o,r,k"

# Heat scores by notice type — earlier signals score lower, formal RFPs higher
HEAT_SCORE_MAP = {
    "p": 15,   # Pre-solicitation
    "s": 20,   # Sources sought
    "o": 25,   # Solicitation
    "r": 30,   # Combined synopsis/solicitation
    "k": 10,   # Special notice
}

# ECAS sector search definitions: NAICS codes + keywords → sector name
SECTOR_SEARCHES = {
    "Power & Grid Infrastructure": {
        "naics": ["237130", "238210", "237110"],
        "keywords": ["transmission", "substation", "power line", "electrical contractor"],
    },
    "Data Center & AI Infrastructure": {
        "naics": ["236220", "238210"],
        "keywords": ["data center", "critical facility"],
    },
    "Water & Wastewater Infrastructure": {
        "naics": ["237110", "237120"],
        "keywords": ["water treatment", "wastewater", "CWSRF"],
    },
    "Defense": {
        "naics": ["236220", "237990"],
        "keywords": ["MILCON", "military construction", "facility"],
    },
    "Industrial & Manufacturing Facilities": {
        "naics": ["236210", "237990"],
        "keywords": ["manufacturing", "semiconductor", "battery"],
    },
    "Nuclear & Critical Minerals": {
        "naics": ["237130", "236210"],
        "keywords": ["nuclear", "SMR", "reactor"],
    },
}

RATE_LIMIT_DELAY = 0.5  # seconds between SAM.gov requests


def _ensure_db(db_path: Path) -> None:
    """Create SQLite table for deduplication."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS sam_gov_opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            notice_id TEXT UNIQUE,
            title TEXT,
            notice_type TEXT,
            posted_date TEXT,
            naics_code TEXT,
            matched_sector TEXT,
            set_aside_type TEXT,
            response_deadline TEXT,
            buying_agency TEXT,
            scraped_at TEXT
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_sam_sector ON sam_gov_opportunities(matched_sector)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_sam_date ON sam_gov_opportunities(posted_date)")
    conn.commit()
    conn.close()


def _search_sam(params: dict) -> dict:
    """Execute a single SAM.gov Opportunities API search."""
    headers = {}
    if SAM_API_KEY:
        params["api_key"] = SAM_API_KEY
    try:
        time.sleep(RATE_LIMIT_DELAY)
        resp = requests.get(SAM_BASE_URL, params=params, headers=headers, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"[SAM.gov] API error: {e}")
        return {}


def _match_sector(naics_code: str, title: str, description: str) -> str | None:
    """Match an opportunity to an ECAS sector by NAICS code or keyword."""
    text = f"{title} {description}".lower()

    # Try NAICS match first
    for sector_name, cfg in SECTOR_SEARCHES.items():
        if naics_code in cfg["naics"]:
            return sector_name

    # Fall back to keyword match
    for sector_name, cfg in SECTOR_SEARCHES.items():
        for kw in cfg["keywords"]:
            if kw.lower() in text:
                return sector_name

    return None


def _is_new(notice_id: str, db_path: Path) -> bool:
    """Check if a notice_id already exists in SQLite."""
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    c.execute("SELECT 1 FROM sam_gov_opportunities WHERE notice_id = ?", (notice_id,))
    exists = c.fetchone() is not None
    conn.close()
    return not exists


def _store_opportunity(opp: dict, db_path: Path) -> bool:
    """Insert opportunity into SQLite. Returns True if new (not duplicate)."""
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    try:
        c.execute("""
            INSERT OR IGNORE INTO sam_gov_opportunities
            (notice_id, title, notice_type, posted_date, naics_code, matched_sector,
             set_aside_type, response_deadline, buying_agency, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            opp["notice_id"],
            opp["title"],
            opp["notice_type"],
            opp["posted_date"],
            opp["naics_code"],
            opp["matched_sector"],
            opp["set_aside_type"],
            opp["response_deadline"],
            opp["buying_agency"],
            datetime.now().isoformat(),
        ))
        inserted = c.rowcount > 0
        conn.commit()
    except sqlite3.Error as e:
        logger.warning(f"[SAM.gov] DB error: {e}")
        inserted = False
    finally:
        conn.close()
    return inserted


def _build_raw_text(opp: dict) -> str:
    """Build raw_text for Airtable signal from opportunity fields."""
    parts = [
        f"Title: {opp['title']}",
        f"Notice Type: {opp['notice_type_label']}",
        f"NAICS: {opp['naics_code']}",
        f"Agency: {opp['buying_agency']}",
    ]
    if opp.get("set_aside_type"):
        parts.append(f"Set-Aside: {opp['set_aside_type']}")
    if opp.get("response_deadline"):
        parts.append(f"Response Deadline: {opp['response_deadline']}")
    if opp.get("description"):
        parts.append(f"Description: {opp['description'][:2000]}")
    if opp.get("url"):
        parts.append(f"URL: {opp['url']}")
    return "\n".join(parts)


def _push_to_airtable(opp: dict) -> str | None:
    """Push a single opportunity signal to Airtable signals_raw."""
    from storage.airtable import get_client

    at = get_client()
    heat = HEAT_SCORE_MAP.get(opp["notice_type"], 15)

    # company_name: set-aside org if available, else buying agency
    company = opp.get("set_aside_org") or opp.get("buying_agency") or "Federal"

    record_id = at.insert_signal(
        signal_type="sam_gov_opportunity",
        source=f"SAM.gov / {opp.get('buying_agency', 'Federal')}",
        company_name=company,
        sector=opp["matched_sector"],
        signal_date=opp.get("posted_date", "")[:10],
        raw_content=_build_raw_text(opp),
        heat_score=float(heat),
        notes=opp.get("url", ""),
    )
    return record_id


# Map SAM.gov noticeType codes to labels
NOTICE_TYPE_LABELS = {
    "p": "Pre-Solicitation",
    "s": "Sources Sought",
    "o": "Solicitation",
    "r": "Combined Synopsis/Solicitation",
    "k": "Special Notice",
}


def _collect_opportunities() -> list[dict]:
    """Search SAM.gov across all ECAS sectors and return parsed opportunities."""
    _ensure_db(DB_PATH)

    lookback_date = (datetime.now() - timedelta(days=30)).strftime("%m/%d/%Y")
    today = datetime.now().strftime("%m/%d/%Y")

    all_opps: list[dict] = []
    seen_ids: set[str] = set()

    for sector_name, cfg in SECTOR_SEARCHES.items():
        # Search by NAICS codes
        for naics in cfg["naics"]:
            params = {
                "postedFrom": lookback_date,
                "postedTo": today,
                "ncode": naics,
                "ptype": NOTICE_TYPES,
                "limit": 100,
                "offset": 0,
            }
            logger.info(f"[SAM.gov] Searching NAICS {naics} for {sector_name}")
            data = _search_sam(params)

            for item in data.get("opportunitiesData", []):
                notice_id = item.get("noticeId", "")
                if not notice_id or notice_id in seen_ids:
                    continue
                seen_ids.add(notice_id)

                title = item.get("title", "") or ""
                description = item.get("description", "") or ""
                naics_code = item.get("naicsCode", naics) or naics
                notice_type = item.get("type", "") or ""
                posted = item.get("postedDate", "") or ""
                deadline = item.get("responseDeadLine", "") or ""
                agency = item.get("fullParentPathName", "") or item.get("department", "") or ""
                set_aside = item.get("typeOfSetAside", "") or ""
                set_aside_org = item.get("organizationName", "") or ""
                opp_url = f"https://sam.gov/opp/{notice_id}/view" if notice_id else ""

                matched = _match_sector(naics_code, title, description) or sector_name

                all_opps.append({
                    "notice_id": notice_id,
                    "title": title,
                    "description": description,
                    "notice_type": notice_type.lower(),
                    "notice_type_label": NOTICE_TYPE_LABELS.get(notice_type.lower(), notice_type),
                    "posted_date": posted,
                    "response_deadline": deadline,
                    "naics_code": naics_code,
                    "matched_sector": matched,
                    "buying_agency": agency,
                    "set_aside_type": set_aside,
                    "set_aside_org": set_aside_org,
                    "url": opp_url,
                })

        # Search by keywords
        for keyword in cfg["keywords"]:
            params = {
                "postedFrom": lookback_date,
                "postedTo": today,
                "title": keyword,
                "ptype": NOTICE_TYPES,
                "limit": 100,
                "offset": 0,
            }
            logger.info(f"[SAM.gov] Searching keyword '{keyword}' for {sector_name}")
            data = _search_sam(params)

            for item in data.get("opportunitiesData", []):
                notice_id = item.get("noticeId", "")
                if not notice_id or notice_id in seen_ids:
                    continue
                seen_ids.add(notice_id)

                title = item.get("title", "") or ""
                description = item.get("description", "") or ""
                naics_code = item.get("naicsCode", "") or ""
                notice_type = item.get("type", "") or ""
                posted = item.get("postedDate", "") or ""
                deadline = item.get("responseDeadLine", "") or ""
                agency = item.get("fullParentPathName", "") or item.get("department", "") or ""
                set_aside = item.get("typeOfSetAside", "") or ""
                set_aside_org = item.get("organizationName", "") or ""
                opp_url = f"https://sam.gov/opp/{notice_id}/view" if notice_id else ""

                matched = _match_sector(naics_code, title, description) or sector_name

                all_opps.append({
                    "notice_id": notice_id,
                    "title": title,
                    "description": description,
                    "notice_type": notice_type.lower(),
                    "notice_type_label": NOTICE_TYPE_LABELS.get(notice_type.lower(), notice_type),
                    "posted_date": posted,
                    "response_deadline": deadline,
                    "naics_code": naics_code,
                    "matched_sector": matched,
                    "buying_agency": agency,
                    "set_aside_type": set_aside,
                    "set_aside_org": set_aside_org,
                    "url": opp_url,
                })

    return all_opps


def run() -> dict:
    """
    Main entry point — called by scheduler.py.
    Collects SAM.gov opportunities, deduplicates via SQLite, pushes new ones to Airtable.
    """
    _ensure_db(DB_PATH)

    logger.info("[SAM.gov] Starting opportunity collection")
    all_opps = _collect_opportunities()
    logger.info(f"[SAM.gov] Found {len(all_opps)} total opportunities across all sectors")

    new_count = 0
    pushed_count = 0
    sector_counts: dict[str, int] = {}

    for opp in all_opps:
        sector = opp["matched_sector"]
        sector_counts[sector] = sector_counts.get(sector, 0) + 1

        # Deduplicate via SQLite
        if not _store_opportunity(opp, DB_PATH):
            continue

        new_count += 1

        # Push new opportunities to Airtable
        try:
            record_id = _push_to_airtable(opp)
            if record_id:
                pushed_count += 1
        except Exception as e:
            logger.error(f"[SAM.gov] Airtable push error for {opp['notice_id']}: {e}")

    logger.info(
        f"[SAM.gov] Done: {len(all_opps)} total | {new_count} new | "
        f"{pushed_count} pushed to Airtable | sectors: {sector_counts}"
    )

    return {
        "total_opportunities": len(all_opps),
        "new_opportunities": new_count,
        "pushed_to_airtable": pushed_count,
        "sector_breakdown": sector_counts,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run()
    print(json.dumps(result, indent=2))
