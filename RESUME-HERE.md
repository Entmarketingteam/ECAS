---
project: ECAS / ContractMotion
status: live + 6 campaigns running; homepage just morphed
last_updated: 2026-05-16
---

# RESUME-HERE — ECAS / ContractMotion

> Signal-driven contract acquisition, branded as ContractMotion.com.
> Verify against `git log origin/main` before trusting any "all set" claim — local state lies, remote is durable.

## Canonical path

**`~/projects/ECAS`** — production exception to the `~/Desktop/` convention. Never recreate `~/Desktop/ECAS` (a prior symlink caused confusion). See `~/CONVENTIONS.md`.

## Current state (2026-05-16)

**LIVE infrastructure:**
- 6 Smartlead campaigns active: Power/Grid (3005694), Data Center (3040599), Water (3040600), Industrial (3040601), Defense (3095136), Drone/Public Safety (3103531)
- Railway: `ecas-scraper-production.up.railway.app`
- n8n: 5 ECAS workflows + 2 new (signal-audit webhook, FERC sniper) active on entagency.app.n8n.cloud
- Sending domains: aicontractmotion.com, getcontractmotion.com, usecontractmotion.com, contractmotionai.com, contractmotion.com — all 99–100% reputation except 2 SMTP failures needing new Google app passwords

**Website (separate repo at `~/Desktop/contractmotion-site`):**
- Homepage morphed to horizontal "Contract Intelligence Platform" thesis (was "Signal Intelligence for EPC Contractors")
- 4 new vertical pages added: `/custom-builders`, `/commercial-trades`, `/document-destruction`, `/govcon-services`
- Existing 8 EPC vertical pages still live
- Sitemap + nginx routes updated
- Draft copy + positioning saved to `~/Desktop/contractmotion-site/campaigns/horizontal-morph/`

**Latest commits this repo:**
- `2bb1630` docs: ContractMotion engine architecture spec (Mermaid + 4-phase) — 2026-05-16
- `0b4fa9d` Update ECAS Intelligence: new signal-driven niches + n8n webhook handlers + Data Center/Industrial sequences
- `08282f9` Replace Proxycurl + Zerobounce with Findymail in workflow 07
- `ab56878` fix: replace dead FERC EFTS endpoint with Federal Register API

---

## Cross-tool sync (Claude + Gemini)

**Don't trust "everything is saved" without verifying remote.** On 2026-05-16 a Gemini session claimed to have committed + pushed `docs/ContractMotion-Engine-Architecture.md` — but it was still untracked locally and not on remote until a later Claude session actually pushed it (commit 2bb1630). Gemini's local-only view looked correct but wasn't durable.

**Rule:** before believing any agent's "done" claim on this repo:
```bash
cd ~/projects/ECAS && git fetch origin main && git log origin/main --oneline -3
```

If the expected commit isn't in `origin/main`, it's not durable.

---

## Outstanding work

### High leverage
1. **Wire Wave 2 C8 sequences into `/custom-builders`** — draft in `~/Desktop/cold-traffic-clusters/wave-2-c8-refined-emails.md`. Create Smartlead campaign + Airtable signal feed (n8n workflow `m20l881jFzyjc40A` is the template).
2. **Surface existing lead magnets on matching vertical pages:**
   - `HIPAA Document Disposal Gap Checklist` (docs/hipaa-document-disposal-gap-checklist.md) → `/document-destruction`
   - `2026 Retail Anchor Vacancy & NNN Recovery Map` → `/commercial-trades`
3. **Build `/govcon-services` engine path** — first sequence + SAM.gov + USAspending signal feed. This is the only true greenfield vertical.

### Operational
4. **Fix 2 SMTP failures:** `karlee@contractmotionai.com`, `ethan.atchley@contractmotion.com` need new Google app passwords (Google Account → Security → App Passwords)
5. **Build the missing `epc_company_leads → Airtable projects` bridge** (CLAUDE.md flags this — leads aren't flowing to enrichment yet)

### Reference / proof
6. **Fill placeholder testimonial slots** on all 4 new vertical pages — drafts at `~/Desktop/contractmotion-site/campaigns/horizontal-morph/`. Self-score 52/70; blockers are Proof + Urgency.

---

## Quick Commands

```bash
# Tail Railway scraper logs
cd ~/projects/ECAS && railway logs

# Check Smartlead campaign stats
doppler run --project ecas --config dev -- \
  curl -s "https://server.smartlead.ai/api/v1/campaigns?api_key=$SMARTLEAD_API_KEY"

# Verify ECAS remote state (do this before trusting any "all set" claim)
cd ~/projects/ECAS && git fetch origin main && git log origin/main --oneline -5

# Audit machine for repo location issues
~/.claude/scripts/repo-audit.sh
```

## Resume Prompt

```
Read RESUME-HERE.md in ~/projects/ECAS and tell me current state + what's next.
Then verify remote with: git fetch origin main && git log origin/main --oneline -3
```
