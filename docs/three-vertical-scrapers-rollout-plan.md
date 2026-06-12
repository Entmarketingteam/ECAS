# Rollout Plan — 3 Vertical Scrapers (TTB / HIPAA / FMCSA)

**Status:** scrapers built + tested, **OFF cron** (on-demand only). Nothing sends until this plan is executed with oversight.
**Owner decision required before any build.** Updated 2026-06-12.

---

## Where we are (verified)

| Item | State |
|------|-------|
| TTB alcohol scraper | ✅ extracts 142/run, dedup, tested. On-demand: `POST /admin/run/ttb_alcohol` |
| HIPAA breach scraper | ✅ extracts 728 avail / 50 freshest per run, dedup, tested. `/admin/run/hipaa_breach` |
| FMCSA fleet scraper | ✅ US 5-50 PU carriers, 50/run, dedup, tested. `/admin/run/fmcsa_fleet` |
| Cron schedules | ⏸️ **paused** (commented in scheduler.py) — no auto-fire |
| Smartlead campaigns for these verticals | ❌ **none exist** (checked all 20) |
| sector→campaign routing | ❌ not mapped; repo's only map defaults unknowns → Industrial EPC (PAUSED) |
| Live n8n router behavior | ❓ `route_lead_to_n8n` → `N8N_ROUTER_WEBHOOK_URL`, a live n8n workflow **not in repo** — unverified |
| Human oversight gate on enroll | ❌ enrichment path auto-enrolls (`pipeline.py:342` → `in_sequence`), no approval step |
| `tracker.db` dedup persistence | ⚠️ ephemeral on Railway (`mkdir -p /app/database`, no volume) — resets on deploy |

---

## Decision 0 — GO/NO-GO per vertical (do this first)

These 3 read like exploratory niches, not core ContractMotion (EPC contract acquisition). Before building anything, confirm there is a **real offer** for each:

- **HIPAA / Document Destruction** — overlaps the existing `Document Destruction` vertical (shredding scraper). Plausible offer (breach → shredding/compliance). Most likely GO.
- **TTB / Craft Spirits & Beverage Logistics** — what do we sell a new distillery/wholesaler? Offer unclear. NO-GO unless an offer exists.
- **FMCSA / Fleet Logistics & Pest Control** — what do we sell a 5-50 truck carrier? Offer unclear. NO-GO unless an offer exists.

**Do not build campaigns for a vertical with no validated offer.** Drop or park those scrapers.

---

## Build sequence (per GO vertical)

Each gate is a checkpoint — nothing advances without sign-off.

1. **Offer + messaging** — define the offer, write the sequence copy in brand voice (money-voice for ContractMotion verticals per `feedback_contractmotion_money_voice`). Self-score on the cold-outreach 7-axis rubric.
2. **Smartlead campaign** — create campaign, attach sending inboxes (which domain pool?), confirm warmup. Use `tools/build_test_campaign.py` pattern; HTML `<p>`-wrap bodies.
3. **Sector → campaign mapping** — add the vertical's sector string to:
   - `config.py SECTOR_CAMPAIGN_MAP`
   - `enroll_contacts_to_campaigns.py SECTOR_TO_CAMPAIGN`
   - the **live n8n router workflow** (see Decision 1) — the repo copy is stale, must edit in n8n cloud.
4. **Oversight gate (the key requirement)** — route new-vertical leads to a **holding state, not direct enroll**:
   - land leads as `outreach_status="pending_review"` in Airtable `contacts` (or Supabase `verification_review_queue`),
   - human reviews in an Airtable grid view → flips to `approved`,
   - an **approved-gated** enroll step (not the auto enrichment path) sends only `approved` + `email_verified` leads to Smartlead.
   - This guarantees "nothing sends without human OK." Confirm the n8n router does NOT auto-enroll (Decision 1).
5. **Pilot** — on-demand run, manually inspect ~10-20 leads: correct campaign, correct copy, NAP/contact sanity. Only after a clean pilot:
6. **Enable cron** — uncomment the schedule in `scheduler.py` (TTB Tue / HIPAA Wed / FMCSA Thu, 12:00 UTC).
7. **Monitor** — bounce rate, reply rate, reputation on the vertical's inboxes.

---

## Decision 1 — inspect the live n8n router (blocking, needs n8n cloud)

`route_lead_to_n8n` posts to `N8N_ROUTER_WEBHOOK_URL` — a workflow on `entagency.app.n8n.cloud` **not in the repo**. Must open it and confirm:
- Does it auto-enroll into Smartlead, or hold for review?
- What does it do with an unmapped sector (drop / default / error)?
- What do the existing niche scrapers' leads (`Document Destruction`, builder) actually do today? (precedent — likely incomplete too)

This determines whether step 4's oversight gate is added in n8n or in code.

---

## Infra fix (before any GO vertical sends)

**Mount a Railway volume at `/app/database`** so `tracker.db` (the dedup defense for ALL scrapers, incl. h1b) survives deploys. Without it, a deploy wipes dedup → re-spam on the next run.

---

## Summary of what blocks "send"

1. GO/NO-GO offer per vertical (Decision 0)
2. Inspect live n8n router (Decision 1)
3. Per GO vertical: offer → copy → campaign → sector mapping → **oversight gate** → pilot → cron
4. Railway volume for `tracker.db`
