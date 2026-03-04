"""
enrichment/clay_enricher.py
Uses Clay.com API to find decision-maker contacts at target EPC companies.
Falls back to Apollo if Clay is unavailable.

Clay replaces: Apollo + FindyMail + Proxycurl waterfall.
One API call → email + LinkedIn + phone + verified.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import CLAY_API_KEY, APOLLO_API_KEY, ICP

logger = logging.getLogger(__name__)

CLAY_BASE_URL = "https://api.clay.com/v1"
APOLLO_SEARCH_URL = "https://api.apollo.io/v1/mixed_people/search"


def find_contacts_clay(company_name: str, titles: list[str] = None) -> list[dict]:
    """
    Use Clay API to find contacts at a company.
    Returns list of enriched contact dicts.
    """
    if not CLAY_API_KEY:
        logger.warning("[Clay] CLAY_API_KEY not set — skipping Clay enrichment")
        return []

    target_titles = titles or ICP["titles"]

    try:
        resp = requests.post(
            f"{CLAY_BASE_URL}/people/search",
            headers={
                "Authorization": f"Bearer {CLAY_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "company_name": company_name,
                "job_titles": target_titles,
                "email_status": "verified",
                "limit": 10,
            },
            timeout=30,
        )
        if resp.status_code == 401:
            logger.error("[Clay] Unauthorized — check CLAY_API_KEY")
            return []
        resp.raise_for_status()
        data = resp.json()

        contacts = []
        for person in data.get("people", data.get("results", [])):
            contacts.append({
                "first_name": person.get("first_name", ""),
                "last_name": person.get("last_name", ""),
                "email": person.get("email", ""),
                "title": person.get("title", person.get("job_title", "")),
                "company": company_name,
                "linkedin_url": person.get("linkedin_url", ""),
                "phone": person.get("phone", ""),
                "email_verified": person.get("email_status") == "verified",
                "source": "Clay",
            })

        logger.info(f"[Clay] Found {len(contacts)} contacts at {company_name}")
        return contacts

    except requests.RequestException as e:
        logger.error(f"[Clay] API error for {company_name}: {e}")
        return []


def find_contacts_apollo(company_name: str, titles: list[str] = None) -> list[dict]:
    """
    Fallback: Apollo people search for a company.
    """
    if not APOLLO_API_KEY:
        logger.warning("[Apollo] APOLLO_API_KEY not set")
        return []

    target_titles = titles or ICP["titles"]

    try:
        resp = requests.post(
            APOLLO_SEARCH_URL,
            headers={
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
                "X-Api-Key": APOLLO_API_KEY,
            },
            json={
                "q_organization_name": company_name,
                "person_titles": target_titles,
                "page": 1,
                "per_page": 10,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        contacts = []
        for person in data.get("people", []):
            email = person.get("email", "")
            if not email or person.get("email_status") == "invalid":
                continue
            contacts.append({
                "first_name": person.get("first_name", ""),
                "last_name": person.get("last_name", ""),
                "email": email,
                "title": person.get("title", ""),
                "company": company_name,
                "linkedin_url": person.get("linkedin_url", ""),
                "phone": person.get("sanitized_phone", ""),
                "email_verified": person.get("email_status") == "verified",
                "source": "Apollo",
            })

        logger.info(f"[Apollo] Found {len(contacts)} contacts at {company_name}")
        return contacts

    except requests.RequestException as e:
        logger.error(f"[Apollo] API error for {company_name}: {e}")
        return []


def enrich_company(company_name: str, titles: list[str] = None) -> list[dict]:
    """
    Waterfall enrichment: Clay → Apollo fallback.
    Returns deduplicated list of contacts.
    """
    contacts = find_contacts_clay(company_name, titles)
    if not contacts:
        contacts = find_contacts_apollo(company_name, titles)

    # Deduplicate by email
    seen_emails: set[str] = set()
    unique_contacts = []
    for c in contacts:
        email = c.get("email", "").lower().strip()
        if email and email not in seen_emails:
            seen_emails.add(email)
            unique_contacts.append(c)

    return unique_contacts


def enrich_and_store(company_name: str, project_record_id: str = None) -> dict:
    """
    Enrich a company with contacts and store in Airtable.
    Returns summary of contacts found and stored.
    """
    from storage.airtable import get_client
    at = get_client()

    contacts = enrich_company(company_name)
    stored = 0

    for contact in contacts:
        email = contact.get("email", "")
        if not email:
            continue

        record_id = at.upsert_contact(
            email=email,
            first_name=contact.get("first_name", ""),
            last_name=contact.get("last_name", ""),
            title=contact.get("title", ""),
            company=company_name,
            linkedin_url=contact.get("linkedin_url", ""),
            phone=contact.get("phone", ""),
            outreach_status="not_contacted",
            notes=f"Source: {contact.get('source', 'unknown')} | {datetime.utcnow().date()}",
        )
        if record_id:
            stored += 1

    logger.info(f"[Enrichment] {company_name}: {len(contacts)} found, {stored} stored")
    return {
        "company": company_name,
        "contacts_found": len(contacts),
        "contacts_stored": stored,
    }


def run_enricher(min_heat_score: float = 50.0) -> dict:
    """
    Pull high-priority projects from Airtable and enrich contacts.
    Only runs for projects that don't already have contacts.
    """
    from storage.airtable import get_client
    at = get_client()

    projects = at.get_projects()
    total_found = 0
    total_stored = 0
    enriched = 0

    for project in projects:
        fields = project.get("fields", {})
        company = fields.get("company_name", "")
        heat_score = fields.get("heat_score", 0)
        record_id = project.get("id")

        if not company or heat_score < min_heat_score:
            continue

        # Check if already has contacts
        existing = at.get_contacts_by_company(company)
        if existing:
            logger.debug(f"[Enrichment] {company}: already has {len(existing)} contacts, skipping")
            continue

        result = enrich_and_store(company, project_record_id=record_id)
        total_found += result["contacts_found"]
        total_stored += result["contacts_stored"]
        enriched += 1

    logger.info(f"[Enrichment] Enriched {enriched} companies | {total_found} found | {total_stored} stored")
    return {
        "companies_enriched": enriched,
        "contacts_found": total_found,
        "contacts_stored": total_stored,
    }


if __name__ == "__main__":
    import json
    import logging
    logging.basicConfig(level=logging.INFO)
    # Test with a single company
    contacts = enrich_company("Quanta Services")
    print(json.dumps(contacts, indent=2))
