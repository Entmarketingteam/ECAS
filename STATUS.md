# ECAS / ContractMotion — STATUS

**Updated:** 2026-06-05  
**Railway:** https://ecas-scraper-production.up.railway.app  
**Brand:** ContractMotion.com

## Live
- 6 sector Smartlead campaigns active + 4 niche test campaigns DRAFTED (gated on enrichment)
- h1b_pipeline job daily 4am UTC (H-1B discover → Supabase→Airtable projects bridge)
- populate_projects bridge LIVE (epc_company_leads → Airtable projects)
- 12/14 ContractMotion inboxes at 99–100% warmup reputation

## Blockers
- 2 SMTP failures need new Google app passwords: `karlee@contractmotionai.com`, `ethan.atchley@contractmotion.com`
- General EPC campaign `3399657` DRAFTED — confirm pay-on-results offer before START
- Test campaigns `3402445`–`3402455` DRAFTED — gated on email enrichment

## Next
- Fix SMTP app passwords in Smartlead
- Enrich sendable contacts for test campaigns → manual START approval
- Run `POST /admin/run/h1b_pipeline` on demand when needed

## Hermes integration
- `gtm pulse` / `pipeline status` → ECAS `/admin/status`
- `status on ECAS` → this file (or RESUME-HERE.md fallback)
- Morning briefing pulls ECAS admin status automatically
