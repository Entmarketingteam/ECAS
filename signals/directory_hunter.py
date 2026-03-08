"""
signals/directory_hunter.py — Multi-source ICP directory scraper.

Finds mid-tier EPC contractors ($20M-$300M) from:
  1. SAM.gov Entity API — federal contractors registered under EPC NAICS codes
  2. MapYourShow — conference exhibitor lists (POWERGEN, DistribuTECH, IEEE T&D)
  3. State electrical licensing boards (VA, TX, NC, GA, FL, MD, PA)

These channels reach companies that:
  - Are actively pursuing government/utility contracts (SAM.gov)
  - Spend money to exhibit at ICP-relevant conferences (MapYourShow)
  - Are licensed to operate in our target states (licensing boards)

Flow:
  1. Hit each source API/page
  2. Normalize to {name, website, state, source, naics, notes}
  3. Deduplicate by normalized company name
  4. Upsert into Airtable projects (sector=Discovery, stage=Identified)
  5. Return summary dict for scheduler logging

Usage:
    python3 signals/directory_hunter.py --dry-run
    python3 signals/directory_hunter.py --limit 100
    python3 signals/directory_hunter.py              # full run, all sources
"""

import argparse
import logging
import re
import sys
import time
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLES

logger = logging.getLogger(__name__)

# ── NAICS codes for EPC-adjacent federal contractors ───────────────────────────

EPC_NAICS = [
    "237130",   # Power and Communication Line and Related Structures Construction
    "238210",   # Electrical Contractors and Other Wiring Installation Contractors
    "237110",   # Water and Sewer Line and Related Structures Construction
    "236220",   # Commercial and Institutional Building Construction
    "237990",   # Other Heavy and Civil Engineering Construction
    "238990",   # All Other Specialty Trade Contractors
    "541330",   # Engineering Services
    "541620",   # Environmental Consulting Services
]

# ── Target states (ECAS ICP geography) ────────────────────────────────────────

TARGET_STATES = ["VA", "TX", "NC", "GA", "FL", "MD", "PA", "OH", "TN", "SC", "AL", "LA"]

# ── Conference exhibitor targets ───────────────────────────────────────────────

# MapYourShow powers exhibitor directories for major energy/grid conferences.
# The search endpoint returns JSON exhibitors with name, booth, description, website.
MAPYOURSHOW_EVENTS = [
    {
        "name": "POWERGEN International",
        "show_id": "PGI25",
        "sector": "Power & Grid Infrastructure",
        "url": "https://www.mapyourshow.com/8_0/exhview/index.cfm",
        "search_url": "https://www.mapyourshow.com/8_0/exhview/index.cfm?exhid=&hallid=&pagenumber=1&searchtype=keyword&searchtext=&show=PGI25",
    },
    {
        "name": "DistribuTECH",
        "show_id": "DTI25",
        "sector": "Power & Grid Infrastructure",
        "url": "https://www.mapyourshow.com/8_0/exhview/index.cfm",
        "search_url": "https://www.mapyourshow.com/8_0/exhview/index.cfm?exhid=&hallid=&pagenumber=1&searchtype=keyword&searchtext=&show=DTI25",
    },
    {
        "name": "IEEE PES T&D Conference",
        "show_id": "IEEEPESTD25",
        "sector": "Power & Grid Infrastructure",
        "url": "https://www.mapyourshow.com/8_0/exhview/index.cfm",
        "search_url": "https://www.mapyourshow.com/8_0/exhview/index.cfm?exhid=&hallid=&pagenumber=1&searchtype=keyword&searchtext=&show=IEEEPESTD25",
    },
    {
        "name": "NECA Annual Convention",
        "show_id": "NECA25",
        "sector": "Power & Grid Infrastructure",
        "url": "https://www.mapyourshow.com/8_0/exhview/index.cfm",
        "search_url": "https://www.mapyourshow.com/8_0/exhview/index.cfm?exhid=&hallid=&pagenumber=1&searchtype=keyword&searchtext=&show=NECA25",
    },
]

# Keywords that indicate EPC-adjacent exhibitors worth tracking
EPC_EXHIBITOR_KEYWORDS = [
    "engineering", "construction", "contractor", "electrical", "mechanical",
    "infrastructure", "systems", "integration", "installation", "substation",
    "transmission", "distribution", "solar", "wind", "generation", "grid",
    "utility", "power", "energy", "services", "solutions", "epc",
]

SKIP_EXHIBITOR_KEYWORDS = [
    "software only", "saas", "staffing", "insurance", "legal", "accounting",
    "banking", "media", "publishing", "food", "catering",
]

# ── SAM.gov Entity API ─────────────────────────────────────────────────────────

SAM_ENTITY_URL = "https://api.sam.gov/entity-information/v3/entities"


def fetch_sam_entities(naics: str, state: str = None, limit: int = 100) -> list[dict]:
    """
    Query SAM.gov Entity Management API for active federal contractors.
    Free API — no key required for basic entity search.

    Returns normalized list of {name, website, state, naics, city, source, notes}
    """
    params = {
        "purposeOfRegistrationCode": "Z2",   # All Awards — active contractors
        "primaryNaics": naics,
        "entityEFTIndicator": "",
        "includeSections": "entityRegistration,coreData",
        "format": "json",
        "size": min(limit, 100),
        "page": 0,
    }
    if state:
        params["stateOrProvinceOfPlaceOfPerformanceCode"] = state

    try:
        resp = requests.get(SAM_ENTITY_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        entities = data.get("entityData", [])

        results = []
        for entity in entities:
            try:
                reg = entity.get("entityRegistration", {})
                core = entity.get("coreData", {})
                addr = core.get("physicalAddress", {})

                name = reg.get("legalBusinessName", "").strip()
                if not name:
                    continue

                # Filter to target states
                entity_state = addr.get("stateOrProvinceCode", "")
                if TARGET_STATES and entity_state not in TARGET_STATES:
                    continue

                results.append({
                    "name": name,
                    "website": core.get("electronicBusinessPOC", {}).get("electronicBusinessFirstLastName", ""),
                    "state": entity_state,
                    "city": addr.get("city", ""),
                    "naics": naics,
                    "source": f"SAM.gov (NAICS {naics})",
                    "notes": (
                        f"Active federal contractor. NAICS {naics}. "
                        f"SAM.gov registration — actively pursuing government contracts."
                    ),
                    "discovery_channel": "sam_gov",
                })
            except Exception:
                continue

        logger.info(f"[SAM.gov] NAICS {naics}{f' / {state}' if state else ''}: {len(results)} results")
        return results

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            logger.warning("[SAM.gov] Rate limited — sleeping 60s")
            time.sleep(60)
        else:
            logger.warning(f"[SAM.gov] HTTP error for NAICS {naics}: {e}")
        return []
    except Exception as e:
        logger.warning(f"[SAM.gov] Error for NAICS {naics}: {e}")
        return []


def run_sam_hunt(limit_per_naics: int = 100) -> list[dict]:
    """Pull EPC contractors from SAM.gov across all target NAICS codes."""
    all_results = []
    seen_names = set()

    for naics in EPC_NAICS[:6]:  # Top 6 most relevant NAICS
        results = fetch_sam_entities(naics, limit=limit_per_naics)
        for r in results:
            normalized = _normalize_name(r["name"])
            if normalized not in seen_names:
                seen_names.add(normalized)
                all_results.append(r)
        time.sleep(1)  # SAM.gov rate limit

    logger.info(f"[SAM.gov] Total unique companies: {len(all_results)}")
    return all_results


# ── MapYourShow Conference Exhibitor Scraper ───────────────────────────────────

def scrape_mapyourshow_event(event: dict) -> list[dict]:
    """
    Scrape exhibitor list from MapYourShow for a given conference.
    MapYourShow uses a paginated HTML directory — we parse company names,
    descriptions, and websites from exhibitor cards.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.mapyourshow.com/",
    }

    results = []
    page = 1
    max_pages = 20  # Safety ceiling — most shows have 5-15 pages

    while page <= max_pages:
        # Build paginated URL
        url = event["search_url"].replace("pagenumber=1", f"pagenumber={page}")

        try:
            resp = requests.get(url, headers=headers, timeout=20)
            if resp.status_code == 404 or resp.status_code >= 500:
                break
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # MapYourShow exhibitor cards use various class patterns
            exhibitors = (
                soup.find_all("div", class_=re.compile(r"exh[-_]?card|exhibitor[-_]?card|company[-_]?card")) or
                soup.find_all("div", class_=re.compile(r"exhListItem|exhibitor-list-item")) or
                soup.find_all("li", class_=re.compile(r"exh|exhibitor"))
            )

            if not exhibitors:
                # Try generic h3/h2 company name pattern
                exhibitors = soup.find_all(["h3", "h2"], class_=re.compile(r"exh|company|exhibitor"))

            if not exhibitors:
                logger.debug(f"[MapYourShow] No exhibitors found on page {page} for {event['name']}")
                break

            found_on_page = 0
            for card in exhibitors:
                name = _extract_text(card.find(["h3", "h2", "h4", "strong"]) or card)
                if not name or len(name) < 3:
                    continue

                description = _extract_text(card.find("p") or card.find(class_=re.compile(r"desc|bio|about")))
                website_el = card.find("a", href=re.compile(r"http"))
                website = website_el["href"] if website_el else ""

                # EPC relevance filter
                combined = f"{name} {description}".lower()
                if not any(kw in combined for kw in EPC_EXHIBITOR_KEYWORDS):
                    continue
                if any(kw in combined for kw in SKIP_EXHIBITOR_KEYWORDS):
                    continue

                results.append({
                    "name": name.strip(),
                    "website": website,
                    "state": "",
                    "city": "",
                    "naics": "",
                    "source": f"MapYourShow — {event['name']}",
                    "sector": event.get("sector", "Power & Grid Infrastructure"),
                    "notes": (
                        f"Conference exhibitor at {event['name']}. "
                        f"Actively paying to be in front of utility buyers. "
                        f"{('Description: ' + description[:200]) if description else ''}"
                    ),
                    "discovery_channel": "conference_exhibitor",
                })
                found_on_page += 1

            logger.debug(f"[MapYourShow] {event['name']} page {page}: {found_on_page} EPC-adjacent exhibitors")

            if found_on_page == 0:
                break

            page += 1
            time.sleep(1.5)  # Polite crawl delay

        except requests.exceptions.ConnectionError:
            logger.warning(f"[MapYourShow] Connection failed for {event['name']} page {page}")
            break
        except Exception as e:
            logger.warning(f"[MapYourShow] Error on {event['name']} page {page}: {e}")
            break

    logger.info(f"[MapYourShow] {event['name']}: {len(results)} EPC-adjacent exhibitors")
    return results


def run_conference_hunt() -> list[dict]:
    """Scrape all configured conference exhibitor lists."""
    all_results = []
    seen_names = set()

    for event in MAPYOURSHOW_EVENTS:
        results = scrape_mapyourshow_event(event)
        for r in results:
            normalized = _normalize_name(r["name"])
            if normalized not in seen_names:
                seen_names.add(normalized)
                all_results.append(r)

    logger.info(f"[Conference Hunt] Total unique exhibitors: {len(all_results)}")
    return all_results


# ── ENR Top 400/600 Specialty Contractors ─────────────────────────────────────

def fetch_enr_specialty_contractors() -> list[dict]:
    """
    Scrape ENR Top 400/600 Specialty Contractors list.
    ENR publishes annual rankings — these are exactly our ICP companies.
    Target: electrical/mechanical/power/industrial specialty contractors.

    URL pattern: https://www.enr.com/toplists/
    Note: ENR may require login for full data. We scrape what's publicly visible.
    """
    urls = [
        "https://www.enr.com/toplists/4-Top-600-Specialty-Contractors",
        "https://www.enr.com/toplists/10-Top-Electrical-Contractors",
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
    }

    results = []

    for url in urls:
        try:
            resp = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
            if resp.status_code != 200:
                logger.warning(f"[ENR] HTTP {resp.status_code} for {url}")
                continue

            soup = BeautifulSoup(resp.text, "html.parser")

            # ENR list items — contractor names in table rows or list items
            rows = (
                soup.find_all("tr", class_=re.compile(r"list|row|contractor")) or
                soup.find_all("td", class_=re.compile(r"company|name")) or
                soup.find_all("div", class_=re.compile(r"list-item|company"))
            )

            for row in rows:
                name_el = row.find(["a", "strong", "td", "span"], string=re.compile(r"[A-Za-z]{3,}"))
                if not name_el:
                    continue
                name = name_el.get_text(strip=True)
                if len(name) < 4 or name.isdigit():
                    continue

                results.append({
                    "name": name,
                    "website": "",
                    "state": "",
                    "city": "",
                    "naics": "238210",
                    "source": "ENR Top Specialty Contractors",
                    "sector": "Power & Grid Infrastructure",
                    "notes": "ENR Top 400/600 Specialty Contractor — definitive ICP list. Confirm revenue before outreach.",
                    "discovery_channel": "enr_ranking",
                })

            logger.info(f"[ENR] {url}: {len(results)} contractors")
            time.sleep(2)

        except Exception as e:
            logger.warning(f"[ENR] Error fetching {url}: {e}")

    return results


# ── Airtable upsert ────────────────────────────────────────────────────────────

def _determine_sector(company: dict) -> str:
    """Infer sector from company data."""
    return company.get("sector", "Power & Grid Infrastructure")


def upsert_to_airtable(companies: list[dict], dry_run: bool = False) -> dict:
    """
    Upsert companies into Airtable projects table.
    Checks for existing records first to avoid duplicates.
    """
    if not AIRTABLE_API_KEY or not AIRTABLE_BASE_ID:
        logger.warning("[Airtable] No credentials — skipping upsert")
        return {"created": 0, "skipped": 0, "errors": 0}

    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLES['projects']}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json",
    }

    results = {"created": 0, "skipped": 0, "errors": 0}

    for company in companies:
        name = company["name"]

        if dry_run:
            print(f"  [DRY RUN] {name} | {company.get('source', '')} | {company.get('state', '')}")
            results["created"] += 1
            continue

        # Check existence
        try:
            check_resp = requests.get(
                url,
                headers={"Authorization": f"Bearer {AIRTABLE_API_KEY}"},
                params={"filterByFormula": f"{{owner_company}}='{name.replace(chr(39), '')}'"},
                timeout=15,
            )
            check_resp.raise_for_status()
            if check_resp.json().get("records"):
                results["skipped"] += 1
                continue
        except Exception:
            pass

        sector = _determine_sector(company)
        notes = company.get("notes", "")
        if company.get("city") and company.get("state"):
            notes += f"\nLocation: {company['city']}, {company['state']}"
        if company.get("website"):
            notes += f"\nWebsite: {company['website']}"
        if company.get("naics"):
            notes += f"\nNAICS: {company['naics']}"

        fields = {
            "owner_company": name,
            "sector": sector,
            "stage": "Identified",
            "priority": "Medium",
            "icp_fit": "Unknown",
            "notes": notes,
            "signal_type": company.get("discovery_channel", "directory"),
            "confidence_score": 45,  # Directory source = moderate signal, needs enrichment
        }

        try:
            resp = requests.post(url, headers=headers, json={"fields": fields}, timeout=15)
            resp.raise_for_status()
            results["created"] += 1
            logger.info(f"[Airtable] Created: {name}")
        except Exception as e:
            logger.error(f"[Airtable] Failed for {name}: {e}")
            results["errors"] += 1

        time.sleep(0.2)

    return results


# ── Helpers ────────────────────────────────────────────────────────────────────

def _normalize_name(name: str) -> str:
    """Normalize company name for deduplication."""
    name = name.lower().strip()
    name = re.sub(r"\b(inc|llc|corp|ltd|co|company|incorporated|limited)\b\.?", "", name)
    name = re.sub(r"[^\w\s]", "", name)
    return re.sub(r"\s+", " ", name).strip()


def _extract_text(el) -> str:
    """Safely extract text from a BeautifulSoup element."""
    if el is None:
        return ""
    return el.get_text(separator=" ", strip=True)


# ── Main ───────────────────────────────────────────────────────────────────────

def run_directory_hunt(dry_run: bool = False, limit: int = None, sources: list = None) -> dict:
    """
    Run full directory hunt across all sources.
    Deduplicates, then upserts to Airtable.

    Args:
        dry_run: Print results without writing to Airtable
        limit: Cap total companies to process
        sources: List of sources to run ('sam_gov', 'conferences', 'enr'). None = all.

    Returns:
        Summary dict with counts per source and total created/skipped/errors
    """
    if sources is None:
        sources = ["sam_gov", "conferences", "enr"]

    all_companies = []
    seen_names = set()
    source_counts = {}

    def _add_companies(new_companies: list[dict], source_key: str):
        added = 0
        for c in new_companies:
            normalized = _normalize_name(c["name"])
            if normalized and normalized not in seen_names:
                seen_names.add(normalized)
                all_companies.append(c)
                added += 1
        source_counts[source_key] = added
        logger.info(f"[DirectoryHunt] {source_key}: {added} unique companies added")

    if "sam_gov" in sources:
        logger.info("[DirectoryHunt] Running SAM.gov hunt...")
        sam_results = run_sam_hunt(limit_per_naics=50)
        _add_companies(sam_results, "sam_gov")

    if "conferences" in sources:
        logger.info("[DirectoryHunt] Running conference exhibitor hunt...")
        conf_results = run_conference_hunt()
        _add_companies(conf_results, "conferences")

    if "enr" in sources:
        logger.info("[DirectoryHunt] Running ENR specialty contractor hunt...")
        enr_results = fetch_enr_specialty_contractors()
        _add_companies(enr_results, "enr")

    if limit:
        all_companies = all_companies[:limit]

    logger.info(f"[DirectoryHunt] Total unique companies: {len(all_companies)}")

    if dry_run:
        print(f"\nDRY RUN — {len(all_companies)} companies found:\n")
        for c in all_companies:
            print(f"  {c['name']} | {c.get('source', '')} | {c.get('state', '')}")
        return {
            "total": len(all_companies),
            "source_counts": source_counts,
            "created": 0,
            "skipped": 0,
            "errors": 0,
        }

    airtable_result = upsert_to_airtable(all_companies, dry_run=False)

    summary = {
        "total": len(all_companies),
        "source_counts": source_counts,
        **airtable_result,
    }
    logger.info(f"[DirectoryHunt] Done: {summary}")
    return summary


if __name__ == "__main__":
    import logging as _logging
    _logging.basicConfig(level=_logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="ECAS Directory Hunter — multi-source ICP scraper")
    parser.add_argument("--dry-run", action="store_true", help="Print results without writing to Airtable")
    parser.add_argument("--limit", type=int, default=None, help="Max companies to process")
    parser.add_argument("--sources", nargs="+", choices=["sam_gov", "conferences", "enr"],
                        default=None, help="Sources to run (default: all)")
    args = parser.parse_args()

    result = run_directory_hunt(dry_run=args.dry_run, limit=args.limit, sources=args.sources)
    print(f"\nResult: {result}")
