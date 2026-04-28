#!/usr/bin/env python3
"""
signals/epc_lead_engine.py — Free EPC lead discovery from non-obvious sources.

Targets two verticals where Apollo lists are thin:
  - Water & Wastewater Infrastructure EPCs
  - Data Center & AI Infrastructure EPCs

Sources (all free, zero API keys required):
  WATER/WASTEWATER
  ─────────────────
  1. WEFTEC exhibitors          wef.org               ~800 companies
  2. AWWA state sections        awwa.org              ~500 companies
  3. EPA CWSRF project states   epa.gov               active SRF projects
  4. USASpending water NAICS    api.usaspending.gov   contract winners by NAICS
  5. WEF member associations    wef.org               state chapter listings
  6. ACEC state members         acec.org + chapters   engineering firms
  7. State SRF IUPs             state sites           TX, FL, CA, OH, NC, VA

  DATA CENTER
  ─────────────
  8. AFCOM/DC World exhibitors  afcom.com             ~300 companies
  9. 7x24 Exchange members      7x24.org              mission-critical firms
  10. BICSI member locator      bicsi.org             cabling + DC infra
  11. USASpending DC NAICS      api.usaspending.gov   federal DC contractors
  12. Fairfax County permits    data.fairfaxcounty.gov  NOVA data center builds
  13. ENR Top 400 water/DC      enr.com               verified top contractors

Storage:
  - SQLite tracker.db for dedup (domain + source)
  - Supabase table epc_company_leads (upsert on domain+source)
  - CSV output → signals/output/epc_leads_{date}.csv

Usage:
  python signals/epc_lead_engine.py                    # all sources
  python signals/epc_lead_engine.py --source weftec    # single source
  python signals/epc_lead_engine.py --dry-run          # print, no save
  python signals/epc_lead_engine.py --sector water     # water sources only
  python signals/epc_lead_engine.py --sector dc        # data center only
"""

import argparse
import csv
import json
import logging
import os
import re
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, date
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("epc_lead_engine")

# ── Config ────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "database" / "tracker.db"
OUTPUT_DIR = BASE_DIR / "signals" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_TABLE = "epc_company_leads"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}
REQUEST_DELAY = 1.2  # seconds between requests — polite scraping

# USASpending NAICS codes
WATER_NAICS      = ["237110", "237120", "238220", "541330", "562213", "562219", "221310"]
DC_NAICS         = ["236220", "238210", "541330", "517311", "518210"]
POWER_NAICS      = ["237130", "237990", "238210", "221121", "221122", "221113", "221114"]
INDUSTRIAL_NAICS = ["236210", "237990", "238220", "238910", "541330", "325110", "324110"]
DEFENSE_NAICS    = ["237990", "236210", "541330", "541712", "541715", "562910", "336414"]

# States to hit for water/wastewater (largest SRF pipelines)
WATER_STATES = ["TX", "FL", "CA", "OH", "NC", "VA", "GA", "PA", "NY", "IL",
                "AZ", "TN", "CO", "IN", "MO", "WA", "MI", "MN", "WI", "NJ"]

# States with active data center construction
DC_STATES = ["VA", "TX", "AZ", "OH", "GA", "IL", "NY", "NJ", "OR", "NV",
             "WA", "NC", "FL", "PA", "CA"]

# States with heavy power grid construction
POWER_STATES = ["TX", "CA", "FL", "NY", "OH", "PA", "VA", "GA", "NC", "AZ",
                "IL", "MI", "WA", "CO", "NJ", "MN", "WI", "IN", "TN", "NM"]

# Heavy industrial corridor states
INDUSTRIAL_STATES = ["TX", "LA", "OH", "PA", "IN", "AL", "GA", "SC", "NC",
                     "MI", "WI", "AZ", "CA", "NY", "WV", "KY", "MO", "IA"]

# DOE/DOD complex states
DEFENSE_STATES = ["VA", "MD", "TX", "CA", "NM", "TN", "WA", "SC", "GA",
                  "AL", "FL", "ID", "CO", "OH", "PA", "NY", "AZ", "KY"]


# ── SQLite dedup ──────────────────────────────────────────────────────────────

def _init_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS epc_leads_seen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dedup_key TEXT UNIQUE,
            scraped_at TEXT
        )
    """)
    conn.commit()
    return conn


def _is_seen(conn: sqlite3.Connection, dedup_key: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM epc_leads_seen WHERE dedup_key=?", (dedup_key,)
    ).fetchone()
    return row is not None


def _mark_seen(conn: sqlite3.Connection, dedup_key: str) -> None:
    try:
        conn.execute(
            "INSERT INTO epc_leads_seen (dedup_key, scraped_at) VALUES (?,?)",
            (dedup_key, datetime.utcnow().isoformat()),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass


# ── Storage ───────────────────────────────────────────────────────────────────

def _make_lead(
    company_name: str,
    domain: str,
    source: str,
    sector: str,
    state: str = "",
    city: str = "",
    raw: dict = None,
) -> dict:
    return {
        "company_name": company_name.strip(),
        "domain": domain.lower().strip().lstrip("www.").strip("/"),
        "source": source,
        "sector": sector,
        "state": state,
        "city": city,
        "raw_data": json.dumps(raw or {}),
        "scraped_at": datetime.utcnow().isoformat(),
        "enrolled_smartlead": False,
    }


def _dedup_key(lead: dict) -> str:
    domain = lead["domain"] or lead["company_name"].lower().replace(" ", "")
    return f"{lead['source']}::{domain}"


def _save_to_supabase(leads: list[dict]) -> int:
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.warning("Supabase not configured — skipping remote save")
        return 0
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }
    batch_size = 100
    saved = 0
    for i in range(0, len(leads), batch_size):
        batch = leads[i : i + batch_size]
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}?on_conflict=domain,source",
            headers=headers,
            json=batch,
            timeout=20,
        )
        if r.status_code in (200, 201):
            saved += len(batch)
        else:
            logger.error("Supabase batch failed %d: %s", r.status_code, r.text[:200])
    return saved


def _save_to_csv(leads: list[dict], suffix: str = "") -> Path:
    today = date.today().isoformat()
    fname = OUTPUT_DIR / f"epc_leads_{today}{suffix}.csv"
    if not leads:
        return fname
    with open(fname, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=leads[0].keys())
        writer.writeheader()
        writer.writerows(leads)
    logger.info("CSV saved: %s (%d rows)", fname, len(leads))
    return fname


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _get(url: str, **kwargs) -> Optional[requests.Response]:
    try:
        r = requests.get(url, headers=HEADERS, timeout=20, **kwargs)
        r.raise_for_status()
        return r
    except Exception as e:
        logger.warning("GET %s failed: %s", url, e)
        return None


def _post(url: str, **kwargs) -> Optional[requests.Response]:
    try:
        r = requests.post(url, headers=HEADERS, timeout=30, **kwargs)
        r.raise_for_status()
        return r
    except Exception as e:
        logger.warning("POST %s failed: %s", url, e)
        return None


def _extract_domain(text: str) -> str:
    m = re.search(r'https?://(?:www\.)?([^/\s"\'<>]+)', text)
    if m:
        d = m.group(1).lower().strip().rstrip(".")
        if "." in d and not any(x in d for x in ["google.", "facebook.", "linkedin.", "twitter.", "youtube."]):
            return d
    return ""


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 1: WEFTEC Exhibitors
# wef.org/weftec — largest water conference in the world (~800 exhibitors)
# ─────────────────────────────────────────────────────────────────────────────

def scrape_weftec(conn: sqlite3.Connection) -> list[dict]:
    """Scrape WEFTEC exhibitor list from WEF website."""
    leads = []
    base_url = "https://www.wef.org/weftec/exhibit/exhibitor-list/"
    logger.info("[WEFTEC] Fetching exhibitor list...")

    r = _get(base_url)
    if not r:
        # Try the search API that WEFTEC uses
        api_url = "https://www.wef.org/weftec/exhibit/exhibitor-list/"
        r = _get(api_url, params={"format": "json"})

    if r:
        soup = BeautifulSoup(r.text, "lxml")

        # Try multiple selectors for exhibitor listings
        companies = set()
        for sel in [
            ".exhibitor-name", ".company-name", "[class*='exhibitor']",
            ".directory-listing .name", "h2.title", ".listing-title",
        ]:
            for el in soup.select(sel):
                name = el.get_text(strip=True)
                if name and len(name) > 3:
                    companies.add(name)

        logger.info("[WEFTEC] Found %d companies from HTML", len(companies))
        for name in companies:
            key = f"weftec::{name.lower()}"
            if not _is_seen(conn, key):
                lead = _make_lead(name, "", "WEFTEC", "Water & Wastewater", raw={"year": "2025"})
                leads.append(lead)
                _mark_seen(conn, key)

    # Fallback: scrape the exhibitor search endpoint
    if not leads:
        logger.info("[WEFTEC] Trying search endpoint fallback...")
        search_url = "https://weftec25.mapyourshow.com/8_0/exhview/index.cfm"
        r2 = _get(search_url)
        if r2:
            soup2 = BeautifulSoup(r2.text, "lxml")
            for el in soup2.select(".exhibitorname, .ExhibitorName, [class*='exhib']"):
                name = el.get_text(strip=True)
                if name and len(name) > 3:
                    key = f"weftec::{name.lower()}"
                    if not _is_seen(conn, key):
                        lead = _make_lead(name, "", "WEFTEC", "Water & Wastewater")
                        leads.append(lead)
                        _mark_seen(conn, key)

    # Second fallback: MapYourShow API (public, used by most trade shows)
    if not leads:
        logger.info("[WEFTEC] Trying MapYourShow API...")
        mys_urls = [
            "https://weftec25.mapyourshow.com/8_0/ajax/get-exhibitor-list.cfm?page=1&perPage=500",
            "https://weftec24.mapyourshow.com/8_0/ajax/get-exhibitor-list.cfm?page=1&perPage=500",
        ]
        for mys_url in mys_urls:
            r3 = _get(mys_url)
            if r3:
                try:
                    data = r3.json()
                    exhibitors = data.get("exhibitors", data.get("data", []))
                    if isinstance(exhibitors, list):
                        for ex in exhibitors:
                            name = ex.get("company", ex.get("name", ex.get("CompanyName", "")))
                            domain = ex.get("website", ex.get("url", ""))
                            if name:
                                key = f"weftec::{name.lower()}"
                                if not _is_seen(conn, key):
                                    lead = _make_lead(
                                        name, _extract_domain(domain),
                                        "WEFTEC", "Water & Wastewater",
                                        raw={"booth": ex.get("booth", ""), "url": domain},
                                    )
                                    leads.append(lead)
                                    _mark_seen(conn, key)
                        if leads:
                            break
                except Exception:
                    pass

    logger.info("[WEFTEC] Done: %d new leads", len(leads))
    return leads


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 2: AWWA State Sections
# awwa.org — American Water Works Association, 50k+ members
# ─────────────────────────────────────────────────────────────────────────────

def scrape_awwa(conn: sqlite3.Connection) -> list[dict]:
    """Scrape AWWA state section member company listings."""
    leads = []
    logger.info("[AWWA] Scraping state section directories...")

    # AWWA section directory — public
    sections_url = "https://www.awwa.org/About-Us/Sections"
    r = _get(sections_url)
    section_links = []
    if r:
        soup = BeautifulSoup(r.text, "lxml")
        for a in soup.select("a[href*='section'], a[href*='awwa.org']"):
            href = a.get("href", "")
            if "section" in href.lower() and href.startswith("http"):
                section_links.append(href)

    # Known AWWA section membership directories (public-facing pages)
    known_sections = [
        ("https://www.fsawwa.org/page/FindaMember", "FL"),
        ("https://www.tawwa.org/resources/member-directory", "TX"),
        ("https://www.cawwa.org/find-a-member", "CA"),
        ("https://www.ohiowea.org/page/membercompanies", "OH"),
        ("https://www.ncawwa.org/find-a-member/", "NC"),
        ("https://www.vwwa.org/page/MemberDirectory", "VA"),
        ("https://www.iawea.org/page/Directory", "IL"),
        ("https://www.mwea.org/page/Members", "MI"),
        ("https://www.pawwa.org/membership/directory", "PA"),
        ("https://www.njawwa.org/member-search", "NJ"),
    ]

    for url, state in known_sections:
        time.sleep(REQUEST_DELAY)
        r = _get(url)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "lxml")
        count = 0
        for sel in [
            ".member-name", ".company-name", "[class*='member'] h3",
            "td:first-child", ".directory-item .name", "h4.org-name",
        ]:
            for el in soup.select(sel):
                name = el.get_text(strip=True)
                if name and len(name) > 4 and not name.lower().startswith("http"):
                    key = f"awwa_{state}::{name.lower()[:50]}"
                    if not _is_seen(conn, key):
                        lead = _make_lead(name, "", f"AWWA-{state}", "Water & Wastewater", state=state)
                        leads.append(lead)
                        _mark_seen(conn, key)
                        count += 1
        if count:
            logger.info("[AWWA] %s: %d leads", state, count)

    # Also hit the main AWWA member finder API if it exists
    awwa_api = "https://www.awwa.org/api/member/search"
    r = _post(awwa_api, json={"memberType": "all", "limit": 500})
    if r:
        try:
            data = r.json()
            members = data.get("members", data.get("results", []))
            for m in members:
                name = m.get("organization", m.get("company", ""))
                state = m.get("state", "")
                if name and len(name) > 3:
                    key = f"awwa_api::{name.lower()[:50]}"
                    if not _is_seen(conn, key):
                        lead = _make_lead(name, m.get("website", ""), "AWWA-API", "Water & Wastewater",
                                          state=state, city=m.get("city", ""))
                        leads.append(lead)
                        _mark_seen(conn, key)
        except Exception:
            pass

    logger.info("[AWWA] Done: %d new leads", len(leads))
    return leads


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 3: EPA CWSRF State Project Lists
# epa.gov — Clean Water State Revolving Fund, all funded projects public
# ─────────────────────────────────────────────────────────────────────────────

def scrape_cwsrf(conn: sqlite3.Connection) -> list[dict]:
    """
    Pull EPA CWSRF funded projects. These are municipalities/utilities that
    received SRF loans → active construction projects → EPCs bidding on them.
    Also pulls the borrower list which is public.
    """
    leads = []
    logger.info("[CWSRF] Scraping EPA Clean Water SRF project data...")

    # EPA CWSRF data is available via their data portal
    cwsrf_urls = [
        "https://www.epa.gov/cwsrf/forms/cwsrf-projects",
        "https://www.epa.gov/system/files/documents/2024-11/cwsrf-projects-fy2024.xlsx",
        "https://ordspub.epa.gov/ords/srf_public/srf_api/cwsrf_projects",
    ]

    # State SRF program pages (each state posts their funded projects)
    state_srf_pages = {
        "TX": "https://www.tceq.texas.gov/goto/cwsrf-assistance",
        "FL": "https://floridadep.gov/water/water-policy/content/clean-water-state-revolving-fund-cwsrf",
        "CA": "https://www.waterboards.ca.gov/water_issues/programs/grants_loans/srf/",
        "OH": "https://epa.ohio.gov/divisions-and-offices/drinking-and-ground-waters/water-quality-loans/water-pollution-control-loan-fund",
        "NC": "https://www.deq.nc.gov/about/divisions/water-infrastructure/water-infrastructure-programs/clean-water-state-revolving-fund",
        "VA": "https://www.deq.virginia.gov/our-programs/water/infrastructure-funding/virginia-clean-water-revolving-loan-fund",
        "GA": "https://epd.georgia.gov/watershed-protection-branch/georgia-environmental-finance-authority",
        "PA": "https://www.pennvest.pa.gov/Clean-Water-Funding/Pages/default.aspx",
        "NY": "https://www.efc.ny.gov/water-programs",
        "IL": "https://epa.illinois.gov/topics/water-quality/water-financial-assistance/clean-water-act-section-212.html",
    }

    for state, url in state_srf_pages.items():
        time.sleep(REQUEST_DELAY)
        r = _get(url)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "lxml")

        # Look for project names / borrower names in tables
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            for row in rows[1:]:  # skip header
                cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
                if not cells:
                    continue
                # First substantial cell is usually project/borrower name
                name = cells[0] if cells else ""
                if name and len(name) > 5 and not name.isdigit():
                    key = f"cwsrf_{state}::{name.lower()[:60]}"
                    if not _is_seen(conn, key):
                        raw = {"cells": cells[:5], "url": url}
                        lead = _make_lead(name, "", f"CWSRF-{state}", "Water & Wastewater",
                                          state=state, raw=raw)
                        leads.append(lead)
                        _mark_seen(conn, key)

        logger.info("[CWSRF] %s: found entries on SRF page", state)

    # Also try the EPA ECHO CWSRF API (no key needed)
    echo_url = "https://echodata.epa.gov/echo/cwa_rest_services.get_facilities"
    for state in WATER_STATES[:10]:  # top 10 states
        time.sleep(REQUEST_DELAY)
        params = {
            "output": "JSON",
            "p_st": state,
            "p_act": "Y",
            "p_major": "Y",  # major facilities only
            "qcolumns": "1,2,3,4,5,6,7,8,9,10",
            "p_rows": "100",
        }
        r = _get(echo_url, params=params)
        if not r:
            continue
        try:
            data = r.json()
            facilities = data.get("Results", {}).get("Facilities", [])
            for f in facilities:
                name = f.get("FacilityName", "")
                city = f.get("CityName", "")
                if name and len(name) > 3:
                    key = f"echo_cwsrf_{state}::{name.lower()[:60]}"
                    if not _is_seen(conn, key):
                        lead = _make_lead(name, "", f"EPA-ECHO-{state}",
                                          "Water & Wastewater", state=state, city=city,
                                          raw={"frs_id": f.get("RegistryID", "")})
                        leads.append(lead)
                        _mark_seen(conn, key)
        except Exception as e:
            logger.debug("[CWSRF] ECHO parse failed %s: %s", state, e)

    logger.info("[CWSRF] Done: %d new leads", len(leads))
    return leads


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 4: USASpending.gov — EPC contract winners by NAICS
# 100% free, no API key, returns real revenue-validated companies
# ─────────────────────────────────────────────────────────────────────────────

def scrape_usaspending(conn: sqlite3.Connection, sector: str = "both") -> list[dict]:
    """
    Pull EPC companies from USASpending.gov by NAICS code.
    Returns recipients who have won federal contracts → revenue-validated EPCs.
    """
    leads = []
    base_url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
    logger.info("[USASpending] Pulling EPC contract recipients...")

    searches = []
    if sector in ("both", "all", "water"):
        for naics in WATER_NAICS:
            searches.append((naics, "Water & Wastewater"))
    if sector in ("both", "all", "dc"):
        for naics in DC_NAICS:
            searches.append((naics, "Data Center & AI Infrastructure"))
    if sector in ("all", "power"):
        for naics in POWER_NAICS:
            searches.append((naics, "Power & Grid Infrastructure"))
    if sector in ("all", "industrial"):
        for naics in INDUSTRIAL_NAICS:
            searches.append((naics, "Industrial & Manufacturing Facilities"))
    if sector in ("all", "defense"):
        for naics in DEFENSE_NAICS:
            searches.append((naics, "Defense & Nuclear Infrastructure"))

    for naics_code, vertical in searches:
        time.sleep(REQUEST_DELAY)
        payload = {
            "filters": {
                "time_period": [{"start_date": "2023-01-01", "end_date": "2026-01-01"}],
                "award_type_codes": ["A", "B", "C", "D"],
                "naics_codes": [naics_code],
            },
            "fields": [
                "Recipient Name",
                "recipient_id",
                "Award Amount",
                "Place of Performance State Code",
                "Place of Performance City Name",
                "Awarding Agency Name",
            ],
            "sort": "Award Amount",
            "order": "desc",
            "limit": 100,
            "page": 1,
        }
        r = _post(base_url, json=payload)
        if not r:
            continue
        try:
            data = r.json()
            results = data.get("results", [])
            for rec in results:
                name = rec.get("Recipient Name", "")
                state = rec.get("Place of Performance State Code", "")
                city = rec.get("Place of Performance City Name", "")
                amount = rec.get("Award Amount", 0)
                if name and len(name) > 3:
                    sector_tag = vertical[:8].lower().replace(" ", "_").replace("&", "")
                    key = f"usaspending_{naics_code}_{sector_tag}::{name.lower()[:60]}"
                    if not _is_seen(conn, key):
                        lead = _make_lead(
                            name, "", f"USASpending-NAICS-{naics_code}", vertical,
                            state=state, city=city,
                            raw={"naics": naics_code, "award_total": amount},
                        )
                        leads.append(lead)
                        _mark_seen(conn, key)
            logger.info("[USASpending] NAICS %s (%s): %d recipients", naics_code, vertical, len(results))
        except Exception as e:
            logger.warning("[USASpending] NAICS %s parse failed: %s", naics_code, e)

    logger.info("[USASpending] Done: %d new leads", len(leads))
    return leads


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 5: ACEC State Chapter Member Directories
# acec.org — American Council of Engineering Companies
# ─────────────────────────────────────────────────────────────────────────────

def scrape_acec(conn: sqlite3.Connection) -> list[dict]:
    """Scrape ACEC state chapter member directories."""
    leads = []
    logger.info("[ACEC] Scraping state chapter member directories...")

    # ACEC state chapter URLs (each has member directory)
    acec_state_chapters = {
        "TX": "https://www.acec-texas.org/find-a-member",
        "FL": "https://www.acecfl.org/directory/",
        "CA": "https://www.acec-ca.org/find-a-member",
        "VA": "https://www.acec-va.org/member-search",
        "NC": "https://www.acecnc.org/member-directory",
        "OH": "https://www.acecohio.org/members/member-directory",
        "GA": "https://www.acecga.org/find-a-firm",
        "PA": "https://www.acecpa.org/member-directory",
        "CO": "https://www.acec-co.org/find-a-member/",
        "AZ": "https://www.acecaz.org/member-directory",
        "IL": "https://www.aecom-illinois.org/find-a-member",
        "WA": "https://www.acec-wa.org/find-a-member",
    }

    # Also hit national ACEC member search
    national_url = "https://www.acec.org/find-a-member/"
    r = _get(national_url)
    if r:
        soup = BeautifulSoup(r.text, "lxml")
        for el in soup.select(".member-firm, .firm-name, .company-name, .member-name"):
            name = el.get_text(strip=True)
            if name and len(name) > 3:
                key = f"acec_national::{name.lower()[:50]}"
                if not _is_seen(conn, key):
                    lead = _make_lead(name, "", "ACEC-National", "Water & Wastewater")
                    leads.append(lead)
                    _mark_seen(conn, key)

    for state, url in acec_state_chapters.items():
        time.sleep(REQUEST_DELAY)
        r = _get(url)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "lxml")
        count = 0
        for sel in [
            ".member-name", ".firm-name", ".company-name",
            "h3.title", ".directory-firm h4", "[class*='firm'] .name",
            "td.firm-name", ".member-listing h2",
        ]:
            for el in soup.select(sel):
                name = el.get_text(strip=True)
                if name and len(name) > 4 and not name.lower().startswith("http"):
                    # Try to find website link nearby
                    parent = el.parent
                    domain = ""
                    if parent:
                        link = parent.find("a", href=re.compile(r"https?://"))
                        if link:
                            domain = _extract_domain(link["href"])
                    key = f"acec_{state}::{name.lower()[:50]}"
                    if not _is_seen(conn, key):
                        lead = _make_lead(name, domain, f"ACEC-{state}",
                                          "Water & Wastewater", state=state)
                        leads.append(lead)
                        _mark_seen(conn, key)
                        count += 1
        if count:
            logger.info("[ACEC] %s: %d leads", state, count)

    logger.info("[ACEC] Done: %d new leads", len(leads))
    return leads


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 6: AFCOM Data Center World Exhibitors
# afcom.com — largest data center operations conference
# ─────────────────────────────────────────────────────────────────────────────

def scrape_afcom(conn: sqlite3.Connection) -> list[dict]:
    """Scrape AFCOM Data Center World exhibitor lists."""
    leads = []
    logger.info("[AFCOM] Scraping Data Center World exhibitor list...")

    urls = [
        "https://afcom.com/dcworld/exhibitors",
        "https://afcom.com/attend/events/data-center-world/dcw-exhibitors",
        "https://www.afcom.com/dcw/exhibitors",
    ]
    # Try MapYourShow (used by many trade shows including Data Center World)
    mys_urls = [
        "https://dcworld25.mapyourshow.com/8_0/ajax/get-exhibitor-list.cfm?page=1&perPage=500",
        "https://dcworld24.mapyourshow.com/8_0/ajax/get-exhibitor-list.cfm?page=1&perPage=500",
        "https://dcwusa25.mapyourshow.com/8_0/ajax/get-exhibitor-list.cfm?page=1&perPage=500",
    ]

    found = False
    for url in urls + mys_urls:
        time.sleep(REQUEST_DELAY)
        r = _get(url)
        if not r:
            continue

        if "application/json" in r.headers.get("Content-Type", "") or url in mys_urls:
            try:
                data = r.json()
                exhibitors = data.get("exhibitors", data.get("data", data.get("results", [])))
                if isinstance(exhibitors, list) and exhibitors:
                    for ex in exhibitors:
                        name = ex.get("company", ex.get("CompanyName", ex.get("name", "")))
                        domain = ex.get("website", ex.get("url", ""))
                        if name:
                            key = f"afcom::{name.lower()[:50]}"
                            if not _is_seen(conn, key):
                                lead = _make_lead(
                                    name, _extract_domain(str(domain)),
                                    "AFCOM-DCWorld", "Data Center & AI Infrastructure",
                                    raw={"booth": ex.get("booth", "")},
                                )
                                leads.append(lead)
                                _mark_seen(conn, key)
                    found = True
                    break
            except Exception:
                pass
        else:
            soup = BeautifulSoup(r.text, "lxml")
            for sel in [".exhibitor-name", ".company-name", "[class*='exhib'] h3",
                        ".directory-name", "h2.listing"]:
                for el in soup.select(sel):
                    name = el.get_text(strip=True)
                    if name and len(name) > 3:
                        key = f"afcom::{name.lower()[:50]}"
                        if not _is_seen(conn, key):
                            lead = _make_lead(name, "", "AFCOM-DCWorld",
                                              "Data Center & AI Infrastructure")
                            leads.append(lead)
                            _mark_seen(conn, key)
                            found = True

    logger.info("[AFCOM] Done: %d new leads", len(leads))
    return leads


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 7: 7x24 Exchange Member Companies
# 7x24.org — mission critical uptime industry association
# ─────────────────────────────────────────────────────────────────────────────

def scrape_7x24(conn: sqlite3.Connection) -> list[dict]:
    """Scrape 7x24 Exchange member company listings."""
    leads = []
    logger.info("[7x24] Scraping member company directory...")

    # 7x24 has regional chapters with member listings
    chapter_urls = [
        "https://www.7x24.org/members/member-list",
        "https://www.7x24.org/about/chapters",
        "https://7x24exchange.org/member-companies",
        "https://www.7x24.org/membership/member-directory",
    ]

    for url in chapter_urls:
        time.sleep(REQUEST_DELAY)
        r = _get(url)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "lxml")
        for sel in [".member-company", ".company-name", "[class*='member'] h3",
                    ".member-listing .title", "li.member-item"]:
            for el in soup.select(sel):
                name = el.get_text(strip=True)
                if name and len(name) > 3:
                    # Find link
                    parent = el.find_parent("li") or el.parent
                    domain = ""
                    if parent:
                        link = parent.find("a", href=re.compile(r"https?://"))
                        if link:
                            domain = _extract_domain(link["href"])
                    key = f"7x24::{name.lower()[:50]}"
                    if not _is_seen(conn, key):
                        lead = _make_lead(name, domain, "7x24-Exchange",
                                          "Data Center & AI Infrastructure")
                        leads.append(lead)
                        _mark_seen(conn, key)

    # Also scrape individual chapter pages
    chapter_pages = [
        ("https://www.7x24.org/chapters/mid-atlantic", "VA"),
        ("https://www.7x24.org/chapters/lone-star", "TX"),
        ("https://www.7x24.org/chapters/chicago", "IL"),
        ("https://www.7x24.org/chapters/arizona", "AZ"),
        ("https://www.7x24.org/chapters/ohio-valley", "OH"),
        ("https://www.7x24.org/chapters/pacific-northwest", "WA"),
        ("https://www.7x24.org/chapters/georgia", "GA"),
    ]
    for url, state in chapter_pages:
        time.sleep(REQUEST_DELAY)
        r = _get(url)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "lxml")
        for el in soup.select(".sponsor, .member, .company, [class*='partner']"):
            name_el = el.find(["h3", "h4", "strong", ".name"])
            if name_el:
                name = name_el.get_text(strip=True)
            else:
                name = el.get_text(strip=True)
            if name and len(name) > 3 and len(name) < 100:
                key = f"7x24_{state}::{name.lower()[:50]}"
                if not _is_seen(conn, key):
                    lead = _make_lead(name, "", f"7x24-{state}",
                                      "Data Center & AI Infrastructure", state=state)
                    leads.append(lead)
                    _mark_seen(conn, key)

    logger.info("[7x24] Done: %d new leads", len(leads))
    return leads


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 8: BICSI Member Locator
# bicsi.org — 26,000+ members, low-voltage/data center infrastructure
# ─────────────────────────────────────────────────────────────────────────────

def scrape_bicsi(conn: sqlite3.Connection) -> list[dict]:
    """Scrape BICSI member company locator by state."""
    leads = []
    logger.info("[BICSI] Scraping member locator...")

    # BICSI member search (company directory)
    search_url = "https://www.bicsi.org/standards-and-practice/find-a-member"
    api_url = "https://www.bicsi.org/api/member-search"

    # Try API endpoint first
    for state in DC_STATES:
        time.sleep(REQUEST_DELAY)
        r = _post(api_url, json={"state": state, "country": "US", "page": 1, "pageSize": 100})
        if r:
            try:
                data = r.json()
                members = data.get("members", data.get("results", data.get("data", [])))
                for m in members:
                    name = m.get("company", m.get("organization", m.get("name", "")))
                    if name and len(name) > 3:
                        key = f"bicsi_{state}::{name.lower()[:50]}"
                        if not _is_seen(conn, key):
                            lead = _make_lead(name, m.get("website", ""),
                                              f"BICSI-{state}",
                                              "Data Center & AI Infrastructure", state=state)
                            leads.append(lead)
                            _mark_seen(conn, key)
            except Exception:
                pass

        # Fallback: GET with query params
        r = _get(search_url, params={"state": state, "country": "US"})
        if r:
            soup = BeautifulSoup(r.text, "lxml")
            for el in soup.select(".member-company, .company-name, [class*='member'] .name"):
                name = el.get_text(strip=True)
                if name and len(name) > 3:
                    key = f"bicsi_{state}_html::{name.lower()[:50]}"
                    if not _is_seen(conn, key):
                        lead = _make_lead(name, "", f"BICSI-{state}",
                                          "Data Center & AI Infrastructure", state=state)
                        leads.append(lead)
                        _mark_seen(conn, key)

    logger.info("[BICSI] Done: %d new leads", len(leads))
    return leads


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 9: NECA Member Directory
# neca.org — National Electrical Contractors Association
# Electrical contractors doing data center + water/wastewater buildouts
# ─────────────────────────────────────────────────────────────────────────────

def scrape_neca(conn: sqlite3.Connection) -> list[dict]:
    """Scrape NECA chapter member directories — electrical contractors."""
    leads = []
    logger.info("[NECA] Scraping chapter member directories...")

    # NECA has 120+ chapters; these are the most active for DC/water markets
    chapter_apis = [
        ("https://necanet.org/find-a-contractor", "national"),
        ("https://www.neca.org/about-neca/find-a-chapter", "chapters"),
    ]

    # NECA contractor finder
    finder_url = "https://necanet.org/find-a-contractor"
    r = _get(finder_url)
    if r:
        soup = BeautifulSoup(r.text, "lxml")
        # NECA uses a search form — look for any embedded data
        script_tags = soup.find_all("script", type="application/json")
        for script in script_tags:
            try:
                data = json.loads(script.string or "")
                contractors = data.get("contractors", data.get("members", []))
                for c in contractors:
                    name = c.get("company", c.get("name", ""))
                    if name:
                        state = c.get("state", "")
                        key = f"neca::{name.lower()[:50]}"
                        if not _is_seen(conn, key):
                            lead = _make_lead(name, c.get("website", ""),
                                              "NECA", "Data Center & AI Infrastructure",
                                              state=state, city=c.get("city", ""))
                            leads.append(lead)
                            _mark_seen(conn, key)
            except Exception:
                pass

    # NECA chapter-specific directories
    neca_chapters = {
        "VA": "https://necava.org/contractor-members",
        "TX": "https://www.necatexas.org/find-a-contractor",
        "AZ": "https://necanet.org/chapters/arizona",
        "OH": "https://www.neca-ohio.org/members",
        "GA": "https://www.neca-ga.org/contractor-members",
        "IL": "https://necanet.org/chapters/illinois",
        "NC": "https://www.neca-carolina.org/members",
        "FL": "https://www.neca-florida.org/contractor-members",
    }

    for state, url in neca_chapters.items():
        time.sleep(REQUEST_DELAY)
        r = _get(url)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "lxml")
        for sel in [".member-name", ".contractor-name", ".company", "td:first-child",
                    "[class*='member'] h3", ".directory-name"]:
            for el in soup.select(sel):
                name = el.get_text(strip=True)
                if name and len(name) > 4 and not name.lower().startswith("http"):
                    key = f"neca_{state}::{name.lower()[:50]}"
                    if not _is_seen(conn, key):
                        lead = _make_lead(name, "", f"NECA-{state}",
                                          "Data Center & AI Infrastructure", state=state)
                        leads.append(lead)
                        _mark_seen(conn, key)

    logger.info("[NECA] Done: %d new leads", len(leads))
    return leads


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 10: SAM.gov Entity Search (free public tier — no key for basic data)
# Pulls companies registered to do federal EPC work by NAICS code
# ─────────────────────────────────────────────────────────────────────────────

def scrape_sam_gov_entities(conn: sqlite3.Connection, sector: str = "both") -> list[dict]:
    """
    Query SAM.gov public entity API for EPC companies registered by NAICS.
    Free public API — no key required for non-sensitive entity data.
    """
    leads = []
    logger.info("[SAM.gov] Pulling registered EPC entities...")

    sam_url = "https://api.sam.gov/entity-information/v3/entities"
    sam_key = os.environ.get("SAM_GOV_API_KEY", "")

    naics_sets = []
    if sector in ("both", "all", "water"):
        naics_sets.extend([(n, "Water & Wastewater") for n in WATER_NAICS[:4]])
    if sector in ("both", "all", "dc"):
        naics_sets.extend([(n, "Data Center & AI Infrastructure") for n in DC_NAICS[:3]])
    if sector in ("all", "power"):
        naics_sets.extend([(n, "Power & Grid Infrastructure") for n in POWER_NAICS[:4]])
    if sector in ("all", "industrial"):
        naics_sets.extend([(n, "Industrial & Manufacturing Facilities") for n in INDUSTRIAL_NAICS[:4]])
    if sector in ("all", "defense"):
        naics_sets.extend([(n, "Defense & Nuclear Infrastructure") for n in DEFENSE_NAICS[:4]])

    for naics_code, vertical in naics_sets:
        time.sleep(REQUEST_DELAY)
        params = {
            "naicsCode": naics_code,
            "entityEFTIndicator": "",
            "includeSections": "entityRegistration,coreData",
            "registrationStatus": "A",
            "purposeOfRegistrationCode": "Z1,Z2",  # all of gov + all transactions
            "q": "",
        }
        if sam_key:
            params["api_key"] = sam_key

        r = _get(sam_url, params=params)
        if not r:
            # Without key, try the public FOUO-free endpoint
            r = _get(
                f"https://api.sam.gov/entity-information/v3/entities?naicsCode={naics_code}&registrationStatus=A",
            )
        if not r:
            continue

        try:
            data = r.json()
            entities = data.get("entityData", data.get("data", []))
            for entity in entities:
                reg = entity.get("entityRegistration", {})
                core = entity.get("coreData", {})
                name = reg.get("legalBusinessName", core.get("entityInformation", {}).get("entityName", ""))
                state = (core.get("physicalAddress", {}) or {}).get("stateOrProvinceCode", "")
                city = (core.get("physicalAddress", {}) or {}).get("city", "")
                cage = reg.get("cageCode", "")
                if name and len(name) > 3:
                    sector_tag = vertical[:8].lower().replace(" ", "_").replace("&", "")
                    key = f"samgov_{naics_code}_{sector_tag}::{name.lower()[:60]}"
                    if not _is_seen(conn, key):
                        lead = _make_lead(
                            name, "",
                            f"SAM.gov-NAICS-{naics_code}", vertical,
                            state=state, city=city,
                            raw={"naics": naics_code, "cage": cage},
                        )
                        leads.append(lead)
                        _mark_seen(conn, key)
            logger.info("[SAM.gov] NAICS %s: %d entities", naics_code,
                        len(data.get("entityData", data.get("data", []))))
        except Exception as e:
            logger.debug("[SAM.gov] Parse failed NAICS %s: %s", naics_code, e)

    logger.info("[SAM.gov] Done: %d new leads", len(leads))
    return leads


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 11: ENR Top Contractors by specialty
# enr.com — Engineering News-Record Top 400 / Top 200 Environmental
# ─────────────────────────────────────────────────────────────────────────────

def scrape_enr(conn: sqlite3.Connection) -> list[dict]:
    """
    Parse ENR Top 500 Design Firms PDF — publicly available each year.
    Falls back to scraping the toplists page for any accessible data.
    """
    leads = []
    logger.info("[ENR] Parsing ENR Top 500 Design Firms PDF...")

    # ENR publishes their top-list PDF publicly in their weekly issue
    pdf_urls = [
        "https://www.enr.com/ext/resources/Issues/National_Issues/2026/27-Apr/ENR04272026_Top500_compressed.pdf",
        "https://www.enr.com/ext/resources/Issues/National_Issues/2025/28-Apr/ENR04282025_Top500_compressed.pdf",
    ]

    NOISE_FRAGMENTS = {
        "PERCENT", "REVENUE", "MARKET", "OWNER TYPE", "INTERNATIONAL STAFF",
        "STAYED", "MANUFACTURING", "PETROLEUM", "INDUSTRIAL", "HAZARDOUS",
        "TRANSPORTATION", "AUSTRALIA", "ANTARCTIC", "CARIBBEAN", "AFRICA",
        "CANADA", "EUROPE", "LATIN AMERICA", "MIDDLE EAST", "NUMBER OF",
        "ENVIRONMENTAL", "INFRASTRUCTURE", "CIVIL ENGINEERING", "ARCHITECT",
        "ENGINEER", "CONSTRUCTION",
    }

    parsed = False
    for pdf_url in pdf_urls:
        time.sleep(REQUEST_DELAY)
        r = _get(pdf_url)
        if not r or len(r.content) < 10000:
            continue
        try:
            import io
            import pdfminer.high_level as pdfm
            text = pdfm.extract_text(io.BytesIO(r.content))
            lines = text.split("\n")
            firms = set()
            for line in lines:
                line = line.strip()
                if not line or len(line) < 8 or len(line) > 85:
                    continue
                if any(s in line.upper() for s in NOISE_FRAGMENTS):
                    continue
                if not re.match(r"^[A-Z]", line):
                    continue
                # Must have lowercase (rules out all-caps headers/regions)
                if not any(c.islower() for c in line):
                    continue
                # Filter sentence fragments (contains verb phrases)
                if any(w in line.lower() for w in [" says ", " has ", " is ", " are ", " was ",
                                                    " will ", " that ", " with ", " from ", " more "]):
                    continue
                words = line.split()
                if 2 <= len(words) <= 8 and re.match(r"^[A-Za-z0-9\s&,\.\-\/\(\)]{8,80}$", line):
                    # Must look like a company name: ends with Inc/LLC/Corp/Group/etc or proper noun
                    if (re.search(r"\b(Inc|LLC|Corp|Ltd|LLP|Co|Group|Partners|Associates|Services|Engineers?|Consulting|Engineering|Architecture|Construction|Design|Solutions|Systems|Technologies|Holdings|International)\b", line, re.IGNORECASE)
                            or (len(words) == 2 and all(w[0].isupper() for w in words))):
                        firms.add(line)

            for name in sorted(firms):
                key = f"enr_pdf::{name.lower()[:60]}"
                if not _is_seen(conn, key):
                    lead = _make_lead(name, "", "ENR-Top500", "Water & Wastewater",
                                      raw={"source_pdf": pdf_url.split("/")[-1]})
                    leads.append(lead)
                    _mark_seen(conn, key)

            logger.info("[ENR] PDF parsed: %d firm names extracted", len(firms))
            parsed = True
            break
        except ImportError:
            logger.warning("[ENR] pdfminer not installed — pip install pdfminer.six")
        except Exception as e:
            logger.warning("[ENR] PDF parse failed: %s", e)

    if not parsed:
        logger.info("[ENR] PDF parse skipped — no accessible PDF found")

    logger.info("[ENR] Done: %d new leads", len(leads))
    return leads


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 12: State Contractor License Databases (public APIs / search)
# FL DBPR, TX TDLR, VA DPOR — licensed EPC contractors
# ─────────────────────────────────────────────────────────────────────────────

def scrape_state_licenses(conn: sqlite3.Connection) -> list[dict]:
    """Scrape state contractor license databases for EPC firms."""
    leads = []
    logger.info("[StateLicenses] Scraping public contractor license databases...")

    # Florida DBPR — Electrical Contractors (license type ECO = electrical contractor)
    fl_url = "https://www.myfloridalicense.com/SearchDetail.asp"
    fl_api = "https://www.myfloridalicense.com/wl11.asp"

    fl_license_types = [
        ("EC", "Electrical Contractor"),
        ("CGC", "General Contractor"),
        ("CUC", "Underground Utility Contractor"),
    ]
    for lic_type, lic_desc in fl_license_types:
        time.sleep(REQUEST_DELAY)
        r = _post(fl_api, data={
            "LicenseType": lic_type,
            "searchField": "NAME",
            "txtName": "",
            "chkShowExpired": "off",
            "Submit": "Search",
        })
        if r:
            soup = BeautifulSoup(r.text, "lxml")
            for row in soup.select("table tr")[1:]:
                cells = [td.get_text(strip=True) for td in row.find_all("td")]
                if len(cells) >= 2:
                    name = cells[1] if len(cells) > 1 else cells[0]
                    if name and len(name) > 3:
                        key = f"fl_license_{lic_type}::{name.lower()[:50]}"
                        if not _is_seen(conn, key):
                            lead = _make_lead(name, "", f"FL-DBPR-{lic_type}",
                                              "Data Center & AI Infrastructure" if lic_type == "EC" else "Water & Wastewater",
                                              state="FL")
                            leads.append(lead)
                            _mark_seen(conn, key)

    # Texas TDLR — Electrical Contractors
    tx_api = "https://www.tdlr.texas.gov/LicenseSearch/licfile.asp"
    time.sleep(REQUEST_DELAY)
    r = _get(tx_api, params={
        "lictype": "ELEC",
        "LicName": "",
        "LicCity": "",
        "LicState": "TX",
    })
    if r:
        soup = BeautifulSoup(r.text, "lxml")
        for row in soup.select("table.searchresults tr, table tr")[1:50]:
            cells = [td.get_text(strip=True) for td in row.find_all("td")]
            if cells and len(cells[0]) > 3:
                name = cells[0]
                key = f"tx_tdlr::{name.lower()[:50]}"
                if not _is_seen(conn, key):
                    lead = _make_lead(name, "", "TX-TDLR", "Data Center & AI Infrastructure", state="TX")
                    leads.append(lead)
                    _mark_seen(conn, key)

    # Virginia DPOR — Engineering Firms (water + data center EPCs)
    va_api = "https://www.dpor.virginia.gov/LicenseSearch"
    time.sleep(REQUEST_DELAY)
    r = _get(va_api, params={
        "LicenseTypeCode": "0900",  # Engineering firm
        "BusinessName": "",
    })
    if r:
        soup = BeautifulSoup(r.text, "lxml")
        for el in soup.select(".search-result .business-name, table tr td:nth-child(2)"):
            name = el.get_text(strip=True)
            if name and len(name) > 3:
                key = f"va_dpor::{name.lower()[:50]}"
                if not _is_seen(conn, key):
                    lead = _make_lead(name, "", "VA-DPOR", "Water & Wastewater", state="VA")
                    leads.append(lead)
                    _mark_seen(conn, key)

    logger.info("[StateLicenses] Done: %d new leads", len(leads))
    return leads


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 13: Fairfax County + Phoenix + Columbus Building Permit APIs
# Data center hot zones — permits for large commercial construction
# ─────────────────────────────────────────────────────────────────────────────

def scrape_building_permits(conn: sqlite3.Connection) -> list[dict]:
    """
    Scrape public building permit databases in data center hot zones.
    Large commercial permits ($5M+) in these areas are almost always
    data centers or mission-critical facilities.
    """
    leads = []
    logger.info("[Permits] Scraping building permit databases for data center construction...")

    # Fairfax County, VA — open data API (Northern Virginia = #1 US data center market)
    fairfax_api = "https://data.fairfaxcounty.gov/resource/i9w4-dms4.json"
    time.sleep(REQUEST_DELAY)
    r = _get(fairfax_api, params={
        "$where": "permitvalue > 5000000 AND permittype='BUILDING'",
        "$limit": "200",
        "$order": "issuedate DESC",
    })
    if r:
        try:
            permits = r.json()
            for p in permits:
                name = p.get("ownername", p.get("applicantname", p.get("contractorname", "")))
                if not name:
                    continue
                value = p.get("permitvalue", "0")
                desc = p.get("workdescription", p.get("description", ""))
                key = f"fairfax_permit::{name.lower()[:50]}"
                if not _is_seen(conn, key):
                    lead = _make_lead(
                        name, "", "Fairfax-Permit",
                        "Data Center & AI Infrastructure",
                        state="VA", city="Fairfax County",
                        raw={"permit_value": value, "description": desc[:200]},
                    )
                    leads.append(lead)
                    _mark_seen(conn, key)
            logger.info("[Permits] Fairfax County: %d permits found", len(permits))
        except Exception as e:
            logger.debug("[Permits] Fairfax parse failed: %s", e)

    # Maricopa County, AZ — Phoenix metro (major data center growth area)
    maricopa_api = "https://data.maricopacounty.gov/resource/bxnm-5pmb.json"
    time.sleep(REQUEST_DELAY)
    r = _get(maricopa_api, params={
        "$where": "estimated_valuation > 5000000",
        "$limit": "200",
        "$order": "issue_date DESC",
    })
    if r:
        try:
            permits = r.json()
            for p in permits:
                name = p.get("owner_name", p.get("contractor_name", p.get("applicant_name", "")))
                if not name:
                    continue
                key = f"maricopa_permit::{name.lower()[:50]}"
                if not _is_seen(conn, key):
                    lead = _make_lead(
                        name, "", "Maricopa-Permit",
                        "Data Center & AI Infrastructure",
                        state="AZ", city="Phoenix Metro",
                        raw={"permit_value": p.get("estimated_valuation", ""),
                             "type": p.get("permit_type_description", "")},
                    )
                    leads.append(lead)
                    _mark_seen(conn, key)
            logger.info("[Permits] Maricopa County: %d permits found", len(permits))
        except Exception as e:
            logger.debug("[Permits] Maricopa parse failed: %s", e)

    # Columbus, OH — emerging data center hub (AWS, Google, Meta all building here)
    columbus_api = "https://opendata.columbus.gov/api/explore/v2.1/catalog/datasets/building-permits/records"
    time.sleep(REQUEST_DELAY)
    r = _get(columbus_api, params={
        "where": "estimated_project_cost > 5000000",
        "order_by": "issue_date DESC",
        "limit": "100",
    })
    if r:
        try:
            data = r.json()
            permits = data.get("results", data.get("records", []))
            for p in permits:
                fields = p.get("fields", p)
                name = fields.get("contractor_name", fields.get("owner_name", ""))
                if not name:
                    continue
                key = f"columbus_permit::{name.lower()[:50]}"
                if not _is_seen(conn, key):
                    lead = _make_lead(
                        name, "", "Columbus-OH-Permit",
                        "Data Center & AI Infrastructure",
                        state="OH", city="Columbus",
                        raw={"cost": fields.get("estimated_project_cost", ""),
                             "type": fields.get("permit_type", "")},
                    )
                    leads.append(lead)
                    _mark_seen(conn, key)
        except Exception as e:
            logger.debug("[Permits] Columbus parse failed: %s", e)

    logger.info("[Permits] Done: %d new leads", len(leads))
    return leads


# ─────────────────────────────────────────────────────────────────────────────
# POWER & GRID SECTOR SCRAPERS
# ─────────────────────────────────────────────────────────────────────────────

def scrape_nema(conn: sqlite3.Connection) -> list[dict]:
    """
    NEMA (National Electrical Manufacturers Association) member directory.
    ~325 member companies — all building electrical infrastructure.
    URL: https://www.nema.org/membership/member-directory
    """
    leads = []
    logger.info("[NEMA] Scraping member directory...")

    urls = [
        "https://www.nema.org/membership/member-directory",
        "https://www.nema.org/about/membership/member-companies",
    ]

    for url in urls:
        time.sleep(REQUEST_DELAY)
        r = _get(url)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "html.parser")

        # Try multiple selector patterns
        for selector in [".member-card", ".member-listing", ".company-name",
                         "[class*='member']", "li a", "td a"]:
            items = soup.select(selector)
            if len(items) > 10:
                for item in items:
                    name = item.get_text(strip=True)
                    if len(name) > 5 and len(name) < 120:
                        href = item.get("href", "")
                        domain = _extract_domain(href) if href.startswith("http") else ""
                        key = f"nema::{name.lower()[:60]}"
                        if not _is_seen(conn, key):
                            leads.append(_make_lead(
                                name, domain, "NEMA-Member-Directory",
                                "Power & Grid Infrastructure",
                                raw={"url": href},
                            ))
                            _mark_seen(conn, key)
                break

        if leads:
            break

    # Fallback: MapYourShow exhibitor list for NEMA EV & Energy conference
    if not leads:
        time.sleep(REQUEST_DELAY)
        r = _get("https://www.mapyourshow.com/8_0/exhview/index.cfm?show=nema")
        if r:
            soup = BeautifulSoup(r.text, "html.parser")
            for tag in soup.find_all(class_=re.compile(r"exhibitor|company|booth")):
                name = tag.get_text(strip=True)
                if 5 < len(name) < 120:
                    key = f"nema_show::{name.lower()[:60]}"
                    if not _is_seen(conn, key):
                        leads.append(_make_lead(
                            name, "", "NEMA-Exhibitor",
                            "Power & Grid Infrastructure",
                        ))
                        _mark_seen(conn, key)

    logger.info("[NEMA] Done: %d new leads", len(leads))
    return leads


def scrape_ferc_eia_projects(conn: sqlite3.Connection) -> list[dict]:
    """
    Pull active power generation projects from EIA generator queue data.
    Uses EIA API (free, no key needed for public data) to find companies
    with new generators entering service — these are the EPCs' clients and
    the EPCs themselves on larger utility-scale projects.
    """
    leads = []
    logger.info("[FERC/EIA] Pulling active generation project applicants...")

    # EIA generator capacity additions — operating generators added recently
    eia_url = "https://api.eia.gov/v2/electricity/operating-generator-capacity/data/"
    eia_key = os.environ.get("EIA_API_KEY", "")

    params = {
        "frequency": "monthly",
        "data[0]": "nameplate-capacity-mw",
        "facets[status][]": "OP",
        "facets[energy_source_code][]": ["SUN", "WND", "NG", "NUC", "WAT", "MWH"],
        "start": "2024-01",
        "sort[0][column]": "nameplate-capacity-mw",
        "sort[0][direction]": "desc",
        "offset": 0,
        "length": 5000,
    }
    if eia_key:
        params["api_key"] = eia_key

    time.sleep(REQUEST_DELAY)
    r = _get(eia_url, params=params)
    if r:
        try:
            data = r.json().get("response", {}).get("data", [])
            for row in data:
                name = row.get("entityName", "") or row.get("plant_name", "")
                state = row.get("stateDescription", row.get("state", ""))[:2] if row.get("stateDescription", row.get("state", "")) else ""
                mw = row.get("nameplate-capacity-mw", 0)
                if name and float(mw or 0) >= 10:
                    key = f"eia_gen::{name.lower()[:60]}"
                    if not _is_seen(conn, key):
                        leads.append(_make_lead(
                            name, "", "EIA-Generator-Capacity",
                            "Power & Grid Infrastructure",
                            state=state,
                            raw={"capacity_mw": mw, "source": row.get("energy_source_code", "")},
                        ))
                        _mark_seen(conn, key)
        except Exception as e:
            logger.warning("[FERC/EIA] Parse failed: %s", e)

    # FERC eLibrary RSS — active project filings
    time.sleep(REQUEST_DELAY)
    ferc_rss = "https://www.ferc.gov/news-events/news/news-releases/rss.xml"
    r2 = _get(ferc_rss)
    if r2:
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(r2.text)
            for item in root.findall(".//item"):
                title = (item.findtext("title") or "").strip()
                desc = (item.findtext("description") or "").strip()
                link = (item.findtext("link") or "").strip()
                # Extract company name from FERC filing titles like "Company X — Application"
                m = re.match(r"^([A-Z][^—\-|]+?)\s*(?:—|-|\|)", title)
                if m:
                    name = m.group(1).strip()
                    if 5 < len(name) < 100:
                        key = f"ferc_rss::{name.lower()[:60]}"
                        if not _is_seen(conn, key):
                            leads.append(_make_lead(
                                name, "", "FERC-RSS-Filing",
                                "Power & Grid Infrastructure",
                                raw={"title": title, "link": link},
                            ))
                            _mark_seen(conn, key)
        except Exception as e:
            logger.warning("[FERC/EIA] RSS parse failed: %s", e)

    logger.info("[FERC/EIA] Done: %d new leads", len(leads))
    return leads


def scrape_agc_power(conn: sqlite3.Connection) -> list[dict]:
    """
    AGC (Associated General Contractors) Power & Energy division members.
    URL: https://www.agc.org
    """
    leads = []
    logger.info("[AGC Power] Scraping power contractor members...")

    # AGC member search — filter to power NAICS
    urls = [
        "https://www.agc.org/learn/construction-data/find-a-member",
        "https://www.agc.org/member-directory",
        "https://www.agc.org/about/membership/find-a-member",
    ]

    for url in urls:
        time.sleep(REQUEST_DELAY)
        r = _get(url)
        if r and len(r.text) > 2000:
            soup = BeautifulSoup(r.text, "html.parser")
            for tag in soup.find_all(class_=re.compile(r"member|company|contractor")):
                name = tag.get_text(strip=True)
                if 5 < len(name) < 100 and any(kw in name.lower() for kw in
                        ["electric", "power", "energy", "grid", "utility",
                         "construction", "engineering", "EPC", "substation"]):
                    key = f"agc_power::{name.lower()[:60]}"
                    if not _is_seen(conn, key):
                        leads.append(_make_lead(
                            name, "", "AGC-Power-Member",
                            "Power & Grid Infrastructure",
                        ))
                        _mark_seen(conn, key)
            if leads:
                break

    # Fallback: POWERCON / ELECTRI International contractor lists
    if not leads:
        time.sleep(REQUEST_DELAY)
        r = _get("https://www.electri.org/about/contractor-members/")
        if r:
            soup = BeautifulSoup(r.text, "html.parser")
            for tag in soup.find_all(["li", "p", "td"]):
                name = tag.get_text(strip=True)
                if 5 < len(name) < 100:
                    key = f"electri::{name.lower()[:60]}"
                    if not _is_seen(conn, key):
                        leads.append(_make_lead(
                            name, "", "ELECTRI-Contractor-Member",
                            "Power & Grid Infrastructure",
                        ))
                        _mark_seen(conn, key)

    logger.info("[AGC Power] Done: %d new leads", len(leads))
    return leads


def scrape_enr_power(conn: sqlite3.Connection) -> list[dict]:
    """
    ENR Top Specialty Contractors — Power/Energy category.
    Pre-vetted, revenue-qualified power EPCs.
    """
    leads = []
    logger.info("[ENR Power] Scraping ENR top power contractors...")

    enr_urls = [
        "https://www.enr.com/toplists/2024-Top-600-Specialty-Contractors-Power",
        "https://www.enr.com/toplists/2023-Top-600-Specialty-Contractors-Power",
        "https://www.enr.com/toplists/2024-Top-400-Contractors",
    ]

    for url in enr_urls:
        time.sleep(REQUEST_DELAY)
        r = _get(url)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "html.parser")

        for selector in ["[class*='contractor']", "[class*='company']",
                         "td:first-child", ".ranklist-row td"]:
            items = soup.select(selector)
            for item in items:
                name = item.get_text(strip=True)
                if 5 < len(name) < 100 and not name.isdigit():
                    key = f"enr_power::{name.lower()[:60]}"
                    if not _is_seen(conn, key):
                        leads.append(_make_lead(
                            name, "", "ENR-Top-Power-Contractors",
                            "Power & Grid Infrastructure",
                            raw={"source_url": url},
                        ))
                        _mark_seen(conn, key)

        if leads:
            break

    logger.info("[ENR Power] Done: %d new leads", len(leads))
    return leads


def scrape_ercot_queue(conn: sqlite3.Connection) -> list[dict]:
    """
    ERCOT (Texas grid) interconnection queue — active projects.
    Developers with projects in queue need EPC contractors.
    URL: https://www.ercot.com/gridinfo/resource
    """
    leads = []
    logger.info("[ERCOT Queue] Scraping Texas interconnection queue...")

    # ERCOT publishes quarterly GIS reports — discover current URL from the resource page
    queue_urls = []
    time.sleep(REQUEST_DELAY)
    index_r = _get("https://www.ercot.com/gridinfo/resource")
    if index_r:
        index_soup = BeautifulSoup(index_r.text, "html.parser")
        for a in index_soup.find_all("a", href=True):
            href = a["href"]
            if "GIS_Report" in href and href.endswith(".xlsx"):
                full_url = href if href.startswith("http") else f"https://www.ercot.com{href}"
                queue_urls.append(full_url)
                if len(queue_urls) >= 2:
                    break
    # Hardcoded recent fallbacks
    if not queue_urls:
        queue_urls = [
            "https://www.ercot.com/files/docs/2025/01/10/GIS_Report_January_2025.xlsx",
            "https://www.ercot.com/files/docs/2024/10/10/GIS_Report_October_2024.xlsx",
        ]

    for url in queue_urls:
        time.sleep(REQUEST_DELAY)
        r = _get(url)
        if r and r.content:
            try:
                import io
                try:
                    import openpyxl
                    wb = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True)
                    ws = wb.active
                    for row in ws.iter_rows(min_row=2, values_only=True):
                        if row and len(row) > 3:
                            # ERCOT GIS reports have company name in col 3 or 4
                            name = str(row[3] or row[2] or "").strip()
                            state = "TX"
                            if name and 5 < len(name) < 120:
                                key = f"ercot_queue::{name.lower()[:60]}"
                                if not _is_seen(conn, key):
                                    leads.append(_make_lead(
                                        name, "", "ERCOT-Interconnection-Queue",
                                        "Power & Grid Infrastructure",
                                        state=state,
                                        raw={"queue_row": list(row[:6])},
                                    ))
                                    _mark_seen(conn, key)
                except ImportError:
                    pass
            except Exception as e:
                logger.debug("[ERCOT] Excel parse failed: %s", e)
            if leads:
                break

    # Fallback: ERCOT resource page HTML
    if not leads:
        time.sleep(REQUEST_DELAY)
        r = _get("https://www.ercot.com/gridinfo/resource")
        if r:
            soup = BeautifulSoup(r.text, "html.parser")
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if "GIS" in href or "queue" in href.lower():
                    logger.info("[ERCOT] Found queue file: %s", href)
                    break

    logger.info("[ERCOT Queue] Done: %d new leads", len(leads))
    return leads


# ─────────────────────────────────────────────────────────────────────────────
# INDUSTRIAL & MANUFACTURING SECTOR SCRAPERS
# ─────────────────────────────────────────────────────────────────────────────

def scrape_smacna(conn: sqlite3.Connection) -> list[dict]:
    """
    SMACNA (Sheet Metal and Air Conditioning Contractors National Association).
    ~1,500 member companies doing HVAC + sheet metal for industrial facilities.
    URL: https://www.smacna.org/membership/find-a-contractor
    """
    leads = []
    logger.info("[SMACNA] Scraping member contractor directory...")

    # SMACNA has a searchable directory via their website
    base_urls = [
        "https://www.smacna.org/membership/find-a-contractor",
        "https://www.smacna.org/membership/contractor-search",
        "https://smacna.org/find-a-member",
    ]

    for url in base_urls:
        time.sleep(REQUEST_DELAY)
        r = _get(url)
        if not r or len(r.text) < 2000:
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        for selector in [".contractor-card", ".member-result", ".company",
                         "[class*='contractor']", "[class*='member']"]:
            items = soup.select(selector)
            if len(items) > 5:
                for item in items:
                    name = item.get_text(strip=True).split("\n")[0]
                    if 5 < len(name) < 120:
                        key = f"smacna::{name.lower()[:60]}"
                        if not _is_seen(conn, key):
                            leads.append(_make_lead(
                                name, "", "SMACNA-Member-Directory",
                                "Industrial & Manufacturing Facilities",
                            ))
                            _mark_seen(conn, key)
                break
        if leads:
            break

    # Fallback: SMACNA chapter list → chapter URLs → chapter member pages
    if not leads:
        time.sleep(REQUEST_DELAY)
        r = _get("https://www.smacna.org/membership/local-associations")
        if r:
            soup = BeautifulSoup(r.text, "html.parser")
            chapter_links = [a["href"] for a in soup.find_all("a", href=True)
                             if "smacna" in a["href"].lower() and "chapter" in a.get_text().lower()]
            for chapter_url in chapter_links[:5]:
                time.sleep(REQUEST_DELAY)
                r2 = _get(chapter_url)
                if r2:
                    soup2 = BeautifulSoup(r2.text, "html.parser")
                    for tag in soup2.find_all(["li", "td", "p"]):
                        name = tag.get_text(strip=True)
                        if 5 < len(name) < 100:
                            key = f"smacna_ch::{name.lower()[:60]}"
                            if not _is_seen(conn, key):
                                leads.append(_make_lead(
                                    name, "", "SMACNA-Chapter-Member",
                                    "Industrial & Manufacturing Facilities",
                                ))
                                _mark_seen(conn, key)

    logger.info("[SMACNA] Done: %d new leads", len(leads))
    return leads


def scrape_abc_contractors(conn: sqlite3.Connection) -> list[dict]:
    """
    ABC (Associated Builders and Contractors) merit-shop industrial contractor members.
    21,000+ members across 67 chapters. Pulls Excellence in Construction award winners
    (public list) + chapter member pages where available.
    """
    leads = []
    logger.info("[ABC] Scraping contractor members...")

    # ABC Excellence in Construction winners (public list, updated annually)
    eic_urls = [
        "https://www.abc.org/News-Media/News-Releases/entryid/19000/abc-announces-excellence-in-construction-award-winners",
        "https://www.abc.org/News-Media/Awards/Excellence-in-Construction",
        "https://abc.org/EIC",
    ]

    for url in eic_urls:
        time.sleep(REQUEST_DELAY)
        r = _get(url)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup.find_all(["li", "td", "h3", "h4", "strong"]):
            name = tag.get_text(strip=True)
            if 5 < len(name) < 100 and not any(x in name.lower() for x in
                    ["award", "winner", "category", "project", "excellence"]):
                key = f"abc_eic::{name.lower()[:60]}"
                if not _is_seen(conn, key):
                    leads.append(_make_lead(
                        name, "", "ABC-Excellence-in-Construction",
                        "Industrial & Manufacturing Facilities",
                    ))
                    _mark_seen(conn, key)
        if leads:
            break

    # ABC chapter member directories (TX, FL, GA, NC, OH chapters)
    chapter_states = {
        "TX": ("Texas", "https://texasabc.org/members/"),
        "FL": ("Florida", "https://abcflorida.org/membership/member-directory/"),
        "GA": ("Georgia", "https://abcga.org/membership/member-directory/"),
        "NC": ("Carolinas", "https://abccarolinas.org/membership/"),
        "OH": ("Ohio", "https://abcohio.net/membership/members/"),
    }

    for state_code, (state_label, url) in chapter_states.items():
        time.sleep(REQUEST_DELAY)
        r = _get(url)
        if not r or len(r.text) < 1000:
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        for selector in [".member-name", ".company-name", "[class*='member']",
                         "td:first-child", "li"]:
            items = soup.select(selector)
            if len(items) > 5:
                for item in items:
                    name = item.get_text(strip=True)
                    if 5 < len(name) < 100:
                        key = f"abc_{state_code.lower()}::{name.lower()[:60]}"
                        if not _is_seen(conn, key):
                            leads.append(_make_lead(
                                name, "", f"ABC-{state_label}-Chapter",
                                "Industrial & Manufacturing Facilities",
                                state=state_code,
                            ))
                            _mark_seen(conn, key)
                break

    logger.info("[ABC] Done: %d new leads", len(leads))
    return leads


def scrape_nfpa_contractors(conn: sqlite3.Connection) -> list[dict]:
    """
    NFPA (National Fire Protection Association) corporate member companies.
    Fire protection contractors are critical path on every industrial build.
    """
    leads = []
    logger.info("[NFPA] Scraping corporate member companies...")

    urls = [
        "https://www.nfpa.org/Membership/Member-Sections-and-Networks",
        "https://www.nfpa.org/Public-Education/Find-a-Pro",
        "https://www.nfpa.org/about/contact/member-directory",
    ]

    for url in urls:
        time.sleep(REQUEST_DELAY)
        r = _get(url)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        for selector in [".member-item", ".company", "[class*='member']",
                         "[class*='sponsor']", ".corporate"]:
            items = soup.select(selector)
            if len(items) > 5:
                for item in items:
                    name = item.get_text(strip=True)
                    if 5 < len(name) < 120:
                        key = f"nfpa::{name.lower()[:60]}"
                        if not _is_seen(conn, key):
                            leads.append(_make_lead(
                                name, "", "NFPA-Corporate-Member",
                                "Industrial & Manufacturing Facilities",
                            ))
                            _mark_seen(conn, key)
                break
        if leads:
            break

    # Fallback: NFPA Conference & Expo exhibitor list (annual, public)
    if not leads:
        time.sleep(REQUEST_DELAY)
        r = _get("https://www.nfpa.org/Conference-and-Expo/Exhibitors")
        if r:
            soup = BeautifulSoup(r.text, "html.parser")
            for tag in soup.find_all(class_=re.compile(r"exhibitor|company|booth|sponsor")):
                name = tag.get_text(strip=True)
                if 5 < len(name) < 100:
                    key = f"nfpa_expo::{name.lower()[:60]}"
                    if not _is_seen(conn, key):
                        leads.append(_make_lead(
                            name, "", "NFPA-Conference-Exhibitor",
                            "Industrial & Manufacturing Facilities",
                        ))
                        _mark_seen(conn, key)

    logger.info("[NFPA] Done: %d new leads", len(leads))
    return leads


def scrape_aiche_corporate(conn: sqlite3.Connection) -> list[dict]:
    """
    AIChE (American Institute of Chemical Engineers) corporate members.
    Chemical/process engineering firms = chemical plant EPCs.
    """
    leads = []
    logger.info("[AIChE] Scraping corporate member companies...")

    urls = [
        "https://www.aiche.org/giving/corporate-engagement",
        "https://www.aiche.org/community/sites/divisions/engineering-construction-contracts",
        "https://www.aiche.org/conferences/aiche-annual-meeting/2024/sponsor",
    ]

    for url in urls:
        time.sleep(REQUEST_DELAY)
        r = _get(url)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        for selector in [".sponsor", ".company", ".corporate-member",
                         "[class*='sponsor']", "[class*='member']", "li"]:
            items = soup.select(selector)
            if len(items) > 3:
                for item in items:
                    name = item.get_text(strip=True)
                    if 5 < len(name) < 120:
                        key = f"aiche::{name.lower()[:60]}"
                        if not _is_seen(conn, key):
                            leads.append(_make_lead(
                                name, "", "AIChE-Corporate-Member",
                                "Industrial & Manufacturing Facilities",
                            ))
                            _mark_seen(conn, key)
                break
        if leads:
            break

    # AICHE CCPS (Process Safety) Sponsoring Companies — pure industrial EPC list
    time.sleep(REQUEST_DELAY)
    r = _get("https://www.aiche.org/ccps/membership/sponsoring-companies")
    if r:
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup.find_all(["li", "p", "td", "div"]):
            name = tag.get_text(strip=True)
            if 5 < len(name) < 100 and len(name.split()) <= 8:
                key = f"aiche_ccps::{name.lower()[:60]}"
                if not _is_seen(conn, key):
                    leads.append(_make_lead(
                        name, "", "AIChE-CCPS-Sponsor",
                        "Industrial & Manufacturing Facilities",
                    ))
                    _mark_seen(conn, key)

    logger.info("[AIChE] Done: %d new leads", len(leads))
    return leads


def scrape_tceq_permits(conn: sqlite3.Connection) -> list[dict]:
    """
    Texas TCEQ (Commission on Environmental Quality) industrial air permits.
    Industrial air permit filed = facility being built = EPC contracted.
    Focuses on major construction permits (NSR, Title V) in Texas.
    """
    leads = []
    logger.info("[TCEQ] Scraping Texas industrial facility permits...")

    # TCEQ STEERS public records — new permit applications
    urls = [
        "https://www15.tceq.texas.gov/crpub/index.cfm?fuseaction=regent.fetchRecentRecords",
        "https://www.tceq.texas.gov/permitting/air/airpermits.html",
    ]

    for url in urls:
        time.sleep(REQUEST_DELAY)
        r = _get(url)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        # TCEQ permit pages list applicant company names
        for tag in soup.find_all(["td", "li", "p"]):
            name = tag.get_text(strip=True)
            if (5 < len(name) < 100 and
                    any(kw in name.lower() for kw in
                        ["inc", "llc", "corp", "company", "industries",
                         "manufacturing", "chemical", "plant", "refining"])):
                key = f"tceq::{name.lower()[:60]}"
                if not _is_seen(conn, key):
                    leads.append(_make_lead(
                        name, "", "TCEQ-Air-Permit",
                        "Industrial & Manufacturing Facilities",
                        state="TX",
                    ))
                    _mark_seen(conn, key)
        if leads:
            break

    # USASpending industrial contracts in Texas + Louisiana (highest industrial density)
    for state in ["TX", "LA"]:
        time.sleep(REQUEST_DELAY)
        payload = {
            "filters": {
                "time_period": [{"start_date": "2023-01-01", "end_date": "2026-01-01"}],
                "award_type_codes": ["A", "B", "C", "D"],
                "naics_codes": ["236210", "237990"],
                "place_of_performance_locations": [{"country": "USA", "state": state}],
            },
            "fields": ["Recipient Name", "Award Amount",
                       "Place of Performance State Code", "Place of Performance City Name"],
            "sort": "Award Amount",
            "order": "desc",
            "limit": 100,
        }
        r = _post("https://api.usaspending.gov/api/v2/search/spending_by_award/", json=payload)
        if r:
            try:
                for rec in r.json().get("results", []):
                    name = rec.get("Recipient Name", "")
                    if name and len(name) > 3:
                        key = f"tceq_spend_{state}::{name.lower()[:60]}"
                        if not _is_seen(conn, key):
                            leads.append(_make_lead(
                                name, "", f"USASpending-Industrial-{state}",
                                "Industrial & Manufacturing Facilities",
                                state=state,
                            ))
                            _mark_seen(conn, key)
            except Exception as e:
                logger.debug("[TCEQ] USASpending %s parse failed: %s", state, e)

    logger.info("[TCEQ] Done: %d new leads", len(leads))
    return leads


# ─────────────────────────────────────────────────────────────────────────────
# DEFENSE & NUCLEAR SECTOR SCRAPERS
# ─────────────────────────────────────────────────────────────────────────────

def scrape_doe_contractors(conn: sqlite3.Connection) -> list[dict]:
    """
    DOE (Department of Energy) M&O and prime contractors.
    These are the highest-value defense/nuclear EPC clients and often
    are themselves large EPCs subcontracting infrastructure work.
    URL: https://www.energy.gov/management/office-management/operational-management/contractor-information
    """
    leads = []
    logger.info("[DOE] Scraping DOE contractor registry...")

    doi_urls = [
        "https://www.energy.gov/em/contractor-information",
        "https://www.energy.gov/em/doe-environmental-management-contractors",
        "https://www.energy.gov/management/federal-personnel/acquisition-and-project-management/contractor-workforce-analysis",
        "https://www.energy.gov/em",
    ]

    for url in doi_urls:
        time.sleep(REQUEST_DELAY)
        r = _get(url)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "html.parser")

        for selector in ["table td", "li", ".contractor-name", ".field-item",
                         "[class*='contractor']", "p"]:
            items = soup.select(selector)
            found = 0
            for item in items:
                name = item.get_text(strip=True)
                if (5 < len(name) < 120 and
                        any(kw in name.lower() for kw in
                            ["inc", "llc", "corp", "company", "group", "contractor",
                             "bechtel", "fluor", "aecom", "jacobs", "leidos",
                             "holtec", "westinghouse", "management"])):
                    key = f"doe::{name.lower()[:60]}"
                    if not _is_seen(conn, key):
                        leads.append(_make_lead(
                            name, "", "DOE-Contractor-Registry",
                            "Defense & Nuclear Infrastructure",
                            raw={"source_url": url},
                        ))
                        _mark_seen(conn, key)
                        found += 1
            if found > 3:
                break

        if leads:
            break

    # USASpending — nuclear + defense facility construction NAICS codes
    for naics_code in ["237990", "236210", "541330"]:
        time.sleep(REQUEST_DELAY)
        payload = {
            "filters": {
                "time_period": [{"start_date": "2022-01-01", "end_date": "2026-01-01"}],
                "award_type_codes": ["A", "B", "C", "D"],
                "naics_codes": [naics_code],
                "place_of_performance_locations": [
                    {"country": "USA", "state": s} for s in DEFENSE_STATES[:8]
                ],
            },
            "fields": ["Recipient Name", "Award Amount",
                       "Place of Performance State Code", "Place of Performance City Name"],
            "sort": "Award Amount",
            "order": "desc",
            "limit": 100,
        }
        r = _post("https://api.usaspending.gov/api/v2/search/spending_by_award/", json=payload)
        if r:
            try:
                for rec in r.json().get("results", []):
                    name = rec.get("Recipient Name", "")
                    state = rec.get("Place of Performance State Code", "")
                    amount = rec.get("Award Amount", 0)
                    if name and len(name) > 3:
                        key = f"doe_spend_{naics_code}::{name.lower()[:60]}"
                        if not _is_seen(conn, key):
                            leads.append(_make_lead(
                                name, "", f"USASpending-Defense-NAICS-{naics_code}",
                                "Defense & Nuclear Infrastructure",
                                state=state,
                                raw={"award_total": amount, "naics": naics_code},
                            ))
                            _mark_seen(conn, key)
            except Exception as e:
                logger.warning("[DOE] USASpending NAICS %s parse failed: %s", naics_code, e)

    logger.info("[DOE] Done: %d new leads", len(leads))
    return leads


def scrape_nrc_licensees(conn: sqlite3.Connection) -> list[dict]:
    """
    NRC (Nuclear Regulatory Commission) licensed reactor operators and facility owners.
    These companies need EPC work for life extension, decommissioning, and SMR builds.
    URL: https://www.nrc.gov/info-finder/reactors/
    """
    leads = []
    logger.info("[NRC] Scraping licensed nuclear facility operators...")

    urls = [
        "https://www.nrc.gov/info-finder/reactors/index",
        "https://www.nrc.gov/reactors/operating/list-power-reactor-units.html",
        "https://www.nrc.gov/reactors/operating.html",
    ]

    for url in urls:
        time.sleep(REQUEST_DELAY)
        try:
            r = requests.get(url, headers=HEADERS, timeout=45)
            r.raise_for_status()
        except Exception as e:
            logger.warning("GET %s failed: %s", url, e)
            r = None
        if not r:
            continue
        soup = BeautifulSoup(r.text, "html.parser")

        # NRC page has a table of reactors with licensee company in each row
        for row in soup.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) >= 3:
                # Licensee is typically in cells[1] or cells[2]
                for cell in cells[1:4]:
                    name = cell.get_text(strip=True)
                    if (5 < len(name) < 100 and
                            not name.lower() in {"unit", "state", "location", "status", "type"}):
                        key = f"nrc::{name.lower()[:60]}"
                        if not _is_seen(conn, key):
                            leads.append(_make_lead(
                                name, "", "NRC-Reactor-Licensee",
                                "Defense & Nuclear Infrastructure",
                                raw={"source_url": url},
                            ))
                            _mark_seen(conn, key)
                        break

        if leads:
            break

    # NRC materials licensees (research reactors, fuel facilities)
    time.sleep(REQUEST_DELAY)
    r = _get("https://www.nrc.gov/info-finder/materials/")
    if r:
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup.find_all(class_=re.compile(r"licensee|facility|company")):
            name = tag.get_text(strip=True)
            if 5 < len(name) < 100:
                key = f"nrc_mat::{name.lower()[:60]}"
                if not _is_seen(conn, key):
                    leads.append(_make_lead(
                        name, "", "NRC-Materials-Licensee",
                        "Defense & Nuclear Infrastructure",
                    ))
                    _mark_seen(conn, key)

    logger.info("[NRC] Done: %d new leads", len(leads))
    return leads


def scrape_same_members(conn: sqlite3.Connection) -> list[dict]:
    """
    SAME (Society of American Military Engineers) corporate sustaining members.
    A/E firms with cleared personnel doing defense facility work.
    URL: https://www.same.org
    """
    leads = []
    logger.info("[SAME] Scraping military engineer corporate members...")

    urls = [
        "https://www.same.org/membership/sustaining-members",
        "https://www.same.org/about/corporate-members",
        "https://www.same.org/about/sustaining-members",
        "https://www.same.org/membership",
    ]

    for url in urls:
        time.sleep(REQUEST_DELAY)
        r = _get(url)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "html.parser")

        for selector in [".corporate-member", ".member-card", ".company",
                         "[class*='member']", "li", "td"]:
            items = soup.select(selector)
            if len(items) > 5:
                for item in items:
                    name = item.get_text(strip=True)
                    word_count = len(name.split())
                    # Filter out nav items: must look like a company name (1-6 words, no verbs/nav noise)
                    if (5 < len(name) < 100 and 1 <= word_count <= 6 and
                            not any(kw in name.lower() for kw in
                                    ["donate", "membership", "events", "awards", "scholarships",
                                     "login", "register", "contact", "news", "about", "click",
                                     "foundation", "fellows", "officers", "registry", "sponsorship",
                                     "opportunities", "program", "download", "webinar", "celebration"])):
                        key = f"same::{name.lower()[:60]}"
                        if not _is_seen(conn, key):
                            leads.append(_make_lead(
                                name, "", "SAME-Corporate-Member",
                                "Defense & Nuclear Infrastructure",
                            ))
                            _mark_seen(conn, key)
                break

        if leads:
            break

    # Fallback: SAME Joint Engineer Training Conference (JETC) exhibitor list
    if not leads:
        for year in ["2025", "2024", "2023"]:
            time.sleep(REQUEST_DELAY)
            r = _get(f"https://www.same.org/joint-engineer-training-conference/jetc-{year}/exhibitors")
            if r:
                soup = BeautifulSoup(r.text, "html.parser")
                for tag in soup.find_all(class_=re.compile(r"exhibitor|company|sponsor")):
                    name = tag.get_text(strip=True)
                    if 5 < len(name) < 100:
                        key = f"same_jetc_{year}::{name.lower()[:60]}"
                        if not _is_seen(conn, key):
                            leads.append(_make_lead(
                                name, "", f"SAME-JETC-{year}-Exhibitor",
                                "Defense & Nuclear Infrastructure",
                            ))
                            _mark_seen(conn, key)
                if leads:
                    break

    # USASpending DOD facility construction — base construction + engineering NAICS
    for naics_code in ["236210", "237990", "541330"]:
        time.sleep(REQUEST_DELAY)
        payload = {
            "filters": {
                "time_period": [{"start_date": "2022-01-01", "end_date": "2026-01-01"}],
                "award_type_codes": ["A", "B", "C", "D"],
                "naics_codes": [naics_code],
                "place_of_performance_locations": [
                    {"country": "USA", "state": s} for s in DEFENSE_STATES[:8]
                ],
            },
            "fields": ["Recipient Name", "Award Amount",
                       "Place of Performance State Code", "Place of Performance City Name"],
            "sort": "Award Amount",
            "order": "desc",
            "limit": 100,
        }
        r = _post("https://api.usaspending.gov/api/v2/search/spending_by_award/", json=payload)
        if r:
            try:
                for rec in r.json().get("results", []):
                    name = rec.get("Recipient Name", "")
                    state = rec.get("Place of Performance State Code", "")
                    amount = rec.get("Award Amount", 0)
                    if name and len(name) > 3:
                        key = f"dod_spend_{naics_code}::{name.lower()[:60]}"
                        if not _is_seen(conn, key):
                            leads.append(_make_lead(
                                name, "", f"USASpending-DOD-Facility-{naics_code}",
                                "Defense & Nuclear Infrastructure",
                                state=state,
                                raw={"award_total": amount, "naics": naics_code},
                            ))
                            _mark_seen(conn, key)
            except Exception as e:
                logger.warning("[SAME] USASpending DOD NAICS %s parse failed: %s", naics_code, e)

    logger.info("[SAME] Done: %d new leads", len(leads))
    return leads


# ─────────────────────────────────────────────────────────────────────────────
# ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────────

SOURCE_MAP = {
    # ── Water & Wastewater ──────────────────────────────────────────────────
    "weftec":        ("water",      scrape_weftec),
    "awwa":          ("water",      scrape_awwa),
    "cwsrf":         ("water",      scrape_cwsrf),
    "acec":          ("water",      scrape_acec),
    # ── Data Center & AI Infrastructure ────────────────────────────────────
    "afcom":         ("dc",         scrape_afcom),
    "7x24":          ("dc",         scrape_7x24),
    "bicsi":         ("dc",         scrape_bicsi),
    "neca":          ("dc",         scrape_neca),
    "permits":       ("dc",         scrape_building_permits),
    # ── Power & Grid Infrastructure ─────────────────────────────────────────
    "nema":          ("power",      scrape_nema),
    "ferc_eia":      ("power",      scrape_ferc_eia_projects),
    "agc_power":     ("power",      scrape_agc_power),
    "enr_power":     ("power",      scrape_enr_power),
    "ercot":         ("power",      scrape_ercot_queue),
    # ── Industrial & Manufacturing Facilities ───────────────────────────────
    "smacna":        ("industrial", scrape_smacna),
    "abc":           ("industrial", scrape_abc_contractors),
    "nfpa":          ("industrial", scrape_nfpa_contractors),
    "aiche":         ("industrial", scrape_aiche_corporate),
    "tceq":          ("industrial", scrape_tceq_permits),
    # ── Defense & Nuclear Infrastructure ────────────────────────────────────
    "doe":           ("defense",    scrape_doe_contractors),
    "nrc":           ("defense",    scrape_nrc_licensees),
    "same":          ("defense",    scrape_same_members),
    # ── Cross-sector ────────────────────────────────────────────────────────
    "state_licenses":("both",       scrape_state_licenses),
    "enr":           ("both",       scrape_enr),
    "usaspending":   ("both",       scrape_usaspending),
    "sam":           ("both",       scrape_sam_gov_entities),
}


def run(
    sources: list[str] = None,
    sector: str = "both",
    dry_run: bool = False,
) -> dict:
    conn = _init_db()
    all_leads = []

    active_sources = sources or list(SOURCE_MAP.keys())

    # Filter by sector
    filtered = []
    for name in active_sources:
        if name not in SOURCE_MAP:
            logger.warning("Unknown source: %s", name)
            continue
        src_sector, fn = SOURCE_MAP[name]
        if sector in ("both", "all") or src_sector in (sector, "both", "all"):
            filtered.append((name, src_sector, fn))

    logger.info("Running %d sources: %s", len(filtered), [f[0] for f in filtered])

    for src_name, src_sector, fn in filtered:
        logger.info("=== %s ===", src_name.upper())
        try:
            # Some scrapers accept sector arg
            import inspect
            sig = inspect.signature(fn)
            if "sector" in sig.parameters:
                leads = fn(conn, sector=sector)
            else:
                leads = fn(conn)
            all_leads.extend(leads)
            logger.info("[%s] Contributed %d leads", src_name, len(leads))
        except Exception as e:
            logger.error("[%s] FAILED: %s", src_name, e, exc_info=True)
        time.sleep(0.5)

    logger.info("Total leads collected: %d", len(all_leads))

    if dry_run:
        for lead in all_leads[:20]:
            print(f"  {lead['company_name']} | {lead['source']} | {lead['state']}")
        print(f"  ... and {max(0, len(all_leads) - 20)} more")
        return {"total": len(all_leads), "saved_supabase": 0, "csv": None}

    # Save CSV
    csv_path = _save_to_csv(all_leads)

    # Save Supabase
    saved = _save_to_supabase(all_leads)
    logger.info("Saved %d leads to Supabase table '%s'", saved, SUPABASE_TABLE)

    return {
        "total": len(all_leads),
        "saved_supabase": saved,
        "csv": str(csv_path),
        "by_source": {
            src: len([l for l in all_leads if l["source"].startswith(src[:8])])
            for src, _, _ in filtered
        },
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="EPC Lead Engine — free source scraper")
    parser.add_argument(
        "--source", nargs="+",
        help=f"Sources to run: {', '.join(SOURCE_MAP.keys())}",
    )
    parser.add_argument(
        "--sector",
        choices=["water", "dc", "power", "industrial", "defense", "both", "all"],
        default="both",
        help="Sector filter (both=water+dc legacy; all=every sector)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print results, don't save")
    args = parser.parse_args()

    result = run(
        sources=args.source,
        sector=args.sector,
        dry_run=args.dry_run,
    )
    print(f"\nDone. {result['total']} leads found.")
    if result.get("csv"):
        print(f"CSV: {result['csv']}")
    if result.get("by_source"):
        print("By source:")
        for src, count in result["by_source"].items():
            print(f"  {src}: {count}")


if __name__ == "__main__":
    main()
