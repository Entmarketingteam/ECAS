"""
signals/npi_poller.py
Healthcare Referral Pipeline — NPI Registry Weekly Poller

Polls the CMS NPI Registry API for newly registered healthcare businesses
that are high-priority referral targets for the compounding pharmacy
prescriber pipeline. Runs weekly (Monday 6am CT via n8n or cron).

Signal flow:
  NPI API → deduplicate vs Airtable → Findymail enrichment
    → Airtable insert → Smartlead enrollment → Slack notify

API docs: https://npiregistry.cms.hhs.gov/api-page
Taxonomy codes: https://taxonomy.nucc.org/
"""

import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("npi_poller")

# ── Constants ─────────────────────────────────────────────────────────────────
NPI_API_BASE = "https://npiregistry.cms.hhs.gov/api/"
NPI_API_VERSION = "2.1"

# CMS NPI Registry taxonomy codes for the healthcare referral pipeline.
# Each entry: (taxonomy_code, human_label, smartlead_campaign_name)
# The campaign name is used for logging; the campaign ID is resolved below
# from the TAXONOMY_CAMPAIGN_MAP at enrollment time.
TAXONOMY_TARGETS = [
    {
        "code": "3336C0003X",
        "label": "Compounding Pharmacy",
        "campaign_name": "Compounding Pharmacy — Prescriber Pipeline",
    },
    {
        "code": "261QS1200X",
        "label": "Sleep Lab",
        "campaign_name": "Sleep Lab — Physician Referral Pipeline",
    },
    {
        "code": "261QR0208X",
        "label": "Imaging Center",
        "campaign_name": "Imaging — Physician Referral Pipeline",
    },
    {
        "code": "251G00000X",
        "label": "Home Health Agency",
        "campaign_name": "Home Health — Referral Pipeline",
    },
]

# Map taxonomy code → Smartlead campaign ID.
# Add the actual IDs once campaigns are created in Smartlead.
# Placeholder values shown — override via env vars if needed.
TAXONOMY_CAMPAIGN_MAP: dict[str, str] = {
    "3336C0003X": os.environ.get("SL_CAMPAIGN_COMPOUNDING_PHARMACY", ""),
    "261QS1200X": os.environ.get("SL_CAMPAIGN_SLEEP_LAB", ""),
    "261QR0208X": os.environ.get("SL_CAMPAIGN_IMAGING_CENTER", ""),
    "251G00000X": os.environ.get("SL_CAMPAIGN_HOME_HEALTH", ""),
}

# Airtable base + table for healthcare signals (separate from ECAS EPC signals)
AIRTABLE_BASE_ID = "appoi8SzEJY8in57x"
# Signals raw table — same base as ECAS but signals are tagged with npi_registry_new source
AIRTABLE_SIGNALS_TABLE_ID = "tblAFJnXToLTKeaNU"
AIRTABLE_BASE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_SIGNALS_TABLE_ID}"

AIRTABLE_RATE_DELAY = 0.25   # 4 req/sec — Airtable limit is 5/sec
SMARTLEAD_RATE_DELAY = 0.25  # be gentle on Smartlead API
FINDYMAIL_RATE_DELAY = 0.1   # Findymail is generally fast

# How far back to look for new NPI registrations (7 days = weekly poll window)
LOOKBACK_DAYS = 7

# Max results per taxonomy query (NPI API maximum is 200)
NPI_LIMIT = 200

# ThreadPoolExecutor workers for parallel taxonomy polls
POLL_WORKERS = 4


# ── Secret resolution ─────────────────────────────────────────────────────────

def _get_env(key: str, required: bool = True) -> str:
    """Read a secret from environment. All secrets are sourced via Doppler."""
    val = os.environ.get(key, "")
    if required and not val:
        logger.error(f"Required env var not set: {key}")
        sys.exit(1)
    return val


# ── NPI API ───────────────────────────────────────────────────────────────────

def _date_range() -> tuple[str, str]:
    """
    Return (start_date, end_date) strings in YYYY-MM-DD format covering the
    last LOOKBACK_DAYS days. NPI API accepts enumeration_date as YYYY-MM-DD.
    """
    end = datetime.utcnow().date()
    start = end - timedelta(days=LOOKBACK_DAYS)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def _extract_primary_address(addresses: list[dict]) -> dict:
    """
    Pull the primary business location from the NPI addresses array.
    NPI returns address_1 / address_2 / city / state / postal_code / telephone_number.
    Prefers address_purpose == 'LOCATION' over 'MAILING'.
    """
    if not addresses:
        return {}
    location = next((a for a in addresses if a.get("address_purpose") == "LOCATION"), None)
    addr = location or addresses[0]
    return {
        "address_line1": addr.get("address_1", ""),
        "address_line2": addr.get("address_2", ""),
        "city": addr.get("city", ""),
        "state": addr.get("state", ""),
        "zip": addr.get("postal_code", "")[:5],
        "phone": addr.get("telephone_number", ""),
    }


def _extract_taxonomy_code(taxonomies: list[dict]) -> str:
    """Return the primary taxonomy code (where primary=True) or the first one."""
    primary = next((t for t in taxonomies if t.get("primary")), None)
    t = primary or (taxonomies[0] if taxonomies else {})
    return t.get("code", "")


def poll_taxonomy(taxonomy: dict, start_date: str, end_date: str) -> list[dict]:
    """
    Query NPI Registry for organizations registered under a single taxonomy code
    within the given date window. Returns a list of normalized contact dicts.

    NPI API query params:
      - taxonomy_description: not used — we filter by enumeration_type=NPI-2 (organizations)
        and taxonomy_code for precision
      - enumeration_type=NPI-2  → organization providers only (Type 2 NPIs)
      - taxonomy_code            → filter to specific taxonomy
      - enumeration_date         → range filter: "YYYY-MM-DD,YYYY-MM-DD"
      - version                  → API version (2.1 is current)
      - limit / skip             → pagination (max 200 per page)
    """
    taxonomy_code = taxonomy["code"]
    taxonomy_label = taxonomy["label"]

    params = {
        "version": NPI_API_VERSION,
        "enumeration_type": "NPI-2",          # Type 2 = organizations/businesses
        "taxonomy_code": taxonomy_code,        # exact taxonomy match
        # enumeration_date range: "YYYY-MM-DD,YYYY-MM-DD" (no spaces)
        "enumeration_date": f"{start_date},{end_date}",
        "limit": NPI_LIMIT,
        "skip": 0,
    }

    contacts: list[dict] = []
    page = 0

    while True:
        params["skip"] = page * NPI_LIMIT
        try:
            resp = requests.get(NPI_API_BASE, params=params, timeout=30)
        except requests.exceptions.Timeout:
            logger.warning(f"[NPI] Timeout fetching {taxonomy_label} (page {page})")
            break
        except requests.exceptions.RequestException as e:
            logger.warning(f"[NPI] Request error for {taxonomy_label}: {e}")
            break

        if resp.status_code != 200:
            logger.warning(
                f"[NPI] HTTP {resp.status_code} for {taxonomy_label}: {resp.text[:200]}"
            )
            break

        data = resp.json()
        result_count = data.get("result_count", 0)
        results = data.get("results", [])

        if not results:
            break

        for record in results:
            # NPI-2 org name is in basic.organization_name
            basic = record.get("basic", {})
            org_name = basic.get("organization_name") or basic.get("name", "")

            if not org_name:
                continue  # Skip records with no org name

            npi_number = record.get("number", "")
            addresses = record.get("addresses", [])
            taxonomies = record.get("taxonomies", [])
            enumeration_date = basic.get("enumeration_date", "")

            addr = _extract_primary_address(addresses)
            primary_tax_code = _extract_taxonomy_code(taxonomies)

            contacts.append({
                "npi_number": npi_number,
                "org_name": org_name,
                "taxonomy_code": primary_tax_code or taxonomy_code,
                "taxonomy_label": taxonomy_label,
                "registration_date": enumeration_date,
                "address_line1": addr.get("address_line1", ""),
                "address_line2": addr.get("address_line2", ""),
                "city": addr.get("city", ""),
                "state": addr.get("state", ""),
                "zip": addr.get("zip", ""),
                "phone": addr.get("phone", ""),
                # Email and Smartlead campaign ID are filled in downstream steps
                "email": "",
                "email_status": "pending",
                "smartlead_campaign_id": TAXONOMY_CAMPAIGN_MAP.get(taxonomy_code, ""),
            })

        logger.info(
            f"[NPI] {taxonomy_label} page {page}: {len(results)} results "
            f"(total available: {result_count})"
        )

        # If we got fewer results than the limit, we've exhausted the dataset
        if len(results) < NPI_LIMIT:
            break

        # Safety cap: never fetch more than 10 pages (2000 orgs) per taxonomy per week
        page += 1
        if page >= 10:
            logger.warning(f"[NPI] Page cap reached for {taxonomy_label}")
            break

    logger.info(f"[NPI] {taxonomy_label}: {len(contacts)} total new registrations")
    return contacts


# ── Airtable deduplication ─────────────────────────────────────────────────────

def _airtable_headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def get_existing_npi_numbers(api_key: str) -> set[str]:
    """
    Fetch all NPI numbers already stored in the Airtable signals table.
    We store the NPI number in the `notes` field with prefix "NPI:" so we can
    filter without a dedicated NPI field.

    Uses Airtable REST API pagination (100 records/page) to load the full set.
    Returns a set of NPI number strings for O(1) dedup lookups.
    """
    headers = _airtable_headers(api_key)
    npi_numbers: set[str] = set()
    offset = None

    while True:
        params: dict = {
            # Only fetch signals tagged as npi_registry_new to keep the query small
            "filterByFormula": "SEARCH('NPI:', {notes})",
            "fields[]": ["notes"],
            "pageSize": 100,
        }
        if offset:
            params["offset"] = offset

        try:
            time.sleep(AIRTABLE_RATE_DELAY)
            resp = requests.get(AIRTABLE_BASE_URL, headers=headers, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            logger.error(f"[Airtable] Error fetching existing NPI numbers: {e}")
            break

        for record in data.get("records", []):
            notes = record.get("fields", {}).get("notes", "")
            # Notes field format: "NPI:1234567890 | ..."
            if notes.startswith("NPI:"):
                npi_part = notes.split("|")[0].replace("NPI:", "").strip()
                if npi_part:
                    npi_numbers.add(npi_part)

        offset = data.get("offset")
        if not offset:
            break

    logger.info(f"[Airtable] {len(npi_numbers)} existing NPI signals found for dedup")
    return npi_numbers


def deduplicate(contacts: list[dict], existing_npis: set[str]) -> list[dict]:
    """
    Filter contacts to only those with NPI numbers not already in Airtable.
    Also deduplicates within the current batch (two taxonomies might return the
    same org if it holds multiple codes).
    """
    seen: set[str] = set()
    net_new: list[dict] = []

    for c in contacts:
        npi = c["npi_number"]
        if not npi:
            continue
        if npi in existing_npis:
            continue
        if npi in seen:
            continue
        seen.add(npi)
        net_new.append(c)

    logger.info(f"[Dedup] {len(contacts)} total → {len(net_new)} net-new after dedup")
    return net_new


# ── Findymail enrichment ───────────────────────────────────────────────────────

def enrich_with_findymail(contact: dict, api_key: str) -> dict:
    """
    Attempt to find a business email for the org via Findymail's company search.

    Findymail API: POST https://app.findymail.com/api/search/name
    Docs: https://findymail.com/docs

    On success: sets contact["email"] and contact["email_status"] = "found"
    On failure: leaves email blank, sets contact["email_status"] = "not_found"
    Either way, the contact is still pushed to Airtable (per spec).
    """
    if not api_key:
        contact["email_status"] = "not_found"
        return contact

    # Findymail name-based company search endpoint
    endpoint = "https://app.findymail.com/api/search/name"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "name": contact["org_name"],
        "domain": "",  # domain lookup not available from NPI data alone
    }

    try:
        time.sleep(FINDYMAIL_RATE_DELAY)
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=20)

        if resp.status_code == 200:
            data = resp.json()
            # Findymail returns { email: "...", confidence: 0-100, ... }
            email = data.get("email") or data.get("emails", [None])[0]
            if email:
                contact["email"] = email
                contact["email_status"] = "found"
                logger.debug(f"[Findymail] Found email for {contact['org_name']}: {email}")
            else:
                contact["email_status"] = "not_found"

        elif resp.status_code == 404:
            contact["email_status"] = "not_found"

        elif resp.status_code == 429:
            logger.warning("[Findymail] Rate limited — skipping enrichment for this contact")
            contact["email_status"] = "not_found"

        else:
            logger.warning(
                f"[Findymail] HTTP {resp.status_code} for {contact['org_name']}: {resp.text[:200]}"
            )
            contact["email_status"] = "not_found"

    except requests.exceptions.Timeout:
        logger.warning(f"[Findymail] Timeout for {contact['org_name']}")
        contact["email_status"] = "not_found"
    except requests.exceptions.RequestException as e:
        logger.warning(f"[Findymail] Request error for {contact['org_name']}: {e}")
        contact["email_status"] = "not_found"

    return contact


# ── Airtable insert ────────────────────────────────────────────────────────────

def push_to_airtable(contact: dict, api_key: str) -> Optional[str]:
    """
    Create a new record in the ECAS signals table for a net-new NPI registration.

    Field mapping:
      signal_type   = "npi_registry_new"
      source        = "manual" (closest valid singleSelect for a custom API signal)
      company_name  = org_name
      sector        = "Healthcare Referral"
      captured_at   = registration_date (or now if missing)
      raw_text      = full address + contact details block
      notes         = "NPI:{npi_number} | Taxonomy:{label} | Email:{email_status}"
      confidence_score = 20.0 (baseline for new registration signal)
    """
    headers = _airtable_headers(api_key)

    # Build a rich raw_text block that captures everything the NPI returned
    addr_parts = [
        contact.get("address_line1", ""),
        contact.get("address_line2", ""),
        contact.get("city", ""),
        contact.get("state", ""),
        contact.get("zip", ""),
    ]
    address_str = ", ".join(p for p in addr_parts if p)

    raw_text_lines = [
        f"Org: {contact['org_name']}",
        f"NPI: {contact['npi_number']}",
        f"Taxonomy: {contact['taxonomy_label']} ({contact['taxonomy_code']})",
        f"Registered: {contact['registration_date']}",
        f"Address: {address_str}",
        f"Phone: {contact.get('phone', '')}",
        f"Email: {contact.get('email', '')} ({contact.get('email_status', 'unknown')})",
    ]
    raw_text = "\n".join(line for line in raw_text_lines if line)

    # notes field carries the NPI number for future dedup lookups (prefix "NPI:")
    notes = (
        f"NPI:{contact['npi_number']} | "
        f"Taxonomy:{contact['taxonomy_label']} | "
        f"Email status:{contact.get('email_status', 'unknown')}"
    )

    # Capture registration date as Airtable dateTime
    reg_date = contact.get("registration_date", "")
    if reg_date:
        captured_at = reg_date[:10] + "T00:00:00.000Z"
    else:
        captured_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")

    fields = {
        "signal_type": "npi_registry_new",
        "source": "manual",              # singleSelect — "manual" is valid per storage/airtable.py
        "company_name": contact["org_name"],
        "sector": "Healthcare Referral",
        "captured_at": captured_at,
        "raw_text": raw_text[:10000],
        "confidence_score": 20.0,        # baseline score for brand-new registration signal
        "processed": False,
        "notes": notes[:10000],
    }

    try:
        time.sleep(AIRTABLE_RATE_DELAY)
        resp = requests.post(
            AIRTABLE_BASE_URL,
            headers=headers,
            json={"fields": fields},
            timeout=30,
        )
        resp.raise_for_status()
        record_id = resp.json().get("id")
        logger.debug(f"[Airtable] Inserted {contact['org_name']} (NPI {contact['npi_number']}) → {record_id}")
        return record_id
    except requests.RequestException as e:
        logger.error(
            f"[Airtable] Insert failed for {contact['org_name']} "
            f"(NPI {contact['npi_number']}): {e}"
        )
        return None


# ── Smartlead enrollment ──────────────────────────────────────────────────────

def enroll_in_smartlead(contact: dict, api_key: str) -> bool:
    """
    Add a net-new NPI contact to the appropriate Smartlead campaign based on
    its taxonomy code. Each taxonomy maps to a different outreach sequence.

    Smartlead add lead endpoint:
      POST /api/v1/campaigns/{campaign_id}/leads
      Body: { api_key, lead_list: [{ email, first_name, last_name, ... }] }

    Returns True on success, False on failure (non-blocking — Airtable insert
    already happened before this is called).
    """
    campaign_id = contact.get("smartlead_campaign_id", "")
    if not campaign_id:
        logger.warning(
            f"[Smartlead] No campaign ID mapped for taxonomy {contact['taxonomy_code']} — "
            f"skipping enrollment for {contact['org_name']}"
        )
        return False

    email = contact.get("email", "")
    if not email:
        logger.debug(
            f"[Smartlead] No email for {contact['org_name']} — cannot enroll, skipping"
        )
        return False

    # Smartlead wants first_name/last_name — for orgs we use org name as first_name
    payload = {
        "api_key": api_key,
        "lead_list": [
            {
                "email": email,
                "first_name": contact["org_name"],
                "last_name": "",
                "phone_number": contact.get("phone", ""),
                "company_name": contact["org_name"],
                "custom_fields": {
                    "npi_number": contact["npi_number"],
                    "taxonomy": contact["taxonomy_label"],
                    "address": ", ".join(filter(None, [
                        contact.get("address_line1"),
                        contact.get("city"),
                        contact.get("state"),
                        contact.get("zip"),
                    ])),
                    "registration_date": contact.get("registration_date", ""),
                    "source": "npi_registry_new",
                },
            }
        ],
    }

    endpoint = f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}/leads"

    try:
        time.sleep(SMARTLEAD_RATE_DELAY)
        resp = requests.post(endpoint, json=payload, timeout=30)

        if resp.status_code in (200, 201):
            logger.debug(
                f"[Smartlead] Enrolled {contact['org_name']} → campaign {campaign_id}"
            )
            return True

        # 409 = lead already in campaign (not a hard failure)
        if resp.status_code == 409:
            logger.debug(
                f"[Smartlead] {contact['org_name']} already in campaign {campaign_id}"
            )
            return True

        logger.warning(
            f"[Smartlead] HTTP {resp.status_code} enrolling {contact['org_name']}: {resp.text[:200]}"
        )
        return False

    except requests.exceptions.Timeout:
        logger.warning(f"[Smartlead] Timeout enrolling {contact['org_name']}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"[Smartlead] Request error enrolling {contact['org_name']}: {e}")
        return False


# ── Slack notification ────────────────────────────────────────────────────────

def send_slack_notification(
    webhook_url: str,
    new_count: int,
    enrolled_count: int,
    taxonomy_breakdown: dict[str, int],
    errors: list[str],
) -> None:
    """
    Post a summary to #ecas-ops via Slack Incoming Webhook.
    Includes per-taxonomy breakdown, enrollment count, and any errors.
    """
    if not webhook_url:
        logger.warning("[Slack] SLACK_WEBHOOK_URL not set — skipping notification")
        return

    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    status_emoji = ":white_check_mark:" if not errors else ":warning:"

    breakdown_lines = "\n".join(
        f"  • {label}: {count}" for label, count in taxonomy_breakdown.items()
    )

    text = (
        f"{status_emoji} *NPI Registry Poller — {date_str}*\n"
        f"New registrations found: *{new_count}*\n"
        f"Enrolled in Smartlead: *{enrolled_count}*\n"
        f"\n*By taxonomy:*\n{breakdown_lines}"
    )

    if errors:
        error_summary = "\n".join(f"  • {e}" for e in errors[:5])
        text += f"\n\n:rotating_light: *Errors ({len(errors)}):*\n{error_summary}"

    payload = {"text": text}

    try:
        resp = requests.post(webhook_url, json=payload, timeout=15)
        if resp.status_code != 200:
            logger.warning(f"[Slack] Webhook returned HTTP {resp.status_code}: {resp.text}")
        else:
            logger.info(f"[Slack] Notification sent — {new_count} new signals")
    except requests.exceptions.RequestException as e:
        logger.error(f"[Slack] Failed to send notification: {e}")


# ── Main orchestrator ─────────────────────────────────────────────────────────

def run_poller() -> dict:
    """
    Full pipeline run:
      1. Load API keys from environment (Doppler-sourced)
      2. Calculate date window (last 7 days)
      3. Poll NPI API in parallel for all 4 taxonomy codes
      4. Deduplicate against Airtable
      5. Enrich with Findymail
      6. Push to Airtable + enroll in Smartlead
      7. Send Slack summary

    Returns a summary dict for logging / n8n downstream steps.
    """
    # ── Load secrets ──────────────────────────────────────────────────────────
    airtable_api_key = _get_env("AIRTABLE_API_KEY")
    findymail_api_key = _get_env("FINDYMAIL_API_KEY", required=False)
    smartlead_api_key = _get_env("SMARTLEAD_API_KEY", required=False)
    slack_webhook_url = _get_env("SLACK_WEBHOOK_URL", required=False)

    if not findymail_api_key:
        logger.warning("[Config] FINDYMAIL_API_KEY not set — email enrichment will be skipped")
    if not smartlead_api_key:
        logger.warning("[Config] SMARTLEAD_API_KEY not set — Smartlead enrollment will be skipped")

    # ── Date window ───────────────────────────────────────────────────────────
    start_date, end_date = _date_range()
    logger.info(f"[NPI] Polling registrations from {start_date} to {end_date}")

    # ── Parallel taxonomy polls ───────────────────────────────────────────────
    # Use ThreadPoolExecutor with 4 workers to fetch all 4 taxonomies concurrently.
    # Each taxonomy poll is independent and I/O bound (HTTP), so parallelism is safe.
    all_contacts: list[dict] = []
    errors: list[str] = []

    with ThreadPoolExecutor(max_workers=POLL_WORKERS) as executor:
        future_to_taxonomy = {
            executor.submit(poll_taxonomy, taxonomy, start_date, end_date): taxonomy
            for taxonomy in TAXONOMY_TARGETS
        }

        for future in as_completed(future_to_taxonomy):
            taxonomy = future_to_taxonomy[future]
            try:
                contacts = future.result()
                all_contacts.extend(contacts)
            except Exception as e:
                msg = f"Poll failed for {taxonomy['label']}: {e}"
                logger.error(f"[NPI] {msg}")
                errors.append(msg)

    logger.info(f"[NPI] Total raw results across all taxonomies: {len(all_contacts)}")

    if not all_contacts:
        logger.info("[NPI] No new registrations found — nothing to process")
        send_slack_notification(
            slack_webhook_url,
            new_count=0,
            enrolled_count=0,
            taxonomy_breakdown={t["label"]: 0 for t in TAXONOMY_TARGETS},
            errors=errors,
        )
        return {"new_contacts": 0, "enrolled": 0, "errors": len(errors)}

    # ── Dedup against Airtable ────────────────────────────────────────────────
    existing_npis = get_existing_npi_numbers(airtable_api_key)
    net_new = deduplicate(all_contacts, existing_npis)

    if not net_new:
        logger.info("[Dedup] All registrations already in Airtable — nothing to process")
        send_slack_notification(
            slack_webhook_url,
            new_count=0,
            enrolled_count=0,
            taxonomy_breakdown={t["label"]: 0 for t in TAXONOMY_TARGETS},
            errors=errors,
        )
        return {"new_contacts": 0, "enrolled": 0, "errors": len(errors)}

    # ── Enrich, insert, enroll ────────────────────────────────────────────────
    taxonomy_breakdown: dict[str, int] = {t["label"]: 0 for t in TAXONOMY_TARGETS}
    inserted_count = 0
    enrolled_count = 0

    for contact in net_new:
        # Step 1: Findymail email enrichment (non-blocking — failures don't stop the record)
        if findymail_api_key:
            contact = enrich_with_findymail(contact, findymail_api_key)
        else:
            contact["email_status"] = "not_found"

        # Step 2: Push to Airtable (always, even without email)
        record_id = push_to_airtable(contact, airtable_api_key)
        if record_id:
            inserted_count += 1
            taxonomy_breakdown[contact["taxonomy_label"]] = (
                taxonomy_breakdown.get(contact["taxonomy_label"], 0) + 1
            )

        # Step 3: Enroll in Smartlead (only if email was found)
        if smartlead_api_key and contact.get("email"):
            enrolled = enroll_in_smartlead(contact, smartlead_api_key)
            if enrolled:
                enrolled_count += 1
        elif not contact.get("email"):
            logger.debug(
                f"[Smartlead] Skipping {contact['org_name']} — no email found by Findymail"
            )

    logger.info(
        f"[Summary] {len(net_new)} net-new | {inserted_count} inserted to Airtable | "
        f"{enrolled_count} enrolled in Smartlead"
    )

    # ── Slack summary ──────────────────────────────────────────────────────────
    send_slack_notification(
        slack_webhook_url,
        new_count=inserted_count,
        enrolled_count=enrolled_count,
        taxonomy_breakdown=taxonomy_breakdown,
        errors=errors,
    )

    return {
        "new_contacts": inserted_count,
        "enrolled": enrolled_count,
        "errors": len(errors),
        "taxonomy_breakdown": taxonomy_breakdown,
    }


if __name__ == "__main__":
    import json

    logger.info("NPI Registry Poller — Healthcare Referral Pipeline")
    logger.info(f"Taxonomies: {[t['label'] for t in TAXONOMY_TARGETS]}")

    result = run_poller()
    print(json.dumps(result, indent=2))
