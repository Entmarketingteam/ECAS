# CMS Part D Prescribing Data — How to Use for Physician Targeting

**Source:** `data.cms.gov/provider-summary-by-type-of-service/medicare-part-d-prescribers`
**Cost:** Free
**Update frequency:** Annual (most recent: 2023 data, released 2024)
**What it is:** Every physician in the US who prescribed a Medicare Part D drug, what drug, how many prescriptions, in what geography.

---

## Why This Is the Secret Weapon

This is what pharma reps pay IQVIA $50k+/year to access. You get it free.

For a compounding pharmacy client in Dallas, you can pull every physician within 25 miles who prescribed estradiol, testosterone, semaglutide, or progesterone in the last 12 months — sorted by prescription volume. These are physicians **already writing the exact scripts the pharmacy wants to compound.** Not keyword-guessed specialties. Actual prescription data.

---

## Download Instructions

1. Go to: `data.cms.gov/provider-summary-by-type-of-service/medicare-part-d-prescribers`
2. Select: "Medicare Part D Prescribers - by Provider and Drug"
3. Download full dataset (CSV) — ~2GB, worth it
4. Or use the API for filtered pulls (see below)

---

## Key Fields

| Field | Description | Use |
|-------|-------------|-----|
| `Prscrbr_NPI` | Physician NPI number | Cross-ref with NPI registry for contact info |
| `Prscrbr_Last_Org_Name` | Last name or org name | Identify physician |
| `Prscrbr_First_Name` | First name | Personalization |
| `Prscrbr_City` | City | Geography filter |
| `Prscrbr_State_Abrvtn` | State | Geography filter |
| `Prscrbr_Zip5` | 5-digit zip | Precise geography |
| `Prscrbr_Type` | Specialty description | Specialty filter |
| `Gnrc_Name` | Generic drug name | THE key filter |
| `Brnd_Name` | Brand name | Cross-reference |
| `Tot_Clms` | Total claims | Volume filter — use min 10+ |
| `Tot_30day_Fills` | 30-day fills | Active prescribing indicator |
| `Tot_Drug_Cst` | Total drug cost | Revenue proxy |
| `Tot_Benes` | Total beneficiaries | Patient base size |

---

## Drug Filters by Niche

### Compounding Pharmacy — BHRT / Hormone
```
Gnrc_Name IN:
  Estradiol
  Progesterone
  Testosterone
  Testosterone Cypionate
  Testosterone Enanthate
  Dehydroepiandrosterone (DHEA)
  Estriol
  Estrone
```

### Compounding Pharmacy — GLP-1 / Weight Loss
```
Gnrc_Name IN:
  Semaglutide
  Tirzepatide
  Liraglutide
  Phentermine
  Topiramate
```

### Compounding Pharmacy — Pain / Dermatology
```
Gnrc_Name IN:
  Ketamine (topical)
  Gabapentin
  Lidocaine
  Diclofenac
  Tretinoin
  Hydroquinone
```

### Sleep Lab Referral Sources
```
Prscrbr_Type IN:
  Family Practice
  Internal Medicine
  Pulmonary Disease
  Cardiology
  Neurology
Filter: high Tot_Clms prescribers in target geography
```

---

## API Usage (Filtered Pulls)

```bash
# Physicians who prescribed semaglutide in Texas, min 10 claims
curl "https://data.cms.gov/data-api/v1/dataset/9552e21a-09e5-4c61-9695-8e8f90a5f6cb/data?\
$filter=Gnrc_Name eq 'Semaglutide' and Prscrbr_State_Abrvtn eq 'TX' and Tot_Clms ge 10\
&$select=Prscrbr_NPI,Prscrbr_Last_Org_Name,Prscrbr_First_Name,Prscrbr_City,Prscrbr_Zip5,Prscrbr_Type,Tot_Clms\
&$limit=5000"
```

Note: Dataset ID changes annually. Check data.cms.gov for current dataset ID.

---

## Clay Workflow (Physician List for Pharmacy Client)

```
Step 1: CMS Part D pull
  Input: drug name(s) + state/zip radius + min claims threshold
  Output: NPI, name, specialty, zip, claim count

Step 2: NPI registry cross-reference
  Input: NPI number
  Output: practice address, phone, entity type, taxonomy code

Step 3: State medical board check
  Input: NPI + state
  Output: active/inactive license status

Step 4: Clay enrichment columns
  - Website (Clearbit / Clay web scrape)
  - LinkedIn URL (LinkedIn enrichment)
  - Email (waterfall: Findymail → Hunter → Apollo)
  - Practice size estimate
  - "Prescribes [drug]" personalization field

Step 5: Smartlead load
  Specialty-matched sequence with personalization:
  "Physicians in [city] who prescribe [drug] for their patients..."
```

---

## Prioritized Geographies for Pilot

High-density metro areas with large compounding pharmacy + prescriber markets:
1. Dallas-Fort Worth, TX (75201–76299)
2. Houston, TX (77001–77299)
3. Miami-Fort Lauderdale, FL (33101–33499)
4. Los Angeles, CA (90001–91999)
5. Atlanta, GA (30301–30399)
6. Phoenix, AZ (85001–85099)
7. Chicago, IL (60601–60699)

Start with one metro for the first pharmacy client. Pull all relevant drug + specialty combos within 25-mile radius.

---

## Limitations

- Data is Medicare Part D only — misses private-pay, cash-pay, and Medicaid prescribers
- 1-year lag (2023 data is most current as of 2025)
- Does not include telehealth prescribers writing to out-of-state patients
- Supplement with Apollo specialty keyword search for private-pay prescribers (functional medicine, concierge MDs)
