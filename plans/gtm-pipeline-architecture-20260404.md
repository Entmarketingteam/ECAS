# GTM Pipeline Architecture — Chained Skills, Agentic Patterns, Self-Healing
**Date:** 2026-04-04
**Status:** Architecture spec — ready for implementation planning
**Execution Model:** Pipeline (6 stages) with Fan-Out parallelism per stage + Self-Healing supervisor

## What This Is

The complete architecture for how signals, list building, personalization, delivery, response handling, and self-healing chain together. Every stage has: retry logic, fallback paths, parallel execution where possible, and LLM-powered diagnosis when things fail.

This is the system design doc. Implementation plans for each stage reference this.

---

## Architecture Overview

```
                    ┌─────────────────────┐
                    │   SUPERVISOR AGENT   │
                    │  (health + recovery) │
                    └──────────┬──────────┘
                               │ monitors all stages
                               │ pre-flight checks before each run
                               │ diagnoses + auto-fixes on failure
                               │ escalates to Slack when stuck
                               ▼
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ STAGE 1  │──►│ STAGE 2  │──►│ STAGE 3  │──►│ STAGE 4  │──►│ STAGE 5  │
│ SIGNALS  │   │  LISTS   │   │PERSONALIZE│   │ DELIVER  │   │ RESPOND  │
│          │   │          │   │          │   │          │   │          │
│ Fan-out  │   │ Fan-out  │   │ Fan-out  │   │ Batch    │   │ Event-   │
│ parallel │   │ parallel │   │ parallel │   │ sequential│   │ driven   │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
     │              │              │              │              │
     ▼              ▼              ▼              ▼              ▼
  Airtable       Airtable       Airtable      Smartlead     Airtable
  signals_raw    contacts       contacts      campaigns     contacts
  projects                      (hooks)       (leads)       (status)
```

---

## Stage 1: Signal Detection

**Pattern:** Fan-Out → Aggregate
**Parallelism:** All signal sources run concurrently (already implemented in ECAS scheduler)
**Skills:** Intent Signal Analyzer, 131 triggers taxonomy
**Compute:** Railway (existing scheduler jobs)

```python
# Already running — 7 concurrent signal sources
PARALLEL: [
    politician_trades(),    # QuiverQuant — every 4h
    sec_13f(),              # SEC EDGAR — weekly Mon
    gov_contracts(),        # USASpending — every 4h
    rss_feeds(),            # 21 feeds — every 6h
    earnings_transcripts(), # FMP API — weekly Tue
    directory_hunt(),       # SAM.gov + conferences — weekly
    # FUTURE: Clay signal monitors (job changes, funding, tech stack)
]
→ Aggregate into signals_raw (Airtable)
→ Claude extraction → projects with confidence_score
→ Sector scoring (composite weights)
```

**Fallback chain per signal source:**
```
Try primary API
  → 401/403: refresh key from Doppler → retry once
  → 429 rate limit: exponential backoff (2s, 4s, 8s, 16s) → max 4 retries
  → 500/502/503: retry 3x with 5s backoff
  → Timeout: retry 2x with longer timeout (60s)
  → All retries exhausted: log warning, skip source, continue pipeline
  → NEVER block entire pipeline because one signal source is down
```

**Self-healing hooks:**
- Pre-flight: Test each API key with lightweight health check before batch run
- Degraded mode: If 2+ sources fail, post Slack alert but still run with available sources
- Circuit breaker: If a source fails 3 consecutive runs, disable it and alert (don't keep wasting API calls)

---

## Stage 2: List Building (Apollo + Findymail Waterfall)

**Pattern:** Pipeline (sequential per company) with Fan-Out (parallel across companies)
**Parallelism:** 4 companies enriched concurrently (ThreadPoolExecutor)
**Skills:** List Architect, identity-resolution
**Compute:** Railway (`enrichment/pipeline.py`)

```python
# PARALLEL across companies, SEQUENTIAL within each company
def enrich_batch(projects: list, workers=4) -> tuple[list, list]:
    results, errors = [], []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(enrich_single_company, p): p for p in projects}
        for future in as_completed(futures):
            project = futures[future]
            try:
                contacts = future.result()
                results.extend(contacts)
            except Exception as e:
                errors.append({
                    "company": project["owner_company"],
                    "error": str(e),
                    "stage": "enrichment",
                })
    return results, errors


def enrich_single_company(project) -> list[dict]:
    """
    SEQUENTIAL per company (each step depends on previous):
    1. Apollo org search → org_id
    2. Apollo people search → candidates
    3. Apollo bulk match → reveal emails
    4. Findymail fallback → fill gaps
    5. Findymail verify → gate
    """
    company = project["owner_company"]

    # Step 1: Org search (with retry)
    org_id = retry_with_fallback(
        primary=lambda: apollo_org_search(company),
        fallback=lambda: apollo_org_search(company.split()[0]),  # try first word
        retries=3,
        backoff=2,
        error_category="apollo_org",
    )
    if not org_id:
        raise EnrichmentError(f"No Apollo org found for '{company}'")

    # Step 2: People search (with retry)
    candidates = retry_with_fallback(
        primary=lambda: apollo_people_search(org_id, ICP_TITLES),
        retries=3,
        backoff=2,
        error_category="apollo_people",
    )
    if not candidates:
        return []  # no people found — not an error, just empty

    # Step 3: Bulk match (with retry, batches of 10)
    revealed = retry_with_fallback(
        primary=lambda: apollo_bulk_match([c["id"] for c in candidates if c.get("has_email")]),
        retries=3,
        backoff=2,
        error_category="apollo_reveal",
    )

    # Step 4-5: Email waterfall per contact (parallel within company)
    verified_contacts = []
    for candidate in candidates:
        email, source = email_waterfall(candidate, revealed, company)
        if email:
            verified_contacts.append({**candidate, "email": email, "source": source})

    return verified_contacts
```

**Email waterfall (per contact):**
```
Step 1: Check Apollo revealed email
  → Found + status != "invalid" → go to verify
  → Not found ↓

Step 2: Findymail search (name + company domain)
  → Found → go to verify
  → Not found ↓

Step 3: Findymail search (name + LinkedIn-derived domain)
  → Found → go to verify
  → Not found → SKIP contact (no email available)

Step 4: Findymail verify
  → "valid" → ACCEPT (add to results)
  → "invalid" / "catch_all" / "disposable" → REJECT (skip contact)
  → API error → ACCEPT with warning (don't block on verify failures)
```

**Fallback chain:**
```
Apollo down entirely?
  → Degrade: skip Apollo reveal, go straight to Findymail search for all contacts
  → Alert: "Apollo API unavailable — running Findymail-only mode (slower, more expensive)"

Findymail down entirely?
  → Degrade: accept Apollo emails without verification
  → Alert: "Findymail unavailable — emails not verified, proceed with caution"
  → Flag: email_verified=false in Airtable

Both down?
  → STOP: Don't push unverified, unresolved contacts to Smartlead
  → Alert: "Pipeline halted — both Apollo and Findymail unavailable"
  → Queue projects for next run
```

**Self-healing:**
- Credit monitoring: Check Findymail credit balance before run. If < 50 credits, alert and reduce batch size.
- Key rotation: On 401 from any API, pull fresh key from Doppler, retry.
- Adaptive batch size: If rate limits hit frequently, automatically reduce workers from 4 → 2 → 1.

---

## Stage 3: Personalization

**Pattern:** Fan-Out (parallel per contact)
**Parallelism:** 8 contacts personalized concurrently (LLM calls are I/O-bound)
**Skills:** Cold Email Strategist, BLUF framework, hook-writer, persona-intel, ai-personalization-prompts
**Compute:** Railway (Claude API calls)

> **Phase 1 (now):** Skip this stage. Use Smartlead's built-in sequence templates.
> **Phase 2 (when Clay or volume justifies it):** Add Claude-powered personalization.

```python
# FUTURE — Phase 2
def personalize_batch(contacts: list, workers=8) -> list[dict]:
    """Generate BLUF hooks + personalized sequences per contact."""
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(personalize_one, c): c for c in contacts}
        results = []
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                # Personalization failure is NOT fatal — use generic template
                contact = futures[future]
                contact["hook"] = None  # falls back to Smartlead template
                contact["personalization_error"] = str(e)
                results.append(contact)
    return results


def personalize_one(contact: dict) -> dict:
    """
    BLUF hook generation:
    Line 1: what we do + proof (grounded in signal data)
    Line 2: who we've done it for (closest case study)
    Line 3: CTA (calibrated to company stage)
    """
    prompt = f"""Write a 3-line BLUF cold email for {contact['first_name']} {contact['last_name']},
    {contact['title']} at {contact['company_name']} ({contact['sector']}).
    Signal: confidence score {contact['heat_score']}/100.
    Line 1: What we do + proof. Line 2: Relevant client. Line 3: Low-friction CTA.
    Max 25 words per line. No greeting, no sign-off."""

    response = retry_with_fallback(
        primary=lambda: claude_generate(prompt, model="claude-haiku-4-5"),
        retries=2,
        backoff=1,
        error_category="claude_personalization",
    )
    contact["hook"] = response
    return contact
```

**Fallback:** Personalization fails → use segment-level template (sector-based). Never block delivery because a hook didn't generate.

---

## Stage 4: Delivery (Smartlead Enrollment)

**Pattern:** Batch sequential (Smartlead API can't handle high parallelism)
**Parallelism:** 1 at a time with 0.5s delay (respect Smartlead rate limits)
**Skills:** cadence-design, deliverability-ops, routing-logic
**Compute:** Railway

```python
def deliver_batch(contacts: list) -> dict:
    """
    Enroll verified contacts into Smartlead campaigns.
    Sequential with delay — Smartlead's API is not designed for bulk parallel.
    """
    results = {"enrolled": 0, "skipped": 0, "errors": [], "campaigns": {}}

    for contact in contacts:
        campaign_id = resolve_campaign(contact["sector"])

        result = retry_with_fallback(
            primary=lambda: smartlead_enroll(contact, campaign_id),
            retries=3,
            backoff=2,
            error_category="smartlead_enroll",
        )

        if result["status"] == "enrolled":
            results["enrolled"] += 1
            results["campaigns"][campaign_id] = results["campaigns"].get(campaign_id, 0) + 1

            # Sync to Airtable (non-blocking — failure here doesn't block enrollment)
            try:
                airtable_upsert(contact, campaign_id)
            except Exception as e:
                results["errors"].append(f"Airtable sync failed for {contact['email']}: {e}")

        elif result["status"] == "skipped":
            results["skipped"] += 1
        else:
            results["errors"].append(f"{contact['email']}: {result.get('reason')}")

        time.sleep(0.5)  # rate limit buffer

    return results
```

**Fallback chain:**
```
Smartlead 429 (rate limit)?
  → Back off 30s → retry
  → If 3x rate limited → reduce to 1 req/3s → continue

Smartlead 500 (server error)?
  → Retry 3x with 5s backoff
  → If still failing → queue remaining contacts for next run
  → Alert: "Smartlead API unstable — X contacts queued for retry"

Smartlead campaign doesn't exist?
  → STOP for that sector → alert immediately
  → Continue enrolling contacts for other sectors

Airtable sync fails?
  → Log error, continue enrollment (Smartlead is the priority)
  → Batch-retry Airtable syncs at end of run
  → Alert if >5 Airtable failures
```

---

## Stage 5: Response Handling

**Pattern:** Event-driven (webhook triggered)
**Parallelism:** N/A — processes one reply at a time
**Skills:** reply-classifier, meeting-prep, battlecard-system
**Compute:** n8n (lightweight webhook receiver) + Railway (classification logic)

> Already partially implemented via Smartlead Signal Intelligence workflow (`4ZkYDJpqg5qBXdAW`).

```
Smartlead reply webhook → n8n
  → Haiku classifies: positive/negative/ooo/question/auto_reply
  → Route:
      positive → Airtable status="replied" + Slack alert + meeting-prep agent
      question → Claude drafts informed reply + human review
      negative → Airtable status="not_interested" + DNC
      ooo → schedule follow-up after return date
      auto_reply → ignore
```

**Future enhancement:** Feed reply patterns back into Stage 3 (personalization) to improve hooks based on what's getting positive responses.

---

## Supervisor Agent (Self-Healing Layer)

**Pattern:** Watchdog + Error Recovery + LLM Diagnosis
**Compute:** Railway (runs on same server as pipeline)

The Supervisor wraps the entire pipeline and handles three phases:

### Phase A: Pre-Flight Check (Before Every Run)

```python
def pre_flight_check() -> dict:
    """
    Run 30 seconds before pipeline. Catches problems before they cause failures.
    Each check is independent — run all in parallel.
    """
    checks = {}

    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {
            ex.submit(check_apollo_health): "apollo",
            ex.submit(check_findymail_credits): "findymail",
            ex.submit(check_smartlead_campaigns): "smartlead",
            ex.submit(check_airtable_access): "airtable",
            ex.submit(check_doppler_keys): "doppler",
            ex.submit(check_slack_webhook): "slack",
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                checks[name] = future.result()  # {"healthy": True/False, "detail": "..."}
            except Exception as e:
                checks[name] = {"healthy": False, "detail": str(e)}

    failures = {k: v for k, v in checks.items() if not v["healthy"]}

    if failures:
        diagnosis = diagnose_preflight_failures(failures)
        auto_fixed = attempt_auto_fix(failures)

        if auto_fixed:
            # Re-check only the fixed services
            rechecks = {k: recheck(k) for k in auto_fixed}
            still_broken = {k: v for k, v in rechecks.items() if not v["healthy"]}
            if not still_broken:
                slack_post(f"Pre-flight: {len(auto_fixed)} issues auto-fixed. Pipeline proceeding.")
                return {"status": "fixed", "checks": checks}

        # Can't auto-fix everything — decide whether to run degraded or skip
        critical = {"apollo", "airtable"}  # pipeline can't run without these
        if failures.keys() & critical:
            slack_post(f"Pipeline BLOCKED — critical service down:\n{diagnosis}")
            return {"status": "blocked", "checks": checks}
        else:
            slack_post(f"Pipeline running DEGRADED — non-critical issues:\n{diagnosis}")
            return {"status": "degraded", "checks": checks}

    return {"status": "healthy", "checks": checks}
```

**Health checks:**

| Check | What It Tests | Auto-Fix on Failure |
|-------|-------------|-------------------|
| `check_apollo_health` | GET `/organizations/search` with known company | Refresh key from Doppler → retry |
| `check_findymail_credits` | GET account balance | If < 50 credits: alert, reduce batch. If 0: switch to Apollo-only mode |
| `check_smartlead_campaigns` | GET each campaign ID exists + active | If campaign missing: alert (can't auto-fix) |
| `check_airtable_access` | Read 1 record from projects table | Refresh token from Doppler → retry |
| `check_doppler_keys` | Verify all required env vars are set | Can't auto-fix — alert immediately |
| `check_slack_webhook` | Post test message | If Slack down: log to Railway stdout (fallback) |

### Phase B: Retry Engine (During Pipeline)

```python
def retry_with_fallback(
    primary: callable,
    fallback: callable = None,
    retries: int = 3,
    backoff: int = 2,
    max_backoff: int = 60,
    error_category: str = "unknown",
    circuit_breaker: CircuitBreaker = None,
) -> any:
    """
    Universal retry wrapper used by every API call in the pipeline.

    Retry strategy per error type:
      - 429 rate limit: wait Retry-After header (or 2^attempt seconds), retry
      - 401/403 auth: refresh credential from Doppler, retry once
      - 500/502/503: exponential backoff, retry up to max
      - Timeout: increase timeout, retry up to max
      - Connection error: retry with backoff
      - 4xx other: permanent failure, don't retry
    """
    if circuit_breaker and circuit_breaker.is_open(error_category):
        raise CircuitBreakerOpen(f"{error_category} circuit breaker is open")

    last_error = None
    for attempt in range(retries + 1):
        try:
            result = primary()
            # Success — reset circuit breaker
            if circuit_breaker:
                circuit_breaker.record_success(error_category)
            return result

        except RateLimitError as e:
            wait = min(e.retry_after or (backoff ** attempt), max_backoff)
            logger.warning(f"[{error_category}] Rate limited. Waiting {wait}s (attempt {attempt+1}/{retries+1})")
            time.sleep(wait)
            last_error = e

        except AuthError as e:
            logger.warning(f"[{error_category}] Auth failed. Attempting key refresh.")
            refreshed = refresh_credential_from_doppler(error_category)
            if refreshed and attempt == 0:
                continue  # retry once with new key
            last_error = e
            break  # don't keep retrying auth failures

        except TransientError as e:
            wait = min(backoff ** attempt, max_backoff)
            logger.warning(f"[{error_category}] Transient error. Backoff {wait}s (attempt {attempt+1}/{retries+1})")
            time.sleep(wait)
            last_error = e

        except PermanentError as e:
            logger.error(f"[{error_category}] Permanent error: {e}")
            last_error = e
            break  # don't retry permanent errors

    # All retries exhausted — try fallback
    if fallback:
        try:
            logger.info(f"[{error_category}] Primary exhausted. Trying fallback.")
            return fallback()
        except Exception as e:
            last_error = e

    # Record failure for circuit breaker
    if circuit_breaker:
        circuit_breaker.record_failure(error_category)

    raise last_error


class CircuitBreaker:
    """
    Tracks consecutive failures per service.
    Opens circuit (blocks calls) after threshold failures.
    Resets after cooldown period.
    """
    def __init__(self, threshold=5, cooldown_seconds=300):
        self.threshold = threshold
        self.cooldown = cooldown_seconds
        self.failures = {}   # category → count
        self.opened_at = {}  # category → timestamp

    def is_open(self, category):
        if category not in self.opened_at:
            return False
        elapsed = time.time() - self.opened_at[category]
        if elapsed > self.cooldown:
            # Half-open: allow one attempt
            del self.opened_at[category]
            self.failures[category] = 0
            return False
        return True

    def record_failure(self, category):
        self.failures[category] = self.failures.get(category, 0) + 1
        if self.failures[category] >= self.threshold:
            self.opened_at[category] = time.time()
            logger.error(f"[CircuitBreaker] {category} opened after {self.threshold} consecutive failures")

    def record_success(self, category):
        self.failures[category] = 0
        if category in self.opened_at:
            del self.opened_at[category]
```

### Phase C: LLM Diagnosis + Smart Escalation (After Retries Exhaust)

```python
def diagnose_and_escalate(error: Exception, context: dict, recent_logs: list[str]) -> None:
    """
    When all retries and auto-fixes fail, Claude diagnoses the problem
    and posts a rich Slack alert with actionable next steps.
    """
    prompt = f"""You are an SRE diagnosing a pipeline failure in the ECAS system.

ERROR: {type(error).__name__}: {error}

CONTEXT:
- Stage: {context.get('stage')}
- API: {context.get('api')}
- Company: {context.get('company', 'N/A')}
- Endpoint: {context.get('endpoint', 'N/A')}
- Attempt: {context.get('attempt', 'N/A')} of {context.get('max_retries', 'N/A')}

AUTO-FIX ATTEMPTS:
{context.get('auto_fix_log', 'None')}

RECENT LOGS (last 20 lines):
{chr(10).join(recent_logs[-20:])}

Provide:
1. ROOT CAUSE (1-2 sentences — what specifically broke and why)
2. WHAT WAS TRIED (list auto-fix attempts and their results)
3. SUGGESTED FIX (specific steps the human should take — CLI commands, URLs, config changes)
4. URGENCY (critical/high/medium/low — based on pipeline impact)
5. PIPELINE STATUS (what completed, what was skipped, what's queued for retry)

Be specific. Include exact CLI commands or URLs where possible."""

    diagnosis = retry_with_fallback(
        primary=lambda: claude_generate(prompt, model="claude-haiku-4-5"),
        retries=1,
        backoff=1,
        error_category="claude_diagnosis",
    )

    # If even Claude fails, post raw error
    if not diagnosis:
        diagnosis = f"Claude diagnosis unavailable. Raw error: {error}"

    slack_message = f"""*ECAS Pipeline — Escalation Required*

*{context.get('stage', 'Unknown Stage')}* failed for *{context.get('company', 'batch run')}*

{diagnosis}

_Next scheduled run: {next_run_time()}_
_Trigger manual run: `curl -X POST {RAILWAY_URL}/api/enrich-and-enroll -d '{{"company_filter": "{context.get('company', '')}", "min_heat": 0}}'`_"""

    try:
        slack_post(slack_message, channel="#ecas-signals")
    except Exception:
        # Last resort: log to stdout (Railway captures this)
        logger.critical(f"ESCALATION (Slack failed):\n{slack_message}")
```

**What the Slack alert looks like:**

```
❌ ECAS Pipeline — Escalation Required

ENRICHMENT failed for Quanta Services

ROOT CAUSE:
Apollo /people/bulk_match returned 402 Payment Required. Your Apollo plan's
email reveal credits are exhausted (0 remaining). The key ending in ...x7f2
is valid but the account has no reveal credits left.

WHAT WAS TRIED:
1. Retried 3x with exponential backoff → same 402
2. Refreshed API key from Doppler → same error (key is valid, credits are not)
3. Attempted Findymail-only fallback → found 3/8 contacts via Findymail

SUGGESTED FIX:
1. Log into app.apollo.io → Settings → Plan → Add email credits
2. Or: switch to Findymail-only mode temporarily by setting APOLLO_REVEAL_ENABLED=false in Doppler
3. Pipeline will auto-retry on next scheduled run

URGENCY: high — enrichment is degraded (Findymail-only mode is 40% lower coverage)

PIPELINE STATUS:
• 3/12 companies processed before credit exhaustion
• 8 contacts enrolled (from first 3 companies)
• 9 companies queued for next run

Next scheduled run: 2026-04-05 10:00 UTC
Trigger manual run: `curl -X POST https://ecas-scraper-production.up.railway.app/api/enrich-and-enroll -d '{"company_filter": "Quanta Services", "min_heat": 0}'`
```

---

## Error Classification Taxonomy

Every API error in the pipeline maps to one of these categories:

```python
class ErrorClassifier:
    """Classify any exception into a retry strategy."""

    @staticmethod
    def classify(error: Exception, response=None) -> str:
        status = getattr(response, 'status_code', None) if response else None

        # Rate limiting
        if status == 429 or "rate limit" in str(error).lower():
            return "rate_limit"  # → wait Retry-After, retry

        # Auth / credentials
        if status in (401, 403) or "unauthorized" in str(error).lower():
            return "auth"  # → refresh key from Doppler, retry once

        # Payment / credits
        if status == 402 or "payment" in str(error).lower():
            return "credits_exhausted"  # → alert, switch to fallback provider

        # Server errors (transient)
        if status in (500, 502, 503, 504):
            return "transient"  # → exponential backoff, retry

        # Timeout
        if isinstance(error, (TimeoutError, requests.Timeout)):
            return "timeout"  # → increase timeout, retry

        # Connection
        if isinstance(error, (ConnectionError, requests.ConnectionError)):
            return "connection"  # → backoff, retry

        # Client errors (permanent)
        if status and 400 <= status < 500:
            return "permanent"  # → don't retry, log and skip

        # Unknown
        return "unknown"  # → retry once, then escalate
```

---

## Credential Refresh from Doppler

```python
import subprocess

def refresh_credential_from_doppler(service: str) -> bool:
    """
    Pull a fresh API key from Doppler when auth fails.
    Maps service name → Doppler secret name.
    """
    KEY_MAP = {
        "apollo_org": "APOLLO_API_KEY",
        "apollo_people": "APOLLO_API_KEY",
        "apollo_reveal": "APOLLO_API_KEY",
        "findymail": "FINDYMAIL_API_KEY",
        "smartlead_enroll": "SMARTLEAD_API_KEY",
        "airtable": "AIRTABLE_API_KEY",
    }

    secret_name = KEY_MAP.get(service)
    if not secret_name:
        return False

    try:
        result = subprocess.run(
            ["doppler", "secrets", "get", secret_name,
             "--project", "ent-agency-automation", "--config", "dev", "--plain"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            new_key = result.stdout.strip()
            os.environ[secret_name] = new_key
            # Reload config module
            import importlib
            import config
            importlib.reload(config)
            logger.info(f"[AutoFix] Refreshed {secret_name} from Doppler")
            return True
    except Exception as e:
        logger.warning(f"[AutoFix] Doppler refresh failed for {secret_name}: {e}")

    return False
```

---

## Pipeline Orchestrator (Ties Everything Together)

```python
def run_pipeline(
    min_heat: float = 50.0,
    company_filter: str = None,
    dry_run: bool = False,
) -> dict:
    """
    Full pipeline orchestrator with self-healing.
    Called by: scheduler cron, /api/enrich-and-enroll endpoint, hot signal handler, CLI.
    """
    circuit_breaker = CircuitBreaker(threshold=5, cooldown_seconds=300)
    results = new_results_dict(dry_run)

    # ── Phase A: Pre-Flight ──────────────────────────────────────
    preflight = pre_flight_check()
    if preflight["status"] == "blocked":
        return {**results, "status": "blocked", "reason": "Pre-flight check failed"}

    degraded_services = set()
    if preflight["status"] == "degraded":
        degraded_services = {k for k, v in preflight["checks"].items() if not v["healthy"]}

    # ── Stage 1: Get Projects ────────────────────────────────────
    projects = get_qualified_projects(min_heat, company_filter)
    if not projects:
        return {**results, "status": "no_projects"}

    # Filter out companies that already have contacts (dedup)
    projects = [p for p in projects if not has_existing_contacts(p)]
    results["companies_qualified"] = len(projects)

    if dry_run:
        return {**results, "status": "dry_run"}

    # ── Stage 2: Enrichment (parallel across companies) ──────────
    contacts, enrich_errors = enrich_batch(
        projects,
        workers=4 if "apollo" not in degraded_services else 1,
        circuit_breaker=circuit_breaker,
        degraded_services=degraded_services,
    )
    results["contacts_found"] = len(contacts)
    results["errors"].extend(enrich_errors)

    if not contacts:
        if enrich_errors:
            diagnose_and_escalate(
                error=Exception(f"{len(enrich_errors)} enrichment failures"),
                context={"stage": "enrichment", "errors": enrich_errors},
                recent_logs=get_recent_logs(50),
            )
        return {**results, "status": "no_contacts_found"}

    # ── Stage 3: Personalization (future — skip in Phase 1) ─────
    # contacts = personalize_batch(contacts, workers=8)

    # ── Stage 4: Delivery (sequential with rate limiting) ────────
    delivery = deliver_batch(contacts, circuit_breaker=circuit_breaker)
    results["contacts_enrolled"] = delivery["enrolled"]
    results["skipped"] = delivery["skipped"]
    results["campaigns"] = delivery["campaigns"]
    results["errors"].extend(delivery["errors"])

    # ── Post-Run: Summary ────────────────────────────────────────
    results["status"] = "complete"
    post_summary(results)

    # If there were errors but pipeline partially succeeded, still diagnose
    if results["errors"]:
        diagnose_and_escalate(
            error=Exception(f"{len(results['errors'])} partial failures"),
            context={"stage": "summary", "errors": results["errors"]},
            recent_logs=get_recent_logs(30),
        )

    return results
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `enrichment/pipeline.py` | Main orchestrator — `run_pipeline()` + all stages |
| `enrichment/retry.py` | `retry_with_fallback()`, `CircuitBreaker`, `ErrorClassifier` |
| `enrichment/health.py` | `pre_flight_check()`, individual health checks |
| `enrichment/diagnosis.py` | `diagnose_and_escalate()`, `diagnose_preflight_failures()`, Slack formatting |
| `enrichment/credentials.py` | `refresh_credential_from_doppler()` |
| `api/main.py` (modify) | Add `POST /api/enrich-and-enroll` endpoint |
| `scheduler.py` (modify) | Replace 2 cron jobs with 1, update hot signal + budget window handlers |

---

## Execution Model Summary

```
Pattern: PIPELINE (6 stages) with FAN-OUT per stage
Parallelism:
  - Stage 1 (signals): 7 sources in parallel (existing)
  - Stage 2 (enrichment): 4 companies in parallel, sequential within each
  - Stage 3 (personalization): 8 contacts in parallel (future)
  - Stage 4 (delivery): sequential with 0.5s delay
  - Stage 5 (responses): event-driven (n8n webhook)
Workers: 4 default (enrichment), 8 for I/O-bound LLM calls (personalization)
Bottlenecks: Smartlead enrollment must be sequential (API design)
Done signal: results dict returned with status + counts + errors
Self-healing: pre-flight checks → retry with backoff → credential refresh → circuit breaker → LLM diagnosis → smart Slack alert
```

---

## Industry Plug-and-Play Config

The entire pipeline is parameterized. Swap config to run for any vertical:

```python
# Each vertical is just a different config dict
VERTICALS = {
    "ecas_epc": {
        "airtable_base": "appoi8SzEJY8in57x",
        "icp_titles": ["VP Operations", "VP Business Development", "President", "CEO", "COO"],
        "sector_campaign_map": {"Power & Grid Infrastructure": "3005694", ...},
        "min_heat": 50.0,
        "slack_channel": "#ecas-signals",
    },
    "ent_brands": {
        "airtable_base": "app9fVT4bBMHlCf2C",
        "icp_titles": ["VP Marketing", "CMO", "Head of Influencer", "Brand Manager"],
        "sector_campaign_map": {},  # TBD
        "min_heat": 0,  # different scoring model
        "slack_channel": "#ent-outbound",
    },
    "dfr_vendors": {
        "airtable_base": "appoi8SzEJY8in57x",
        "icp_titles": ["VP Sales", "VP Government Sales", "Head of Public Safety Sales"],
        "sector_campaign_map": {"Drone & Public Safety Technology": "3103531"},
        "min_heat": 0,
        "slack_channel": "#ecas-signals",
    },
}

# Run for any vertical:
run_pipeline(vertical="ecas_epc")
run_pipeline(vertical="dfr_vendors", company_filter="BRINC")
```
