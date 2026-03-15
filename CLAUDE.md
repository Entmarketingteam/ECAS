# ECAS — Enterprise Contract Acquisition System

## What This Is
Signal-driven enterprise contract acquisition for mid-tier power/grid EPCs ($20M–$300M).
Positioning: "We get you on the short-list before the RFP drops."

## Status: LIVE — Signal Engine Running, FERC/PJM Broken (2026-03-13)
- 51 companies in projects, 118 contacts, 60 enrolled in Smartlead campaign
- Brand: **ContractMotion.com** ✅ purchased 2026-03-10
- Smartlead sequence expanded to 6 emails (Day 0/4/9/15/22/30) ✅ 2026-03-13

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
- 6 emails: Day 0/4/9/15/22/30 ✅ updated 2026-03-13 | 60 leads in sequence
- ⚠️ Sending from marketingteam@nickient.com — needs dedicated ECAS domain/mailbox
- Sending domains to buy: `contractmotion.io`, `getcontractmotion.com` — then 3-week warmup before switching

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

## Signal Collection Status (2026-03-13)
| Source | Job | Status | Notes |
|--------|-----|--------|-------|
| USASpending.gov | `gov_contracts` | ✅ WORKING | 662 contracts, pushing 45/run to Airtable |
| Politician trades | `politician_trades` | ✅ WORKING | Running every 4h |
| RSS feeds | `rss_feeds` | ✅ WORKING | Running every 6h |
| SEC 13F | `sec_13f` | ✅ WORKING | Weekly Mon 7am |
| Earnings transcripts | `earnings_transcripts` | ✅ WORKING | Weekly Tue 6am (FMP API) |
| FERC eLibrary | `ferc_poller` | ❌ BROKEN | Cloudflare-protected SPA — always returns HTML, 0 filings collected |
| PJM interconnection queue | (none) | ❌ MISSING | URL changed (404), no working poller |
| ERCOT interconnection queue | (none) | ❌ MISSING | API inaccessible |

**Fix needed:** Replace `ferc_poller` with EIA API (`api.eia.gov` — free, just needs API key) + PJM Dataminer2.
FERC/PJM/ERCOT are the core of the pitch — priority fix before client onboarding.

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

## n8n Workflows — ALL ACTIVE ✅ (wired 2026-03-14)
- `g4g5Eom2pQV8ybHR` — ECAS 01 FERC Signal Poller — ACTIVE (every 6h)
- `Kg0xi3Ldem59lYuF` — ECAS 02 PJM Queue Poller — ACTIVE (Mon 7am)
- `0DmEuRRQqcLXCUUY` — ECAS 03 RSS Aggregator — ACTIVE (every 15min)
- `8nQHnHFmdnH8lWmL` — ECAS 05 Signal Processor / Claude Extraction — ACTIVE (every 15min)
- `kMssKmg50794zXl8` — ECAS 07 Contact Enricher — ACTIVE (every 5min poll)
  - NOTE: airtableTrigger replaced with scheduleTrigger + Airtable poll (v2 trigger had airtableApi cred conflict)
- n8n creds: Airtable `dAoeOLbTnBUK1gTy`, Anthropic `MwxIqQP3l6cUcwcZ`, Slack `EMdoV2Sq9neZV1Tn`
- ⚠️ Doppler PLACEHOLDERS still need real values: `PROXYCURL_API_KEY`, `FULLENRICH_API_KEY`, `FMP_API_KEY`, `CLOSE_CRM_API_KEY`
  - Contact Enricher (07) will fail at Proxycurl node until PROXYCURL_API_KEY is set
  - Signal Processor (05) will fail at Claude extraction until Anthropic cred is confirmed working

## Airtable Manual Items Still Needed
- Linked record fields: projects↔signals, projects↔contacts, projects↔deals, contacts↔project, deals↔project, deals↔contact
- Formula fields: `days_in_stage`, `guarantee_end_date`, `weighted_value`, `guarantee_days_remaining`
- Delete "Table 1"

## Marketing Assets
- `~/Desktop/ECAS/power-grid-outreach-kit.md` — full outreach kit
- `~/Desktop/ECAS-Master-Plan.md`, `~/Desktop/ECAS-Sales-Motion.md`, `~/Desktop/ECAS-Brand-GTM.md`
- Lead magnet: "Contract Signal Report" — 5 active grid projects in territory before RFPs drop
- Target niches: Substation EPC, Solar EPC (Utility-Scale), EV Charging Station Installers
- **Website:** https://contractmotion-site-production.up.railway.app ✅ LIVE 2026-03-13

## Remaining GTM Steps
- [x] Register domain — ContractMotion.com ✅ purchased 2026-03-10
- [x] Expand Smartlead sequence to 6 emails ✅ 2026-03-13
- [ ] **PRIORITY: Fix FERC poller** — replace with EIA API (`api.eia.gov`) + PJM/ERCOT alternatives
- [ ] **PRIORITY: Purchase sending domains** — `contractmotion.io` + `getcontractmotion.com`, set up Google Workspace mailboxes, add to Smartlead warmup (3 weeks)
- [ ] Wire new sending domains to Smartlead campaign (replace marketingteam@nickient.com)
- [x] Wire n8n credentials + activate all 5 workflows ✅ 2026-03-14
- [ ] Add Airtable linked/formula fields manually (see Airtable Manual Items below)
- [ ] Build ICP list (PDL API or USASpending hunter already running)
- [x] Build website ✅ LIVE at https://contractmotion-site-production.up.railway.app (2026-03-13)
