# ECAS Airtable Schema

**Base name:** `ECAS — Enterprise Contract Acquisition System`

Create a new base in Airtable. All four tables below live in this single base. Replace `ECAS_BASE_ID` in n8n workflows with the `appXXX` ID shown after creation.

---

## Table 1: `signals_raw`

The raw intake table. Every inbound signal lands here first. Processed signals are linked to a project record or dismissed.

| Field Name | Airtable Type | Description |
|---|---|---|
| `signal_id` | Autonumber | Primary key, auto-incremented |
| `source` | Single select | Origin of the signal. Options: `ferc_efts`, `pjm_queue`, `ercot_queue`, `rss_feed`, `manual` |
| `url` | URL | Direct link to the source document or article |
| `raw_text` | Long text | Raw extracted text from the signal (title + description + metadata) |
| `captured_at` | Date (include time, GMT) | When the signal was ingested |
| `processed` | Checkbox | False until the signal processor workflow runs against it |
| `linked_project` | Linked record → `projects` | Set by the signal processor if the signal becomes a project |
| `confidence_score` | Number (decimal, 2 places) | Claude's confidence that this is a real infrastructure project (0.00–1.00) |
| `notes` | Long text | Manual analyst notes |

**Views to create:**
- `Unprocessed Queue` — filter: `processed = false`, sort: `captured_at` ascending
- `All Signals` — default view, all records

---

## Table 2: `projects`

The core intelligence table. Each row is a distinct infrastructure project ECAS is tracking. Auto-populated by the signal processor; enriched by analysts.

| Field Name | Airtable Type | Description |
|---|---|---|
| `project_id` | Autonumber | Primary key |
| `project_name` | Single line text | Name of the project (extracted or assigned) |
| `state` | Single select | `VA` or `TX` |
| `county` | Single line text | County where project is located |
| `mw_capacity` | Number (decimal) | Megawatt capacity of the project |
| `estimated_contract_value_band` | Single select | `<$1M`, `$1M-$5M`, `$5M-$25M`, `$25M-$100M`, `>$100M` |
| `project_type` | Single select | `transmission`, `substation`, `generation`, `distribution`, `interconnection`, `data_center_power`, `other` |
| `signal_type` | Single select | `ferc_filing`, `interconnection_queue`, `rate_case`, `ppa`, `job_posting`, `press_release`, `earnings_call`, `permit`, `other` |
| `owner_company` | Single line text | Utility or developer who owns the project |
| `epc_company` | Single line text | Known EPC contractor (if already awarded) |
| `rfp_expected_date` | Single line text | `YYYY-MM` format — when RFP is expected to drop |
| `positioning_window_open` | Single line text | `YYYY-MM` — earliest to begin outreach |
| `positioning_window_close` | Single line text | `YYYY-MM` — deadline to be positioned |
| `scope_summary` | Long text | Claude-generated summary, max 200 chars |
| `source_url` | URL | Original signal URL |
| `confidence_score` | Number (decimal, 2 places) | Inherited from signal extraction |
| `stage` | Single select | Pipeline stage. Options: `Identified`, `Researching`, `Outreach`, `Meeting Set`, `Proposal Sent`, `Negotiating`, `Won`, `Lost`, `Dormant` |
| `assigned_to` | Single line text | Internal team member assigned to pursue |
| `priority` | Single select | `High`, `Medium`, `Low` |
| `signals` | Linked record → `signals_raw` | All raw signals that contributed to this project |
| `contacts` | Linked record → `contacts` | All contacts associated with this project |
| `deals` | Linked record → `deals` | Deal records once we reach proposal stage |
| `days_in_stage` | Formula | `DATETIME_DIFF(NOW(), {stage_entered_at}, 'days')` |
| `stage_entered_at` | Date (include time) | When the record entered its current stage |
| `created_at` | Created time | Auto-populated by Airtable |
| `last_modified` | Last modified time | Auto-populated by Airtable |
| `analyst_notes` | Long text | Free-form analyst notes |
| `icp_fit` | Single select | `Strong`, `Moderate`, `Weak`, `Unknown` — does this project fit our ICP? |
| `positioning_notes` | Long text | How we plan to differentiate for this project |

**Formula fields:**

`days_in_stage`:
```
DATETIME_DIFF(NOW(), {stage_entered_at}, 'days')
```

**Views to create:**
- `Pipeline Board` — grouped by `stage`, kanban-style
- `High Priority` — filter: `priority = High`, sort: `positioning_window_close` asc
- `Virginia Projects` — filter: `state = VA`
- `Texas Projects` — filter: `state = TX`
- `Needs Outreach` — filter: `stage = Identified` OR `stage = Researching`, `contacts` is not empty

---

## Table 3: `contacts`

Individual people associated with project owner or EPC companies. Auto-populated by the contact enricher workflow; reviewed before outreach.

| Field Name | Airtable Type | Description |
|---|---|---|
| `contact_id` | Autonumber | Primary key |
| `first_name` | Single line text | |
| `last_name` | Single line text | |
| `full_name` | Formula | `{first_name} & " " & {last_name}` |
| `email` | Email | Primary email address |
| `email_verified` | Checkbox | True if Zerobounce returned `valid` |
| `title` | Single line text | Job title (e.g. Director of Preconstruction) |
| `company_name` | Single line text | Employer |
| `company_role` | Single select | `owner` or `epc` — which company role this contact belongs to |
| `linkedin_url` | URL | LinkedIn profile URL |
| `phone` | Phone number | Direct phone if available |
| `city` | Single line text | |
| `state` | Single line text | |
| `headline` | Single line text | LinkedIn headline (from Proxycurl) |
| `summary` | Long text | LinkedIn about section (from Proxycurl) |
| `follower_count` | Number | LinkedIn follower count |
| `connections` | Number | LinkedIn connection count |
| `outreach_status` | Single select | `pending_review`, `approved`, `do_not_contact`, `in_sequence`, `replied`, `meeting_booked`, `not_interested`, `unsubscribed` |
| `project_id` | Linked record → `projects` | Project this contact is associated with |
| `smartlead_campaign_id` | Single line text | Smartlead campaign ID once enrolled |
| `expandi_campaign_id` | Single line text | Expandi LinkedIn campaign ID once enrolled |
| `apollo_id` | Single line text | Apollo.io person ID for deduplication |
| `last_outreach_date` | Date | When we last touched this contact |
| `response_received` | Checkbox | Did they respond to any outreach? |
| `response_notes` | Long text | What they said |
| `created_at` | Created time | Auto-populated |
| `last_modified` | Last modified time | Auto-populated |
| `analyst_notes` | Long text | Any additional context |

**Formula fields:**

`full_name`:
```
{first_name} & " " & {last_name}
```

**Views to create:**
- `Pending Review` — filter: `outreach_status = pending_review`, sort: `created_at` desc
- `Approved for Outreach` — filter: `outreach_status = approved`, `email_verified = true`
- `In Sequence` — filter: `outreach_status = in_sequence`
- `Replied` — filter: `response_received = true`

---

## Table 4: `deals`

Created when a project reaches the `Proposal Sent` stage. Tracks contract financials, guarantee amounts, and close timing.

| Field Name | Airtable Type | Description |
|---|---|---|
| `deal_id` | Autonumber | Primary key |
| `deal_name` | Formula | `{project_name} & " — " & {company_name}` |
| `project_id` | Linked record → `projects` | Parent project |
| `company_name` | Single line text | The company we're selling to |
| `primary_contact` | Linked record → `contacts` | Decision-maker contact |
| `stage` | Single select | `Proposal Sent`, `Negotiating`, `Contract Out`, `Closed Won`, `Closed Lost` |
| `contract_value` | Currency (USD) | Final or estimated contract value |
| `guaranteed_revenue` | Currency (USD) | Guaranteed floor amount in the contract |
| `performance_upside` | Currency (USD) | Variable upside above guarantee |
| `contract_sent_date` | Date | When the contract was sent |
| `contract_signed_date` | Date | When fully executed |
| `guarantee_period_days` | Number | Number of days the guarantee runs from contract_signed_date |
| `guarantee_end_date` | Formula | `DATEADD({contract_signed_date}, {guarantee_period_days}, 'days')` |
| `guarantee_days_remaining` | Formula | `IF({contract_signed_date}, MAX(0, DATETIME_DIFF({guarantee_end_date}, NOW(), 'days')), BLANK())` |
| `close_probability` | Number (percent) | Analyst's estimated probability of closing |
| `weighted_value` | Formula | `{contract_value} * {close_probability} / 100` |
| `expected_close_date` | Date | |
| `lost_reason` | Single select | `No budget`, `Went with competitor`, `Project cancelled`, `No response`, `Scope mismatch`, `Other` |
| `lost_notes` | Long text | Detail on why we lost |
| `close_notes` | Long text | How we won, key decision factors |
| `next_step` | Single line text | Immediate next action |
| `next_step_due` | Date | When next step must happen |
| `created_at` | Created time | Auto-populated |
| `last_modified` | Last modified time | Auto-populated |

**Formula fields:**

`deal_name`:
```
{project_name} & " — " & {company_name}
```

`guarantee_end_date`:
```
DATEADD({contract_signed_date}, {guarantee_period_days}, 'days')
```

`guarantee_days_remaining`:
```
IF(
  {contract_signed_date},
  MAX(0, DATETIME_DIFF({guarantee_end_date}, NOW(), 'days')),
  BLANK()
)
```

`weighted_value`:
```
{contract_value} * {close_probability} / 100
```

**Views to create:**
- `Active Deals` — filter: `stage` is not `Closed Won` or `Closed Lost`
- `Guarantees Expiring` — sort: `guarantee_days_remaining` asc — helps track contract risk
- `Won Deals` — filter: `stage = Closed Won`
- `Pipeline Value` — all active deals, show `weighted_value`, enable field totals
