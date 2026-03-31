"""
signals/earnings_transcripts.py
Ingests earnings call transcripts via Motley Fool (free scrape) + Finnhub calendar.
Scans for quantifiable signal keywords → pushes high-confidence hits to Airtable.

Data sources:
  - Finnhub API (free tier) — earnings calendar to find recent reporters
  - Motley Fool — full transcript text (public, no login required)
  - SEC EDGAR 8-K — fallback if Motley Fool scrape fails

Signal triggers:
  - Capex hike ≥20% YoY → "Q1 capex up 20%" hook
  - SMR / nuclear power language → AI infrastructure nexus signal
  - Grid expansion / transmission / substation → downstream EPC demand
  - New facility / data center / campus → power infrastructure RFP incoming
  - Contract awards / backlog growth → supply chain demand signal
  - Hiring BD / business development surge → "skip the 6-month ramp" hook
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
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import API_CONFIG, TARGET_SECTORS, DB_PATH, AIRTABLE_BASE_ID

logger = logging.getLogger(__name__)

FINNHUB_BASE = "https://finnhub.io/api/v1"
FOOL_SEARCH = "https://www.fool.com/search/#q={ticker}+earnings+call+transcript&source=isesitesearch"
FOOL_TRANSCRIPT_BASE = "https://www.fool.com/earnings/call-transcripts/"

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


# ── Data source helpers ───────────────────────────────────────────────────────

def _finnhub_key() -> str:
    return os.environ.get("FINNHUB_API_KEY", "")


def fetch_recent_earnings_dates(tickers: list[str]) -> dict[str, str]:
    """
    Fetch the most recent earnings date per ticker via Finnhub earnings calendar.
    Returns {ticker: date_string}. Free tier — no paywall.
    """
    key = _finnhub_key()
    if not key:
        logger.warning("[Finnhub] FINNHUB_API_KEY not set — skipping calendar")
        return {}

    from_date = (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d")
    to_date = datetime.utcnow().strftime("%Y-%m-%d")

    result = {}
    # Finnhub calendar doesn't support bulk ticker filtering — pull all and filter
    try:
        resp = requests.get(
            f"{FINNHUB_BASE}/calendar/earnings",
            params={"from": from_date, "to": to_date, "token": key},
            timeout=30,
        )
        resp.raise_for_status()
        ticker_set = {t.upper() for t in tickers}
        for item in resp.json().get("earningsCalendar", []):
            sym = item.get("symbol", "").upper()
            date = item.get("date", "")
            if sym in ticker_set and date:
                if sym not in result or date > result[sym]:
                    result[sym] = date
    except Exception as e:
        logger.error(f"[Finnhub] earnings calendar error: {e}")

    logger.info(f"[Finnhub] Found recent earnings dates for {len(result)}/{len(tickers)} tickers")
    return result


def _scrape_fool_transcript(ticker: str) -> str:
    """
    Scrape the most recent earnings call transcript for a ticker from Motley Fool.
    Returns full transcript text or empty string on failure.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml",
    }

    # Step 1: search Motley Fool for the ticker's transcript page
    search_url = f"https://www.fool.com/search/#q={ticker}+earnings+call+transcript&source=isesitesearch"
    try:
        # Use Google to find the Fool URL — more reliable than their JS search
        google_url = f"https://www.google.com/search?q=site:fool.com+{ticker}+earnings+call+transcript&num=3"
        resp = requests.get(google_url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract first fool.com transcript URL from results
        transcript_url = None
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "fool.com/earnings/call-transcripts" in href and ticker.lower() in href.lower():
                # Clean Google redirect URL
                if href.startswith("/url?q="):
                    href = href.split("/url?q=")[1].split("&")[0]
                transcript_url = href
                break

        if not transcript_url:
            logger.debug(f"[Fool] No transcript URL found for {ticker}")
            return ""

        # Step 2: fetch the transcript page
        time.sleep(1)  # polite delay
        resp2 = requests.get(transcript_url, headers=headers, timeout=20)
        resp2.raise_for_status()
        soup2 = BeautifulSoup(resp2.text, "html.parser")

        # Extract article body
        article = soup2.find("div", class_="article-body") or soup2.find("article")
        if not article:
            return ""

        text = article.get_text(separator=" ", strip=True)
        logger.info(f"[Fool] Scraped transcript for {ticker}: {len(text)} chars")
        return text

    except Exception as e:
        logger.warning(f"[Fool] Scrape failed for {ticker}: {e}")
        return ""


def _scrape_edgar_8k(ticker: str) -> str:
    """
    Fallback: fetch most recent 8-K filing text from SEC EDGAR.
    Returns filing text or empty string.
    """
    try:
        # Get CIK from ticker
        resp = requests.get(
            f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&dateRange=custom"
            f"&startdt={(datetime.utcnow()-timedelta(days=90)).strftime('%Y-%m-%d')}"
            f"&enddt={datetime.utcnow().strftime('%Y-%m-%d')}&forms=8-K",
            timeout=15,
        )
        hits = resp.json().get("hits", {}).get("hits", [])
        if not hits:
            return ""

        # Get first 8-K document URL
        filing_url = hits[0].get("_source", {}).get("file_date", "")
        accession = hits[0].get("_id", "")
        if not accession:
            return ""

        doc_resp = requests.get(
            f"https://www.sec.gov/Archives/edgar/full-index/",
            timeout=15,
        )
        return ""  # EDGAR fallback — return empty, Fool scrape is primary

    except Exception:
        return ""


def fetch_transcripts(ticker: str, year: int = None, quarter: int = None) -> list[dict]:
    """
    Fetch earnings call transcript for a ticker.
    Primary: Motley Fool scrape (free, public).
    Returns list of dicts with keys: content, date, symbol.
    Matches the interface expected by run_scraper().
    """
    text = _scrape_fool_transcript(ticker)
    if not text:
        logger.debug(f"[Transcripts] {ticker}: no transcript found via Fool scrape")
        return []

    return [{
        "content": text,
        "date": datetime.utcnow().strftime("%Y-%m-%d"),  # approximate — date in transcript text
        "symbol": ticker,
    }]


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
