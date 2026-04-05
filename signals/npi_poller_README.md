# NPI Registry Weekly Poller — Healthcare Referral Pipeline

## What It Does

Polls the CMS NPI Registry API every Monday at 6am CT to detect newly registered healthcare businesses in four target categories. New registrations are buying-signal leads for the healthcare referral pipeline — businesses that registered within the last 7 days are greenfield targets with no existing vendor relationships.

**Signal flow:**
1. Polls NPI API in parallel (4 workers) for each taxonomy code
2. Filters to registrations from the last 7 days (`enumeration_date` range)
3. Deduplicates against existing records in Airtable (checks for `NPI:` prefix in notes field)
4. Enriches each net-new contact with a business email via Findymail
5. Pushes all net-new contacts to Airtable `appoi8SzEJY8in57x` signals table (even without email)
6. Enrolls contacts that have emails into the appropriate Smartlead campaign by taxonomy
7. Posts a summary to `#ecas-ops` Slack with count breakdown by taxonomy

## Taxonomy Codes Monitored

| NPI Code | Business Type | Smartlead Campaign |
|----------|--------------|-------------------|
| `3336C0003X` | Compounding Pharmacy | Compounding Pharmacy — Prescriber Pipeline |
| `261QS1200X` | Sleep Lab | Sleep Lab — Physician Referral Pipeline |
| `261QR0208X` | Imaging Center | Imaging — Physician Referral Pipeline |
| `251G00000X` | Home Health Agency | Home Health — Referral Pipeline |

## How to Run

All secrets are sourced from Doppler. Run with:

```bash
doppler run --project ent-agency-automation --config dev -- python signals/npi_poller.py
```

Run from the ECAS repo root (`~/Desktop/ECAS/`).

## Required Environment Variables (via Doppler)

| Variable | Required | Description |
|----------|----------|-------------|
| `AIRTABLE_API_KEY` | Yes | Airtable Personal Access Token |
| `FINDYMAIL_API_KEY` | No | Findymail email enrichment API key |
| `SMARTLEAD_API_KEY` | No | Smartlead API key for campaign enrollment |
| `SLACK_WEBHOOK_URL` | No | Slack Incoming Webhook URL for `#ecas-ops` |

If `FINDYMAIL_API_KEY` is absent, contacts are still pushed to Airtable with `email_status: not_found`. If `SMARTLEAD_API_KEY` is absent, Smartlead enrollment is skipped silently.

## Smartlead Campaign ID Setup

Set the following environment variables in Doppler once campaigns are created in Smartlead:

| Variable | Taxonomy |
|----------|---------|
| `SL_CAMPAIGN_COMPOUNDING_PHARMACY` | `3336C0003X` — Compounding Pharmacy |
| `SL_CAMPAIGN_SLEEP_LAB` | `261QS1200X` — Sleep Lab |
| `SL_CAMPAIGN_IMAGING_CENTER` | `261QR0208X` — Imaging Center |
| `SL_CAMPAIGN_HOME_HEALTH` | `251G00000X` — Home Health Agency |

## Cron Schedule (Monday 6am CT)

Add to crontab via `crontab -e`:

```cron
0 6 * * 1 cd /path/to/ECAS && doppler run --project ent-agency-automation --config dev -- python signals/npi_poller.py >> /var/log/npi_poller.log 2>&1
```

Or trigger via n8n cron node (workflow `4ZkYDJpqg5qBXdAW`) with an HTTP Request node calling the ECAS Railway admin endpoint:

```
POST https://ecas-scraper-production.up.railway.app/admin/run/npi_poller
```

## Airtable Fields Populated

Records are written to base `appoi8SzEJY8in57x`, table `tblAFJnXToLTKeaNU` (signals_raw):

| Airtable Field | Value |
|---------------|-------|
| `signal_type` | `npi_registry_new` |
| `source` | `manual` |
| `company_name` | Organization name from NPI |
| `sector` | `Healthcare Referral` |
| `captured_at` | NPI registration date |
| `raw_text` | Full address, phone, email, taxonomy block |
| `notes` | `NPI:{number} | Taxonomy:{label} | Email status:{status}` |
| `confidence_score` | `20.0` (baseline for new registration) |
| `processed` | `false` |

## Dependencies

- `requests` — HTTP calls (NPI API, Airtable, Findymail, Smartlead, Slack)

Already in `requirements.txt`. No additional packages needed.
