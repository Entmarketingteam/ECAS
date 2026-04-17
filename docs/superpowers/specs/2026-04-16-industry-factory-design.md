# Industry Factory — Zero-Debug, Hands-Off GTM Framework

**Date:** 2026-04-16
**Status:** Design approved — ready for implementation plan
**Scope:** Turn ECAS into a reusable Industry Factory that takes any industry as input (YAML) and runs end-to-end lead generation → enrichment → enrollment → follow-up automation with minimal human-in-the-loop.

---

## Problem

ECAS currently runs one hardcoded track (ContractMotion → EPCs). Adding a new industry requires edits across 4+ files, manual directory research, and custom scraper code. Running DC + Water today means seeding the Airtable `projects` table by hand, verifying campaigns exist in Smartlead, and watching for silent failures.

Adding a **second product track** (AI Automation for underserved blue-collar commercial services) makes the current approach untenable — it's a different ICP, different pitch, different scoring logic, different campaigns.

## Goal

One command, one YAML file → new industry fully live in ≤30 minutes of wall-clock time, ≤5 minutes of human attention. Zero debugging during first run. Silent failures surfaced loudly.

## Non-Goals

- Multi-client tenancy (different Airtable bases per client) — future Phase D
- LinkedIn multichannel outreach — future, after AI Automation track proves CAC
- Real-time (< 5 min) signal → send cycle — batch is fine
- Full SaaS productization — this is internal infrastructure

---

## Architecture

### Data flow

```
YAML (industries/<slug>.yaml)
  │
  ▼
industry_runner.py <slug> [--dry-run | --live]
  │
  ├─ pre_flight_check()  ◄── extended w/ Perplexity/Firecrawl/Browserbase/Wappalyzer probes
  │
  ├─ ensure_campaign_ready()  ◄── NEW: verify Smartlead campaign exists, active, has warmed sender
  │
  ├─ ensure_landing_page()  ◄── NEW: HEAD-check industry landing page URL exists
  │
  ├─ directory_finder.discover(industry)  ◄── NEW: Perplexity + Claude → URL list + classification
  │       │
  │       ▼
  │   universal_scraper.scrape(urls)  ◄── NEW: routes to Firecrawl/Airtop/Browserbase
  │       │
  │       ▼
  │   companies: list[dict]
  │
  ├─ tech_stack.enrich_batch(companies)  ◄── NEW: Wappalyzer + optional BuiltWith
  │
  ├─ lead_priority_scoring.score(companies, mode=yaml.scoring_mode)  ◄── EXTENDED: positive | negative_tech_stack | hybrid
  │
  ├─ populate_projects(scored_companies, sector=yaml.display_name)  ◄── writes Airtable projects
  │
  ├─ enrichment.pipeline.run_pipeline(company_filter=..., min_heat=yaml.min_heat)  ◄── EXISTING
  │
  ├─ signal_ttl_sweep()  ◄── NEW: drop leads older than yaml.signal_ttl_days
  │
  ├─ compliance_filter()  ◄── NEW: drop EU/CA unless explicit opt-in
  │
  └─ post_summary() → Slack #ecas-ops
```

### New modules (all under `~/Desktop/ECAS/`)

| Path | LOC est. | Purpose |
|---|---|---|
| `industries/<slug>.yaml` | per-file | Industry config (one per industry) |
| `industries/_schema.py` | ~80 | Pydantic schema for YAML validation |
| `industries/loader.py` | ~60 | YAML load + schema validate + defaults |
| `signals/industry_runner.py` | ~200 | Orchestrator entrypoint |
| `discovery/directory_finder.py` | ~180 | Perplexity/Claude → ranked URL list |
| `discovery/universal_scraper.py` | ~150 | Router: Firecrawl / Airtop / Browserbase |
| `enrichment/tech_stack.py` | ~200 | Wappalyzer + BuiltWith + SQLite cache |
| `enrichment/compliance.py` | ~60 | EU/CA filter before enrollment |
| `enrichment/signal_ttl.py` | ~50 | Expire stale leads from projects |
| `ops/campaign_guard.py` | ~120 | Auto-pause underperformers + warmup pool manager |
| `ops/deliverability_watchdog.py` | ~150 | GlockApps or Mailreach daily check |
| `ops/oauth_refresh.py` | ~80 | Gmail/GWS token refresh cron |
| `ops/health_dashboard.py` | ~200 | `GET /admin/dashboard` — single-URL status view |
| `lead_priority_scoring.py` | +~100 | Extend with `negative_tech_stack` mode |
| `enrichment/health.py` | +~60 | Add new pre-flight probes |
| `api/main.py` | +~40 | `POST /admin/run/industry/{slug}` + `GET /admin/dashboard` |

Total new code: ~1,700 LOC. Additions to existing files: ~200 LOC.

---

## YAML Schema

```yaml
# industries/<slug>.yaml
slug: commercial_roofing
display_name: "Commercial Roofing"
track: ai_automation          # or "contract_motion"
campaign_id: "TBD"            # Smartlead campaign ID

# ICP
revenue_range_m: [2, 25]
naics: ["238160"]
titles: [Owner, President, General Manager, Operations Manager]
states: [TX, FL, GA, NC, VA]

# Discovery
apollo_keywords:
  - commercial roofing contractor
  - flat roof contractor
  - industrial roofing
directory_seeds:              # optional — auto-discovered if empty
  - https://www.nrca.net/nrca-members
directory_auto_discovery: true

# Scoring
scoring_mode: negative_tech_stack   # positive | negative_tech_stack | hybrid
expected_stack_if_mature:
  fsm: [ServiceTitan, Jobber, HousecallPro, FieldEdge, Buildertrend]
  crm: [HubSpot, Salesforce, Zoho, Pipedrive]
  sms: [Twilio, Podium, Textline, ClickSend]
prioritize_when_missing: [fsm, sms]
min_heat: 30.0

# Guardrails
signal_ttl_days: 120
budget_cap_per_run: 50        # max companies enriched per run
landing_page_url: https://entagency.co/ai-automation/commercial-roofing

# Deliverability
sender_pool: ai_automation    # which warmed domain pool to rotate from
```

---

## Zero-Debug Guardrails (baked into framework)

### Pre-flight (extends existing `enrichment/health.py`)

Probes added — pipeline BLOCKS if any fail:
- `check_perplexity()` — if directory auto-discovery enabled
- `check_firecrawl()` — if any seed URL classified static
- `check_browserbase()` — if any URL classified JS-heavy
- `check_airtop()` — if any URL classified gated
- `check_wappalyzer()` — import succeeds, sample scan passes
- `check_landing_page()` — HEAD on `yaml.landing_page_url` returns 200
- `check_campaign_state()` — Smartlead campaign exists, is active, has ≥1 sending account
- `check_sender_pool()` — ≥1 warmed domain available in `yaml.sender_pool`
- `check_oauth_tokens()` — all OAuth tokens refreshed within last 24h

### Runtime gates

- **Dry-run mandatory for new industries** — first execution of any `slug` MUST be `--dry-run`. State stored in SQLite (`industries_dryrun_log`). `--live` errors if dry-run never succeeded.
- **Budget cap** — hard-stop after `yaml.budget_cap_per_run` companies enriched per invocation. Prevents Apollo credit blowout on bad keywords.
- **Discovery validation** — directory finder must return ≥3 URLs with confidence ≥0.7, else abort with Slack alert. No garbage-in.
- **Idempotent** — running the same industry twice in a day = no-op on overlap (existing dedup handles this).

### Post-run

- **Auto-pause floor** — daily cron: any campaign with <1% reply rate after 200 sends → auto-pause + Slack alert.
- **Deliverability watchdog** — daily seed-list test; Primary placement <70% → auto-pause + Slack alert.
- **Signal TTL sweep** — weekly: drop leads older than `yaml.signal_ttl_days` from active sequences.
- **OAuth refresh** — daily cron refreshes Gmail/GWS tokens before expiration.
- **Compliance filter** — EU/CA contacts dropped pre-enrollment unless explicit opt-in flag set.

### Observability

- **Health dashboard** — `GET /admin/dashboard` returns JSON + HTML view:
  - Every industry: last run timestamp, next scheduled run, lag, health
  - Every pre-flight probe: current status, last green timestamp
  - Every campaign: active/paused, send volume 7d, reply rate 7d, placement score
  - Every OAuth token: expiration, last refresh
  - Every Doppler key: present/missing
- **Slack digest** — `post_summary()` posts per-run to `#ecas-ops`. Morning Brief (`nG2yiF8Rv4kVYRLG`) rolls up daily.

---

## First-Touch Automation (prevents reply bottleneck)

Every sequence email template MUST include:
- Direct calendar booking link (Cal.com or GWS `calendar_events_insert` integration)
- Reply-to address matches sending account (avoid deliverability flags)

On positive reply (via Smartlead Signal Intelligence `4ZkYDJpqg5qBXdAW`):
- Auto-send follow-up with fresh calendar link if not already clicked
- Draft suggested reply → Slack button for one-click send
- Create Airtable deal with full context (campaign, sector, signal, contact history)
- Mark Airtable contact `outreach_status="meeting_requested"`

---

## Industries in Scope (this spec)

### ContractMotion Track
1. **Data Center & AI Infrastructure** — campaign `3040599`, positive scoring, existing YAML migration
2. **Water & Wastewater Infrastructure** — campaign `3040600`, positive scoring, existing YAML migration

### AI Automation Track (NEW)
3. **Commercial Roofing** — new campaign TBD, negative tech-stack scoring
4. **Commercial Glass Installation** — new campaign TBD, negative tech-stack scoring
5. **Commercial Cleaning & Janitorial** — new campaign TBD, negative tech-stack scoring

Each industry gets a YAML, Smartlead campaign with 5–6 email sequence, and landing page URL. Sequence copy drafted as part of build (not in this spec — handled by `email-sequences` skill).

---

## Execution Plan (Waves)

### Wave 1 — Foundation (parallel subagents, ~4 tasks)

1a. Industry YAML schema + loader (`industries/_schema.py`, `industries/loader.py`)
1b. Directory finder + universal scraper (`discovery/`)
1c. Tech-stack enrichment module (`enrichment/tech_stack.py`)
1d. Lead priority scoring extension (negative_tech_stack mode)

### Wave 2 — Orchestration + Guardrails (parallel, ~4 tasks)

2a. `signals/industry_runner.py` + API endpoint
2b. Pre-flight probe extensions
2c. `ops/campaign_guard.py` (auto-pause, warmup pool)
2d. `ops/health_dashboard.py` (+ `ops/oauth_refresh.py`, `enrichment/signal_ttl.py`, `enrichment/compliance.py`)

### Wave 3 — Industry Configs + Validation (parallel, ~5 tasks)

3a. `industries/data_center.yaml` + dry-run + live run
3b. `industries/water.yaml` + dry-run + live run
3c. `industries/commercial_roofing.yaml` + Smartlead campaign creation + sequence copy + landing page
3d. `industries/commercial_glass.yaml` + Smartlead campaign creation + sequence copy + landing page
3e. `industries/commercial_cleaning.yaml` + Smartlead campaign creation + sequence copy + landing page

### Wave 4 — Deliverability + Post-Launch (~2 tasks)

4a. Deliverability watchdog integration (GlockApps or Mailreach)
4b. Warmed domain pool provisioning (set up ≥2 idle warmed domains for AI Automation track)

---

## Success Criteria

Must all be true before this spec is closed:

1. **Zero-debug first run** — executing `POST /admin/run/industry/commercial_roofing` for the first time results in live leads enrolled in Smartlead, with no manual intervention, or fails loudly at a pre-flight gate with a Slack alert explaining exactly what's missing.
2. **Hands-off second industry** — adding a 6th industry takes ≤30 min wall-clock (most of that is Smartlead campaign setup) and ≤5 min of human work (write YAML, approve sequence draft).
3. **Silent failure detection** — every failure mode listed in the blind-spot audit has either a pre-flight probe or a post-run watchdog. No silent breaks.
4. **DC + Water live** — both ContractMotion industries successfully running through the framework, producing enrolled leads daily.
5. **AI Automation track validated** — Commercial Roofing campaign sends its first batch with tech-stack scoring applied; measurable reply rate within 14 days.

---

## Doppler Keys Required

Existing (verified present):
`APOLLO_API_KEY`, `FINDYMAIL_API_KEY`, `SMARTLEAD_API_KEY`, `AIRTABLE_API_KEY`, `ANTHROPIC_API_KEY`, `BROWSERBASE_API_KEY`, `BROWSERBASE_PROJECT_ID`, `FIRECRAWL_API_KEY`, `SLACK_ACCESS_TOKEN`

New (must add to Doppler `ecas/dev` before Wave 2 completes):
- `PERPLEXITY_API_KEY` (preferred) — directory auto-discovery. Fallback: Anthropic + Firecrawl search if absent.
- `AIRTOP_API_KEY` — gated-page scraping
- `GLOCKAPPS_API_KEY` or `MAILREACH_API_KEY` — deliverability watchdog
- `BUILTWITH_API_KEY` (optional) — deeper tech-stack data; Wappalyzer covers 90% without it

---

## Out of Scope (explicitly deferred)

- Multi-client tenancy (different Airtable base per client)
- LinkedIn multichannel (Heyreach/Expandi) — Wave 5+
- Closed-loop learning (outcomes → scoring weights) — Wave 5+
- Known-failure library (self-healing from failure fingerprints) — Wave 5+
- Lookalike expansion from closed deals — Wave 5+
- Objection auto-reply library — Wave 5+
- Invoice handoff on deal close — handled by existing `gmw6ERtrV3dfA7e5` workflow; wire-up deferred to Wave 5

---

## Branching Strategy

All work on branch `industry-factory`. Worktree at `~/Desktop/ECAS-industry-factory/` to avoid disrupting live ECAS deploys during build. Merge to `main` only after Wave 3 complete and DC + Water first-live-run validated.
