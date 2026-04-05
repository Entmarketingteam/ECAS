# Association Directory Scraper — README

`signals/association_directory_scraper.py`

Scrapes 6 healthcare association directories to build pre-qualified contact lists for the compounding pharmacy prescriber pipeline. These lists supplement Apollo and state board data with contacts who have **self-identified** with the niche — the highest-intent cold list available before any additional enrichment.

---

## HTML-Scrappable vs JS-Rendered

| Association | Site | Status | Notes |
|-------------|------|--------|-------|
| APC | a4pc.org | Likely HTML | May be login-gated; check `/membership/member-directory/` — if 0 results, Apify needed |
| ABOM | abom.org | Likely HTML | WP-based; script attempts HTML + JSON REST fallback |
| AASM | sleepeducation.org | Likely HTML | Script attempts HTML + JSON REST fallback |
| PCAB | pcab.org | **JS-RENDERED** | React SPA — requests returns shell HTML, 0 pharmacy records |
| NAMS | menopause.org | **JS-RENDERED** | Dynamic map-based practitioner locator |
| IFM | ifm.org | **JS-RENDERED** | Form-based search with JS-rendered results |

The three JS-rendered sites (PCAB, NAMS, IFM) require Playwright or Apify. The script handles this gracefully: it attempts requests first, logs a `REQUIRES_JS` warning if 0 records are found, and writes a placeholder row to the CSV so the combined output notes the gap.

---

## Apify Recommendations for JS-Rendered Sites

### PCAB (pcab.org/find-a-pharmacy)

**Recommended actor:** Apify "Web Scraper" (`apify/web-scraper`)

Configuration:
```json
{
  "startUrls": [{"url": "https://pcab.org/find-a-pharmacy"}],
  "waitFor": "div.pharmacy-card, table tr.pharmacy-row",
  "pageFunction": "async function pageFunction(context) { ... }"
}
```
Inspect the rendered DOM in Chrome DevTools first to confirm the correct CSS selectors for pharmacy cards. PCAB updates their directory quarterly — run on a quarterly cron.

### NAMS (menopause.org practitioner locator)

**Recommended actor:** Apify "Web Scraper" (`apify/web-scraper`)

Strategy: Automate the ZIP code search form across major metros (50 largest US cities by population). Each search returns nearby practitioners. Deduplicate on NPI or name+state.

Alternative: Check the Network tab in DevTools while performing a search — NAMS may expose an XHR endpoint (e.g., `api.menopause.org/practitioners?zip=...`). If so, direct API calls are faster and more reliable than browser automation.

### IFM (ifm.org/find-a-practitioner)

**Recommended actor:** Apify "Web Scraper" for full JS automation, OR "Cheerio Scraper" if the results page is server-side rendered after form submission.

Strategy: Submit the search form for each US state (50 iterations). The IFM directory may also have a WordPress REST API endpoint — check `/wp-json/ifm/v1/practitioners` before setting up Playwright automation.

---

## Running the Script

```bash
# Install dependencies
pip install requests beautifulsoup4 lxml

# Run all 6 associations
python signals/association_directory_scraper.py

# Run specific associations
python signals/association_directory_scraper.py --associations abom,aasm

# Custom output directory
python signals/association_directory_scraper.py --output-dir /tmp/assoc-test
```

Output files land in `signals/output/`:
- `association_pcab_2026-04-05.csv`
- `association_apc_2026-04-05.csv`
- `association_nams_2026-04-05.csv`
- `association_ifm_2026-04-05.csv`
- `association_abom_2026-04-05.csv`
- `association_aasm_2026-04-05.csv`
- `associations_combined_2026-04-05.csv` — all records, unified columns, `source` field

---

## Feeding Output into Clay for Enrichment

After running the scraper (or Apify), the CSV files are ready for Clay enrichment.

### Clay Table Setup

1. Create a new Clay table: "Healthcare Association Contacts — [Date]"
2. Import CSV: use `associations_combined_[date].csv`
3. Key columns to map:
   - `source` → Custom field "Association Source"
   - `pharmacy_name` / `name` / `facility_name` → "Company Name" or "Contact Name"
   - `city`, `state` → Location fields

### Clay Enrichment Waterfall

For pharmacy contacts (PCAB, APC):
```
1. NPI Registry lookup by company name + state → get NPI, address, phone
2. Website scraper → extract contact email from pharmacy website
3. Findymail → email enrichment (first + last name + domain)
4. Hunter.io fallback → if Findymail returns no result
5. Output: enriched CSV ready for Smartlead upload
```

For physician contacts (NAMS, IFM, ABOM):
```
1. NPI Registry lookup by name + state → confirm active license, get NPI
2. Proxycurl → LinkedIn profile + practice info
3. Findymail → email enrichment
4. Apollo → fill gaps in phone/email
5. Output: physician targeting list for client delivery
```

For facility contacts (AASM):
```
1. NPI Registry lookup by facility name + state → taxonomy code 261QS1200X
2. Google Maps scraper (Outscraper) → get current phone, website, hours
3. Website scraper → extract owner/director contact
4. Findymail → email enrichment
5. Output: sleep center targeting list
```

---

## Update Frequency

| Association | Recommended Frequency | Signal Value | Notes |
|-------------|----------------------|--------------|-------|
| PCAB | Quarterly | **High** — new accreditation = high-intent signal | New accreditations = trigger outreach within 14–21 days (see PRD Section 5) |
| AASM | Monthly | **High** — new accreditation = high-intent signal | New accreditations = trigger outreach within 14 days |
| APC | Monthly | Medium | Member list changes as pharmacies join/renew |
| ABOM | Semi-annual | Medium | Board certification is annual; full list changes slowly |
| NAMS | Semi-annual | Medium | Certified practitioners, annual renewal cycle |
| IFM | Semi-annual | Medium | Board-certified practitioners, annual renewal |

### Automating PCAB/AASM as Signals

Wire the quarterly/monthly scrape into the ECAS signal pipeline:

1. Run scraper → compare output to previous run (diff on pharmacy/facility name + state)
2. New entries = new accreditations = high-intent signal
3. Enrich new entries via Clay → Findymail
4. Enroll in Smartlead:
   - PCAB new accreditation → `SL_CAMPAIGN_COMPOUNDING_PHARMACY`
   - AASM new accreditation → `SL_CAMPAIGN_SLEEP_LAB` (when built)
5. Outreach angle for new accreditations:
   - PCAB: "Now that you're accredited, physicians will take your calls. We help you make those calls at scale."
   - AASM: Same positioning for sleep centers

This is Phase 2 of the PRD build order (`signals/npi_poller.py` follows the same pattern).

---

## File Structure

```
ECAS/signals/
├── association_directory_scraper.py   ← main scraper (this script)
├── association_scraper_README.md      ← this file
├── npi_poller.py                      ← NPI registry weekly poller
├── pharmacy_list_enricher.py          ← Findymail enrichment pipeline
└── output/
    ├── association_pcab_[date].csv
    ├── association_apc_[date].csv
    ├── association_nams_[date].csv
    ├── association_ifm_[date].csv
    ├── association_abom_[date].csv
    ├── association_aasm_[date].csv
    └── associations_combined_[date].csv
```
