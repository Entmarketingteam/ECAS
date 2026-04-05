"""
signals/fda_warning_letter_monitor.py

FDA Warning Letter + State Board Action signal monitor for the Healthcare
Referral Pipeline (compounding pharmacy beachhead).

Detects pharmacies that have recently received a regulatory action and
schedules outreach 30 days post-action — the recovery/rebuild window.

Two phases:
  Phase 1 — detect:
    - Fetch FDA warning letters RSS feed (weekly, filter for pharmacy keywords)
    - Scrape 5 state board disciplinary action pages in parallel
    - Lookup NPI by organization name + state
    - Save to Airtable appoi8SzEJY8in57x with status="pending_wait"
    - Does NOT enroll in Smartlead — only logs the signal

  Phase 2 — trigger:
    - Query Airtable for records where status="pending_wait" AND
      scheduled_outreach_date <= today
    - Enrich with Findymail email lookup
    - Enroll in Smartlead recovery-framing sequence (env: SL_CAMPAIGN_RECOVERY)
    - Update record status to "enrolled"
    - Notify #ecas-ops via Slack

Cron: 0 7 * * 1  (Phase 1 runs weekly Monday 7am)
      0 8 * * *   (Phase 2 runs daily — checks for records ready to trigger)

CLI: python fda_warning_letter_monitor.py --phase [detect|trigger|both]
     default: both

All secrets from env:
  AIRTABLE_API_KEY
  FINDYMAIL_API_KEY
  SMARTLEAD_API_KEY
  SLACK_WEBHOOK_URL
"""

import argparse
import json
import logging
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ─── Config ──────────────────────────────────────────────────────────────────

AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY", "")
FINDYMAIL_API_KEY = os.environ.get("FINDYMAIL_API_KEY", "")
SMARTLEAD_API_KEY = os.environ.get("SMARTLEAD_API_KEY", "")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")

# Airtable base + table for regulatory signals
AIRTABLE_BASE_ID = "appoi8SzEJY8in57x"
AIRTABLE_TABLE_NAME = "regulatory_signals"   # create this table in Airtable
AIRTABLE_API_BASE = "https://api.airtable.com/v0"
AIRTABLE_RATE_DELAY = 0.25  # 4 req/sec — under the 5/sec limit

# Smartlead campaign for recovery-framing outreach
SL_CAMPAIGN_RECOVERY = os.environ.get("SL_CAMPAIGN_RECOVERY", "")
SMARTLEAD_API_BASE = "https://server.smartlead.ai/api/v1"

# FDA Warning Letters RSS
FDA_RSS_URL = (
    "https://www.fda.gov/about-fda/contact-fda/stay-informed/"
    "rss-feeds/warning-letters/rss.xml"
)

# Pharmacy / compounding keywords for FDA filter
PHARMACY_KEYWORDS = [
    "pharmacy", "compounding", "503a", "503b", "sterile", "non-sterile",
    "beyond-use date", "beyond-use", "usp", "compounded", "dispensing",
    "pharmacist", "drug quality", "current good manufacturing",
]

# Chain pharmacies to skip — not outreach targets
CHAIN_EXCLUDE = [
    "walgreens", "cvs", "walmart", "rite aid", "kroger", "costco",
    "target", "albertsons", "safeway", "publix", "heb", "meijer",
    "express scripts", "optumrx", "caremark", "humana pharmacy",
    "kaiser", "va pharmacy", "veterans affairs",
]

# User-Agent header to avoid bot blocks on state board pages
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

REQUEST_TIMEOUT = 20  # seconds

# ─── State Board Scraper Config ───────────────────────────────────────────────
# Each entry describes how to scrape disciplinary/enforcement actions.
# strategy: "table" = parse HTML tables | "list" = parse <ul>/<li> or <div> blocks
# name_selector: CSS selector for the pharmacy name within each row/item
# date_selector: CSS selector for the action date
# type_selector: CSS selector for the action type/description

STATE_BOARDS = [
    {
        "state": "TX",
        "url": "https://www.pharmacy.texas.gov/compliance/enforcement",
        "strategy": "table",
        "notes": "Texas State Board of Pharmacy enforcement actions",
    },
    {
        "state": "FL",
        "url": "https://flhealthsource.gov/MQA/enforcement",
        "strategy": "table",
        "notes": "Florida MQA enforcement actions",
    },
    {
        "state": "CA",
        "url": "https://www.pharmacy.ca.gov/enforcement/fy1011/fines.shtml",
        "strategy": "table",
        "notes": "California Board of Pharmacy enforcement",
    },
    {
        "state": "NY",
        "url": "https://www.op.nysed.gov/oped/enforcement",
        "strategy": "table",
        "notes": "New York Office of Professions enforcement",
    },
    {
        "state": "IL",
        "url": "https://idfpr.illinois.gov/profs/Pharmacy.asp",
        "strategy": "table",
        "notes": "Illinois IDFPR pharmacy enforcement",
    },
]

# NPI Registry endpoint (public, no auth)
NPI_REGISTRY_URL = "https://npiregistry.cms.hhs.gov/api/"

# Findymail endpoint
FINDYMAIL_SEARCH_URL = "https://app.findymail.com/api/search/name"


# ─── Airtable helpers ─────────────────────────────────────────────────────────

def _at_headers() -> dict:
    return {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json",
    }


def _at_url(table_name: str) -> str:
    return f"{AIRTABLE_API_BASE}/{AIRTABLE_BASE_ID}/{table_name}"


def airtable_get_pending(table_name: str) -> list[dict]:
    """
    Fetch all records with status='pending_wait' where
    scheduled_outreach_date <= today.
    """
    today = datetime.utcnow().strftime("%Y-%m-%d")
    formula = (
        f"AND("
        f"{{status}}='pending_wait',"
        f"IS_BEFORE({{scheduled_outreach_date}},DATEADD(TODAY(),1,'days'))"
        f")"
    )
    records = []
    offset = None
    while True:
        params = {
            "filterByFormula": formula,
            "maxRecords": 100,
        }
        if offset:
            params["offset"] = offset
        try:
            time.sleep(AIRTABLE_RATE_DELAY)
            resp = requests.get(
                _at_url(table_name),
                headers=_at_headers(),
                params=params,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            records.extend(data.get("records", []))
            offset = data.get("offset")
            if not offset:
                break
        except requests.RequestException as e:
            logger.error(f"[Airtable] GET pending records error: {e}")
            break
    return records


def airtable_insert(table_name: str, fields: dict) -> Optional[str]:
    """
    Insert a record. Returns Airtable record ID or None.
    Skips insert if company_name + action_date + source already exists.
    """
    company = fields.get("company_name", "")
    action_date = fields.get("action_date", "")[:10] if fields.get("action_date") else ""
    source = fields.get("source", "")

    if not company:
        return None

    # Dedup check
    escaped = company.replace("'", "\\'")
    dedup_formula = (
        f"AND("
        f"LOWER({{company_name}})=LOWER('{escaped}'),"
        f"LEFT({{action_date}},10)='{action_date}',"
        f"{{source}}='{source}'"
        f")"
    )
    try:
        time.sleep(AIRTABLE_RATE_DELAY)
        resp = requests.get(
            _at_url(table_name),
            headers=_at_headers(),
            params={
                "filterByFormula": dedup_formula,
                "maxRecords": 1,
                "fields[]": ["company_name", "action_date"],
            },
            timeout=30,
        )
        resp.raise_for_status()
        existing = resp.json().get("records", [])
        if existing:
            logger.info(
                f"[Airtable] Skipping duplicate: {company} / {action_date}"
            )
            return existing[0]["id"]
    except requests.RequestException as e:
        logger.warning(f"[Airtable] Dedup check error for {company}: {e}")

    # Insert
    try:
        time.sleep(AIRTABLE_RATE_DELAY)
        resp = requests.post(
            _at_url(table_name),
            headers=_at_headers(),
            json={"fields": fields},
            timeout=30,
        )
        resp.raise_for_status()
        record = resp.json()
        logger.info(f"[Airtable] Inserted: {company} -> {record['id']}")
        return record["id"]
    except requests.RequestException as e:
        logger.error(f"[Airtable] Insert error for {company}: {e}")
        return None


def airtable_update(table_name: str, record_id: str, fields: dict) -> bool:
    """Update an existing record. Returns True on success."""
    try:
        time.sleep(AIRTABLE_RATE_DELAY)
        resp = requests.patch(
            f"{_at_url(table_name)}/{record_id}",
            headers=_at_headers(),
            json={"fields": fields},
            timeout=30,
        )
        resp.raise_for_status()
        return True
    except requests.RequestException as e:
        logger.error(f"[Airtable] PATCH {record_id} error: {e}")
        return False


# ─── FDA Warning Letters ───────────────────────────────────────────────────────

def _is_pharmacy_related(text: str) -> bool:
    """Return True if text contains any pharmacy/compounding keyword."""
    lower = (text or "").lower()
    return any(kw in lower for kw in PHARMACY_KEYWORDS)


def _is_chain_pharmacy(name: str) -> bool:
    lower = (name or "").lower()
    return any(chain in lower for chain in CHAIN_EXCLUDE)


def fetch_fda_warning_letters() -> list[dict]:
    """
    Fetch FDA warning letters RSS and filter for pharmacy/compounding-related
    entries published in the last 30 days.

    Returns list of dicts with keys:
      company_name, action_date, action_type, source, source_url, raw_notes
    """
    logger.info("[FDA] Fetching warning letters RSS...")
    results = []

    try:
        resp = requests.get(
            FDA_RSS_URL,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        content = resp.text
    except requests.RequestException as e:
        logger.error(f"[FDA] RSS fetch error: {e}")
        return []

    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        logger.error(f"[FDA] RSS parse error: {e}")
        return []

    # RSS 2.0 structure: channel > item
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    channel = root.find("channel")
    if channel is None:
        # Try Atom format
        items = root.findall("{http://www.w3.org/2005/Atom}entry")
    else:
        items = channel.findall("item")

    cutoff = datetime.utcnow() - timedelta(days=30)

    for item in items:
        # Extract fields — handle both RSS 2.0 and Atom
        title = (
            (item.findtext("title") or "")
            + " "
            + (item.findtext("{http://www.w3.org/2005/Atom}title") or "")
        ).strip()
        description = (
            (item.findtext("description") or "")
            + " "
            + (item.findtext("{http://www.w3.org/2005/Atom}summary") or "")
        ).strip()
        link = (
            item.findtext("link")
            or item.findtext("{http://www.w3.org/2005/Atom}link")
            or ""
        )
        pub_date_raw = (
            item.findtext("pubDate")
            or item.findtext("{http://www.w3.org/2005/Atom}published")
            or item.findtext("{http://www.w3.org/2005/Atom}updated")
            or ""
        ).strip()

        # Parse date
        action_date = _parse_date(pub_date_raw)
        if action_date:
            try:
                dt = datetime.strptime(action_date, "%Y-%m-%d")
                if dt < cutoff:
                    continue
            except ValueError:
                pass

        combined_text = f"{title} {description}"
        if not _is_pharmacy_related(combined_text):
            continue

        # Extract company name — typically first part of title before comma/dash
        company_name = _extract_company_from_fda_title(title)
        if not company_name:
            company_name = title[:80]

        if _is_chain_pharmacy(company_name):
            logger.debug(f"[FDA] Skipping chain pharmacy: {company_name}")
            continue

        results.append({
            "company_name": company_name,
            "action_date": action_date or datetime.utcnow().strftime("%Y-%m-%d"),
            "action_type": "FDA Warning Letter",
            "source": "fda",
            "source_url": link,
            "raw_notes": f"Title: {title}\n\nSummary: {description[:500]}",
        })
        logger.info(f"[FDA] Found pharmacy warning letter: {company_name} ({action_date})")

    logger.info(f"[FDA] {len(results)} pharmacy-related letters found in last 30 days")
    return results


def _extract_company_from_fda_title(title: str) -> str:
    """
    FDA warning letter titles typically follow the pattern:
    'Company Name dba DBA Name' or 'Company Name - Warning Letter'
    """
    if not title:
        return ""
    # Remove common suffixes
    for suffix in [
        " - Warning Letter",
        " Warning Letter",
        "; Untitled Letter",
        " - Untitled Letter",
    ]:
        if suffix.lower() in title.lower():
            idx = title.lower().index(suffix.lower())
            title = title[:idx]
            break
    return title.strip()[:200]


def _parse_date(date_str: str) -> str:
    """
    Parse a date string in various formats to YYYY-MM-DD.
    Returns empty string if parsing fails.
    """
    if not date_str:
        return ""

    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d",
        "%B %d, %Y",
        "%b %d, %Y",
        "%m/%d/%Y",
        "%d-%b-%Y",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            continue
    return ""


# ─── State Board Scrapers ─────────────────────────────────────────────────────

def scrape_state_board(board: dict) -> list[dict]:
    """
    Scrape a single state board enforcement page.
    Returns list of dicts with: company_name, action_date, action_type, state.

    Catches all exceptions — a broken page should not stop other states.
    """
    state = board["state"]
    url = board["url"]
    logger.info(f"[StateBoard/{state}] Scraping {url}")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        html = resp.text
    except requests.exceptions.Timeout:
        logger.warning(f"[StateBoard/{state}] Timeout fetching {url}")
        return []
    except requests.exceptions.ConnectionError as e:
        logger.warning(f"[StateBoard/{state}] Connection error: {e}")
        return []
    except requests.RequestException as e:
        logger.warning(f"[StateBoard/{state}] Request error: {e}")
        return []

    try:
        soup = BeautifulSoup(html, "html.parser")
        return _parse_state_board_page(soup, state, url)
    except Exception as e:
        logger.warning(f"[StateBoard/{state}] Parse error: {e}")
        return []


def _parse_state_board_page(
    soup: BeautifulSoup, state: str, source_url: str
) -> list[dict]:
    """
    Attempt to extract pharmacy enforcement actions from an HTML page.

    Strategy (applied in order until results are found):
    1. Find HTML tables with headers containing 'name', 'date', 'action'
    2. Find definition lists / description lists
    3. Find any element with pharmacy keywords nearby a date pattern

    Returns list of action dicts.
    """
    results = []

    # Strategy 1: structured tables
    tables = soup.find_all("table")
    for table in tables:
        rows = _extract_table_rows(table, state, source_url)
        if rows:
            results.extend(rows)

    if results:
        return results

    # Strategy 2: definition lists or list items with dates
    results = _extract_list_items(soup, state, source_url)
    if results:
        return results

    # Strategy 3: generic text scan for date patterns near pharmacy names
    results = _extract_text_scan(soup, state, source_url)
    return results


def _extract_table_rows(
    table, state: str, source_url: str
) -> list[dict]:
    """Extract enforcement actions from an HTML table."""
    results = []
    rows = table.find_all("tr")
    if len(rows) < 2:
        return []

    # Parse header row
    header_row = rows[0]
    headers = [
        th.get_text(strip=True).lower()
        for th in header_row.find_all(["th", "td"])
    ]

    if not headers:
        return []

    # Find column indexes
    name_idx = _find_col_idx(headers, ["name", "licensee", "pharmacy", "company", "entity"])
    date_idx = _find_col_idx(headers, ["date", "action date", "effective", "order date"])
    type_idx = _find_col_idx(headers, [
        "action", "type", "violation", "description", "disposition", "sanction"
    ])

    if name_idx is None:
        return []

    for row in rows[1:]:
        cells = row.find_all(["td", "th"])
        if not cells:
            continue

        def cell_text(idx):
            if idx is not None and idx < len(cells):
                return cells[idx].get_text(strip=True)
            return ""

        company_name = cell_text(name_idx)
        if not company_name or len(company_name) < 3:
            continue

        # Skip non-pharmacy entities
        if not _is_pharmacy_related(company_name) and not _looks_like_pharmacy(company_name):
            # Check action type too before skipping
            action_text = cell_text(type_idx)
            if not _is_pharmacy_related(action_text):
                continue

        if _is_chain_pharmacy(company_name):
            continue

        date_raw = cell_text(date_idx)
        action_type = cell_text(type_idx) or "State Board Action"

        results.append({
            "company_name": company_name[:200],
            "action_date": _parse_date(date_raw) or datetime.utcnow().strftime("%Y-%m-%d"),
            "action_type": action_type[:200],
            "state": state,
            "source": "state_board",
            "source_url": source_url,
            "raw_notes": f"State: {state} | Action: {action_type} | Date: {date_raw}",
        })

    return results


def _extract_list_items(
    soup: BeautifulSoup, state: str, source_url: str
) -> list[dict]:
    """Extract enforcement actions from list items or paragraphs."""
    results = []
    date_pattern = re.compile(
        r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\w+ \d{1,2},?\s*\d{4})\b"
    )

    for tag in soup.find_all(["li", "p", "dt", "dd"]):
        text = tag.get_text(strip=True)
        if len(text) < 10 or len(text) > 500:
            continue
        if not _is_pharmacy_related(text) and not _looks_like_pharmacy(text):
            continue
        if _is_chain_pharmacy(text):
            continue

        date_match = date_pattern.search(text)
        action_date = _parse_date(date_match.group(0)) if date_match else ""

        # Use the first part of the text as the company name
        company_name = text.split("\n")[0].split("|")[0].split("–")[0].strip()[:200]
        if not company_name:
            continue

        results.append({
            "company_name": company_name,
            "action_date": action_date or datetime.utcnow().strftime("%Y-%m-%d"),
            "action_type": "State Board Action",
            "state": state,
            "source": "state_board",
            "source_url": source_url,
            "raw_notes": f"State: {state} | Extracted text: {text[:300]}",
        })

    return results


def _extract_text_scan(
    soup: BeautifulSoup, state: str, source_url: str
) -> list[dict]:
    """
    Last-resort text scan: find any element containing pharmacy keywords.
    Returns at most 10 results per page to avoid noise.
    """
    results = []
    date_pattern = re.compile(
        r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})\b"
    )

    seen_names: set = set()
    for tag in soup.find_all(text=True):
        text = str(tag).strip()
        if len(text) < 5 or len(text) > 300:
            continue
        if not _is_pharmacy_related(text):
            continue
        if _is_chain_pharmacy(text):
            continue

        company_name = text[:100].strip()
        if company_name in seen_names:
            continue
        seen_names.add(company_name)

        date_match = date_pattern.search(text)
        action_date = _parse_date(date_match.group(0)) if date_match else ""

        results.append({
            "company_name": company_name,
            "action_date": action_date or datetime.utcnow().strftime("%Y-%m-%d"),
            "action_type": "State Board Action",
            "state": state,
            "source": "state_board",
            "source_url": source_url,
            "raw_notes": f"State: {state} | Text scan: {text[:300]}",
        })

        if len(results) >= 10:
            break

    return results


def _find_col_idx(headers: list[str], candidates: list[str]) -> Optional[int]:
    """Find the first header index that contains any candidate string."""
    for i, h in enumerate(headers):
        for c in candidates:
            if c in h:
                return i
    return None


def _looks_like_pharmacy(text: str) -> bool:
    """Heuristic: does the text look like a pharmacy entity name?"""
    lower = text.lower()
    return any(kw in lower for kw in [
        "pharmacy", "rx", "drug", "compounding", "apothecary", "dispensary",
        "chemist", "medicinal", "pharmaceutical",
    ])


def scrape_all_state_boards() -> list[dict]:
    """
    Scrape all state board pages in parallel (4 workers).
    Per-state exceptions are caught inside scrape_state_board.
    """
    results = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(scrape_state_board, board): board["state"]
            for board in STATE_BOARDS
        }
        for future in as_completed(futures):
            state = futures[future]
            try:
                state_results = future.result()
                logger.info(f"[StateBoard/{state}] {len(state_results)} actions found")
                results.extend(state_results)
            except Exception as e:
                logger.warning(f"[StateBoard/{state}] Unexpected error: {e}")

    return results


# ─── NPI Registry Lookup ───────────────────────────────────────────────────────

def lookup_npi(company_name: str, state: str = "") -> dict:
    """
    Query the NPI Registry by organization name + state.
    Returns dict with: npi, address, phone (or empty strings if not found).
    """
    params = {
        "version": "2.1",
        "enumeration_type": "NPI-2",   # NPI-2 = organizations
        "organization_name": company_name,
        "limit": 5,
    }
    if state:
        params["state"] = state

    try:
        time.sleep(0.3)  # NPI Registry rate limit
        resp = requests.get(
            NPI_REGISTRY_URL,
            params=params,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.warning(f"[NPI] Lookup failed for '{company_name}': {e}")
        return {"npi": "", "address": "", "phone": ""}
    except json.JSONDecodeError:
        return {"npi": "", "address": "", "phone": ""}

    results = data.get("results", [])
    if not results:
        # Retry with shorter name (first two words)
        short_name = " ".join(company_name.split()[:2])
        if short_name != company_name:
            return lookup_npi(short_name, state)
        return {"npi": "", "address": "", "phone": ""}

    # Pick best match — prefer exact substring match
    best = None
    company_lower = company_name.lower()
    for r in results:
        org = (
            r.get("basic", {}).get("organization_name", "")
            or r.get("basic", {}).get("name", "")
        ).lower()
        if company_lower in org or org in company_lower:
            best = r
            break
    if not best:
        best = results[0]

    npi = best.get("number", "")
    # Extract address
    addresses = best.get("addresses", [])
    primary_addr = next(
        (a for a in addresses if a.get("address_purpose") == "LOCATION"),
        addresses[0] if addresses else {},
    )
    addr_parts = [
        primary_addr.get("address_1", ""),
        primary_addr.get("city", ""),
        primary_addr.get("state", ""),
        primary_addr.get("postal_code", ""),
    ]
    address = ", ".join(p for p in addr_parts if p)

    # Phone
    phone = primary_addr.get("telephone_number", "")

    return {"npi": npi, "address": address, "phone": phone}


# ─── Findymail Email Lookup ────────────────────────────────────────────────────

def findymail_lookup(
    first_name: str,
    last_name: str,
    domain: str,
) -> Optional[str]:
    """
    Look up a verified email via Findymail.
    Returns email string or None if not found.
    """
    if not FINDYMAIL_API_KEY:
        logger.warning("[Findymail] FINDYMAIL_API_KEY not set — skipping enrichment")
        return None
    if not first_name or not domain:
        return None

    name = f"{first_name} {last_name}".strip()
    try:
        resp = requests.post(
            FINDYMAIL_SEARCH_URL,
            json={"name": name, "domain": domain},
            headers={
                "Authorization": f"Bearer {FINDYMAIL_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )
        if resp.status_code == 404:
            return None
        if resp.status_code == 429:
            time.sleep(2)
            return findymail_lookup(first_name, last_name, domain)
        resp.raise_for_status()
        data = resp.json()
        return data.get("email") or data.get("data", {}).get("email")
    except requests.RequestException as e:
        logger.warning(f"[Findymail] Lookup error for {name}@{domain}: {e}")
        return None


def _extract_domain_from_npi_data(record: dict) -> str:
    """
    Try to extract a company domain from NPI data (address/org name).
    Falls back to constructing a likely domain from the company name.
    """
    company = record.get("company_name", "")
    if not company:
        return ""

    # Normalize to likely domain
    clean = company.lower()
    clean = re.sub(r"[^\w\s]", "", clean)
    clean = re.sub(r"\b(pharmacy|compounding|rx|llc|inc|corp|ltd|the|and)\b", "", clean)
    clean = clean.strip().replace(" ", "")
    if clean:
        return f"{clean}.com"
    return ""


# ─── Smartlead Enrollment ──────────────────────────────────────────────────────

def enroll_in_smartlead(
    campaign_id: str,
    email: str,
    first_name: str,
    last_name: str,
    company_name: str,
    custom_fields: dict = None,
) -> bool:
    """
    Enroll a single contact in a Smartlead campaign.
    Returns True on success.

    Note: Does NOT include violation details in the lead data —
    the recovery-framing sequence handles messaging without referencing
    the specific regulatory action.
    """
    if not SMARTLEAD_API_KEY:
        logger.warning("[Smartlead] SMARTLEAD_API_KEY not set — skipping enrollment")
        return False
    if not campaign_id:
        logger.warning("[Smartlead] SL_CAMPAIGN_RECOVERY not set — skipping enrollment")
        return False
    if not email or "@" not in email:
        logger.warning(f"[Smartlead] Invalid email for {company_name}: {email!r}")
        return False

    lead_payload = {
        "email": email,
        "first_name": first_name or "",
        "last_name": last_name or "",
        "company_name": company_name or "",
        "custom_fields": custom_fields or {},
    }

    try:
        resp = requests.post(
            f"{SMARTLEAD_API_BASE}/campaigns/{campaign_id}/leads",
            params={"api_key": SMARTLEAD_API_KEY},
            json={"lead_list": [lead_payload]},
            headers={"Content-Type": "application/json"},
            timeout=20,
        )
        if resp.status_code == 200:
            logger.info(f"[Smartlead] Enrolled: {email} ({company_name})")
            return True
        else:
            logger.warning(
                f"[Smartlead] Enroll failed for {email}: "
                f"HTTP {resp.status_code} — {resp.text[:200]}"
            )
            return False
    except requests.RequestException as e:
        logger.error(f"[Smartlead] Enrollment error for {email}: {e}")
        return False


# ─── Slack Notification ────────────────────────────────────────────────────────

def slack_notify(text: str) -> bool:
    """Send a message to #ecas-ops via Slack webhook."""
    if not SLACK_WEBHOOK_URL:
        logger.info(f"[Slack] Webhook not configured — message: {text}")
        return False
    try:
        resp = requests.post(
            SLACK_WEBHOOK_URL,
            json={"text": text, "channel": "#ecas-ops"},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        return resp.status_code == 200
    except requests.RequestException as e:
        logger.warning(f"[Slack] Notify error: {e}")
        return False


# ─── Phase 1: Detection ────────────────────────────────────────────────────────

def run_detect(table_name: str = AIRTABLE_TABLE_NAME) -> dict:
    """
    Phase 1: Collect FDA warning letters + state board actions,
    enrich with NPI data, and save to Airtable with status='pending_wait'.

    Returns stats dict.
    """
    logger.info("=== Phase 1: Detection ===")

    # Collect signals in parallel
    fda_signals: list[dict] = []
    state_signals: list[dict] = []

    with ThreadPoolExecutor(max_workers=2) as executor:
        fda_future = executor.submit(fetch_fda_warning_letters)
        state_future = executor.submit(scrape_all_state_boards)
        fda_signals = fda_future.result()
        state_signals = state_future.result()

    all_signals = fda_signals + state_signals
    logger.info(
        f"[Detect] {len(fda_signals)} FDA signals + "
        f"{len(state_signals)} state board signals = {len(all_signals)} total"
    )

    inserted = 0
    skipped = 0

    for signal in all_signals:
        company_name = signal.get("company_name", "").strip()
        if not company_name:
            skipped += 1
            continue

        # NPI lookup
        state = signal.get("state", "")
        npi_data = lookup_npi(company_name, state)

        # Compute scheduled outreach date (action_date + 30 days)
        action_date_str = signal.get("action_date", "")
        try:
            action_dt = datetime.strptime(action_date_str, "%Y-%m-%d")
            scheduled_outreach = (action_dt + timedelta(days=30)).strftime("%Y-%m-%d")
        except ValueError:
            scheduled_outreach = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d")

        fields = {
            "company_name": company_name,
            "npi": npi_data.get("npi", ""),
            "state": state or npi_data.get("address", "")[-2:],  # fallback: last 2 chars of addr
            "action_type": signal.get("action_type", "Unknown"),
            "action_date": action_date_str + "T00:00:00.000Z" if action_date_str else "",
            "source": signal.get("source", "unknown"),
            "source_url": signal.get("source_url", ""),
            "address": npi_data.get("address", ""),
            "phone": npi_data.get("phone", ""),
            "status": "pending_wait",
            "scheduled_outreach_date": scheduled_outreach,
            # Store violation context for internal use — NOT used in outreach copy
            "internal_notes": signal.get("raw_notes", ""),
        }

        record_id = airtable_insert(table_name, fields)
        if record_id:
            inserted += 1
        else:
            skipped += 1

    logger.info(f"[Detect] Complete: {inserted} inserted, {skipped} skipped/duped")

    return {
        "phase": "detect",
        "fda_signals": len(fda_signals),
        "state_board_signals": len(state_signals),
        "total_signals": len(all_signals),
        "inserted": inserted,
        "skipped": skipped,
    }


# ─── Phase 2: Outreach Trigger ────────────────────────────────────────────────

def run_trigger(table_name: str = AIRTABLE_TABLE_NAME) -> dict:
    """
    Phase 2: Find records ready for outreach (pending_wait + date passed),
    enrich with Findymail, enroll in Smartlead, update status to 'enrolled'.

    Returns stats dict.
    """
    logger.info("=== Phase 2: Outreach Trigger ===")

    if not SL_CAMPAIGN_RECOVERY:
        logger.warning(
            "[Trigger] SL_CAMPAIGN_RECOVERY env var not set. "
            "Enrichment will run but Smartlead enrollment is disabled."
        )

    ready_records = airtable_get_pending(table_name)
    logger.info(f"[Trigger] {len(ready_records)} records ready for outreach")

    enrolled = 0
    failed = 0

    for record in ready_records:
        fields = record.get("fields", {})
        record_id = record["id"]
        company_name = fields.get("company_name", "Unknown")

        logger.info(f"[Trigger] Processing: {company_name} ({record_id})")

        # Attempt email enrichment via Findymail
        # We don't have a contact name yet — use generic "owner" lookup via company domain
        domain = _extract_domain_from_npi_data(fields)
        email = None
        if domain:
            # Try "Owner" as a generic first attempt
            email = findymail_lookup("Owner", "", domain)
            if not email:
                # Try "Pharmacist in Charge"
                email = findymail_lookup("Pharmacist", "", domain)

        if not email:
            logger.info(
                f"[Trigger] No email found for {company_name} (domain={domain!r}) "
                "— saving enrichment_status and continuing"
            )
            airtable_update(table_name, record_id, {
                "status": "email_not_found",
                "enrichment_notes": f"Tried domain: {domain}. Findymail returned no result.",
            })
            failed += 1
            continue

        # Enroll in Smartlead recovery sequence
        # Note: Only company_name is passed — no violation details in the lead payload
        success = enroll_in_smartlead(
            campaign_id=SL_CAMPAIGN_RECOVERY,
            email=email,
            first_name="",
            last_name="",
            company_name=company_name,
            custom_fields={
                "state": fields.get("state", ""),
                "npi": fields.get("npi", ""),
                "phone": fields.get("phone", ""),
            },
        )

        if success:
            airtable_update(table_name, record_id, {
                "status": "enrolled",
                "email": email,
                "enrolled_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            })
            enrolled += 1
        else:
            airtable_update(table_name, record_id, {
                "status": "enroll_failed",
                "email": email,
                "enrichment_notes": "Smartlead enrollment failed — check campaign ID and API key",
            })
            failed += 1

    # Slack summary
    if enrolled > 0 or len(ready_records) > 0:
        msg = (
            f":pill: *FDA/State Board Recovery Pipeline*\n"
            f"Records ready: {len(ready_records)} | "
            f"Enrolled: {enrolled} | "
            f"Failed/no-email: {failed}"
        )
        slack_notify(msg)

    logger.info(f"[Trigger] Complete: {enrolled} enrolled, {failed} failed")

    return {
        "phase": "trigger",
        "records_ready": len(ready_records),
        "enrolled": enrolled,
        "failed": failed,
    }


# ─── CLI Entrypoint ───────────────────────────────────────────────────────────

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="FDA Warning Letter + State Board Action signal monitor."
    )
    parser.add_argument(
        "--phase",
        choices=["detect", "trigger", "both"],
        default="both",
        help=(
            "detect: collect FDA/state board signals and save to Airtable. "
            "trigger: enroll ready records in Smartlead. "
            "both: run detect then trigger (default)."
        ),
    )
    parser.add_argument(
        "--table",
        default=AIRTABLE_TABLE_NAME,
        help="Airtable table name (default: regulatory_signals)",
    )
    args = parser.parse_args()

    if not AIRTABLE_API_KEY:
        logger.error("AIRTABLE_API_KEY is not set. Exiting.")
        sys.exit(1)

    results = {}

    if args.phase in ("detect", "both"):
        results["detect"] = run_detect(args.table)

    if args.phase in ("trigger", "both"):
        results["trigger"] = run_trigger(args.table)

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()


# ─── Cron schedule (reference) ────────────────────────────────────────────────
# Phase 1 — weekly Monday 7am:  0 7 * * 1
# Phase 2 — daily 8am:          0 8 * * *
# Run both together (weekly):   0 7 * * 1  python fda_warning_letter_monitor.py --phase both
