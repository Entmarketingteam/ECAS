# Physician Outreach — GLP-1 / Obesity Medicine / Weight Loss Prescribers

**Sent by:** Compounding pharmacy rep on behalf of pharmacy client
**Target:** Obesity medicine physicians, internal medicine / family medicine with weight loss focus, functional medicine MDs writing GLP-1 scripts
**Purpose:** Establish the pharmacy as a reliable GLP-1 compounding partner post-shortage — supply stability, formulation flexibility, clinical support
**Smartlead setup:** Day 1 → Day 5 → Day 12 | pause on any reply
**From name:** [Pharmacy Rep Name] (personal name, not pharmacy name)

---

## Email 1 — Day 1

**Subject:** GLP-1 compounding after the shortage window

Hi {{first_name}},

Reaching out from [Pharmacy Name]. We compound GLP-1 peptides and have stayed consistently stocked through the shortage period — I wanted to make sure you knew we were here in case your current supply situation has been inconsistent.

The FDA shortage designation for semaglutide and tirzepatide is under pressure right now, and a lot of pharmacies that ramped up quickly are running into supply and compliance issues. We've been deliberate about staying within the regulatory lines — 503A compounding, physician-initiated prescriptions, appropriate documentation — and we've kept our supply stable as a result.

If you're writing GLP-1 scripts and you've had any disruptions with your current pharmacy, worth knowing there's an option nearby.

Want me to send over our current formulary and pricing?

{{signature}}

---

## Email 2 — Day 5

**Subject:** what prescribers are asking us about right now

{{first_name}} —

The questions we're getting from physicians most often right now:

**Tirzepatide availability** — yes, we have it. Full titration protocol, maintenance doses, and we can match the schedule your patients are already on.

**Maintenance dosing** — a lot of patients who lost weight on semaglutide are now in a maintenance phase. We compound maintenance doses at lower concentrations than the acute weight loss protocol, which some patients tolerate better and costs less to sustain long-term.

**Peptide combinations** — some physicians are pairing GLP-1 with BPC-157 for GI tolerance, or with other peptides for body composition support. We can compound those if you're exploring that direction.

We also have a pharmacist available for clinical consults — not to tell you how to practice, just to work through formulation questions when they come up.

Would a 15-minute call with our lead pharmacist be useful? I can have you on the calendar this week.

{{signature}}

---

## Email 3 — Day 12

**Subject:** last one

{{first_name}} —

Last one from me.

If GLP-1 supply has been smooth for you and your current pharmacy is doing the job — great. Nothing to change.

But if you ever hit a week where a patient's refill falls through, or a formulation isn't available, or your pharmacy starts struggling with compliance pressure — we're here and we can fill quickly.

Reply any time or book a call: [Link]

{{signature}}

---

## Personalization Tokens

| Token | Source |
|-------|--------|
| `{{first_name}}` | Physician first name from NPI/CMS data |
| `{{specialty}}` | Obesity medicine / internal medicine / family medicine |
| `[Pharmacy Name]` | Client pharmacy name |
| `[Pharmacy Rep Name]` | Name of person sending (pharmacy staff or rep) |

## Apollo / NPI List Filters

```
Taxonomy codes: 207QH0002X (Obesity Medicine), 207Q00000X (Family Medicine), 207R00000X (Internal Medicine)
Association filter (high intent): ABOM-certified physicians (abom.org), OMA members
State: match to client pharmacy state + border states
City/zip radius: 25–50 miles from pharmacy location
CMS Part D filter (if available): prescribed semaglutide or tirzepatide in last 12 months, min 10 claims
Exclude: hospital-employed physicians, bariatric surgery-only practices
```

## Timing Notes

- This sequence is most effective while the FDA shortage designation is still active or recently expired
- If shortage window closes before sequence launches, update Email 1 to focus on supply stability post-shortage and formulation flexibility vs. brand-name options
- Email 2 references tirzepatide explicitly — verify current compounding legality in client state before sending

## Objection Handling (Quick Reference)

| Objection | Response |
|-----------|----------|
| "The FDA shortage may end soon — is this sustainable?" | "We're 503A, physician-prescription compounding only — not the bulk distribution model that's getting scrutiny. Compliant 503A compounding is legal regardless of shortage status. Happy to walk through the distinction." |
| "I already have a pharmacy I use for this" | "Makes sense — just good to have a backup. Supply disruptions are still happening sporadically. Would it be okay to send you our formulary in case you ever need a fill covered fast?" |
| "I'm not sure about the regulatory situation" | "Completely fair — it moves fast. Our pharmacist can walk you through exactly where we stand and how we document prescriptions to keep you clean on your end. Want to set that call up?" |

---

*Sequences ready to load into Smartlead. Sending domain should be pharmacy-neutral — not ContractMotion branded.*
