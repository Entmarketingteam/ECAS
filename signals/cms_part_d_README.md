# CMS Part D Physician Targeting Pipeline

## What It Does

Pulls Medicare Part D prescribing data from CMS to build a physician targeting list for compounding pharmacy clients.

This identifies physicians **already writing the exact scripts** a pharmacy wants to compound — not keyword-guessed specialties, but actual prescription volume data. It's what pharma reps pay IQVIA $50k+/year to access. We get it free via the CMS public API.

**Pipeline steps:**

1. Queries CMS Part D API for target drugs (semaglutide, tirzepatide, estradiol, progesterone, testosterone, naltrexone) filtered to TX + `Tot_Clms >= 10`
2. Runs 6 concurrent API workers (one per drug), with automatic pagination
3. Deduplicates by NPI — keeps highest-claim drug as `primary_drug`, lists others in `secondary_drugs`
4. Enriches each NPI via the NPI Registry API (practice address + phone) using 10 concurrent workers
5. Scores and sorts by `priority_score = (total_claims * 0.5) + specialty_weight`
6. Outputs a clean CSV ready for Clay import

**Specialty weights used in scoring:**

| Specialty | Weight |
|-----------|--------|
| OB-GYN / Obstetrics & Gynecology | 10 |
| Obesity Medicine | 10 |
| Integrative / Functional Medicine | 9 |
| Internal Medicine / Endocrinology | 8 |
| Family Medicine / Family Practice | 7 |
| Nurse Practitioner / PA | 6 |
| Other | 5 |

---

## Run Command

```bash
doppler run --project ent-agency-automation --config dev -- \
  python signals/cms_part_d_pipeline.py --state TX --drugs semaglutide,estradiol,testosterone
```

Full TX pull with all default drugs:

```bash
doppler run --project ent-agency-automation --config dev -- \
  python signals/cms_part_d_pipeline.py --state TX
```

---

## CLI Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--state` | `TX` | 2-letter state abbreviation |
| `--drugs` | semaglutide,tirzepatide,estradiol,progesterone,testosterone,naltrexone | Comma-separated generic drug names |
| `--min-claims` | `10` | Minimum total Medicare claims — filters low-volume prescribers |
| `--output-dir` | `signals/output/` | Directory for the output CSV |
| `--dataset-id` | `9552919b-5568-4b4b-8f82-8e4d2e0a0ef4` | CMS dataset ID (update annually) |
| `--cms-workers` | `6` | Concurrent CMS API threads (one per drug) |
| `--npi-workers` | `10` | Concurrent NPI registry lookup threads |
| `--skip-npi-lookup` | off | Skip NPI enrichment step (faster, no phone/address) |
| `--verbose` | off | Enable DEBUG logging |

---

## Output

CSV saved to: `signals/output/cms_{state}_physicians_{YYYYMMDD}.csv`

**Columns:**

| Column | Description |
|--------|-------------|
| `npi` | 10-digit NPI number |
| `first_name` | Physician first name |
| `last_name` | Physician last name / org name |
| `specialty` | CMS specialty description |
| `practice_name` | Practice name (from NPI Registry) |
| `address` | Practice street address |
| `city` | Practice city |
| `state` | Practice state |
| `zip` | 5-digit zip |
| `phone` | Practice phone |
| `primary_drug` | Highest-volume drug this physician prescribes |
| `total_claims` | Total Medicare Part D claims for primary drug |
| `total_day_supply` | Total day supply across all matched drugs |
| `secondary_drugs` | Other matched drugs (pipe-delimited with claim counts) |
| `priority_score` | `(total_claims * 0.5) + specialty_weight` — sort field |
| `specialty_weight` | Specialty score component |

---

## How Output Feeds Into Clay

**Step 1 — Import CSV to Clay**

Upload `cms_tx_physicians_YYYYMMDD.csv` as a new Clay table. NPI is the unique key.

**Step 2 — Clay enrichment columns to add:**

```
Website        → Clay web scrape (Clearbit lookup by practice name + zip)
LinkedIn URL   → LinkedIn enrichment by name + specialty
Email          → Waterfall: Findymail → Hunter → Apollo
                 Use "Prescribes [primary_drug]" as personalization variable
Practice Size  → Apollo org enrichment by practice name
License Status → State medical board check (TX: tmb.state.tx.us)
```

**Step 3 — Smartlead sequence load**

Filter Clay table: `priority_score >= 15` → export to Smartlead.

Personalization field for sequence opener:
```
"As a physician in [city] who prescribes [primary_drug] for your patients..."
```

Use specialty-matched sequences:
- OB-GYN / hormone prescribers → BHRT track
- Internal Medicine / Obesity Med → GLP-1 track
- Integrative / Functional → compounded hormone + GLP-1 track

---

## Data Limitations

- **Medicare only** — misses private-pay, cash-pay, and Medicaid prescribers. Supplement with Apollo specialty keyword search for functional medicine / concierge MDs.
- **1-year lag** — 2022 data is current as of 2026. Check `data.cms.gov` for 2023 dataset ID when released.
- **Dataset ID changes annually** — update `--dataset-id` when CMS releases new year. Current ID: `9552919b-5568-4b4b-8f82-8e4d2e0a0ef4` (2022 dataset).
- **Telehealth gap** — does not capture out-of-state telehealth prescribers writing into TX.

---

## Environment Variables (Doppler)

| Key | Required | Description |
|-----|----------|-------------|
| `CMS_API_KEY` | No | CMS API key for higher rate limits. Without it, CMS applies stricter throttling. Get one free at `data.cms.gov/developer`. |

---

## Updating for a New Year's Dataset

1. Go to `data.cms.gov/provider-summary-by-type-of-service/medicare-part-d-prescribers`
2. Select "Medicare Part D Prescribers - by Provider and Drug"
3. Copy the API dataset ID from the URL
4. Run with `--dataset-id <new-id>` or update `CMS_DATASET_ID` in the script
