# Smartlead Campaign Setup SOP
## Compounding Pharmacy Owner Outreach — Launch Guide

**Version:** 1.0
**Date:** 2026-04-05
**Owner:** ContractMotion
**Read time:** ~15 minutes
**This is the single doc to read the morning you set up this campaign. Every field is specified.**

---

## Before You Start

Have these tabs open:
- Smartlead dashboard: app.smartlead.ai
- Doppler: dashboard.doppler.com (project `ent-agency-automation`, config `dev`)
- Domain registrar (Namecheap or wherever you register the sending domain)
- Google Workspace Admin: admin.google.com
- Sequence copy: `sequences/compounding-pharmacy.md` in this repo

---

## Section 1: Domain Setup

### 1.1 Register the Sending Domain

Register a **neutral, health/growth-adjacent domain** — do NOT use ContractMotion.com or ContractMotion branding. This is a dedicated cold outreach domain, not your main brand.

**Approved domain name patterns:**

| Domain | Notes |
|--------|-------|
| `prescriberpipeline.com` | Best — exact positioning |
| `rxgrowthpartners.com` | Strong — pharmacy-adjacent |
| `clinicalgrowth.co` | Good — healthcare-neutral |
| `referralpipeline.co` | Solid — benefit-first |
| `prescribegrowth.com` | Alternative |

Pick whichever of the above is available. Register at Namecheap. Cost ~$12–15/year.

**Inbox format:** `ethan@[domain].com` — personal first name, not `info@` or `team@`.

### 1.2 Connect to Google Workspace

1. Go to admin.google.com → Domains → Add domain → Add the new domain as an alias or new domain
2. Or: Create a new Google Workspace account for this domain ($6/user/month) — preferred for clean sending reputation
3. Create one inbox: `ethan@[yourdomain].com`

### 1.3 DNS Records

Set all four of these at your domain registrar before starting warmup. DNS propagation takes 24–48 hours — do this first.

**MX Records (for Google Workspace):**

| Priority | Value |
|----------|-------|
| 1 | `ASPMX.L.GOOGLE.COM` |
| 5 | `ALT1.ASPMX.L.GOOGLE.COM` |
| 5 | `ALT2.ASPMX.L.GOOGLE.COM` |
| 10 | `ALT3.ASPMX.L.GOOGLE.COM` |
| 10 | `ALT4.ASPMX.L.GOOGLE.COM` |

**SPF (TXT record at `@`):**
```
v=spf1 include:_spf.google.com ~all
```

**DKIM:**
1. Google Workspace Admin → Apps → Gmail → Authenticate email → Generate new record
2. Copy the TXT record (long string starting with `v=DKIM1;`)
3. Add as TXT record at `google._domainkey.[yourdomain].com`

**DMARC (TXT record at `_dmarc.[yourdomain].com`):**
```
v=DMARC1; p=none; rua=mailto:ethan@[yourdomain].com
```
Start with `p=none` (monitoring only) — do not use `p=reject` during warmup.

### 1.4 Verify DNS

After 24 hours, verify all records are propagated:
- SPF/DKIM/DMARC checker: mxtoolbox.com/SuperTool.aspx
- Run checks for: SPF Lookup, DKIM Lookup, DMARC Lookup
- All three must show green before proceeding

### 1.5 Warmup Setup in Smartlead

1. Smartlead → Email Accounts → Add Account → Gmail OAuth or App Password
2. Enable **Warmup** toggle
3. Warmup settings:
   - Daily warmup emails: start at 5, ramp to 40 over 14 days
   - Enable smart warmup (Smartlead default)
   - Warmup reply rate: 30–40%
4. **Do not send any real campaigns until warmup has run for 14 full days**
5. Target: 40 warmup emails/day before campaign launch

---

## Section 2: Campaign Creation in Smartlead

### 2.1 Create the Campaign

Smartlead → Campaigns → New Campaign

| Field | Value |
|-------|-------|
| Campaign name | `Healthcare-CompoundingPharmacy-Owners-[YYYY-MM-DD]` e.g. `Healthcare-CompoundingPharmacy-Owners-2026-04-20` |
| From name | `Ethan Atchley` — personal name, NOT "ContractMotion" or "Prescriber Pipeline" |
| From email | `ethan@[yourdomain].com` |
| Reply-to | Same as From email |
| Timezone | Recipient's timezone (Smartlead setting: auto-detect) |

### 2.2 Sending Settings

| Setting | Value | Reason |
|---------|-------|--------|
| Open tracking | ON | Monitor engagement |
| Click tracking | OFF | Every redirect = deliverability risk |
| Unsubscribe header | ON | CAN-SPAM compliance |
| Stop on reply | YES — stop sequence on ANY reply | Prevents follow-up after positive response |
| Daily limit | 40/day (week 1), 50/day (week 2), 60/day (week 3+) | Matches warmup ramp |

### 2.3 Schedule

| Setting | Value |
|---------|-------|
| Send days | Monday through Friday only |
| Send hours | 8:00 AM – 5:00 PM (recipient timezone) |
| Exclude dates | None needed at launch; add holidays later |

### 2.4 Unsubscribe Footer

Paste this as plain text at the bottom of every email template (Smartlead has a footer field):

```
If you'd prefer not to receive these emails, reply "unsubscribe" and I'll remove you immediately.
```

Plain text only — no links, no HTML. Links in footers reduce deliverability.

---

## Section 3: Loading the Sequence

### 3.1 Step Configuration

The sequence has exactly three steps. Create each step in order.

| Step | Send Day | Delay from Previous |
|------|----------|---------------------|
| Email 1 | Day 1 (immediate) | n/a — first step |
| Email 2 | Day 4 | 3 days after Email 1 |
| Email 3 | Day 9 | 5 days after Email 2 |

In Smartlead, "delay" is set in the step settings as "Wait X days before sending."

### 3.2 Email 1 — Day 1

**Subject line (copy exactly):**
```
how new prescribers find {{company}}
```

**Body (copy exactly — preserve spacing and line breaks):**
```
Hi {{first_name}},

Quick question — when a physician who's never worked with you before needs a compounding partner, how do they find {{company}}?

Most pharmacy owners I ask say: referral from another doctor, or they just called out of the blue one day.

Which means your prescriber network grows when you get lucky.

We run targeted cold email outreach to physicians on behalf of compounding pharmacies — connecting you directly with BHRT, functional medicine, and weight management prescribers in your area who don't know you exist yet.

Typically adds 5–10 net-new active prescribers in the first 90 days.

Worth a 15-minute call to see if the math makes sense for {{company}}?

{{signature}}
```

### 3.3 Email 2 — Day 4 (3-day delay)

**Subject line:**
```
the GLP-1 cliff
```

**Body:**
```
{{first_name}} —

Compounding pharmacies that built around semaglutide are running into the same problem right now: the FDA shortage window is closing and those prescriber relationships are thinning out.

The ones that are fine used that run to diversify — BHRT, peptides, dermatology, functional medicine. Prescribers who'll still be there when GLP-1 compounding is fully wound down.

That's what we help build. A prescriber pipeline into the specialties that aren't going anywhere.

One new prescriber writing 5 scripts/month at $300 average is $1,800/month recurring. We typically add 5–10 in 90 days.

15 minutes this week?

{{signature}}
```

### 3.4 Email 3 — Day 9 (5-day delay)

**Subject line:**
```
last one from me
```

**Body:**
```
{{first_name}} —

Not going to keep filling your inbox.

If prescriber diversification is something {{company}} is thinking about this year — specifically getting in front of BHRT, longevity, or functional medicine physicians who've never heard of you — I'd love to show you exactly how we'd do it.

If the timing isn't right, no problem at all.

Either way, best of luck with the pharmacy.

{{first_name_sender}}
```

Note: Email 3 uses `{{first_name_sender}}` (your first name only, no full signature block). This is intentional — the final email is deliberately low-pressure and informal.

### 3.5 Variable Mapping in Smartlead

| Smartlead Variable | Maps To | Source Column in CSV |
|--------------------|---------|---------------------|
| `{{first_name}}` | Recipient's first name | `first_name` |
| `{{company}}` | Pharmacy name | `company` |
| `{{signature}}` | Full email signature block | Set in Email Account settings in Smartlead |
| `{{first_name_sender}}` | Your first name | Set as global variable in Smartlead account settings |

**Set `{{signature}}` in Smartlead Email Account settings:**
```
Ethan Atchley
Prescriber Pipeline
ethan@[yourdomain].com
```
No phone number in signature — reduces spam signals.

**Set `{{first_name_sender}}`** as a campaign-level variable: value = `Ethan`

### 3.6 Preview Before Saving

After entering all three steps, use Smartlead's preview function to send a test email to your personal inbox (`ethan@gmail.com` or similar). Verify:
- Subject lines appear correctly (no curly braces showing)
- `{{first_name}}` previews with a real name (e.g., "Sarah")
- `{{company}}` previews with a real pharmacy name
- No HTML artifacts or broken formatting
- Check your spam folder — if it lands in spam, fix DNS before proceeding

---

## Section 4: Contact Upload

### 4.1 Required CSV Columns

Smartlead requires these exact column headers (lowercase, underscore-separated):

| Column | Description | Example |
|--------|-------------|---------|
| `first_name` | Contact first name | `Sarah` |
| `last_name` | Contact last name | `Kim` |
| `email` | Verified email address | `sarah@compoundrxaustin.com` |
| `company` | Pharmacy name (full legal name or DBA) | `Compound Rx Austin` |
| `title` | Job title | `Owner-Pharmacist` |

Optional but recommended:
| Column | Description |
|--------|-------------|
| `state` | Two-letter state code — used for segment tracking |
| `city` | City — useful for personalization reference |
| `phone` | Phone number — not used in sequence but valuable for CRM |
| `website` | Pharmacy website — used in enrichment |
| `linkedin_url` | LinkedIn profile — for manual follow-up prioritization |

### 4.2 Source Files

Run enrichment pipeline before uploading:

```bash
# Step 1: Export from Apollo (500–750 contacts, filters in sequences/compounding-pharmacy.md)
# Save as: apollo-compounding-[date].csv

# Step 2: Download state board CSVs
# TX: pharmacy.texas.gov
# FL: flhealthsource.gov
# CA: pharmacy.ca.gov
# NY: op.nysed.gov
# IL: idfpr.illinois.gov

# Step 3: Merge + enrich
doppler run --project ent-agency-automation --config dev -- \
  python ~/Desktop/ECAS/signals/pharmacy_list_enricher.py \
  --input apollo-compounding-[date].csv

# Output: enriched_apollo-compounding-[date].csv
```

### 4.3 Deduplication Rules

Before uploading to Smartlead, dedup on:
1. **Email address** — exact match, remove duplicates
2. **Company name + owner name** — fuzzy match (pharmacy_list_enricher.py handles this)
3. **Phone number** — if same phone appears at two records, keep the one with the verified email

Chain pharmacy filter (remove any contact at):
- Walgreens, CVS, Walmart, Rite Aid, Kroger, Costco, Target, Publix, Meijer, Winn-Dixie, Health Mart (chain-owned), Medicine Shoppe (chain-owned)

### 4.4 Segmentation

Create separate upload batches by state for tracking purposes. This lets you monitor which states have the best reply rates and double down accordingly.

Recommended initial batches:
- Batch 1: TX (largest compounding pharmacy state)
- Batch 2: FL + CA
- Batch 3: NY + IL
- Batch 4: All other states

Add a `segment` column to each batch CSV (`TX`, `FL-CA`, `NY-IL`, `Other`) — this lets you filter in Smartlead analytics.

### 4.5 Upload Process

1. Smartlead → Campaign → Leads → Upload CSV
2. Map columns to Smartlead fields (first_name → First Name, etc.)
3. Check "Skip duplicates" → ON
4. Confirm preview: verify first 5 rows show correct data
5. Submit upload
6. Wait for upload to complete (may take 2–5 minutes for 500+ contacts)

---

## Section 5: Doppler Keys to Set

Set these in Doppler before the signal pipeline goes live. Some already exist (Smartlead API key, Findymail) — only the campaign IDs need to be added after creating campaigns.

**Project:** `ent-agency-automation` | **Config:** `dev`

To set a key:
```bash
doppler secrets set KEY_NAME "value" --project ent-agency-automation --config dev
```

| Key | What It Is | When to Set |
|-----|------------|-------------|
| `SL_CAMPAIGN_COMPOUNDING_PHARMACY` | Smartlead campaign ID for compounding pharmacy outreach — get from URL after creating campaign: `app.smartlead.ai/campaign/{ID}/` | After creating campaign in Section 2 |
| `SL_CAMPAIGN_SLEEP_LAB` | Campaign ID for AASM sleep lab outreach (Phase 4) | When sleep lab campaign is created |
| `SL_CAMPAIGN_IMAGING` | Campaign ID for imaging center outreach (Phase 4) | When imaging campaign is created |
| `SL_CAMPAIGN_HOME_HEALTH` | Campaign ID for home health agency outreach (Phase 4) | When home health campaign is created |
| `SL_CAMPAIGN_RECOVERY` | Campaign ID for recovery center outreach (Phase 4) | When recovery campaign is created |
| `SL_CAMPAIGN_JOB_POSTING_COMPOUNDING` | Campaign ID for job-posting-triggered enrollment (Phase 2 signal) | When job posting signal campaign is created |
| `FINDYMAIL_API_KEY` | Findymail email enrichment API key | Before running pharmacy_list_enricher.py — get from app.findymail.com |
| `RAPIDAPI_KEY` | RapidAPI key (used by some enrichment scripts) | Before running enrichment pipeline |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook for signal notifications | If not already set — get from ContractMotion Slack workspace App settings |

**To confirm the campaign ID:**
After creating the campaign in Smartlead, open the campaign and check the URL:
```
https://app.smartlead.ai/app/campaign/3XXXXXX/overview
                                       ^^^^^^^
                                       This number is the campaign ID
```
Set it: `doppler secrets set SL_CAMPAIGN_COMPOUNDING_PHARMACY "3XXXXXX" --project ent-agency-automation --config dev`

**Verify existing keys are set before launch:**
```bash
doppler secrets get FINDYMAIL_API_KEY RAPIDAPI_KEY SLACK_WEBHOOK_URL \
  --project ent-agency-automation --config dev
```

---

## Section 6: Launch Checklist

Work through this top to bottom. Do not activate the campaign until every box is checked.

### Domain & Deliverability
- [ ] Sending domain registered (neutral/health-adjacent — not ContractMotion)
- [ ] Google Workspace inbox created: `ethan@[yourdomain].com`
- [ ] MX records set and verified (mxtoolbox.com)
- [ ] SPF record verified (`v=spf1 include:_spf.google.com ~all`)
- [ ] DKIM record generated in Google Workspace and DNS verified
- [ ] DMARC record set (`p=none` to start)
- [ ] All DNS records show green in MXToolbox SuperTool
- [ ] Smartlead warmup has been running for **14+ days** (check warmup dashboard)
- [ ] Warmup daily volume reached 40+ emails/day

### Contacts
- [ ] Apollo export pulled (500–750 contacts, filters from `sequences/compounding-pharmacy.md`)
- [ ] State board CSVs downloaded for TX, FL, CA (at minimum)
- [ ] `pharmacy_list_enricher.py` run on merged list
- [ ] Chain pharmacies filtered out
- [ ] Deduplication completed (no duplicate emails)
- [ ] 500+ verified email addresses in final upload CSV
- [ ] CSV columns match required format (first_name, last_name, email, company, title)
- [ ] Contacts uploaded to Smartlead campaign
- [ ] Upload preview confirmed — first 5 rows look correct

### Campaign Configuration
- [ ] Campaign name follows convention: `Healthcare-CompoundingPharmacy-Owners-[Date]`
- [ ] From name is personal (`Ethan Atchley`) — not agency name
- [ ] Click tracking is OFF
- [ ] Open tracking is ON
- [ ] Stop on reply is YES
- [ ] Schedule: Mon–Fri, 8am–5pm recipient timezone
- [ ] Daily limit: 40/day (week 1)
- [ ] Unsubscribe footer added to all three steps

### Sequence Copy
- [ ] Email 1 subject: `how new prescribers find {{company}}`
- [ ] Email 2 subject: `the GLP-1 cliff`
- [ ] Email 3 subject: `last one from me`
- [ ] All three email bodies loaded (match `sequences/compounding-pharmacy.md` exactly)
- [ ] Step delays: Day 1 → wait 3 days → Day 4 → wait 5 days → Day 9
- [ ] `{{signature}}` set in Email Account settings (no phone number)
- [ ] `{{first_name_sender}}` set as campaign variable: value = `Ethan`
- [ ] Test send to personal inbox — previews correctly
- [ ] Test email is NOT in spam folder (if it is, fix DNS and re-test)

### Infrastructure
- [ ] `SL_CAMPAIGN_COMPOUNDING_PHARMACY` set in Doppler (campaign ID from Smartlead URL)
- [ ] `FINDYMAIL_API_KEY` confirmed set in Doppler
- [ ] Smartlead Signal Intelligence webhook is active — n8n workflow `4ZkYDJpqg5qBXdAW` status = ACTIVE in n8n dashboard
- [ ] Test reply classification: send a test reply to `ethan@[yourdomain].com`, confirm it appears in Airtable `tblUv9HIiiE4ZOALd` (Smartlead Signals table in Agency CRM `app9fVT4bBMHlCf2C`)
- [ ] Slack `#ecas-ops` receives notification when a signal is logged

### Final Gate
- [ ] All boxes above are checked
- [ ] Today is a weekday (Mon–Fri)
- [ ] Time is between 8am and 4pm CT (to allow first batch to send same day)
- [ ] Campaign status set to ACTIVE in Smartlead

---

## Section 7: Post-Launch Monitoring

### Day 1–3 (Critical Window)
Check daily:
- Smartlead dashboard → campaign → Analytics
- Open rate target: 40%+ (if below 20%, pause and investigate DNS/warmup)
- Spam complaints: 0 (any spam complaint = pause immediately and investigate)
- Bounce rate: below 5% (if above, enrichment had bad data — audit list)

### Week 1 Report
After 7 days, check:
- Total sent, open rate, reply rate, bounce rate
- Replies categorized in Airtable `tblUv9HIiiE4ZOALd`: Interested / Meeting Request / Not Interested
- Any DNC requests processed (remove from Smartlead + flag in Airtable)

### What "Good" Looks Like

| Metric | Target | Action If Below |
|--------|--------|-----------------|
| Open rate | 40–60% | Check subject lines, check spam folder, verify DKIM |
| Reply rate | 5–10% | Review copy, check if list quality is good |
| Positive reply rate | 2–4% | Good — these become sales calls |
| Bounce rate | < 3% | If above: list enrichment quality issue — re-run Findymail |
| Spam complaint rate | 0% | Any complaint: pause campaign, investigate immediately |

### Reply Handling
All replies are auto-classified by n8n workflow `4ZkYDJpqg5qBXdAW` (Smartlead Signal Intelligence):
- **Positive / Meeting Request** → Slack alert to `#ecas-ops` → book discovery call
- **Objection** → Review the objection handling table in `sequences/compounding-pharmacy.md` → respond manually
- **Unsubscribe** → Smartlead marks contact, removes from sequences
- **OOO** → Smartlead pauses until return date (if Smartlead OOO detection is enabled)

---

## Appendix: Domain Registration Checklist

Use this if registering through Namecheap (recommended):

1. Go to namecheap.com → search your chosen domain
2. Add to cart → checkout (no extras needed — skip privacy protection, it's free now)
3. After purchase: Namecheap Dashboard → Domain List → Manage → Advanced DNS
4. Delete default Namecheap parking records (URL redirect, etc.)
5. Add MX records (Priority + Value from Section 1.3)
6. Add SPF TXT record at `@`
7. After setting up Google Workspace: add DKIM TXT record
8. Add DMARC TXT record
9. Save all records → wait 24–48 hours for propagation
10. Verify at mxtoolbox.com before proceeding

---

*Last updated: 2026-04-05 | Owner: ContractMotion*
*Sequence source: `sequences/compounding-pharmacy.md`*
*Signal webhook: n8n `4ZkYDJpqg5qBXdAW` | Airtable signals: `tblUv9HIiiE4ZOALd` in `app9fVT4bBMHlCf2C`*
