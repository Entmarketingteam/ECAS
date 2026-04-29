# ECAS — Gemini CLI Context

This file is loaded automatically by Gemini CLI via the superpowers plugin (gemini-extension.json).
All context is identical to CLAUDE.md — read that file for full project state.

## Quick Reference

**Doppler:** `doppler run --project ecas --config dev -- <command>`

**Primary LLM in codebase:** Claude (`claude-3-5-sonnet-20241022`) via `ANTHROPIC_API_KEY`
- All AI calls in `intelligence/`, `enrichment/`, `verification/`, `outreach/` use Anthropic
- To switch a call to Gemini, replace `anthropic.Anthropic()` with Google GenAI client and update model ref in `config.py`

**Run lead engine:**
```bash
doppler run --project ecas --config dev -- python3 signals/epc_lead_engine.py --sector all
```

**Critical gap to fix:**
`epc_company_leads` (Supabase) → Airtable `projects` bridge is missing.
Build `populate_projects.py` that reads `epc_company_leads` and upserts to Airtable projects table with sector-based campaign routing.

**Sector → Smartlead campaign:**
- Power & Grid → `3005694`
- Data Center → `3040599`
- Water & Wastewater → `3040600`
- Industrial & Manufacturing → `3040601`
- Defense & Federal → `3095136`
- Drone & Public Safety → `3103531`

See CLAUDE.md for full context.
