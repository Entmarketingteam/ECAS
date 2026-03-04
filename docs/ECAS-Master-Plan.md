# ECAS — Enterprise Contract Acquisition System
## Master Planning Document
**Generated:** March 3, 2026
**Status:** Planning Complete — Ready to Build
**Entity:** Standalone company (separate from ENT Agency)
**Phase 1 Vertical:** Power & Grid Infrastructure / Data Center Power EPCs
**Phase 1 Geography:** Virginia (Dominion territory / Loudoun County)

---

## TABLE OF CONTENTS

1. [Product Overview](#1-product-overview)
2. [Vertical Intelligence — Where the Capital Is](#2-vertical-intelligence)
3. [Technical Architecture](#3-technical-architecture)
4. [Data Source Inventory](#4-data-source-inventory)
5. [8-Week Build Sequence](#5-8-week-build-sequence)
6. [n8n Workflow Architecture](#6-n8n-workflow-architecture)
7. [Signal-Based Outreach — Real Examples](#7-signal-based-outreach)
8. [Earnings Call Ingestion](#8-earnings-call-ingestion)
9. [Trade Show Signals](#9-trade-show-signals)
10. [Tool Stack Decisions](#10-tool-stack-decisions)
11. [Monthly Operating Cost](#11-monthly-operating-cost)
12. [Real Mid-Tier Target Companies](#12-real-mid-tier-target-companies)
13. [Critical Path](#13-critical-path)

---

## 1. PRODUCT OVERVIEW

**What ECAS is:**
A signal-driven enterprise contract acquisition system for mid-tier power infrastructure contractors.

**What ECAS is not:**
- A marketing service
- A lead generation agency
- An AI automation firm

**Core thesis:**
Power infrastructure is entering a multi-decade capital expansion cycle driven by AI data center load growth, electrification, grid strain, and federal infrastructure funding. Mid-tier contractors are relationship-dependent, RFP-reactive, and have zero proactive positioning systems. Information asymmetry exists in public filings, permit data, interconnection queues, and earnings disclosures. ECAS installs a predictive contract positioning engine that places contractors before formal bid cycles.

**Guarantee:** 2 signed enterprise contracts within 180 days ($500K+ each)
**Pricing:** $12K–$15K/month retainer + $25K–$50K per signed contract
**Target Economics:** 5 clients × $12K = $60K MRR + performance upside

**ICP:**
- Revenue: $20M–$300M
- Employees: 50–500
- Services: Substation construction, transmission EPC, HV installation, switchgear integration, utility interconnection, grid modernization
- Has executed 3+ enterprise projects, avg contract value $500K+

---

## 2. VERTICAL INTELLIGENCE

### Where the Capital Is Going (March 2026)

Based on ARB Letter equity positioning (AXON, KTOS, MSFT, AVGO, MRVL, SMCI, NB, BBAI, NOW) + data center infrastructure news:

```
UPSTREAM (Supply/Enablers)
├── Critical minerals: scandium (NB), uranium (UEC/CCJ), rare earths (MP)
├── Semiconductor fab supply chain (TSMC adjacents, specialty gases)
└── Long-lead equipment: transformers, switchgear (128-week lead times NOW)

CORE INFRASTRUCTURE ← ECAS plays here
├── Data center power EPCs — substation/transmission for hyperscaler campuses
├── Grid modernization contractors — T&D upgrades for AI baseload demand
├── Defense tech integrators — drone systems, sensor networks, satcom
└── SMR/nuclear project services — NuScale, Oklo supply chain

DOWNSTREAM (Applications/End-Use)
├── Public safety AI: AXON, SoundThinking — agency contract cycle
├── Enterprise workflow AI: ServiceNow, Palantir — DoD/federal contracts
├── Unmanned systems: KTOS, AeroVironment — DoD acquisition
└── Hyperscaler compute: SMCI racks, MRVL networking, AVGO interconnects
```

### Vertical Scoring — Cold Traffic Offer for Mid-Tier ($20M–$300M)

| Vertical | Signal Density | Sales Cycle | Contract Size | Saturation | Score |
|---|---|---|---|---|---|
| **Data Center Power EPCs** | Very High | 90–180d | $500K–$50M | Low | ★★★★★ |
| **Defense Tech Contractors** | High (SAM.gov) | 60–180d | $1M–$100M | Medium | ★★★★ |
| **Grid Modernization Firms** | High (FERC/PUC) | 90–180d | $500K–$25M | Low | ★★★★ |
| Oilfield Services | Medium (permits) | 45–120d | $250K–$5M | High | ★★★ |
| Critical Minerals Services | Low | 180–365d | $1M–$50M | Low | ★★ |

### Why Data Center Power EPCs Win

1. **Capital confirmation** — $1T+ in hyperscaler capex announced 2025–2026. Microsoft, Meta, Google, Amazon all building. Every campus needs a substation. Every substation needs an EPC.
2. **Signal richness** — Interconnection queue filings, land permits, zoning, PPA announcements, earnings call mentions — all publicly available, all 60–180 days before RFP
3. **Mid-tier sweet spot** — MMR Group / MYR Group have graduated out of mid-tier. The $30M–$150M electrical contractors are being approached by hyperscalers but have no BD systems
4. **No competition** — Zero agencies are doing signal-based positioning for electrical EPCs. Entirely referral + relationship dependent
5. **Virginia lock-in** — Loudoun County alone has more data center power infrastructure in the queue than most states combined

### Capital Signals From Stock Market (Feb–Mar 2026)

| Stock | Thesis | Downstream Infrastructure Signal |
|---|---|---|
| SMCI | AI-optimized servers/racks for hyperscalers | Data center construction surge → power EPCs |
| MRVL | Networking/interconnects for AI clusters | Same — data center buildout |
| AVGO | Custom silicon + connectivity for data centers | Same |
| MSFT | Azure expansion, AI infrastructure capex | Direct hyperscaler = direct power demand |
| AXON | Public safety agency multi-year contracts | Model for guaranteed agency contract approach |
| KTOS | Unmanned defense + satellite comms | Defense tech contractors need BD systems too |
| NB | Scandium/rare earths for AI/defense/aerospace | Critical minerals upstream |
| BBAI | Decision intelligence for defense/logistics | Defense AI contract pipeline |

---

## 3. TECHNICAL ARCHITECTURE

### System Overview

```
Layer 1: Signal Engine (n8n + Firecrawl + Claude API → Airtable)
    ↓
Layer 2: Contact Mapping (Apollo.io + Proxycurl + Zerobounce → Airtable contacts)
    ↓
Layer 3: Outreach Engine (n8n → Smartlead [email] + Expandi [LinkedIn])
    ↓
Layer 4: Pipeline Control (Close CRM + Airtable + n8n SLA monitors)
```

### Full Stack Per Layer

**Layer 1 — Signal Intelligence Engine**

| Component | Tool | Notes |
|---|---|---|
| Workflow orchestration | n8n (existing instance) | entagency.app.n8n.cloud |
| Primary scraper | Firecrawl MCP | Already connected, handles JS-rendered pages |
| Fallback scraper | Scrapling + Playwright on Railway | Same pattern as creator-proposal project |
| AI extraction | Claude API (claude-sonnet-4-6) | Existing cred `MwxIqQP3l6cUcwcZ` |
| Structured storage | Airtable (new ECAS base) | Existing cred `dAoeOLbTnBUK1gTy` |
| PDF parsing | Reducto AI API | Purpose-built for regulatory PDFs (FERC orders, IRP docs) |
| Job posting monitoring | Firecrawl scrape LinkedIn/Indeed company pages | No API needed |
| Earnings call transcripts | Financial Modeling Prep Ultimate API | Keyword search across transcripts |
| FERC filings | FERC EFTS API (free) | `efts.ferc.gov/EFTS-Java/search` — no key required |
| PJM interconnection queue | PJM Data Miner 2 API | Free, registration required, county-level data |
| ERCOT interconnection queue | ERCOT MIS public data | CSV download, no auth |
| DOE grants | DOE EERE award API via api.data.gov | Free, API key required |

**Layer 2 — Contact Mapping**

| Component | Tool | Notes |
|---|---|---|
| Primary enrichment | Apollo.io API ($49/mo) | Email + LinkedIn + phone; REST API |
| LinkedIn profile data | Proxycurl API ($49/mo) | Full profile, tenure, reporting structure |
| Email verification | Zerobounce API (~$0.008/email) | Before any sequence launch |
| Contact storage | Airtable `contacts` table | Linked to `projects` table |
| LinkedIn outreach | Expandi.io ($99/mo) | Cloud-based, no Chrome extension |

**Layer 3 — Outreach System**

| Component | Tool | Notes |
|---|---|---|
| Email sequencing | Smartlead (existing) | New ECAS sending domain — keep separate from ENT |
| Email copy generation | Claude API (claude-sonnet-4-6) | Signal-aware personalization per project |
| LinkedIn automation | Expandi.io | Connection request + DM cadence |
| Conference intelligence | Firecrawl on DTECH/IEEE PES T&D pages | Exhibitor list cross-reference |
| CRM push | Close CRM API via n8n HTTP node | On reply event |

**Layer 4 — Pipeline Control**

| Component | Tool | Notes |
|---|---|---|
| CRM | Close CRM ($49/mo Startup) | Built for outbound B2B; clean API |
| SLA monitoring | n8n daily poll | Query Close for leads with no activity >24h |
| Revenue forecasting | Airtable formulas + n8n weekly Slack summary | |
| Guarantee tracking | Airtable `deals` table | `signed_at`, `contract_value`, 180-day window |
| Meeting scheduling | Calendly | Webhooks → n8n → Close CRM update + Slack |

---

## 4. DATA SOURCE INVENTORY

| Signal Type | Source | Access Method | Cost | Update Frequency |
|---|---|---|---|---|
| FERC filings | `efts.ferc.gov/EFTS-Java/search` | Free REST API, no key | $0 | Real-time |
| PJM interconnection queue (Dominion) | `dataminer2.pjm.com` | Free REST API, registration | $0 | Weekly |
| ERCOT interconnection queue | `mis.ercot.com/misapp/GetReports.do` | CSV download, no auth | $0 | Weekly |
| Virginia SCC utility rate cases | `scc.virginia.gov/pages/Utility-Rate-Cases` | Firecrawl scrape + RSS | $0 | Daily |
| Texas PUC dockets | `interchange.puc.texas.gov` | Firecrawl scrape | $0 | Daily |
| DOE EERE grants | `api.data.gov` EERE awards | Free API, key required | $0 | Weekly |
| Utility IRPs | State PUC + utility IR pages | Firecrawl PDF → Reducto AI | $50–200/mo | Quarterly (monitored weekly) |
| EPA permits | `echo.epa.gov/api/` ECHO system | Free REST API | $0 | Weekly |
| Land acquisitions / zoning | County recorder sites (Loudoun, Travis) | Firecrawl scrape | $0 | Daily |
| PPA announcements | Google News RSS for "power purchase agreement" | Free RSS | $0 | Daily |
| Job postings (surge detection) | LinkedIn + Indeed via Firecrawl | Scrape company pages | $0 | Daily |
| Earnings call transcripts | FMP Ultimate API | Paid — keyword search API | $100–200/mo | Quarterly |
| EPC partnership announcements | PR Newswire RSS + Business Wire RSS | Free RSS | $0 | Daily |
| Company contact data | Apollo.io API | Paid — $49/mo | $49/mo | On-demand |
| LinkedIn profiles | Proxycurl API | Paid — $49/mo | $49/mo | On-demand |
| Email verification | Zerobounce API | $0.008/email | Pay-per-use | On-demand |
| DISTRIBUTECH exhibitors | `dt2026.mapyourshow.com` + ExpoCaptive | Browse free / pay for enriched data | Varies | Annual (post-event now) |
| IEEE PES T&D exhibitors | `td26.mapyourshow.com` | Browse free | $0 | Pre-event now (May 2026) |

**Virginia targets to monitor:** Dominion Energy Virginia, AES, Sievert Larsen, Ames Construction, MYR Group (Harlan Electric), Quanta Services, Pike Electric, MasTec

**Texas targets:** Oncor, CenterPoint Energy, LCRA, Primoris Services, Quanta Services, MYR Group, Willbros Group

**Utility + EPC earnings tickers to monitor:**
`D` (Dominion), `SO` (Southern Company), `NEE` (NextEra), `AES`, `ETR` (Entergy), `DUK` (Duke), `PWR` (Quanta), `MYR` (MYR Group), `PRIM` (Primoris), `WLDN` (Willdan)

---

## 5. 8-WEEK BUILD SEQUENCE

### Week 1 — Foundation & Raw Signal Ingestion

**Goal:** Data flowing into Airtable. No AI processing yet.

**Critical action this week:** Buy ECAS sending domain. 3-week warmup starts Day 1.

1. Create Airtable base `ECAS` with two tables:
   - `projects`: `name`, `location`, `state`, `MW`, `estimated_value_band`, `signal_sources`, `positioning_window_open`, `positioning_window_close`, `owner_company`, `epc_company`, `scope`, `status`, `created_at`
   - `signals_raw`: `source`, `url`, `raw_text`, `captured_at`, `processed`, `linked_project`

2. Build n8n Workflow 1: **FERC Signal Poller** — HTTP GET to FERC EFTS API every 6h, filter `state:VA` OR `state:TX`, push to `signals_raw`
3. Build n8n Workflow 2: **PJM Queue Poller** — HTTP GET to PJM Data Miner 2 weekly, filter by county (Loudoun, Fauquier, Stafford for VA), push to `signals_raw`
4. Build n8n Workflow 3: **ERCOT Queue Poller** — CSV download weekly, parse in Code node, push to `signals_raw`
5. Build n8n Workflow 4: **RSS Aggregator** — 8 RSS feeds (Google News: "Dominion Energy project", "ERCOT expansion", "data center power Virginia", "Texas grid construction"; PR Newswire energy; Business Wire EPC; PPA announcements), push to `signals_raw`

**Output:** ~20–50 raw signals/day in Airtable.

---

### Week 2 — AI Signal Processing

**Goal:** Claude extracts structured project opportunities from raw signals.

1. Build n8n Workflow 5: **Signal Processor** — Trigger: new unprocessed row in `signals_raw` (poll every 15 min). Pass `raw_text` + `url` to Claude API with extraction prompt. Parse JSON. Upsert into `projects`. Mark signal processed.

2. Deploy ECAS Scraper microservice to Railway:
   - Clone `~/Desktop/creator-proposal/` pattern exactly: `python:3.11-slim` + Playwright + FastAPI + uvicorn
   - Endpoints: `POST /scrape-pdf` (Reducto AI) and `POST /scrape-page` (Firecrawl fallback)

3. Build n8n Workflow 6: **PUC Docket Monitor** — Firecrawl scrape Virginia SCC + Texas PUC, route PDFs through Railway `/scrape-pdf`, store in `signals_raw`

**Claude extraction prompt (Signal Processor):**
```
You are extracting power/grid infrastructure project data from a regulatory filing or announcement.
Extract only if there is a concrete infrastructure project with identifiable scope.

Source URL: {{signal.url}}
Source type: {{signal.source}}
Raw text: {{signal.raw_text}}

Return JSON with exactly these fields (null if unknown):
{
  "is_infrastructure_project": boolean,
  "confidence_score": 0.0-1.0,
  "project_name": string,
  "state": "VA" or "TX" or null,
  "county": string,
  "mw_capacity": number,
  "estimated_contract_value_band": "<$1M" | "$1M-$5M" | "$5M-$25M" | "$25M-$100M" | ">$100M" | null,
  "project_type": "transmission" | "substation" | "generation" | "distribution" | "interconnection" | "other",
  "owner_company": string,
  "epc_company": string or null,
  "rfp_expected_date": "YYYY-MM" or null,
  "positioning_window_open": "YYYY-MM" or null,
  "positioning_window_close": "YYYY-MM" or null,
  "scope_summary": string (max 200 chars),
  "signal_type": "ferc_filing" | "interconnection_queue" | "rate_case" | "ppa" | "job_posting" | "press_release" | "earnings_call" | "permit" | "other"
}
```

**Output:** `projects` table populating with structured opportunity records.

---

### Week 3 — Contact Mapping

**Goal:** 5–15 verified contacts per identified project.

1. Create `contacts` table in Airtable: `project_id`, `name`, `title`, `company`, `email`, `linkedin_url`, `email_verified`, `enrichment_source`, `enrichment_date`, `outreach_status`

2. Build n8n Workflow 7: **Contact Enricher** — Trigger: new project in Airtable. Extract `owner_company` + `epc_company`. For each company, POST to Apollo.io `/people/search` with title filters. For each result, call Proxycurl for LinkedIn profile. Verify email via Zerobounce. Push verified contacts to `contacts` linked to project.

3. Create Airtable view: `outreach_status = pending_review` — manual daily review, mark `approved` before launch.

**Target roles per project:**
- Utility: Director of Transmission Planning, Interconnection Manager, Capital Projects Director
- EPC: VP Operations, Director of Preconstruction, Project Executive, Estimating Manager
- Hyperscaler construction: Head of Energy Strategy, Construction Director, Energy Procurement Lead

**Output:** 5–15 approved contacts per project.

---

### Week 4 — Outreach Launch

**Goal:** First Smartlead campaign running with signal-personalized emails.

1. Create Smartlead campaign structure: 4-touch sequence, 3–4 day gaps, from new ECAS sending domain
2. Build n8n Workflow 8: **Outreach Launcher** — Trigger: `outreach_status = approved`. Group by project. Pass project signals + contact data to Claude to generate personalized Touch 1. Push to Smartlead `POST /api/v1/campaigns/{id}/leads/bulk`. Set `outreach_status = in_sequence`.
3. Build n8n Workflow 9: **Reply Handler** — Smartlead webhook → update Airtable contacts → push to Close CRM → Slack notification.

**Outreach philosophy:**
- Never: "Do you need work?"
- Always: "We monitor expansion cycles and position contractors before formal RFP windows."

**Email structure:**
1. Signal reference (specific project, filing, announcement)
2. Strategic observation
3. Positioning opportunity
4. Guarantee anchor
5. Call to conversation

**Output:** First emails live by end of Week 4.

---

### Week 5 — CRM + Pipeline Control

**Goal:** Close CRM live, SLA monitoring running.

1. Configure Close CRM pipeline: `Signal Identified` → `Contact Mapped` → `Outreach Active` → `Meeting Booked` → `Proposal Sent` → `Contract Negotiation` → `Closed Won` / `Closed Lost`

2. Custom fields in Close: `project_mw`, `estimated_contract_value`, `positioning_window`, `signal_source`, `guarantee_window_day`

3. Smart Views: `Hot Leads (replied, no meeting booked)`, `SLA Breach Risk (>18h no activity)`, `Guarantee Pace Tracker`

4. Build n8n Workflow 10: **CRM Sync** — Airtable project → Close Lead, Airtable contact → Close Contact

5. Build n8n Workflow 11: **SLA Monitor** — Daily 8am: query Close for `status = Outreach Active` with `date_updated < 24h`. Notify Slack `#ecas-pipeline`.

6. Build n8n Workflow 12: **Pipeline Report** — Weekly Monday 9am: deal metrics → Google Sheets → Slack summary.

**Output:** Human-facing pipeline live.

---

### Week 6 — LinkedIn Layer + Sequence Tuning

**Goal:** Multi-channel running (email + LinkedIn in parallel).

1. Configure Expandi.io: dedicate a new LinkedIn account ("BD Analyst" persona for ECAS — not personal profile)
2. Build n8n Workflow 13: **LinkedIn Sync** — On `outreach_status = in_sequence`, generate LinkedIn connection message referencing signal, push to Expandi via Zapier webhook
3. Review first 100 outreach results: open rates, reply rates, bounce rates. Adjust Claude prompt. A/B test subject lines in Smartlead.

---

### Week 7 — Conference Intelligence

**Goal:** Pre-conference outreach layer on top of sequences.

1. Build n8n Workflow 14: **Conference Monitor** — Firecrawl scrape DISTRIBUTECH 2026 (already occurred — Feb, San Diego), IEEE PES T&D 2026 (May, Chicago) speaker/exhibitor pages. Extract company names. Cross-reference `contacts` table. Flag `conference_opportunity = true`.

2. Touch 0 variant in Smartlead (pre-conference email):
   > "I see [Company] is at IEEE PES T&D in Chicago next month — we're working with several EPC firms on [specific grid project type]. Would you be open to a quick 15-minute introduction?"

**DISTRIBUTECH 2026 (already done, post-event outreach is valid NOW):**
- 680+ exhibitors, 18,000+ attendees, San Diego, Feb 2–5, 2026
- Exhibitor directory: `dt2026.mapyourshow.com`
- Enriched list with verified emails: ExpoCaptive (`expocaptive.com/distributech/`)

**IEEE PES T&D 2026 (upcoming — use for pre-event outreach):**
- 800+ exhibitors, Chicago, May 4–7, 2026
- Directory: `td26.mapyourshow.com`

---

### Week 8 — Guarantee Tracking + Hardening

**Goal:** 180-day guarantee tracking live, system autonomous.

1. Add `deals` table to Airtable: `project_id`, `contact_id`, `contract_value`, `contract_type`, `signed_at`, `status`
2. Airtable formula: `guarantee_days_remaining = 180 - (TODAY() - first_outreach_date)`
3. Build n8n Workflow 15: **Guarantee Dashboard** — Weekly: count closed deals in 180-day window. Slack alert if behind pace (<0.5 deals/month by day 90).
4. Error alerting on all 15 workflows: any failure → Slack `#ecas-ops`
5. Create ECAS project `CLAUDE.md` (same pattern as existing projects)

---

## 6. n8n WORKFLOW ARCHITECTURE

### Complete Workflow Map

```
FERC Poller (6h cron)          ─┐
PJM Poller (weekly)            ─┤
ERCOT Poller (weekly)          ─┤→ signals_raw (Airtable) → Signal Processor → projects (Airtable)
RSS Aggregator (15m cron)      ─┤                                ↓
PUC Docket Monitor (daily)     ─┤                         Contact Enricher
Earnings Call Monitor (weekly) ─┘                               ↓
                                                          contacts (Airtable)
                                                                ↓
                                                    [Manual Approval View]
                                                                ↓
                                                       Outreach Launcher
                                                          ↓         ↓
                                                     Smartlead    Expandi
                                                          ↓         ↓
                                                       Reply Handler
                                                                ↓
                                                       CRM Sync → Close CRM
                                                                ↓
                                                        SLA Monitor (daily)
                                                        Pipeline Report (weekly)
                                                        Guarantee Dashboard (weekly)
```

### Workflow Registry

| # | Name | Trigger | Purpose |
|---|---|---|---|
| 1 | FERC Signal Poller | 6h cron | FERC filings → signals_raw |
| 2 | PJM Queue Poller | Weekly cron | PJM interconnection queue → signals_raw |
| 3 | ERCOT Queue Poller | Weekly cron | ERCOT queue CSV → signals_raw |
| 4 | RSS Aggregator | 15m cron | 8 RSS feeds → signals_raw |
| 5 | Signal Processor | Airtable trigger (new unprocessed row) | Claude extraction → projects |
| 6 | PUC Docket Monitor | Daily cron | VA SCC + TX PUC + Railway scraper → signals_raw |
| 7 | Contact Enricher | Airtable trigger (new project) | Apollo + Proxycurl + Zerobounce → contacts |
| 8 | Outreach Launcher | Airtable trigger (approved contacts) | Claude email gen → Smartlead bulk load |
| 9 | Reply Handler | Smartlead webhook | Reply event → Airtable + Close CRM + Slack |
| 10 | CRM Sync | Airtable trigger | projects/contacts → Close CRM |
| 11 | SLA Monitor | Daily 8am cron | Detect >24h no activity in Close → Slack |
| 12 | Pipeline Report | Weekly Monday 9am | Deal metrics → Sheets + Slack |
| 13 | LinkedIn Sync | Airtable trigger (in_sequence) | Generate LI message → Expandi |
| 14 | Conference Monitor | Weekly cron | Exhibitor scrape → flag conference_opportunity |
| 15 | Guarantee Dashboard | Weekly cron | Count signed deals → pace alert |

---

## 7. SIGNAL-BASED OUTREACH

### Benchmark Reply Rates (2025–2026)

| Outreach Type | Reply Rate |
|---|---|
| Generic cold email | 1–3% |
| Basic personalization | 3–5% |
| Single signal + tailored value prop | 15–25% |
| Multi-signal stacked (2–3 triggers) | 25–40% |

### Signal Types + Timing

| Signal | Source | Outreach Window | Relevance |
|---|---|---|---|
| Hiring BD/Estimating Manager | LinkedIn Jobs, Apollo | Within 2 weeks of posting | Company ramping to pursue contracts |
| Permit filing | BuildZoom, local permit feeds | Within 30 days | Project real + awarded; subs needed |
| Conference exhibitor (DTECH, IEEE PES T&D) | MapYourShow, ExpoCaptive | Within 30 days post-event | Company actively selling into utilities |
| Earnings call capex mention | FMP Ultimate API | Within 1 week of transcript | Executive publicly committed to spend |
| Expansion announcement | PR Newswire, press releases | Within 2 weeks | New facility = new vendor needs |
| Interconnection queue filing | PJM/ERCOT APIs | Within 2 weeks | Project in active pre-construction |
| Acquisition announcement | SEC filings | Within 30 days | Integration chaos = new vendor evaluations |

### Real Cold Email Templates (Adapted for Grid/EPC)

**Permit filing signal:**
> "Hi [Name], saw that [Company] filed permits for the [Project] substation in [County] last month. Most EPCs miss the pre-bid positioning window on projects like this. We work with electrical contractors to get them in front of the right utility and EPC stakeholders 60–90 days before RFP release — and we guarantee 2 signed contracts in 180 days. Worth a 15-minute conversation?"

**Post-DISTRIBUTECH (use RIGHT NOW — event was Feb 2–5):**
> "Hi [Name], saw [Company] had a presence at DISTRIBUTECH in San Diego last month. Teams investing in a DTECH booth are actively working the T&D market — we help those firms get positioned on specific projects before the formal bid list goes out. We guarantee 2 signed enterprise contracts in 180 days. Worth 15 minutes?"

**Earnings call capex signal:**
> "Hi [Name], caught [CEO]'s comments on the Q4 call about [specific capex commitment]. When the CEO puts grid expansion on the public record, the pressure to find qualified execution partners is real. We monitor those signals and help EPCs position before the RFP hits. Guarantee 2 signed contracts in 180 days. Would this be useful to you right now?"

**Hiring surge signal:**
> "Hi [Name], saw [Company] has [X] estimating and preconstruction roles posted right now — that's a serious pipeline ramp. New BD talent typically takes 3–6 months to hit full productivity. We install systems that short-circuit that. Guarantee 2 enterprise contracts in 180 days. Worth a quick call?"

**Interconnection queue approval:**
> "Saw [Utility] got approval on the [Project Name] interconnection in [County] last week. Most contractors wait until the bid list circulates. We help firms like [Company] position 60–90 days earlier and guarantee 2 signed contracts in 180 days. Want to see how this works?"

### What No One Is Doing

No agency currently does signal-based BD positioning for electrical EPCs or grid contractors. Every agency in this space runs generic:
- Conference marketing
- Trade publication ads
- LinkedIn content
- Referral networks

The signal-first, guarantee-backed approach is unclaimed territory in this vertical.

---

## 8. EARNINGS CALL INGESTION

### Source Comparison

| Source | API | Keyword Filter | Cost | Best For |
|---|---|---|---|---|
| **Financial Modeling Prep (FMP)** | Yes — Search Transcripts API | Yes — pass any keyword | $100–200/mo (Ultimate) | Automated signal extraction ✓ |
| Seeking Alpha | No | Manual only | Free to read | Manual research |
| Finnhub | Yes | No | $50–200/mo | Portfolio monitoring |
| API Ninjas | Yes | No | $39–99/mo | Full transcript by ticker |
| OpenBB | Yes (self-hosted) | Build your own | Free (open source) | Custom pipeline, no per-call cost |

### Recommended Setup

**FMP Ultimate API → n8n HTTP node → keyword filter → signals_raw → Claude processor**

Keywords to filter:
- `"capital expenditure increase"`
- `"transmission expansion"`
- `"data center interconnection"`
- `"substation upgrade"`
- `"grid expansion"`
- `"new capacity"`
- `"infrastructure investment"`
- `"interconnection queue"`

FMP Search Transcripts endpoint: `site.financialmodelingprep.com/developer/docs/stable/search-transcripts`

### Target Tickers for Monitoring

**Utilities (demand signals):**
`D` (Dominion), `SO` (Southern Company), `NEE` (NextEra), `AES`, `ETR` (Entergy), `DUK` (Duke Energy), `EXC` (Exelon), `PCG` (PG&E)

**EPCs / contractors (competitive intel + partnership signals):**
`PWR` (Quanta Services), `MYR` (MYR Group), `PRIM` (Primoris), `WLDN` (Willdan), `J` (Jacobs Solutions), `MDU` (MDU Resources)

**Hyperscalers (capex commitment signals):**
`MSFT`, `GOOGL`, `AMZN`, `META` — watch for specific state/region capex announcements

### Q1 2026 Earnings Calendar (March–April)

| Date | Ticker | Watch For |
|---|---|---|
| Mar 3 | TDW (Tidewater) | Fleet/capex shifts (offshore support) |
| Mar 3 | CRC (California Resources) | Production, E&P signals |
| Mar 10 | BBCP (Concrete Pumping) | Adjacent energy infra |
| Late Mar | PWR (Quanta) | T&D pipeline, data center work |
| April | D (Dominion) | Virginia grid capex, data center interconnections |
| April | NEE (NextEra) | Renewables + T&D expansion |

---

## 9. TRADE SHOW SIGNALS

### DISTRIBUTECH 2026 — POST-EVENT (Use Now)

- **Dates:** February 2–5, 2026 — San Diego Convention Center
- **Scale:** 680+ exhibitors, 18,000+ attendees, 81% decision-makers
- **Exhibitor directory:** `dt2026.mapyourshow.com` (free to browse)
- **Enriched contact list:** ExpoCaptive (`expocaptive.com/distributech/`) — 20,000+ attendees + 700+ exhibitors with verified emails, titles, company classifications

**Signal logic:** Companies that paid for a DTECH booth are:
1. Actively selling into utilities and grid operators
2. Have approved sales/marketing budgets
3. Had decision-makers travel to San Diego in February

Post-event outreach window (March 2026) is still fully valid. Reference the event specifically.

### IEEE PES T&D 2026 — PRE-EVENT (Use for Pre-Conference Outreach)

- **Dates:** May 4–7, 2026 — Chicago
- **Scale:** 800+ exhibitors
- **Directory:** `td26.mapyourshow.com` (browseable now, pre-event)
- **Contact:** pestdexhibitor@ieee.org

Pre-event outreach: "Saw [Company] is exhibiting at IEEE PES T&D in Chicago in May — we work with EPCs to turn conference visibility into signed contracts. Our system guarantees 2 signed enterprise contracts in 180 days. Worth 15 minutes before the event?"

### Other Key Conferences

| Conference | Focus | Date | Signal Use |
|---|---|---|---|
| DISTRIBUTECH 2026 | T&D / Smart Grid | Feb 2–5 (done) | Post-event outreach NOW |
| IEEE PES T&D 2026 | Power engineering | May 4–7, Chicago | Pre-event outreach |
| POWERGEN 2026 | Power generation | Dec 2026 | Monitor exhibitor list |
| Western Energy Infrastructure Summit | Western grid | Spring 2026 | Exhibitor scrape |
| Data Center World 2026 | Data center ops | April 2026 | Adjacent — power suppliers |

---

## 10. TOOL STACK DECISIONS

### Why Apollo.io + Proxycurl over Clay

| | Clay.com | Apollo.io API + Proxycurl |
|---|---|---|
| Price | $149–800/mo | $98/mo combined |
| n8n integration | HTTP node only (no native node) | HTTP node, clean JSON |
| LinkedIn data | Moderate | Excellent via Proxycurl |
| Speed | Slow (waterfall enrichment) | Fast (direct API calls) |
| Built for | Visual no-code spreadsheet enrichment | Backend automation pipelines |
| Verdict | Manual prospecting tool | Automated pipeline tool ✓ |

Clay is a manual tool designed for humans doing spreadsheet enrichment. Apollo + Proxycurl as n8n HTTP nodes gives deterministic, fast, JSON-output enrichment that plugs directly into the automation pipeline.

### Why Close CRM over HubSpot / Salesforce

| | Close CRM | HubSpot | Salesforce |
|---|---|---|---|
| Price | $49/mo | $90–800/mo | $150+/seat |
| Built for | Outbound B2B sales ✓ | Inbound marketing | Enterprise |
| n8n node | Yes (native) | Yes | Yes (painful) |
| Email/activity tracking | Native 2-way sync | Paid add-on | Add-on required |
| Implementation | 1 day | 3–5 days | Weeks |
| API rate limits | 1,000 req/hr | Variable | Governor limits |

### Why Virginia over Texas (Phase 1)

| Factor | Virginia | Texas |
|---|---|---|
| Data source quality | PJM Data Miner 2 = county-level structured data | ERCOT less granular |
| Market density | Loudoun County = world's highest data center concentration | More distributed |
| Signal volume | High — Dominion IRP, VA SCC rate cases, PJM queue | Moderate |
| Competition | Low — Virginia power BD is under-targeted | Higher — Permian Basin saturated |
| Scale path | Add Texas in Week 9 using same workflows | |

---

## 11. MONTHLY OPERATING COST

| Tool | Plan | Monthly Cost | Incremental? |
|---|---|---|---|
| n8n Cloud | Existing | $0 | No |
| Firecrawl MCP | Existing | $0 | No |
| Claude API | Pay-per-use | $30–80/mo | Yes |
| Airtable | Existing | $0 | No |
| Railway (ECAS scraper) | Hobby/Pro | $10–20/mo | Yes |
| Reducto AI | Starter | $50–100/mo | Yes |
| Apollo.io | Starter | $49/mo | Yes |
| Proxycurl | Starter | $49/mo | Yes |
| Zerobounce | Pay-per-use | $10–20/mo | Yes |
| Smartlead | Existing | $0 | No |
| Expandi.io | Basic | $99/mo | Yes |
| Close CRM | Startup (1 user) | $49/mo | Yes |
| FMP Ultimate | Transcript access | $100–200/mo | Yes |
| ECAS sending domain + Google Workspace | | $15/mo | Yes |
| **Total incremental** | | **~$460–680/mo** | |

**Payback math:** 1 contract in power/grid EPC space = $500K–$50M in contract value for the client. At $25K–$50K performance fee per signed contract, first deal pays back 6+ months of tool costs in a single close.

**Cost reduction for validation phase:** Skip Reducto (process IRPs manually), skip FMP (use Seeking Alpha manually), skip Expandi (email only for 30 days) → reduces to ~$220/mo while proving signal quality.

---

## 12. REAL MID-TIER TARGET COMPANIES

### Virginia / Mid-Atlantic

| Company | Size | Signal | Why Target |
|---|---|---|---|
| Harlan Electric (MYR Group sub) | Mid-tier subsidiary | MYR Group Q2 2025 highlighted data center/clean energy boom | Regional T&D operator, active in VA/DC metro |
| Pike Electric | ~$500M | Dominion preferred contractor list | Direct Dominion work, substation EPC |
| Expanse Electrical | <$100M | Explicitly markets data center power infrastructure | Named ICP match |
| PowerSecure (Southern Company sub) | Mid-tier | On-site generation + utility interconnection | Data center distributed power |
| S&N Communications | <$200M | Utility infrastructure specialist | VA market focus |

### Texas

| Company | Size | Signal | Why Target |
|---|---|---|---|
| Primoris Services (PRIM) | ~$1.7B potential | Record gas revenue, shift to transmission/substation | Public company, subs are mid-tier scale |
| Willbros Group (acquired by Primoris) | Was mid-tier | Integration phase = new vendor eval window | |
| Ames Construction | $300M+ | Texas infrastructure focus | Grid + heavy civil |

### National (Mid-Tier Graduates — Study for ICP Definition)

| Company | What Happened | Lesson |
|---|---|---|
| MMR Group | $2.33B revenue in 2024 (67% YoY) — built utility services division for data centers | Was perfect ICP 2 years ago |
| CEC Facilities Group | Acquired for $505M in 2025 — was $390–415M revenue | Perfect ICP before acquisition |

These graduated companies show the trajectory — find the firms that are where MMR/CEC were 2–3 years ago.

---

## 13. CRITICAL PATH

```
Day 1:     Buy ECAS sending domain → start 3-week warmup (hard constraint)
           Create Airtable ECAS base + schema

Week 1:    All data collection workflows (need Airtable to write to)
    ↓
Week 2:    Claude signal processor (needs signals_raw populated to test)
           Deploy Railway ECAS scraper microservice
    ↓
Week 3:    Contact enricher (needs projects.owner_company/epc_company)
           Apollo.io + Proxycurl accounts active
    ↓
Week 4:    Outreach launcher (needs contacts table + approved contacts)
           Smartlead campaign created manually (must exist before launcher pushes leads)
           Domain warmup complete (3 weeks from Day 1)
    ↓
Week 5:    Close CRM (must receive replied contacts from Reply Handler)
           FMP Ultimate API key stored in Doppler
    ↓
Week 5+:   SLA Monitor (needs Close CRM populated)
Week 6:    LinkedIn / Expandi (independent of Close)
Week 7:    Conference monitor (needs contacts table to cross-reference)
Week 8:    Guarantee tracking (needs deal data from Close)
```

**Hard dependencies in order:**
1. Airtable schema → everything else
2. Smartlead campaign created manually → Workflow 8
3. ECAS Railway service deployed → Workflow 6 (PUC PDFs)
4. Domain purchased Week 1 → first emails Week 4
5. Apollo.io + Proxycurl active before Week 3
6. Close CRM API key in Doppler before Week 5

---

## APPENDIX: Existing Credentials to Reuse

All stored in n8n at `entagency.app.n8n.cloud`:

| Service | n8n Credential ID |
|---|---|
| Airtable | `dAoeOLbTnBUK1gTy` |
| Google Drive | `JBWswZ7Y4bcX5Fpf` |
| Google Sheets | `Qa1HC1hAtO3zjeNE` |
| Gmail OAuth | `LrrTIA7Dv6yJoAuP` |
| Anthropic (Claude API) | `MwxIqQP3l6cUcwcZ` |
| Slack | `EMdoV2Sq9neZV1Tn` |

New credentials needed for ECAS:
- Apollo.io API key → add to n8n + Doppler
- Proxycurl API key → add to n8n + Doppler
- Zerobounce API key → add to n8n + Doppler
- FMP Ultimate API key → add to n8n + Doppler
- Close CRM API key → add to n8n + Doppler
- Reducto AI API key → add to n8n + Doppler
- Expandi.io API key → add to n8n + Doppler

---

*End of ECAS Master Planning Document*
*Next action: Decide — build the system first, or build the sales motion first (outreach sequences + call script) to start selling ECAS as a service while the system is being built.*
