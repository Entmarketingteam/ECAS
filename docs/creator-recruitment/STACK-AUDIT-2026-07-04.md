# ENT Creator Recruitment Stack — Full Audit & Gap Report
# Generated: 2026-07-04

## WHAT IS ACTUALLY LIVE ✅

### Infrastructure
- Supabase (ent-agency-automation): LIVE — 75+ tables, active data
- error_logs + error_logs_archive: CREATED TODAY ✅ (RLS on, 4 indexes)
- n8n: LIVE at entagency.app.n8n.cloud — 44 active workflows
- ECAS Railway: LIVE — 39 scheduler jobs running
- ContractMotion site: LIVE
- agent.entagency.co: LIVE (tunnel restored)

### Secrets (all present in Doppler ent-agency-automation/dev)
- APIFY_API_TOKEN ✅
- SMARTLEAD_API_KEY + CAMPAIGN_ID ✅
- N8N_URL + N8N_API_KEY ✅
- SUPABASE_URL + SUPABASE_SERVICE_KEY ✅
- ANTHROPIC_API_KEY ✅
- ENT_BOT_SLACK_BOT_TOKEN ✅ (channel C0B300WMPM3)
- AIRTABLE_API_KEY + BASE_ID ✅
- APOLLO_API_KEY ✅ (in ecas/dev)

### n8n Workflows active and relevant
- ENT Dream 100 Full Pipeline (UBIZDzq0fJhm1X3F) ✅
- ENT Creator Vetting Auto-Trigger ✅
- Smartlead Signal Intelligence ✅
- ENT Brief Intake Agent ✅
- ENT Gmail Watch → Action ✅

---

## WHAT IS INCOMPLETE / BROKEN ❌

### 1. Global Error Handler (CRITICAL)
- ID: 1M1oWq0vfbKgOBzE
- Status: INACTIVE
- Missing: Supabase insert node, severity IF branch
- Risk: ALL n8n workflow failures are silent — no log, no audit

### 2. pg_cron NOT installed
- Extension not enabled on this Supabase project
- Weekly retention job cannot be scheduled
- Fix: Must enable via Supabase Dashboard → Database → Extensions → pg_cron
- Workaround: n8n weekly cron workflow can replace it

### 3. Creator Recruitment Schema — NOT BUILT
- The v2.6-v4.2 spec describes a NEW system
- No tables exist: prospects, enrichment_queue, outreach_log, replies, scores, nurture_state
- No AGENTS.md, no .claude/ harness, no sub-agent files
- No repo exists for this new system

### 4. Unipile — NOT in stack
- Spec requires Unipile for DM outreach (Instagram/LinkedIn)
- No Unipile credentials anywhere in Doppler
- No Unipile n8n nodes
- Alternative: current stack uses Smartlead (email only)

### 5. ECAS Doppler placeholders (ecas/dev)
- PROXYCURL_API_KEY: empty → Contact Enricher (07) fails at Proxycurl node
- FULLENRICH_API_KEY: empty
- FMP_API_KEY: empty → earnings_transcripts job may fail
- CLOSE_CRM_API_KEY: empty

### 6. ECAS Smartlead warmup — NOT done
- 3 sending domains still need Google Workspace + mailbox setup
- contractmotionai.com DNS SPF record missing
- Campaigns still sending from marketingteam@nickient.com (wrong)

### 7. Airtable manual items — NOT done (ECAS)
- Linked record fields not created
- Formula fields not created
- "Table 1" not deleted

### 8. ENT Dream 100 Weekly Scout — INACTIVE (LDdksr9L7oUsRPI4)
- Scout is disabled, pipeline runs without fresh discovery input

### 9. Mavely Daily Auth — INACTIVE (3gYfgPzMu6wZ1OEZ)
- Mavely sync may be stale

### 10. No chaos engineering / testing harness
- No staging environment
- No test workflows
- No circuit breakers in Supabase (service_status table)

---

## BULLET HOLES (what will break at scale)

1. Silent failures — Global Error Handler inactive = zero visibility into workflow errors
2. No dedup on prospects — running discovery twice will create duplicate outreach
3. Smartlead rate limits — no circuit breaker, will hit limits silently
4. Apify caching not implemented — every discovery run hits API fresh = cost bleed
5. No reply detection loop — Smartlead replies not feeding back into any agent loop
6. No consent/opt-out table — legal risk at 300+ prospects
7. No token cost tracking — Claude calls unmetered
8. No staging DB — all testing hits production Supabase
9. pg_cron not enabled — error_logs will never auto-archive
10. PROXYCURL not configured — enrichment is broken right now

---

## BUILD PRIORITY ORDER

### DO NOW (no approval needed, safe)
1. Upgrade + activate Global Error Handler in n8n ← NEXT
2. Create n8n weekly retention workflow (pg_cron replacement)
3. Save v2.6-v4.2 spec docs to ECAS/docs/creator-recruitment/
4. Scaffold creator recruitment repo + .claude/CLAUDE.md harness
5. Create core prospects schema in Supabase

### NEEDS YOUR ACTION (requires dashboard/UI access)
- Enable pg_cron: Supabase Dashboard → Database → Extensions
- Fix ECAS Doppler: set PROXYCURL_API_KEY, FMP_API_KEY, FULLENRICH_API_KEY
- DNS: add SPF record to contractmotionai.com
- Activate ENT Dream 100 Weekly Scout

### NEEDS DECISION
- Unipile vs alternative for DM outreach
- Which creators to target first (feed into discovery)
- Opt-out/consent approach
