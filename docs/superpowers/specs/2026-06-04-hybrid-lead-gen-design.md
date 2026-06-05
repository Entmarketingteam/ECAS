# Design Specification: Hybrid Sourcing, Multi-Directory Scraping, & Cost-Optimized Email Verification Architecture

**Owner:** Ethan Atchley & Emily Atchley (ENT Agency)  
**Date:** 2026-06-04  
**Status:** Under Collaborative Review (Brainstorming Phase)  
**Location:** `~/Desktop/ECAS-industry-factory/docs/superpowers/specs/2026-06-04-hybrid-lead-gen-design.md`  

---

## 1. Executive Summary

To scale our B2B outbound engine for **Custom Builders** and **Document Destruction / Commercial Industries**, we must move away from credit-heavy **Clay Enrichment Waterfalls** which can cost between $0.15 to $0.45 per successfully enriched lead. 

This design implements a **Code-First Hybrid Sourcing Pipeline** inside the `ECAS` ecosystem. It leverages:
1.  **Free/Low-Cost Sourcing:** Association directory scrapers (NAHB, Local Builders Associations, i-SIGMA/NAID shredding directories) and local DFW permit pollers.
2.  **Domain Finder:** Cost-effective web searches (SerpAPI/Google) to resolve company domains before hitting any enrichment API.
3.  **Sales Navigator / Apollo Sourcing:** Querying precise job titles (Owner, VP of Construction, Facility/Operations Manager) to identify contacts.
4.  **Verification Cascade:** **Million Verifier Bulk V2** ($0.00019/verify) as a cheap first-pass filter, fallback to **Findymail API** ($0.01/search) *only* when emails are missing or catch-all.

---

## 2. Strategic Sourcing Architecture (Hybrid Model)

We are targeting two highly profitable, distinct commercial niches:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        SOURCE & DIRECTORIES                            │
└───────────────────┬────────────────────────────────┬───────────────────┘
                    │                                │
      [Custom Builders Niche]            [Doc Destruction Niche]
      - Local DFW Permit Pollers         - i-SIGMA / NAID Member Directories
      - Dallas Builders Association      - Regional Law, Accounting, Medical
      - NAHB Directory Scraper           - Commercial Facility Lists
                    │                                │
                    └───────────────┬────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      DOMAIN FINDER (SerpAPI / Google)                  │
│       Resolves business names to clean corporate domains for $0.002   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  CONTACT SOURCING (Sales Navigator / Apollo)           │
│        Targeted title lookup: Owners, VPs, and Facilities Managers     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  EMAIL VERIFICATION CASCADE                            │
│        - Pass 1: Million Verifier Bulk V2 (Fractional Cent)            │
│        - Pass 2: Findymail Search/Verify (Fallback only)                │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    CRM (Airtable) & OUTREACH (Smartlead)               │
│        Pushes clean, verified leads directly into cadences             │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Component Breakdown

### A. Directory Scraping & Permits (Sourcing)
*   **Custom Builders:** Extend the existing `association_directory_scraper.py` template to target home builder databases:
    *   *Dallas Builders Association:* Scrapes active local builders, GC firms, and remodelers in North Texas.
    *   *NAHB (National Association of Home Builders):* Queries members categorized by residential custom builds.
    *   *Permit Poller (`signals/permit_poller.py`):* Polls municipal Socrata/ArcGIS databases in DFW (Plano, Frisco, Dallas, Fort Worth) for active residential/commercial permits over $100k valuation.
*   **Document Destruction:** Target security associations:
    *   *i-SIGMA / NAID Directory:* Scrapes certified secure shredding, computer recycling, and document destruction providers by region.
    *   *Commercial Facility Scrapes:* Scrapes regional law offices, medical clinics, and accounting firms in the DFW metroplex that legally require high-security recurring shredding containers.

### B. Cost-Efficient Domain Finder (`tools/domain_resolver.py`)
Clay charges multiple credits to search for a company's domain. We will bypass this by writing a Python helper:
1.  Input: Company Name + City/State (from directories).
2.  Execution: Executes a clean web search using our `SERP_API_KEY` (or SerpAPI/SearchAPI) looking for the company website.
3.  Regex Parsing: Extracts the domain (e.g., `companyname.com`) from the top search results.
4.  Cost: **$0.002** per search (vs. Clay's premium credit rates).

### C. Contact Finder (`tools/contact_finder.py`)
Once we have the domain, we resolve the correct decision-maker:
1.  **Apollo Search API:** We query the Apollo `people/search` endpoint using the corporate domain and our configured target titles:
    *   *Builders:* `Owner`, `President`, `VP of Construction`, `Chief Estimator`, `Project Executive`.
    *   *Doc Destruction:* `Office Manager`, `VP Operations`, `HR Director`, `Facilities Manager`, `General Counsel`.
2.  **LinkedIn Sales Navigator Link:** Match the contact to their LinkedIn Sales Navigator URL (`https://www.linkedin.com/sales/people/...`) for outbound visibility.

### D. The Million Verifier + Findymail Cascade (`tools/verify_cascade.py`)
To prevent costly and useless bounces, every email undergoes a two-step validation:

1.  **Pass 1: Million Verifier Bulk V2**
    *   Uses the bulk endpoint (`https://api.millionverifier.com/bulk/v2/verify`) which is lightning-fast and exceptionally cheap.
    *   If the email status returns `deliverable` → **Enrolled instantly** (90% of leads).
2.  **Pass 2: Findymail Fallback (Premium)**
    *   If Million Verifier returns `catch_all`, `risky`, or is missing entirely, we trigger the **Findymail Search/Verify API**.
    *   Findymail re-verifies catch-alls with high precision or finds alternative corporate email addresses.
3.  **Result:** Cuts enrichment costs by over **75%** compared to traditional Clay/Apollo waterfalls.

---

## 4. Database & Airtable Schema Integration

Leads will be synced directly into the existing ECAS Airtable base (`appoi8SzEJY8in57x`):

*   **Projects Table (`tbloen0rEkHttejnC`):**
    *   `owner_company` (Builder or Shredding Client name)
    *   `domain` (Resolved website domain)
    *   `sector` (Marked as `Custom Builders` or `Document Destruction`)
    *   `source` (Permit, NAHB, i-SIGMA, etc.)
    *   `permit_valuation` / `permit_details` (If permit signal)
*   **Contacts Table (`tblPBvTBuhwlS8AnS`):**
    *   `first_name`, `last_name`
    *   `email`
    *   `title`
    *   `linkedin_url`
    *   `verification_status` (`verified_clean`, `catch_all_verified`, `bounced`)
    *   `smartlead_status` (`enrolled`, `bounced`, `paused`)

---

## 5. Cost Analysis: Code-First vs. Clay Waterfall

| Enrichment Step | Clay Waterfall Cost (per lead) | Code-First Pipeline Cost (per lead) | Savings |
|---|---|---|---|
| Domain Resolution | $0.02 (Clay search) | $0.002 (SerpAPI lookup) | **90%** |
| Contact Finder | $0.05 (Clay Apollo find) | $0.005 (Direct Apollo API) | **90%** |
| Email Verification | $0.04 (Clay verification) | $0.00019 (Million Verifier Bulk) | **99%** |
| Catch-All Verify | $0.12 (Clay Scrubby) | $0.01 (Findymail Verify) | **91%** |
| **Total Cost / Lead** | **~$0.23** | **~$0.017** | **~92% Savings** |

By running this pipeline in Python on Railway, we can process **10,000 leads for ~$170** instead of **~$2,300** inside Clay.

---

## 6. Project Directory Additions

To implement this design, we will add the following files to `ECAS-industry-factory`:

1.  `signals/permit_poller.py` — Custom builder permit scaper.
2.  `signals/builder_association_scraper.py` — Dallas Builders Association & NAHB scraper.
3.  `signals/shredding_association_scraper.py` — i-SIGMA / NAID member directory scraper.
4.  `tools/domain_resolver.py` — Cheap Google/SerpAPI domain finder.
5.  `tools/verify_cascade.py` — Million Verifier Bulk V2 + Findymail verification pipeline.
6.  `tools/load_shredding_leads.py` — Traditional list loader.

---

## 8. System Resilience, Alerts & Recovery Fallback Specification

To ensure 24/7 autonomous pipeline reliability and keep Ethan and Emily informed when issues arise, the system features three structural safeguards:

### A. Cascade Failovers
The system must gracefully degrade and recover from API/network issues without losing leads or corrupting state:
1.  **Domain Resolution Fallback:** If `SerpAPI` returns quota exhaustion (402) or is down, the resolver automatically fails over to a secondary `SearchAPI` key or a custom local search scraper (e.g., using `googlesearch-python` with rotating proxies/agents).
2.  **Email Verification Fallback:**
    *   If **Million Verifier** is offline or rate-limiting, the lead verification is paused and put in a temporary sqlite retry queue.
    *   If Million Verifier returns `catch_all` or `risky`, the cascade triggers **Findymail** with strict rate-limiters (e.g., max 5 queries per minute) to respect Findymail API limits.
    *   If Findymail also fails or is out of credits, lead status is set to `findymail_failed` and routed to the manual review queue rather than being dropped or triggering false bounces.

### B. Real-Time Alert Notifications
Direct API integrations with Slack / Discord webhooks will notify Emily and Ethan immediately if:
*   **Credit Threshold Warnings:** SerpAPI, Apollo, Million Verifier, or Findymail key credits fall below **10%** of their monthly allotment.
*   **Scraper Blockages:** Any scraper (Permit Poller, NAHB, i-SIGMA) experiences **3+ consecutive HTTP blocks** (403 Forbidden / Cloudflare Turnstile).
*   **Process Halts:** Uncaught exceptions in multiprocessing pools halt workers (critical error alert).
*   **Format of Webhook Alerts:**
    ```json
    {
      "channel": "#gtm-alerts",
      "username": "ECAS Pipeline Sentinel",
      "text": "⚠️ *CRITICAL CREDIT ALERT*: Findymail API key has only 45 credits remaining. Please top up to avoid pipeline pauses.",
      "icon_emoji": "🚨"
    }
    ```

### C. Airtable Dead-Letter Queue (DLQ) & Manual Override Mode
Leads that fail automated processing are never lost. They are rerouted to a manual-resolution state:
1.  **Error Tagging:** If a lead cannot resolve a domain, or contact finding returns no results, the lead is synced to Airtable with:
    *   `verification_status` = `needs_manual_review`
    *   `error_log` = `Domain not resolved / Contact lookup failed`
2.  **Manual Intervention Grid View:** Emily and Ethan can open a dedicated Grid View in Airtable filtering for `needs_manual_review`.
3.  **Correction & Retry Checkbox:**
    *   They manually research and input the correct `domain` or `email` into the fields.
    *   They check a `Retry` checkbox field (`tblPBvTBuhwlS8AnS`).
    *   The Python daemon polls for checked `Retry` flags every 12 hours, clears errors, re-processes the leads, and enrolls them into Smartlead.

---

## 9. Next Steps & Todo Checklist

- [ ] **Task 1: Present Design Document** — Share this specification with Ethan and Emily.
- [ ] **Task 2: Spec Self-Review** — Audit requirements for ambiguity or contradictions.
- [ ] **Task 3: User Approval Gate** — Wait for approval on the Hybrid Sourcing + Verification Cascade design with integrated Alerts & Recovery safeguards.
- [ ] **Task 4: Transition to Implementation** — Once approved, invoke the `writing-plans` skill to write the daily milestones.
