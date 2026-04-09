# ECAS — Enterprise Contract Acquisition System

## What This Is
Signal-driven enterprise contract acquisition for mid-tier power/grid EPCs ($20M–$300M).
Positioning: "We get you on the short-list before the RFP drops."

## Status: LIVE — All Signal Sources Running (2026-04-09)
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
- **Campaign `3005694`** — "ECAS — EPC Power & Grid Outreach 2026" | 6 emails Day 0/4/9/15/22/30 | 60 leads
- **Campaign `3040599`** — "ContractMotion — Data Center & AI Infrastructure 2026" | 6 emails ✅ 2026-03-15
- **Campaign `3040600`** — "ContractMotion — Water & Wastewater Infrastructure 2026" | 6 emails ✅ 2026-03-15
- **Campaign `3040601`** — "ContractMotion — Industrial & Manufacturing Facilities 2026" | 6 emails ✅ 2026-03-15
- ⚠️ Sending from marketingteam@nickient.com — switch after warmup completes (~2026-04-06)
- **Sending domains purchased 2026-03-16:** `getcontractmotion.com`, `trycontractmotion.com`, `contractmotionai.com`, `aicontractmotion.com`, `usecontractmotion.com`
- Warmup start: 2026-03-16 | Warmup end (3 weeks): ~2026-04-06 | Then switch campaigns to new inboxes

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
| FERC Federal Register | `ferc_rss` | ✅ WORKING | Federal Register API — ~3 filings/week, every 6h |
| EIA Capacity Additions | `ferc_poller` | ✅ WORKING | EIA API (`api.eia.gov`) — 655 signals/run, weekly |
| PJM territory capacity | `pjm_poller` | ✅ WORKING | EIA API filtered to PJM states, weekly |

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
- [x] **Fix FERC poller** — replaced with EIA API (`api.eia.gov`) + Federal Register FERC RSS ✅ 2026-04-09
- [x] **Sending domains purchased** — 5 domains, 4 inboxes exist on 2 domains ✅
- [ ] **Start Smartlead warmup** — generate app passwords (Google Account → Security → App passwords), store in Doppler (`ecas/dev`), run `doppler run --project ecas --config dev -- python3 tools/smartlead_warmup_setup.py`
  - Doppler keys needed: `INBOX_ETHAN_AICONTRACTMOTION_PASS`, `INBOX_ETHAN_ATCHLEY_AICONTRACTMOTION_PASS`, `INBOX_KARLEE_AICONTRACTMOTION_PASS`, `INBOX_ETHAN_CONTRACTMOTIONAI_PASS`
  - DNS fix needed for `contractmotionai.com`: add `v=spf1 include:_spf.google.com -all` TXT record at `@` (Google Domains UI)
  - 3 remaining domains (`getcontractmotion.com`, `trycontractmotion.com`, `usecontractmotion.com`) need Workspace setup + mailbox creation before they can be added
- [ ] Wire new sending domains to Smartlead campaign (replace marketingteam@nickient.com)
- [x] Wire n8n credentials + activate all 5 workflows ✅ 2026-03-14
- [ ] Add Airtable linked/formula fields manually (see Airtable Manual Items below)
- [ ] Build ICP list (PDL API or USASpending hunter already running)
- [x] Build website ✅ LIVE at https://contractmotion-site-production.up.railway.app (2026-03-13)
