# PCAB / AASM Accreditation Scraper — Spec

**Repo:** ECAS (`~/Desktop/ECAS/`)
**Trigger:** n8n Cron — 1st of every month, 7am CT
**Purpose:** Detect newly accredited facilities (highest-intent signal — just invested in quality, now needs volume)

## Target Accreditation Bodies

| Body | What They Accredit | Directory URL | Update Frequency |
|------|-------------------|---------------|-----------------|
| PCAB | Compounding pharmacies | pcab.org/find-a-pharmacy | Quarterly |
| AASM | Sleep labs | sleepeducation.org/find-a-facility | Monthly |
| AAAASF | Surgery centers, med spas | aaaasf.org/patients/find-accredited-facility | Quarterly |
| QUAD A | Same as AAAASF | quadaaccreditation.org | Quarterly |
| CAP | Clinical labs | cap.org/laboratory-improvement/accreditation | Monthly |

## Workflow Steps
1. **Cron Trigger** — 1st of month
2. **HTTP Request / Apify scraper** — scrape each accreditation directory
3. **Parse results** — extract: facility name, address, accreditation date, contact info
4. **Filter** — accreditation date within last 60 days (newly accredited)
5. **NPI lookup** — match facility name + address to NPI record
6. **Apollo enrichment** — find owner/decision-maker
7. **Findymail** — verify email
8. **Airtable dedup** — skip if existing
9. **Airtable create** — `source: accreditation_signal`, `signal_type: newly_accredited`
10. **Smartlead enroll** — accreditation-specific sequence variant
11. **Slack notify** — monthly digest

## Email Angle for This Signal
Subject: `congrats on the PCAB accreditation`
> "Saw {{company}} just earned PCAB accreditation — that's a significant investment in quality. Now that you have that credential, physicians will take your calls. We help you make those calls at scale. Worth 15 minutes?"
