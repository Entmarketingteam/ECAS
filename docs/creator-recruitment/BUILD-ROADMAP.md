# ENT Creator Recruitment & Outbound System
# Spec versions v2.6 through v4.2 — Build Roadmap Reference
# Saved: 2026-07-04 | Status: Reference docs — implement in sequence

---

## Build Sequence

### DONE ✅ (2026-07-04)
- error_logs + error_logs_archive tables created in Supabase
- RLS enabled on both tables
- 4 indexes on error_logs (severity, resolved, timestamp, workflow)
- Global Error Handler upgraded (Error Trigger → Supabase log → Slack alert)
- 15 active workflows wired to Global Error Handler
- Stack audit saved to STACK-AUDIT-2026-07-04.md

### NEXT — Requires Supabase Dashboard
- Enable pg_cron extension:
  Supabase Dashboard → Database → Extensions → search pg_cron → Enable
  Then the cron SQL in ecas_schema_clean.sql can run

### NEXT — Requires Doppler config (ecas/dev)
- Set PROXYCURL_API_KEY (Contact Enricher 07 is broken without it)
- Set FMP_API_KEY (earnings_transcripts job)
- Set FULLENRICH_API_KEY

### NEXT — Requires DNS access (contractmotionai.com)
- Add SPF TXT record: v=spf1 include:_spf.google.com -all

### PHASE 2 — Creator Recruitment Schema (not yet built)
Tables needed (see v2.6 spec):
- prospects (id, platform, handle, followers, niche, score, tier, status, created_at)
- enrichment_queue (prospect_id, status, source, raw_data, enriched_at)
- outreach_log (prospect_id, channel, message, sent_at, campaign_id, status)
- replies (outreach_id, content, received_at, sentiment, action_taken)
- nurture_state (prospect_id, iteration, last_contact, next_action, memory_summary)
- scores (prospect_id, engagement_rate, brand_fit, tier, confidence, scored_at)

### PHASE 3 — Claude Harness
- Create .claude/ directory in creator recruitment repo
- CLAUDE.md (system spec)
- agents/verifier.md
- agents/orchestrator.md
- skills/personalize_dm/SKILL.md
- scripts/run_nurture_loop.sh

### PHASE 4 — n8n Workflows
- Discovery pipeline (Apify → dedup → prospects table)
- Enrichment queue processor
- Scoring workflow (Haiku → confidence gate → Sonnet if <70%)
- Outreach router (Smartlead for email, Unipile for DM when added)
- Reply listener + triage
- Daily digest to Slack

### PHASE 5 — Multi-agent orchestration (v4.0)
- Only after Phase 4 loops are proven

### PHASE 6 — Debugging + Chaos (v4.2 / v3.5)
- agent_traces table
- Chaos workflow (10% failure injection)
- Weekly staging test runs

---

## Bullet Holes (risks to fix before scale)

1. No dedup on prospects — will create duplicate outreach ← fix in schema with UNIQUE constraint
2. No consent/opt-out table ← add before any volume outreach
3. No reply detection loop ← Smartlead webhook → n8n → replies table
4. Apify caching not implemented ← dedupe by handle+date before insert
5. No token cost tracking ← add context.tokens_used to error_logs or separate table
6. No staging DB ← create Supabase branch or separate project
7. Unipile not in stack ← evaluate vs direct Instagram Graph API
8. PROXYCURL broken ← ECAS enrichment dead until key set
9. pg_cron not enabled ← weekly retention won't run
10. 3 sending domains not warmed ← Smartlead still using personal inbox

---

## Spec File Index
- v2.6: PRD + TDD + Spec + Harness Code (full system blueprint)
- v3.0: pg_cron retention with error handling
- v3.1: pg_cron retry logic (5s/30s/120s backoff, 3 attempts)
- v3.2: n8n Global Error Handler setup ← IMPLEMENTED ✅
- v3.5: Chaos engineering strategies (staging only)
- v4.0: Multi-agent orchestration (Hierarchical + Fan-out + Event-driven)
- v4.2: Multi-agent debugging (agent_traces table, VerifierAgent debug mode)
