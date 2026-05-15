# NPI Taxonomy Codes — Healthcare Referral Pipeline

API: `https://npiregistry.cms.hhs.gov/api/?taxonomy_description=KEYWORD&limit=200`

## Healthcare Businesses (Client targets)

| Code | Type | Niche |
|------|------|-------|
| `3336C0003X` | Compounding pharmacy | Compounding pharmacy |
| `3336H0001X` | Home infusion pharmacy | IV therapy / home infusion |
| `261QA0600X` | Ambulatory surgery center | ASC |
| `261QR0208X` | Radiology / imaging center | Imaging |
| `261QS1200X` | Sleep lab / center | Sleep lab |
| `261QM1200X` | Magnetic resonance imaging | MRI center |
| `282N00000X` | General acute care hospital | Hospital (for discharge planner targeting) |
| `251G00000X` | Home health agency | Home health |
| `251E00000X` | Home health — hospice | Hospice |
| `261QD0000X` | Dental clinic | Dental |
| `261QO0400X` | Optometry | LASIK / optometry |
| `261QP3300X` | Pain clinic | Pain management |
| `261QR0400X` | Rehabilitation clinic | Rehab / PT |

## Physicians (Outreach targets for pharmacy clients)

| Code | Specialty | Use Case |
|------|-----------|----------|
| `207Q00000X` | Family medicine | General prescribers |
| `207QH0002X` | Obesity medicine | GLP-1 / weight loss prescribers |
| `207RG0100X` | OB-GYN | BHRT / hormone prescribers |
| `207R00000X` | Internal medicine | General + functional |
| `207N00000X` | Dermatology | Dermatology compounds |
| `208VP0014X` | Pain medicine | Pain compound prescribers |
| `207L00000X` | Anesthesiology | Pain / procedural |
| `207P00000X` | Emergency medicine | (lower priority) |
| `207RI0011X` | Integrative medicine | Functional / integrative |
| `207X00000X` | Orthopedic surgery | MSK / DME referrals |
| `2084N0400X` | Neurology | Neuropathy / pain |
| `207YS0123X` | Sleep medicine | Sleep lab referrals |
| `207V00000X` | OB-GYN | Fertility / women's health |
| `207XX0004X` | Sports medicine | MSK / performance |
| `363L00000X` | Nurse practitioner | High volume prescribers |
| `363A00000X` | Physician assistant | High volume prescribers |

## API Usage

```bash
# Find all compounding pharmacies in Texas
curl "https://npiregistry.cms.hhs.gov/api/?taxonomy_description=Compounding&state=TX&limit=200&version=2.1"

# Find new registrations (filter by enumeration_date)
curl "https://npiregistry.cms.hhs.gov/api/?taxonomy_description=Compounding&enumeration_date=2026-01-01&limit=200&version=2.1"

# Find obesity medicine physicians in Dallas zip
curl "https://npiregistry.cms.hhs.gov/api/?taxonomy_description=Obesity Medicine&postal_code=75201&limit=200&version=2.1"
```

Response fields to extract:
- `number` — NPI number
- `basic.first_name`, `basic.last_name`, `basic.organization_name`
- `basic.enumeration_date` — when registered (new = signal)
- `addresses[0].address_1`, `city`, `state`, `postal_code`
- `addresses[0].telephone_number`
- `taxonomies[0].desc` — specialty description
