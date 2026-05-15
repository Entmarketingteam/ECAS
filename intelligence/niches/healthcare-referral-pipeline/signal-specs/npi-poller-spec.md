# NPI Registry Weekly Poller — Signal Spec

**Repo:** ECAS (`~/Desktop/ECAS/`)
**Trigger:** n8n Cron — every Monday 6am CT
**Purpose:** Detect newly registered healthcare businesses (pharmacies, labs, clinics) and enroll in Smartlead

## What It Does
1. Polls NPI registry API weekly
2. Filters by target taxonomy codes + registration date (last 7 days)
3. Checks against Airtable for existing contacts (dedup)
4. Enriches new contacts via Findymail waterfall
5. Enrolls net-new in appropriate Smartlead campaign based on taxonomy

## API Endpoint
`GET https://npiregistry.cms.hhs.gov/api/?taxonomy_description={TAXONOMY}&enumeration_date={LAST_WEEK}&limit=200&version=2.1`

## Taxonomy Codes to Poll
| Code | Business Type | Smartlead Campaign |
|------|--------------|-------------------|
| `3336C0003X` | Compounding pharmacy | Compounding Pharmacy — Prescriber Pipeline |
| `261QS1200X` | Sleep lab | Sleep Lab — Physician Referral Pipeline |
| `261QR0208X` | Imaging center | Imaging — Physician Referral Pipeline |
| `251G00000X` | Home health agency | Home Health — Referral Pipeline |

## n8n Workflow Steps
1. **Cron Trigger** — Monday 6am CT
2. **Calculate date range** — last 7 days (Function node)
3. **HTTP Request (parallel per taxonomy)** — NPI API call for each taxonomy code
4. **Merge results** — combine all taxonomy pulls
5. **Airtable search** — check `appoi8SzEJY8in57x` contacts table for existing NPI number
6. **Filter** — keep only net-new (not in Airtable)
7. **HTTP Request** — Findymail email enrichment per contact
8. **Airtable create record** — add to ECAS contacts table with `source: npi_registry_new`
9. **Smartlead — add to campaign** — map taxonomy to campaign ID
10. **Slack notify** — `#ecas-ops` with count of new contacts enrolled

## Airtable Fields to Populate
- Name, Organization, NPI Number, Address, Phone, Taxonomy, Registration Date, Source, Email (from Findymail), Smartlead Campaign ID

## Error Handling
- If Findymail returns no email → still add to Airtable, flag `email_status: not_found`
- If NPI API returns 0 results → log + continue (don't error)
- Slack alert on any workflow error
