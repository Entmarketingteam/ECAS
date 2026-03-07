# ECAS Cold Email Sequence Templates

Three sector-specific 4-email Smartlead sequences. Each maps to a tracked sector in the ECAS engine.

---

## Sequences

| File | Sector | Smartlead Campaign | Activation Trigger |
|------|--------|-------------------|-------------------|
| `power-grid-epc-sequence.md` | Power & Grid Infrastructure | 2924407 (ACTIVE) | Heat score 45+ — LIVE |
| `defense-epc-sequence.md` | Defense | TBD — create campaign | Heat score 55+ |
| `nuclear-epc-sequence.md` | Nuclear & Critical Minerals | TBD — create campaign | Heat score 45+ |

---

## How to Activate a New Campaign

1. Create a new Smartlead campaign
2. Set sending domain (3-week warmup required — do this first)
3. Copy email bodies from the sequence file into Smartlead
4. Set sending cadence: Day 0 / Day 3 / Day 7 / Day 14
5. Wire Apollo enrichment for `{FirstName}` and `{Company}` variables
6. Pull leads from Airtable contacts filtered by sector
7. Activate when ECAS Slack alert fires for that sector

---

## Planned: Auto-generation via ECAS Engine

Target endpoint: `POST /admin/generate-sequence?sector=Defense`

The ECAS engine has all the context needed (sector heat score, top tickers, signal breakdown, ICP profile) to generate a sector-specific sequence via Claude and push it directly to a Smartlead campaign via API. This removes the manual step of copying sequence files into the UI.

See plan in `docs/sequence-generator-plan.md`.
