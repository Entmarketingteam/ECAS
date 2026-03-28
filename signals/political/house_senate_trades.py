"""
signals/political/house_senate_trades.py
Scrapes politician stock trades from Quiver Quantitative API.
Replaces the defunct House/Senate Stock Watcher S3 endpoints (403 as of 2026-03).
Stores raw matches in SQLite (for dedup), pushes scored signals to Airtable.

Quiver Quant free tier: https://api.quiverquant.com/beta/live/congresstrading
Returns 1000 most recent trades across both chambers in one call.
No API key required for the free endpoint.
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


def _ensure_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS politician_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chamber TEXT,
            politician TEXT,
            ticker TEXT,
            asset_description TEXT,
            transaction_type TEXT,
            transaction_date TEXT,
            disclosure_date TEXT,
            amount TEXT,
            district TEXT,
            party TEXT,
            matched_sector TEXT,
            scraped_at TEXT
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_trades_sector ON politician_trades(matched_sector)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_trades_date ON politician_trades(transaction_date)")
    conn.commit()
    conn.close()


def fetch_all_trades() -> list[dict]:
    """
    Fetch recent congressional trades from Quiver Quantitative.
    Returns up to 1000 most recent trades across both House and Senate.
    No API key required for the free endpoint.
    """
    url = API_CONFIG["quiver_congress_url"]
    try:
        resp = requests.get(url, headers={"Accept": "application/json"}, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        logger.info(f"[QuiverQuant] {len(data)} total transactions fetched")
        return data if isinstance(data, list) else []
    except Exception as e:
        logger.error(f"[QuiverQuant] fetch error: {e}")
        return []


# Keep old names as shims so scheduler.py doesn't break
def fetch_house_trades() -> list[dict]:
    return []  # Replaced by fetch_all_trades()


def fetch_senate_trades() -> list[dict]:
    return []  # Replaced by fetch_all_trades()


def normalize_quiver(t: dict) -> dict:
    """Normalize a Quiver Quant record to the internal trade format."""
    chamber = t.get("House", "Unknown")  # "House" or "Senate" (their field name)
    return {
        "chamber": chamber,
        "politician": t.get("Representative", "Unknown"),
        "ticker": (t.get("Ticker") or "").upper().strip(),
        "asset_description": t.get("Description") or t.get("Ticker", ""),
        "transaction_type": t.get("Transaction", ""),
        "transaction_date": t.get("TransactionDate", ""),
        "disclosure_date": t.get("ReportDate", ""),
        "amount": t.get("Range", t.get("Amount", "")),
        "district": t.get("BioGuideID", ""),
        "party": t.get("Party", ""),
    }


# Legacy normalizers kept for any external callers
def normalize_house(t: dict) -> dict:
    return normalize_quiver(t)


def normalize_senate(t: dict) -> dict:
    return normalize_quiver(t)


def _parse_date(s: str) -> datetime | None:
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s.strip(), fmt)
        except (ValueError, AttributeError):
            continue
    return None


def match_sector(trade: dict) -> list[str]:
    import re as _re
    ticker = trade.get("ticker", "").upper().strip()
    desc = (trade.get("asset_description") or "").lower()
    matched = []
    for sector_name, cfg in TARGET_SECTORS.items():
        if ticker and ticker in [t.upper() for t in cfg.get("tickers", [])]:
            matched.append(sector_name)
            continue
        for kw in cfg.get("keywords", []):
            kw_lower = kw.lower()
            # Short keywords (≤5 chars) require word-boundary match to prevent
            # false positives (e.g. "abb" matching inside "abbott").
            if len(kw_lower) <= 5:
                if _re.search(r'\b' + _re.escape(kw_lower) + r'\b', desc):
                    matched.append(sector_name)
                    break
            else:
                if kw_lower in desc:
                    matched.append(sector_name)
                    break
    return matched


def _is_duplicate(c, trade: dict, sector: str) -> bool:
    c.execute(
        "SELECT id FROM politician_trades WHERE politician=? AND ticker=? "
        "AND transaction_date=? AND matched_sector=?",
        (trade["politician"], trade["ticker"], trade["transaction_date"], sector),
    )
    return c.fetchone() is not None


def run_scraper() -> dict:
    lookback = ALERT_THRESHOLDS["politician_lookback_days"]
    cutoff = datetime.now() - timedelta(days=lookback)

    _ensure_db(DB_PATH)

    all_raw = fetch_all_trades()
    all_trades = [normalize_quiver(t) for t in all_raw]

    # Filter to lookback window
    recent = [t for t in all_trades if (d := _parse_date(t["transaction_date"])) and d >= cutoff]
    logger.info(f"[Trades] {len(recent)} trades in last {lookback} days")

    # Match to sectors
    matched: list[tuple[dict, str]] = []
    for trade in recent:
        for sector in match_sector(trade):
            matched.append((trade, sector))

    # Store new trades in SQLite
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    inserted = 0
    for trade, sector in matched:
        if not _is_duplicate(c, trade, sector):
            c.execute("""
                INSERT INTO politician_trades
                (chamber, politician, ticker, asset_description, transaction_type,
                 transaction_date, disclosure_date, amount, district, party,
                 matched_sector, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade["chamber"], trade["politician"], trade["ticker"],
                trade["asset_description"], trade["transaction_type"],
                trade["transaction_date"], trade["disclosure_date"],
                trade["amount"], trade["district"], trade["party"],
                sector, datetime.now().isoformat(),
            ))
            inserted += 1
    conn.commit()
    conn.close()

    # Sector breakdown for scoring
    sector_counts: dict[str, int] = {}
    sector_politicians: dict[str, set] = {}
    for trade, sector in matched:
        sector_counts[sector] = sector_counts.get(sector, 0) + 1
        sector_politicians.setdefault(sector, set()).add(trade["politician"])

    logger.info(f"[Trades] inserted {inserted} new | sector breakdown: {sector_counts}")

    return {
        "total_fetched": len(all_trades),
        "recent_count": len(recent),
        "matched_count": len(matched),
        "new_inserts": inserted,
        "sector_breakdown": sector_counts,
        "sector_politicians": {k: list(v) for k, v in sector_politicians.items()},
    }


def get_sector_stats(sector: str, lookback_days: int = 90) -> dict:
    """Query SQLite for politician trade stats for a given sector."""
    _ensure_db(DB_PATH)
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    cutoff = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    c.execute("""
        SELECT COUNT(*) as trade_count, COUNT(DISTINCT politician) as unique_pols,
               COUNT(DISTINCT ticker) as unique_tickers
        FROM politician_trades
        WHERE matched_sector=? AND transaction_date >= ?
    """, (sector, cutoff))
    row = c.fetchone()

    # Top tickers
    c.execute("""
        SELECT ticker, COUNT(*) as cnt FROM politician_trades
        WHERE matched_sector=? AND transaction_date >= ?
        GROUP BY ticker ORDER BY cnt DESC LIMIT 5
    """, (sector, cutoff))
    top_tickers = [{"ticker": r[0], "count": r[1]} for r in c.fetchall()]

    conn.close()
    return {
        "trade_count": row[0] if row else 0,
        "unique_politicians": row[1] if row else 0,
        "unique_tickers": row[2] if row else 0,
        "top_tickers": top_tickers,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run_scraper()
    print(json.dumps(result, indent=2))
