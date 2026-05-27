# Building-Permit Signal — Findings & Recommendation

**Date:** 2026-05-25
**Context:** Evaluate a proposed "IntentSignal permit engine" (municipal building permits → infra-EPC cold-outbound leads) for ContractMotion.
**Verdict:** Built and verified a working module, but **city building permits are a poor primary source for ContractMotion's infra-EPC ICP.** Do NOT wire to the live auto-enroll pipeline as-is.

---

## Executive Summary

| Question | Answer |
|---|---|
| Does the proposed engine fit ContractMotion? | **No.** Wrong ICP (cleaning/elevator/homebuilders), wrong LLM (Gemini vs ECAS Claude), wrong store (SQLite vs Supabase), reinvents SAM.gov. |
| Can municipal permits feed the *real* infra ICP? | **Weakly.** Verified live: Chicago yields ~11 candidate leads/year at ~30-40% precision even after tightening. |
| Why so weak? | Heavy-infra projects (substations, treatment plants, data centers, fabs) are **not permitted at municipal building desks**. They route through utility/ISO interconnection queues, state SRF/environmental programs, and federal procurement. |
| What was shipped | `signals/building_permits.py` — clean, verified, dedup-safe, CLI-only (NOT in scheduler). Useful as a research tool, not a live lead pipe. |

## What was verified (live, 2026-05-25)

- **Austin `3syk-w9eu`** — no contractor name, no valuation field → unusable. (The pasted "ready tonight" code targeted endpoints like this without checking.)
- **Chicago `ydr8-5enu`** — ✅ has `reported_cost`, `work_description`, 4 typed contacts (`ELECTRICAL CONTRACTOR`, `CONTRACTOR-GENERAL CONTRACTOR`, …). Only viable verified source.
- **NYC `ipu4-2q9a`** — has `permittee_s_business_name` but no valuation; filtered pulls were flaky. Left documented, not enabled.

## Why precision is low (real examples)

Loose keywords mis-fired badly:
- `factory` → **"Burlington Coat Factory"** (retail brand)
- `generator` / `transformer` → incidental backup equipment in office / car-wash fit-outs
- `solar` → rooftop panels on a building

After tightening to high-precision terms only, surviving Chicago hits over 12 months: ~11, of which genuinely ICP-relevant: a handful (a substation upgrade, a wastewater pH-adjustment job, a switchgear building). Volume is too low and noise too high to justify auto-enrollment into live Smartlead campaigns — doing so risks deliverability and ContractMotion sender reputation for negligible lead gain.

## Charlotte & Nashville (requested specifically)

| City | Status | Endpoint | Result |
|---|---|---|---|
| **Charlotte** (Mecklenburg) | ✅ Scrapable, wired | `meckgis.mecklenburgcountync.gov/.../BuildingPermits/FeatureServer/0` (ArcGIS) | Rich `bldgcost`/`projname`/`projdesc`/`ownname`. Real megaprojects pulled: **$651M hospital bed tower, $340M airport terminal, $127M Centene HQ, Ally Charlotte Center**. BUT exposes the **owner/developer, not the EPC contractor**. Of 76 permits >$5M in 12mo, only **1** matched an ECAS infra sector (rest = hospitals/offices/airport/residential). |
| **Nashville** (Davidson) | ❌ No clean API | — | Migrated off Socrata; every old dataset 302-redirects to `hub.arcgis.com/legacy`. Permits now live behind the Accela Citizen Access portal — no bulk API. Would require brittle portal automation (Playwright), ToS-gray, not worth it. |

**Takeaway:** Charlotte's big-project feed is excellent data but **owner-side** — it tells you a $650M hospital is going up, not which EPC won the electrical/mechanical scope. For ContractMotion (sells *to* EPCs), that's an intro/ABM signal at best, and infra-sector matches are ~1/year. Nashville isn't accessible via open data at all.

## Recommendation — where the "money flowing" signal actually lives

ECAS already polls the right sources; deepen these instead of scraping 50 city permit schemas:

1. **Interconnection queues (FERC / PJM / ERCOT)** — `signals/ferc_poller.py`, `signals/pjm_poller.py` already exist. These are *pre-construction* grid/data-center/storage projects = the truest "before the RFP drops" signal. Highest ROI to expand (add MISO, SPP, CAISO, NYISO queues).
2. **State Revolving Funds (CWSRF/DWSRF)** — funded water/wastewater project lists = money committed. Strong fit for the Water sector campaign.
3. **Paid large-project DB (Dodge / ConstructConnect / Shovels.ai)** — if a true national construction feed is wanted, these carry valuations + named GCs/EPCs nationwide. This is the professional version of what city permits only gesture at — worth a budget conversation, not a scraping project.

## The module (`signals/building_permits.py`)

- Pulls high-valuation commercial permits from verified Socrata sources, classifies to ECAS sectors via high-precision keywords, extracts the contractor company.
- SQLite dedup (`building_permits_seen`), Supabase upsert to `epc_company_leads` (dotless company-slug domain → collision-free `(domain,source)` key, bridge-safe), CSV to `signals/output/`.
- **Not added to `scheduler.py`** — runs only via CLI:
  ```bash
  doppler run --project ecas --config dev -- python3 signals/building_permits.py --dry-run
  doppler run --project ecas --config dev -- python3 signals/building_permits.py --metro chicago --days 30 --min-cost 1000000
  ```
- To enable for real: validate per-metro precision first, and consider routing to `verification_review_queue` (human gate) rather than direct auto-enroll.
