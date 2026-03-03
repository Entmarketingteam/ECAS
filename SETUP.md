# ECAS Setup Guide

Complete technical setup for the Enterprise Contract Acquisition System. Follow in order — dependencies exist between steps.

---

## Step 1: Airtable Base Creation

### 1.1 Create the Base

1. Log in to Airtable → click **Add a base** → **Start from scratch**
2. Name it: `ECAS — Enterprise Contract Acquisition System`
3. Note the base ID from the URL: `airtable.com/appXXX/...` — this is your `ECAS_BASE_ID`

### 1.2 Create Table: `signals_raw`

Delete the default "Table 1". Create a new table named `signals_raw`.

Add these fields (Airtable will auto-create a primary field — rename it to `signal_id`, type: Autonumber):

| Field | Type | Settings |
|---|---|---|
| `source` | Single select | Add options: `ferc_efts`, `pjm_queue`, `ercot_queue`, `rss_feed`, `manual` |
| `url` | URL | — |
| `raw_text` | Long text | Enable rich text: OFF |
| `captured_at` | Date | Include time: ON, timezone: GMT |
| `processed` | Checkbox | Default: unchecked |
| `linked_project` | Linked record | Link to `projects` table (create it first if needed, then come back) |
| `confidence_score` | Number | Format: Decimal, precision: 2 |
| `notes` | Long text | — |

Create views:
- `Unprocessed Queue`: filter `processed` is unchecked, sort by `captured_at` ascending
- `All Signals`: default view

### 1.3 Create Table: `projects`

New table named `projects`. Primary field: `project_id` (Autonumber).

| Field | Type | Settings |
|---|---|---|
| `project_name` | Single line text | — |
| `state` | Single select | Options: `VA`, `TX` |
| `county` | Single line text | — |
| `mw_capacity` | Number | Decimal, 1 place |
| `estimated_contract_value_band` | Single select | Options: `<$1M`, `$1M-$5M`, `$5M-$25M`, `$25M-$100M`, `>$100M` |
| `project_type` | Single select | Options: `transmission`, `substation`, `generation`, `distribution`, `interconnection`, `data_center_power`, `other` |
| `signal_type` | Single select | Options: `ferc_filing`, `interconnection_queue`, `rate_case`, `ppa`, `job_posting`, `press_release`, `earnings_call`, `permit`, `other` |
| `owner_company` | Single line text | — |
| `epc_company` | Single line text | — |
| `rfp_expected_date` | Single line text | — |
| `positioning_window_open` | Single line text | — |
| `positioning_window_close` | Single line text | — |
| `scope_summary` | Long text | — |
| `source_url` | URL | — |
| `confidence_score` | Number | Decimal, 2 places |
| `stage` | Single select | Options: `Identified`, `Researching`, `Outreach`, `Meeting Set`, `Proposal Sent`, `Negotiating`, `Won`, `Lost`, `Dormant` |
| `assigned_to` | Single line text | — |
| `priority` | Single select | Options: `High`, `Medium`, `Low` |
| `stage_entered_at` | Date | Include time: ON |
| `icp_fit` | Single select | Options: `Strong`, `Moderate`, `Weak`, `Unknown` |
| `positioning_notes` | Long text | — |
| `analyst_notes` | Long text | — |
| `signals` | Linked record | Link to `signals_raw` |
| `contacts` | Linked record | Link to `contacts` (create first if needed) |
| `deals` | Linked record | Link to `deals` (create first if needed) |
| `days_in_stage` | Formula | `DATETIME_DIFF(NOW(), {stage_entered_at}, 'days')` |
| `created_at` | Created time | — |
| `last_modified` | Last modified time | — |

### 1.4 Create Table: `contacts`

Table named `contacts`. Primary field: `contact_id` (Autonumber).

| Field | Type |
|---|---|
| `first_name` | Single line text |
| `last_name` | Single line text |
| `full_name` | Formula: `{first_name} & " " & {last_name}` |
| `email` | Email |
| `email_verified` | Checkbox |
| `title` | Single line text |
| `company_name` | Single line text |
| `company_role` | Single select: `owner`, `epc` |
| `linkedin_url` | URL |
| `phone` | Phone number |
| `city` | Single line text |
| `state` | Single line text |
| `headline` | Single line text |
| `summary` | Long text |
| `follower_count` | Number |
| `connections` | Number |
| `outreach_status` | Single select: `pending_review`, `approved`, `do_not_contact`, `in_sequence`, `replied`, `meeting_booked`, `not_interested`, `unsubscribed` |
| `project_id` | Linked record → `projects` |
| `smartlead_campaign_id` | Single line text |
| `expandi_campaign_id` | Single line text |
| `apollo_id` | Single line text |
| `last_outreach_date` | Date |
| `response_received` | Checkbox |
| `response_notes` | Long text |
| `analyst_notes` | Long text |
| `created_at` | Created time |
| `last_modified` | Last modified time |

### 1.5 Create Table: `deals`

Table named `deals`. Primary field: `deal_id` (Autonumber).

| Field | Type |
|---|---|
| `project_id` | Linked record → `projects` |
| `project_name` | Lookup from `project_id` → `project_name` |
| `company_name` | Single line text |
| `deal_name` | Formula: `{project_name} & " — " & {company_name}` |
| `primary_contact` | Linked record → `contacts` |
| `stage` | Single select: `Proposal Sent`, `Negotiating`, `Contract Out`, `Closed Won`, `Closed Lost` |
| `contract_value` | Currency (USD) |
| `guaranteed_revenue` | Currency (USD) |
| `performance_upside` | Currency (USD) |
| `contract_sent_date` | Date |
| `contract_signed_date` | Date |
| `guarantee_period_days` | Number |
| `guarantee_end_date` | Formula: `DATEADD({contract_signed_date}, {guarantee_period_days}, 'days')` |
| `guarantee_days_remaining` | Formula: `IF({contract_signed_date}, MAX(0, DATETIME_DIFF({guarantee_end_date}, NOW(), 'days')), BLANK())` |
| `close_probability` | Number (percent) |
| `weighted_value` | Formula: `{contract_value} * {close_probability} / 100` |
| `expected_close_date` | Date |
| `lost_reason` | Single select: `No budget`, `Went with competitor`, `Project cancelled`, `No response`, `Scope mismatch`, `Other` |
| `lost_notes` | Long text |
| `close_notes` | Long text |
| `next_step` | Single line text |
| `next_step_due` | Date |
| `created_at` | Created time |
| `last_modified` | Last modified time |

---

## Step 2: Accounts to Create & API Key Storage

All secrets go into Doppler under project `ecas`, config `dev`. Create the Doppler project first:

```bash
doppler projects create ecas
doppler setup --project ecas --config dev
```

### Accounts Needed

| Service | Purpose | Where to Get Key | Doppler Key Name |
|---|---|---|---|
| **Apollo.io** | Contact search by company + title | apollo.io → Settings → API Keys | `APOLLO_API_KEY` |
| **Proxycurl** | LinkedIn profile enrichment | nubela.co/proxycurl → Dashboard | `PROXYCURL_API_KEY` |
| **Zerobounce** | Email verification | zerobounce.net → API | `ZEROBOUNCE_KEY` |
| **Reducto AI** | PDF extraction | reducto.ai → Dashboard | `REDUCTO_API_KEY` |
| **Smartlead** | Email outreach sequencing | app.smartlead.ai → Settings → API | `SMARTLEAD_API_KEY` |
| **Expandi.io** | LinkedIn outreach automation | app.expandi.io → Settings | `EXPANDI_API_KEY` |
| **Close CRM** | Deal tracking | app.close.com → Settings → API Keys | `CLOSE_CRM_API_KEY` |

Store each key:
```bash
doppler secrets set APOLLO_API_KEY="..." --project ecas --config dev
doppler secrets set PROXYCURL_API_KEY="..." --project ecas --config dev
doppler secrets set REDUCTO_API_KEY="..." --project ecas --config dev
doppler secrets set ZEROBOUNCE_KEY="..." --project ecas --config dev
doppler secrets set SMARTLEAD_API_KEY="..." --project ecas --config dev
doppler secrets set EXPANDI_API_KEY="..." --project ecas --config dev
doppler secrets set CLOSE_CRM_API_KEY="..." --project ecas --config dev
```

Retrieve any key later:
```bash
doppler secrets get APOLLO_API_KEY --project ecas --config dev --plain
```

---

## Step 3: Railway Deployment

### 3.1 Prerequisites

```bash
npm install -g @railway/cli
railway login
```

### 3.2 Initialize and Deploy

```bash
cd /Users/ethanatchley/Desktop/ECAS
git init
git add .
git commit -m "Initial ECAS scraper service"

railway new
# Name the project: ecas-scraper

railway link
# Select the ecas-scraper project

railway up
```

### 3.3 Set Environment Variables in Railway

In the Railway dashboard → project → Variables tab, add:

```
REDUCTO_API_KEY=<from Doppler>
APOLLO_API_KEY=<from Doppler>
PROXYCURL_API_KEY=<from Doppler>
ZEROBOUNCE_KEY=<from Doppler>
```

Or push from Doppler directly (if Railway-Doppler integration is configured):
```bash
doppler secrets get REDUCTO_API_KEY --project ecas --config dev --plain | railway variables set REDUCTO_API_KEY=
```

### 3.4 Note the Railway URL

After deployment, Railway assigns a URL like:
`https://ecas-scraper-production.up.railway.app`

Test it:
```bash
curl https://ecas-scraper-production.up.railway.app/health
# Expected: {"status":"ok","service":"ecas-scraper"}
```

Store the Railway URL in Doppler:
```bash
doppler secrets set ECAS_RAILWAY_URL="https://ecas-scraper-production.up.railway.app" --project ecas --config dev
```

---

## Step 4: n8n Workflow Import

### 4.1 Import Each Workflow

In n8n (entagency.app.n8n.cloud):
1. Go to **Workflows** → **Import from File**
2. Import in this order:
   - `01-ferc-signal-poller.json`
   - `02-pjm-queue-poller.json`
   - `03-rss-aggregator.json`
   - `05-signal-processor.json`
   - `07-contact-enricher.json`

### 4.2 Update the Airtable Base ID

All workflows contain the placeholder `ECAS_BASE_ID`. After importing each workflow:
1. Click each Airtable node
2. Replace `ECAS_BASE_ID` with the actual base ID (`appXXX`) from Step 1

### 4.3 Verify Credentials Are Wired

Each workflow uses pre-existing credentials. Confirm these are selected in each relevant node:

| Credential Type | n8n Credential ID |
|---|---|
| Airtable | `dAoeOLbTnBUK1gTy` |
| Anthropic | `MwxIqQP3l6cUcwcZ` |
| Slack | `EMdoV2Sq9neZV1Tn` |

### 4.4 Activate Workflows

Activate in this order (signals must flow before processor can run):
1. `03-rss-aggregator` — activate first, let it run one cycle
2. `01-ferc-signal-poller` — activate
3. `02-pjm-queue-poller` — activate (runs weekly, so just verify no errors on manual test)
4. `05-signal-processor` — activate only after signals_raw has data
5. `07-contact-enricher` — activate last

---

## Step 5: Smartlead Sending Domain Setup

### 5.1 Domains to Purchase

Buy 3 sending domains (never use the primary `ecas.com` or main business domain for cold email). Recommended naming pattern for construction/EPC outreach:

- `ent-bid.com` (or `entbid.io`)
- `entproposals.com`
- `entenergy-ops.com`

Purchase via Namecheap or Cloudflare Registrar.

### 5.2 DNS Records (per domain)

Add to each domain's DNS (example for `ent-bid.com`):

**SPF Record:**
```
Type: TXT
Name: @
Value: v=spf1 include:servers.mcsv.net include:_spf.google.com include:sendgrid.net ~all
```
Replace `include:` values with Smartlead's actual SPF include (found in Smartlead → Settings → Email).

**DKIM Record:**
```
Type: CNAME or TXT
Name: smartlead._domainkey  (or as provided by Smartlead)
Value: <Smartlead-provided DKIM value>
```

**DMARC Record:**
```
Type: TXT
Name: _dmarc
Value: v=DMARC1; p=none; rua=mailto:dmarc@ent-bid.com; pct=100;
```

**MX Record (for bounce handling):**
```
Type: MX
Name: @
Priority: 10
Value: <Smartlead or Google MX record>
```

### 5.3 Warmup Schedule

Do NOT send cold email from a fresh domain. Warmup each domain for 4 weeks minimum.

In Smartlead → Email Accounts → Add each sending address → Enable Warmup:

| Week | Daily Send Volume per Address | Notes |
|---|---|---|
| 1 | 5–10 | Warmup only, no campaigns |
| 2 | 15–20 | Warmup only |
| 3 | 25–30 | Begin with highest-priority contacts only |
| 4 | 40–50 | Ramp to full campaign volume |

Run 3 addresses per domain. Rotate sends across all addresses in Smartlead campaigns (round-robin setting).

---

## Step 6: Expandi.io LinkedIn Account Setup

### 6.1 Requirements

You need a LinkedIn account dedicated to ECAS outreach. Do not use a personal account. Options:
- Create a new LinkedIn account with a real name and professional history
- Or use an existing team member's secondary account

### 6.2 Setup Steps

1. Create LinkedIn account, fill out profile completely (photo, experience, connections)
2. Add 100+ connections to establish credibility before campaigns (2 weeks minimum)
3. Go to Expandi → Add Account → Connect LinkedIn
4. Install Expandi Chrome extension on the account's browser session
5. In Expandi → Account Settings, set:
   - Daily connection requests: 20 (start low)
   - Daily messages: 30
   - Working hours: Mon–Fri, 8am–6pm local

### 6.3 Campaign Templates

Create these two campaign types in Expandi:

**Campaign A: Connection Request (blind)**
```
Hi {{firstName}}, I work with EPC firms pursuing infrastructure contracts in {{state}}.
We track FERC filings and interconnection queues to surface RFP windows early.
Worth connecting?
```

**Campaign B: Follow-up Message (post-connect)**
```
Thanks for connecting, {{firstName}}.

We identified {{projectName}} as an active opportunity based on a recent
FERC filing — I thought you might have visibility into who's handling
preconstruction. Happy to share what we're seeing if useful.
```

---

## Step 7: Close CRM Pipeline Configuration

### 7.1 Create the ECAS Pipeline

In Close CRM:
1. Settings → Pipelines → Add Pipeline
2. Name: `ECAS — Infrastructure Contracts`

### 7.2 Pipeline Stages

Create these stages in order:

| Stage Name | Expected Win Rate | Notes |
|---|---|---|
| `Identified` | 2% | Signal flagged, not yet outreached |
| `Researching` | 5% | Analyst researching scope and timeline |
| `Outreach Active` | 10% | In Smartlead or Expandi sequence |
| `Meeting Set` | 30% | Discovery or intro call scheduled |
| `Proposal Sent` | 50% | Formal proposal delivered |
| `Negotiating` | 70% | Back and forth on terms |
| `Contract Out` | 85% | Contract sent, awaiting signature |
| `Closed Won` | 100% | Executed contract |
| `Closed Lost` | 0% | Dead |

### 7.3 Custom Fields to Create

Go to Settings → Custom Fields → Opportunities:

| Field Name | Type | Options / Notes |
|---|---|---|
| `Project Type` | Choice | transmission, substation, generation, distribution, interconnection, data_center_power, other |
| `State` | Choice | VA, TX |
| `County` | Text | — |
| `MW Capacity` | Number | — |
| `Estimated Contract Value Band` | Choice | <$1M, $1M-$5M, $5M-$25M, $25M-$100M, >$100M |
| `Positioning Window Open` | Text | YYYY-MM |
| `Positioning Window Close` | Text | YYYY-MM |
| `RFP Expected Date` | Text | YYYY-MM |
| `Owner Company` | Text | Utility or developer |
| `EPC Company` | Text | Known contractor if awarded |
| `Airtable Project ID` | Text | For cross-reference |
| `Signal Source` | Choice | ferc_efts, pjm_queue, ercot_queue, rss_feed, manual |
| `ICP Fit` | Choice | Strong, Moderate, Weak |

### 7.4 Views to Create

- `My Open Deals` — assigned to me, not closed
- `High Priority` — ICP Fit = Strong, stage not Closed
- `Stale Deals` — last activity > 14 days, stage not Closed
- `Positioning Window This Quarter` — Positioning Window Close = current quarter

---

## Step 8: First-Run Checklist

Run through this after completing all steps above. Check each item before considering the system live.

### Infrastructure

- [ ] Railway `/health` returns `{"status":"ok","service":"ecas-scraper"}`
- [ ] Railway `/scrape-page` with a test URL returns valid HTML
- [ ] Airtable base exists and all 4 tables are created with correct fields
- [ ] Doppler project `ecas` has all 7 API keys stored

### n8n Workflows

- [ ] Manually execute `03-rss-aggregator` — verify at least 1 record appears in `signals_raw`
- [ ] Manually execute `01-ferc-signal-poller` — verify records appear in `signals_raw`
- [ ] Manually execute `02-pjm-queue-poller` — verify it runs without error (may return 0 VA matches depending on week)
- [ ] Manually execute `05-signal-processor` — verify it reads from `signals_raw`, calls Claude, and either creates a project or marks the signal processed
- [ ] Verify `07-contact-enricher` triggers when you manually create a test project record with `owner_company` filled in
- [ ] All 5 workflows set to **Active**

### Outreach Infrastructure

- [ ] Smartlead: 3 sending domains added, warmup enabled
- [ ] Smartlead: DNS records verified (SPF, DKIM, DMARC) — use mxtoolbox.com to check
- [ ] Expandi: LinkedIn account connected, daily limits configured
- [ ] Close CRM: Pipeline created with all 9 stages
- [ ] Close CRM: All 13 custom fields created

### Signal Validation (Day 1 Check)

After 24 hours of the RSS aggregator running:
- [ ] `signals_raw` has > 20 records
- [ ] `projects` has > 0 records (signal processor ran successfully)
- [ ] No error messages in Slack `#ecas-ops`
- [ ] Confidence score distribution looks sane (most should be < 0.5 for RSS, higher for FERC/PJM)

---

## Ongoing Maintenance

| Cadence | Task |
|---|---|
| Weekly | Review `#ecas-review` Slack channel for low-confidence signals needing manual triage |
| Weekly | Move projects through Close CRM pipeline stages |
| Weekly | Review `contacts` table for new `pending_review` entries — approve or reject for outreach |
| Monthly | Review Smartlead sending stats — adjust copy if reply rates < 2% |
| Monthly | Audit Apollo API usage (credits deplete) |
| Quarterly | Review ICP fit of won vs lost deals — adjust county/MW filters in PJM workflow |
