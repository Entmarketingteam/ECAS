"""Universal scraper router: routes URLs to Firecrawl/Airtop/Browserbase."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from urllib.parse import urlparse

import requests

from discovery.directory_finder import DirectoryCandidate, ScraperType

logger = logging.getLogger(__name__)


@dataclass
class ScrapedCompany:
    name: str
    website: str
    source_url: str
    extras: dict = field(default_factory=dict)


def _normalize_host(url_or_host: str) -> str:
    if not url_or_host:
        return ""
    s = url_or_host.strip().lower()
    if not s.startswith("http"):
        s = "https://" + s
    host = (urlparse(s).hostname or "").lower()
    return host.removeprefix("www.")


def _firecrawl_scrape(url: str) -> list[ScrapedCompany]:
    """Scrape a static directory page via Firecrawl API."""
    key = os.environ.get("FIRECRAWL_API_KEY", "")
    if not key:
        raise RuntimeError("FIRECRAWL_API_KEY not set")
    resp = requests.post(
        "https://api.firecrawl.dev/v1/scrape",
        headers={"Authorization": f"Bearer {key}"},
        json={
            "url": url,
            "formats": ["extract"],
            "extract": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "companies": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "website": {"type": "string"},
                                },
                                "required": ["name"],
                            },
                        },
                    },
                },
                "prompt": "Extract all companies/vendors/exhibitors listed on this page.",
            },
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    extracted = (data.get("data", {}) or {}).get("extract", {}) or {}
    companies = extracted.get("companies", []) or []
    return [
        ScrapedCompany(
            name=c["name"],
            website=c.get("website", ""),
            source_url=url,
        )
        for c in companies
        if c.get("name")
    ]


def _airtop_scrape(url: str) -> list[ScrapedCompany]:
    """Scrape a gated directory via Airtop browser session."""
    key = os.environ.get("AIRTOP_API_KEY", "")
    if not key:
        logger.warning("[Scraper] AIRTOP_API_KEY not set — skipping %s", url)
        return []
    resp = requests.post(
        "https://api.airtop.ai/api/v1/sessions/scrape",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "url": url,
            "prompt": "Extract company names and websites from all visible listings.",
        },
        timeout=180,
    )
    if resp.status_code >= 400:
        logger.warning("[Scraper] Airtop %s: %s", url, resp.status_code)
        return []
    data = resp.json()
    return [
        ScrapedCompany(
            name=c["name"],
            website=c.get("website", ""),
            source_url=url,
        )
        for c in data.get("companies", [])
        if c.get("name")
    ]


def _browserbase_scrape(url: str) -> list[ScrapedCompany]:
    """Scrape a JS-heavy SPA via Browserbase session."""
    key = os.environ.get("BROWSERBASE_API_KEY", "")
    project = os.environ.get("BROWSERBASE_PROJECT_ID", "")
    if not (key and project):
        logger.warning("[Scraper] Browserbase creds missing — skipping %s", url)
        return []
    resp = requests.post(
        "https://api.browserbase.com/v1/scrape",
        headers={"X-BB-API-Key": key},
        json={"projectId": project, "url": url},
        timeout=180,
    )
    if resp.status_code >= 400:
        logger.warning("[Scraper] Browserbase %s: %s", url, resp.status_code)
        return []
    data = resp.json()
    return [
        ScrapedCompany(
            name=c["name"],
            website=c.get("website", ""),
            source_url=url,
        )
        for c in data.get("companies", [])
        if c.get("name")
    ]


_ROUTER_NAMES = {
    ScraperType.STATIC: "_firecrawl_scrape",
    ScraperType.GATED: "_airtop_scrape",
    ScraperType.JS_HEAVY: "_browserbase_scrape",
}


def scrape_candidates(candidates: list[DirectoryCandidate]) -> list[ScrapedCompany]:
    """Scrape every candidate, dedupe by normalized host, return unified list."""
    import sys
    module = sys.modules[__name__]
    seen: set[str] = set()
    results: list[ScrapedCompany] = []
    for c in candidates:
        fn_name = _ROUTER_NAMES.get(c.scraper_type)
        if not fn_name:
            logger.error("[Scraper] No router for %s", c.scraper_type)
            continue
        scraper = getattr(module, fn_name)
        try:
            companies = scraper(c.url)
        except Exception as exc:
            logger.error("[Scraper] %s failed on %s: %s", c.scraper_type, c.url, exc)
            continue
        for company in companies:
            host = _normalize_host(company.website) or company.name.lower().strip()
            if host in seen:
                continue
            seen.add(host)
            results.append(company)
    return results
