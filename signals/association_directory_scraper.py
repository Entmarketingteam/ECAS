#!/usr/bin/env python3
"""
signals/association_directory_scraper.py
Healthcare Referral Pipeline — Association Directory Scraper

Scrapes 6 association directories to build pre-qualified contact lists for
the compounding pharmacy prescriber pipeline. Association members have
self-identified with the niche (e.g., PCAB-accredited = already a compounding
pharmacy that cares about quality) — this is the highest-intent cold list
available before any enrichment.

Associations:
  1. PCAB  — pcab.org/find-a-pharmacy (accredited compounding pharmacies)
  2. APC   — a4pc.org member directory (Alliance for Pharmacy Compounding)
  3. NAMS  — menopause.org (certified menopause practitioners / BHRT prescribers)
  4. IFM   — ifm.org/find-a-practitioner (functional medicine MDs)
  5. ABOM  — abom.org/find-a-physician (obesity medicine / GLP-1 prescribers)
  6. AASM  — sleepeducation.org/find-a-facility (accredited sleep centers)

Output:
  signals/output/association_{name}_{date}.csv  — per-association
  signals/output/associations_combined_{date}.csv — merged with source column

Usage:
  python association_directory_scraper.py
  python association_directory_scraper.py --associations pcab,apc
  python association_directory_scraper.py --output-dir /tmp/associations

Required:
  pip install requests beautifulsoup4 lxml

JS-rendered sites:
  PCAB and NAMS require Playwright or Apify — see comments marked REQUIRES_JS
"""

import argparse
import csv
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("association_scraper")

# ── Constants ─────────────────────────────────────────────────────────────────
TODAY = date.today().isoformat()  # e.g. "2026-04-05"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# Retry config
MAX_RETRIES = 3
RETRY_DELAY = 2.0  # seconds between retries

# Output CSV columns per source type
PHARMACY_COLS = ["source", "pharmacy_name", "city", "state", "phone", "website"]
PHYSICIAN_COLS = ["source", "name", "specialty", "city", "state", "practice_name"]
FACILITY_COLS = ["source", "facility_name", "city", "state", "phone"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_session() -> requests.Session:
    """Return a requests.Session with realistic browser headers."""
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    return session


def safe_get(session: requests.Session, url: str, **kwargs) -> Optional[requests.Response]:
    """GET with retries. Returns None if all attempts fail."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = session.get(url, timeout=20, **kwargs)
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            logger.warning("Attempt %d/%d failed for %s — %s", attempt, MAX_RETRIES, url, exc)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
    return None


def write_csv(rows: list[dict], path: Path, fieldnames: list[str]) -> None:
    """Write list-of-dicts to CSV, creating parent dirs as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    logger.info("Wrote %d records → %s", len(rows), path)


# ── 1. PCAB ───────────────────────────────────────────────────────────────────
# REQUIRES_JS: pcab.org/find-a-pharmacy renders via React. The requests
# attempt below will return a shell HTML page with no pharmacy data.
# Production path: Use Playwright (headless Chromium) or the Apify actor
# "pcab-pharmacy-scraper" (search Apify store). Playwright example at bottom
# of this file. Flag output rows with requires_js=True when JS path is needed.

def scrape_pcab(output_dir: Path) -> list[dict]:
    """
    PCAB — Accredited compounding pharmacies.
    URL: https://pcab.org/find-a-pharmacy
    Extracts: pharmacy_name, city, state, phone, website
    Update frequency: quarterly (new accreditations granted every 3 months)

    REQUIRES_JS: This page is a React SPA. The requests attempt is included
    for completeness and to detect if PCAB ever adds a server-rendered fallback.
    If the parse returns 0 records, switch to Playwright or Apify.
    """
    source = "pcab"
    url = "https://pcab.org/find-a-pharmacy"
    session = make_session()

    logger.info("[PCAB] Attempting requests fetch (SPA — likely requires JS)…")
    resp = safe_get(session, url)

    if resp is None:
        logger.warning("[PCAB] Request failed — use Playwright/Apify scraper instead")
        return _pcab_js_fallback_notice()

    soup = BeautifulSoup(resp.text, "lxml")

    # Attempt to find pharmacy listings in HTML
    # Actual selectors depend on PCAB's markup — update these after inspecting
    # the rendered DOM via browser DevTools.
    rows: list[dict] = []

    # Try common patterns: <tr> rows in a table, or <div class="pharmacy-card">
    cards = soup.select("div.pharmacy-listing, div.pharmacy-card, tr.pharmacy-row")
    if not cards:
        # Try generic table rows (skip header)
        table = soup.find("table")
        if table:
            trs = table.find_all("tr")[1:]
            for tr in trs:
                cols = [td.get_text(strip=True) for td in tr.find_all("td")]
                if len(cols) >= 3:
                    rows.append({
                        "source": source,
                        "pharmacy_name": cols[0] if len(cols) > 0 else "",
                        "city": cols[1] if len(cols) > 1 else "",
                        "state": cols[2] if len(cols) > 2 else "",
                        "phone": cols[3] if len(cols) > 3 else "",
                        "website": cols[4] if len(cols) > 4 else "",
                    })

    if not rows:
        logger.warning(
            "[PCAB] 0 records parsed from HTML — page is JS-rendered. "
            "Switch to Playwright: `playwright_pcab_scraper()` at bottom of file."
        )
        return _pcab_js_fallback_notice()

    out_path = output_dir / f"association_pcab_{TODAY}.csv"
    write_csv(rows, out_path, PHARMACY_COLS)
    return rows


def _pcab_js_fallback_notice() -> list[dict]:
    """
    Returns a single-row placeholder so the combined CSV notes the gap.
    Replace with real Playwright/Apify results before production use.
    """
    return [{
        "source": "pcab",
        "pharmacy_name": "REQUIRES_JS — use Playwright or Apify actor",
        "city": "",
        "state": "",
        "phone": "",
        "website": "https://pcab.org/find-a-pharmacy",
    }]


# ── 2. APC ────────────────────────────────────────────────────────────────────
# APC (Alliance for Pharmacy Compounding) — a4pc.org
# Member directory may be behind login; public search sometimes accessible.
# Update frequency: as members join/renew, typically monthly delta.

def scrape_apc(output_dir: Path) -> list[dict]:
    """
    APC — Alliance for Pharmacy Compounding member directory.
    URL: https://a4pc.org/membership/member-directory/
    Extracts: pharmacy_name, state, contact info (if publicly visible)

    Note: APC may gate their directory behind member login. If 0 results
    are returned, check if a public search endpoint exists under
    https://a4pc.org/find-a-member or similar. Apify can handle login-gated
    pages if credentials are available.
    """
    source = "apc"
    # Try known public directory paths
    candidate_urls = [
        "https://a4pc.org/membership/member-directory/",
        "https://a4pc.org/find-a-member/",
        "https://a4pc.org/members/",
    ]
    session = make_session()
    rows: list[dict] = []

    for url in candidate_urls:
        logger.info("[APC] Trying %s", url)
        resp = safe_get(session, url)
        if resp is None:
            continue

        soup = BeautifulSoup(resp.text, "lxml")

        # Look for member cards, list items, or table rows
        entries = soup.select(
            "div.member-card, div.member-listing, "
            "li.member-item, article.member, "
            "tr.member-row"
        )

        if not entries:
            # Generic: look for any table
            table = soup.find("table")
            if table:
                for tr in table.find_all("tr")[1:]:
                    cols = [td.get_text(strip=True) for td in tr.find_all("td")]
                    if cols:
                        rows.append({
                            "source": source,
                            "pharmacy_name": cols[0] if len(cols) > 0 else "",
                            "city": cols[1] if len(cols) > 1 else "",
                            "state": cols[2] if len(cols) > 2 else "",
                            "phone": cols[3] if len(cols) > 3 else "",
                            "website": cols[4] if len(cols) > 4 else "",
                        })

        for entry in entries:
            name_el = entry.select_one(".member-name, .name, h3, h4")
            state_el = entry.select_one(".state, .location")
            phone_el = entry.select_one(".phone, .tel")
            website_el = entry.select_one("a[href^='http']")

            rows.append({
                "source": source,
                "pharmacy_name": name_el.get_text(strip=True) if name_el else "",
                "city": "",
                "state": state_el.get_text(strip=True) if state_el else "",
                "phone": phone_el.get_text(strip=True) if phone_el else "",
                "website": website_el["href"] if website_el else "",
            })

        if rows:
            logger.info("[APC] Found %d entries at %s", len(rows), url)
            break

    if not rows:
        logger.warning(
            "[APC] 0 records — directory may be login-gated or JS-rendered. "
            "Check https://a4pc.org for public member search or use Apify."
        )
        rows = [{
            "source": source,
            "pharmacy_name": "REQUIRES_MANUAL_CHECK — directory may be login-gated",
            "city": "",
            "state": "",
            "phone": "",
            "website": "https://a4pc.org",
        }]

    out_path = output_dir / f"association_apc_{TODAY}.csv"
    write_csv(rows, out_path, PHARMACY_COLS)
    return rows


# ── 3. NAMS ───────────────────────────────────────────────────────────────────
# NAMS — menopause.org practitioner locator
# These are BHRT prescribers — the physician targeting list for compounding
# pharmacy clients who want to reach menopause/BHRT practitioners.
# REQUIRES_JS: The NAMS locator uses a JS-rendered map/list. Playwright needed.
# Update frequency: relatively static (certified practitioners, annual renewal)

def scrape_nams(output_dir: Path) -> list[dict]:
    """
    NAMS — North American Menopause Society certified practitioners.
    URL: https://www.menopause.org/for-women/menopause-practitioner-locator
    Extracts: name, specialty, city, state, practice_name

    REQUIRES_JS: The practitioner locator is a dynamic map-based tool.
    Recommended approach: Playwright to trigger a ZIP/radius search and
    paginate through results, OR use the Apify actor for healthcare directory
    scraping (configure with menopause.org URL).

    If a JSON API endpoint exists (check Network tab in DevTools for XHR calls
    to api.menopause.org or similar), direct API calls will be faster.
    """
    source = "nams"
    # REQUIRES_JS: use Playwright or Apify scraper
    base_url = "https://www.menopause.org/for-women/menopause-practitioner-locator"
    session = make_session()

    logger.info("[NAMS] Checking for server-side API or HTML fallback…")
    resp = safe_get(session, base_url)

    rows: list[dict] = []

    if resp:
        soup = BeautifulSoup(resp.text, "lxml")
        # Look for any API endpoint hints in page source
        scripts = soup.find_all("script")
        api_endpoints = [
            s.get("src", "") for s in scripts if "api" in s.get("src", "").lower()
        ]
        if api_endpoints:
            logger.info("[NAMS] Potential API endpoints found: %s", api_endpoints)

        # Attempt direct listing parse (works if fallback HTML list exists)
        practitioners = soup.select(
            "div.practitioner, div.provider-card, "
            "li.practitioner-item, article.provider"
        )
        for p in practitioners:
            name_el = p.select_one(".name, h3, h4, .provider-name")
            spec_el = p.select_one(".specialty, .credentials")
            city_el = p.select_one(".city")
            state_el = p.select_one(".state")
            practice_el = p.select_one(".practice, .organization, .clinic")
            rows.append({
                "source": source,
                "name": name_el.get_text(strip=True) if name_el else "",
                "specialty": spec_el.get_text(strip=True) if spec_el else "Menopause/BHRT",
                "city": city_el.get_text(strip=True) if city_el else "",
                "state": state_el.get_text(strip=True) if state_el else "",
                "practice_name": practice_el.get_text(strip=True) if practice_el else "",
            })

    if not rows:
        logger.warning(
            "[NAMS] 0 records — practitioner locator is JS-rendered. "
            "Use Playwright: automate ZIP code search across major metros, "
            "or Apify actor 'healthcare-directory-scraper' pointed at menopause.org."
        )
        rows = [{
            "source": source,
            "name": "REQUIRES_JS — use Playwright or Apify actor",
            "specialty": "Menopause/BHRT Practitioner",
            "city": "",
            "state": "",
            "practice_name": "",
        }]

    out_path = output_dir / f"association_nams_{TODAY}.csv"
    write_csv(rows, out_path, PHYSICIAN_COLS)
    return rows


# ── 4. IFM ────────────────────────────────────────────────────────────────────
# IFM — Institute for Functional Medicine certified practitioners
# Functional medicine MDs — high-value prescriber list for compounding
# pharmacies targeting BHRT, peptides, nutraceuticals.
# Update frequency: static (board certification, annual renewal)

def scrape_ifm(output_dir: Path) -> list[dict]:
    """
    IFM — Institute for Functional Medicine Find a Practitioner.
    URL: https://www.ifm.org/find-a-practitioner/
    Extracts: name, specialty, city, state

    IFM has a search form with zip/distance filters. The results page
    may be HTML or JS-rendered depending on implementation.
    If the directory is behind a POST form, attempt form submission directly.
    """
    source = "ifm"
    base_url = "https://www.ifm.org/find-a-practitioner/"
    session = make_session()

    logger.info("[IFM] Fetching directory…")
    resp = safe_get(session, base_url)
    rows: list[dict] = []

    if resp:
        soup = BeautifulSoup(resp.text, "lxml")

        # IFM may use a Gravity Forms or WP-based directory plugin
        # Look for practitioner listing containers
        practitioners = soup.select(
            "div.practitioner-card, div.ifm-practitioner, "
            "div.member-card, li.practitioner, "
            "div[class*='practitioner'], div[class*='provider']"
        )

        for p in practitioners:
            name_el = p.select_one("h2, h3, h4, .name, .practitioner-name")
            spec_el = p.select_one(".specialty, .credentials, .certification")
            location_el = p.select_one(".location, .city-state, address")
            rows.append({
                "source": source,
                "name": name_el.get_text(strip=True) if name_el else "",
                "specialty": spec_el.get_text(strip=True) if spec_el else "Functional Medicine",
                "city": "",  # Parse from location_el if combined
                "state": location_el.get_text(strip=True) if location_el else "",
                "practice_name": "",
            })

        # Fallback: check for a JSON endpoint (IFM sometimes uses REST)
        if not practitioners:
            # Try the IFM REST API pattern used by directory plugins
            api_url = "https://www.ifm.org/wp-json/ifm/v1/practitioners"
            api_resp = safe_get(session, api_url)
            if api_resp:
                try:
                    data = api_resp.json()
                    if isinstance(data, list):
                        for item in data:
                            rows.append({
                                "source": source,
                                "name": item.get("name", ""),
                                "specialty": item.get("specialty", "Functional Medicine"),
                                "city": item.get("city", ""),
                                "state": item.get("state", ""),
                                "practice_name": item.get("practice", ""),
                            })
                        logger.info("[IFM] JSON API returned %d records", len(rows))
                except ValueError:
                    pass

    if not rows:
        logger.warning(
            "[IFM] 0 records from HTML or JSON. "
            "Use Playwright to automate the search form at https://www.ifm.org/find-a-practitioner/ "
            "— submit searches by state (50 loops) to collect all certified practitioners."
        )
        rows = [{
            "source": source,
            "name": "REQUIRES_JS — use Playwright with state-by-state form submission",
            "specialty": "Functional Medicine",
            "city": "",
            "state": "",
            "practice_name": "",
        }]

    out_path = output_dir / f"association_ifm_{TODAY}.csv"
    write_csv(rows, out_path, PHYSICIAN_COLS)
    return rows


# ── 5. ABOM ───────────────────────────────────────────────────────────────────
# ABOM — American Board of Obesity Medicine
# Board-certified obesity medicine physicians = GLP-1 prescriber list.
# These are the primary referral target for compounding pharmacies offering
# semaglutide/tirzepatide alternatives as the FDA shortage closes.
# Update frequency: relatively static (annual board certification cycle)

def scrape_abom(output_dir: Path) -> list[dict]:
    """
    ABOM — American Board of Obesity Medicine Find a Physician.
    URL: https://abom.org/find-a-physician/
    Extracts: name, city, state

    ABOM has a searchable directory. Check if results are server-side rendered
    or loaded via AJAX. Some ABOM pages return JSON from a WP REST endpoint.
    """
    source = "abom"
    base_url = "https://abom.org/find-a-physician/"
    session = make_session()

    logger.info("[ABOM] Fetching directory…")
    resp = safe_get(session, base_url)
    rows: list[dict] = []

    if resp:
        soup = BeautifulSoup(resp.text, "lxml")

        # ABOM often uses a PHP/WP directory plugin — look for standard patterns
        physicians = soup.select(
            "div.physician-card, div.doctor-listing, "
            "div[class*='physician'], div[class*='member-card'], "
            "li.physician-item, article.physician"
        )

        for p in physicians:
            name_el = p.select_one("h2, h3, h4, .name, .physician-name, strong")
            city_el = p.select_one(".city")
            state_el = p.select_one(".state")
            location_el = p.select_one(".location, address, .city-state")

            city = city_el.get_text(strip=True) if city_el else ""
            state = state_el.get_text(strip=True) if state_el else ""
            if not city and not state and location_el:
                loc_text = location_el.get_text(strip=True)
                # "Dallas, TX" pattern
                parts = loc_text.split(",")
                if len(parts) >= 2:
                    city = parts[0].strip()
                    state = parts[1].strip()

            rows.append({
                "source": source,
                "name": name_el.get_text(strip=True) if name_el else "",
                "specialty": "Obesity Medicine",
                "city": city,
                "state": state,
                "practice_name": "",
            })

        if not physicians:
            # Try ABOM JSON endpoint pattern
            json_urls = [
                "https://abom.org/wp-json/abom/v1/physicians",
                "https://abom.org/wp-json/wp/v2/physicians",
            ]
            for json_url in json_urls:
                json_resp = safe_get(session, json_url)
                if json_resp:
                    try:
                        data = json_resp.json()
                        if isinstance(data, list) and data:
                            for item in data:
                                rows.append({
                                    "source": source,
                                    "name": item.get("name", item.get("title", {}).get("rendered", "")),
                                    "specialty": "Obesity Medicine",
                                    "city": item.get("city", ""),
                                    "state": item.get("state", ""),
                                    "practice_name": item.get("practice", ""),
                                })
                            logger.info("[ABOM] JSON API returned %d records from %s", len(rows), json_url)
                            break
                    except ValueError:
                        pass

    if not rows:
        logger.warning(
            "[ABOM] 0 records — try Playwright or check ABOM's AJAX endpoint "
            "in browser DevTools (Network tab → filter XHR). "
            "Also check https://abom.org/find-a-physician/?state=TX pattern."
        )
        rows = [{
            "source": source,
            "name": "REQUIRES_JS — check ABOM AJAX endpoint or use Playwright",
            "specialty": "Obesity Medicine",
            "city": "",
            "state": "",
            "practice_name": "",
        }]

    out_path = output_dir / f"association_abom_{TODAY}.csv"
    write_csv(rows, out_path, PHYSICIAN_COLS)
    return rows


# ── 6. AASM ───────────────────────────────────────────────────────────────────
# AASM — American Academy of Sleep Medicine accredited sleep labs
# Accredited sleep centers = client targets for the Healthcare Referral Pipeline.
# New accreditations are a signal (see PRD Section 5).
# Update frequency: monthly (new accreditations granted monthly)

def scrape_aasm(output_dir: Path) -> list[dict]:
    """
    AASM — American Academy of Sleep Medicine Find a Facility.
    URL: https://sleepeducation.org/find-a-facility/
    Extracts: facility_name, city, state, phone

    sleepeducation.org is the patient-facing site for AASM. The facility
    locator may use a REST API for the search results — check the Network tab.
    If HTML-rendered, parse the listing directly.
    """
    source = "aasm"
    base_url = "https://sleepeducation.org/find-a-facility/"
    session = make_session()

    logger.info("[AASM] Fetching facility directory…")
    resp = safe_get(session, base_url)
    rows: list[dict] = []

    if resp:
        soup = BeautifulSoup(resp.text, "lxml")

        # Look for facility cards
        facilities = soup.select(
            "div.facility-card, div.sleep-center, "
            "div[class*='facility'], div[class*='center-card'], "
            "li.facility-item, article.facility"
        )

        for f in facilities:
            name_el = f.select_one("h2, h3, h4, .name, .facility-name, strong")
            city_el = f.select_one(".city")
            state_el = f.select_one(".state")
            phone_el = f.select_one(".phone, .tel, a[href^='tel:']")
            location_el = f.select_one(".location, address, .city-state")

            city = city_el.get_text(strip=True) if city_el else ""
            state = state_el.get_text(strip=True) if state_el else ""
            if not city and not state and location_el:
                loc_text = location_el.get_text(strip=True)
                parts = loc_text.split(",")
                if len(parts) >= 2:
                    city = parts[0].strip()
                    state = parts[1].strip()

            phone = ""
            if phone_el:
                phone = phone_el.get_text(strip=True)
                if phone.startswith("tel:"):
                    phone = phone[4:]

            rows.append({
                "source": source,
                "facility_name": name_el.get_text(strip=True) if name_el else "",
                "city": city,
                "state": state,
                "phone": phone,
            })

        if not facilities:
            # Try the AASM/sleepeducation.org REST API — it often exposes a
            # facility search endpoint
            api_candidates = [
                "https://sleepeducation.org/wp-json/aasm/v1/facilities",
                "https://sleepeducation.org/wp-json/wp/v2/facilities",
                "https://sleepeducation.org/api/facilities",
            ]
            for api_url in api_candidates:
                api_resp = safe_get(session, api_url)
                if api_resp:
                    try:
                        data = api_resp.json()
                        if isinstance(data, list) and data:
                            for item in data:
                                rows.append({
                                    "source": source,
                                    "facility_name": item.get("name", item.get("title", {}).get("rendered", "")),
                                    "city": item.get("city", ""),
                                    "state": item.get("state", ""),
                                    "phone": item.get("phone", ""),
                                })
                            logger.info("[AASM] JSON API returned %d records from %s", len(rows), api_url)
                            break
                    except ValueError:
                        pass

    if not rows:
        logger.warning(
            "[AASM] 0 records — check sleepeducation.org Network tab for XHR "
            "facility search endpoint. Alternatively, use Playwright to automate "
            "ZIP/state searches. New AASM accreditations are a priority signal "
            "(monthly update — wire to ECAS signal pipeline)."
        )
        rows = [{
            "source": source,
            "facility_name": "REQUIRES_JS — check AASM XHR endpoint or use Playwright",
            "city": "",
            "state": "",
            "phone": "",
        }]

    out_path = output_dir / f"association_aasm_{TODAY}.csv"
    write_csv(rows, out_path, FACILITY_COLS)
    return rows


# ── Orchestrator ──────────────────────────────────────────────────────────────

ALL_SCRAPERS = {
    "pcab": scrape_pcab,
    "apc": scrape_apc,
    "nams": scrape_nams,
    "ifm": scrape_ifm,
    "abom": scrape_abom,
    "aasm": scrape_aasm,
}


def run_scrapers(
    associations: list[str],
    output_dir: Path,
) -> dict[str, list[dict]]:
    """
    Run selected scrapers concurrently (up to 6 workers).
    Returns dict of {association_name: rows}.
    """
    results: dict[str, list[dict]] = {}
    failed: list[str] = []

    logger.info("Running %d scrapers in parallel: %s", len(associations), ", ".join(associations))

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(ALL_SCRAPERS[name], output_dir): name
            for name in associations
            if name in ALL_SCRAPERS
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                rows = future.result()
                results[name] = rows
                logger.info("[%s] Completed — %d records", name.upper(), len(rows))
            except Exception as exc:
                logger.error("[%s] Scraper raised exception: %s", name.upper(), exc)
                failed.append(name)
                results[name] = []

    if failed:
        logger.warning("Failed scrapers: %s", ", ".join(failed))

    return results


def write_combined(results: dict[str, list[dict]], output_dir: Path) -> Path:
    """
    Merge all results into a single combined CSV with unified columns.
    Missing columns are filled with empty strings.
    """
    combined_cols = [
        "source", "name", "pharmacy_name", "facility_name",
        "specialty", "practice_name",
        "city", "state", "phone", "website",
    ]
    all_rows: list[dict] = []
    for rows in results.values():
        for row in rows:
            # Normalize: ensure all combined columns present
            normalized = {col: row.get(col, "") for col in combined_cols}
            all_rows.append(normalized)

    out_path = output_dir / f"associations_combined_{TODAY}.csv"
    write_csv(all_rows, out_path, combined_cols)
    return out_path


def print_stats(results: dict[str, list[dict]]) -> None:
    """Print per-association record counts and total."""
    print("\n" + "=" * 50)
    print("ASSOCIATION DIRECTORY SCRAPER — RESULTS")
    print("=" * 50)
    total = 0
    for name, rows in sorted(results.items()):
        real_rows = [r for r in rows if "REQUIRES" not in str(list(r.values()))]
        flag_rows = len(rows) - len(real_rows)
        status = "REQUIRES_JS" if flag_rows > 0 and not real_rows else "OK"
        count = len(real_rows)
        total += count
        print(f"  {name.upper():8s}  {count:>5d} records  [{status}]")
    print("-" * 50)
    print(f"  {'TOTAL':8s}  {total:>5d} records")
    print("=" * 50 + "\n")


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape association directories for healthcare referral pipeline contacts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python association_directory_scraper.py
  python association_directory_scraper.py --associations pcab,apc
  python association_directory_scraper.py --associations abom,nams --output-dir /tmp/assoc

Associations: pcab, apc, nams, ifm, abom, aasm
        """,
    )
    parser.add_argument(
        "--associations",
        type=str,
        default=",".join(ALL_SCRAPERS.keys()),
        help="Comma-separated list of associations to scrape (default: all)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(Path(__file__).parent / "output"),
        help="Directory to write CSV output files",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    associations = [a.strip().lower() for a in args.associations.split(",") if a.strip()]
    output_dir = Path(args.output_dir)

    unknown = [a for a in associations if a not in ALL_SCRAPERS]
    if unknown:
        logger.error("Unknown associations: %s. Valid: %s", unknown, list(ALL_SCRAPERS.keys()))
        raise SystemExit(1)

    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Output directory: %s", output_dir.resolve())

    results = run_scrapers(associations, output_dir)
    combined_path = write_combined(results, output_dir)
    print_stats(results)
    logger.info("Combined output: %s", combined_path)


if __name__ == "__main__":
    main()


# =============================================================================
# PLAYWRIGHT REFERENCE — Use for JS-rendered sites (PCAB, NAMS, IFM)
# =============================================================================
#
# Install: pip install playwright && playwright install chromium
#
# async def playwright_pcab_scraper(output_dir: Path) -> list[dict]:
#     """Playwright-based scraper for PCAB (JS-rendered React SPA)."""
#     from playwright.async_api import async_playwright
#     rows = []
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=True)
#         page = await browser.new_page()
#         await page.goto("https://pcab.org/find-a-pharmacy", wait_until="networkidle")
#         # Wait for pharmacy cards to render
#         await page.wait_for_selector("div.pharmacy-card, tr.pharmacy-row", timeout=15000)
#         cards = await page.query_selector_all("div.pharmacy-card")
#         for card in cards:
#             name = await card.query_selector(".pharmacy-name")
#             city = await card.query_selector(".city")
#             state = await card.query_selector(".state")
#             phone = await card.query_selector(".phone")
#             website = await card.query_selector("a")
#             rows.append({
#                 "source": "pcab",
#                 "pharmacy_name": await name.inner_text() if name else "",
#                 "city": await city.inner_text() if city else "",
#                 "state": await state.inner_text() if state else "",
#                 "phone": await phone.inner_text() if phone else "",
#                 "website": await website.get_attribute("href") if website else "",
#             })
#         await browser.close()
#     return rows
#
# APIFY RECOMMENDATIONS:
#   - PCAB: Use Apify "Web Scraper" actor with Start URL = pcab.org/find-a-pharmacy
#     Configure to wait for React render, then extract .pharmacy-card elements
#   - NAMS: Same approach — Apify Web Scraper, automate ZIP search across metros
#   - IFM: Apify "Cheerio Scraper" if server-side rendered, "Web Scraper" if JS
#
# After Playwright/Apify produces CSVs, feed output directly into Clay:
#   Clay column: "Company Name" ← pharmacy_name
#   Clay column: "Location" ← city + state
#   Waterfall: Findymail → Hunter → Apollo email enrichment
# =============================================================================
