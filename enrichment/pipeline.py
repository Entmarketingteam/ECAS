"""
enrichment/pipeline.py
Atomic enrichment + enrollment pipeline.
Apollo → Findymail → Smartlead → Airtable in one pass.

Design decisions (from architecture review 2026-04-05):
- Wraps existing find_contacts_apollo() — does NOT reimplement the waterfall
- Wraps existing enroll_lead() — does NOT reimplement Smartlead enrollment
- Caches Smartlead campaign leads at batch start (fixes N+1 query bug)
- Parallel enrichment across companies (4 workers default)
- Sequential Smartlead enrollment (API not designed for parallel)
- Pre-flight health checks before every run
- LLM diagnosis on escalation
- All compute on Railway (flat rate) — no n8n/Zapier dependency
"""

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

logger = logging.getLogger(__name__)


def run_pipeline(
    min_heat: float = 50.0,
    company_filter: str | None = None,
    dry_run: bool = False,
    titles: list[str] | None = None,
    workers: int = 4,
) -> dict:
    """
    Full enrichment + enrollment pipeline. One function does everything.

    Called by:
      - scheduler cron (daily 10am)
      - POST /api/enrich-and-enroll
      - hot signal handler
      - budget window handler
      - manual CLI: curl POST /api/enrich-and-enroll

    Args:
        min_heat: Minimum confidence_score to process (default 50.0)
        company_filter: Process only this company (for hot signals / manual runs)
        dry_run: If True, find contacts but don't enroll or sync
        titles: Override ICP title filters (default from config.py)
        workers: Parallel enrichment workers (default 4)

    Returns:
        Results dict with counts, campaign breakdown, errors, and status.
    """
    from enrichment.health import pre_flight_check
    from enrichment.diagnosis import escalate, post_summary, post_preflight_alert
    from enrichment.retry import CircuitBreaker

    circuit_breaker = CircuitBreaker(threshold=5, cooldown_seconds=300)

    results = {
        "companies_processed": 0,
        "companies_qualified": 0,
        "contacts_found": 0,
        "contacts_enrolled": 0,
        "skipped": 0,
        "campaigns": {},
        "errors": [],
        "dry_run": dry_run,
        "status": "starting",
        "started_at": datetime.utcnow().isoformat(),
    }

    # ── Phase A: Pre-Flight ──────────────────────────────────────
    preflight = pre_flight_check()
    post_preflight_alert(preflight)

    if preflight["status"] == "blocked":
        results["status"] = "blocked"
        results["reason"] = f"Pre-flight failed: {preflight['failures']}"
        logger.error(f"[Pipeline] BLOCKED — {preflight['failures']}")
        return results

    degraded = set(preflight["failures"].keys()) if preflight["status"] == "degraded" else set()
    if degraded:
        logger.warning(f"[Pipeline] Running DEGRADED — failing services: {degraded}")
        # Reduce workers if Apollo is degraded
        if "apollo" in degraded:
            workers = 1

    # ── Stage 1: Get Qualified Projects ──────────────────────────
    projects = _get_projects(min_heat, company_filter)
    if not projects:
        results["status"] = "no_projects"
        logger.info("[Pipeline] No qualified projects found — nothing to do")
        return results

    results["companies_qualified"] = len(projects)

    if dry_run:
        results["status"] = "dry_run"
        logger.info(f"[Pipeline] Dry run — {len(projects)} projects qualified")
        return results

    # ── Stage 2: Enrich (parallel across companies) ──────────────
    contacts, enrich_errors = _enrich_batch(projects, workers=workers, titles=titles)
    results["contacts_found"] = len(contacts)
    results["errors"].extend(enrich_errors)

    if not contacts:
        if enrich_errors:
            escalate(
                error=Exception(f"{len(enrich_errors)} enrichment failures"),
                context={
                    "stage": "Enrichment",
                    "progress": f"0/{len(projects)} companies",
                    "api": "Apollo + Findymail",
                },
            )
        results["status"] = "no_contacts_found"
        return results

    # ── Stage 3: Enroll + Sync (sequential with caching) ────────
    delivery = _deliver_batch(contacts, circuit_breaker=circuit_breaker)
    results["contacts_enrolled"] = delivery["enrolled"]
    results["skipped"] += delivery["skipped"]
    results["campaigns"] = delivery["campaigns"]
    results["errors"].extend(delivery["errors"])

    # ── Post-Run ─────────────────────────────────────────────────
    results["status"] = "complete"
    results["completed_at"] = datetime.utcnow().isoformat()
    results["companies_processed"] = len(set(c["company"] for c in contacts))

    post_summary(results)

    # Partial failure — still diagnose
    if results["errors"]:
        escalate(
            error=Exception(f"{len(results['errors'])} partial failures"),
            context={
                "stage": "Summary",
                "progress": f"{results['contacts_enrolled']}/{results['contacts_found']} enrolled",
            },
        )

    logger.info(f"[Pipeline] Complete: {results}")
    return results


# ── Internal: Project Fetching ───────────────────────────────────────────────

def _get_projects(min_heat: float, company_filter: str | None) -> list[dict]:
    """Fetch qualified projects from Airtable. Skip companies with existing contacts."""
    from storage.airtable import get_client

    at = get_client()

    # Build filter
    if company_filter:
        formula = f"AND({{confidence_score}}>={min_heat}, {{owner_company}}='{company_filter}')"
    else:
        formula = f"AND({{confidence_score}}>={min_heat}, {{owner_company}}!='')"

    all_projects = at._get("projects", {"filterByFormula": formula, "maxRecords": 50})

    # Filter out companies that already have contacts (dedup)
    qualified = []
    for project in all_projects:
        fields = project.get("fields", {})
        company = fields.get("owner_company", "")
        if not company:
            continue
        existing = at.get_contacts_by_company(company)
        if existing:
            logger.debug(f"[Pipeline] {company}: already has {len(existing)} contacts — skipping")
            continue
        qualified.append(project)

    logger.info(f"[Pipeline] {len(qualified)}/{len(all_projects)} projects qualified (no existing contacts)")
    return qualified


# ── Internal: Enrichment (Parallel) ──────────────────────────────────────────

def _enrich_batch(
    projects: list[dict],
    workers: int = 4,
    titles: list[str] | None = None,
) -> tuple[list[dict], list[str]]:
    """
    Enrich multiple companies in parallel.
    Wraps existing find_contacts_apollo() — no waterfall reimplementation.
    Returns (contacts, errors).
    """
    from enrichment.clay_enricher import find_contacts_apollo
    from enrichment.retry import retry_with_fallback

    all_contacts = []
    errors = []

    def enrich_one(project: dict) -> list[dict]:
        fields = project.get("fields", {})
        company = fields.get("owner_company", "")
        record_id = project.get("id", "")

        # Parse sector from positioning_notes JSON
        sector = "Power & Grid Infrastructure"
        raw_notes = fields.get("positioning_notes", "")
        if raw_notes:
            try:
                notes_data = json.loads(raw_notes)
                sector = notes_data.get("sector", sector)
            except (json.JSONDecodeError, TypeError):
                pass

        heat = float(fields.get("confidence_score", 0))

        # Call existing waterfall with retry
        contacts = retry_with_fallback(
            primary=lambda: find_contacts_apollo(company, titles=titles),
            retries=2,
            backoff=3,
            category="apollo_waterfall",
        )

        # Attach project metadata to each contact
        for c in contacts:
            c["sector"] = sector
            c["heat_score"] = heat
            c["project_record_id"] = record_id

        return contacts

    # Fan-out across companies
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(enrich_one, p): p for p in projects}
        for future in as_completed(futures):
            project = futures[future]
            company = project.get("fields", {}).get("owner_company", "unknown")
            try:
                contacts = future.result()
                all_contacts.extend(contacts)
                logger.info(f"[Pipeline] {company}: {len(contacts)} verified contacts found")
            except Exception as e:
                error_msg = f"{company}: {type(e).__name__}: {e}"
                errors.append(error_msg)
                logger.error(f"[Pipeline] Enrichment failed for {company}: {e}")

    return all_contacts, errors


# ── Internal: Delivery (Sequential with Caching) ────────────────────────────

def _deliver_batch(
    contacts: list[dict],
    circuit_breaker=None,
) -> dict:
    """
    Enroll contacts in Smartlead + sync to Airtable.
    Sequential with 0.5s delay (Smartlead API design).

    FIX: Caches campaign leads at batch start to avoid N+1 fetch-all-leads-per-enrollment.
    """
    from outreach.smartlead import enroll_lead, get_campaign_leads, _resolve_campaign_id
    from storage.airtable import get_client
    from enrichment.retry import retry_with_fallback

    at = get_client()

    results = {"enrolled": 0, "skipped": 0, "campaigns": {}, "errors": []}

    # Pre-cache: fetch existing leads per campaign (fixes N+1 bug)
    # Group contacts by campaign first
    campaign_contacts = {}
    for contact in contacts:
        sector = contact.get("sector", "Power & Grid Infrastructure")
        campaign_id = _resolve_campaign_id(sector)
        contact["_campaign_id"] = campaign_id
        campaign_contacts.setdefault(campaign_id, []).append(contact)

    # Fetch existing leads per campaign (ONE API call per campaign, not per contact)
    existing_emails = {}  # campaign_id → set of emails
    for campaign_id in campaign_contacts:
        try:
            leads = get_campaign_leads(campaign_id)
            existing_emails[campaign_id] = {
                lead.get("email", "").lower().strip()
                for lead in leads
                if lead.get("email")
            }
            logger.info(f"[Pipeline] Campaign {campaign_id}: {len(existing_emails[campaign_id])} existing leads cached")
        except Exception as e:
            logger.warning(f"[Pipeline] Could not cache leads for campaign {campaign_id}: {e}")
            existing_emails[campaign_id] = set()  # can't cache — will skip dedup for this campaign

    # Enroll each contact
    for contact in contacts:
        email = contact.get("email", "")
        campaign_id = contact["_campaign_id"]
        company = contact.get("company", "")

        if not email:
            continue

        # Dedup against cached leads
        if email.lower().strip() in existing_emails.get(campaign_id, set()):
            logger.debug(f"[Pipeline] {email} already in campaign {campaign_id} — skipping")
            results["skipped"] += 1
            continue

        # Enroll with retry
        try:
            enroll_result = retry_with_fallback(
                primary=lambda e=email, fn=contact.get("first_name", ""), ln=contact.get("last_name", ""),
                       co=company, ti=contact.get("title", ""), se=contact.get("sector", ""),
                       hs=contact.get("heat_score", 0), cid=campaign_id: enroll_lead(
                    email=e, first_name=fn, last_name=ln, company=co,
                    title=ti, sector=se, heat_score=hs, campaign_id=cid,
                ),
                retries=2,
                backoff=2,
                category="smartlead_enroll",
                circuit_breaker=circuit_breaker,
            )

            if enroll_result.get("status") == "enrolled":
                results["enrolled"] += 1
                results["campaigns"][campaign_id] = results["campaigns"].get(campaign_id, 0) + 1

                # Add to cache to prevent duplicates within same batch
                existing_emails.setdefault(campaign_id, set()).add(email.lower().strip())

                # Airtable sync (non-blocking — enrollment is the priority)
                try:
                    record_id = at.upsert_contact(
                        email=email,
                        first_name=contact.get("first_name", ""),
                        last_name=contact.get("last_name", ""),
                        title=contact.get("title", ""),
                        company=company,
                        linkedin_url=contact.get("linkedin_url", ""),
                        phone=contact.get("phone", ""),
                        outreach_status="in_sequence",
                        notes=(
                            f"Source: {contact.get('source', 'unknown')} | Pipeline | "
                            f"{datetime.utcnow().date()} | Campaign {campaign_id}"
                        ),
                    )
                    # Link contact to project
                    project_id = contact.get("project_record_id")
                    if project_id and record_id:
                        at.link_contact_to_project(project_id, record_id)
                except Exception as e:
                    results["errors"].append(f"Airtable sync failed for {email}: {e}")
                    logger.warning(f"[Pipeline] Airtable sync failed for {email}: {e}")

            elif enroll_result.get("status") == "skipped":
                results["skipped"] += 1

        except Exception as e:
            results["errors"].append(f"Smartlead enrollment failed for {email}: {e}")
            logger.error(f"[Pipeline] Enrollment failed for {email}: {e}")

        time.sleep(0.5)  # Smartlead rate limit buffer

    return results
