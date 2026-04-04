"""
contractor/pipeline/orchestrator.py — Full autonomous outbound pipeline.

Chains: Signal Detection → Multi-Signal Scoring → ICP Qualification
        → Apollo Contact Hunt → Findymail Enrichment → Copy Generation
        → Smartlead Enrollment → Health Monitoring

Run via APScheduler (wired in ECAS main scheduler) or triggered manually
via FastAPI admin endpoint: POST /admin/run/contractor_pipeline

Architecture:
- Signal scrapers push raw signals to Airtable signals_raw table
- Orchestrator reads signals, scores, qualifies, enriches, generates copy, enrolls
- Health monitor runs every 6h independently
- All failures → Slack alert → continue (never crash the pipeline)

Designed for LEAST HUMAN IN THE LOOP:
- Red Hot (150+): Slack alert → human closer within 1hr
- Hot (100-149): Auto-enrolled in Smartlead + LinkedIn queued
- Warm (50-99): Auto-enrolled in Smartlead email-only
- Cool / Cold: Airtable monitoring queue, no outreach
"""

import logging
import os
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

import requests

from contractor.config import (
    VERTICAL_ICPS, CONTRACTOR_CAMPAIGN_MAP, CONTRACTOR_DOMAINS
)
from contractor.pipeline.signal_scorer import Signal, score_lead, filter_actionable, ScoredLead
from contractor.pipeline.health_monitor import (
    run_health_check, alert_pipeline_error, alert_hot_lead
)

logger = logging.getLogger(__name__)

# ─── Env / Config ─────────────────────────────────────────────────────────────
APOLLO_API_KEY = os.environ.get("APOLLO_API_KEY", "")
FINDYMAIL_API_KEY = os.environ.get("FINDYMAIL_API_KEY", "")
SMARTLEAD_API_KEY = os.environ.get("SMARTLEAD_API_KEY", "")
AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY", "")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID", "appoi8SzEJY8in57x")

SMARTLEAD_BASE = "https://server.smartlead.ai/api/v1"
APOLLO_BASE = "https://api.apollo.io/v1"
FINDYMAIL_BASE = "https://app.findymail.com/api"

# ICP scoring thresholds for Tier A/B/C (ColdIQ qualify-accounts framework)
ICP_TIER_A = 80   # Tier 1 ABM: full multichannel, manual AE touch
ICP_TIER_B = 60   # Tier 2: Smartlead sequence + LinkedIn
ICP_TIER_C = 40   # Tier 3: Smartlead email-only


# ─── Data Classes ─────────────────────────────────────────────────────────────
class EnrichedContact:
    def __init__(self, first_name, last_name, email, title, company_name,
                 company_domain, vertical, icp_score, signal_score,
                 heat_level, personalization_hook, email_verified=False):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.title = title
        self.company_name = company_name
        self.company_domain = company_domain
        self.vertical = vertical
        self.icp_score = icp_score
        self.signal_score = signal_score
        self.heat_level = heat_level
        self.personalization_hook = personalization_hook
        self.email_verified = email_verified


# ─── Step 1: Read Raw Signals from Airtable ──────────────────────────────────
def fetch_unprocessed_signals(vertical: str = None) -> list[dict]:
    """
    Pull unprocessed signals from Airtable signals_raw table.
    Filters to contractor verticals only.
    """
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/signals_raw"
    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}

    # Filter formula: not yet processed, contractor vertical
    vertical_filter = ""
    if vertical:
        vertical_filter = f", {{vertical}}='{vertical}'"
    formula = f"AND({{processed}}=FALSE(), {{vertical_type}}='contractor'{vertical_filter})"

    params = {"filterByFormula": formula, "maxRecords": 100}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json().get("records", [])
    except Exception as e:
        logger.error("Failed to fetch signals from Airtable: %s", e)
        alert_pipeline_error("orchestrator.fetch_signals", str(e))
        return []


def group_signals_by_company(raw_records: list[dict]) -> dict:
    """
    Group Airtable signal records by company domain.
    Returns: {domain: {"company_name": str, "vertical": str, "signals": [Signal]}}
    """
    grouped = {}
    for record in raw_records:
        fields = record.get("fields", {})
        domain = fields.get("company_domain", "").lower().strip()
        if not domain:
            continue

        if domain not in grouped:
            grouped[domain] = {
                "company_name": fields.get("company_name", ""),
                "company_domain": domain,
                "vertical": fields.get("vertical", ""),
                "signals": [],
                "airtable_ids": [],
            }

        grouped[domain]["signals"].append(Signal(
            type=fields.get("signal_type", "company_news"),
            detected_at=datetime.fromisoformat(
                fields.get("detected_at", datetime.utcnow().isoformat())
            ),
            source=fields.get("source", "unknown"),
            raw_data=fields.get("raw_data_json", {}),
            notes=fields.get("notes", ""),
        ))
        grouped[domain]["airtable_ids"].append(record["id"])

    return grouped


# ─── Step 2: ICP Scoring ─────────────────────────────────────────────────────
def icp_score_company(company: dict, vertical: str) -> int:
    """
    Score a company against the vertical ICP.
    100-point system (ColdIQ qualify-accounts framework).

    Criteria:
    - Employee count in range: 30 pts
    - Revenue in range: 25 pts
    - Title match (when contact found): 20 pts
    - Geo match: 15 pts
    - No excluded keywords: 10 pts
    """
    icp = VERTICAL_ICPS.get(vertical, {})
    score = 0

    emp_count = company.get("employee_count", 0) or 0
    if icp.get("employee_min", 0) <= emp_count <= icp.get("employee_max", 9999):
        score += 30

    revenue_m = (company.get("annual_revenue_usd", 0) or 0) / 1_000_000
    if icp.get("revenue_min_m", 0) <= revenue_m <= icp.get("revenue_max_m", 9999):
        score += 25

    state = company.get("state", "")
    if state in icp.get("geo_focus", []):
        score += 15

    name_lower = company.get("name", "").lower()
    desc_lower = company.get("short_description", "").lower()
    excluded = [kw.lower() for kw in icp.get("exclude_keywords", [])]
    if not any(ex in name_lower or ex in desc_lower for ex in excluded):
        score += 10

    # Title scoring deferred to contact-level (added when contact found)
    # Base company score max: 80 pts — contact title adds up to 20

    return score


# ─── Step 3: Apollo Contact Hunt ─────────────────────────────────────────────
def hunt_contact_apollo(company_name: str, vertical: str) -> Optional[dict]:
    """
    Find the best decision-maker contact at a company via Apollo.
    Uses /mixed_people/api_search (NOT deprecated /people/search).

    Returns contact dict or None.
    """
    icp = VERTICAL_ICPS.get(vertical, {})
    target_titles = icp.get("target_titles", ["Owner", "President", "CEO"])

    # Step 1: Find org
    try:
        org_resp = requests.post(
            f"{APOLLO_BASE}/organizations/search",
            headers={"Content-Type": "application/json", "x-api-key": APOLLO_API_KEY},
            json={"q_organization_name": company_name, "page": 1, "per_page": 1},
            timeout=30,
        )
        org_resp.raise_for_status()
        orgs = org_resp.json().get("organizations", [])
        if not orgs:
            logger.debug("No Apollo org found for %s", company_name)
            return None
        org_id = orgs[0]["id"]
    except Exception as e:
        logger.error("Apollo org search failed for %s: %s", company_name, e)
        return None

    # Step 2: Find person by org + title
    try:
        people_resp = requests.post(
            f"{APOLLO_BASE}/mixed_people/api_search",
            headers={"Content-Type": "application/json", "x-api-key": APOLLO_API_KEY},
            json={
                "organization_ids": [org_id],
                "titles": target_titles,
                "page": 1,
                "per_page": 5,
            },
            timeout=30,
        )
        people_resp.raise_for_status()
        people = people_resp.json().get("people", [])
        if not people:
            return None
        return people[0]  # Take best match (Apollo sorts by relevance)
    except Exception as e:
        logger.error("Apollo people search failed for %s: %s", company_name, e)
        return None


# ─── Step 4: Findymail Email Enrichment ──────────────────────────────────────
def enrich_email_findymail(
    first_name: str, last_name: str, company_domain: str
) -> Optional[dict]:
    """
    Find and verify email via Findymail.
    Waterfall: /search by domain → verify.
    Returns {"email": str, "verified": bool} or None.
    """
    try:
        resp = requests.post(
            f"{FINDYMAIL_BASE}/search",
            headers={
                "Authorization": f"Bearer {FINDYMAIL_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "name": f"{first_name} {last_name}",
                "domain": company_domain,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        email = data.get("email")
        if not email:
            return None

        # Verify
        verify_resp = requests.post(
            f"{FINDYMAIL_BASE}/verify",
            headers={
                "Authorization": f"Bearer {FINDYMAIL_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"email": email},
            timeout=30,
        )
        verify_resp.raise_for_status()
        verify_data = verify_resp.json()

        return {
            "email": email,
            "verified": verify_data.get("status") in ("valid", "accept_all"),
        }
    except Exception as e:
        logger.debug("Findymail enrichment failed for %s %s @ %s: %s",
                     first_name, last_name, company_domain, e)
        return None


# ─── Step 5: Smartlead Enrollment ────────────────────────────────────────────
def enroll_in_smartlead(contact: EnrichedContact) -> bool:
    """
    Enroll a contact in the appropriate Smartlead campaign.
    Skips if already enrolled (Smartlead deduplicates by email).
    """
    campaign_id = CONTRACTOR_CAMPAIGN_MAP.get(contact.vertical)
    if not campaign_id:
        logger.warning("No campaign ID for vertical %s — skipping enrollment", contact.vertical)
        return False

    payload = {
        "lead_list": [{
            "email": contact.email,
            "first_name": contact.first_name,
            "last_name": contact.last_name,
            "company_name": contact.company_name,
            "custom_fields": {
                "vertical": contact.vertical,
                "icp_score": str(contact.icp_score),
                "signal_score": str(round(contact.signal_score, 1)),
                "heat_level": contact.heat_level,
                "personalization_hook": contact.personalization_hook,
            },
        }],
        "settings": {
            "ignore_global_block_list": False,
            "ignore_unsubscribe_list": False,
            "ignore_community_bounce_list": False,
        },
    }

    try:
        resp = requests.post(
            f"{SMARTLEAD_BASE}/campaigns/{campaign_id}/leads",
            params={"api_key": SMARTLEAD_API_KEY},
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        logger.info(
            "Enrolled %s %s (%s) in campaign %s",
            contact.first_name, contact.last_name, contact.vertical, campaign_id
        )
        return True
    except Exception as e:
        logger.error(
            "Smartlead enrollment failed for %s @ %s: %s",
            contact.email, contact.company_name, e
        )
        return False


# ─── Step 6: Mark Signals Processed ─────────────────────────────────────────
def mark_signals_processed(airtable_ids: list[str]) -> None:
    """Update Airtable signal records as processed."""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/signals_raw"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json",
    }
    for record_id in airtable_ids:
        try:
            requests.patch(
                f"{url}/{record_id}",
                headers=headers,
                json={"fields": {"processed": True, "processed_at": datetime.utcnow().isoformat()}},
                timeout=15,
            )
        except Exception as e:
            logger.warning("Failed to mark signal %s processed: %s", record_id, e)


# ─── Main Pipeline ────────────────────────────────────────────────────────────
def process_company(company_data: dict) -> Optional[EnrichedContact]:
    """
    Process a single company through the full pipeline.
    Returns EnrichedContact on success, None on failure/skip.
    """
    company_name = company_data["company_name"]
    domain = company_data["company_domain"]
    vertical = company_data["vertical"]
    signals = company_data["signals"]

    # Score signals
    scored = score_lead(company_name, domain, vertical, signals)

    # Skip if below warm threshold
    if scored.heat_level in ("cold", "cool"):
        logger.debug("Skipping %s — heat=%s score=%.1f", company_name, scored.heat_level, scored.score)
        return None

    # Red Hot: alert immediately, still enroll
    if scored.heat_level == "red_hot":
        alert_hot_lead(
            company_name=company_name,
            vertical=vertical,
            score=scored.score,
            hook=scored.personalization_hook,
            sla_hours=scored.sla_hours,
        )

    # ICP scoring — basic company-level (title score added when contact found)
    icp_score = icp_score_company(
        {"name": company_name, "domain": domain},
        vertical
    )

    if icp_score < ICP_TIER_C:
        logger.info("Skipping %s — ICP score %d below tier C (%d)", company_name, icp_score, ICP_TIER_C)
        return None

    # Find contact via Apollo
    contact_data = hunt_contact_apollo(company_name, vertical)
    if not contact_data:
        logger.info("No contact found via Apollo for %s", company_name)
        return None

    # Add title score to ICP
    icp = VERTICAL_ICPS.get(vertical, {})
    contact_title = contact_data.get("title", "")
    if any(t.lower() in contact_title.lower() for t in icp.get("target_titles", [])):
        icp_score += 20

    # Enrich email via Findymail
    first_name = contact_data.get("first_name", "")
    last_name = contact_data.get("last_name", "")
    email_result = enrich_email_findymail(first_name, last_name, domain)

    if not email_result or not email_result.get("email"):
        logger.info("No verified email found for %s at %s", contact_title, company_name)
        return None

    return EnrichedContact(
        first_name=first_name,
        last_name=last_name,
        email=email_result["email"],
        title=contact_title,
        company_name=company_name,
        company_domain=domain,
        vertical=vertical,
        icp_score=icp_score,
        signal_score=scored.score,
        heat_level=scored.heat_level,
        personalization_hook=scored.personalization_hook,
        email_verified=email_result.get("verified", False),
    )


def run_contractor_pipeline(vertical: str = None) -> dict:
    """
    Main pipeline job — called by APScheduler every 4 hours.

    Flow:
    1. Fetch unprocessed signals from Airtable
    2. Group by company → score signals (multi-signal framework)
    3. Filter to warm/hot/red_hot
    4. Apollo contact hunt (parallel, 4 workers)
    5. Findymail email enrichment (parallel, 4 workers)
    6. Smartlead enrollment
    7. Mark signals processed
    8. Run health check on all campaigns

    Args:
        vertical: Optional — run for a single vertical only

    Returns:
        Summary dict with counts for logging/alerting
    """
    start = time.time()
    logger.info("=== Contractor Pipeline START | vertical=%s ===", vertical or "ALL")

    summary = {
        "signals_found": 0,
        "companies_scored": 0,
        "actionable": 0,
        "contacts_found": 0,
        "emails_enriched": 0,
        "enrolled": 0,
        "skipped": 0,
        "errors": 0,
        "duration_seconds": 0,
    }

    # Step 1: Fetch signals
    try:
        raw_records = fetch_unprocessed_signals(vertical)
        summary["signals_found"] = len(raw_records)

        if not raw_records:
            logger.info("No unprocessed signals found — pipeline done")
            return summary

        grouped = group_signals_by_company(raw_records)
        summary["companies_scored"] = len(grouped)
    except Exception as e:
        logger.error("Signal fetch failed: %s", e)
        alert_pipeline_error("orchestrator.fetch_signals", str(e))
        return summary

    # Step 2: Score all companies
    companies_list = list(grouped.values())

    # Steps 3-6: Process each company (parallel, 4 workers)
    enrolled_count = 0
    all_airtable_ids = []

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(process_company, company): company
            for company in companies_list
        }

        for future in as_completed(futures):
            company = futures[future]
            try:
                contact = future.result()

                if contact is None:
                    summary["skipped"] += 1
                    # Still mark signals processed so we don't re-evaluate
                    all_airtable_ids.extend(company.get("airtable_ids", []))
                    continue

                summary["contacts_found"] += 1
                if contact.email:
                    summary["emails_enriched"] += 1

                # Enroll in Smartlead
                enrolled = enroll_in_smartlead(contact)
                if enrolled:
                    summary["enrolled"] += 1

                all_airtable_ids.extend(company.get("airtable_ids", []))

            except Exception as e:
                summary["errors"] += 1
                logger.error("Company processing failed for %s: %s",
                             company.get("company_name", "?"), e)
                alert_pipeline_error(
                    "orchestrator.process_company",
                    str(e),
                    {"company": company.get("company_name", "?"), "vertical": company.get("vertical", "?")}
                )

    # Step 7: Mark signals processed
    if all_airtable_ids:
        mark_signals_processed(all_airtable_ids)

    # Step 8: Health check (every 4th run — roughly once/day)
    # Health monitor runs on its own 6h schedule; skip here unless explicitly needed
    # run_health_check(CONTRACTOR_CAMPAIGN_MAP)

    summary["duration_seconds"] = round(time.time() - start, 1)
    logger.info("=== Contractor Pipeline DONE | %s ===", summary)
    return summary


# ─── APScheduler Job Registration ────────────────────────────────────────────
def register_contractor_jobs(scheduler) -> None:
    """
    Register all contractor pipeline jobs with the existing ECAS APScheduler.
    Call this from ECAS's main scheduler setup.

    Jobs added:
    - contractor_pipeline: every 4h — main signal → enroll pipeline
    - contractor_health: every 6h — campaign health monitoring
    - contractor_hail_signals: every 6h — NOAA hail event scraper (Roofing)
    """
    from contractor.signals.hail_events import run_hail_signal_job
    from contractor.pipeline.health_monitor import run_health_check

    # Main pipeline — every 4 hours
    scheduler.add_job(
        func=run_contractor_pipeline,
        trigger="interval",
        hours=4,
        id="contractor_pipeline",
        name="Contractor Signal → Enroll Pipeline",
        replace_existing=True,
        misfire_grace_time=300,
    )

    # Health monitor — every 6 hours
    scheduler.add_job(
        func=lambda: run_health_check(CONTRACTOR_CAMPAIGN_MAP),
        trigger="interval",
        hours=6,
        id="contractor_health",
        name="Contractor Campaign Health Monitor",
        replace_existing=True,
        misfire_grace_time=300,
    )

    # Hail signal scraper — every 6 hours (Roofing vertical)
    scheduler.add_job(
        func=run_hail_signal_job,
        trigger="interval",
        hours=6,
        id="contractor_hail_signals",
        name="NOAA Hail Event Signal Scraper",
        replace_existing=True,
        misfire_grace_time=300,
    )

    logger.info("Contractor jobs registered: contractor_pipeline, contractor_health, contractor_hail_signals")
