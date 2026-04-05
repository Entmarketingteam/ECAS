# ECAS Contractor Signal Expansion — Design Spec
**Date:** 2026-04-05
**Status:** Approved for implementation
**Scope:** System A only — ECAS signal scrapers. System B (ABR Bid OS) is a separate future spec.

---

## What We're Building

Six new signal scrapers for the ECAS contractor pipeline, plus scheduler wiring and signal weight updates. All scrapers feed `Airtable signals_raw` with `vertical_type = "contractor"`. The existing orchestrator picks them up automatically — no orchestrator changes needed.

**Verticals served:** Commercial Roofing · Commercial Janitorial · Pest Control

---

## Decisions Made

| Question | Answer |
|----------|--------|
| Association members = direct leads? | **Yes** — membership alone qualifies for outreach pipeline |
| SAM.gov usage | **Lead signal** — companies winning gov contracts are growing ICP leads |
| Association enrollment threshold | **Bump `industry_association_member` weight to 50 pts** (warm floor) so scraped members enter the pipeline |
| New signals to add | RTO/office reopening, commercial property sold, OSHA citations, commercial lease signed |
| Geographic scope | Per-vertical `geo_focus` from `VERTICAL_ICPS` config (TX, FL, GA, NC, OH primary) |
| Parallelism | 4 agents build scrapers concurrently, main thread handles config + scheduler + tests |

---

## Architecture

```
contractor/signals/
  hail_events.py           ✅ DONE — NOAA hail scraper
  association_scraper.py   🔨 NEW — NRCA + NPMA + ISSA + state chapters
  sam_gov_watcher.py       🔨 NEW — SAM.gov contract award lead signal
  permit_watcher.py        🔨 NEW — Socrata permit APIs (Austin/Dallas/Charlotte/Atlanta)
  fm_job_watcher.py        🔨 NEW — Apollo FM/Ops hiring signal + job change detection
  competitor_watcher.py    🔨 NEW — Google Maps negative reviews + franchise expansion RSS
  rto_watcher.py           🔨 NEW — RTO/office reopening RSS + commercial lease news
```

All scrapers share the same output contract:
```python
{
    "company_name": str,
    "company_domain": str,        # best-guess or empty
    "vertical": str,              # "Commercial Roofing" | "Commercial Janitorial" | "Pest Control"
    "vertical_type": "contractor",
    "signal_type": str,           # matches CONTRACTOR_SIGNAL_WEIGHTS key
    "detected_at": str,           # ISO8601 UTC
    "source": str,                # "NRCA" | "SAM.gov" | "Socrata-Austin" | etc.
    "processed": False,
    "raw_data_json": dict,        # source-specific detail
}
```

Scrapers push directly to Airtable `signals_raw` (base `appoi8SzEJY8in57x`, table `tblAFJnXToLTKeaNU`).

---

## Scraper Specs

### 1. `association_scraper.py`
**Signal type:** `industry_association_member` (50 pts — bumped from 20)
**Sources:**
- NRCA Find-a-Contractor: `https://www.nrca.net/roofing/find-a-contractor` (paginated by state)
- NPMA Find-a-Pro: `https://www.npmapestworld.org/find-a-pro` (zip/state search)
- ISSA member directory: `https://access.issa.com/dir` (HTML paginated)
- State chapter fallback: simple HTML scrape of KRCA, TRA, FRSA pages

**Approach:** `requests` + `BeautifulSoup` for HTML directories. Playwright via `playwright` async for JS-rendered pages. Parallel by state using `ThreadPoolExecutor`.
**Output:** One signal record per company. Domain inferred from website field if present.
**Schedule:** Weekly (Sunday 3am) — member lists don't change daily.
**Dedup:** Skip if `company_domain` already has a non-stale `industry_association_member` signal in Airtable (within 30 days).

### 2. `sam_gov_watcher.py`
**Signal type:** `government_contract_win` (new — 45 pts)
**Source:** SAM.gov API v2 — `https://api.sam.gov/opportunities/v2/search`
**Filter:** NAICS codes 238160 (roofing), 561720 (janitorial), 561710 (pest control). Award notices only. Target states from `geo_focus`.
**Output:** Awardee company name + location → signal record. Domain enrichment deferred to orchestrator (Apollo lookup).
**Schedule:** Every 24h (5am daily).
**API key:** Free, but rate-limited. Use `SAM_GOV_API_KEY` from Doppler (register at sam.gov/api).

### 3. `permit_watcher.py`
**Signal type:** `commercial_permit_pulled` (65 pts — already defined)
**Sources:** Socrata APIs already in `PERMIT_SOURCES` config:
- Austin: `data.austintexas.gov`
- Dallas: `www.dallasopendata.com`
- Charlotte: `data.charlottenc.gov`
- Atlanta: `data.atlantaga.gov`

**Filter:** Commercial permits > $50K, roofing/janitorial/pest-relevant categories.
**Schedule:** Every 12h.

### 4. `fm_job_watcher.py`
**Signal type:** `fm_job_posting` (40 pts) + `fm_job_change` (75 pts — when person detected)
**Sources:**
- Apollo `mixed_people/api_search` for titles "Facilities Manager", "Property Manager", "Building Operations" with recent job change flag
- Indeed RSS feeds for FM/Ops job postings in target geographies (free, no auth)

**Note:** Apollo job-change detection uses the `employment_history` change flag, not a real-time webhook. Treated as 14-day signal (1.0x recency multiplier).
**Schedule:** Every 8h.

### 5. `competitor_watcher.py`
**Signal types:** `negative_review_competitor` (35 pts), `franchise_new_territory` (70 pts)
**Sources:**
- Google Maps Places API — search for Jan-Pro, Coverall, Orkin, Rollins in target cities. Detect new listings within 30 days → `franchise_new_territory`.
- RSS feeds: Jan-Pro, Coverall, ServiceMaster, Rollins press release feeds → parse for expansion announcements.
- Google Places reviews for known competitors in target geographies — flag 1-2 star recent reviews.

**Schedule:** Every 24h.

### 6. `rto_watcher.py`
**Signal types:** `rto_announcement` (new — 40 pts, janitorial-only), `commercial_lease_signed` (new — 45 pts, all verticals)
**Sources:**
- RSS aggregation: major employer RSS + Google News RSS for "[Company] return to office" + "[City] commercial lease"
- CoStar/LoopNet lease signings (if accessible without paywall — fallback to Google News RSS)

**Schedule:** Every 12h.

---

## Signal Weight Updates (config.py)

```python
# Changes from current:
"industry_association_member": 50,   # was 20 — bumped to warm floor
"government_contract_win": 45,       # new
"rto_announcement": 40,              # new (janitorial only)
"commercial_lease_signed": 45,       # new (all verticals)
"osha_citation": 55,                 # new (pest control + janitorial)
```

---

## Scheduler Wiring (scheduler.py additions)

```python
# Association scraper — weekly Sunday 3am
scheduler.add_job(run_association_scraper, CronTrigger(day_of_week="sun", hour=3), id="contractor_associations")

# SAM.gov watcher — daily 5am
scheduler.add_job(run_sam_gov_watcher, CronTrigger(hour=5), id="contractor_sam_gov")

# Permit watcher — every 12h
scheduler.add_job(run_permit_watcher, IntervalTrigger(hours=12), id="contractor_permits")

# FM job watcher — every 8h
scheduler.add_job(run_fm_job_watcher, IntervalTrigger(hours=8), id="contractor_fm_jobs")

# Competitor watcher — daily 6am
scheduler.add_job(run_competitor_watcher, CronTrigger(hour=6), id="contractor_competitors")

# RTO watcher — every 12h
scheduler.add_job(run_rto_watcher, IntervalTrigger(hours=12), id="contractor_rto")
```

---

## Testing Strategy

Each scraper gets a unit test with mocked HTTP responses. No live API calls in tests.
Integration test extension: add new signal types to `test_pipeline_integration.py` happy path.

Test files:
- `contractor/tests/test_association_scraper.py`
- `contractor/tests/test_sam_gov_watcher.py`
- `contractor/tests/test_permit_watcher.py`
- `contractor/tests/test_signal_scrapers_shared.py` (shared fixtures + output contract validation)

---

## Out of Scope (System B — Future)

- ABR Construction bid automation
- RFP ingestion and proposal drafting
- Drone workflow integration
- ConstructConnect / Dodge scraping
- Bid pipeline Airtable tracking

---

## Build Order (parallel agents)

| Agent | Files | Dependency |
|-------|-------|------------|
| Agent 1 | `association_scraper.py` + test | None |
| Agent 2 | `sam_gov_watcher.py` + `permit_watcher.py` + test | None |
| Agent 3 | `fm_job_watcher.py` + `competitor_watcher.py` | None |
| Agent 4 | `rto_watcher.py` + shared test fixtures | None |
| Main | `config.py` signal weight updates + `scheduler.py` wiring | After all agents |
