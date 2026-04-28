# ECAS Smartlead Email Sequence
## Campaign: Defense Facility & Infrastructure EPC Outreach 2026
### Status: TEMPLATE — Load into Smartlead before activating

Sending cadence: Day 0 → Day 3 → Day 7 → Day 14 → Day 22 → Day 30

---

## ICP Profile

**Who this goes to:**
- Electrical, mechanical, and general contractors doing DoD facility work
- C-UAS/counter-drone installation contractors
- Firms building or upgrading hardened communications, command & control, or base infrastructure
- Security systems integrators with DoD facility contracts

**Title filters:** VP Operations, VP Business Development, President, CEO, Owner, Director of BD, COO
**Company revenue:** $20M–$300M
**NAICS:** 236210, 236220, 238210, 237310, 237130
**States:** VA, MD, TX, NC, GA, FL, PA (proximity to major installations)

**Do not send to:**
- Companies already in active BD conversations
- Firms with `outreach_status = enrolled` in Airtable

---

## Signal Hooks (pull from current sector data before sending)

- DoD MILCON (Military Construction) budget line items in your region
- C-UAS base hardening awards (Kratos, AeroVironment contracts signal downstream facility work)
- AXON/body camera rollouts → law enforcement facility upgrades
- Any defense prime (LMT, RTX, NOC, GD) capex announcement = downstream EPC demand

---

## Email 1 — Day 0
**Subject:** {Company} — DoD facility pipeline is moving

**Body:**

{FirstName},

We track DoD contract awards, MILCON allocations, and defense prime capex announcements — the upstream signals that predict where facility and infrastructure EPC spending lands next.

{Company} showed up in our scan this week. Defense infrastructure is at an active signal level right now — MILCON budgets are at a 10-year high, C-UAS installation contracts are accelerating across domestic bases, and the primes are in a capex expansion cycle that flows downstream to facility and electrical contractors inside of 12 months.

That usually means pre-qualification windows are opening before the RFPs publish. The contractors on the approved vendor list when those packages drop win. The ones who wait compete on price in a crowded field.

Happy to send you a one-page breakdown of what we're seeing specifically in your region and contract tier — no pitch, just the data.

Worth a look?

[Your Name]
[Company]

---

## Email 2 — Day 3
**Subject:** Re: {Company} — DoD facility pipeline is moving

**Body:**

{FirstName},

Following up on my note.

Pulled a quick competitive snapshot while I had your sector open. Several of the firms competing for the same DoD pre-qualifications you'd be targeting have added program-specific case studies and updated their capability statements in the last 90 days.

Two of them are now showing up when contracting officers search for approved vendors in your NAICS codes.

That's not how contracts get awarded. But it is how firms get the phone call before the solicitation drops — and that call is the difference between being on the short list and being on the outside looking in.

The firms getting that call are already positioned. That's the gap we close.

Ten minutes, no obligation — I'll send a calendar link if you want to see how we'd approach your specific situation.

[Your Name]

---

## Email 3 — Day 7
**Subject:** the math on one DoD pre-qual

**Body:**

{FirstName},

Quick thought before I move on.

A single new DoD pre-qualification that leads to a $2.5M facility or electrical contract is $500K in gross profit at a 20% margin.

Our full-year engagement runs $66K. That's 13% of the margin on one contract you wouldn't have been positioned for otherwise.

The MILCON pipeline doesn't slow down because a contractor isn't ready. It just routes around them.

If Q2 is a better conversation — genuinely fine. I'll reach back out then. If you want to see how we'd approach your specific situation before I do, reply and I'll send the one-pager.

[Your Name]

---

## Email 4 — Day 14
**Subject:** closing the loop

**Body:**

{FirstName},

Last note from me.

If the DoD pipeline is healthy and you're winning the pre-qualifications you're after — nothing to talk about.

If there's a contract vehicle, base, or prime relationship you've been trying to crack and haven't — that's exactly where we tend to be useful.

Either way: the defense facility and infrastructure spend cycle we're tracking right now is the largest since post-9/11 GWOT construction. C-UAS installations alone are creating a 3-year runway of electrical and facility work across domestic bases. The contractors on pre-approved vendor lists when those task orders release will be the ones who were visible 12 months before.

Worth keeping in mind whenever the timing is right.

[Your Name]

---

## Email 5 — Day 22
**Subject:** 2 pre-RFP shortlist positions. 180 days. Guaranteed.

**Body:**

{FirstName},

One thing I have not mentioned: ContractMotion guarantees 2 pre-RFP shortlist positions in the defense facility and infrastructure sector within 180 days of onboarding — or we keep working at no charge until we hit it.

That guarantee exists because we are not generating leads. We are tracking a funded pipeline — MILCON appropriations, FPDS contract awards, and C-UAS installation records that already exist in federal procurement data but have not reached formal solicitation yet.

The pool of qualified defense facility EPCs is smaller than it looks. The contractors getting on pre-approved vendor lists are not out-competing anyone — they are simply showing up when the contracting officer is building the list.

Worth 20 minutes to see if {Company} qualifies?

[Your Name]

---

## Email 6 — Day 30
**Subject:** closing the file on this

**Body:**

{FirstName},

Last note from me.

If defense facility and infrastructure positioning ever becomes relevant for {Company}, I am easy to find. I will leave you this: MILCON appropriations for FY2025–FY2026 are the largest two-year defense construction allocation in two decades. C-UAS installation mandates across domestic bases are creating a 3-year runway of electrical and facility work. The contracts behind both are being awarded now — before most of the associated solicitations exist.

The contractors on pre-qualified vendor lists when those task orders drop will be the ones who were visible to contracting officers 12 months before.

Worth keeping in mind.

[Your Name]

---

## Setup Notes

**Sending domain:** Separate from Power & Grid campaign — use subdomains (e.g., defense.contractmotion.com)

**Personalization variables (Apollo enrichment):**
- `{FirstName}` — contact first name
- `{Company}` — company name
- Pull from Airtable contacts table, filter `sector = Defense`

**Signal-triggered send:** When Defense sector heat score crosses 55/100, ECAS engine will Slack-alert. That's the trigger to activate this campaign in Smartlead.

**A/B test candidates:**
- Email 1 subject: "DoD facility pipeline is moving" vs. "something we noticed in the base construction data"
- Email 3: margin math vs. "the contracts going to firms that were ready 12 months ago"
