"""
signals/federal_register.py
Polls the Federal Register API for regulatory signals indicating upcoming
infrastructure projects — proposed rules, notices of intent, environmental
impact statements, records of decision.

API: https://www.federalregister.gov/api/v1/documents.json
No API key required (fully open).
"""

import json
import logging
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DB_PATH

logger = logging.getLogger(__name__)

FR_API_URL = "https://www.federalregister.gov/api/v1/documents.json"

LOOKBACK_DAYS = 14

DOCUMENT_TYPES = ["Notice", "Proposed Rule", "Rule", "Presidential Document"]

# Heat scores by document type / subtype
HEAT_SCORES = {
    "Proposed Rule": 20,
    "Notice": 12,
    "Rule": 22,              # Final Rule
    "Presidential Document": 18,
}

# Additional heat for specific phrases in title/abstract
HEAT_KEYWORDS = {
    "notice of intent": 18,
    "record of decision": 25,
    "environmental impact statement": 20,
    "combined license": 22,
    "final rule": 22,
}

# Agency slugs → display name + default sector
AGENCIES = {
    "energy-department": {
        "name": "DOE",
        "sector": "Power & Grid Infrastructure",
    },
    "environmental-protection-agency": {
        "name": "EPA",
        "sector": "Water & Wastewater Infrastructure",
    },
    "defense-department": {
        "name": "DOD",
        "sector": "Defense & Military Construction",
    },
    "nuclear-regulatory-commission": {
        "name": "NRC",
        "sector": "Nuclear",
    },
    "federal-energy-regulatory-commission": {
        "name": "FERC",
        "sector": "Power & Grid Infrastructure",
    },
    "transportation-department": {
        "name": "DOT",
        "sector": "Power & Grid Infrastructure",
    },
    "interior-department": {
        "name": "DOI",
        "sector": "Industrial & Manufacturing Facilities",
    },
    "engineers-corps": {
        "name": "USACE",
        "sector": "Water & Wastewater Infrastructure",
    },
}

# Sector-specific search keywords
SECTOR_KEYWORDS = {
    "Power & Grid Infrastructure": [
        "interconnection", "transmission", "substation", "grid", "generator",
        "NEVI", "electric vehicle", "charging",
    ],
    "Water & Wastewater Infrastructure": [
        "water treatment", "NPDES", "consent decree", "state revolving fund",
        "water", "flood control",
    ],
    "Defense & Military Construction": [
        "military construction", "MILCON", "DD 1391",
    ],
    "Nuclear": [
        "nuclear", "reactor", "combined license", "SMR",
    ],
    "Data Center & AI Infrastructure": [
        "data center", "critical facility",
    ],
    "Industrial & Manufacturing Facilities": [
        "critical mineral", "mining", "rare earth",
    ],
}


def _ensure_db(db_path: Path) -> None:
    """Create deduplication table if not exists."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS federal_register_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_number TEXT UNIQUE,
            title TEXT,
            document_type TEXT,
            publication_date TEXT,
            agencies TEXT,
            matched_sector TEXT,
            heat_score REAL,
            html_url TEXT,
            scraped_at TEXT
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_fr_sector ON federal_register_signals(matched_sector)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_fr_date ON federal_register_signals(publication_date)")
    conn.commit()
    conn.close()


def _determine_heat_score(doc: dict) -> float:
    """Calculate heat score based on document type and keyword matches."""
    doc_type = doc.get("type", "Notice")
    score = HEAT_SCORES.get(doc_type, 12)

    # Check title + abstract for high-value phrases — use highest match
    title = (doc.get("title") or "").lower()
    abstract = (doc.get("abstract") or "").lower()
    text = title + " " + abstract

    for phrase, phrase_score in HEAT_KEYWORDS.items():
        if phrase in text:
            score = max(score, phrase_score)

    return float(score)


def _determine_sector(doc: dict, agency_sector: str) -> str:
    """Refine sector based on keyword matching in title + abstract."""
    title = (doc.get("title") or "").lower()
    abstract = (doc.get("abstract") or "").lower()
    text = title + " " + abstract

    # Check each sector's keywords — return first match
    for sector, keywords in SECTOR_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text:
                return sector

    return agency_sector


def _fetch_documents(agency_slug: str, start_date: str, end_date: str, page: int = 1) -> dict:
    """Query Federal Register API for documents from a specific agency."""
    params = {
        "conditions[agencies][]": agency_slug,
        "conditions[type][]": DOCUMENT_TYPES,
        "conditions[publication_date][gte]": start_date,
        "conditions[publication_date][lte]": end_date,
        "fields[]": [
            "title", "abstract", "agencies", "type", "document_number",
            "publication_date", "html_url",
        ],
        "per_page": 100,
        "page": page,
        "order": "newest",
    }
    try:
        resp = requests.get(FR_API_URL, params=params, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"[FedRegister] API error for {agency_slug}: {e}")
        return {}


def _build_raw_text(doc: dict) -> str:
    """Compose raw_text field from document metadata."""
    agencies = ", ".join(
        a.get("name", "") for a in (doc.get("agencies") or [])
    )
    parts = [
        f"Title: {doc.get('title', 'N/A')}",
        f"Abstract: {doc.get('abstract', 'N/A')}",
        f"Agencies: {agencies}",
        f"Document Type: {doc.get('type', 'N/A')}",
        f"Publication Date: {doc.get('publication_date', 'N/A')}",
        f"URL: {doc.get('html_url', 'N/A')}",
    ]
    return "\n".join(parts)


def run_scraper() -> dict:
    """Main entry point — fetch Federal Register documents and push signals."""
    _ensure_db(DB_PATH)

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%d")

    logger.info(f"[FedRegister] Scanning {len(AGENCIES)} agencies | {start_date} → {end_date}")

    all_docs: list[dict] = []
    seen_doc_numbers: set[str] = set()

    for agency_slug, agency_info in AGENCIES.items():
        data = _fetch_documents(agency_slug, start_date, end_date)
        results = data.get("results", [])
        logger.info(f"[FedRegister] {agency_info['name']}: {len(results)} documents")

        for doc in results:
            doc_number = doc.get("document_number", "")
            if not doc_number or doc_number in seen_doc_numbers:
                continue
            seen_doc_numbers.add(doc_number)

            sector = _determine_sector(doc, agency_info["sector"])
            heat_score = _determine_heat_score(doc)

            all_docs.append({
                "document_number": doc_number,
                "title": doc.get("title", ""),
                "document_type": doc.get("type", ""),
                "publication_date": doc.get("publication_date", ""),
                "agencies": ", ".join(
                    a.get("name", "") for a in (doc.get("agencies") or [])
                ),
                "matched_sector": sector,
                "heat_score": heat_score,
                "html_url": doc.get("html_url", ""),
                "raw_text": _build_raw_text(doc),
            })

        # Paginate if needed
        total_pages = data.get("total_pages", 1)
        for page in range(2, min(total_pages + 1, 6)):  # Cap at 5 pages per agency
            data = _fetch_documents(agency_slug, start_date, end_date, page=page)
            for doc in data.get("results", []):
                doc_number = doc.get("document_number", "")
                if not doc_number or doc_number in seen_doc_numbers:
                    continue
                seen_doc_numbers.add(doc_number)

                sector = _determine_sector(doc, agency_info["sector"])
                heat_score = _determine_heat_score(doc)

                all_docs.append({
                    "document_number": doc_number,
                    "title": doc.get("title", ""),
                    "document_type": doc.get("type", ""),
                    "publication_date": doc.get("publication_date", ""),
                    "agencies": ", ".join(
                        a.get("name", "") for a in (doc.get("agencies") or [])
                    ),
                    "matched_sector": sector,
                    "heat_score": heat_score,
                    "html_url": doc.get("html_url", ""),
                    "raw_text": _build_raw_text(doc),
                })

    logger.info(f"[FedRegister] {len(all_docs)} total documents collected")

    # Store in SQLite for deduplication
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    inserted = 0
    for doc in all_docs:
        try:
            c.execute("""
                INSERT OR IGNORE INTO federal_register_signals
                (document_number, title, document_type, publication_date,
                 agencies, matched_sector, heat_score, html_url, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc["document_number"], doc["title"], doc["document_type"],
                doc["publication_date"], doc["agencies"], doc["matched_sector"],
                doc["heat_score"], doc["html_url"], datetime.now().isoformat(),
            ))
            if c.rowcount > 0:
                inserted += 1
        except sqlite3.Error as e:
            logger.warning(f"[FedRegister] DB error: {e}")
    conn.commit()
    conn.close()

    # Push new signals to Airtable
    pushed = 0
    if inserted > 0:
        try:
            from storage.airtable import get_client
            at = get_client()

            # Re-query SQLite for only newly inserted docs (scraped in last minute)
            conn = sqlite3.connect(str(DB_PATH))
            c = conn.cursor()
            cutoff = (datetime.now() - timedelta(minutes=2)).isoformat()
            c.execute("""
                SELECT document_number, title, document_type, publication_date,
                       agencies, matched_sector, heat_score, html_url
                FROM federal_register_signals
                WHERE scraped_at >= ?
            """, (cutoff,))
            new_rows = c.fetchall()
            conn.close()

            for (doc_num, title, doc_type, pub_date, agencies,
                 sector, heat, url) in new_rows:
                raw_text = (
                    f"Title: {title}\n"
                    f"Agencies: {agencies}\n"
                    f"Document Type: {doc_type}\n"
                    f"Publication Date: {pub_date}\n"
                    f"URL: {url}"
                )
                at.insert_signal(
                    signal_type="federal_register",
                    source=f"Federal Register / {agencies}",
                    company_name=agencies or "Federal Agency",
                    sector=sector,
                    signal_date=(pub_date or "")[:10],
                    raw_content=raw_text,
                    heat_score=heat,
                    notes=url,
                )
                pushed += 1

            logger.info(f"[FedRegister] Pushed {pushed} new signals to Airtable")
        except Exception as e:
            logger.error(f"[FedRegister] Airtable push failed: {e}")

    # Summary
    sector_counts: dict[str, int] = {}
    for doc in all_docs:
        s = doc["matched_sector"]
        sector_counts[s] = sector_counts.get(s, 0) + 1

    logger.info(f"[FedRegister] {inserted} new inserts | {sector_counts}")
    return {
        "total_documents": len(all_docs),
        "new_inserts": inserted,
        "pushed_to_airtable": pushed,
        "sector_breakdown": sector_counts,
    }


def run() -> dict:
    """Entry point for scheduler.py."""
    return run_scraper()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run_scraper()
    print(json.dumps(result, indent=2))
