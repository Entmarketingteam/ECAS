# State Board Download SOP — Pharmacy License Data

**Goal:** Download pharmacy licensee data from state boards to supplement Apollo pull with contacts that have no web presence.
**Target states:** TX, FL, CA, NY, IL (highest compounding pharmacy density in the US)
**Output:** Raw CSVs from each state → feed into `pharmacy_list_enricher.py` for merge + dedup against Apollo

---

## Why State Board Data

State boards are ground truth. They have every licensed pharmacy, including:
- Micro-operations run from a single pharmacist with no website
- Newly licensed pharmacies not yet indexed by Apollo
- Pharmacies where the owner title isn't in Apollo's database

Limitation: Most states provide business/pharmacy data, not individual pharmacist names. The PIC (Pharmacist-in-Charge) designation is the closest proxy for decision-maker — they are usually the owner at independent compounding pharmacies.

---

## State 1: Texas

**Board:** Texas State Board of Pharmacy (TSBP)
**Download URL:** https://www.pharmacy.texas.gov/license-verification

**Steps:**
1. Go to https://www.pharmacy.texas.gov/license-verification
2. Click **"Download License Data"** (bottom of the page or under "Licensee Data")
3. Select **License Type: Pharmacy** from the dropdown
4. Select **Status: Active**
5. Click **Download CSV**

**File format:** CSV
**Expected fields:** License Number, License Type, Business Name, DBA Name, Address 1, Address 2, City, State, Zip, Phone, Email, License Status, Issue Date, Expiration Date, Pharmacist-in-Charge Name, PIC License Number

**Identifying the decision maker:**
- Look for the **"Pharmacist-in-Charge Name"** column — this is the person to target
- At compounding pharmacies with 1–5 employees, the PIC is almost always the owner
- If PIC name is blank, the business name contact is still worth enriching via Findymail domain search

**Filtering for compounding:**
- Filter column **License Type** for: `Compounding Pharmacy`, `Sterile Compounding`, `Non-Sterile Compounding`
- If no compounding-specific license type: filter Business Name for keywords: `compounding`, `503A`, `BHRT`, `sterile`, `peptide`

**Estimated record count:** ~600–900 active compounding pharmacies in TX (largest compounding market in the US due to permissive regulation and physician density)

---

## State 2: Florida

**Board:** Florida Department of Health — Medical Quality Assurance (MQA)
**Download URL:** https://mqa-internet.doh.state.fl.us/MQASearchServices/Home

**Steps:**
1. Go to https://mqa-internet.doh.state.fl.us/MQASearchServices/Home
2. Click **"Download"** or **"Bulk Data Download"** in the top navigation
3. Select **Profession: Pharmacy**
4. Select **License Type: Community Pharmacy** (compounding pharmacies are licensed as community pharmacies in FL)
5. Select **Status: Active**
6. Click **Download** — file downloads as a zipped CSV

**Alternative bulk download:**
- Florida Health Source bulk file: https://flhealthsource.gov/MQA (look for "Bulk Data" link)
- Select Profession = Pharmacy, download full dataset, then filter locally

**File format:** CSV (zipped)
**Expected fields:** License Number, Name, License Type, Address, City, State, Zip, County, Phone, Status, Issue Date, Expiration Date

**Identifying the decision maker:**
- Florida licenses pharmacies as businesses — the individual PIC name is not always in the bulk export
- For contacts with no individual name: use company name + domain for Findymail enrichment
- Cross-reference with Apollo FL pull to attach individual names

**Filtering for compounding:**
- Florida does not have a separate "compounding pharmacy" license type — all are "Community Pharmacy"
- Post-download: filter business name for compounding keywords: `compounding`, `sterile`, `BHRT`, `peptide`, `503A`
- Also filter by zip codes known for health-focused demographics (Miami-Dade, Palm Beach, Broward, Pinellas)

**Estimated record count:** ~400–600 compounding pharmacies in FL after keyword filtering from full pharmacy dataset of ~8,000

---

## State 3: California

**Board:** California State Board of Pharmacy
**Download URL:** https://www.pharmacy.ca.gov/consumers/license_verification.shtml

**Steps:**
1. Go to https://www.pharmacy.ca.gov/consumers/license_verification.shtml
2. Look for **"License Data Download"** or **"Downloadable License Data"** link (usually in a sidebar or footer section)
3. Direct bulk file: https://www.pharmacy.ca.gov/applications/license_data.zip (updated monthly)
4. Download the zip — it contains multiple CSV files by license type
5. Open the file named `pharmacy.csv` or `PHCY.csv`
6. Filter for **License Status = CLEAR** (California's term for "active")
7. Filter for **License Type** containing: `CLX` (Clinic Pharmacy), `PHY` (Pharmacy)

**File format:** CSV (zipped archive)
**Expected fields:** License Number, License Type, Status, Name, Business Name, Address, City, Zip, Phone, Email, Issue Date, Expiration Date

**Identifying the decision maker:**
- California's bulk data includes both the pharmacist license and the pharmacy business record
- Join on: business address or business name to find the licensed pharmacist (PIC) at each location
- The pharmacist license holder at a single-location pharmacy is almost always the owner

**Filtering for compounding:**
- Filter Business Name for: `compounding`, `sterile`, `BHRT`, `peptide`, `503A`, `GLP`
- California has a high density of functional medicine and anti-aging pharmacies — also filter for `wellness`, `longevity`, `integrative`

**Estimated record count:** ~500–800 compounding pharmacies in CA (second largest market; strong in LA, Bay Area, San Diego)

---

## State 4: New York

**Board:** New York State Education Department — Office of the Professions
**Download URL:** https://www.op.nysed.gov/professions/pharmacists/

**Steps:**
1. Go to https://www.op.nysed.gov/professions/pharmacists/
2. Click **"Licensee Data"** or **"Download Licensee Data"**
3. Select **Profession: Pharmacy** (business entity, not individual pharmacist)
4. Select **Status: Registered** (NY's term for active)
5. Download CSV

**Alternative search route:**
- eSPLICENSE lookup: https://eservices.op.nysed.gov/profiler/
- Set Profession = Pharmacist or Pharmacy, Status = Registered, download results

**File format:** CSV or Excel
**Expected fields:** License Number, Name, Business Name, Address, City, Zip, Phone, License Type, Status, Registration Date, Expiration Date

**Identifying the decision maker:**
- NY licenses both individual pharmacists and pharmacy businesses separately
- Match the pharmacy business address to the licensed pharmacist at that address — if only one pharmacist is registered at that address, they are the PIC/owner
- For NYC pharmacies: borough filtering helps (Manhattan and Brooklyn have high compounding density)

**Filtering for compounding:**
- NY does not have a distinct compounding license type at the state level
- Post-download: filter on business name for compounding keywords
- Focus on zip codes: 10001–10199 (Manhattan), 11201–11249 (Brooklyn), 10301–10314 (Staten Island), 10451–10475 (Bronx), 11101–11106 (Queens)

**Estimated record count:** ~250–400 compounding pharmacies in NY after keyword filtering (dense market but smaller than TX/CA/FL in total count)

---

## State 5: Illinois

**Board:** Illinois Department of Financial and Professional Regulation (IDFPR)
**Download URL:** https://idfpr.illinois.gov/profs/Pharmacy.asp

**Steps:**
1. Go to https://idfpr.illinois.gov/profs/Pharmacy.asp
2. Click **"License Lookup"** or the **"Download"** link on the Pharmacy page
3. Direct bulk download: https://idfpr.illinois.gov/licenselookup/LicenseLookup.aspx
4. Select **Profession: Pharmacy**, **License Type: Pharmacy**, **Status: Active**
5. Click **Download Results as CSV**

**File format:** CSV
**Expected fields:** License Number, Name, Business Name, License Type, Status, Address, City, Zip, Phone, Issue Date, Expiration Date, Expiration Status

**Identifying the decision maker:**
- IDFPR data includes the pharmacist-in-charge name on some pharmacy records
- If PIC name is absent: use business name for Findymail domain lookup
- Chicago metro has the highest density; also target suburban Cook County, DuPage, and Lake County

**Filtering for compounding:**
- Filter License Type for: `Pharmacy - Compounding` if available, or filter business name keywords
- Keywords: `compounding`, `sterile`, `BHRT`, `peptide`, `503A`

**Estimated record count:** ~200–350 compounding pharmacies in IL after filtering (Chicago and suburbs; smaller market than TX/FL/CA but higher-value prescriber density)

---

## Dedup Strategy: Apollo vs. State Board

After downloading all five state files and completing the Apollo pull, merge them before enrichment.

### Matching Rules (in order of priority)

**Rule 1: Exact Phone Match**
- Normalize phone numbers to 10 digits (strip country code, spaces, dashes, parentheses)
- If Apollo phone == State Board phone → confirmed same business
- Action: Keep Apollo record (has email + name); supplement with state board address if Apollo address is blank

**Rule 2: Fuzzy Company Name Match at 85%+**
- Normalize both names: lowercase, remove punctuation, strip common suffixes (`pharmacy`, `rx`, `compounding`, `llc`, `inc`, `&`)
- Run token_sort_ratio (fuzzywuzzy/rapidfuzz) — score 85+ = same business
- Action: Merge, keep best-populated record

**Rule 3: Address + Name at 70–84%**
- If name fuzzy score is 70–84%, check street address
- Normalize address: lowercase, strip `st`/`ave`/`blvd`, keep number + first word
- If address also matches → confirmed duplicate
- Action: Same as Rule 2

### Conflict Resolution

| Scenario | Action |
|----------|--------|
| Apollo has email, state board has phone | Merge — keep both fields |
| Both have different emails | Keep Apollo email (higher quality source); flag for Findymail verification |
| State board has PIC name, Apollo has generic title | Use state board PIC name as contact |
| Duplicate confirmed, records identical | Keep one, set source = `apollo+state_board` |

---

## Fields to Extract from State Board Downloads

When processing state board CSVs, normalize to these columns before merging with Apollo data:

| Field | Source Column Name (varies by state) | Notes |
|-------|--------------------------------------|-------|
| `company` | Business Name / Pharmacy Name | Primary merge key |
| `pic_name` | Pharmacist-in-Charge / PIC Name | Split into first/last for enrichment |
| `address` | Address 1 + Address 2 | Normalize before fuzzy match |
| `city` | City | |
| `state` | State | Hard-code from file if not present |
| `zip` | Zip / Postal Code | 5-digit only |
| `phone` | Phone | Normalize to 10 digits |
| `license_type` | License Type | Keep for filtering |
| `license_status` | Status / License Status | Filter to Active/Clear/Registered only |
| `source` | (add manually) | Set to `state_board` |

---

*After download and dedup, pass the merged file to `~/Desktop/ECAS/signals/pharmacy_list_enricher.py` with `--input merged-pharmacy-list.csv`.*
