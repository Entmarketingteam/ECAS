"""
signals/ferc_rss_poller.py
FERC EFTS (Electronic Filing & Tracking System) API poller.

FERC eLibrary (elibrary.ferc.gov) is Cloudflare-protected and returns 0 results.
This replaces it by querying the EFTS search-index JSON API directly — no auth needed,
returns structured filing metadata including docket number, title, and filing date.

API: https://efts.ferc.gov/LATEST/search-index?q=...&dateRange=custom&startDate=...
Docs: https://efts.ferc.gov/LATEST/search-index (no formal docs — reverse-engineered from FERC search UI)

Signal logic:
  - "interconnection agreement" filings → heat_score 20.0 (strongest EPC demand signal)
  - "construction" + "transmission" filings → heat_score 15.0
  - "rate case" / "rate schedule" filings → heat_score 12.0
  - All others → heat_score 8.0
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

EFTS_BASE_URL = "https://efts.ferc.gov/LATEST/search-index"

# How many days back to look for new filings
LOOKBACK_DAYS = 7

# Queries and their associated base heat scores
# Each tuple: (query_string, base_heat_score, label)
FERC_QUERIES = [
    (
        '"interconnection agreement" OR "generator interconnection" OR "transmission interconnection"',
        20.0,
        "Interconnection Agreement",
    ),
    (
        '"construction" "transmission" "upgrade" OR "expansion"',
        15.0,
        "Transmission Construction",
    ),
    (
        '"rate case" OR "rate schedule" OR "integrated resource plan" OR "IRP"',
        12.0,
        "Rate Case / IRP",
    ),
    (
        '"power purchase agreement" OR "PPA" OR "energy storage" "interconnection"',
        18.0,
        "PPA / Storage Interconnection",
    ),
]

# FERC filing categories that are strongest EPC signals
HIGH_VALUE_CATEGORIES = {
    "E": "Electric",    # Electric filings — most relevant
    "G": "Gas",         # Gas pipeline — moderate relevance
}

# Minimum results per query to bother logging as successful
MIN_RESULTS_TO_LOG = 1

_HEADERS = {
    "User-Agent": "ECAS admin@contractmotion.com (signal monitoring)",
    "Accept": "application/json",
}


def _get_date_range() -> tuple[str, str]:
    """Return (start_date, end_date) strings in YYYY-MM-DD format."""
    end = datetime.utcnow()
    start = end - timedelta(days=LOOKBACK_DAYS)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def _calculate_heat_score(base_score: float, filing: dict) -> float:
    """
    Adjust base score based on filing metadata.
    Filings with dollar amounts or explicit construction language score higher.
    """
    score = base_score
    title = (filing.get("title") or "").lower()
    description = (filing.get("description") or "").lower()
    text = title + " " + description

    # Bonus for large dollar amounts in title/description
    import re
    dollar_matches = re.findall(r"\$[\d,.]+ ?(?:billion|million|b\b|m\b)", text, re.IGNORECASE)
    for m in dollar_matches:
        if "billion" in m.lower():
            score += 10.0
        else:
            score += 3.0

    # Bonus for specific high-value terms
    if any(kw in text for kw in ["765 kv", "500 kv", "345 kv", "hvdc", "high voltage"]):
        score += 8.0
    if any(kw in text for kw in ["datacenter", "data center", "hyperscale", "ai campus"]):
        score += 5.0
    if "nuclear" in text or "smr" in text:
        score += 5.0

    return min(round(score, 1), 100.0)


def _extract_company(filing: dict) -> str:
    """Best-effort: extract company/utility name from FERC filing metadata."""
    # EFTS returns "applicant" or "companyName" fields on some records
    for field in ("applicant", "companyName", "company_name", "filer"):
        val = filing.get(field)
        if val and isinstance(val, str) and len(val) > 2:
            return val.strip()

    # Fall back to docket prefix (e.g., "ER26-1234" → utility filed with FERC)
    docket = filing.get("docket_number") or filing.get("docketNumber") or ""
    if docket:
        return f"FERC Docket {docket}"

    return "Unknown Utility (FERC Filing)"


def _determine_sector(filing: dict, query_label: str) -> str:
    text = (
        (filing.get("title") or "") + " " +
        (filing.get("description") or "") + " " +
        query_label
    ).lower()

    if any(kw in text for kw in ["nuclear", "smr", "uranium", "reactor"]):
        return "Nuclear & Critical Minerals"
    if any(kw in text for kw in ["defense", "military", "dod", "pentagon"]):
        return "Defense"
    return "Power & Grid Infrastructure"


def fetch_ferc_filings(lookback_days: int = LOOKBACK_DAYS) -> list[dict]:
    """
    Query FERC EFTS API for recent filings matching EPC-relevant search terms.
    Returns list of signal dicts ready for Airtable insertion.
    """
    start_date, end_date = _get_date_range()
    signals = []
    seen_dockets = set()  # Deduplicate across queries by docket number

    for query, base_score, label in FERC_QUERIES:
        params = {
            "q": query,
            "dateRange": "custom",
            "startDate": start_date,
            "endDate": end_date,
            "sortOrder": "Last Modified Date",
            "sortDir": "DESC",
            "rows": 50,  # Max rows per request
        }

        try:
            resp = requests.get(
                EFTS_BASE_URL,
                params=params,
                headers=_HEADERS,
                timeout=30,
            )

            if resp.status_code == 429:
                logger.warning(f"[FERC EFTS] Rate limited on query: {label}")
                continue
            if resp.status_code != 200:
                logger.warning(
                    f"[FERC EFTS] HTTP {resp.status_code} for query '{label}': "
                    f"{resp.text[:200]}"
                )
                continue

            data = resp.json()

            # EFTS returns either {"hits": {"hits": [...]}} or {"response": {"docs": [...]}}
            # Handle both shapes
            filings = []
            if "hits" in data:
                raw_hits = data["hits"].get("hits", [])
                filings = [h.get("_source", h) for h in raw_hits]
            elif "response" in data:
                filings = data["response"].get("docs", [])
            elif isinstance(data, list):
                filings = data

            if not filings:
                logger.info(f"[FERC EFTS] '{label}': 0 results ({start_date} to {end_date})")
                continue

            count = 0
            for filing in filings:
                docket = (
                    filing.get("docket_number")
                    or filing.get("docketNumber")
                    or filing.get("accession_number")
                    or ""
                )
                # Deduplicate by docket + label to allow same docket across different queries
                dedup_key = f"{docket}:{label}"
                if dedup_key in seen_dockets:
                    continue
                seen_dockets.add(dedup_key)

                title = filing.get("title") or filing.get("document_title") or f"FERC Filing — {label}"
                filed_date = (
                    filing.get("filed_date")
                    or filing.get("filedDate")
                    or filing.get("last_modified")
                    or end_date
                )
                # Normalize date to YYYY-MM-DD
                if isinstance(filed_date, str) and "T" in filed_date:
                    filed_date = filed_date[:10]
                elif isinstance(filed_date, str) and len(filed_date) >= 10:
                    filed_date = filed_date[:10]

                company = _extract_company(filing)
                sector = _determine_sector(filing, label)
                heat = _calculate_heat_score(base_score, filing)

                description = filing.get("description") or filing.get("full_text", "")[:500]
                raw_content = (
                    f"FERC Filing: {title}\n"
                    f"Docket: {docket} | Type: {label} | Filed: {filed_date}\n"
                    f"Filer: {company}\n"
                    f"{description[:1000]}"
                )

                link = ""
                if docket:
                    # FERC eLibrary direct link (may require browser, but useful as reference)
                    link = f"https://elibrary.ferc.gov/eLibrary/docID/{docket}"

                signals.append({
                    "signal_type": "ferc_filing",
                    "source": "FERC EFTS",
                    "company_name": company,
                    "sector": sector,
                    "signal_date": filed_date,
                    "raw_content": raw_content,
                    "heat_score": heat,
                    "notes": link or f"FERC EFTS query: {label} | Docket: {docket}",
                })
                count += 1

            logger.info(f"[FERC EFTS] '{label}': {count} signals ({start_date} to {end_date})")

        except requests.exceptions.Timeout:
            logger.warning(f"[FERC EFTS] Timeout on query: {label}")
        except ValueError as e:
            logger.warning(f"[FERC EFTS] JSON parse error for query '{label}': {e}")
        except Exception as e:
            logger.warning(f"[FERC EFTS] Error on query '{label}': {e}")

    logger.info(f"[FERC EFTS] Total: {len(signals)} signals from {lookback_days}-day lookback")
    return signals


def run_poller(push_to_airtable: bool = True) -> dict:
    """
    Poll FERC EFTS API for new filings.
    Returns dict with stats.
    """
    signals = fetch_ferc_filings(lookback_days=LOOKBACK_DAYS)

    signals_pushed = 0
    if push_to_airtable and signals:
        try:
            from storage.airtable import get_client
            at = get_client()

            for sig in signals:
                try:
                    at.insert_signal(
                        signal_type=sig["signal_type"],
                        source=sig["source"],
                        company_name=sig["company_name"],
                        sector=sig["sector"],
                        signal_date=sig["signal_date"],
                        raw_content=sig["raw_content"],
                        heat_score=sig["heat_score"],
                        notes=sig["notes"],
                    )
                    signals_pushed += 1
                except Exception as e:
                    logger.warning(f"[FERC EFTS] Airtable insert failed: {e}")

        except Exception as e:
            logger.error(f"[FERC EFTS] Airtable client error: {e}")

    return {
        "ferc_filings_found": len(signals),
        "signals_pushed": signals_pushed,
        "queries_run": len(FERC_QUERIES),
        "lookback_days": LOOKBACK_DAYS,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import json
    result = run_poller(push_to_airtable=False)
    print(json.dumps(result, indent=2))
