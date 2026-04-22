"""
signals/gmaps_scraper.py
Google Maps business scraper for EPC contractor discovery.

Uses RapidAPI Google Maps Extractor 2 to search for EPC-related businesses
across US zip codes. Pulls zip codes from Supabase zip_codes table (already
populated by zip-demographics pipeline) filtered by population.

Results are deduplicated by place_id and written to Supabase gmaps_companies.
"""

import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
from typing import Optional

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import RAPIDAPI_KEY, GMAPS_QUERIES
from storage.supabase_leads import upsert_companies

logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

RAPIDAPI_HOST = "google-maps-extractor2.p.rapidapi.com"

MIN_POPULATION = 10_000
MAX_WORKERS = 5
RESULTS_PER_ZIP = 20


class _RateLimiter:
    def __init__(self, max_per_second: int = 5):
        self._lock = Lock()
        self._timestamps: list[float] = []
        self._max = max_per_second

    def wait(self):
        with self._lock:
            now = time.time()
            self._timestamps = [t for t in self._timestamps if now - t < 1.0]
            if len(self._timestamps) >= self._max:
                sleep_for = 1.0 - (now - self._timestamps[0]) + 0.01
                if sleep_for > 0:
                    time.sleep(sleep_for)
                self._timestamps = self._timestamps[1:]
            self._timestamps.append(time.time())


_rate_limiter = _RateLimiter(max_per_second=5)


def _get_zips_from_supabase(state: Optional[str] = None) -> list[dict]:
    """Pull zip codes from Supabase zip_codes table with population filter."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("[GMapsScraper] Supabase not configured")
        return []
    params = {
        "select": "zip,city,state_id",
        "population": f"gte.{MIN_POPULATION}",
        "limit": 5000,
        "order": "population.desc",
    }
    if state:
        params["state_id"] = f"eq.{state.upper()}"
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/zip_codes",
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
        params=params,
        timeout=15,
    )
    if r.status_code != 200:
        logger.error(f"[GMapsScraper] zip fetch failed: {r.status_code}")
        return []
    return r.json()


def _search_maps(query: str, zip_code: str, rapidapi_key: str) -> list[dict]:
    """Search Google Maps for a query in a given zip code."""
    _rate_limiter.wait()
    headers = {
        "x-rapidapi-key": rapidapi_key,
        "x-rapidapi-host": RAPIDAPI_HOST,
    }
    try:
        r = requests.get(
            f"https://{RAPIDAPI_HOST}/locate_and_search",
            headers=headers,
            params={"query": f"{query} in {zip_code}", "limit": RESULTS_PER_ZIP},
            timeout=20,
        )
        if r.status_code == 429:
            logger.warning("[GMapsScraper] Rate limited — sleeping 5s")
            time.sleep(5)
            return []
        if r.status_code != 200:
            return []
        data = r.json()
        return data if isinstance(data, list) else data.get("results", [])
    except Exception as e:
        logger.debug(f"[GMapsScraper] search error {zip_code}: {e}")
        return []


def _extract_domain(website_url: Optional[str]) -> Optional[str]:
    if not website_url:
        return None
    try:
        from urllib.parse import urlparse
        parsed = urlparse(website_url if "://" in website_url else f"https://{website_url}")
        domain = parsed.netloc.lower().lstrip("www.")
        return domain if domain else None
    except Exception:
        return None


def _scrape_zip(query_config: dict, zip_info: dict, rapidapi_key: str) -> list[dict]:
    """Scrape one (query, zip) pair. Returns list of company dicts ready for Supabase."""
    query = query_config["query"]
    sector = query_config["sector"]
    zip_code = zip_info["zip"]
    state = zip_info.get("state_id", "")

    results = _search_maps(query, zip_code, rapidapi_key)
    companies = []
    for biz in results:
        place_id = biz.get("place_id") or biz.get("business_id")
        if not place_id:
            continue
        website = biz.get("website")
        companies.append({
            "place_id":       place_id,
            "name":           biz.get("name") or biz.get("title"),
            "address":        biz.get("address") or biz.get("full_address"),
            "phone":          biz.get("phone"),
            "website_domain": _extract_domain(website),
            "rating":         biz.get("rating"),
            "total_reviews":  biz.get("reviews") or biz.get("total_reviews"),
            "zip_code":       zip_code,
            "state":          state,
            "query":          query,
            "sector":         sector,
        })
    return companies


def run_scraper(states: Optional[list[str]] = None, max_zips: Optional[int] = None) -> dict:
    """
    Main entry point. Scrapes all GMAPS_QUERIES × matching zip codes.

    Args:
        states: List of state codes to limit scope (e.g. ["TX", "CA"]). None = all states.
        max_zips: Cap total zips per query for testing. None = no cap.

    Returns summary dict.
    """
    if not RAPIDAPI_KEY:
        logger.error("[GMapsScraper] RAPIDAPI_KEY not set")
        return {"error": "RAPIDAPI_KEY not set"}

    totals = {"companies_found": 0, "companies_written": 0, "zips_processed": 0}
    batch: list[dict] = []
    BATCH_SIZE = 200

    for query_config in GMAPS_QUERIES:
        target_states = states if states else [None]
        for state in target_states:
            zips = _get_zips_from_supabase(state=state)
            if max_zips:
                zips = zips[:max_zips]
            if not zips:
                continue

            logger.info(
                f"[GMapsScraper] '{query_config['query']}' × {len(zips)} zips"
                + (f" in {state}" if state else "")
            )

            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
                futures = {pool.submit(_scrape_zip, query_config, z, RAPIDAPI_KEY): z for z in zips}
                for future in as_completed(futures):
                    try:
                        companies = future.result()
                        batch.extend(companies)
                        totals["companies_found"] += len(companies)
                        totals["zips_processed"] += 1
                    except Exception as e:
                        logger.debug(f"[GMapsScraper] future error: {e}")

                    if len(batch) >= BATCH_SIZE:
                        written = upsert_companies(batch)
                        totals["companies_written"] += written
                        batch.clear()

    if batch:
        written = upsert_companies(batch)
        totals["companies_written"] += written

    logger.info(f"[GMapsScraper] Done — {totals}")
    return totals


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run_scraper(states=["TX"], max_zips=10)
    print(result)
