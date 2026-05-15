# Apollo Pull SOP — Compounding Pharmacy Owner Contacts

**Goal:** Build a list of 500–750 owner-pharmacist contacts across TX, FL, CA, NY, IL for physician referral pipeline outreach.
**Tool:** Apollo.io (app.apollo.io)
**Output:** CSV exported from Apollo, enriched via Findymail before Smartlead load

---

## Step 1: Open the People Search

1. Log into [app.apollo.io](https://app.apollo.io)
2. In the left sidebar, click **Search** → **People**
3. You'll land on the People filters panel. All filter steps below apply here.

---

## Step 2: Set Job Title Filters

1. Click **Job Titles** in the left filter panel
2. Add each of the following as separate entries (Apollo matches on partial):
   - `Owner`
   - `Pharmacist-in-Charge`
   - `PIC`
   - `Director of Pharmacy`
   - `Pharmacist`
3. Set the match mode to **Any** (not All)

> **Why these titles:** "Owner" and "PIC" are the decision makers. "Pharmacist" catches sole practitioners who are their own PIC but don't use a formal title. "Director of Pharmacy" appears at larger independents.

---

## Step 3: Set Industry Filters

1. Click **Industry** in the filter panel
2. Add both:
   - `Pharmaceutical Retail`
   - `Health, Wellness & Fitness`
3. Set to **Any**

> Apollo classifies many independent pharmacies under Health/Wellness rather than Pharmaceutical Retail. Both are needed.

---

## Step 4: Set Company Size

1. Click **# Employees** (or "Company Headcount")
2. Set range: **1 to 25**

> Compounding pharmacies are almost universally small operations. Anything over 25 employees is likely a chain, hospital pharmacy, or 503B facility — not the target.

---

## Step 5: Set Company Keywords

1. Click **Company Keywords** (may appear as "Keywords" under company filters)
2. Add the following as **Any** match:
   - `compounding`
   - `503A`
   - `BHRT`
   - `sterile`
   - `GLP-1`
   - `semaglutide`
   - `peptide`

> These keywords appear in pharmacy names, taglines, and Apollo company descriptions. They are the strongest signal for a compounding-focused operation.

---

## Step 6: Set Location — United States

1. Click **Location** → **Person Location** (not company HQ)
2. Select **United States**
3. Leave country-level filter active — you'll add state-level in Step 7

---

## Step 7: Run State-by-State Pulls

Pull each state separately to hit volume targets and keep lists clean for state board dedup.

| State | Target Contacts | Add Filter |
|-------|----------------|------------|
| Texas | 150–200 | Location → State → Texas |
| Florida | 100–150 | Location → State → Florida |
| California | 100–150 | Location → State → California |
| New York | 75–100 | Location → State → New York |
| Illinois | 75–100 | Location → State → Illinois |

**How to add state filter:**
1. Under **Location**, click **Add Location**
2. Select **State/Province**
3. Type the state name and select from the dropdown
4. Run the search, review the count, then export

Run each state as a separate export. Label the file clearly: `apollo-TX-[date].csv`, `apollo-FL-[date].csv`, etc.

---

## Step 8: Apply Exclusion Filters

Before exporting each state list, add these exclusions to remove chain pharmacies and non-targets:

1. Click **Company Keywords** → switch the second keyword block to **Exclude**
2. Add each of the following as excluded keywords:
   - `hospital`
   - `Walgreens`
   - `CVS`
   - `Walmart`
   - `Rite Aid`
   - `chain`
   - `retail`
   - `clinic` (optional — catches hospital-adjacent entries)
   - `health system`
   - `medical center`

> Apollo's keyword exclusion is applied to company name and description. This removes the bulk of false positives.

---

## Step 9: Verify Required Fields Before Export

Before clicking Export, use Apollo's column selector to confirm these fields are visible in the results table:

| Field | Required | Notes |
|-------|----------|-------|
| First Name | Yes | Must be populated — no "Unknown" entries |
| Last Name | Yes | Must be populated |
| Email | Yes | Even "guessed" Apollo email is fine — Findymail will verify |
| Job Title | Yes | Confirms decision-maker match |
| Company Name | Yes | Used for state board dedup |
| Company Phone | Recommended | Used for state board dedup |
| LinkedIn URL | Recommended | Enrichment fallback |
| City | Yes | For geo verification |
| State | Yes | For geo verification |
| Company Address | Recommended | Used in state board fuzzy match |

**How to check:** Click the column icon (top right of results table) and verify all above fields are toggled on before export.

---

## Step 10: Export the CSV

1. Click the **Export** button (top right of results)
2. Select **Export to CSV**
3. Choose **All Contacts** (not just selected)
4. Select **All Fields** or manually check all required fields from Step 9
5. Apollo will email the CSV download link within 1–5 minutes
6. Download and save to: `~/Desktop/research-lab/niches/healthcare-referral-pipeline/lists/apollo-[STATE]-[YYYY-MM-DD].csv`

> Apollo free tier limits exports. If hitting export limits, prioritize TX first (largest market), then FL and CA.

---

## Step 11: State Board Dedup

After downloading all state CSVs from Apollo, deduplicate against the state board data.

**The goal:** State board data has contacts Apollo missed (small pharmacies with no web presence). Apollo has email and title. Merging both fills gaps.

**Dedup logic (run via `pharmacy_list_enricher.py`):**
1. **Exact phone match** — if Apollo and state board share the same 10-digit phone number, they are the same business. Keep Apollo record (has email), attach state board address if missing.
2. **Company name fuzzy match at 85%** — normalize both names (strip "Pharmacy", "Rx", "Compounding", punctuation, case), then run fuzzy match. 85%+ = same business.
3. **Address match** — if company name match is 70–84%, check if street address also matches. Combined = confirmed duplicate.

**What to do with duplicates:**
- Keep the record with the most complete data (email + phone + address)
- Flag source as `apollo+state_board` when merged
- Discard the thinner record

---

## Quality Check Before Enrichment

Run a quick audit before sending to Findymail:

| Check | Threshold | Action if Fails |
|-------|-----------|----------------|
| Email field populated | > 60% of rows | Re-export with email column active |
| First name populated | 100% | Remove rows without first name |
| Company name populated | 100% | Remove rows without company |
| State matches target state | 100% | Filter and remove cross-state entries |
| Title matches target list | > 80% | Review and manually remove obvious mismatches |

---

## Summary: Full Filter Configuration Reference

```
People Search Filters:
  Job Titles (Any):     Owner, Pharmacist-in-Charge, PIC, Director of Pharmacy, Pharmacist
  Industry (Any):       Pharmaceutical Retail | Health, Wellness & Fitness
  Headcount:            1–25
  Company Keywords:     compounding, 503A, BHRT, sterile, GLP-1, semaglutide, peptide
  Location:             United States → [State]
  Exclude Keywords:     hospital, Walgreens, CVS, Walmart, Rite Aid, chain, retail

Export Fields:
  first_name, last_name, email, title, company_name, company_phone,
  linkedin_url, city, state, company_address
```

---

*After export, pass CSVs through `~/Desktop/ECAS/signals/pharmacy_list_enricher.py` for Findymail enrichment, dedup, and chain pharmacy filtering before loading to Smartlead.*
