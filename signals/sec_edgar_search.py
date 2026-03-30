"""
signals/sec_edgar_search.py
Full-text search of SEC EDGAR for capex signals from public companies.

API: https://efts.sec.gov/LATEST/search-index (no auth, requires User-Agent header)
Searches 8-K and 10-K filings for capital expenditure language across target sectors.

Signal logic:
  - 8-K filing match → heat_score 20 (material event disclosure)
  - 10-K filing match → heat_score 15 (annual plan / capex guidance)

Deduplicates by filing accession number in SQLite table `sec_edgar_search`.
"""

import json
import logging
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import API_CONFIG, DB_PATH

logger = logging.getLogger(__name__)

# SEC EDGAR full-text search API
EDGAR_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"

# User-Agent required by SEC (no API key needed)
EDGAR_HEADERS = {
    "User-Agent": API_CONFIG.get("sec_edgar_user_agent", "ECAS admin@contractmotion.com"),
    "Accept": "application/json",
}

# Rate limit between API calls (SEC asks for max 10 req/sec; we do 2/sec to be safe)
RATE_LIMIT_SECONDS = 0.5

# Look back 30 days
LOOKBACK_DAYS = 30

# Filing form types to filter
TARGET_FORMS = ["8-K", "10-K"]

# Heat scores by form type
FORM_HEAT_SCORES = {
    "8-K": 20,   # Material event — most actionable
    "10-K": 15,  # Annual report — capex plan confirmation
}

# Search queries: (query_string, sector_label)
SEARCH_QUERIES = [
    ('"capital expenditure" "data center"', "Data Center & AI Infrastructure"),
    ('"capital expenditure" "transmission" OR "substation"', "Power & Grid Infrastructure"),
    ('"capital expenditure" "water treatment" OR "wastewater"', "Water & Wastewater Infrastructure"),
    ('"military construction" OR "MILCON"', "Defense"),
    ('"capital expenditure" "manufacturing" OR "semiconductor" OR "battery"', "Industrial & Manufacturing Facilities"),
    ('"small modular reactor" OR "nuclear" "capital"', "Nuclear & Critical Minerals"),
    ('"interconnection" "megawatt"', "Power & Grid Infrastructure"),
    ('"consent decree" "water"', "Water & Wastewater Infrastructure"),
]


def _ensure_db(db_path: Path) -> None:
    """Create SQLite table for deduplication."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS sec_edgar_search (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            accession_number TEXT UNIQUE,
            company_name TEXT,
            form_type TEXT,
            filed_date TEXT,
            query_label TEXT,
            sector TEXT,
            heat_score REAL,
            title TEXT,
            url TEXT,
            scraped_at TEXT
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_ses_sector ON sec_edgar_search(sector)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_ses_date ON sec_edgar_search(filed_date)")
    conn.commit()
    conn.close()


def _search_edgar(query: str, start_date: str, end_date: str, forms: list[str]) -> list[dict]:
    """
    Query the SEC EDGAR full-text search API.
    Returns list of filing result dicts.
    """
    params = {
        "q": query,
        "dateRange": "custom",
        "startdt": start_date,
        "enddt": end_date,
        "forms": ",".join(forms),
    }

    try:
        resp = requests.get(
            EDGAR_SEARCH_URL,
            params=params,
            headers=EDGAR_HEADERS,
            timeout=30,
        )

        if resp.status_code == 429:
            logger.warning("[SEC EDGAR] Rate limited — backing off")
            time.sleep(5)
            return []

        if resp.status_code != 200:
            logger.warning(f"[SEC EDGAR] HTTP {resp.status_code}: {resp.text[:200]}")
            return []

        data = resp.json()

        # EDGAR search returns {"hits": {"hits": [...]}} or {"filings": [...]}
        filings = []
        if "hits" in data:
            raw_hits = data["hits"].get("hits", [])
            filings = [h.get("_source", h) for h in raw_hits]
        elif "filings" in data:
            filings = data["filings"]
        elif isinstance(data, list):
            filings = data

        return filings

    except requests.exceptions.Timeout:
        logger.warning(f"[SEC EDGAR] Timeout for query: {query[:50]}")
        return []
    except ValueError as e:
        logger.warning(f"[SEC EDGAR] JSON parse error: {e}")
        return []
    except Exception as e:
        logger.error(f"[SEC EDGAR] Error: {e}")
        return []


def _extract_filing_data(filing: dict) -> dict:
    """Extract normalized fields from a single EDGAR filing result."""
    accession = (
        filing.get("accession_no")
        or filing.get("accession_number")
        or filing.get("_id", "")
    )
    company = (
        filing.get("entity_name")
        or filing.get("display_names", [""])[0] if isinstance(filing.get("display_names"), list) else ""
        or filing.get("company_name", "")
    )
    form_type = filing.get("form_type") or filing.get("file_type") or ""
    filed_date = filing.get("file_date") or filing.get("filed_date") or filing.get("date_filed") or ""
    title = filing.get("file_description") or filing.get("title") or filing.get("description") or ""

    # Normalize date
    if isinstance(filed_date, str) and "T" in filed_date:
        filed_date = filed_date[:10]

    # Build EDGAR filing URL
    url = ""
    if accession:
        clean_accession = accession.replace("-", "")
        url = f"https://www.sec.gov/Archives/edgar/data/{clean_accession}"

    return {
        "accession_number": accession,
        "company_name": company if isinstance(company, str) else str(company),
        "form_type": form_type,
        "filed_date": filed_date,
        "title": title,
        "url": url,
    }


def run(push_to_airtable: bool = True) -> dict:
    """
    Search SEC EDGAR for capex-related filings across target sectors.
    Deduplicates in SQLite, pushes new signals to Airtable.
    Returns summary dict.
    """
    _ensure_db(DB_PATH)

    end_date = datetime.utcnow().strftime("%Y-%m-%d")
    start_date = (datetime.utcnow() - timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%d")

    logger.info(f"[SEC EDGAR] Searching {len(SEARCH_QUERIES)} queries | {start_date} → {end_date}")

    all_signals: list[dict] = []
    seen_accessions: set[str] = set()

    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    for query, sector in SEARCH_QUERIES:
        time.sleep(RATE_LIMIT_SECONDS)

        filings = _search_edgar(query, start_date, end_date, TARGET_FORMS)
        count = 0

        for filing in filings:
            data = _extract_filing_data(filing)
            accession = data["accession_number"]

            if not accession or accession in seen_accessions:
                continue
            seen_accessions.add(accession)

            # Check SQLite for existing
            c.execute(
                "SELECT 1 FROM sec_edgar_search WHERE accession_number = ?",
                (accession,),
            )
            if c.fetchone():
                continue

            # Determine heat score by form type
            form = data["form_type"].upper()
            heat_score = FORM_HEAT_SCORES.get("8-K" if "8-K" in form else "10-K" if "10-K" in form else "", 10)

            signal = {
                "accession_number": accession,
                "company_name": data["company_name"] or "Unknown Filer",
                "form_type": data["form_type"],
                "filed_date": data["filed_date"],
                "query_label": query[:80],
                "sector": sector,
                "heat_score": heat_score,
                "title": data["title"],
                "url": data["url"],
            }

            # Insert into SQLite
            try:
                c.execute("""
                    INSERT OR IGNORE INTO sec_edgar_search
                    (accession_number, company_name, form_type, filed_date,
                     query_label, sector, heat_score, title, url, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    signal["accession_number"], signal["company_name"],
                    signal["form_type"], signal["filed_date"],
                    signal["query_label"], signal["sector"],
                    signal["heat_score"], signal["title"],
                    signal["url"], datetime.utcnow().isoformat(),
                ))
                if c.rowcount > 0:
                    all_signals.append(signal)
                    count += 1
            except sqlite3.Error as e:
                logger.warning(f"[SEC EDGAR] DB error: {e}")

        logger.info(f"[SEC EDGAR] '{query[:50]}' → {count} new signals for {sector}")

    conn.commit()
    conn.close()

    # Push to Airtable
    signals_pushed = 0
    if push_to_airtable and all_signals:
        try:
            from storage.airtable import get_client
            at = get_client()

            for sig in all_signals:
                try:
                    raw_content = (
                        f"SEC Filing: {sig['form_type']} — {sig['title']}\n"
                        f"Company: {sig['company_name']}\n"
                        f"Filed: {sig['filed_date']}\n"
                        f"Accession: {sig['accession_number']}\n"
                        f"Query: {sig['query_label']}"
                    )
                    at.insert_signal(
                        signal_type="sec_edgar_search",
                        source=f"SEC EDGAR / {sig['form_type']}",
                        company_name=sig["company_name"],
                        sector=sig["sector"],
                        signal_date=sig["filed_date"],
                        raw_content=raw_content,
                        heat_score=sig["heat_score"],
                        notes=sig["url"],
                    )
                    signals_pushed += 1
                except Exception as e:
                    logger.warning(f"[SEC EDGAR] Airtable insert failed: {e}")

        except Exception as e:
            logger.error(f"[SEC EDGAR] Airtable client error: {e}")

    # Summary by sector
    sector_counts: dict[str, int] = {}
    for sig in all_signals:
        s = sig["sector"]
        sector_counts[s] = sector_counts.get(s, 0) + 1

    logger.info(
        f"[SEC EDGAR] Done: {len(all_signals)} new signals, "
        f"{signals_pushed} pushed to Airtable | {sector_counts}"
    )

    return {
        "total_new_signals": len(all_signals),
        "signals_pushed": signals_pushed,
        "sector_breakdown": sector_counts,
        "queries_run": len(SEARCH_QUERIES),
        "lookback_days": LOOKBACK_DAYS,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run(push_to_airtable=False)
    print(json.dumps(result, indent=2))
