"""
contractor/signals/association_scraper.py — Trade association member directory scrapers.

Sources:
- NRCA (National Roofing Contractors Association) — JS-rendered, scraped via Firecrawl
- NPMA (National Pest Management Association) — JS-rendered, scraped via Firecrawl
- ISSA (Worldwide Cleaning Industry Association) — HTML paginated, scraped direct

Schedule: Weekly (Sunday 3am) — member lists change slowly.
Signal type: industry_association_member (50 pts — warm floor, qualifies for direct outreach)
"""
import os
import re
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from contractor.signals._airtable import push_signals, signal_exists

logger = logging.getLogger(__name__)

FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")
FIRECRAWL_BASE = "https://api.firecrawl.dev/v1"

# States to scrape — matches geo_focus across all three verticals
TARGET_STATES = ["TX", "FL", "GA", "NC", "VA", "PA", "OH", "TN", "CO", "KS", "OK"]

NRCA_SEARCH_URL = "https://www.nrca.net/roofing/find-a-contractor?state={state}"
NPMA_SEARCH_URL = "https://www.npmapestworld.org/find-a-pro?state={state}"
ISSA_DIR_URL = "https://access.issa.com/dir?page={page}&country=US"


# ─── Firecrawl helper ─────────────────────────────────────────────────────────

def _firecrawl_scrape(url: str) -> str:
    """Scrape a URL via Firecrawl and return markdown content."""
    resp = requests.post(
        f"{FIRECRAWL_BASE}/scrape",
        headers={"Authorization": f"Bearer {FIRECRAWL_API_KEY}", "Content-Type": "application/json"},
        json={"url": url, "formats": ["markdown"], "waitFor": 2000},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json().get("data", {}).get("markdown", "")


def _extract_domain(text: str) -> str:
    """Extract a domain from a markdown link like [example.com](https://example.com)."""
    match = re.search(r'\[([^\]]+)\]\(https?://([^/)]+)', text)
    if match:
        return match.group(2).lower().strip()
    # Bare URL
    match = re.search(r'https?://([^/\s)]+)', text)
    return match.group(1).lower().strip() if match else ""


def _make_signal(company_name: str, domain: str, vertical: str, source: str, extra: dict = None) -> dict:
    return {
        "company_name": company_name.strip(),
        "company_domain": domain.lower().strip(),
        "vertical": vertical,
        "vertical_type": "contractor",
        "signal_type": "industry_association_member",
        "detected_at": datetime.utcnow().isoformat(),
        "source": source,
        "processed": False,
        "raw_data_json": extra or {},
    }


# ─── NRCA scraper ─────────────────────────────────────────────────────────────

def scrape_nrca_state(state: str) -> list[dict]:
    """Scrape one state's NRCA contractor listings via Firecrawl."""
    url = NRCA_SEARCH_URL.format(state=state)
    try:
        markdown = _firecrawl_scrape(url)
    except Exception as e:
        logger.warning("NRCA Firecrawl failed for state %s: %s", state, e)
        return []

    signals = []
    # Parse company blocks: look for bold company names (**Company Name**)
    # Only match bold text — headings (##) are section titles, not company entries
    lines = markdown.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        name_match = re.match(r'^\*\*(.+?)\*\*\s*$', line)
        if name_match:
            company_name = name_match.group(1).strip()
            # Look ahead up to 5 lines for a website
            domain = ""
            for j in range(i + 1, min(i + 6, len(lines))):
                if "http" in lines[j] or ".com" in lines[j]:
                    domain = _extract_domain(lines[j])
                    break

            if company_name and len(company_name) > 3:
                if not signal_exists(domain, "industry_association_member"):
                    signals.append(_make_signal(
                        company_name, domain, "Commercial Roofing", "NRCA",
                        {"state": state}
                    ))
        i += 1

    logger.info("NRCA %s: found %d new members", state, len(signals))
    return signals


# ─── NPMA scraper ─────────────────────────────────────────────────────────────

def scrape_npma_state(state: str) -> list[dict]:
    """Scrape one state's NPMA pest control listings via Firecrawl."""
    url = NPMA_SEARCH_URL.format(state=state)
    try:
        markdown = _firecrawl_scrape(url)
    except Exception as e:
        logger.warning("NPMA Firecrawl failed for state %s: %s", state, e)
        return []

    signals = []
    # Only match bold text — headings (##) are section titles, not company entries
    lines = markdown.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        name_match = re.match(r'^\*\*(.+?)\*\*\s*$', line)
        if name_match:
            company_name = name_match.group(1).strip()
            domain = ""
            for j in range(i + 1, min(i + 6, len(lines))):
                if "http" in lines[j] or ".com" in lines[j]:
                    domain = _extract_domain(lines[j])
                    break

            if company_name and len(company_name) > 3:
                if not signal_exists(domain, "industry_association_member"):
                    signals.append(_make_signal(
                        company_name, domain, "Pest Control", "NPMA",
                        {"state": state}
                    ))
        i += 1

    logger.info("NPMA %s: found %d new members", state, len(signals))
    return signals


# ─── ISSA scraper ─────────────────────────────────────────────────────────────

def scrape_issa_page(page: int) -> tuple[list[dict], bool]:
    """
    Scrape one page of ISSA member directory.
    Returns (signals, has_next_page).
    """
    url = ISSA_DIR_URL.format(page=page)
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; ECASBot/1.0)"},
            timeout=30,
        )
        resp.raise_for_status()
    except Exception as e:
        logger.warning("ISSA page %d failed: %s", page, e)
        return [], False

    soup = BeautifulSoup(resp.text, "lxml")
    signals = []

    for member in soup.select(".member, .member-listing .member, [class*='member-item']"):
        name_el = member.select_one(".member-name, h3, h2, [class*='name']")
        if not name_el:
            continue
        company_name = name_el.get_text(strip=True)

        website_el = member.select_one("a.member-website, a[href*='http']:not([href*='issa.com'])")
        domain = ""
        if website_el and website_el.get("href"):
            href = website_el["href"]
            domain_match = re.search(r'https?://([^/]+)', href)
            domain = domain_match.group(1).lower() if domain_match else ""

        state_el = member.select_one(".member-state, [class*='state']")
        state = state_el.get_text(strip=True) if state_el else ""

        if company_name and len(company_name) > 3:
            if not signal_exists(domain, "industry_association_member"):
                signals.append(_make_signal(
                    company_name, domain, "Commercial Janitorial", "ISSA",
                    {"state": state, "page": page}
                ))

    has_next = bool(soup.select_one("a.next-page, a[rel='next'], .pagination .next"))
    logger.info("ISSA page %d: found %d new members, has_next=%s", page, len(signals), has_next)
    return signals, has_next


# ─── Main entry point ─────────────────────────────────────────────────────────

def run_association_scraper() -> int:
    """
    APScheduler entry point. Scrapes all three associations across target states.
    Runs NRCA and NPMA in parallel (one task per state), ISSA paginated.
    Returns total signals pushed to Airtable.
    """
    all_signals = []

    # NRCA + NPMA: parallel by state
    with ThreadPoolExecutor(max_workers=4) as executor:
        nrca_futures = {executor.submit(scrape_nrca_state, s): ("NRCA", s) for s in TARGET_STATES}
        npma_futures = {executor.submit(scrape_npma_state, s): ("NPMA", s) for s in TARGET_STATES}

        for future in as_completed({**nrca_futures, **npma_futures}):
            try:
                all_signals.extend(future.result())
            except Exception as e:
                logger.error("Association scrape task failed: %s", e)

    # ISSA: paginated
    page = 1
    while True:
        signals, has_next = scrape_issa_page(page)
        all_signals.extend(signals)
        if not has_next or page > 50:  # Safety cap: 50 pages max
            break
        page += 1

    pushed = push_signals(all_signals)
    logger.info("Association scraper done: %d signals pushed", pushed)
    return pushed
