# ECAS — Enterprise Contract Acquisition System

## What This Is
Signal-driven enterprise contract acquisition for mid-tier EPCs across 5 sectors ($20M–$300M).
Positioning: "We get you on the short-list before the RFP drops."
Brand: **ContractMotion.com**

## Status: LIVE (2026-04-29)
- 12/14 ContractMotion inboxes warming at 99–100% reputation
- 2 SMTP failures need new Google app passwords: `karlee@contractmotionai.com`, `ethan.atchley@contractmotion.com`
- 365 leads/run from USASpending + SAM.gov across 5 sectors
- **Bridge LIVE (2026-05-25):** `populate_projects.py` moves `epc_company_leads` (Supabase) → Airtable `projects`. Wired as scheduler job `h1b_pipeline` (daily 4am UTC: discover H-1B leads → bridge all sources → projects, before ICP hunt 5am + enrichment 10am). Also CLI: `--source h1b_lca|all`, `--min-score`, `--dry-run`. Trigger on demand: `POST /admin/run/h1b_pipeline`.

## Code & Deploy
- **Local:** `~/projects/ECAS/`
- **GitHub:** `https://github.com/Entmarketingteam/ECAS`
- **Railway:** `https://ecas-scraper-production.up.railway.app`
  - Project ID: `48f4f546-d55a-4ceb-a34c-f46b8af4b10f`
- **Architecture:** Pure Python — FastAPI + APScheduler (13 jobs)
- **Dockerfile:** `python:3.11-slim` + `PLAYWRIGHT_BROWSERS_PATH=/ms-playwright`
- **Run locally:** `doppler run --project ecas --config dev -- python3 -m uvicorn api.main:app`

## AI Runtime
- **Primary LLM:** Claude (`claude-3-5-sonnet-20241022`) via `ANTHROPIC_API_KEY` in Doppler
- **Model config:** `config.py → CLAUDE_MODEL`
- **Gemini CLI:** Supported via superpowers plugin (`gemini-extension.json` → reads `GEMINI.md` as context)
- **MCP Connectors active in Claude Code:**
  - `playwright` — browser automation for scrapers
  - `google-workspace` — Gmail/Drive/Sheets access
  - `notebooklm-mcp` — Gemini-powered research notebook (use for signal research + doc ingestion)

## Airtable (Base: `appoi8SzEJY8in57x` — ContractMotion CRM)
| Table | ID | Purpose |
|-------|-----|---------|
| `signals_raw` | `tblAFJnXToLTKeaNU` | Raw signal ingestion |
| `projects` | `tbloen0rEkHttejnC` | ICP companies in pipeline |
| `contacts` | `tblPBvTBuhwlS8AnS` | Decision-makers |
| `deals` | `tbl2ZkD20cf6zMxJj` | Deal tracking |

**Field name gotchas:**
- contacts: `company_name` (NOT `company`), `confidence_score` (NOT `heat_score`)
- projects: `owner_company` (NOT `company_name`)
- `outreach_status` values: `pending_review | approved | do_not_contact | in_sequence | replied | meeting_booked | not_interested | unsubscribed`
- projects singleSelect: `stage` = `Identified | Researching | Outreach | Meeting Set | Proposal Sent | Negotiating | Won | Lost | Dormant`
- projects singleSelect: `priority` = `High | Medium | Low`, `icp_fit` = `Strong | Moderate | Weak | Unknown`

## Supabase Tables
| Table | Purpose | Unique Key |
|-------|---------|-----------|
| `epc_company_leads` | EPC scraper output (epc_lead_engine.py) | (domain, source) |
| `gmaps_companies` | Google Maps discovered companies | place_id |
| `gmaps_contacts` | Decision-makers from Gmaps enrichment | email |
| `enrollment_log` | Audit trail — all Smartlead enrollments | — |
| `verification_review_queue` | Human review queue (REVIEW/HOLD leads) | (company_name, domain) |

## Smartlead Campaigns
| Sector | Campaign ID | Status |
|--------|-------------|--------|
| Power & Grid Infrastructure | `3005694` | LIVE — 60 leads |
| Data Center & AI Infrastructure | `3040599` | LIVE |
| Water & Wastewater Infrastructure | `3040600` | LIVE |
| Industrial & Manufacturing Facilities | `3040601` | LIVE |
| Defense & Federal Infrastructure | `3095136` | LIVE |
| Drone & Public Safety Tech | `3103531` | LIVE (2026-03-30) |

**Sector → campaign mapping lives in:** `config.py` lines 35–47 and `enroll_contacts_to_campaigns.py` lines 16–22

**Smartlead API gotchas:**
- Leads endpoint: `GET /campaigns/{id}/leads?api_key=KEY` — NO `limit`/`offset` params → 400 error
- Warmup enable: `POST /email-accounts/{id}/warmup`
- Base URL: `https://server.smartlead.ai/api/v1`

## Sending Domains & Inbox Warmup (2026-04-29)
| Domain | Inboxes | Status |
|--------|---------|--------|
| aicontractmotion.com | ethan@, ethan.atchley@, karlee@ | ✅ ACTIVE 99–100% |
| getcontractmotion.com | ethan@, ethan.atchley@, karlee@ | ✅ ACTIVE 99–100% |
| usecontractmotion.com | ethan@, ethan.atchley@, karlee@ | ✅ ACTIVE 99–100% |
| contractmotionai.com | ethan@, ethan.atchley@ | ✅ ACTIVE 100% |
| contractmotionai.com | karlee@ | ⚠️ SMTP failure — needs new app password |
| contractmotion.com | ethan@, ethan.atchley@ | ethan@ ✅ / ethan.atchley@ ⚠️ SMTP failure |

**Fix SMTP failures:** Google Account → Security → App Passwords → create new → paste into Smartlead email account settings

## Pipeline Architecture

```
epc_lead_engine.py (5 sectors)
  │  Sources: USASpending, SAM.gov, associations, permits
  ▼
Supabase: epc_company_leads
  │
  ✓ BRIDGE: populate_projects.py (built 2026-05-25)
  │  (reads epc_company_leads, upserts to Airtable projects; tier→priority/icp_fit)
  ▼
Airtable: projects  ◄── also populated by scheduler.job_populate_projects()
  │                      (via Apollo ICP hunt from sector heat scores)
  ▼
lead_priority_scoring.py
  │  Scores: company_size + sector + icp_fit → priority (High/Medium/Low)
  ▼
enrichment/pipeline.py  (daily 10am UTC, 4 workers)
  │  Apollo org search → Findymail email → Smartlead enrollment → Airtable sync
  ▼
Smartlead campaigns (sector-routed via enroll_contacts_to_campaigns.py)
```

**Verification path (for epc_lead_engine CSV output):**
```
signals/output/epc_leads_{date}.csv
  → verification/pipeline.py (5-stage: entity resolve → verify → contact verify → content gen → route)
  → AUTO (score ≥70) / REVIEW (score 40–69) / HOLD (score <40)
  → Supabase: verification_review_queue
```

## Signal Sources by Sector
| Sector | NAICS | Key Sources |
|--------|-------|-------------|
| Water & Wastewater | 236220, 237110, 237120, 562212, 562219 | USASpending, SAM.gov, WEFTEC, AWWA, CWSRF, ACEC |
| Data Center & AI | 236210, 237990, 238210, 541512, 541519 | USASpending, SAM.gov, AFCOM, 7x24, BICSI, NECA, permits |
| Power & Grid | 237130, 237990, 238210, 221121, 221122, 221113, 221114 | USASpending, SAM.gov, NEMA, FERC/EIA, AGC, ERCOT queue |
| Industrial & Manufacturing | 236210, 237990, 238220, 238910, 541330, 325110, 324110 | USASpending, SAM.gov, SMACNA, ABC, NFPA, AIChE, TCEQ |
| Defense & Nuclear | 237990, 236210, 541330, 541712, 541715, 562910, 336414 | USASpending, SAM.gov, DOE, NRC, SAME |

**Signal quality tiers:**
- USASpending contract award = company won federal contract → **hottest signal**
- SAM.gov registration = registered to bid → **medium signal**
- Association membership = operates in sector → **cold signal**

## EPC Lead Engine (signals/epc_lead_engine.py)
```bash
# Run all sectors
doppler run --project ecas --config dev -- python3 signals/epc_lead_engine.py --sector all

# Single sector
doppler run --project ecas --config dev -- python3 signals/epc_lead_engine.py --sector water|dc|power|industrial|defense

# Dry run
doppler run --project ecas --config dev -- python3 signals/epc_lead_engine.py --dry-run
```
Output: SQLite `database/tracker.db` (dedup) + Supabase `epc_company_leads` + `signals/output/epc_leads_{date}.csv`

## Admin API Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Service status |
| GET | `/admin/status` | Pipeline + Airtable table counts |
| POST | `/admin/run/{job_id}` | Trigger any scheduled job |
| GET | `/admin/signals` | Recent signals from Airtable |
| GET | `/admin/scores` | Current sector heat scores |
| POST | `/admin/enroll` | Manually enroll lead in Smartlead |
| POST | `/admin/generate-sequence` | Generate cold email sequence via Claude |
| POST | `/scrape-pdf` | PDF extraction via Claude |
| POST | `/scrape-page` | Playwright page scrape |

## Job IDs (13)
`politician_trades`, `sec_13f`, `gov_contracts`, `ferc_poller`, `rss_feeds`,
`claude_extraction`, `sector_scoring`, `enrichment`, `smartlead`,
`weekly_digest`, `earnings_transcripts`, `budget_window_monitor`, `populate_projects`,
`h1b_pipeline` (daily 4am — H-1B discover + Supabase→projects bridge)

## Secrets (Doppler: `ecas/dev`)
**Active:**
`APOLLO_API_KEY`, `ANTHROPIC_API_KEY`, `SMARTLEAD_API_KEY`, `AIRTABLE_API_KEY`,
`FINDYMAIL_API_KEY`, `SLACK_ACCESS_TOKEN`, `EIA_API_KEY`, `SAM_GOV_API_KEY`,
`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `CENSUS_API_KEY`, `BLS_API_KEY`,
`CONGRESS_API_KEY`, `RAPIDAPI_KEY`, `BLITZ_API_KEY`, `PROSPEO_API_KEY`,
`MILLIONVERIFIER_API_KEY`

**Placeholders (not yet set — cause failures):**
`PROXYCURL_API_KEY`, `FULLENRICH_API_KEY`, `FMP_API_KEY`, `CLOSE_CRM_API_KEY`, `REDUCTO_API_KEY`

**Inbox warmup secrets:**
`INBOX_ETHAN_AICONTRACTMOTION_PASS`, `INBOX_ETHAN_ATCHLEY_AICONTRACTMOTION_PASS`,
`INBOX_KARLEE_AICONTRACTMOTION_PASS`, `INBOX_ETHAN_CONTRACTMOTIONAI_PASS`

## Claude LLM Usage in Codebase
Files that call Anthropic API:
- `intelligence/claude_extractor.py` — extract structured JSON from raw signals
- `enrichment/diagnosis.py` — pipeline failure diagnostics
- `enrichment/health.py` — pre-flight health check analysis
- `outreach/sequence_generator.py` — cold email sequence generation
- `verification/content_qa.py` — content generation + claim verification
- `verification/entity_resolver.py` — company name disambiguation
- `verification/signal_verifier.py` — signal content verification
- `api/main.py` — `/scrape-pdf` and `/admin/generate-sequence` endpoints
- `contractor/pipeline/copy_generator.py` — contractor outreach copy

## Apollo API Usage
- Use `/mixed_people/api_search` NOT `/people/search` (deprecated)
- 3-step: `/organizations/search` → org ID → `/mixed_people/api_search` by org ID → `/people/bulk_match` to reveal emails

## n8n Workflows (Cloud — ALL ACTIVE)
- `g4g5Eom2pQV8ybHR` — ECAS 01 FERC Signal Poller (every 6h)
- `Kg0xi3Ldem59lYuF` — ECAS 02 PJM Queue Poller (Mon 7am)
- `0DmEuRRQqcLXCUUY` — ECAS 03 RSS Aggregator (every 15min)
- `8nQHnHFmdnH8lWmL` — ECAS 05 Signal Processor / Claude Extraction (every 15min)
- `kMssKmg50794zXl8` — ECAS 07 Contact Enricher (every 5min poll)
- `contract-motion-signal-audit` — **NEW** Site Webhook Handler (`n8n-webhook-handler.json`)
- `contract-motion-ferc-sniper` — **NEW** FERC/PJM Project Sniper (`n8n-ferc-sniper.json`)
- n8n creds: Airtable `dAoeOLbTnBUK1gTy`, Anthropic `MwxIqQP3l6cUcwcZ`, Slack `EMdoV2Sq9neZV1Tn`

## Niche Intelligence Lab (intelligence/niches/)
Recent 17-part deep-dives and ColdIQ mapping completed for:
- Document Shredding Services
- Janitorial Services (High-Rise)
- Restaurant Equipment Sales
- Retirement Planning Services
- 401(k) Plan Advisory
- Tax Planning & Strategy
- ... (20+ total niches refactored to ContractMotion identity)

## Marketing Assets
- **Website:** https://contractmotion.com ✅ LIVE
- **Smartlead Campaign 3040599:** Data Center & AI Infrastructure ✅ 6-email sequence updated
- **Lead magnet:** "HIPAA Document Disposal Gap Checklist" (docs/hipaa-document-disposal-gap-checklist.md)
- **Lead magnet:** "2026 Retail Anchor Vacancy & NNN Recovery Map" (docs/2026-retail-anchor-vacancy-nnn-recovery-map.md)
- **ABM Plan:** High-Rise Janitorial Infrastructure (intelligence/niches/janitorial-services-high-rise/ABM_Plan.md)
