"""
storage/supabase_leads.py
Supabase write client for Google Maps discovery pipeline.
Handles upsert/query for gmaps_companies, gmaps_contacts, enrollment_log.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional

import requests

logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")


def _headers() -> dict:
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates",
    }


def _sb_upsert(table: str, records: list[dict], on_conflict: str) -> bool:
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.warning("[SupabaseLeads] SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set")
        return False
    headers = _headers()
    headers["Prefer"] = f"resolution=merge-duplicates,return=minimal"
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/{table}?on_conflict={on_conflict}",
        headers=headers,
        json=records,
        timeout=15,
    )
    if r.status_code not in (200, 201):
        logger.error(f"[SupabaseLeads] upsert {table} failed {r.status_code}: {r.text[:200]}")
        return False
    return True


def _sb_get(table: str, params: dict) -> list:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/{table}",
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
        params=params,
        timeout=15,
    )
    if r.status_code != 200:
        logger.error(f"[SupabaseLeads] get {table} failed {r.status_code}")
        return []
    return r.json()


def _sb_patch(table: str, match_params: dict, update: dict) -> bool:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return False
    r = requests.patch(
        f"{SUPABASE_URL}/rest/v1/{table}",
        headers={**_headers(), "Prefer": "return=minimal"},
        params=match_params,
        json=update,
        timeout=15,
    )
    if r.status_code not in (200, 204):
        logger.error(f"[SupabaseLeads] patch {table} failed {r.status_code}: {r.text[:200]}")
        return False
    return True


def upsert_companies(companies: list[dict]) -> int:
    """Upsert a batch of gmaps_companies. Returns count written."""
    if not companies:
        return 0
    ok = _sb_upsert("gmaps_companies", companies, "place_id")
    return len(companies) if ok else 0


def upsert_contacts(contacts: list[dict]) -> int:
    """Upsert a batch of gmaps_contacts. Returns count written."""
    if not contacts:
        return 0
    ok = _sb_upsert("gmaps_contacts", contacts, "email")
    return len(contacts) if ok else 0


def mark_company_enriched(place_id: str) -> None:
    _sb_patch(
        "gmaps_companies",
        {"place_id": f"eq.{place_id}"},
        {"enrichment_status": "enriched", "enriched_at": datetime.now(timezone.utc).isoformat()},
    )


def mark_company_enrichment_failed(place_id: str) -> None:
    _sb_patch(
        "gmaps_companies",
        {"place_id": f"eq.{place_id}"},
        {"enrichment_status": "failed"},
    )


def get_pending_companies(limit: int = 100) -> list[dict]:
    """Return companies waiting for contact enrichment."""
    return _sb_get("gmaps_companies", {
        "enrichment_status": "eq.pending",
        "website_domain": "not.is.null",
        "select": "place_id,name,website_domain,sector,state",
        "limit": limit,
        "order": "created_at.asc",
    })


def get_unenrolled_contacts(limit: int = 200) -> list[dict]:
    """Return good-quality contacts not yet enrolled in Smartlead."""
    return _sb_get("gmaps_contacts", {
        "enrolled_at": "is.null",
        "email_quality": "eq.good",
        "select": "id,place_id,company_name,website_domain,first_name,last_name,title,email,linkedin_url",
        "limit": limit,
        "order": "created_at.asc",
    })


def mark_contact_enrolled(contact_id: str, campaign_id: str) -> None:
    _sb_patch(
        "gmaps_contacts",
        {"id": f"eq.{contact_id}"},
        {"enrolled_at": datetime.now(timezone.utc).isoformat(), "smartlead_campaign_id": campaign_id},
    )


def log_enrollment(email: str, campaign_id: str, source: str, lead_data: dict) -> None:
    _sb_upsert("enrollment_log", [{
        "contact_email": email,
        "smartlead_campaign_id": campaign_id,
        "source": source,
        "lead_data": lead_data,
    }], "contact_email")
