# Job Posting Signal Monitor — Spec

**Repo:** ECAS (`~/Desktop/ECAS/`)
**Trigger:** n8n Cron — every Tuesday + Friday 8am CT
**Purpose:** Detect healthcare businesses posting growth-mode jobs = scaling signal

## Signal Logic
A healthcare business posting for specific roles is actively scaling. Outreach timed to job posting catches them at peak investment mindset.

## Target Job Postings by Niche

| Job Title Keywords | Business Type | Signal Meaning |
|-------------------|---------------|----------------|
| "pharmacy technician" OR "compounding specialist" | Compounding pharmacy | Scaling capacity — needs prescribers to fill it |
| "nurse injector" OR "aesthetic injector" OR "aesthetician" | Med spa | Adding providers — needs patient/referral volume |
| "sleep technologist" OR "polysomnography" | Sleep lab | Expanding capacity |
| "IV therapy" OR "infusion nurse" | IV infusion center | Scaling — needs physician pipeline |
| "patient coordinator" + (LASIK OR "vision correction") | LASIK center | Growth hire — front-end build |
| "pharmacy rep" OR "business development" + pharmacy | Compounding pharmacy | Actively trying to grow, not succeeding organically |

## Data Sources
1. **Indeed API** — `https://api.indeed.com/ads/apisearch` (publisher key needed)
2. **Clay** — job posting enrichment column (pulls from LinkedIn/Indeed)
3. **Apify — Indeed Scraper** — `apify/indeed-scraper` actor

## n8n Workflow Steps
1. **Cron Trigger** — Tue + Fri 8am
2. **HTTP Request** — Indeed API search per keyword set + location (US, healthcare industry)
3. **Filter** — company size indicators (small/medium, exclude hospital systems + chains)
4. **Extract company domain** — from job posting
5. **NPI lookup** — search NPI registry by company name + location to get NPI/taxonomy
6. **Apollo enrichment** — find owner/decision-maker contact at company
7. **Findymail** — verify/find email
8. **Airtable dedup check** — skip if already in system
9. **Airtable create** — add with `source: job_posting_signal`, `signal_type: growth_hire`
10. **Smartlead enroll** — appropriate campaign with job-posting angle variant
11. **Slack notify** — `#ecas-ops` daily digest of new job posting signals

## Email Angle for This Signal
Subject: `saw you're hiring a [role]`
> "Saw {{company}} is hiring a {{job_title}} — usually means you're scaling capacity. The businesses that time physician referral outreach with a capacity hire never have to slow down. Worth a 15-min call?"
