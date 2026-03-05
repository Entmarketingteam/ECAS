"""
signals/earnings_transcripts.py
Ingests earnings call transcripts via Financial Modeling Prep (FMP) API.
Scans for quantifiable signal keywords → pushes high-confidence hits to Airtable.

Signal triggers (from Gemini research synthesis):
  - Capex hike ≥20% YoY → "Q1 capex up 20%" hook
  - SMR / nuclear power language → AI infrastructure nexus signal
  - Grid expansion / transmission / substation → downstream EPC demand
  - New facility / data center / campus → power infrastructure RFP incoming
  - Contract awards / backlog growth → supply chain demand signal
  - Hiring BD / business development surge → "skip the 6-month ramp" hook
"""

import json
import logging
import re
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import API_CONFIG, TARGET_SECTORS, DB_PATH, AIRTABLE_BASE_ID

logger = logging.getLogger(__name__)

FMP_BASE = "https://financialmodelingprep.com/api/v3"

# ── Signal keyword categories ─────────────────────────────────────────────────

SIGNAL_PATTERNS = {
    "capex_hike": {
        "keywords": [
            "capex", "capital expenditure", "capital spending", "infrastructure investment",
        ],
        "qualifiers": [
            r"\b(\d{1,3})%\s*(increase|growth|higher|up|rise)",
            r"(increase|grow|expand|accelerate|ramp).{0,30}(capex|capital)",
            r"(capex|capital).{0,30}(increase|grow|expand|accelerate|ramp)",
        ],
        "confidence": 75,
        "hook": "Q{quarter} capex up — leveraging that spend to secure new enterprise contracts through our fulfillment engine.",
    },
    "smr_nuclear": {
        "keywords": [
            "small modular reactor", "smr", "nuclear power", "advanced nuclear",
            "nuscale", "oklo", "last energy", "x-energy", "kairos",
            "nuclear ppa", "nuclear energy", "uranium", "enrichment",
        ],
        "qualifiers": [],
        "confidence": 85,
        "hook": "Your SMR/nuclear positioning just triggered a new supply chain opportunity window.",
    },
    "grid_expansion": {
        "keywords": [
            "transmission", "substation", "grid modernization", "grid expansion",
            "power infrastructure", "interconnection", "utility upgrade",
            "distribution upgrade", "high voltage", "energization",
        ],
        "qualifiers": [],
        "confidence": 80,
        "hook": "Grid expansion signals upcoming EPC procurement — positioning now gets you on the short-list before RFPs publish.",
    },
    "data_center_power": {
        "keywords": [
            "data center", "hyperscaler", "ai infrastructure", "on-site power",
            "modular power", "grid-constrained", "power demand", "megawatt",
            "gigawatt", "cooling infrastructure", "power purchase agreement", "ppa",
        ],
        "qualifiers": [],
        "confidence": 80,
        "hook": "AI data center build-out = sustained EPC demand. Your power infrastructure window is open.",
    },
    "contract_backlog": {
        "keywords": [
            "backlog growth", "contract awards", "new contracts", "contract wins",
            "awarded contract", "signed contract", "bookings",
        ],
        "qualifiers": [
            r"backlog.{0,20}(grew|increased|up|grew by)",
            r"(awarded|won|secured).{0,20}contract",
        ],
        "confidence": 70,
        "hook": "Contract backlog growth signals active deployment budget — outreach timing is optimal.",
    },
    "hiring_bd": {
        "keywords": [
            "hiring business development", "bd team", "business development headcount",
            "sales team expansion", "growing our bd", "capture team",
            "government relations", "federal sales",
        ],
        "qualifiers": [],
        "confidence": 72,
        "hook": "Hiring BD? Skip the 6-month ramp — our system delivers a ready-made pipeline of qualified operator leads.",
    },
    "facility_expansion": {
        "keywords": [
            "new facility", "new campus", "breaking ground", "greenfield",
            "expansion project", "new plant", "capacity expansion",
            "new site", "new location",
        ],
        "qualifiers": [],
        "confidence": 70,
        "hook": "Facility expansion → power infrastructure procurement cycle is 12-18 months out. Positioning starts now.",
    },
}

# ── SQLite dedup ───────────────────────────────────────────────────────────────

def _ensure_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS earnings_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            company TEXT,
            filing_date TEXT,
            signal_type TEXT,
            confidence INTEGER,
            excerpt TEXT,
            hook TEXT,
            sector TEXT,
            scraped_at TEXT,
            UNIQUE(ticker, filing_date, signal_type)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_earnings_ticker ON earnings_signals(ticker)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_earnings_date ON earnings_signals(filing_date)")
    conn.commit()
    conn.close()


def _is_duplicate(conn, ticker: str, filing_date: str, signal_type: str) -> bool:
    row = conn.execute(
        "SELECT id FROM earnings_signals WHERE ticker=? AND filing_date=? AND signal_type=?",
        (ticker, filing_date, signal_type),
    ).fetchone()
    return row is not None


# ── FMP API calls ─────────────────────────────────────────────────────────────

def _get_fmp_key() -> str:
    import os
    key = os.environ.get("FMP_API_KEY", "")
    if not key:
        raise ValueError("FMP_API_KEY not set. Add to Doppler: doppler secrets set FMP_API_KEY=<key>")
    return key


def fetch_transcripts(ticker: str, year: int = None, quarter: int = None) -> list[dict]:
    """Fetch earnings call transcript(s) for a ticker from FMP."""
    try:
        key = _get_fmp_key()
    except ValueError as e:
        logger.warning(str(e))
        return []

    if year and quarter:
        url = f"{FMP_BASE}/earning_call_transcript/{ticker}?year={year}&quarter={quarter}&apikey={key}"
    else:
        # Latest available transcript
        url = f"{FMP_BASE}/earning_call_transcript/{ticker}?apikey={key}"

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return data
        return []
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 401:
            logger.warning(f"[FMP] Unauthorized — check FMP_API_KEY tier (transcripts require paid plan)")
        else:
            logger.error(f"[FMP] {ticker} transcript fetch error: {e}")
        return []
    except Exception as e:
        logger.error(f"[FMP] {ticker} fetch error: {e}")
        return []


def fetch_recent_earnings_dates(tickers: list[str]) -> dict[str, str]:
    """
    Fetch the most recent earnings date per ticker via FMP earnings calendar.
    Returns {ticker: date_string}.
    """
    try:
        key = _get_fmp_key()
    except ValueError:
        return {}

    # Pull earnings calendar for the last 90 days
    from_date = (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d")
    to_date = datetime.utcnow().strftime("%Y-%m-%d")
    ticker_list = ",".join(tickers)

    url = (
        f"{FMP_BASE}/earning_calendar?"
        f"from={from_date}&to={to_date}&symbol={ticker_list}&apikey={key}"
    )
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        result = {}
        for item in data:
            sym = item.get("symbol", "").upper()
            date = item.get("date", "")
            if sym and date:
                # Keep the most recent date per ticker
                if sym not in result or date > result[sym]:
                    result[sym] = date
        return result
    except Exception as e:
        logger.error(f"[FMP] earnings calendar fetch error: {e}")
        return {}


# ── Signal scanning ────────────────────────────────────────────────────────────

def _extract_context(text: str, keyword: str, window: int = 300) -> str:
    """Extract surrounding context around a keyword match."""
    idx = text.lower().find(keyword.lower())
    if idx == -1:
        return ""
    start = max(0, idx - window // 2)
    end = min(len(text), idx + window // 2)
    return text[start:end].strip()


def scan_transcript(text: str, ticker: str, filing_date: str, company: str, sector: str) -> list[dict]:
    """
    Scan a transcript for signal patterns.
    Returns list of signal dicts with type, confidence, excerpt, hook.
    """
    if not text:
        return []

    text_lower = text.lower()
    found_signals = []

    for signal_type, cfg in SIGNAL_PATTERNS.items():
        # Primary keyword match
        keyword_hit = any(kw in text_lower for kw in cfg["keywords"])
        if not keyword_hit:
            continue

        # Qualifier regex boost (optional — raises confidence)
        qualifier_hit = False
        for pattern in cfg.get("qualifiers", []):
            if re.search(pattern, text_lower):
                qualifier_hit = True
                break

        # Find best keyword hit for context extraction
        matched_kw = next((kw for kw in cfg["keywords"] if kw in text_lower), cfg["keywords"][0])
        excerpt = _extract_context(text, matched_kw, window=400)

        confidence = cfg["confidence"]
        if qualifier_hit:
            confidence = min(confidence + 10, 95)

        # Build the hook with quarter substitution if possible
        hook = cfg["hook"]
        if "{quarter}" in hook:
            try:
                q = (datetime.strptime(filing_date[:10], "%Y-%m-%d").month - 1) // 3 + 1
                hook = hook.replace("{quarter}", str(q))
            except Exception:
                hook = hook.replace("{quarter}", "?")

        found_signals.append({
            "ticker": ticker,
            "company": company,
            "filing_date": filing_date,
            "signal_type": signal_type,
            "confidence": confidence,
            "excerpt": excerpt[:800],
            "hook": hook,
            "sector": sector,
        })

    return found_signals


def _ticker_to_sector(ticker: str) -> str:
    """Map a ticker to its target sector."""
    for sector_name, cfg in TARGET_SECTORS.items():
        if ticker.upper() in [t.upper() for t in cfg.get("tickers", [])]:
            return sector_name
    return "Unknown"


# ── Main runner ───────────────────────────────────────────────────────────────

def run_scraper(lookback_days: int = 90, push_to_airtable: bool = True) -> dict:
    """
    For each ticker in TARGET_SECTORS, fetch the most recent earnings transcript,
    scan for signal patterns, dedup, store in SQLite, push to Airtable.
    """
    _ensure_db(DB_PATH)

    # Collect all unique tickers across sectors
    all_tickers: dict[str, str] = {}  # ticker → sector
    for sector_name, cfg in TARGET_SECTORS.items():
        for t in cfg.get("tickers", []):
            all_tickers[t.upper()] = sector_name

    logger.info(f"[EarningsTranscripts] Scanning {len(all_tickers)} tickers")

    total_signals = 0
    total_new = 0
    sector_breakdown: dict[str, int] = {}

    conn = sqlite3.connect(str(DB_PATH))

    for ticker, sector in all_tickers.items():
        transcripts = fetch_transcripts(ticker)
        if not transcripts:
            logger.debug(f"[EarningsTranscripts] {ticker}: no transcripts found")
            continue

        # Process most recent transcript only
        latest = transcripts[0]
        text = latest.get("content", "")
        date = latest.get("date", datetime.utcnow().strftime("%Y-%m-%d"))
        company = latest.get("symbol", ticker)

        # Only process if within lookback window
        try:
            filing_dt = datetime.strptime(date[:10], "%Y-%m-%d")
            if filing_dt < datetime.utcnow() - timedelta(days=lookback_days):
                logger.debug(f"[EarningsTranscripts] {ticker}: transcript too old ({date}), skipping")
                continue
        except ValueError:
            pass

        signals = scan_transcript(text, ticker, date, company, sector)
        total_signals += len(signals)

        for sig in signals:
            if _is_duplicate(conn, ticker, date, sig["signal_type"]):
                continue

            conn.execute("""
                INSERT OR IGNORE INTO earnings_signals
                (ticker, company, filing_date, signal_type, confidence, excerpt, hook, sector, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sig["ticker"], sig["company"], sig["filing_date"],
                sig["signal_type"], sig["confidence"], sig["excerpt"],
                sig["hook"], sig["sector"], datetime.utcnow().isoformat(),
            ))
            total_new += 1
            sector_breakdown[sector] = sector_breakdown.get(sector, 0) + 1

            if push_to_airtable:
                _push_signal_to_airtable(sig)

        logger.info(f"[EarningsTranscripts] {ticker}: {len(signals)} signals ({date})")

    conn.commit()
    conn.close()

    logger.info(
        f"[EarningsTranscripts] Done — {total_signals} signals found, "
        f"{total_new} new inserts | {sector_breakdown}"
    )
    return {
        "tickers_scanned": len(all_tickers),
        "total_signals": total_signals,
        "new_inserts": total_new,
        "sector_breakdown": sector_breakdown,
    }


def _push_signal_to_airtable(sig: dict) -> None:
    try:
        from storage.airtable import get_client
        at = get_client()

        # Build readable raw content from excerpt + hook
        raw = (
            f"EARNINGS TRANSCRIPT SIGNAL: {sig['signal_type'].replace('_', ' ').upper()}\n\n"
            f"Company: {sig['company']} ({sig['ticker']})\n"
            f"Filing Date: {sig['filing_date']}\n"
            f"Confidence: {sig['confidence']}/100\n\n"
            f"Excerpt:\n{sig['excerpt']}\n\n"
            f"Outreach Hook:\n{sig['hook']}"
        )

        at.insert_signal(
            signal_type="earnings_transcript",
            source=f"FMP Earnings Call — {sig['ticker']}",
            company_name=sig["company"],
            sector=sig["sector"],
            signal_date=sig["filing_date"][:10],
            raw_content=raw,
            heat_score=float(sig["confidence"]),
        )
    except Exception as e:
        logger.warning(f"[EarningsTranscripts] Airtable push failed for {sig['ticker']}: {e}")


def get_sector_stats(sector: str, lookback_days: int = 90) -> dict:
    """Query SQLite for earnings signal stats for a sector (used by sector_scoring.py)."""
    _ensure_db(DB_PATH)
    conn = sqlite3.connect(str(DB_PATH))
    cutoff = (datetime.utcnow() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    row = conn.execute("""
        SELECT COUNT(*) as count,
               AVG(confidence) as avg_confidence,
               COUNT(DISTINCT ticker) as unique_tickers
        FROM earnings_signals
        WHERE sector=? AND filing_date >= ?
    """, (sector, cutoff)).fetchone()

    top = conn.execute("""
        SELECT ticker, signal_type, confidence, hook
        FROM earnings_signals
        WHERE sector=? AND filing_date >= ?
        ORDER BY confidence DESC LIMIT 5
    """, (sector, cutoff)).fetchall()

    conn.close()

    return {
        "signal_count": row[0] if row else 0,
        "avg_confidence": round(row[1] or 0, 1),
        "unique_tickers": row[2] if row else 0,
        "top_signals": [
            {"ticker": r[0], "signal_type": r[1], "confidence": r[2], "hook": r[3]}
            for r in top
        ],
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run_scraper(push_to_airtable=False)
    print(json.dumps(result, indent=2))
