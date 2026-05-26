# ContractMotion Smartlead Sequence — H-1B Intent Signal (2026-05-25)
## Trigger: EPC just funded a pipeline/revenue role (estimator, preconstruction, BD, capture)

Pairs with: `signals/h1b_signal_engine.py` + `docs/h1b-intent-outreach-playbook.md`
Cadence: Day 0 / 4 / 9 / 15 / 22 / 30 (matches v2 house cadence)
Enroll trigger: lead lands in `epc_company_leads` with `source = h1b_lca` and `raw_data.intent_tier` ∈ {High, Medium}

---

## What makes this sequence different

Every other ContractMotion sequence opens on a *project* signal (FERC filing, PJM queue, federal award). This one opens on a *hiring* signal: the firm just spent real money staffing the team that chases work. That is a leading indicator — it fires before the pursuit even starts. The copy references the **inferred state** ("you're scaling your pursuit team"), never the data point ("your H-1B filing"). See playbook Caveat #1.

---

## Sequence structure

| Email | Day | Purpose | CTA |
|-------|-----|---------|-----|
| 1 | 0 | Pattern interrupt — name the pursuit build-out | No ask |
| 2 | 4 | Before vs after — more bid capacity, same win-rate problem | Soft interest check |
| 3 | 9 | Social proof — EPC that scaled pursuit then got short-listed | Territory offer |
| 4 | 15 | The math — capacity you're paying for vs winnable work | Offer Pursuit Capacity Snapshot |
| 5 | 22 | The guarantee — 2 pre-RFP shortlist positions / 180 days | 20-min meeting ask |
| 6 | 30 | Door-open — leave the Snapshot, no pressure | No CTA |

---

## Personalization tokens

| Token | Source |
|-------|--------|
| `{{first_name}}`, `{{company_name}}` | Airtable contacts (post-enrichment) |
| `{{pursuit_role}}` | `raw_data.roles` → friendly label (see Role-Swap table) |
| `{{role_open}}` | Role-routed opening clause (Role-Swap table) |
| `{{sector_proof}}` | Sector-matched proof line (Sector-Routing table) |

---

## Email 1 — Day 0
**Subject:** `{{company_name}} — scaling the pursuit side?`

{{first_name}},

We watch the market signals that show which mid-tier EPCs are gearing up to win more work — and {{company_name}} has been building out {{pursuit_role}} over the last couple of years.

Usually that means one thing: the bid pipeline is growing faster than the team can qualify it. More capacity to chase work, same problem deciding *which* work is actually winnable.

{{role_open}}

No pitch here — just flagging that we tend to be useful to firms right at this stage. More below over the next couple weeks.

— Ethan

---

## Email 2 — Day 4
**Subject:** `Re: {{company_name}} — scaling the pursuit side?`

{{first_name}},

The hard part about adding estimating and preconstruction capacity: it raises your *throughput*, not your *hit rate*. You can qualify twice as many bids and still win the same percentage — you're just busier losing.

How most EPCs find work now: the RFP drops, you scramble, you compete on price against a crowded field where the short-list was decided months ago.

How the firms winning more actually do it: they're visible to the buyer 6–18 months before the RFP — already on the short list when it drops.

That gap is the whole reason your new {{pursuit_role}} hires matter. Worth 10 minutes to see where {{company_name}} sits?

— Ethan

---

## Email 3 — Day 9
**Subject:** `how an EPC like {{company_name}} got on the short list first`

{{first_name}},

{{sector_proof}}

The pattern repeats: the firm that's *visible* before procurement opens gets the pre-RFP phone call. The firm that waits for the RFP competes on price.

We hold a limited number of territory engagements per sector so we're never positioning two competitors into the same buyer. {{company_name}}'s sector still has an opening.

Want me to hold it while we talk?

— Ethan

---

## Email 4 — Day 15
**Subject:** `the math on the capacity you just added`

{{first_name}},

Quick math before I move on.

A new estimator or BD hire is a real annual cost once you count salary, sponsorship, and ramp. That investment only pays back if the extra bids they qualify actually convert.

One pre-RFP short-list position that lands a $3M contract is ~$600K gross profit at 20% margin. Our full-year engagement runs $66K — about 11% of the margin on one contract you weren't positioned for otherwise.

You've already made the expensive move (the team). This is the cheap part (making sure they chase winnable work).

I can pull a **Pursuit Capacity Snapshot** for {{company_name}} — your recent pipeline build-out benchmarked against the sector peers also scaling, and where they're visible to your buyers and you aren't. Reply "snapshot" and it's yours, no obligation.

— Ethan

---

## Email 5 — Day 22
**Subject:** `2 short-list positions, 180 days`

{{first_name}},

Straight offer.

We'll get {{company_name}} into at least **2 pre-RFP short-list positions in your sector within 180 days** — visible to the buyer before procurement opens. If we don't, you don't renew. That's the whole risk.

The reason now is simple: you've staffed up to chase more work. The bottleneck isn't capacity anymore — it's being seen early enough to win. That's the part we own.

20 minutes this week? Here's my calendar: [LINK]

— Ethan

---

## Email 6 — Day 30
**Subject:** `closing the loop, {{first_name}}`

{{first_name}},

Last note — I don't want to become inbox noise.

If the pipeline's healthy and the new {{pursuit_role}} hires are landing the work they're chasing, great. Nothing to talk about.

If there's a project type, geography, or buyer relationship you've been trying to crack and haven't — that's exactly where we tend to earn our keep.

Either way I'll leave you the **Pursuit Capacity Snapshot** for {{company_name}} whenever you want it — just reply. The firms on the short list when the next RFP drops are the ones who were visible 12 months before. Worth keeping in mind.

— Ethan

---

## Role-Swap table — populate `{{pursuit_role}}` + `{{role_open}}`

| Detected role (`raw_data.roles`) | `{{pursuit_role}}` | `{{role_open}}` |
|-----------------------------------|--------------------|-----------------|
| capture manager | federal capture | A capture hire usually means federal work is now a priority — and federal short-lists are decided earlier than any other. That timing is exactly what we manage. |
| director of business development / business development manager | business development | A BD leadership hire means top-of-funnel growth is now somebody's full-time job — we make sure that funnel is fed with winnable, pre-RFP opportunities. |
| chief estimator / estimator | estimating | More estimating horsepower only pays off if it's pointed at bids you can actually win. That targeting is the part we handle. |
| preconstruction manager | preconstruction | Preconstruction owns the front end of the pursuit — the earlier you're positioned, the more that role is worth. |
| proposal manager | proposal | A dedicated proposal hire means you're submitting enough to need one — we work to get more of those submissions onto a short list before the RFP is even public. |

---

## Sector-Routing — populate `{{sector_proof}}` + Smartlead campaign

| Sector (`epc_company_leads.sector`) | Smartlead Campaign | `{{sector_proof}}` proof line |
|-------------------------------------|--------------------|-------------------------------|
| power | `3005694` Power & Grid | A regional power EPC scaled estimating ahead of the PJM queue expansion — we had them short-listed on two utility pre-quals before either RFP went public. |
| dc | `3040599` Data Center & AI | A mid-tier data-center contractor built out preconstruction as hyperscaler demand spiked — we positioned them with two operators 9 months before procurement. |
| water | `3040600` Water & Wastewater | A water/wastewater EPC added BD capacity ahead of an SRF funding cycle — we got them in front of two municipal buyers before the RFPs dropped. |
| industrial | `3040601` Industrial & Manufacturing | An industrial EPC scaled estimating for reshoring work — we had them on two owner short-lists ahead of the formal bid. |
| defense / general_epc | `3095136` Defense & Federal | A federal-focused EPC added a capture manager — we positioned them on two agency short-lists before the solicitations were posted. |

---

## Setup notes

**Enrollment:** route via `enroll_contacts_to_campaigns.py` using `epc_company_leads.sector` → campaign map above. `raw_data.intent_tier = High` enrolls immediately; `Medium` holds for review (mirrors verification routing).

**Do not send to:**
- Contacts with Airtable `outreach_status` ∈ {in_sequence, replied, meeting_booked, do_not_contact, unsubscribed}
- Companies already enrolled from another signal source (dedupe on resolved domain, not the h1b slug)

**Never reference:** the H-1B filing, a visa, or any named individual. The signal is *inferred* ("scaling your pursuit team"), per playbook Caveat #1.

**A/B test candidates:**
- Email 1 subject: `scaling the pursuit side?` vs `building out {{pursuit_role}}?`
- Email 5: guarantee framing (`2 positions / 180 days`) vs pilot framing (`90-day pilot, walk away`)
- `{{role_open}}` present vs omitted (does role-routing lift reply rate?)
