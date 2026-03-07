# ECAS Smartlead Email Sequence
## Campaign: Power & Grid EPC Outreach 2026
### Campaign ID: 2924407

Sending cadence: Day 0 → Day 3 → Day 7 → Day 14

---

## Email 1 — Day 0
**Subject:** {Company} — something we noticed in the grid data

**Body:**

{FirstName},

We track congressional investment activity, FERC interconnection filings, and federal contract awards across the power and grid sector — basically the upstream signals that predict where EPC spending is going to land.

{Company} showed up in our scan this week. Power & Grid is running at a confirmed signal level right now — politicians and institutional capital are positioned, federal contracts are flowing, and the interconnection queue in your region has expanded significantly.

That usually means utilities are 6–18 months from a procurement cycle. The contractors who get pre-qualified before that cycle opens win. The ones who wait for the RFP compete on price in a crowded field.

Happy to send you a one-page breakdown of what we're seeing specifically in your market — no pitch, just the data.

Worth a look?

[Your Name]
[Company]

---

## Email 2 — Day 3
**Subject:** Re: {Company} — something we noticed in the grid data

**Body:**

{FirstName},

Following up on my note from a few days ago.

Pulled a quick competitive snapshot while I had your sector open. Three of the firms competing for the same utility pre-qualifications you'd be targeting have updated their digital presence and content in the last 90 days. Two of them are now ranking for search terms your buyers use when building an approved vendor list.

That's not the reason utilities award contracts. But it is how procurement managers decide who gets a phone call before the RFP drops.

The firms that get that call are already on a short list your firm isn't on yet. That's the gap we fix.

If you want to see the actual competitive breakdown — 10 minutes, no obligation — I'll send you a calendar link.

[Your Name]

---

## Email 3 — Day 7
**Subject:** the math on one contract

**Body:**

{FirstName},

Quick thought before I move on.

A single new utility pre-qualification that leads to a $3M contract is $600K in gross profit at a 20% margin.

Our full-year engagement runs $66K. That's 11% of the margin on one contract you wouldn't have been positioned for otherwise.

The question isn't whether marketing works for EPC firms. It's whether the timing is right for you.

If Q2 is a better conversation — genuinely fine. I'll reach back out then. If you want to see how we'd approach your specific situation before I do, reply and I'll send the one-pager.

[Your Name]

---

## Email 4 — Day 14
**Subject:** closing the loop

**Body:**

{FirstName},

Last note from me.

I know timing isn't always right, and I don't want to become noise in your inbox.

If the BD pipeline is healthy and you're winning the pre-qualifications you're after — great, nothing to talk about.

If there's a project type, geography, or buyer relationship you've been trying to crack and haven't — that's exactly where we tend to be useful.

Either way, I'll leave you with this: the FERC interconnection queue in your region has more pending projects right now than at any point in the last five years. The utility procurement cycles that follow that queue are already in motion. The contractors on the short list when those RFPs drop will be the ones who were visible 12 months before.

Worth keeping in mind whenever the timing is right.

[Your Name]

---

## Sequence Setup Notes

**Sending domain:** Configure before activating (needs 3-week warmup)

**Personalization variables to populate via Apollo enrichment:**
- `{FirstName}` — contact first name
- `{Company}` — company name
- Pull from Airtable contacts table after enrichment job runs

**Targeting:**
- Title filters: VP Operations, VP Business Development, President, CEO, Owner, Director of Business Development, COO
- Company revenue: $20M–$300M
- NAICS: 237130, 238210, 237110
- States: VA, TX, NC, GA, FL, MD, PA (expand after initial results)

**Do not send to:**
- Companies already in active BD conversations
- Firms with Airtable `outreach_status = enrolled` already

**A/B test candidates:**
- Email 1 subject: "something we noticed in the grid data" vs. "{Company} — grid signal this week"
- Email 3: math-based vs. risk-reversal framing ("90-day pilot, walk away if it doesn't work")
