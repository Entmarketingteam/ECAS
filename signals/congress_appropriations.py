"""
signals/congress_appropriations.py
Congressional appropriations and infrastructure bills.

Bills moving through Congress are leading indicators of infrastructure spend.
When an appropriations bill passes committee or a chamber, EPCs start positioning
3-6 months before funds actually flow.

API: Congress.gov API (free, requires CONGRESS_API_KEY env var).
Stores in SQLite for deduplication. Top signals pushed to Airtable signals_raw.
Runs weekly (Congress moves slowly).
"""

import json
import logging
import os
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

SIGNAL_TYPE = "congress_bill"
CONGRESS_API_BASE = "https://api.congress.gov/v3"
CONGRESS_API_KEY = os.environ.get("CONGRESS_API_KEY", "")

# Current Congress number (119th Congress: Jan 2025 - Jan 2027)
CURRENT_CONGRESS = 119

# Bill types to search
BILL_TYPES = ["hr", "s", "hjres", "sjres"]

# Keywords to search for infrastructure-relevant bills
SEARCH_KEYWORDS = [
    "infrastructure",
    "construction",
    "military construction",
    "MILCON",
    "water infrastructure",
    "clean water",
    "drinking water",
    "energy",
    "grid",
    "transmission",
    "nuclear",
    "data center",
    "semiconductor",
    "CHIPS",
    "critical mineral",
    "mining",
    "appropriations",
]

# ── Bill Status → Heat Score Mapping ─────────────────────────────────────────
# Higher score = bill more likely to become law = more likely to unlock EPC spend
STATUS_SCORES = {
    "became_law": 30.0,
    "signed_by_president": 30.0,
    "passed_both": 25.0,
    "passed_senate": 15.0,
    "passed_house": 15.0,
    "committee": 8.0,
    "introduced": 5.0,
}

# ── Keyword → Sector Mapping ─────────────────────────────────────────────────
SECTOR_KEYWORDS = {
    "Power & Grid Infrastructure": [
        "energy", "grid", "transmission", "electric", "power",
        "renewable", "solar", "wind", "battery", "storage",
        "utility", "electricity", "geothermal",
    ],
    "Nuclear & Critical Minerals": [
        "nuclear", "uranium", "critical mineral", "rare earth",
        "mining", "small modular reactor", "smr",
    ],
    "Water & Wastewater Infrastructure": [
        "water infrastructure", "clean water", "drinking water",
        "wastewater", "water treatment", "sewer", "stormwater",
        "lead service line", "pfas",
    ],
    "Defense": [
        "military construction", "milcon", "defense", "dod",
        "army corps", "naval", "air force", "space force",
    ],
    "Data Center & AI Infrastructure": [
        "data center", "semiconductor", "chips", "artificial intelligence",
        "broadband", "fiber", "digital infrastructure",
    ],
    "Industrial & Manufacturing Facilities": [
        "manufacturing", "industrial", "factory", "plant construction",
        "lng", "hydrogen", "ammonia", "petrochemical",
    ],
}

REQUEST_DELAY = 0.5  # Congress.gov rate limit: ~1000/hour


def _ensure_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS congress_bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_id TEXT UNIQUE,
            congress INTEGER,
            bill_number TEXT,
            bill_type TEXT,
            title TEXT,
            sponsor TEXT,
            latest_action TEXT,
            latest_action_date TEXT,
            policy_area TEXT,
            status_phase TEXT,
            heat_score REAL,
            sector TEXT,
            url TEXT,
            scraped_at TEXT
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_cong_score ON congress_bills(heat_score)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_cong_sector ON congress_bills(sector)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_cong_date ON congress_bills(latest_action_date)")
    conn.commit()
    conn.close()


def _determine_status_phase(latest_action: str) -> str:
    """Determine bill's progress phase from latest action text."""
    action_lower = (latest_action or "").lower()

    if any(kw in action_lower for kw in ["became public law", "signed by president", "became law"]):
        return "became_law"
    if "signed by president" in action_lower:
        return "signed_by_president"
    if any(kw in action_lower for kw in ["passed senate", "passed house", "agreed to in"]):
        # Check if it passed both chambers
        if "senate" in action_lower and "house" in action_lower:
            return "passed_both"
        if "passed senate" in action_lower:
            return "passed_senate"
        if "passed house" in action_lower or "agreed to in house" in action_lower:
            return "passed_house"
    if any(kw in action_lower for kw in [
        "referred to", "committee", "subcommittee", "markup", "reported",
        "ordered to be reported", "hearing",
    ]):
        return "committee"

    return "introduced"


def _determine_sector(title: str, policy_area: str, subjects: list[str] = None) -> str:
    """Map bill to ECAS sector based on title, policy area, and subjects."""
    text = (title + " " + (policy_area or "")).lower()
    if subjects:
        text += " " + " ".join(subjects).lower()

    # Score each sector by keyword matches
    sector_scores: dict[str, int] = {}
    for sector, keywords in SECTOR_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in text)
        if count > 0:
            sector_scores[sector] = count

    if sector_scores:
        return max(sector_scores, key=sector_scores.get)

    # Default: if it's appropriations, classify as Power & Grid
    if "appropriations" in text:
        return "Power & Grid Infrastructure"

    return "Power & Grid Infrastructure"


def _score_bill(status_phase: str, title: str, policy_area: str) -> float:
    """Score a bill based on its progress and relevance."""
    score = STATUS_SCORES.get(status_phase, 5.0)
    text = (title + " " + (policy_area or "")).lower()

    # Bonus for appropriations bills (contain specific dollar amounts)
    if "appropriations" in text or "appropriation" in text:
        score += 3.0

    # Bonus for infrastructure-specific language
    infra_terms = ["infrastructure", "construction", "capital improvement", "modernization"]
    for term in infra_terms:
        if term in text:
            score += 2.0

    # Dollar amount extraction from title
    dollar_matches = re.findall(r"\$[\d,.]+ ?(?:billion|million|trillion)", text, re.IGNORECASE)
    for m in dollar_matches:
        if "trillion" in m.lower():
            score += 15.0
        elif "billion" in m.lower():
            score += 10.0
        else:
            score += 3.0

    return min(score, 60.0)


def _api_get(endpoint: str, params: dict = None) -> dict:
    """Make a GET request to Congress.gov API."""
    if not CONGRESS_API_KEY:
        logger.error("[Congress] CONGRESS_API_KEY not set — register at api.congress.gov/sign-up")
        return {}

    url = f"{CONGRESS_API_BASE}{endpoint}"
    p = params.copy() if params else {}
    p["api_key"] = CONGRESS_API_KEY
    p["format"] = "json"

    try:
        time.sleep(REQUEST_DELAY)
        resp = requests.get(url, params=p, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logger.error(f"[Congress] API error for {endpoint}: {e}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"[Congress] JSON error for {endpoint}: {e}")
        return {}


def search_bills(keyword: str, limit: int = 25) -> list[dict]:
    """Search for bills by keyword in the current Congress."""
    data = _api_get("/bill", {
        "query": keyword,
        "limit": limit,
        "sort": "updateDate+desc",
    })

    bills_raw = data.get("bills", [])
    bills = []

    for b in bills_raw:
        congress = b.get("congress", CURRENT_CONGRESS)
        bill_type = b.get("type", "").lower()
        bill_number = b.get("number", "")
        bill_id = f"{congress}-{bill_type}{bill_number}"

        title = b.get("title", "")
        latest_action = b.get("latestAction", {})
        latest_action_text = latest_action.get("text", "") if isinstance(latest_action, dict) else str(latest_action)
        latest_action_date = latest_action.get("actionDate", "") if isinstance(latest_action, dict) else ""

        sponsor = ""
        sponsors = b.get("sponsors", [])
        if sponsors and isinstance(sponsors, list):
            s = sponsors[0] if isinstance(sponsors[0], dict) else {}
            sponsor = f"{s.get('firstName', '')} {s.get('lastName', '')}".strip()
            if s.get("party") and s.get("state"):
                sponsor += f" ({s['party']}-{s['state']})"

        policy_area = ""
        pa = b.get("policyArea", {})
        if isinstance(pa, dict):
            policy_area = pa.get("name", "")
        elif isinstance(pa, str):
            policy_area = pa

        status_phase = _determine_status_phase(latest_action_text)
        sector = _determine_sector(title, policy_area)
        heat_score = _score_bill(status_phase, title, policy_area)

        url = b.get("url", f"https://www.congress.gov/bill/{congress}th-congress/{bill_type}/{bill_number}")

        bills.append({
            "bill_id": bill_id,
            "congress": congress,
            "bill_number": f"{bill_type.upper()}{bill_number}",
            "bill_type": bill_type,
            "title": title,
            "sponsor": sponsor,
            "latest_action": latest_action_text,
            "latest_action_date": latest_action_date,
            "policy_area": policy_area,
            "status_phase": status_phase,
            "heat_score": heat_score,
            "sector": sector,
            "url": url,
        })

    return bills


def run(push_to_airtable: bool = True) -> dict:
    """
    Run Congressional appropriations signal collector.
    1. Search Congress.gov for infrastructure-relevant bills
    2. Score and classify by sector
    3. Deduplicate and store in SQLite
    4. Push top signals to Airtable

    Returns dict with stats.
    """
    if not CONGRESS_API_KEY:
        logger.error("[Congress] CONGRESS_API_KEY not set. Register at https://api.congress.gov/sign-up")
        return {"error": "CONGRESS_API_KEY not set", "total_bills": 0}

    _ensure_db(DB_PATH)

    # Search across all keywords
    all_bills: dict[str, dict] = {}
    for keyword in SEARCH_KEYWORDS:
        bills = search_bills(keyword, limit=25)
        for bill in bills:
            bid = bill["bill_id"]
            if bid not in all_bills or bill["heat_score"] > all_bills[bid]["heat_score"]:
                all_bills[bid] = bill

        logger.info(f"[Congress] '{keyword}': {len(bills)} bills")

    # Sort by heat score
    scored = sorted(all_bills.values(), key=lambda x: x["heat_score"], reverse=True)
    logger.info(f"[Congress] {len(scored)} unique bills after dedup")

    # Store in SQLite
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    inserted = 0
    for bill in scored:
        try:
            c.execute("""
                INSERT OR REPLACE INTO congress_bills
                (bill_id, congress, bill_number, bill_type, title, sponsor,
                 latest_action, latest_action_date, policy_area, status_phase,
                 heat_score, sector, url, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                bill["bill_id"], bill["congress"], bill["bill_number"],
                bill["bill_type"], bill["title"], bill["sponsor"],
                bill["latest_action"], bill["latest_action_date"],
                bill["policy_area"], bill["status_phase"],
                bill["heat_score"], bill["sector"], bill["url"],
                datetime.now().isoformat(),
            ))
            if c.rowcount > 0:
                inserted += 1
        except sqlite3.Error as e:
            logger.warning(f"[Congress] DB error: {e}")
    conn.commit()
    conn.close()

    logger.info(f"[Congress] {inserted} new/updated inserts to SQLite")

    # Push top signals to Airtable
    signals_pushed = 0
    if push_to_airtable and scored:
        try:
            from storage.airtable import get_client
            at = get_client()
        except Exception as e:
            logger.error(f"[Congress] Airtable client error: {e}")
            at = None

        if at:
            # Push bills with heat_score >= 8 (at least in committee)
            top = [bill for bill in scored if bill["heat_score"] >= 8.0][:40]
            for bill in top:
                raw_content = (
                    f"{bill['bill_number']}: {bill['title']}\n\n"
                    f"Sponsor: {bill['sponsor']}\n"
                    f"Status: {bill['status_phase'].replace('_', ' ').title()}\n"
                    f"Latest Action: {bill['latest_action']}\n"
                    f"Action Date: {bill['latest_action_date']}\n"
                    f"Policy Area: {bill['policy_area']}\n"
                )

                try:
                    at.insert_signal(
                        signal_type=SIGNAL_TYPE,
                        source=f"Congress.gov / {bill['bill_number']}",
                        company_name=bill["bill_number"],
                        sector=bill["sector"],
                        signal_date=bill["latest_action_date"] or datetime.now().strftime("%Y-%m-%d"),
                        raw_content=raw_content,
                        heat_score=bill["heat_score"],
                        notes=bill.get("url", ""),
                    )
                    signals_pushed += 1
                except Exception as e:
                    logger.warning(f"[Congress] Airtable insert failed: {e}")

            logger.info(f"[Congress] Pushed {signals_pushed} signals to Airtable")

    # Sector breakdown
    sector_counts: dict[str, int] = {}
    status_counts: dict[str, int] = {}
    for bill in scored:
        s = bill.get("sector", "Unknown")
        sector_counts[s] = sector_counts.get(s, 0) + 1
        st = bill.get("status_phase", "unknown")
        status_counts[st] = status_counts.get(st, 0) + 1

    return {
        "total_bills": len(scored),
        "new_inserts": inserted,
        "signals_pushed": signals_pushed,
        "sector_breakdown": sector_counts,
        "status_breakdown": status_counts,
        "top_bills": [
            {
                "number": bill["bill_number"],
                "title": bill["title"][:80],
                "score": bill["heat_score"],
                "status": bill["status_phase"],
                "sector": bill["sector"],
            }
            for bill in scored[:5]
        ],
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run(push_to_airtable=False)
    print(json.dumps(result, indent=2))
