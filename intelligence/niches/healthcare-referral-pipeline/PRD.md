# Healthcare Referral Pipeline — Product Requirements Document

**Version:** 1.0
**Date:** 2026-04-05
**Owner:** ContractMotion
**Status:** Ready to Build

---

## 1. What We're Building

A signal-driven cold outreach system that:
1. Identifies referral-dependent healthcare businesses at the moment they need a physician pipeline
2. Builds targeted physician lists using public government data (not just Apollo)
3. Delivers personalized cold email sequences that connect healthcare businesses with their referral sources
4. Runs continuously as a self-refreshing pipeline on existing ECAS infrastructure

**Positioning:**
> "We build physician referral pipelines for independent healthcare businesses."

This is one repeatable playbook across a cluster of niches — the list and copy changes per niche, the infrastructure is identical.

---

## 2. Beachhead Niche: Compounding Pharmacies

### Why First
- 7,500+ 503A pharmacies, single owner-pharmacist DM
- GLP-1 revenue cliff (2026) = current urgent pain
- Zero cold email competition — 100% referral-dependent
- $3,500–$4,500/month retainer, 45–60 day sales cycle
- Same ECAS infrastructure, zero new build cost

### Offer
Connect compounding pharmacies with prescribing physicians (BHRT, functional medicine, weight loss, peptides, dermatology) in their geography via targeted cold email outreach. Typically 5–10 net-new active prescribers per 90-day pilot.

### Pricing
| Item | Amount |
|------|--------|
| One-time setup | $1,500 |
| Monthly retainer | $3,500–$4,500/mo |
| 90-day pilot total | ~$12,000–$15,000 |

### Cold Email Sequences (ready to load into Smartlead)

**To: Compounding Pharmacy Owners**

**Email 1 — Day 1**
Subject: `how new prescribers find [Pharmacy Name]`

> Hi {{first_name}},
>
> Quick question — when a physician who's never worked with you before needs a compounding partner, how do they find {{company}}?
>
> Most pharmacy owners I ask say: referral from another doctor, or they just called out of the blue one day.
>
> Which means your prescriber network grows when you get lucky.
>
> We run targeted cold email outreach to physicians on behalf of compounding pharmacies — connecting you directly with BHRT, functional medicine, and weight management prescribers in your area who don't know you exist yet.
>
> Typically adds 5–10 net-new active prescribers in the first 90 days.
>
> Worth a 15-minute call to see if the math makes sense for {{company}}?

**Email 2 — Day 4**
Subject: `the GLP-1 cliff`

> {{first_name}} —
>
> Compounding pharmacies that built around semaglutide are running into the same problem right now: the FDA shortage window is closing and those prescriber relationships are thinning out.
>
> The ones that are fine used that run to diversify — BHRT, peptides, dermatology, functional medicine. Prescribers who'll still be there when GLP-1 compounding is fully wound down.
>
> That's what we help build. A prescriber pipeline into the specialties that aren't going anywhere.
>
> One new prescriber writing 5 scripts/month at $300 average is $1,800/month recurring. We typically add 5–10 in 90 days.
>
> 15 minutes this week?

**Email 3 — Day 9**
Subject: `last one from me`

> {{first_name}} —
>
> Not going to keep filling your inbox.
>
> If prescriber diversification is something {{company}} is thinking about this year — specifically getting in front of BHRT, longevity, or functional medicine physicians who've never heard of you — I'd love to show you exactly how we'd do it.
>
> If the timing isn't right, no problem at all.
>
> Either way, best of luck with the pharmacy.

---

## 3. Full Niche Cluster (Expand After Beachhead)

All share the same structural problem: growth gated by physician/specialist referrals never systematically pursued.

| Niche | Referral Source They Need | Score |
|-------|--------------------------|-------|
| Compounding Pharmacies | Prescribing physicians by specialty | 9.0 |
| Specialty / Functional Medicine Labs | Functional medicine, integrative MDs | 8.5 |
| Medical Spas / Aesthetics Clinics | Dermatologists, plastic surgeons, OB-GYNs | 8.0 |
| IV Therapy / Infusion Centers | Functional medicine MDs, concierge practices | 8.0 |
| LASIK / Refractive Surgery Centers | Optometrists (OD co-management) | 8.0 |
| Audiology Clinics | ENTs, primary care, geriatricians | 7.5 |
| Sleep Labs / Sleep Centers | Primary care, pulmonologists, cardiologists | 7.5 |
| DME Suppliers (specialty) | Orthopedic surgeons, neurologists | 7.5 |
| Ambulatory Surgery Centers | Surgeons needing OR time | 7.0 |
| Home Health Agencies | Hospital discharge planners, primary care | 7.0 |
| Imaging Centers / Radiology | Primary care, orthopedic, neurology | 7.0 |
| Fertility Clinics | OB-GYNs, endocrinologists | 7.0 |
| Wound Care Centers | Vascular surgeons, podiatrists, diabetologists | 7.0 |

---

## 4. Data Sources (No Apollo Required)

### Tier 1 — Government Data (Free, Complete)

#### CMS Part D Prescribing Data — Primary Physician Targeting
`data.cms.gov/provider-summary-by-type-of-service/medicare-part-d-prescribers`

Shows every physician in the US, what drugs they prescribed, claim count — by geography and year.

**Use case for compounding pharmacy:**
Pull every physician within 25 miles of a client pharmacy who prescribed estradiol, progesterone, testosterone, semaglutide, or tirzepatide in the last 12 months. Sort by claim volume. These are already writing the exact scripts the pharmacy wants.

Filter fields:
- `Gnrc_Name` — generic drug name (e.g., "Semaglutide", "Estradiol")
- `Prscrbr_State_Abrvtn` — state
- `Prscrbr_Zip5` — zip code
- `Tot_Clms` — total claims (filter min 10+)
- `Prscrbr_Type` — specialty

**This is what pharma reps pay IQVIA $50k+/year for. It's free.**

#### NPI Registry — Business Discovery + Physician Contact Info
`npiregistry.cms.hhs.gov/api`

Key taxonomy codes:
| Code | Type |
|------|------|
| `3336C0003X` | Compounding pharmacy |
| `3336H0001X` | Home infusion pharmacy |
| `261QA0600X` | Ambulatory surgery center |
| `261QR0208X` | Radiology / imaging center |
| `261QS1200X` | Sleep lab |
| `207Q00000X` | Family medicine |
| `207QH0002X` | Obesity medicine |
| `207RG0100X` | OB-GYN |
| `207R00000X` | Internal medicine |
| `2084N0400X` | Neurology |

Weekly API poll → filter by registration date (new = signal) or bulk pull by taxonomy + state.

#### State Board of Pharmacy License Databases
Every state publishes full pharmacy licensee lists. Most downloadable as CSV. More complete than Apollo for small independents.
- Texas: pharmacy.texas.gov
- Florida: flhealthsource.gov
- California: pharmacy.ca.gov
- All 50: NABP connects to each state board

#### State Medical Board Databases
Same for physicians — full licensee lists with specialty, downloadable by state.

#### CMS Open Payments (Sunshine Act)
`openpaymentsdata.cms.gov`
Physicians receiving pharma/device payments = high-volume prescribers. Proxy for identifying most active prescribers in any specialty.

---

### Tier 2 — Association Directories (Pre-Qualified, High Intent)

| Association | Members | URL |
|-------------|---------|-----|
| PCAB | Accredited compounding pharmacies | pcab.org/find-a-pharmacy |
| APC | Alliance for Pharmacy Compounding members | a4pc.org |
| NAMS | Certified menopause practitioners | menopause.org/find-a-provider |
| IFM | Functional medicine certified MDs | ifm.org/find-a-practitioner |
| A4M | Anti-aging / longevity physicians | a4m.com/find-a-doctor |
| ABOM | Board-certified obesity medicine physicians | abom.org/find-a-physician |
| AmSpa | Medical spa owners | americanmedspa.org |
| AASM | Accredited sleep labs | sleepeducation.org/find-a-facility |

---

### Tier 3 — Scraping + Enrichment

| Tool | Use |
|------|-----|
| Outscraper | Google Maps by category + geography — name, phone, website, reviews, email |
| Apify | Pre-built scrapers for Healthgrades, Zocdoc, Yelp, medical directories |
| Clay | Orchestrates everything — NPI pull, CMS enrichment, web scrape, email waterfall |
| Findymail | Email enrichment waterfall (already in ECAS stack) |

---

## 5. Signal Detection System

Signals identify businesses at the highest-intent moment. Same pattern as ECAS — signal detected → contact enriched → Smartlead enrolled.

| Signal | Source | Timing | Outreach Angle |
|--------|---------|--------|----------------|
| New NPI registration | NPI registry API (weekly poll) | Email within 7–14 days | "Most new practices wait 6 months to build referral pipeline — the ones that do it from day one win the market" |
| New state business filing | Secretary of State / OpenCorporates | Email within 14 days | Pre-opening outreach, pipeline-from-day-one angle |
| PCAB accreditation granted | PCAB directory (quarterly) | Email within 14–21 days | "Now that you're accredited, physicians will take your calls. We help you make those calls at scale." |
| AASM accreditation granted | AASM directory (monthly) | Email within 14 days | Same angle for sleep labs |
| Job posting: growth role | Indeed / LinkedIn (weekly scrape) | Email within 7 days | "Saw you're hiring [role] — we help [type] build the referral infrastructure to justify that hire" |
| FDA warning letter (pharmacy) | fda.gov/warning-letters (weekly) | Email 30–45 days post-resolution | "Compliance is handled. Now let's rebuild the prescriber pipeline." |
| State board action resolved | State board sites (weekly) | Email 30 days post-resolution | Same as above |
| New Google My Business listing | SerpAPI / Outscraper (weekly) | Email within 14 days | New business = needs pipeline |

---

## 6. Clay Workflow (Physician List for Pharmacy Clients)

```
Step 1: CMS Part D data pull
  → Filter: drug name + state/zip + min 10 claims
  → Output: physician NPI, name, specialty, zip

Step 2: NPI registry cross-reference
  → Input: NPI number from CMS
  → Output: practice address, phone, entity type, taxonomy

Step 3: State medical board validation
  → Confirm active license

Step 4: Clay enrichment
  → Website, LinkedIn, email (waterfall: Findymail → Hunter → Apollo)
  → Personalization fields: specialty, practice size, drugs prescribed

Step 5: Smartlead load
  → Specialty-matched sequence
  → Personalized: drug type, geography, prescriber volume
```

---

## 7. Smartlead Campaign Setup

| Setting | Value |
|---------|-------|
| Sending domain | Fresh neutral domain (not ContractMotion-branded) |
| Daily send limit | 40/day week 1, ramp to 60 week 2 |
| Step delays | Day 1 → Day 4 → Day 9 |
| Reply detection | Pause sequence on any reply |
| From name | Personal name, not agency name |
| Reply classification | Smartlead Signal Intelligence n8n (already live: `4ZkYDJpqg5qBXdAW`) |

---

## 8. Build Order (Priority Sequence)

### Phase 1 — Launch (Now, uses existing infrastructure)
1. ✅ Cold email sequences written (compounding pharmacy)
2. ☐ Apollo pull: 500–750 owner-pharmacist contacts
3. ☐ Supplement with state board license downloads (TX, FL, CA, NY, IL)
4. ☐ Enrich via Findymail waterfall
5. ☐ Load into Smartlead on April 6 warmed domain
6. ☐ Register neutral sending domain (health/growth adjacent)

### Phase 2 — Signal Layer (ECAS repo, n8n)
7. ☐ NPI registry weekly poller (n8n workflow)
8. ☐ Job posting monitor (Clay or Apify → Smartlead enrollment)
9. ☐ PCAB/AASM accreditation scraper (quarterly trigger)
10. ☐ FDA warning letter monitor (weekly scrape)

### Phase 3 — Physician Targeting (Clay)
11. ☐ CMS Part D data pipeline for first pharmacy client
12. ☐ Clay table: CMS + NPI + state board + email enrichment
13. ☐ Physician sequence written + loaded per specialty

### Phase 4 — Niche Expansion
14. ☐ Med spa sequences + AmSpa directory pull
15. ☐ Sleep lab sequences + AASM directory pull
16. ☐ LASIK sequences + state optometry board pull
17. ☐ Expand to remaining cluster niches

---

## 9. Proof of Concept (ContractMotion Track Record)

**Existing credibility framing for sales calls:**
> "We run cold outreach that gets hard-to-reach professional buyers to respond and book calls. We've done it for Enterprise Contract Acquisition (ECAS)-to-brand partnerships at ContractMotion. The mechanics of getting a physician to respond are the same — what changes is the offer language. We've done the work on that for compounding specifically."

**Stats to document before first pharmacy pitch:**
- ContractMotion cold outreach open rates
- Reply rates from existing campaigns
- Number of cold-sourced clients closed
- One 2–3 sentence case study in analogous-industry framing

---

## 10. Repo Structure

```
research-lab/niches/healthcare-referral-pipeline/
├── PRD.md                          ← This document
├── sequences/
│   ├── compounding-pharmacy.md     ← 3-touch owner sequence
│   ├── med-spa.md                  ← TBD
│   ├── sleep-lab.md                ← TBD
│   └── lasik.md                    ← TBD
├── data-sources/
│   ├── cms-part-d-guide.md         ← How to pull + filter CMS data
│   ├── npi-taxonomy-codes.md       ← All relevant taxonomy codes
│   └── state-board-links.md        ← All 50 state pharmacy board URLs
└── signal-specs/
    ├── npi-poller-spec.md          ← n8n workflow spec (build in ECAS repo)
    ├── job-posting-monitor-spec.md
    ├── pcab-scraper-spec.md
    └── fda-warning-letter-spec.md

ECAS repo (~/Desktop/ECAS/):
└── signals/
    ├── npi_poller.py / n8n workflow
    ├── job_posting_monitor.py
    ├── pcab_scraper.py
    └── fda_warning_letters.py
```

---

*Last updated: 2026-04-05 | Owner: ContractMotion*
