# ECAS / ContractMotion — GTM Plan
**Version:** 1.0 | **Date:** 2026-03-10 | **Owner:** Ethan Atchley

---

## Executive Summary

ECAS is a signal-driven contract intelligence system that gets infrastructure EPCs on procurement short-lists before RFPs are published. The positioning is airtight, the system is live, and the differentiation is structurally defensible. This GTM plan converts that system into a repeatable revenue motion — 100 leads per niche, 3 niches, 90-day test — then scales into the top-scoring expansion niches.

**The single thesis:** Procurement short-lists are built before RFPs are published. We're the only firm that can prove it with public data, in writing, before a client signs anything.

---

## 1. GTM Strategy Overview

### Positioning Statement

**For the prospect:** "We get you on the short-list before the RFP drops."

**Full positioning (internal/website):** ContractMotion monitors FERC filings, USASpending.gov, SAM.gov, interconnection queues, earnings transcripts, and congressional investment activity to identify active infrastructure contract cycles 6–18 months before public procurement opens. We then get our clients pre-qualified, digitally positioned, and relationship-mapped before their competitors know the project exists.

**What makes this defensible:** The signal sources are public. The synthesis is proprietary. The timing advantage is structural — you cannot replicate a 6-month head start by working harder in month 7.

### What "Done" Looks Like — 90 Days

| Milestone | Target | Success Metric |
|-----------|--------|----------------|
| Sending infrastructure live | Day 21 | 3 sending domains purchased, warmed, active in Smartlead |
| Clay tables built | Day 14 | 3 tables, 100 leads each, signal-enriched |
| Smartlead campaigns active | Day 21 | 3 separate campaigns, niche-specific sequences |
| Outreach volume | Day 90 | 300 total leads contacted (100/niche) |
| Reply rate | Day 90 | ≥8% across all niches |
| Positive/interested responses | Day 90 | ≥15 positive replies |
| Discovery calls booked | Day 90 | ≥8 calls |
| Deals closed | Day 90 | 1–2 clients (target: 1 guaranteed) |
| ContractMotion.com live | Day 30 | 5 pages live on Framer |
| LinkedIn content | Day 90 | 24+ posts published (3/week) |

### Key Metrics to Track Weekly

| Metric | Target | Source |
|--------|--------|--------|
| Leads enrolled/week | 30–50 | Smartlead campaign dashboard |
| Email open rate | ≥45% | Smartlead analytics |
| Reply rate | ≥8% | Smartlead analytics |
| Positive reply rate | ≥2% | Smartlead (classified manually) |
| Calls booked | 2–3/week at steady state | Calendar |
| LinkedIn impressions | 5K+/week | LinkedIn Creator Analytics |
| ContractMotion inbound | 1+/month | Website form / GTM |
| Deals in pipeline | Running count | Airtable `deals` table |

---

## 2. Phase 1: Test Launch (Days 1–90)

### Infrastructure

#### Sending Domain Setup

Do NOT cold email from ContractMotion.com. It's the brand domain and must stay clean.

Purchase 3–5 sending domains that vary the brand/entity slightly to distribute reputation risk:

| Domain | Use | Niche Assignment |
|--------|-----|-----------------|
| contractmotion.co | Primary sending #1 | Substation EPC |
| getcontractmotion.com | Primary sending #2 | Solar EPC Utility-Scale |
| contractmotionhq.com | Primary sending #3 | EV Charging |
| signalmotion.io | Backup/reserve | Overflow / LinkedIn follow-up |
| gridcontractintel.com | Backup/reserve | Future expansion niches |

**DNS Configuration (each domain):**
- SPF record: `v=spf1 include:spf.smtp.mailercloud.com ~all` (or Smartlead equivalent)
- DKIM: Generate in Smartlead → add as TXT record at registrar
- DMARC: `v=DMARC1; p=quarantine; rua=mailto:admin@contractmotion.com`
- MX records: Point to Google Workspace or Smartlead mail server
- Registrar recommendation: Namecheap or Cloudflare (Cloudflare preferred — already used for tunnel infrastructure)

**Mailbox setup per domain:**
- Create 2 mailboxes per domain: `ethan@` and `info@` (use info@ for backup)
- Primary sender name: "Ethan | ContractMotion" or "Ethan Atchley"
- Connect all to Smartlead as separate sender accounts
- Rotate sending across mailboxes per campaign to distribute load

#### Warmup Timeline and Milestones

| Week | Volume/Day | Action |
|------|-----------|--------|
| Week 1 | 2 emails/day | Auto-warmup enabled (Smartlead warmup pool). No real outreach. |
| Week 2 | 5 emails/day | Continue warmup. Build Clay tables. |
| Week 3 | 10 emails/day | Continue warmup. Final list QA. |
| Day 21 | 20–30 emails/day | Launch Campaigns. Start with 20/day/mailbox. |
| Week 5–6 | 40 emails/day | Scale to 40/day/mailbox if open rates ≥40% |
| Week 7–8 | 60 emails/day | Full throttle if reputation clean |
| Week 9–12 | 60–80 emails/day | Steady state. Monitor spam placement weekly via GlockApps. |

**Warmup rules:**
- Never exceed 50% increase in daily volume week-over-week
- If spam placement exceeds 5% on GlockApps test: pause, investigate, reduce volume
- Set Smartlead: reply to warmup emails ON, unsubscribe warmup replies ON
- Check Google Postmaster Tools weekly (set up immediately after DNS)

#### Smartlead Campaign Structure

Three separate campaigns, one per niche. Never mix niches in a single campaign.

| Campaign | Smartlead ID | Niche | Sending Domain | Sequence |
|----------|-------------|-------|---------------|---------|
| ECAS-SUB-001 | (create) | Substation EPC | contractmotion.co | 3-email, Day 0/4/9 |
| ECAS-SOL-001 | (create) | Solar EPC Utility-Scale | getcontractmotion.com | 3-email, Day 0/4/9 |
| ECAS-EVC-001 | (create) | EV Charging Installers | contractmotionhq.com | 3-email, Day 0/4/9 |

**Smartlead settings for all campaigns:**
- Send window: Monday–Thursday, 8am–4pm local time (prospect timezone)
- Daily send cap: 30/mailbox to start (scale after Week 4)
- Stop on reply: YES
- Stop on click: NO (don't stop — they're interested but haven't replied)
- Unsubscribe tracking: YES
- Track opens: YES

---

### Clay Table Architecture

#### Niche A: Substation EPC

**ICP Filter Criteria**

| Filter | Value |
|--------|-------|
| NAICS Codes | 237130 (Power and Communication Line Construction), 238210 (Electrical Contractors) |
| Revenue Range | $20M–$300M (proxy: 50–500 employees via Apollo/Clay) |
| Geography | TX, VA, NC, GA, FL, MD, PA, OH, IN, IL — high FERC activity states |
| Employee Count | 50–500 |
| Keywords in Company Name/Description | "substation," "transmission," "high voltage," "EPC," "electrical contractor," "T&D" |
| Exclude | Pure residential electrical, utilities themselves, engineering-only firms with no field crews |

**Signal Sources**

| Source | URL / Feed | What to Look For |
|--------|-----------|-----------------|
| FERC eLibrary | elibrary.ferc.gov/idmws/search/fercadvsearch.asp | New interconnection requests, transmission line applications, substation permits |
| PJM Interconnection Queue | pjm.com/planning/interconnection-projects | New generator interconnection requests — each one requires substation work |
| MISO Queue | misoenergy.org/planning/generator-interconnection | Same — MISO territory queue additions |
| USASpending.gov | usaspending.gov (award search: NAICS 237130, 238210) | Contract awards to competitors = signal that utility is actively procuring |
| SAM.gov | sam.gov (active opportunities + contract awards) | Pre-solicitation notices, sources sought — these are pre-RFP |
| State Utility Commission Filings | State PUCs (e.g., TX PUC, VA SCC) | Rate case filings with capital expenditure plans = future project signals |
| DOE Grid Deployment Office | energy.gov/gdo | Infrastructure grants, loan guarantees to utilities — budget unlock |
| FERC Form 715 | Annual transmission planning reports from utilities | Multi-year capital plans — 3–5 year project pipeline |

**Clay Table Column Architecture**

```
Column 1:  Company Name (from Apollo org search)
Column 2:  Website
Column 3:  LinkedIn URL (company)
Column 4:  Revenue Estimate (Apollo enrichment)
Column 5:  Employee Count (Apollo)
Column 6:  NAICS Code (Apollo)
Column 7:  HQ State
Column 8:  ICP Score (Clay formula: NAICS match + revenue in range + geo match → 0–10)
Column 9:  [GATE: ICP Score ≥ 7] — only proceed if TRUE
Column 10: Signal Source (which database triggered inclusion)
Column 11: Signal Type (FERC filing / SAM.gov award / PJM queue / state PUC)
Column 12: Signal Date
Column 13: Signal Detail (project name, filing number, award amount)
Column 14: Signal Geography (state/region of the contract trigger)
Column 15: Primary Contact — Name (Apollo people search: title filter below)
Column 16: Primary Contact — Title
Column 17: Primary Contact — LinkedIn URL
Column 18: Email Waterfall #1 (Apollo reveal)
Column 19: Email Waterfall #2 (Hunter.io fallback)
Column 20: Email Waterfall #3 (Prospeo fallback)
Column 21: Email Waterfall #4 (FullEnrich — already in Doppler)
Column 22: Best Email (first non-null from waterfall)
Column 23: Email Confidence Score
Column 24: [GATE: Email Confidence ≥ 70%] — only proceed if TRUE
Column 25: AI Personalization — Recent Company Activity (Claygent: scrape LinkedIn for recent posts/project news)
Column 26: AI Personalization — Opening Line (Claude Haiku: generate signal-specific opener)
Column 27: Outreach Status (pending / ready / do_not_contact)
Column 28: Export to Smartlead (webhook trigger → Smartlead ECAS-SUB-001)
```

**Title Filter for Contact Search:**
- VP Business Development, VP BD, Director of Business Development
- VP Operations, COO
- CEO, President, Owner
- Director of Estimating, Chief Estimator
- VP Preconstruction

**Sample Personalized Opening Line — Substation EPC:**

> "saw the FERC eLibrary filing for the 230kV switching station in [County, State] — that's a $12M+ scope and the interconnection queue shows pre-solicitation activity within the next 8 months. [Company] has the credentials to be on that shortlist, and most substation EPCs in your territory won't know this project exists for another 6 months."

---

#### Niche B: Solar EPC (Utility-Scale)

**ICP Filter Criteria**

| Filter | Value |
|--------|-------|
| NAICS Codes | 238210 (Electrical Contractors), 237990 (Other Heavy Construction), 221114 (Solar Electric Power) |
| Revenue Range | $20M–$300M |
| Geography | TX, CA, FL, AZ, NC, NV, GA — highest utility-scale solar activity states |
| Employee Count | 50–500 |
| Keywords | "solar EPC," "utility-scale solar," "MW AC," "BESS," "PV installation," "solar developer-contractor" |
| Exclude | Residential solar, rooftop solar companies, pure developers with no field capability, panel manufacturers |

**Signal Sources**

| Source | URL / Feed | What to Look For |
|--------|-----------|-----------------|
| CAISO Queue | caiso.com/planning/interconnectionandfacilities | New large-scale solar interconnection applications |
| MISO/PJM/SPP Queues | Respective ISOs | Solar interconnection application filings |
| DOE EERE Grants | energy.gov/eere | IRA-funded solar grants to utilities/developers |
| DOE Loan Programs Office | energy.gov/lpo | Loan conditional commitments = large project confirmed |
| USASpending.gov | NAICS 238210 + "solar" keyword | Contract awards to competitors — competitor wins signal active buyer |
| SAM.gov Pre-Solicitations | "solar" + "utility" + "construction" | Sources Sought notices = 3–6 months before RFP |
| State Energy Office Announcements | CA CEC, TX PUC, FL PSC, NC NCUC | State utility IRP filings with renewable procurement targets |
| PPA Announcement Press Releases | pv-tech.org, Canary Media, PV Magazine | Signed PPAs = imminent procurement for EPC services |
| Earnings Transcripts (public utilities) | Seeking Alpha, The Motley Fool | Utilities announce "we're adding 500MW by 2027" — EPC procurement follows |

**Clay Table Column Architecture**

```
Column 1:  Company Name
Column 2:  Website
Column 3:  LinkedIn URL (company)
Column 4:  Revenue Estimate
Column 5:  Employee Count
Column 6:  NAICS Code
Column 7:  HQ State
Column 8:  Project States (where they operate — scrape from website/LinkedIn)
Column 9:  ICP Score
Column 10: [GATE: ICP Score ≥ 7]
Column 11: Signal Source
Column 12: Signal Type (PPA announcement / ISO queue / DOE grant / SAM.gov pre-sol)
Column 13: Signal Date
Column 14: Signal Detail (project MW, developer name, utility offtaker)
Column 15: Signal State/ISO Region
Column 16: Interconnection Queue Position # (if available)
Column 17: Estimated MW Capacity
Column 18: Primary Contact — Name
Column 19: Primary Contact — Title
Column 20: Primary Contact — LinkedIn URL
Column 21: Email Waterfall #1–4 (same cascade as Niche A)
Column 22: Best Email
Column 23: Email Confidence Score
Column 24: [GATE: Email Confidence ≥ 70%]
Column 25: AI Personalization — Recent Project/Milestone (Claygent: LinkedIn/website scrape)
Column 26: AI Personalization — Opening Line (Claude Haiku: ISO-specific, MW-specific)
Column 27: Outreach Status
Column 28: Export to Smartlead → ECAS-SOL-001
```

**Sample Personalized Opening Line — Solar EPC:**

> "the [Utility Name] PPA for [X]MW in [State] just signed — that's a confirmed EPC procurement cycle opening in the next 4–6 months. the CAISO/MISO interconnection queue shows [Company]'s region has 3 additional utility-scale projects in the same stage. most of your competitors won't be positioned for pre-qualification until the RFP drops."

---

#### Niche C: EV Charging Station Installers (Commercial/Fleet)

**ICP Filter Criteria**

| Filter | Value |
|--------|-------|
| NAICS Codes | 238210 (Electrical Contractors), 811121 (Automotive Body/Paint — proxy for EVSE), 237310 (Highway/Street Construction — proxy for NEVI corridor) |
| Revenue Range | $5M–$150M (smaller than Substation/Solar but growing fast) |
| Geography | All 50 states but prioritize: TX, CA, FL, NY, WA, CO — highest NEVI allocation states |
| Employee Count | 20–300 |
| Keywords | "EV charging," "EVSE installation," "Level 2," "DC fast charge," "DCFC," "fleet electrification," "NEVI" |
| Exclude | EVSE manufacturers (ChargePoint, Blink), utilities doing own installation, residential EV installers under $5M |

**Signal Sources**

| Source | URL / Feed | What to Look For |
|--------|-----------|-----------------|
| FHWA NEVI Program | highways.dot.gov/electrification/nevi | State NEVI plans and RFP issuances — each state runs its own procurement |
| SAM.gov EV Awards | NAICS 238210 + "electric vehicle" + "charging" | Federal agency EV charging awards (GSA, DOD, USPS fleet) |
| DOE EVSE Grants | energy.gov/eere/vehicles | MDHD charging grants, community charging grants |
| State DOT Announcements | Each state DOT (TX DOT, Caltrans, FDOT) | NEVI corridor designation = imminent installer RFP |
| GSA Leasing Bulletins | gsa.gov | Federal building EVSE requirements (executive order mandated) |
| BIL/IIJA Federal Register | federalregister.gov | EV infrastructure program rule changes — new funding tranches |
| Municipal Fleet Procurement | City/county purchasing portals | Fleet electrification RFPs — cities bidding EVSE installation |
| Amazon/Walmart/Real Estate Press | Business press | Large fleet/real estate EVSE announcements = installer RFP follow-on |

**Clay Table Column Architecture**

```
Column 1:  Company Name
Column 2:  Website
Column 3:  LinkedIn URL (company)
Column 4:  Revenue Estimate
Column 5:  Employee Count
Column 6:  HQ State
Column 7:  States of Operation (Clay scrape from website)
Column 8:  Charger Types Installed (L2 / DCFC / Fleet — from website scrape)
Column 9:  Primary Market (Commercial / Municipal / Fleet / Highway Corridor)
Column 10: ICP Score
Column 11: [GATE: ICP Score ≥ 6] — lower threshold; niche has more variability
Column 12: Signal Source
Column 13: Signal Type (NEVI state plan / SAM.gov award / DOE grant / municipal RFP)
Column 14: Signal Date
Column 15: Signal Detail (state, funding amount, program name, award winner if competitor)
Column 16: Funding Program (NEVI / MDHD / CFI / FTA)
Column 17: Primary Contact — Name
Column 18: Primary Contact — Title
Column 19: Primary Contact — LinkedIn URL
Column 20: Email Waterfall #1–4
Column 21: Best Email
Column 22: Email Confidence Score
Column 23: [GATE: Email Confidence ≥ 65%]
Column 24: AI Personalization — Specific Installation/Contract Win (Claygent: scrape recent news)
Column 25: AI Personalization — Opening Line (Claude Haiku: NEVI/state-specific, program-specific)
Column 26: Outreach Status
Column 27: Export to Smartlead → ECAS-EVC-001
```

**Sample Personalized Opening Line — EV Charging:**

> "[State] just released its NEVI Corridor RFP for Phase 2 — $47M in federal funds, applications open in 6 weeks. we track which installers are pre-positioned with the state DOT before those RFPs publish. [Company]'s footprint in [State] makes you a natural fit, but DOT short-lists are built before the public application window opens."

---

### Sequence Structure (All 3 Niches)

The sequences are 3 emails at Day 0 / Day 4 / Day 9. No 4th email — the current 4-email sequence in `smartlead-ecas-sequence.md` uses marketing agency positioning that needs to be replaced with direct ECAS positioning.

#### Substation EPC Sequence

**Email 1 — Day 0**
Subject: `[Company] — 3 substation projects in your region`

> [First Name],
>
> We track FERC eLibrary filings, state utility commission dockets, and USASpending.gov contract awards for substation and transmission work — specifically to identify active procurement cycles before they go to public RFP.
>
> [Company] showed up in our scan this week. There are 3 active substation projects within your operating geography that are in the pre-solicitation phase right now — one of which is a [X]kV switching station sourced from a FERC filing dated [Month].
>
> The EPCs on the short-list for those projects are being identified by utilities right now, before the RFP exists.
>
> Worth sending over the contract signal report? It's a one-pager — no pitch, just the data on what we're seeing in your region.
>
> [Name]

---

**Email 2 — Day 4**
Subject: `re: substation pipeline in [Region]`

> [First Name],
>
> Quick follow-up.
>
> The pre-solicitation activity we flagged in your region has moved — one of the three projects is now listed as a Sources Sought on SAM.gov. That's typically 60–90 days before a formal solicitation.
>
> The contractors who get a phone call from utilities at this stage are the ones already on the approved vendor list. The ones who apply from the public RFP compete against 15–20 firms on price.
>
> The signal report for your territory is ready whenever you want it — takes 2 minutes to review.
>
> [Name]

---

**Email 3 — Day 9**
Subject: `last note`

> [First Name],
>
> Last one from me.
>
> The USASpending.gov contract awards for substation work in [State] this year totaled $[X]M. Across those awards, the top 3 winning contractors had one thing in common: pre-existing relationships with the utility's procurement team before the solicitation opened.
>
> That relationship isn't built by responding to RFPs. It's built 12 months before one exists.
>
> If you want to see where your firm stands vs. the contractors winning those awards in your region — reply and I'll send the breakdown.
>
> [Name]

---

#### Solar EPC Sequence

**Email 1 — Day 0**
Subject: `[X] utility-scale projects in your ISO region`

> [First Name],
>
> We monitor the CAISO/MISO/PJM interconnection queues, DOE IRA funding announcements, and signed PPA disclosures to track utility-scale solar procurement cycles before they go to public RFP.
>
> [Company] is operating in a region with significant queue activity right now — there are [X] large-scale solar projects that have cleared interconnection study phase and are moving toward EPC procurement. One of them is a [X]MW project with a confirmed offtake agreement.
>
> EPC pre-qualification for projects at this stage happens before a public RFP is published. The developers are identifying contractors now.
>
> Want me to send the pipeline report for your ISO region? One page, no pitch, just the project data.
>
> [Name]

---

**Email 2 — Day 4**
Subject: `re: solar pipeline — [ISO Region]`

> [First Name],
>
> Following up on my note.
>
> Pulled a quick update: the [X]MW project in [State/Region] I flagged has added a construction manager to the developer's team — that's typically 60–90 days before EPC RFP publication.
>
> The developers we track move fast between that hiring signal and the formal solicitation. The EPCs who are already known to the CM get a call before the posting goes public.
>
> The pipeline report is ready whenever you want it.
>
> [Name]

---

**Email 3 — Day 9**
Subject: `moving on — one thing to know`

> [First Name],
>
> Last note.
>
> The IRA has committed $[X]B to utility-scale renewable interconnection in your region over the next 5 years. That's been translated into [X] specific projects in the interconnection queue we track — projects with confirmed offtake, cleared studies, and active developer teams.
>
> The EPCs winning those contracts are being pre-qualified now, not when the RFPs drop.
>
> If you want to know which projects fit [Company]'s capabilities and where you stand in the pre-qualification window — reply. I'll send the breakdown.
>
> [Name]

---

#### EV Charging Sequence

**Email 1 — Day 0**
Subject: `NEVI funding in [State] — pre-RFP window`

> [First Name],
>
> We track NEVI formula program RFP timelines, DOE EVSE grant awards, and state DOT procurement cycles to identify EV charging installation contracts before they go to public bidding.
>
> [State] has [X] active NEVI corridor segments moving toward RFP phase right now — one of them in a geography where [Company] has installed capacity. The state DOT's approved installer list for that corridor is being built in the next 30–45 days.
>
> Contractors on that list get invited to bid. Everyone else competes from the public RFP, which typically goes to the lowest compliant bid.
>
> Want me to send the NEVI pipeline report for [State]? Covers the active funding windows and which corridors are pre-solicitation right now.
>
> [Name]

---

**Email 2 — Day 4**
Subject: `re: [State] NEVI pipeline`

> [First Name],
>
> Quick follow-up.
>
> The [State] DOT released an updated NEVI implementation plan this week — Phase 2 corridors now include [Route], which runs through [Company]'s operating area. Phase 2 RFPs are expected to publish in [X] weeks based on the Phase 1 procurement timeline.
>
> Getting on the pre-approval list at this point is still possible. It closes when the RFP drops.
>
> The pipeline report for [State] is ready — 2 minutes to review.
>
> [Name]

---

**Email 3 — Day 9**
Subject: `closing the loop on NEVI`

> [First Name],
>
> Last one.
>
> $5B of NEVI funding is in motion across all 50 states. The contractors winning the large corridor contracts — $2M–$15M per corridor — are on pre-approved installer lists that were built before the RFPs published.
>
> We know which states have active pre-approval windows right now because we track the DOT procurement timelines, not just the public RFP feeds.
>
> If [Company] wants to see where the open windows are in your states — reply and I'll send it.
>
> [Name]

---

## 3. ECAS Niche Scoring Model

This rubric scores niches on their fit for the ECAS signal-driven contract intelligence system — NOT on general business attractiveness.

### Rubric Definition

| Dimension | What It Measures | Weight |
|-----------|-----------------|--------|
| Signal Density | Number and reliability of public data sources that predict contract timing | 25% |
| Budget Predictability | Can we identify when money unlocks, from what source, and for how long? | 25% |
| RFP Volume | Contracts awarded per year in this niche — pipeline depth | 20% |
| ICP Accessibility | Can we reach decision-makers via cold email / LinkedIn at mid-tier firms? | 15% |
| Market Size | How many mid-tier ($20M–$300M) companies exist? | 15% |

### Scoring Scale

- **9–10:** Exceptional. Lead niche. Build immediately.
- **7–8:** Strong. High confidence. Queue after Phase 1.
- **5–6:** Moderate. Signals exist but incomplete or lagging.
- **3–4:** Weak fit. Signals are sparse, private, or trailing.
- **1–2:** Not viable for ECAS model.

---

## 4. 10 Recommended New Niches for ECAS

### Scoring Table

| Niche | Signal Density | Budget Predictability | RFP Volume | ICP Accessibility | Market Size | Composite |
|-------|---------------|----------------------|------------|-------------------|-------------|-----------|
| Transmission Line Contractors | 9.5 | 9.5 | 8.5 | 7.0 | 7.5 | **8.7** |
| Battery Storage EPC | 9.0 | 9.5 | 8.0 | 8.0 | 7.0 | **8.5** |
| Broadband/Fiber Infrastructure | 8.5 | 9.0 | 9.0 | 8.5 | 8.0 | **8.7** |
| Water/Wastewater Treatment Contractors | 8.5 | 8.5 | 9.5 | 7.5 | 8.0 | **8.5** |
| Environmental Remediation Contractors | 8.0 | 8.5 | 8.5 | 7.5 | 7.0 | **8.0** |
| Highway/Road Construction | 7.5 | 8.5 | 9.5 | 7.0 | 8.5 | **8.2** |
| Wind Energy EPC | 8.5 | 8.5 | 7.0 | 8.0 | 6.0 | **7.7** |
| Defense Facility Contractors (MILCON) | 9.0 | 9.5 | 8.5 | 6.0 | 6.5 | **7.9** |
| Airport Infrastructure Contractors | 8.0 | 8.0 | 7.5 | 7.0 | 6.5 | **7.5** |
| Nuclear Plant Services | 8.5 | 9.0 | 5.5 | 5.5 | 4.5 | **6.8** |
| Pipeline Construction/Rehabilitation | 7.0 | 7.5 | 7.0 | 7.5 | 6.5 | **7.1** |
| Port/Maritime Infrastructure | 7.0 | 8.0 | 6.5 | 6.5 | 5.5 | **6.7** |
| Federal Building/Facility Construction | 7.5 | 8.0 | 9.0 | 7.5 | 8.5 | **8.0** |

---

### Top 10 Ranked with Full Rationale

---

**#1 — Transmission Line Contractors (High-Voltage, FERC-Regulated)**
Composite: 8.7

Signal sources are exceptional. FERC dockets publicly log every transmission expansion project from pre-application through construction permit. NERC reliability standards force utilities to file 10-year expansion plans. State PUC rate cases include capital expenditure schedules for transmission. The "budget unlock" event is a FERC order or state commission approval — publicly logged, date-stamped, searchable.

- Signal sources: FERC eLibrary, state PUC filings, NERC ERO portal, DOE Grid Deployment Office, IIJA transmission grants
- Budget unlock trigger: FERC Order 1000 compliance filing + state commission rate case approval
- ICP: 50–400 employee transmission line contractors doing $30M–$250M revenue
- NAICS: 237130
- Key titles: VP BD, Director of Preconstruction, VP Operations, Owner
- Pre-RFP window: 9–18 months (utility capital plan to procurement)
- Why now: $2.5B in IIJA transmission funding is being deployed; FERC Order 1920 requires regional transmission planning — the filing volume has tripled since 2022

---

**#2 — Broadband/Fiber Infrastructure Contractors (BEAD Act)**
Composite: 8.7

The BEAD Act ($42.45B) has the most public-facing procurement infrastructure of any infrastructure program in modern history. Every state has a published BEAD implementation plan with deployment timelines. NTIA's program portal tracks every state's allocation, spending schedule, and subgrantee award. The "budget unlock" event is a state's BEAD Initial Proposal approval by NTIA — after that approval, state RFPs for construction contractors follow in 60–120 days.

- Signal sources: NTIA BEAD portal (internetforall.gov), state broadband office announcements, FCC BEAD eligibility maps, SAM.gov BEAD awards
- Budget unlock trigger: NTIA approves state Initial Proposal → state issues construction contractor RFP
- ICP: Regional fiber/broadband contractors doing $20M–$200M revenue; often telecom construction firms
- NAICS: 237130, 517311 (Wired Telecommunications Carriers)
- Key titles: VP BD, Director of Operations, CEO, Owner
- Pre-RFP window: 60–120 days (NTIA approval to state RFP)
- Why now: $42.45B is being distributed NOW. Most state RFPs will publish 2026–2027. The pre-RFP positioning window is open today.

---

**#3 — Battery Storage EPC (Utility-Scale)**
Composite: 8.5

Battery storage is following the same interconnection queue signal model as solar. IRA Section 45X manufacturing credits + ITC incentives have made BESS economically mandatory for utilities. ISO interconnection queues now include standalone storage projects. DOE Loan Programs Office conditional commitments are publicly announced — each one represents a $100M+ project moving toward EPC procurement.

- Signal sources: ISO interconnection queues (BESS applications), DOE LPO conditional commitments, SAM.gov storage awards, IRA tax credit program filings, PPA disclosures with storage components
- Budget unlock trigger: DOE LPO conditional commitment OR ISO interconnection study completion
- ICP: Solar EPCs with storage capabilities, standalone storage EPCs, $20M–$300M revenue
- NAICS: 238210, 237990
- Key titles: VP BD, COO, CEO, Director of Project Development
- Pre-RFP window: 4–12 months (ISO queue position to EPC RFP)
- Why now: BESS procurement volume tripled 2024–2025 due to IRA. Standalone storage is now its own EPC procurement category.

---

**#4 — Water/Wastewater Treatment Contractors**
Composite: 8.5

Water infrastructure has the highest RFP volume of any infrastructure niche (thousands of municipal procurement cycles annually) and the most predictable budget signals. EPA SRF (State Revolving Fund) allocations are published annually by state. IIJA provided $55B for water infrastructure. Every municipal water authority files an annual capital improvement plan (CIP) — these are public records that show exactly which projects are funded, in what year, and for how much.

- Signal sources: EPA SRF allocation tables, municipal CIP filings, SAM.gov water infrastructure awards, state EPA grant announcements, FEMA hazard mitigation grants (water resilience)
- Budget unlock trigger: State SRF loan approval OR municipal bond authorization
- ICP: Regional water/wastewater construction contractors doing $20M–$300M revenue
- NAICS: 237110 (Water and Sewer Line Construction), 237990
- Key titles: VP Business Development, Director of Estimating, President, VP Operations
- Pre-RFP window: 3–9 months (SRF loan approval to RFP publication)
- Why now: $55B IIJA water money is actively being awarded. SRF pipeline is at all-time high volume.

---

**#5 — Highway/Road Construction Contractors (IIJA)**
Composite: 8.2

IIJA allocated $110B for roads and bridges. State DOT STIP (Statewide Transportation Improvement Program) documents are public records that list every planned project with funding year, project type, and estimated cost — typically 4 years forward. The "budget unlock" is a FHWA obligation of funds to a state project. That event is searchable on FHWA's FMIS database and precedes state DOT RFP issuance by 3–12 months.

- Signal sources: State DOT STIP (all 50 states public), FHWA FMIS database (federal fund obligations), USASpending.gov highway awards, state DOT procurement portals
- Budget unlock trigger: FHWA obligates funds to project in FMIS → state DOT issues RFP
- ICP: Regional highway contractors doing $30M–$300M revenue; heavy civil firms
- NAICS: 237310 (Highway, Street, and Bridge Construction)
- Key titles: VP Business Development, Director of Estimating, CEO/Owner, VP Preconstruction
- Pre-RFP window: 3–12 months (FHWA obligation to state RFP)
- Why now: IIJA money peaked in 2025–2026 obligation cycle. State DOTs are issuing the most RFPs in a decade.

---

**#6 — Environmental Remediation Contractors (EPA Superfund / DoD)**
Composite: 8.0

Environmental remediation has two of the most reliable signal systems in government contracting. EPA Superfund National Priorities List sites have publicly tracked remedial investigation/feasibility study (RI/FS) phases — completion of RI/FS directly precedes remediation design and construction RFPs. DoD FUDS (Formerly Used Defense Sites) cleanup is tracked on USACE's public FUDS database. Both are date-stamped and searchable.

- Signal sources: EPA CERCLIS/ACRES database, EPA NPL site status tracker, USACE FUDS database, DoD DERP program announcements, USASpending.gov remediation awards
- Budget unlock trigger: EPA ROD (Record of Decision) issuance OR DoD FUDS Phase II approval
- ICP: Environmental remediation EPCs doing $20M–$200M revenue
- NAICS: 562910 (Remediation Services), 237990
- Key titles: VP Business Development, Director of Projects, CEO, Principal Scientist/PM
- Pre-RFP window: 6–18 months (ROD issuance to remediation construction RFP)
- Why now: Bipartisan Infrastructure Law added $3.5B to Superfund. DoD PFAS cleanup is a new $2B+ annual program.

---

**#7 — Federal Building/Facility Construction (GSA)**
Composite: 8.0

GSA's Capital Investment and Leasing Program (CILP) is submitted to Congress annually and publicly available. Every federal building project that receives a congressional appropriation has a predictable procurement timeline: appropriation → design authorization → construction RFP, typically 12–24 months. PBS (Public Buildings Service) pre-solicitation notices appear on SAM.gov 90–180 days before formal RFP.

- Signal sources: GSA CILP (annual congressional submission), SAM.gov GSA pre-solicitations, FedBizOpps GSA notices, Congressional appropriations acts (defense.gov + congress.gov), DHS/VA/DOJ capital improvement plans
- Budget unlock trigger: Congressional appropriation in NDAA or omnibus → GSA issues design-build solicitation
- ICP: Federal construction contractors doing $30M–$300M revenue; often hold GSA schedule or IDIQ contracts
- NAICS: 236220 (Commercial Building Construction), 237990
- Key titles: VP Federal Sector, VP Business Development, Director of Estimating, President
- Pre-RFP window: 6–18 months (appropriation to design-build RFP)

---

**#8 — Defense Facility Contractors (MILCON/DoD Construction)**
Composite: 7.9

MILCON (Military Construction) is one of the most signal-rich niches in government contracting. The DoD submits a MILCON budget request to Congress each February — this is a line-item list of every planned military construction project with cost, location, and scope. Congressional approval (NDAA) precedes USACE/NAVFAC RFP issuance by 9–18 months. The NAVFAC and USACE pre-solicitation databases on SAM.gov are comprehensive.

- Signal sources: DoD MILCON budget request (submitted annually to Congress, publicly searchable), USACE/NAVFAC SAM.gov pre-solicitations, NDAA conference report (final appropriations), Congressional Budget Justification Books
- Budget unlock trigger: NDAA signed into law with project-specific MILCON line item → USACE/NAVFAC issues pre-solicitation
- ICP: Defense construction firms doing $30M–$300M revenue; many hold USACE/NAVFAC IDIQ vehicles
- NAICS: 236220, 237990, 237310
- Key titles: VP Federal Business Development, VP Contracts, VP Operations, CEO
- Pre-RFP window: 9–18 months (NDAA authorization to NAVFAC/USACE RFP)
- Caveat: Decision-maker accessibility is lower (government-contractor relationships are more formal). ICP score penalized accordingly.

---

**#9 — Airport Infrastructure Contractors (FAA AIP Grants)**
Composite: 7.5

FAA Airport Improvement Program (AIP) grants are publicly tracked through the FAA's ACIP (Airports Capital Improvement Plan) database. Each airport files a 5-year CIP, and FAA publishes annual grant awards. The pre-RFP signal chain: FAA publishes ACIP priority list → airport authority issues design authorization → construction RFP follows 6–18 months later. IIJA added $15B to AIP.

- Signal sources: FAA ACIP database, FAA AIP grant awards (faa.gov/airports/aip), SAM.gov airport construction notices, airport authority capital plans (public), IIJA aviation program announcements
- Budget unlock trigger: FAA AIP grant award to airport authority → airport issues design-build or construction manager at-risk RFP
- ICP: Airport construction specialists doing $20M–$250M revenue; also general heavy civil with airport experience
- NAICS: 237310, 236220
- Key titles: VP Business Development, Director of Estimating, VP Aviation, CEO
- Pre-RFP window: 6–18 months (FAA grant award to construction RFP)

---

**#10 — Wind Energy EPC (Utility-Scale)**
Composite: 7.7

Utility-scale wind follows similar signal patterns to solar — ISO interconnection queues, PPA announcements, DOE grants. However, wind has a more concentrated geographic footprint (Great Plains, Midwest, offshore Northeast) and fewer active EPCs at the mid-tier level, reducing ICP market size. Offshore wind adds a separate signal layer (BOEM leases, state offshore wind solicitations). The niche earns a spot in Phase 3 given its signal density.

- Signal sources: MISO/SPP/PJM interconnection queues (wind applications), BOEM offshore wind lease database, DOE Wind Energy Technologies Office grants, PPA disclosures, state offshore wind solicitations (NY, NJ, MA, CT, MD, VA)
- Budget unlock trigger: PPA execution + interconnection study completion → developer issues EPC RFP
- ICP: Wind EPCs doing $30M–$300M revenue; often overlapping with solar EPC firms
- NAICS: 237990, 238210
- Key titles: VP Business Development, COO, VP Project Development, CEO
- Pre-RFP window: 6–15 months (PPA signing to EPC RFP)

---

## 5. Niche Sequencing Roadmap

### Phase 1: Test Launch (Months 1–3) — Current 3 Niches

| Niche | Composite | Why First |
|-------|-----------|-----------|
| Substation EPC | ~9.0 | Highest LTV. Signal infrastructure (FERC/SAM) already wired in ECAS engine. 60 leads already enrolled. |
| Solar EPC (Utility-Scale) | ~8.8 | IRA tailwinds. ISO queue signals active. Overlaps with Substation EPC signal sources — low marginal setup cost. |
| EV Charging Installers | ~8.5 | Fastest sales cycle. NEVI is time-sensitive (window is NOW). More reachable ICP on digital. |

**Goal:** 100 leads each, 8%+ reply rate, 8 calls, 1–2 closed deals by Day 90.

---

### Phase 2: Expansion (Months 4–6) — Add 3 Niches

| Niche | Composite | Why Now |
|-------|-----------|---------|
| Transmission Line Contractors | 8.7 | Directly adjacent to Substation EPC. Same signal sources (FERC, NERC). Share Clay infrastructure. Client profile is similar. |
| Broadband/Fiber Infrastructure | 8.7 | BEAD RFP window is open NOW — this is time-sensitive. State NTIA approvals are rolling through. Add immediately after Phase 1 proves the model. |
| Battery Storage EPC | 8.5 | Natural extension of Solar EPC niche. Same ICP, similar signal sources. Many Solar EPC clients also do BESS. Requires minimal new Clay build. |

**Goal:** 100 leads each in Months 4–6. By end of Month 6: 6 active niches, 600 total leads, 3–5 clients.

---

### Phase 3: Scale (Months 7–12) — Add 4 Niches

| Niche | Composite | Why Next |
|-------|-----------|---------|
| Water/Wastewater Treatment | 8.5 | Highest RFP volume of any niche. Municipal CIPs give 4-year forward visibility. Once ECAS proves its model across energy niches, water is the highest-volume expansion play. |
| Highway/Road Construction | 8.2 | Massive IIJA pipeline. State DOT STIP signals are the most standardized and accessible signal source of any niche. Clean data, high volume. |
| Environmental Remediation | 8.0 | EPA/DoD signal sources are unique to this niche. No overlap with energy ICPs — expands addressable market meaningfully. |
| Federal Building/Facility (GSA) | 8.0 | GSA CILP gives 18-month forward visibility. High contract values. Signals are well-documented in congressional records. |

**Goal:** 4 additional niches activated. By Month 12: 10 active niches, diversified across energy, infrastructure, federal, and environmental sectors.

---

### Why This Sequencing

1. **Proof of model before expansion:** Phase 1 tests all core infrastructure assumptions (signal sourcing, Clay enrichment, Smartlead sequences, sales motion) with the highest-confidence niches.
2. **Signal source leverage:** Phases 1 and 2 niches share signal infrastructure (FERC, ISO queues, DOE, SAM.gov). Marginal cost of adding Transmission and Battery Storage is low.
3. **Time-sensitive opportunities:** Broadband/BEAD is in Phase 2 even though it's not an energy niche — BEAD RFP windows are opening now and will close as states deploy funding.
4. **Market diversification:** Phase 3 deliberately adds non-energy niches (water, highway, federal, environmental) to protect against energy-specific headwinds and expand TAM.
5. **Sales cycle alignment:** Shorter-cycle niches (EV Charging, Broadband) generate early revenue while longer-cycle niches (Substation, Transmission) build toward higher-LTV client relationships.

---

## 6. ContractMotion.com Brand GTM

### Website Structure (Framer, 5 Pages)

**Page 1: Homepage**
- Hero: "We get you on the short-list before the RFP drops."
- Sub-headline: "ContractMotion monitors FERC filings, ISO queues, USASpending.gov, and SAM.gov to identify active infrastructure contract cycles 6–18 months before public procurement opens."
- Primary CTA: "Get Your Contract Signal Report" → lead capture form (company, state, niche)
- Social proof section: "We track signals in [X] niches across [Y] public databases"
- How It Works: 3 steps — Signal Detection → Pre-Qualification Positioning → Short-List Placement
- Niche logos/icons: Grid, Solar, EV, Broadband, Water (expand as niches are added)
- Footer: minimal. No pricing. No case studies until they exist.

**Page 2: How It Works**
- Detailed explanation of the signal-to-shortlist pipeline
- The 6–18 month window: diagram showing typical procurement timeline from budget authorization to RFP publication
- Signal sources listed explicitly: FERC eLibrary, PJM/MISO/CAISO, USASpending.gov, SAM.gov, DOE, state PUCs
- "Most contractors find out about a project when the RFP hits their inbox. Our clients find out 6–18 months before that." — prominent pullquote
- Secondary CTA: "Request a Signal Report for Your Territory"

**Page 3: Niches**
- Grid/Card layout — one card per active niche
- Each card: niche name, primary signal source, typical pre-RFP window, sample contract type
- Only show active niches (start with 3, add as phases launch)
- No pricing on this page

**Page 4: Contract Signal Report (Lead Magnet)**
- Dedicated landing page for the lead magnet
- Headline: "See 5 Active Infrastructure Contracts in Your Territory — Before the RFP Drops"
- What's in the report: project names (anonymized), signal source, procurement stage, timeline estimate, decision-maker function (anonymized)
- Form: Name, Company, State/Region, Niche (dropdown), Work Email
- After form submission: "Your report will be delivered within 24 hours" (then manually fulfill for now)
- This page is the primary LinkedIn ad destination

**Page 5: About / Contact**
- Who we are: one paragraph, no fluff
- Why we built ContractMotion: the signal gap that exists between budget authorization and RFP publication
- Contact: work email only (no form — keeps it human)
- LinkedIn link (Ethan's profile or company page)

---

### Lead Magnet Concept — "Contract Signal Report"

**Format:** PDF, 1–2 pages. Professional, data-forward. No marketing language.

**What it contains:**
1. 5 active infrastructure contracts in the prospect's territory, in pre-solicitation phase
2. For each project: signal source (FERC filing #, SAM.gov notice, ISO queue ID), procurement stage, project owner, estimated value range, and estimated months until RFP publication
3. One decision-maker function at the project owner (e.g., "Director of Engineering, [Utility Name]") — not full contact details, but enough to be credible
4. A one-paragraph note on the competitive landscape: "Here is what contractors in your niche are typically doing at this pre-RFP stage"

**Delivery:** Initially manual — run the ECAS engine for the prospect's state/niche and format the output. Scale with a templated Framer page + n8n automation once volume justifies it.

**Gating:** Work email required. No personal Gmail/Yahoo accepted (Clay can filter this on inbound form entries).

---

### LinkedIn Content Strategy

**Goal:** Build authority as the infrastructure contract intelligence voice. Not "marketing tips for contractors." Signal-specific, data-forward, credibility-building.

**Posting cadence:** 3 posts/week — Tuesday, Wednesday, Thursday (highest B2B engagement days)

**Content pillars:**

| Pillar | % of Content | Format | Example |
|--------|-------------|--------|---------|
| Signal Intelligence Drops | 35% | Data post with specific signal | "FERC eLibrary this week: 7 new substation applications filed in PJM territory. Here's what that means for EPC procurement timing..." |
| Pre-RFP Timing Education | 25% | Explainer/process post | "The 6-step journey from utility budget authorization to published RFP — and where most contractors enter too late." |
| Contract Award Analysis | 20% | Short analysis of a public award | "USASpending.gov: [Utility] awarded a $22M substation contract. The winning contractor was on their approved vendor list 14 months before this posting appeared." |
| Niche Market Intelligence | 15% | Data-forward market insight | "BEAD Act: 12 states have received NTIA approval as of March 2026. Here's which states are 60-90 days from construction RFP issuance." |
| Framework/System Posts | 5% | Process/system explainer | "How we built a real-time signal tracker across FERC, SAM.gov, ISO queues, and USASpending — and what it tells us that RFP alerts miss." |

**Voice:** Direct, data-backed, no hype. Write like a former procurement officer who knows exactly how the sausage is made. Avoid marketing language — use contractor language ("pre-qualification," "short-list," "approved vendor list," "procurement cycle," "RFP release date").

**LinkedIn profile:** Ethan Atchley → update headline to "Contract Intelligence for Infrastructure EPCs | ContractMotion" and feature the Signal Report lead magnet in the Featured section.

---

### Case Study Structure (Pre-Client)

Until real case studies exist, use this structure to build positioning credibility:

**Format:** "Signal Study" — not a case study. It's a retrospective analysis of a real contract award, using public data, showing what the pre-RFP signals looked like.

**Example Signal Study:**
> **"The Duke Energy $45M Substation Contract — What the Signals Said 11 Months Before the RFP"**
>
> In Q1 2024, Duke Energy filed 3 interconnection applications in the Carolinas service territory with FERC. In Q2 2024, their rate case filing with the NC Utilities Commission included a $180M capital expenditure line for substation upgrades. In Q3 2024, USASpending.gov recorded a $2.1M design engineering award to [Engineering Firm] for substation design services.
>
> The construction RFP published in Q1 2025. Award was $45M to [Contractor].
>
> **The contractors on the short-list when that RFP dropped were visible to Duke Energy's procurement team 11 months before the posting existed.**

This format requires no client. It uses public data to demonstrate the signal-to-RFP pattern retroactively. Run 3–5 of these for the website and LinkedIn. It proves the system works before you have any clients to reference.

---

## 7. Week 1 Action List

| Day | Task | Owner | Deadline | Notes |
|-----|------|-------|----------|-------|
| **Mon 3/11** | Purchase 3 sending domains (contractmotion.co, getcontractmotion.com, contractmotionhq.com) | Ethan | EOD | Use Cloudflare Registrar. All 3 on same account for centralized DNS. |
| **Mon 3/11** | Create Google Workspace accounts for sending domains (ethan@ on each) | Ethan | EOD | Use ENT Google Workspace admin or create new org. 2 mailboxes per domain. |
| **Mon 3/11** | Configure DNS for all 3 domains (SPF, DKIM, DMARC, MX) | Ethan | EOD | Use Cloudflare DNS. Set DMARC to p=none first, switch to p=quarantine after 2 weeks. |
| **Tue 3/12** | Connect all 6 mailboxes to Smartlead | Ethan | EOD | Enable warmup for all mailboxes. Set warmup volume to 2/day/mailbox to start. |
| **Tue 3/12** | Create 3 new Smartlead campaigns (ECAS-SUB-001, ECAS-SOL-001, ECAS-EVC-001) | Ethan | EOD | Replace current ECAS campaign 3005694 (wrong positioning — marketing agency language). |
| **Tue 3/12** | Load 3-email sequences (from this document, Section 2) into each Smartlead campaign | Ethan | EOD | One sequence per niche. Day 0/4/9 cadence. |
| **Wed 3/13** | Build Clay table — Substation EPC (all 28 columns per architecture in Section 2) | Ethan | EOD | Source first 100 companies from Apollo (NAICS 237130/238210, 50–500 employees, target states). |
| **Wed 3/13** | Build Clay table — Solar EPC (all 28 columns) | Ethan | EOD | Source from Apollo + PJM/MISO interconnection queue applicant lists. |
| **Thu 3/14** | Build Clay table — EV Charging Installers | Ethan | EOD | Source from Apollo + SAM.gov NEVI award winners (use as ICP signal). |
| **Thu 3/14** | Set up Google Postmaster Tools for all 3 sending domains | Ethan | EOD | Required for reputation monitoring. Takes 10 min per domain. |
| **Thu 3/14** | Set up GlockApps account — run initial spam placement test on all 3 domains | Ethan | EOD | Baseline deliverability before any real sends. |
| **Fri 3/15** | QA first 25 rows in each Clay table — verify ICP filters, signal data, email waterfall | Ethan | EOD | Check: ICP score gate is working, email confidence >70% gate is working, AI opener is specific (not generic). |
| **Fri 3/15** | Register ContractMotion.com on Framer — start homepage build | Ethan | EOD | 5 pages. Deploy by Day 30. Start with homepage + lead magnet page (most critical). |
| **Sat 3/16 (optional)** | Write 3 LinkedIn Signal Studies (retrospective analysis of real public contract awards) | Ethan | Weekend | Use USASpending.gov + FERC data to find a real award and trace the pre-RFP signals retroactively. |
| **Day 21 (4/1)** | Go/No-Go check: Are domains warm enough? Are Clay tables QA'd and ready? | Ethan | 4/1 | If warmup metrics clean (open rate >40% on warmup emails), launch all 3 campaigns. |
| **Day 21 (4/1)** | Launch ECAS-SUB-001 with first 25 leads | Ethan | 4/1 | Start with 25 leads, not 100. Watch deliverability for 72 hours before scaling. |

---

*Document last updated: 2026-03-10*
*Next review: 2026-04-01 (Day 21 — Go/No-Go checkpoint)*
