# Creator Recruitment Source-Map Preservation Manifest — 2026-08-04

## Source
Recovered from dirty local checkout `C:/Users/ejatc/Documents/ECAS` on branch `approval-gate-scaffold`.

## Preserved in this PR
- `docs/creator-recruitment/BUILD-ROADMAP.md`
- `docs/creator-recruitment/STACK-AUDIT-2026-07-04.md`
- `docs/creator-recruitment/harness/CLAUDE.md`
- `docs/creator-recruitment/harness/verifier-agent.md`
- `docs/creator-recruitment/harness/personalize-dm-skill.md`

## Safety handling
- Harness files were moved under `docs/creator-recruitment/harness/` so they are reference material, not an auto-loaded live `.claude` or skill runtime.
- Added safety notes to stop before live n8n changes, Supabase schema/DB writes, Smartlead/outreach sends, DNS changes, Doppler/secret edits, or paid services.
- No secrets were copied. The files name systems and required env var names only.

## Next safe action
Use these docs to create a reviewed implementation issue/PR for a pure, locked-grader schema/test scaffold. Do not run live migrations or outreach until explicitly approved.
