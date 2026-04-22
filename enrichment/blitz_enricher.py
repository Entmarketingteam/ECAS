"""
enrichment/blitz_enricher.py
Domain-to-contacts enrichment waterfall for Google Maps companies.

Waterfall order:
  1. Blitz API (domain → owner/decision-maker, best for SMB/owner-operated contractors)
  2. Prospeo domain search (fallback, title-filtered)
  3. Mark failed if both return nothing

Contacts are validated via MillionVerifier before being written to Supabase.
"""

import logging
import sys
import time
from pathlib import Path
from typing import Optional

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import BLITZ_API_KEY, BLITZ_BASE_URL, PROSPEO_API_KEY
from enrichment.millionverifier import verify_email
from storage.supabase_leads import (
    get_pending_companies,
    mark_company_enriched,
    mark_company_enrichment_failed,
    upsert_contacts,
)

logger = logging.getLogger(__name__)

TARGET_TITLES = [
    "owner", "president", "ceo", "founder", "principal",
    "vp", "vice president", "director", "operations manager",
    "project manager", "business development",
]


def _blitz_search(domain: str) -> list[dict]:
    """Search Blitz API for contacts at a domain."""
    if not BLITZ_API_KEY:
        return []
    try:
        r = requests.post(
            f"{BLITZ_BASE_URL}/v1/people/search",
            headers={"Authorization": f"Bearer {BLITZ_API_KEY}", "Content-Type": "application/json"},
            json={"domain": domain, "titles": TARGET_TITLES, "limit": 5},
            timeout=15,
        )
        if r.status_code != 200:
            logger.debug(f"[BlitzEnricher] Blitz {r.status_code} for {domain}")
            return []
        data = r.json()
        return data.get("people", data) if isinstance(data, dict) else data
    except Exception as e:
        logger.debug(f"[BlitzEnricher] Blitz error for {domain}: {e}")
        return []


def _prospeo_search(domain: str) -> list[dict]:
    """Prospeo domain search fallback."""
    if not PROSPEO_API_KEY:
        return []
    try:
        r = requests.post(
            "https://api.prospeo.io/domain-search",
            headers={"X-KEY": PROSPEO_API_KEY, "Content-Type": "application/json"},
            json={"url": domain, "limit": 10},
            timeout=15,
        )
        if r.status_code != 200:
            logger.debug(f"[BlitzEnricher] Prospeo {r.status_code} for {domain}")
            return []
        data = r.json()
        people = data.get("response", {}).get("emails", [])
        return [
            {
                "first_name": p.get("first_name"),
                "last_name":  p.get("last_name"),
                "title":      p.get("position"),
                "email":      p.get("email"),
                "linkedin_url": p.get("linkedin_url"),
            }
            for p in people
            if p.get("email")
        ]
    except Exception as e:
        logger.debug(f"[BlitzEnricher] Prospeo error for {domain}: {e}")
        return []


def _normalize_contact(raw: dict) -> Optional[dict]:
    """Normalize a raw contact dict from either API into a consistent shape."""
    email = (raw.get("email") or "").strip().lower()
    if not email or "@" not in email:
        return None
    return {
        "first_name":   raw.get("first_name") or raw.get("firstName"),
        "last_name":    raw.get("last_name") or raw.get("lastName"),
        "title":        raw.get("title") or raw.get("job_title") or raw.get("position"),
        "email":        email,
        "linkedin_url": raw.get("linkedin_url") or raw.get("linkedin"),
    }


def enrich_company(place_id: str, company_name: str, domain: str, sector: str, state: str) -> int:
    """
    Enrich one company. Returns count of contacts written.
    """
    raw_contacts = _blitz_search(domain)
    source = "blitz"
    if not raw_contacts:
        raw_contacts = _prospeo_search(domain)
        source = "prospeo"

    if not raw_contacts:
        mark_company_enrichment_failed(place_id)
        return 0

    contacts_to_write = []
    for raw in raw_contacts[:5]:
        contact = _normalize_contact(raw)
        if not contact:
            continue
        is_valid, quality = verify_email(contact["email"])
        if not is_valid:
            continue
        contacts_to_write.append({
            **contact,
            "place_id":      place_id,
            "company_name":  company_name,
            "website_domain": domain,
            "email_quality": quality,
            "source":        source,
        })
        time.sleep(0.1)

    written = upsert_contacts(contacts_to_write)
    mark_company_enriched(place_id)
    return written


def run_enricher(batch_size: int = 50) -> dict:
    """
    Process a batch of pending companies from Supabase.
    Called by APScheduler daily.
    """
    companies = get_pending_companies(limit=batch_size)
    if not companies:
        logger.info("[BlitzEnricher] No pending companies")
        return {"processed": 0, "contacts_written": 0}

    totals = {"processed": 0, "contacts_written": 0}
    for company in companies:
        domain = company.get("website_domain")
        if not domain:
            mark_company_enrichment_failed(company["place_id"])
            continue
        written = enrich_company(
            place_id=company["place_id"],
            company_name=company.get("name", ""),
            domain=domain,
            sector=company.get("sector", ""),
            state=company.get("state", ""),
        )
        totals["processed"] += 1
        totals["contacts_written"] += written
        time.sleep(0.5)

    logger.info(f"[BlitzEnricher] Done — {totals}")
    return totals


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run_enricher(batch_size=5)
    print(result)
