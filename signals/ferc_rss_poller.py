"""
signals/ferc_rss_poller.py
Federal Register API poller for FERC notices.

Replaces the dead FERC EFTS endpoint (efts.ferc.gov no longer resolves).
Queries the Federal Register API — no auth needed, structured JSON, reliable.

API: https://www.federalregister.gov/api/v1/articles.json
     ?conditions[agencies][]=federal-energy-regulatory-commission
Docs: https://www.federalregister.gov/reader-aids/developer-resources/rest-api

Signal logic:
  - Interconnection agreement / generator interconnection → heat 20
  - PPA / energy storage interconnection               → heat 18
  - Transmission construction / upgrade / expansion    → heat 15
  - Rate case / IRP / integrated resource plan         → heat 12
  - Hydro license / relicensing                        → heat 10
  - Administrative / clerical notices                  → skipped
"""

import logging
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

FEDERAL_REGISTER_URL = "https://www.federalregister.gov/api/v1/articles.json"
FERC_AGENCY_SLUG = "federal-energy-regulatory-commission"

LOOKBACK_DAYS = 7
PER_PAGE = 50  # max allowed by Federal Register API

# Ordered from highest to lowest priority — first match wins for base score
SIGNAL_RULES = [
    (20.0, "Interconnection Agreement", [
        "interconnection agreement", "generator interconnection",
        "transmission interconnection", "large generator interconnection",
        "small generator interconnection",
    ]),
    (18.0, "PPA / Storage Interconnection", [
        "power purchase agreement", " ppa ", "energy storage interconnection",
        "battery storage", "pumped storage",
    ]),
    (15.0, "Transmission Construction", [
        "transmission line", "transmission project", "transmission upgrade",
        "transmission expansion", "transmission facility", "new transmission",
        "overhead line", "underground cable", "substation construction",
    ]),
    (12.0, "Rate Case / IRP", [
        "rate case", "rate schedule", "integrated resource plan", " irp ",
        "cost of service", "wholesale rate",
    ]),
    (10.0, "Hydro License", [
        "hydroelectric", "hydro license", "relicensing", "water power license",
    ]),
]

# Bonus terms that boost any matched signal
BONUS_TERMS = {
    "billion":      10.0,
    "765 kv":       8.0,
    "500 kv":       8.0,
    "345 kv":       5.0,
    "hvdc":         8.0,
    "high voltage": 5.0,
    "data center":  5.0,
    "datacenter":   5.0,
    "hyperscale":   5.0,
    "nuclear":      5.0,
    " smr ":        5.0,
    "solar":        3.0,
    "wind":         3.0,
    "gigawatt":     5.0,
    " gw ":         3.0,
    " mw ":         2.0,
}

# Skip purely administrative / clerical notices — no EPC signal value
SKIP_KEYWORDS = [
    "comment request", "paperwork reduction", "information collection",
    "omb review", "notice of filing", "delegation of authority",
    "sunshine act", "closed meeting", "open meeting",
]


def _get_date_range(lookback_days: int) -> tuple[str, str]:
    end = datetime.utcnow()
    start = end - timedelta(days=lookback_days)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def _classify(title: str, abstract: str) -> tuple[float, str] | None:
    """Return (base_heat_score, label) for first matching rule, or None to skip."""
    text = (title + " " + (abstract or "")).lower()

    if any(kw in text for kw in SKIP_KEYWORDS):
        return None

    for base_score, label, keywords in SIGNAL_RULES:
        if any(kw in text for kw in keywords):
            return base_score, label

    return None


def _boost_score(base: float, title: str, abstract: str) -> float:
    text = (title + " " + (abstract or "")).lower()
    score = base
    for term, bonus in BONUS_TERMS.items():
        if term in text:
            score += bonus
    dollar_hits = re.findall(r"\$[\d,.]+ ?(?:billion|million)", text, re.IGNORECASE)
    score += len(dollar_hits) * 3.0
    return min(round(score, 1), 100.0)


def _extract_company(title: str, abstract: str) -> str:
    """
    FERC notice titles typically start with 'Company Name; Notice of ...'
    Extract the company from the prefix before the semicolon.
    """
    match = re.match(r"^([^;]+);", title)
    if match:
        candidate = match.group(1).strip()
        if not any(w in candidate.lower() for w in ["commission", "ferc", "notice", "order"]):
            return candidate

    if abstract:
        match = re.search(
            r"\b([A-Z][a-zA-Z\s&,.]+(?:Inc|LLC|Corp|Company|Authority|Power|Energy|Electric|Utility|Co)\.?)\b",
            abstract,
        )
        if match:
            return match.group(1).strip()

    return "FERC Filing"


def _determine_sector(title: str, abstract: str) -> str:
    text = (title + " " + (abstract or "")).lower()
    if any(kw in text for kw in ["nuclear", "smr", "uranium", "reactor", "atomic"]):
        return "Nuclear & Critical Minerals"
    if any(kw in text for kw in ["defense", "military", "dod", "pentagon"]):
        return "Defense"
    if any(kw in text for kw in ["natural gas", "lng", "pipeline", "gas transmission"]):
        return "Natural Gas Infrastructure"
    return "Power & Grid Infrastructure"


def fetch_ferc_filings(lookback_days: int = LOOKBACK_DAYS) -> list[dict]:
    """
    Query Federal Register API for recent FERC notices.
    Returns list of signal dicts ready for Airtable insertion.
    """
    start_date, end_date = _get_date_range(lookback_days)
    signals = []
    seen_docs: set[str] = set()
    page = 1

    while True:
        try:
            resp = requests.get(
                FEDERAL_REGISTER_URL,
                params={
                    "conditions[agencies][]": FERC_AGENCY_SLUG,
                    "conditions[publication_date][gte]": start_date,
                    "conditions[publication_date][lte]": end_date,
                    "per_page": PER_PAGE,
                    "page": page,
                    "order": "newest",
                    "fields[]": ["title", "publication_date", "abstract", "document_number", "html_url"],
                },
                timeout=20,
            )
        except requests.exceptions.Timeout:
            logger.warning("[FERC FR] Timeout on page %d", page)
            break
        except Exception as e:
            logger.warning("[FERC FR] Request error on page %d: %s", page, e)
            break

        if resp.status_code == 429:
            logger.warning("[FERC FR] Rate limited — stopping pagination")
            break
        if resp.status_code != 200:
            logger.warning("[FERC FR] HTTP %d: %s", resp.status_code, resp.text[:200])
            break

        data = resp.json()
        results = data.get("results", [])
        if not results:
            break

        for article in results:
            doc_num = article.get("document_number", "")
            if doc_num in seen_docs:
                continue
            seen_docs.add(doc_num)

            title    = article.get("title", "")
            abstract = article.get("abstract") or ""
            pub_date = article.get("publication_date", end_date)
            html_url = article.get("html_url", "")

            classification = _classify(title, abstract)
            if classification is None:
                continue

            base_score, label = classification
            heat    = _boost_score(base_score, title, abstract)
            company = _extract_company(title, abstract)
            sector  = _determine_sector(title, abstract)

            raw_content = (
                f"FERC Notice: {title}\n"
                f"Type: {label} | Published: {pub_date} | Doc: {doc_num}\n"
                f"{abstract[:800]}"
            )

            signals.append({
                "signal_type": "ferc_filing",
                "source": "Federal Register (FERC)",
                "company_name": company,
                "sector": sector,
                "signal_date": pub_date,
                "raw_content": raw_content,
                "heat_score": heat,
                "notes": html_url or f"FERC doc {doc_num} | {label}",
            })

        total_pages = data.get("total_pages", 1)
        if page >= total_pages:
            break
        page += 1

    logger.info(
        "[FERC FR] %d signals from %d FERC notices (%s to %s)",
        len(signals), len(seen_docs), start_date, end_date,
    )
    return signals


def run_poller(push_to_airtable: bool = True) -> dict:
    """
    Poll Federal Register for recent FERC notices.
    Keeps same interface as the original FERC EFTS poller.
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
                    logger.warning("[FERC FR] Airtable insert failed: %s", e)
        except Exception as e:
            logger.error("[FERC FR] Airtable client error: %s", e)

    return {
        "ferc_filings_found": len(signals),
        "signals_pushed": signals_pushed,
        "queries_run": 1,
        "lookback_days": LOOKBACK_DAYS,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import json
    result = run_poller(push_to_airtable=False)
    print(json.dumps(result, indent=2))
