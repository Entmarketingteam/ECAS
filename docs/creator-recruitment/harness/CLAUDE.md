<!-- PRESERVATION SAFETY NOTE (2026-08-04): Recovered harness reference only. Kept under docs/ so it does not auto-load as a live agent harness. Do not use for live outreach without consent_log checks and explicit approval gates. -->

# ENT Creator Recruitment — Claude Code Harness

Project: ENT Agency Creator Recruitment & Outbound Automation
Tech: n8n, Supabase, Smartlead, Anthropic, Apify
Doppler: ent-agency-automation/dev

## Rules
- Doppler secrets only — never hardcode credentials
- RLS enforced on all DB writes
- Personalization MUST reference live data (bio, recent post, follower count)
- Fogarty flow: seed → nurture → performance affiliate
- Token rule: Haiku for triage/scoring, escalate to Sonnet only if confidence <70% or complex negotiation
- Max loop iterations: 5 per nurture cycle
- Always log errors to error_logs table
- Dedup on platform+handle before inserting prospects
- Check consent_log before any outreach

## Pipeline
Apify discovery → dedup → prospects table → enrichment_queue → scoring → outreach_log → replies → nurture_state

## Tables (Supabase guypsezcriypwyvodmhq / ent-agency-automation)
- prospects: discovered creators with UNIQUE(platform, handle)
- enrichment_queue: pending enrichment jobs
- outreach_log: sent messages (email + DM)
- replies: inbound replies with sentiment
- nurture_state: per-prospect loop state and memory
- consent_log: opt-out tracking (ALWAYS check before outreach)
- error_logs: all workflow errors (RLS + pg_cron retention active)

## Escalate to human when
- Prospect replies with interest (positive sentiment)
- Negotiation exceeds 3 iterations
- Confidence score <50% after Sonnet
- Any legal/compliance question
- consent_log shows opted_out or do_not_contact
