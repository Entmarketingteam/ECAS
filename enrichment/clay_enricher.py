"""
enrichment/clay_enricher.py
Apollo two-step people enrichment for target EPC companies.

Step 1: Resolve company → Apollo org ID via /organizations/search
Step 2: Search people by organization_ids + title filters

Clay v1 API is deprecated. Apollo is primary.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import APOLLO_API_KEY, FINDYMAIL_API_KEY, ICP
from enrichment.millionverifier import verify_email as _mv_verify

logger = logging.getLogger(__name__)

APOLLO_BASE = "https://api.apollo.io/v1"
FINDYMAIL_BASE = "https://app.findymail.com/api"


def _apollo_headers() -> dict:
    return {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": APOLLO_API_KEY,
    }


def _resolve_org_id(company_name: str) -> str | None:
    """
    Look up Apollo organization ID by company name.
    Uses /organizations/search which is reliable for name-based lookup.
    """
    try:
        resp = requests.post(
            f"{APOLLO_BASE}/organizations/search",
            headers=_apollo_headers(),
            json={
                "q_organization_name": company_name,
                "page": 1,
                "per_page": 1,
            },
            timeout=30,
        )
        if resp.status_code in (401, 403):
            logger.error("[Apollo] Unauthorized on org search — check APOLLO_API_KEY")
            return None
        resp.raise_for_status()
        data = resp.json()
        orgs = data.get("organizations", [])
        if orgs:
            org_id = orgs[0].get("id")
            logger.debug(f"[Apollo] Resolved '{company_name}' → org_id={org_id}")
            return org_id
        logger.debug(f"[Apollo] No org found for '{company_name}'")
        return None
    except requests.RequestException as e:
        logger.error(f"[Apollo] Org search error for '{company_name}': {e}")
        return None


def _reveal_contacts(person_ids: list[str]) -> list[dict]:
    """
    Reveal emails for a batch of Apollo person IDs via bulk_match.
    Returns list of enriched person dicts with email populated.
    Apollo bulk_match accepts up to 10 IDs per request.
    """
    results = []
    for i in range(0, len(person_ids), 10):
        batch = person_ids[i:i + 10]
        try:
            resp = requests.post(
                f"{APOLLO_BASE}/people/bulk_match",
                headers=_apollo_headers(),
                json={
                    "details": [{"id": pid} for pid in batch],
                    "reveal_personal_emails": True,
                    "reveal_phone_number": False,
                },
                timeout=30,
            )
            if resp.status_code in (401, 403):
                logger.error("[Apollo] Unauthorized on bulk_match")
                break
            resp.raise_for_status()
            data = resp.json()
            results.extend(data.get("matches", []))
        except requests.RequestException as e:
            logger.error(f"[Apollo] bulk_match error: {e}")
    return results


def _domain_from_linkedin(linkedin_url: str, first_name: str = "", last_name: str = "") -> str:
    """
    Extract company domain from a LinkedIn profile URL or company page.
    Apollo people records often include linkedin_url like:
      linkedin.com/in/john-doe  → can't derive domain directly
      linkedin.com/company/acme-corp → scrape or look up acme-corp.com

    Strategy: parse the company slug from /company/ URLs and attempt
    common domain patterns (slug.com). For /in/ profiles we return ""
    since we can't reliably derive a domain without a live lookup.
    """
    if not linkedin_url:
        return ""
    url = linkedin_url.lower().strip().rstrip("/")
    # Company page: linkedin.com/company/acme-corp → try acme-corp.com
    if "/company/" in url:
        slug = url.split("/company/")[-1].split("/")[0].split("?")[0]
        # Strip common suffixes that appear in slugs
        slug = slug.replace("-inc", "").replace("-llc", "").replace("-corp", "").replace("-co", "")
        if slug:
            return f"{slug}.com"
    return ""


def _findymail_email(first_name: str, last_name: str, domain: str) -> str | None:
    """
    Findymail fallback: find email by name + company domain.
    Called when Apollo bulk_match doesn't reveal an email.
    """
    if not FINDYMAIL_API_KEY or not domain:
        return None
    try:
        resp = requests.post(
            f"{FINDYMAIL_BASE}/search",
            headers={"Authorization": f"Bearer {FINDYMAIL_API_KEY}", "Content-Type": "application/json"},
            json={"name": f"{first_name} {last_name}".strip(), "domain": domain},
            timeout=15,
        )
        if resp.status_code == 200:
            contact = resp.json().get("contact", {})
            email = contact.get("email", "")
            if email:
                logger.debug(f"[Findymail] Found {email} for {first_name} {last_name} @ {domain}")
                return email
    except requests.RequestException as e:
        logger.debug(f"[Findymail] Error for {first_name} {last_name}: {e}")
    return None


def _findymail_verify(email: str) -> bool:
    """
    Verify an email address via Findymail before storing.
    Returns True if the email is valid/deliverable, False otherwise.
    Blocks invalid, catch-all, and disposable addresses from entering Airtable.
    """
    if not FINDYMAIL_API_KEY or not email:
        # No Findymail key — fall back to MillionVerifier
        is_valid, _ = _mv_verify(email)
        return is_valid
    try:
        resp = requests.post(
            f"{FINDYMAIL_BASE}/verify",
            headers={"Authorization": f"Bearer {FINDYMAIL_API_KEY}", "Content-Type": "application/json"},
            json={"email": email},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            status = data.get("status", "unknown").lower()
            # Accept: valid. Reject: invalid, disposable, spamtrap, catch_all risky.
            is_valid = status == "valid"
            logger.debug(f"[Findymail] Verify {email} → {status} ({'pass' if is_valid else 'REJECT'})")
            return is_valid
    except requests.RequestException as e:
        logger.debug(f"[Findymail] Verify error for {email}: {e}")
    # Findymail network error — fall back to MillionVerifier
    is_valid, _ = _mv_verify(email)
    return is_valid


def find_contacts_apollo(company_name: str, titles: list[str] = None) -> list[dict]:
    """
    Apollo + Findymail enrichment waterfall:
      1. Apollo /organizations/search → org ID
      2. Apollo /mixed_people/api_search → candidates by title
      3. Apollo /people/bulk_match → reveal emails
      4. Findymail /search fallback → find email by name + org domain (if Apollo misses)
      5. Findymail /search fallback → find email by name + LinkedIn company domain (last resort)
      6. Findymail /verify → verify EVERY email before accepting into Airtable
    Only contacts with a verified, deliverable email are returned.
    """
    if not APOLLO_API_KEY:
        logger.warning("[Apollo] APOLLO_API_KEY not set")
        return []

    target_titles = titles or ICP["titles"]

    # Step 1: resolve org ID
    org_id = _resolve_org_id(company_name)
    if not org_id:
        logger.warning(f"[Apollo] Could not resolve org ID for '{company_name}' — skipping")
        return []

    # Step 2: search people by org ID (returns IDs + basic info, no emails)
    try:
        resp = requests.post(
            f"{APOLLO_BASE}/mixed_people/api_search",
            headers=_apollo_headers(),
            json={
                "organization_ids": [org_id],
                "person_titles": target_titles,
                "page": 1,
                "per_page": 10,
            },
            timeout=30,
        )
        if resp.status_code in (401, 403):
            logger.error("[Apollo] Unauthorized on people search")
            return []
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.error(f"[Apollo] People search error for '{company_name}': {e}")
        return []

    # Filter to people who have an email in Apollo's database
    # Also keep people without has_email for Findymail fallback
    candidates = data.get("people", [])
    if not candidates:
        logger.info(f"[Apollo] No people found at '{company_name}'")
        return []

    # Build domain map from Apollo org data for Findymail fallback
    domain_map: dict[str, str] = {}
    for p in candidates:
        org = p.get("organization") or {}
        domain = org.get("primary_domain", "")
        if domain:
            domain_map[p.get("id", "")] = domain

    # Step 3: reveal emails via bulk_match (only for has_email candidates)
    has_email_ids = [p["id"] for p in candidates if p.get("has_email")]
    revealed_map: dict[str, dict] = {}
    if has_email_ids:
        for person in _reveal_contacts(has_email_ids):
            revealed_map[person.get("id", "")] = person

    contacts = []
    for candidate in candidates:
        pid = candidate.get("id", "")
        person = revealed_map.get(pid, candidate)

        email = person.get("email", "")
        if not email or person.get("email_status") == "invalid":
            # Findymail fallback 1: search by name + company domain
            domain = domain_map.get(pid, "")
            email = _findymail_email(
                person.get("first_name", ""),
                person.get("last_name", ""),
                domain,
            ) or ""

        if not email:
            # Findymail fallback 2: search by name + domain extracted from LinkedIn URL
            linkedin = person.get("linkedin_url", "")
            li_domain = _domain_from_linkedin(linkedin, person.get("first_name", ""), person.get("last_name", ""))
            if li_domain and li_domain != domain_map.get(pid, ""):
                email = _findymail_email(
                    person.get("first_name", ""),
                    person.get("last_name", ""),
                    li_domain,
                ) or ""

        if not email:
            continue

        # Verify every email via Findymail before accepting it
        if not _findymail_verify(email):
            logger.info(f"[Findymail] Rejected {email} (invalid/undeliverable)")
            continue

        source = "Apollo" if pid in revealed_map and revealed_map[pid].get("email") else "Findymail"
        contacts.append({
            "first_name": person.get("first_name", ""),
            "last_name": person.get("last_name", ""),
            "email": email,
            "title": person.get("title", ""),
            "company": company_name,
            "linkedin_url": person.get("linkedin_url", ""),
            "phone": person.get("sanitized_phone", ""),
            "email_verified": True,  # passed Findymail verification
            "source": source,
        })

    logger.info(f"[Apollo] Found {len(contacts)} verified contacts at '{company_name}'")
    return contacts


def enrich_company(company_name: str, titles: list[str] = None) -> list[dict]:
    """
    Enrich a company with decision-maker contacts via Apollo.
    Returns deduplicated list of contacts.
    """
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


def enrich_and_store(company_name: str, project_record_id: str = None, titles: list[str] = None) -> dict:
    """
    Enrich a company with contacts and store in Airtable.
    Returns summary of contacts found and stored.
    """
    from storage.airtable import get_client
    at = get_client()

    contacts = enrich_company(company_name, titles=titles)
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
            outreach_status="pending_review",
            notes=f"Source: {contact.get('source', 'unknown')} | {datetime.utcnow().date()}",
        )
        if record_id:
            stored += 1
            # BUG FIX: link the contact back to its parent project record
            if project_record_id:
                at.link_contact_to_project(project_record_id, record_id)

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
        # Airtable field is owner_company (not company_name); score is confidence_score
        company = fields.get("owner_company") or fields.get("company_name", "")
        heat_score = float(fields.get("confidence_score") or fields.get("heat_score") or 0)
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
