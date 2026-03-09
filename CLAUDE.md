# ECAS — Enterprise Contract Acquisition System

## What This Is
Signal-driven enterprise contract acquisition for mid-tier power/grid EPCs ($20M–$300M).
Positioning: "We get you on the short-list before the RFP drops."

## Status: FULLY LIVE ✅ (2026-03-05)
- 51 companies in projects, 118 contacts, 60 enrolled in Smartlead campaign
- Brand name decision pending: ContractMotion.com (#1), EnterpriseCapture.com, ContractWon.com

## Code & Deploy
- **Local:** `~/Desktop/ECAS/`
- **GitHub:** `https://github.com/Entmarketingteam/ECAS`
- **Railway:** `https://ecas-scraper-production.up.railway.app`
  - Project ID: `48f4f546-d55a-4ceb-a34c-f46b8af4b10f`
- **Architecture:** Pure Python (NO n8n) — FastAPI + APScheduler (13 jobs)
- **Dockerfile:** `python:3.11-slim` + `PLAYWRIGHT_BROWSERS_PATH=/ms-playwright`

## Airtable
- **Base:** `appoi8SzEJY8in57x`
- `signals_raw` = `tblAFJnXToLTKeaNU`
- `projects` = `tbloen0rEkHttejnC`
- `contacts` = `tblPBvTBuhwlS8AnS`
- `deals` = `tbl2ZkD20cf6zMxJj`

## Smartlead
- **Campaign:** `3005694` — "ECAS — EPC Power & Grid Outreach 2026"
- 3 emails: Day 0/4/9 | 60 leads STARTED
- ⚠️ Sending from marketingteam@nickient.com — needs dedicated ECAS domain/mailbox

## Admin API
- `POST /admin/run/{job_id}` — trigger any job manually
- `GET /admin/status` — all job statuses
- `GET /admin/scores` — sector scores
- `GET /admin/signals` — raw signals

## Job IDs (13)
`politician_trades`, `sec_13f`, `gov_contracts`, `ferc_poller`, `rss_feeds`,
`claude_extraction`, `sector_scoring`, `enrichment`, `smartlead`,
`weekly_digest`, `earnings_transcripts`, `budget_window_monitor`, `populate_projects`

## Pipeline
signals → Claude extraction → sector scoring → ICP hunt (Apollo orgs) → enrichment (Apollo people) → Smartlead enrollment

## Known Gotchas ⚠️
- **Apollo:** Use `/mixed_people/api_search` NOT `/people/search` (deprecated)
  - 3-step: `/organizations/search` → org ID → `/mixed_people/api_search` by org ID → `/people/bulk_match` to reveal emails
- **Smartlead leads endpoint:** GET `/campaigns/{id}/leads?api_key=KEY` — NO `limit`/`offset` params → 400 error
- **Airtable field names (contacts):** `company_name` (NOT `company`), `confidence_score` (NOT `heat_score`)
- **Airtable field names (projects):** `owner_company` (NOT `company_name`)
- **outreach_status valid values:** `pending_review | approved | do_not_contact | in_sequence | replied | meeting_booked | not_interested | unsubscribed`
- **Airtable singleSelect (projects):** stage=`Identified/Researching/Outreach/etc`, priority=`High/Medium/Low`, icp_fit=`Strong/Moderate/Weak/Unknown`

## Secrets (Doppler: `ecas/dev`)
- `REDUCTO_API_KEY`, `APOLLO_API_KEY`, `PROXYCURL_API_KEY`, `FULLENRICH_API_KEY`
- `FMP_API_KEY`, `ECAS_BASE_ID=appoi8SzEJY8in57x`, `CLOSE_CRM_API_KEY`

## n8n Workflows (all INACTIVE — need credential wiring)
- `g4g5Eom2pQV8ybHR` — ECAS 01 FERC Signal Poller
- `Kg0xi3Ldem59lYuF` — ECAS 02 PJM Queue Poller
- `0DmEuRRQqcLXCUUY` — ECAS 03 RSS Aggregator
- `8nQHnHFmdnH8lWmL` — ECAS 05 Signal Processor / Claude Extraction
- `kMssKmg50794zXl8` — ECAS 07 Contact Enricher
- n8n creds: Airtable `dAoeOLbTnBUK1gTy`, Anthropic `MwxIqQP3l6cUcwcZ`, Slack `EMdoV2Sq9neZV1Tn`

## Airtable Manual Items Still Needed
- Linked record fields: projects↔signals, projects↔contacts, projects↔deals, contacts↔project, deals↔project, deals↔contact
- Formula fields: `days_in_stage`, `guarantee_end_date`, `weighted_value`, `guarantee_days_remaining`
- Delete "Table 1"

## Marketing Assets
- `~/Desktop/ECAS/power-grid-outreach-kit.md` — full outreach kit
- `~/Desktop/ECAS-Master-Plan.md`, `~/Desktop/ECAS-Sales-Motion.md`, `~/Desktop/ECAS-Brand-GTM.md`
- Lead magnet: "Contract Signal Report" — 5 active grid projects in territory before RFPs drop
- Target niches: Substation EPC, Solar EPC (Utility-Scale), EV Charging Station Installers

## Remaining GTM Steps
- [ ] Register domain (ContractMotion.com decision pending)
- [ ] Purchase sending domain (3-week warmup — Day 1 action)
- [ ] Wire n8n credentials + activate workflows
- [ ] Add Airtable linked/formula fields manually
- [ ] Build ICP list (PDL API)
- [ ] Build website (Framer)
