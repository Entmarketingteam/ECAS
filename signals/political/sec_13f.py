"""
signals/political/sec_13f.py
Fetches hedge fund 13F filings from SEC EDGAR.
Stores in SQLite, returns sector stats for scoring.
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

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import API_CONFIG, TARGET_SECTORS, ALERT_THRESHOLDS, DB_PATH

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": API_CONFIG["sec_edgar_user_agent"],
    "Accept": "application/json",
}

# Major institutional filers that regularly file 13F
MAJOR_FILERS = [
    ("Bridgewater Associates", "0001350694"),
    ("Citadel Advisors", "0001423053"),
    ("Renaissance Technologies", "0001037389"),
    ("Two Sigma Investments", "0001179392"),
    ("D.E. Shaw", "0001009207"),
    ("Millennium Management", "0001273087"),
    ("Point72 Asset Management", "0001603466"),
    ("Baupost Group", "0001061768"),
    ("Elliott Investment Management", "0001048445"),
    ("Third Point", "0001040273"),
    ("Viking Global Investors", "0001103804"),
    ("Pershing Square Capital", "0001336528"),
    ("Appaloosa Management", "0001656456"),
    ("Soros Fund Management", "0001029160"),
    ("Tiger Global Management", "0001167483"),
]


def _ensure_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS hedge_fund_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filer TEXT,
            cik TEXT,
            filing_date TEXT,
            ticker TEXT,
            sector TEXT,
            value_thousands INTEGER,
            scraped_at TEXT
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_hf_sector ON hedge_fund_positions(sector)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_hf_date ON hedge_fund_positions(filing_date)")
    conn.commit()
    conn.close()


def _get_all_target_tickers() -> dict[str, str]:
    """Returns {TICKER: sector_name} for all sectors."""
    result = {}
    for sector_name, cfg in TARGET_SECTORS.items():
        for ticker in cfg.get("tickers", []):
            result[ticker.upper()] = sector_name
    return result


def fetch_13f_holdings(cik: str, filer_name: str) -> list[dict]:
    """Fetch most recent 13F holdings for a given filer."""
    ticker_map = _get_all_target_tickers()
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"

    try:
        time.sleep(0.2)  # SEC rate limit
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning(f"[13F] Error fetching {filer_name} (CIK {cik}): {e}")
        return []

    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])

    filing_idx = next((i for i, f in enumerate(forms) if "13F" in f), None)
    if filing_idx is None:
        return []

    filing_date = dates[filing_idx] if filing_idx < len(dates) else "Unknown"
    accession = accessions[filing_idx] if filing_idx < len(accessions) else None
    if not accession:
        return []

    accession_clean = accession.replace("-", "")
    cik_stripped = cik.lstrip("0")
    matched_holdings = []

    try:
        time.sleep(0.2)
        index_url = (
            f"https://www.sec.gov/Archives/edgar/data/{cik_stripped}"
            f"/{accession_clean}/index.json"
        )
        idx_resp = requests.get(index_url, headers=HEADERS, timeout=30)
        if idx_resp.status_code != 200:
            return []

        idx_data = idx_resp.json()
        for item in idx_data.get("directory", {}).get("item", []):
            name = item.get("name", "").lower()
            if "infotable" in name or ("information" in name and name.endswith(".xml")):
                table_url = (
                    f"https://www.sec.gov/Archives/edgar/data/{cik_stripped}"
                    f"/{accession_clean}/{item['name']}"
                )
                time.sleep(0.2)
                table_resp = requests.get(table_url, headers=HEADERS, timeout=30)
                if table_resp.status_code != 200:
                    continue

                content = table_resp.text.upper()
                for ticker, sector in ticker_map.items():
                    if ticker in content or any(
                        kw.upper() in content
                        for kw in TARGET_SECTORS[sector].get("keywords", [])[:3]
                    ):
                        value_match = re.search(
                            rf"{ticker}.*?<value>(\d+)</value>",
                            content, re.IGNORECASE | re.DOTALL
                        )
                        value = int(value_match.group(1)) * 1000 if value_match else 0
                        matched_holdings.append({
                            "filer": filer_name,
                            "cik": cik,
                            "filing_date": filing_date,
                            "ticker": ticker,
                            "sector": sector,
                            "value_thousands": value // 1000 if value else 0,
                        })
                break
    except Exception as e:
        logger.warning(f"[13F] Error parsing info table for {filer_name}: {e}")

    return matched_holdings


def _store_holdings(holdings: list[dict], db_path: Path) -> int:
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    inserted = 0
    for h in holdings:
        c.execute(
            "SELECT id FROM hedge_fund_positions WHERE filer=? AND ticker=? AND filing_date=?",
            (h["filer"], h["ticker"], h["filing_date"]),
        )
        if c.fetchone():
            continue
        c.execute("""
            INSERT INTO hedge_fund_positions
            (filer, cik, filing_date, ticker, sector, value_thousands, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            h["filer"], h["cik"], h["filing_date"], h["ticker"],
            h["sector"], h["value_thousands"], datetime.now().isoformat(),
        ))
        inserted += 1
    conn.commit()
    conn.close()
    return inserted


def run_scraper() -> dict:
    _ensure_db(DB_PATH)
    logger.info(f"[13F] Scanning {len(MAJOR_FILERS)} institutional filers...")

    all_holdings = []
    for filer_name, cik in MAJOR_FILERS:
        holdings = fetch_13f_holdings(cik, filer_name)
        if holdings:
            logger.info(f"  {filer_name}: {len(holdings)} target-sector positions")
            all_holdings.extend(holdings)

    inserted = _store_holdings(all_holdings, DB_PATH)

    sector_counts: dict[str, int] = {}
    sector_filers: dict[str, set] = {}
    for h in all_holdings:
        s = h["sector"]
        sector_counts[s] = sector_counts.get(s, 0) + 1
        sector_filers.setdefault(s, set()).add(h["filer"])

    logger.info(f"[13F] {len(all_holdings)} total matches | {inserted} new inserts")
    return {
        "filers_scanned": len(MAJOR_FILERS),
        "total_matches": len(all_holdings),
        "new_inserts": inserted,
        "sector_breakdown": sector_counts,
        "sector_filers": {k: len(v) for k, v in sector_filers.items()},
    }


def get_sector_stats(sector: str, lookback_days: int = 120) -> dict:
    _ensure_db(DB_PATH)
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    cutoff = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    c.execute("""
        SELECT COUNT(*) as positions, COUNT(DISTINCT filer) as unique_funds,
               SUM(value_thousands) as total_value_k
        FROM hedge_fund_positions WHERE sector=? AND filing_date >= ?
    """, (sector, cutoff))
    row = c.fetchone()

    c.execute("""
        SELECT filer, COUNT(*) as cnt FROM hedge_fund_positions
        WHERE sector=? AND filing_date >= ?
        GROUP BY filer ORDER BY cnt DESC LIMIT 5
    """, (sector, cutoff))
    top_filers = [{"filer": r[0], "count": r[1]} for r in c.fetchall()]
    conn.close()

    return {
        "position_count": row[0] if row else 0,
        "unique_funds": row[1] if row else 0,
        "total_value_thousands": row[2] if row and row[2] else 0,
        "top_filers": top_filers,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run_scraper()
    print(json.dumps(result, indent=2))
