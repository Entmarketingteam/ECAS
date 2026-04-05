# Plan: ECAS Lead Enrichment Pipeline — Cost-Optimized Architecture
**Date:** 2026-04-04
**Status:** Ready to implement
**Clay:** Deferred. Workspace: `https://app.clay.com/workspaces/68018/workbooks/wb_0tczkvnNDXwGcbGPB9i`

## The Problem with n8n-Heavy Pipelines

n8n cloud charges per execution. Each workflow run with loops, batches, and HTTP nodes burns executions fast:
- 10 companies × (3 Apollo calls + 2 Findymail calls + 1 Smartlead push + 1 Airtable write) = **70+ node executions per run**
- At scale (50 companies/day): **350+ executions/day = 10K+/month just for enrichment**
- Same problem with Zapier/Make — all charge per operation

Meanwhile: **Railway is flat-rate** (~$5-20/mo). The ECAS server already runs 24/7 with all API keys, all logic, and all endpoints. Every API call made from Railway costs $0 in orchestration fees.

## The Architecture: Railway Does the Work, n8n Just Triggers

```
┌─────────────────────────────────────────────────────────────────┐
│                     COST-OPTIMIZED ARCHITECTURE                  │
│                                                                  │
│  ┌──────────────┐     1 HTTP call      ┌─────────────────────┐  │
│  │   TRIGGERS    │────────────────────►│  ECAS Railway API    │  │
│  │              │                      │  (flat-rate compute) │  │
│  │ • n8n cron   │                      │                     │  │
│  │ • Slack bot  │  POST /api/enrich    │ Apollo waterfall    │  │
│  │ • Hot signal │  ─────────────────►  │ Findymail fallback  │  │
│  │ • Budget win │                      │ Findymail verify    │  │
│  │ • Manual CLI │  POST /api/enroll    │ Smartlead push      │  │
│  │ • Agent srv  │  ─────────────────►  │ Airtable sync       │  │
│  │ • Webhook    │                      │ Slack notification  │  │
│  └──────────────┘                      └─────────────────────┘  │
│                                                                  │
│  n8n: 1 execution (trigger + 1 HTTP call) = ~30 executions/mo   │
│  vs: 70+ executions per run in n8n-heavy approach               │
│                                                                  │
│  SAVINGS AT SCALE:                                               │
│  10 companies/day × 30 days = 300 runs                           │
│  n8n-heavy: 300 × 70 nodes = 21,000 executions/mo               │
│  This approach: 300 × 1 trigger = 300 executions/mo (98% less)  │
└─────────────────────────────────────────────────────────────────┘
```

## What We're Building

**One new FastAPI endpoint** on the existing ECAS Railway server: `POST /api/enrich-and-enroll`

This endpoint does everything in one atomic call:
1. Pulls qualified projects from Airtable (or accepts a company list in the request body)
2. Runs Apollo waterfall (org search → people search → bulk match)
3. Runs Findymail fallback + verify
4. Pushes verified leads to correct Smartlead campaign
5. Upserts contacts in Airtable
6. Posts summary to Slack
7. Returns results JSON

**Any system can trigger it:** n8n cron (1 execution), Slack bot, Claude agent, `curl`, another Railway service, or the existing Python scheduler. No vendor lock-in to any orchestration tool.

## What "Done" Looks Like
- [ ] `POST /api/enrich-and-enroll` endpoint live on Railway
- [ ] Accepts optional body: `{ "min_heat": 50, "company_filter": "Quanta Services", "dry_run": false }`
- [ ] Defaults: processes all projects with confidence_score >= 50, no company filter, not dry run
- [ ] Returns: `{ "companies_processed": 5, "contacts_found": 18, "contacts_verified": 12, "contacts_enrolled": 12, "campaigns": {"3005694": 4, "3040599": 8}, "errors": [] }`
- [ ] n8n workflow: Schedule Trigger → HTTP Request to endpoint → done (2 nodes)
- [ ] Existing scheduler jobs (`enrichment` + `smartlead`) refactored to call same endpoint
- [ ] Hot signal + budget window handlers call same endpoint
- [ ] Slack summary posted on every run

## Current State vs. Target

### Current (3 separate code paths doing the same thing)
```
Path 1: scheduler.py job_enrichment() → clay_enricher.run_enricher()
          + 30 min later: job_smartlead_enrollment() → smartlead.enroll_airtable_contacts()

Path 2: scheduler.py _check_hot_signal_threshold() → smartlead.enroll_airtable_contacts()

Path 3: scheduler.py job_budget_window_monitor() → smartlead.enroll_airtable_contacts()
```
**Problem:** 3 paths, 2-step process (enrich then enroll separately), duplicated logic, 30-min gap.

### Target (1 endpoint, all paths call it)
```
POST /api/enrich-and-enroll  ← n8n cron, hot signal, budget window, manual, agent, CLI
  → atomic: enrich + verify + enroll + sync + notify
```
**Benefit:** One code path. No gap. Any trigger. Zero orchestration cost.

## Implementation Steps

### Step 1 — New Endpoint: `POST /api/enrich-and-enroll`
**File:** `api/main.py`
**Owner:** Claude Code

```python
class EnrichAndEnrollRequest(BaseModel):
    min_heat: float = 50.0
    company_filter: str | None = None
    dry_run: bool = False
    titles: list[str] | None = None  # override ICP titles

class EnrichAndEnrollResponse(BaseModel):
    companies_processed: int
    contacts_found: int
    contacts_verified: int
    contacts_enrolled: int
    campaigns: dict[str, int]  # campaign_id → count
    skipped: int
    errors: list[str]
    dry_run: bool


@app.post("/api/enrich-and-enroll")
async def enrich_and_enroll(req: EnrichAndEnrollRequest, background_tasks: BackgroundTasks):
    """
    Atomic enrichment + enrollment pipeline.
    Finds contacts at qualified companies, verifies emails, enrolls in Smartlead, syncs to Airtable.
    """
    # Run in background so the HTTP response returns immediately
    # (enrichment for 10+ companies can take 2-5 minutes)
    background_tasks.add_task(_run_enrich_and_enroll, req)
    return {"status": "started", "message": "Pipeline running in background. Results posted to Slack."}
```

### Step 2 — Core Pipeline Function
**File:** `enrichment/pipeline.py` (NEW — clean separation from legacy `clay_enricher.py`)
**Owner:** Claude Code

```python
"""
enrichment/pipeline.py
Atomic enrichment + enrollment pipeline.
Apollo → Findymail → Smartlead → Airtable in one pass.
"""

def run_pipeline(
    min_heat: float = 50.0,
    company_filter: str | None = None,
    dry_run: bool = False,
    titles: list[str] | None = None,
) -> dict:
    """
    Single function that does everything:
    1. Get qualified projects from Airtable
    2. Apollo enrichment (org → people → reveal)
    3. Findymail fallback + verify
    4. Smartlead enrollment (sector → campaign routing)
    5. Airtable contact upsert
    6. Slack summary
    Returns results dict.
    """
    from storage.airtable import get_client
    from enrichment.clay_enricher import find_contacts_apollo
    from outreach.smartlead import enroll_lead, _resolve_campaign_id
    from config import SLACK_ACCESS_TOKEN

    at = get_client()
    results = {
        "companies_processed": 0,
        "contacts_found": 0,
        "contacts_verified": 0,
        "contacts_enrolled": 0,
        "campaigns": {},
        "skipped": 0,
        "errors": [],
        "dry_run": dry_run,
    }

    # 1. Get projects
    formula = f"AND({{confidence_score}}>={min_heat}, {{owner_company}}!='')"
    if company_filter:
        formula = f"AND({{confidence_score}}>={min_heat}, {{owner_company}}='{company_filter}')"

    projects = at._get("projects", {"filterByFormula": formula, "maxRecords": 50})

    for project in projects:
        fields = project.get("fields", {})
        company = fields.get("owner_company", "")
        record_id = project.get("id", "")
        if not company:
            continue

        # Parse sector from positioning_notes JSON
        sector = "Power & Grid Infrastructure"
        raw_notes = fields.get("positioning_notes", "")
        if raw_notes:
            try:
                import json
                notes_data = json.loads(raw_notes)
                sector = notes_data.get("sector", sector)
            except (json.JSONDecodeError, TypeError):
                pass

        heat = float(fields.get("confidence_score", 0))

        # Skip if already has contacts
        existing = at.get_contacts_by_company(company)
        if existing:
            results["skipped"] += 1
            continue

        results["companies_processed"] += 1

        # 2-3. Apollo enrichment + Findymail fallback + verify
        # (find_contacts_apollo already does the full waterfall)
        contacts = find_contacts_apollo(company, titles=titles)
        results["contacts_found"] += len(contacts)
        results["contacts_verified"] += len(contacts)  # all returned contacts are pre-verified

        if dry_run:
            continue

        # 4-5. Enroll each contact
        campaign_id = _resolve_campaign_id(sector)
        for contact in contacts:
            email = contact.get("email", "")
            if not email:
                continue

            # Smartlead enrollment
            enroll_result = enroll_lead(
                email=email,
                first_name=contact.get("first_name", ""),
                last_name=contact.get("last_name", ""),
                company=company,
                title=contact.get("title", ""),
                sector=sector,
                heat_score=heat,
                campaign_id=campaign_id,
            )

            if enroll_result["status"] == "enrolled":
                results["contacts_enrolled"] += 1
                results["campaigns"][campaign_id] = results["campaigns"].get(campaign_id, 0) + 1

                # Airtable upsert
                at.upsert_contact(
                    email=email,
                    first_name=contact.get("first_name", ""),
                    last_name=contact.get("last_name", ""),
                    title=contact.get("title", ""),
                    company=company,
                    linkedin_url=contact.get("linkedin_url", ""),
                    phone=contact.get("phone", ""),
                    outreach_status="in_sequence",
                    notes=f"Source: {contact.get('source', 'unknown')} | Pipeline | {datetime.utcnow().date()} | Campaign {campaign_id}",
                )
                if record_id:
                    at.link_contact_to_project(record_id, contact_record_id)

            elif enroll_result["status"] == "error":
                results["errors"].append(f"{email}: {enroll_result.get('reason', 'unknown')}")

    # 6. Slack summary
    if SLACK_ACCESS_TOKEN and not dry_run and results["contacts_enrolled"] > 0:
        _post_slack_summary(results)

    return results
```

### Step 3 — Refactor Existing Scheduler to Use Pipeline
**File:** `scheduler.py`
**Owner:** Claude Code

```python
# Replace job_enrichment() + job_smartlead_enrollment() with one job:
def job_enrich_and_enroll():
    """Atomic enrichment + enrollment. Replaces separate enrichment and smartlead jobs."""
    logger.info("=== JOB: Enrich & Enroll Pipeline ===")
    try:
        from enrichment.pipeline import run_pipeline
        result = run_pipeline(min_heat=50.0)
        logger.info(f"Pipeline done: {result}")
    except Exception as e:
        logger.error(f"Pipeline job failed: {e}", exc_info=True)

# Replace the two cron jobs with one:
# OLD:
#   scheduler.add_job(job_enrichment, CronTrigger(hour=10, minute=0), id="enrichment")
#   scheduler.add_job(job_smartlead_enrollment, CronTrigger(hour=10, minute=30), id="smartlead")
# NEW:
scheduler.add_job(job_enrich_and_enroll, CronTrigger(hour=10, minute=0), id="enrich_and_enroll")

# Hot signal handler — replace inline enrollment with pipeline call:
def _check_hot_signal_threshold(projects):
    # ... existing hot signal detection logic ...
    # Replace:
    #   from outreach.smartlead import enroll_airtable_contacts
    #   result = enroll_airtable_contacts(min_heat_score=_HOT_SIGNAL_THRESHOLD, company_filter=company)
    # With:
    from enrichment.pipeline import run_pipeline
    result = run_pipeline(min_heat=0.0, company_filter=company)

# Budget window handler — same refactor
```

### Step 4 — n8n Workflow (Minimal — 2 Nodes)
**Owner:** Claude Code

Only needed if you want n8n as an additional trigger alongside the Python cron.

```
[Schedule Trigger] ──► [HTTP Request: POST to Railway /api/enrich-and-enroll]
   daily 10am UTC         URL: https://ecas-scraper-production.up.railway.app/api/enrich-and-enroll
                          Body: { "min_heat": 50.0 }
                          (Railway handles everything else — Slack notification included)
```

**That's it. 2 nodes. 1 execution/day. ~30 executions/month.**

Or skip n8n entirely — the Python scheduler already runs the cron.

### Step 5 — Direct Webhook Access (No Orchestrator Needed)
**Owner:** Any system

Any system can call the endpoint directly:

```bash
# Manual CLI
curl -X POST https://ecas-scraper-production.up.railway.app/api/enrich-and-enroll \
  -H "Content-Type: application/json" \
  -d '{"min_heat": 50}'

# Single company (hot signal)
curl -X POST https://ecas-scraper-production.up.railway.app/api/enrich-and-enroll \
  -H "Content-Type: application/json" \
  -d '{"company_filter": "Quanta Services", "min_heat": 0}'

# Dry run (test without enrolling)
curl -X POST https://ecas-scraper-production.up.railway.app/api/enrich-and-enroll \
  -H "Content-Type: application/json" \
  -d '{"min_heat": 50, "dry_run": true}'
```

**Systems that can trigger without any orchestrator:**
| Trigger | How |
|---------|-----|
| Python scheduler (existing) | Direct function call — already on same server |
| Slack bot | POST from ent-slack-bot → Railway endpoint |
| Agent server | POST from agent.entagency.co → Railway endpoint |
| n8n (optional) | 2-node workflow: cron → HTTP Request |
| Claude Code CLI | `curl` command |
| Hot signals | Python scheduler calls `run_pipeline()` directly |
| Budget window | Python scheduler calls `run_pipeline()` directly |
| Morning brief agent | Can trigger enrichment as part of daily brief |

## Cost Comparison

| Approach | Monthly Cost | Executions/Month | Vendor Lock-in |
|----------|-------------|-----------------|---------------|
| **n8n-heavy (70 nodes)** | $50+ (n8n Team plan) | 10K-21K | n8n |
| **Zapier equivalent** | $100-300+ | 10K-21K | Zapier |
| **Make equivalent** | $50-150 | 10K+ | Make |
| **Clay (Launch)** | $185 | N/A (credits) | Clay |
| **This approach (Railway)** | ~$5-20 (flat) | N/A (flat rate) | None |

**At 50 companies/day:** n8n-heavy = 105K executions/month. This approach = 30 (one daily trigger) or 0 (Python cron only).

## Scaling Path

```
TODAY (Phase 1):
  Python scheduler on Railway → run_pipeline() → done
  Cost: $0 new (Railway already paid)

TOMORROW (Phase 2 — more volume):
  Same endpoint, increase maxRecords from 50 → 500
  Add rate limiting (Apollo 100/min, Findymail 100/min)
  Cost: $0 new

LATER (Phase 3 — AI personalization):
  Add Claygent/Claude step inside pipeline: research + BLUF hook generation
  Still runs on Railway (flat rate)
  OR: upgrade Clay for their native AI if volume justifies $185/mo

SCALE (Phase 4 — multiple clients/verticals):
  Parameterize pipeline: different ICP titles, different campaign maps, different Airtable bases
  Same endpoint, different request bodies per client
  Deploy as a reusable microservice
```

## Files to Create/Modify

| File | Action | What Changes |
|------|--------|-------------|
| `enrichment/pipeline.py` | **CREATE** | Atomic pipeline function: enrich + verify + enroll + sync + notify |
| `api/main.py` | **MODIFY** | Add `POST /api/enrich-and-enroll` endpoint (~30 lines) |
| `scheduler.py` | **MODIFY** | Replace 2 cron jobs with 1. Refactor hot signal + budget window to use pipeline. |
| `CLAUDE.md` | **MODIFY** | Update pipeline docs, add endpoint reference |
| n8n workflow (optional) | **CREATE** | 2 nodes: Schedule → HTTP Request. Only if you want n8n as secondary trigger. |

## Edge Cases
- **Large batch (50+ companies):** Background task + Slack notification on completion. HTTP returns immediately.
- **Partial failure:** Pipeline continues on per-company errors. Errors collected in response `errors` array.
- **Concurrent calls:** Two triggers hit endpoint simultaneously → both run. Smartlead dedup prevents double-enrollment. Airtable upsert on email prevents duplicates.
- **Railway cold start:** First request after idle may take 2-3s. Background task handles this gracefully.
- **API rate limits:** Apollo 100/min, Findymail 100/min. At 10 contacts/company, 50 companies = ~200 calls over ~5 min. Well within limits.

## Testing
1. Deploy to Railway
2. `curl` with `dry_run: true` → verify project selection + contact discovery without enrolling
3. `curl` with single `company_filter` → verify full flow for one company
4. Check Smartlead dashboard → lead appears in correct campaign
5. Check Airtable → contact has `outreach_status="in_sequence"`
6. Check Slack → summary message posted
7. Run twice → confirm no duplicate enrollment

## Security
- Add API key auth to the endpoint: check `X-Api-Key` header against `AGENT_SERVER_API_KEY` from Doppler
- Or use the existing Railway internal networking (no public exposure needed if only triggered from Python scheduler)

## What This Replaces
- `job_enrichment()` scheduler cron (line 1056)
- `job_smartlead_enrollment()` scheduler cron (line 1057)
- The 30-minute gap between enrichment and enrollment
- 3 separate code paths for the same logic (daily batch, hot signal, budget window)
- Any need for n8n/Zapier/Make to run the heavy pipeline logic

## What This Doesn't Replace (Keep As-Is)
- Signal collection jobs (RSS, gov contracts, politician trades, SEC 13F) — these are lightweight and fine in the scheduler
- Claude extraction + sector scoring — same, lightweight
- ICP hunter / populate_projects — same
- Weekly digest — same
- The existing `clay_enricher.py` functions — `pipeline.py` calls them, doesn't duplicate them
