# ECAS Smartlead Email Sequence
## Campaign: Nuclear & Critical Minerals Infrastructure EPC Outreach 2026
### Status: TEMPLATE — Load into Smartlead before activating

Sending cadence: Day 0 → Day 3 → Day 7 → Day 14

---

## ICP Profile

**Who this goes to:**
- Heavy industrial and specialty contractors doing nuclear facility prep, construction, or decommissioning
- Industrial electrical contractors working near SMR or nuclear plant sites
- Contractors building critical mineral processing or rare earth refinery infrastructure
- Civil/mechanical contractors with nuclear QA programs (NQA-1 holders or pursuing)

**Title filters:** VP Operations, VP Business Development, President, CEO, Owner, Director of BD, COO, VP Preconstruction
**Company revenue:** $20M–$500M (wider band — nuclear projects run larger)
**NAICS:** 237110, 237120, 237130, 238210, 236210
**States:** ID, WY, TX, SC, TN, OH, VA, PA (SMR site clusters + existing plant states)

**Do not send to:**
- Companies already in active BD conversations
- Firms with `outreach_status = enrolled` in Airtable

---

## Signal Hooks (pull from current sector data before sending)

- SMR site announcements: Oklo, X-Energy, Kairos, NuScale, Last Energy
- DOE loan guarantee awards and Critical Minerals grants (USASpending)
- Microsoft, Oracle, Google nuclear PPA announcements — site prep contracts follow within 6-12 months
- Uranium enrichment plant construction awards (Centrus, Urenco)
- Rare earth processing facility permits (MP Materials, Energy Fuels)

---

## Email 1 — Day 0
**Subject:** {Company} — nuclear infrastructure is moving faster than most contractors realize

**Body:**

{FirstName},

We track DOE loan awards, SMR site announcements, nuclear PPA filings, and critical mineral facility permits — the upstream signals that predict where heavy industrial and specialty EPC spending lands next.

{Company} showed up in our scan this week. Nuclear infrastructure is at a confirmed signal level right now — Microsoft just signed the first nuclear PPA in 20 years, three SMR developers received DOE funding in the last 90 days, and the critical minerals processing pipeline has more active site permits than at any point in the last decade.

The contractors who get pre-qualified on those sites before ground breaks win the work. The ones who find out when the RFP publishes compete against firms that have been on-site for months.

Happy to send you a one-page breakdown of what we're seeing in your region and contract tier — no pitch, just the data.

Worth a look?

[Your Name]
[Company]

---

## Email 2 — Day 3
**Subject:** Re: {Company} — nuclear infrastructure is moving faster than most contractors realize

**Body:**

{FirstName},

Following up quickly.

Pulled a competitive snapshot while I had your sector open. A handful of the specialty and heavy industrial contractors targeting the same SMR and critical mineral sites you'd be going after have updated their capability statements and nuclear QA program documentation in the last 60 days.

Two are actively pursuing NQA-1 certification now — not because they have a contract, but because they know pre-qualification requires it and the window to get qualified before site selection closes is short.

The developers doing site selection aren't waiting for contractors to get ready. They're building approved vendor lists now.

If you want to see the actual competitive breakdown — 10 minutes, no obligation — I'll send you a calendar link.

[Your Name]

---

## Email 3 — Day 7
**Subject:** the math is different in nuclear

**Body:**

{FirstName},

Quick thought before I move on.

A single SMR site prep or critical mineral facility contract runs $5M–$30M. At a 15% margin, that's $750K–$4.5M in gross profit on one award.

Our full-year engagement runs $66K. That's less than 1% of the margin on one contract you wouldn't have been positioned for otherwise.

The question isn't whether marketing matters in nuclear and heavy industrial. It's whether you're going to be in the room when site selection happens or find out after the fact.

If Q2 is a better conversation — genuinely fine. If you want to see how we'd approach your specific situation before I reach back out, reply and I'll send the one-pager.

[Your Name]

---

## Email 4 — Day 14
**Subject:** closing the loop

**Body:**

{FirstName},

Last note from me.

If the nuclear and heavy industrial pipeline is healthy and you're winning the pre-qualifications you're after — nothing to talk about.

If there's a site, developer, or contract vehicle you've been trying to crack and haven't — that's where we tend to be useful.

Either way: the SMR and critical minerals buildout is the largest new heavy industrial construction cycle since the 1970s nuclear build. Microsoft, Oracle, Amazon, and Google are all under contract or in advanced negotiations for nuclear power. The site prep and infrastructure work that follows those PPAs is already in motion. The contractors on approved vendor lists when those projects break ground will be the ones who were visible 12 months before.

Worth keeping in mind whenever the timing is right.

[Your Name]

---

## Setup Notes

**Sending domain:** Separate subdomain recommended (e.g., nuclear.contractmotion.com or energy.contractmotion.com)

**Personalization variables (Apollo enrichment):**
- `{FirstName}` — contact first name
- `{Company}` — company name
- Pull from Airtable contacts table, filter `sector = Nuclear & Critical Minerals`

**Signal-triggered send:** Nuclear sector is early_signal (0.0/100) as of 2026-03-07. ECAS engine will Slack-alert when it crosses 45/100. That's the activation trigger for this campaign.

**NQA-1 note:** If Apollo/Clay enrichment can detect whether the company has nuclear QA certifications, use that as a personalization variable — firms pursuing NQA-1 are highest intent.

**A/B test candidates:**
- Email 1 subject: "nuclear infrastructure is moving faster than most contractors realize" vs. "the SMR buildout is closer than it looks"
- Email 3: dollar-math anchor vs. "the developers doing site selection aren't waiting for contractors to get ready"
