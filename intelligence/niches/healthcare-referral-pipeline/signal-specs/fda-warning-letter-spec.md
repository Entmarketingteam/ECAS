# FDA Warning Letter + State Board Action Monitor — Spec

**Repo:** ECAS (`~/Desktop/ECAS/`)
**Trigger:** n8n Cron — every Monday 7am CT
**Purpose:** Detect pharmacies that received regulatory action and are now in "prove compliance + grow" mode

## Why This Signal Works
A pharmacy 30–45 days post-warning-letter has:
- Resolved their compliance issue (survived it)
- Revenue anxiety from the disruption
- Urgency to rebuild and diversify their prescriber base
- High receptivity to outbound that acknowledges their situation

## Data Sources

### FDA Warning Letters
`https://www.fda.gov/inspections-compliance-enforcement/warning-letters`
- Searchable by date, company name, state
- Filter: `subject` contains "pharmacy" OR "compounding" OR "503A" OR "503B"
- Published weekly, usually Monday/Tuesday

### State Board of Pharmacy Actions
Top 10 states to monitor:
| State | URL |
|-------|-----|
| TX | pharmacy.texas.gov/compliance/enforcement |
| FL | flhealthsource.gov/MQA/enforcement |
| CA | pharmacy.ca.gov/enforcement/actions |
| NY | op.nysed.gov/oped/enforcement |
| IL | idfpr.illinois.gov/profs/Pharmacy |
| OH | pharmacy.ohio.gov/licensing/discipline |
| PA | dos.pa.gov/ProfessionalLicensing/BoardsCommissions/Pharmacy |
| NC | ncbop.org/disciplinary_actions |
| GA | sos.ga.gov/georgia-board-pharmacy |
| WA | doh.wa.gov/LicensesPermitsandCertificates/MedicalProfessionsLicensing |

## Workflow Steps
1. **Cron Trigger** — Monday 7am
2. **HTTP Request** — FDA warning letters RSS/search (last 7 days)
3. **Filter** — subject/company contains pharmacy keywords
4. **HTTP Request (parallel)** — top 10 state board action pages (Apify scraper)
5. **Parse + extract** — company name, address, action date, violation type
6. **Store in Airtable** — `source: regulatory_action`, `action_date`, `action_type`, `status: monitoring`
7. **Wait 30 days** — schedule follow-up (n8n Wait node or date-based trigger)
8. **NPI lookup + Apollo enrichment** — find owner contact
9. **Findymail** — verify email
10. **Smartlead enroll** — warning letter recovery sequence
11. **Slack notify** — `#ecas-ops` when contact enrolled (30 days post-action)

## Email Angle for This Signal
Subject: `after the FDA letter`
> "The compliance work is the hardest part — most pharmacies don't make it through a 483 without changes. Since {{company}} did, you're in a stronger position than before. Now is when the best ones rebuild their prescriber network. Happy to show you how we'd do that."

Note: Do NOT mention the warning letter directly by name. Reference the situation generally. Validate their resilience without being specific about the violation.
