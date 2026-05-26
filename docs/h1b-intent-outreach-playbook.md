# The H-1B Intent Playbook: Catching EPCs the Moment They Fund Their Pipeline

**For:** ContractMotion outbound (mid-tier EPC contractors, $20M–$300M, 5 sectors)
**Signal source:** H-1B LCA disclosure data (h1bdata.info → DOL OFLC)
**Engine:** `signals/h1b_signal_engine.py`
**Positioning fit:** "We get you on the short-list before the RFP drops." This signal gets *us* in front of the EPC before *they* finish staffing the team that chases those RFPs.

---

## The Thesis in One Paragraph

Sponsoring an H-1B worker is expensive and slow: legal fees, DOL/USCIS filing fees, and a multi-month process, often $10K–$20K+ all-in before the person starts. No EPC spends that on a *whim* role. So when a mid-tier EPC files an H-1B Labor Condition Application for a **pipeline / revenue role** — Estimator, Preconstruction Manager, Business Development, Proposal Manager, Capture Manager — it is a hard-money vote that the firm is (1) funded, (2) deliberately investing in *winning more work*, and (3) scaling the exact function ContractMotion makes more effective. That filing is public, dated, and visible months before any RFP the new hire will eventually chase. It is a leading indicator of buying intent that no competitor is watching.

---

## Why This Signal Beats the Others

| Signal | What it tells you | Lag |
|--------|-------------------|-----|
| USASpending award | EPC already won federal work | Trailing — they already have the contract |
| SAM.gov registration | EPC registered to bid | Coincident |
| **H-1B pipeline-role LCA** | **EPC is staffing up to win *future* work** | **Leading — fires before the pursuit even starts** |
| Association membership | EPC operates in sector | None (static) |

The H-1B signal is the only one that catches the EPC *building the muscle*, not flexing it. A firm that just hired its third estimator in two years is about to bid more, on bigger jobs, in more places — and is acutely aware its win rate needs to keep up. That is the exact moment ContractMotion is most relevant.

---

## The Signal Logic

The engine scores employers on **two dimensions** (the wage figure is captured for context but not scored):

### 1. Role (gate + weight)
Only pipeline/revenue-investment roles count. These also act as a free EPC filter — almost no non-construction firm sponsors an H-1B "Estimator."

| Role keyword | Weight | Why it's a pursuit-investment signal |
|--------------|:---:|--------------------------------------|
| Chief Estimator | 4 | Senior cost-leadership hire — firm is bidding bigger |
| Preconstruction Manager | 4 | Owns the pursuit-to-award front end |
| Director of Business Development | 4 | Top-of-funnel growth leadership |
| Capture Manager | 4 | Explicit federal-pursuit role — they want govt work |
| Estimator | 3 | Core pipeline throughput |
| Business Development Manager | 3 | Active demand generation |
| Proposal Manager | 3 | They're submitting enough to need a specialist |
| Project Executive | 2 | Senior delivery + client growth |

### 2. Volume
Total qualifying filings by the employer. More filings = larger, more deliberate GTM investment.

### 3. Velocity
Distinct years with filings. **Sustained multi-year hiring is the strongest signal** — it separates a funded, scaling firm from a one-off backfill.

**Scoring:** `score = min(100, volume×6 + velocity×12 + role_weight×4)` → tiers **High ≥60 / Medium ≥35 / Low <35**. Velocity is weighted hardest on purpose.

**Live sample (estimator + BD roles, 2022–2024):**

| Employer | Tier | Score | Volume | Velocity | Read |
|----------|:---:|:---:|:---:|:---:|------|
| McCarthy Building Companies | High | 94 | 7 | 2 | Aggressive, sustained pursuit staffing |
| JT Magen & Company | High | 90 | 9 | 2 | High-volume bidder scaling estimating |
| DPR Construction | High | 84 | 4 | 2 | Multi-year, senior pursuit roles |
| Turner Construction | High | 66 | 5 | 2 | Enterprise — confirms the pattern holds |
| Helix Electric (power) | High | 60 | 4 | 2 | Sector-matched ICP, scaling |

---

## The Pipeline

```
h1b_signal_engine.py  (role × year fan-out, 6 workers)
  │  queries h1bdata.info per pipeline-role keyword × year
  │  parses per-employer summary (employer + filing count + median wage)
  ▼
aggregate → score (volume + velocity + role weight) → tier
  │  EPC filter (role auto-pass + employer-name tokens), sector inference
  ▼
SQLite tracker.db (dedup)  +  Supabase epc_company_leads (source="h1b_lca")
  │  domain = name-slug placeholder; raw_data carries intent_score/tier/roles/years
  ▼
[populate_projects.py bridge]  →  Airtable projects
  │  Apollo resolves real domain from company_name; intent_tier → priority
  ▼
enrichment/pipeline.py → Findymail → Smartlead (sector-routed campaign)
```

This source slots into the **existing** `epc_company_leads` table with a new `source` value, so it rides the same enrichment + Smartlead rails as `epc_lead_engine.py`. No new infrastructure. (Note: the `epc_company_leads → projects` bridge is still the known open gap — see `CLAUDE.md` Status.)

### Run commands
```bash
# All pipeline roles, last 3 full years, EPC-only, save
doppler run --project ecas --config dev -- python3 signals/h1b_signal_engine.py

# High-intent only, four years (better velocity resolution)
doppler run --project ecas --config dev -- \
  python3 signals/h1b_signal_engine.py --years 2022 2023 2024 2025 --min-score 60

# Single role, dry-run (no writes)
python3 signals/h1b_signal_engine.py --role "preconstruction manager" --dry-run
```

---

## The Plays — Turning the Filing Into a Conversation

Every play is built on the same move as the Whale Hunter's Playbook: **give before you ask**, and reference the signal *obliquely* — never "I saw your visa filing" (creepy), always "noticed you're scaling your pursuit team" (flattering, true, and shows you watch the market).

### Play 1 — The "Scaling Your Pursuit" Cold Open
**Target:** VP/Director of Business Development or Chief Estimator at a **High-tier** employer.
**The play:** Lead the first email with the *inferred state*, not the data point:
> "Noticed [Firm] has been building out estimating/preconstruction over the last couple of years — usually means the bid pipeline is growing faster than the team can qualify it. We help mid-tier EPCs get short-listed before the RFP drops so the estimators you're hiring spend their time on winnable work, not long-shots."

**Why it works:** It names a real, specific tension the new hires create (more capacity, same win-rate problem) and positions ContractMotion as the fix. The reader assumes you've studied them — because you have.

### Play 2 — The Pursuit Capacity Audit (lead magnet)
**Target:** Firms with **velocity ≥ 2** (sustained hirers).
**The play:** Deliver a one-page "Pursuit Capacity Snapshot": their recent pipeline-role hiring (public LCA data, framed as market intelligence), benchmarked against 3 sector peers also scaling, with the gap — "you're adding estimating capacity but [N] competitors in [sector] are visible on the signals your buyers act on; you aren't." Mail or attach it. This *is* the offer.

**Why it works:** Mirrors the Whale Hunter "Red Team" play. You've done their competitive homework and handed them an uncomfortable, specific gap.

### Play 3 — The New-Hire Trigger
**Target:** Employer whose **most recent year** shows a new senior pursuit role (Director BD / Chief Estimator / Capture Manager).
**The play:** Time outreach to the role, not the calendar. A firm that just added a Capture Manager is explicitly chasing *federal* work — route them straight to the **Defense & Federal** Smartlead sequence and open with the federal-pursuit angle. A new Director of BD gets the growth-leadership angle.

**Why it works:** Role-matched messaging. The person they hired tells you exactly which sector pain to press.

### Play 4 — The Velocity Watch (re-trigger)
**Target:** Firms previously contacted at Medium tier.
**The play:** Re-run the engine quarterly. When a Medium-tier firm crosses into High (new filings push velocity/volume up), that's a fresh, dated reason to re-engage: "Looks like the pursuit build-out is continuing — worth a quick conversation now that it's clearly a priority."

**Why it works:** Manufactures a legitimate, non-pushy reason to follow up, keyed to *their* behavior.

---

## Role → Message Routing

| Role they hired | Sector lean | Open with | Smartlead route |
|-----------------|-------------|-----------|-----------------|
| Capture Manager | Defense/Federal | "Federal pursuit is clearly a focus…" | `3095136` Defense |
| Director of BD | Any | Growth-leadership / win-rate angle | sector-inferred |
| Chief / Sr. Estimator | Power, Industrial | "Bidding bigger jobs…" capacity angle | sector-inferred |
| Preconstruction Mgr | DC, Power | Front-end pursuit / early positioning | sector-inferred |
| Proposal Manager | Any | Volume + quality of submissions | sector-inferred |

---

## Caveats — Read Before You Send

1. **An LCA is intent to hire, not proof of hire.** ~30%+ of LCAs never become a working visa (lottery, withdrawal). Treat it as a *budget/intent* signal about the firm, not a fact about a specific person. Never reference a named individual.
2. **Employer-name variants don't auto-merge.** "TURNER CONSTRUCTION" vs "TURNER CONSTRUCTION COMPANY" can appear as two rows; Apollo domain resolution in enrichment collapses them downstream. Don't dedupe by hand.
3. **`domain` is a placeholder slug** until enrichment resolves the real one — `raw_data.needs_domain_resolution = true`. Don't email the slug.
4. **Big-tech false-positives are sometimes true ICP.** Meta filing "Estimator" is real — it staffs data-center construction estimation. Let the DC sector route catch it; don't blanket-blocklist.
5. **Source is the convenience index.** For an audit-grade or compliance-sensitive rebuild, swap the fetch layer for the authoritative DOL OFLC quarterly disclosure files (same schema, no scraping). The engine docstring marks the seam.

---

## The Unifying Principle

The Whale Hunter's Playbook lands hyperscale contracts by *giving before asking*. This playbook adds the missing front half: **knowing precisely when to give.** An EPC that just funded its pursuit team is, for a brief window, both able to buy and acutely aware of the problem ContractMotion solves. The H-1B filing is the timestamp on that window. Watch the filings, route by the role, lead with the inferred state — and you are talking to the buyer while the budget is still warm.
