# ECAS — Enterprise Contract Acquisition System

> Signal-driven enterprise contract acquisition for mid-tier power/grid EPCs ($20M–$300M).
> Positioning: **"We get you on the short-list before the RFP drops."**

**Brand:** [ContractMotion.com](https://contractmotion-site-production.up.railway.app) · **API:** [ecas-scraper-production.up.railway.app](https://ecas-scraper-production.up.railway.app)

---

## Pipeline Architecture

![ECAS Pipeline](docs/diagrams/pipeline-v3.png)

*Full pipeline: Signal collection → Claude Haiku extraction → sector scoring → Apollo enrichment → Smartlead delivery. Self-healing layer with circuit breaker and AI diagnosis on all failures. [Edit source](docs/diagrams/pipeline-v3.d2)*

---

## Stack

| Layer | Tech | Notes |
|-------|------|-------|
| Compute | Railway | $5-20/mo flat · FastAPI + APScheduler |
| Signals | USASpending.gov, RSS, SEC 13F, Politician trades, FMP earnings | FERC/PJM broken — EIA API fix pending |
| AI | Claude Haiku | Signal extraction + self-healing diagnosis |
| Enrichment | Apollo.io + Findymail | Org search → people search → bulk reveal → fallback |
| CRM | Airtable `appoi8SzEJY8in57x` | signals_raw, projects, contacts, deals |
| Outreach | Smartlead | 6 campaigns across Power/DC/Water/Industrial/Defense/DFR |
| Alerts | Slack | Run summaries + error escalation with retry commands |

---

## Signal Sources

| Source | Job | Status |
|--------|-----|--------|
| USASpending.gov | `gov_contracts` | ✅ 662 contracts/run |
| Politician stock trades | `politician_trades` | ✅ Every 4h |
| RSS feeds | `rss_feeds` | ✅ Every 6h |
| SEC 13F filings | `sec_13f` | ✅ Weekly Mon 7am |
| Earnings transcripts | `earnings_transcripts` | ✅ Weekly Tue 6am (FMP API) |
| FERC eLibrary | `ferc_poller` | ❌ Cloudflare-blocked — replace with EIA API |
| PJM interconnection queue | — | ❌ URL changed (404) |

---

## Smartlead Campaigns

| Campaign ID | Sector | Status |
|-------------|--------|--------|
| `3005694` | Power & Grid | ✅ Active |
| `3040599` | Data Center & AI Infrastructure | ✅ Active |
| `3040600` | Water & Wastewater | ✅ Active |
| `3040601` | Industrial & Manufacturing | ✅ Active |
| `3095136` | Defense | ✅ Active |
| `3103531` | Drone DFR | ✅ Active |

6 emails per sequence · Day 0/4/9/15/22/30

---

## Admin API

```bash
# Check all job statuses
curl https://ecas-scraper-production.up.railway.app/admin/status

# Trigger any job manually
curl -X POST https://ecas-scraper-production.up.railway.app/admin/run/{job_id}

# Job IDs: politician_trades, sec_13f, gov_contracts, ferc_poller, rss_feeds,
#           claude_extraction, sector_scoring, enrichment, smartlead,
#           weekly_digest, earnings_transcripts, budget_window_monitor, populate_projects
```

---

## Local Dev

```bash
# Secrets via Doppler (project: ecas, config: dev)
doppler run --project ecas --config dev -- uvicorn api.main:app --reload
```

---

## Diagrams

| File | Description |
|------|-------------|
| [`pipeline-v3.png`](docs/diagrams/pipeline-v3.png) | Full pipeline — horizontal LTR layout (current) |
| [`pipeline-v3.d2`](docs/diagrams/pipeline-v3.d2) | D2 source — edit with `d2` CLI |
| [`pipeline-d2.svg`](docs/diagrams/pipeline-d2.svg) | Vertical flowchart with self-healing detail |

To regenerate: `d2 --layout elk --theme 1 --pad 50 docs/diagrams/pipeline-v3.d2 docs/diagrams/pipeline-v3.png`
