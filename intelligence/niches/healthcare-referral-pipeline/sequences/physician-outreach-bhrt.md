# Physician Outreach — BHRT / Hormone Prescribers

**Sent by:** Compounding pharmacy rep on behalf of pharmacy client
**Target:** OB-GYN, internal medicine, integrative medicine — any physician actively prescribing hormone therapy
**Purpose:** Introduce the pharmacy, offer formulary, open door for clinical collaboration
**Smartlead setup:** Day 1 → Day 5 → Day 12 | pause on any reply
**From name:** [Pharmacy Rep Name] (personal name, not pharmacy name)

---

## Email 1 — Day 1

**Subject:** compounding partner for your hormone patients

Hi {{first_name}},

Reaching out from [Pharmacy Name] — we're a compounding pharmacy in [City/Region] that specializes in BHRT and hormone formulations.

We work with a lot of OB-GYNs and integrative medicine physicians who are writing hormone scripts and want more control over what their patients are actually getting — exact doses, specific delivery forms, no fillers they didn't ask for.

We compound Biest, progesterone capsules, testosterone cream, DHEA, and most of the standard BHRT combinations. Turnaround is typically 24–48 hours on most formulations, and we have a licensed pharmacist available for clinical consultations on complex cases.

Would it make sense to send you our formulary? Happy to do it in whatever format is easiest — email, physical copy, or a quick call if you'd rather talk through it.

{{signature}}

---

## Email 2 — Day 5

**Subject:** one thing our prescribers always mention

{{first_name}} —

The thing physicians tell us they notice first is usually turnaround time. When a patient is waiting on a custom progesterone formulation or a testosterone cream titration, a 2-week wait from a mail-order compounder creates a real problem. We're [X miles / same metro] from your practice — most scripts are ready same or next business day.

The other thing they mention: being able to actually reach the pharmacist. If you have a patient who's on a complex protocol and something isn't landing right, you can call us and talk to someone who knows what they're doing.

Two ways to take a next step — whichever is easier:

1. I'll send over the formulary now and you can look it over when you have time
2. 15-minute call with our lead pharmacist to walk through any BHRT case you have coming up

Either one works. What makes more sense?

{{signature}}

---

## Email 3 — Day 12

**Subject:** leaving this here

{{first_name}} —

Not going to keep following up — I know the inbox is brutal.

If you ever have a hormone patient who needs a specific formulation and your current pharmacy is slow to fill it, out of stock, or just won't compound it — we're here.

We're easy to reach, fast to fill, and we'll actually pick up the phone.

Reply anytime or book a call here: [Link]

{{signature}}

---

## Personalization Tokens

| Token | Source |
|-------|--------|
| `{{first_name}}` | Physician first name from NPI/CMS data |
| `{{specialty}}` | Physician specialty (OB-GYN / integrative medicine / internal medicine) |
| `[Pharmacy Name]` | Client pharmacy name |
| `[Pharmacy Rep Name]` | Name of person sending (pharmacy staff or rep) |
| `[City/Region]` | Pharmacy location — use city name, not full address |
| `[X miles / same metro]` | Distance from pharmacy to physician practice (from NPI addresses) |

## Apollo / NPI List Filters

```
Taxonomy codes: 207RG0100X (OB-GYN), 207R00000X (Internal Medicine), 207RI0011X (Integrative Medicine)
State: match to client pharmacy state + border states
City/zip radius: 25 miles from pharmacy location
CMS Part D filter (if available): prescribed estradiol, progesterone, or testosterone in last 12 months, min 10 claims
Exclude: hospital-employed physicians, multi-specialty group practices with >20 physicians
```

## Objection Handling (Quick Reference)

| Objection | Response |
|-----------|----------|
| "We already have a compounding pharmacy we use" | "Totally understood — most physicians have a go-to. We just like to be on the backup list for when turnaround is slow or a specific formulation isn't available. Would it be okay to send you our formulary to keep on file?" |
| "We don't prescribe much compounded hormone therapy" | "Got it — if that changes, or if you have a patient who needs something more custom than what's commercially available, we're easy to reach. Mind if I leave you the formulary?" |
| "I'm not familiar with your pharmacy" | "We're [X years] old, [state] licensed, [PCAB accredited if applicable]. Happy to send credentials and references from prescribers you may know." |

---

*Sequences ready to load into Smartlead. Sending domain should be pharmacy-neutral — not ContractMotion branded.*
