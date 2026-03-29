"""
signals/political/government_contracts.py
Fetches government contract awards from USASpending.gov.
Stores in SQLite. Top contracts pushed to Airtable as signals.
"""

import json
import logging
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import API_CONFIG, TARGET_SECTORS, ALERT_THRESHOLDS, DB_PATH

logger = logging.getLogger(__name__)

USASPENDING_URL = f"{API_CONFIG['usaspending_base_url']}/search/spending_by_award/"


def _ensure_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS government_contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            award_id TEXT UNIQUE,
            recipient_name TEXT,
            description TEXT,
            award_amount REAL,
            start_date TEXT,
            awarding_agency TEXT,
            naics_code TEXT,
            matched_sector TEXT,
            scraped_at TEXT
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_gc_sector ON government_contracts(matched_sector)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_gc_date ON government_contracts(start_date)")
    conn.commit()
    conn.close()


def _search_contracts(keyword: str, start_date: str, end_date: str, page: int = 1) -> dict:
    payload = {
        "filters": {
            "keywords": [keyword],
            "time_period": [{"start_date": start_date, "end_date": end_date}],
            "award_type_codes": ["A", "B", "C", "D"],  # Contracts only
        },
        "fields": [
            "Award ID", "Recipient Name", "Award Amount", "Description",
            "Start Date", "Awarding Agency", "NAICS Code",
        ],
        "page": page,
        "limit": 100,
        "sort": "Award Amount",
        "order": "desc",
    }
    try:
        resp = requests.post(USASPENDING_URL, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"[Contracts] USASpending error for '{keyword}': {e}")
        return {}


def _match_sector_by_naics(naics_code: str) -> str | None:
    for sector_name, cfg in TARGET_SECTORS.items():
        if naics_code in cfg.get("naics_codes", []):
            return sector_name
    return None


def _match_sector_by_description(description: str, recipient: str) -> str | None:
    import re
    text = (description + " " + recipient).lower()
    for sector_name, cfg in TARGET_SECTORS.items():
        for kw in cfg.get("keywords", []):
            kw_lower = kw.lower()
            # Short keywords (≤5 chars like "abb", "aps", "pge") must match as whole
            # words to avoid false positives (e.g. "abb" inside "abbott").
            # Longer keywords use substring match (they're specific enough).
            if len(kw_lower) <= 5:
                if re.search(r'\b' + re.escape(kw_lower) + r'\b', text):
                    return sector_name
            else:
                if kw_lower in text:
                    return sector_name
    return None


def run_scraper() -> dict:
    _ensure_db(DB_PATH)
    lookback = ALERT_THRESHOLDS.get("contract_lookback_days", 90)
    min_value = ALERT_THRESHOLDS["min_contract_value"]

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=lookback)).strftime("%Y-%m-%d")

    # Collect all keywords across sectors
    all_keywords: list[tuple[str, str]] = []
    for sector_name, cfg in TARGET_SECTORS.items():
        for kw in cfg.get("keywords", []):
            all_keywords.append((kw, sector_name))

    logger.info(f"[Contracts] Searching {len(all_keywords)} keywords | {start_date} → {end_date}")

    all_contracts: list[dict] = []
    seen_award_ids: set[str] = set()

    for keyword, default_sector in all_keywords:
        data = _search_contracts(keyword, start_date, end_date)
        results = data.get("results", [])
        for r in results:
            award_id = r.get("Award ID", "")
            if not award_id or award_id in seen_award_ids:
                continue
            seen_award_ids.add(award_id)

            amount = float(r.get("Award Amount") or 0)
            if amount < min_value:
                continue

            naics = r.get("NAICS Code", "") or ""
            desc = r.get("Description", "") or ""
            recipient = r.get("Recipient Name", "") or ""

            # Determine sector — require a real NAICS or description match.
            # Do NOT fall back to default_sector: keyword "abb" fetches ABBOTT, etc.
            sector = _match_sector_by_naics(naics)
            if not sector:
                sector = _match_sector_by_description(desc, recipient)
            if not sector:
                continue  # skip false-positive keyword hits

            all_contracts.append({
                "award_id": award_id,
                "recipient_name": recipient,
                "description": desc,
                "award_amount": amount,
                "start_date": r.get("Start Date", "") or "",
                "awarding_agency": r.get("Awarding Agency", "") or "",
                "naics_code": naics,
                "matched_sector": sector,
            })

    logger.info(f"[Contracts] {len(all_contracts)} contracts above ${min_value:,}")

    # Store in SQLite
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    inserted = 0
    for ct in all_contracts:
        try:
            c.execute("""
                INSERT OR IGNORE INTO government_contracts
                (award_id, recipient_name, description, award_amount, start_date,
                 awarding_agency, naics_code, matched_sector, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ct["award_id"], ct["recipient_name"], ct["description"],
                ct["award_amount"], ct["start_date"], ct["awarding_agency"],
                ct["naics_code"], ct["matched_sector"], datetime.now().isoformat(),
            ))
            if c.rowcount > 0:
                inserted += 1
        except sqlite3.Error as e:
            logger.warning(f"[Contracts] DB error: {e}")
    conn.commit()
    conn.close()

    # Summary
    sector_counts: dict[str, int] = {}
    sector_values: dict[str, float] = {}
    for ct in all_contracts:
        s = ct["matched_sector"]
        sector_counts[s] = sector_counts.get(s, 0) + 1
        sector_values[s] = sector_values.get(s, 0.0) + ct["award_amount"]

    logger.info(f"[Contracts] {inserted} new inserts | {sector_counts}")
    return {
        "total_contracts": len(all_contracts),
        "new_inserts": inserted,
        "sector_breakdown": sector_counts,
        "sector_values_m": {k: round(v / 1_000_000, 1) for k, v in sector_values.items()},
    }


def get_sector_stats(sector: str, lookback_days: int = 90) -> dict:
    """Query SQLite for contract stats for a given sector."""
    _ensure_db(DB_PATH)
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    cutoff = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    c.execute("""
        SELECT COUNT(*) as cnt, SUM(award_amount) as total_value
        FROM government_contracts
        WHERE matched_sector=? AND start_date >= ?
    """, (sector, cutoff))
    row = c.fetchone()

    # Top recipients
    c.execute("""
        SELECT recipient_name, SUM(award_amount) as total FROM government_contracts
        WHERE matched_sector=? AND start_date >= ?
        GROUP BY recipient_name ORDER BY total DESC LIMIT 5
    """, (sector, cutoff))
    top = [{"recipient": r[0], "total_m": round(r[1] / 1_000_000, 1)} for r in c.fetchall()]
    conn.close()

    return {
        "contract_count": row[0] if row else 0,
        "total_value_m": round((row[1] or 0) / 1_000_000, 1) if row else 0,
        "top_recipients": top,
    }


def push_top_contracts_to_airtable(sector: str, limit: int = 20, min_value_m: float = 5.0) -> int:
    """
    Push the top contracts (by value) for a sector from SQLite to Airtable signals_raw.
    Only pushes contracts above min_value_m million.
    Returns number of signals pushed.
    """
    _ensure_db(DB_PATH)
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    cutoff = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    c.execute("""
        SELECT recipient_name, description, award_amount, start_date, awarding_agency
        FROM government_contracts
        WHERE matched_sector=? AND start_date >= ? AND award_amount >= ?
        ORDER BY award_amount DESC LIMIT ?
    """, (sector, cutoff, min_value_m * 1_000_000, limit))
    rows = c.fetchall()
    conn.close()

    if not rows:
        return 0

    from storage.airtable import get_client
    at = get_client()
    pushed = 0

    for recipient, description, amount, start_date, agency in rows:
        at.insert_signal(
            signal_type="gov_contract",
            source=f"USASpending.gov / {agency or 'Federal'}",
            company_name=recipient or "Unknown Recipient",
            sector=sector,
            signal_date=(start_date or "")[:10],
            raw_content=(
                f"Contract award: ${amount / 1_000_000:.1f}M\n"
                f"Agency: {agency}\n"
                f"Description: {description[:500] if description else 'N/A'}"
            ),
            heat_score=min(20.0 + (amount / 1_000_000) * 0.005, 60.0),
        )
        pushed += 1

    logger.info(f"[Contracts] Pushed {pushed} top contracts to Airtable for {sector}")
    return pushed


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run_scraper()
    print(json.dumps(result, indent=2))
