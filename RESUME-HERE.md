---
project: ECAS / ContractMotion
status: blocked on sending domains
last_updated: 2026-04-30
---

# RESUME-HERE — ECAS / ContractMotion

> Signal-driven contract acquisition for mid-tier EPCs, branded as ContractMotion.com

## Last session state

4 Smartlead campaigns active (Power/Grid, Data Center, Water, Industrial). Defense/Nuclear pending. Scraper running on Railway at `ecas-scraper-production.up.railway.app`.

---

## Blockers

1. **Buy sending domains** [USER ACTION] — blocking warmup timeline; can't scale outbound until done
2. **Defense/Nuclear campaign launch** [BLOCKED on domains] — copy + list ready, waiting on warm inboxes
3. **Decide ContractMotion.com landing page scope** — current site is placeholder

---

## Quick Commands

```bash
# Tail Railway scraper logs
cd ~/projects/ECAS && railway logs

# Check Smartlead campaign stats via API
doppler run --project example-project --config prd -- \
  curl -s "https://server.smartlead.ai/api/v1/campaigns?api_key=$SMARTLEAD_API_KEY"
```

## Resume Prompt

```
Read RESUME-HERE.md in Entmarketingteam/ECAS and tell me what's outstanding.
Then help me move on the next blocker.
```
