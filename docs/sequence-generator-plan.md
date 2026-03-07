# ECAS Sequence Generator — Build Plan

## What It Does

`POST /admin/generate-sequence?sector=Power+%26+Grid+Infrastructure`

1. Pulls current sector heat score + signal breakdown from SQLite/Airtable
2. Pulls ICP profile from config.py
3. Builds a prompt with all that context → Claude generates 4-email sequence
4. Creates a new Smartlead campaign (or updates existing)
5. Uploads all 4 emails with correct day delays
6. Returns campaign ID + preview of generated copy

No manual copy/paste. Signal fires → endpoint called → campaign live.

---

## Architecture

### New file: `outreach/sequence_generator.py`

```python
def generate_sequence(sector: str) -> dict:
    """
    Pull sector context, call Claude, return 4-email sequence dict.
    """
    # 1. Get current sector heat + components
    from intelligence.sector_scoring import calculate_sector_heat
    score_data = calculate_sector_heat(sector)

    # 2. Get recent top signals for context
    from storage.airtable import get_client
    at = get_client()
    signals = at.get_signals_by_sector(sector, days=30)

    # 3. Build prompt with full context
    prompt = _build_sequence_prompt(sector, score_data, signals)

    # 4. Claude generates the sequence
    import anthropic
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    # 5. Parse into structured email dict
    return _parse_sequence(response.content[0].text)


def push_to_smartlead(sequence: dict, campaign_name: str) -> dict:
    """
    Create Smartlead campaign and upload 4 emails.
    Returns campaign_id.
    """
    # POST /api/v1/campaigns (create)
    # POST /api/v1/campaigns/{id}/sequences (add emails with day delays)
```

### New API endpoint: `api/main.py`

```python
@app.post("/admin/generate-sequence")
async def generate_sequence_endpoint(sector: str, push: bool = False):
    """
    Generate a cold email sequence for a sector.
    If push=true, creates Smartlead campaign automatically.
    """
    sequence = generate_sequence(sector)
    if push:
        result = push_to_smartlead(sequence, f"ECAS — {sector} EPC 2026")
        return {"sequence": sequence, "smartlead": result}
    return {"sequence": sequence}
```

---

## Prompt Design

The Claude prompt includes:
- Sector name + description
- Current heat score + phase label
- Top signal components (politician score, contract count, top tickers)
- Recent signal headlines (last 30 days from Airtable)
- ICP profile (revenue range, NAICS, titles, states)
- Existing sequence as style reference
- Output format spec (JSON: subject + body for each of 4 emails)

---

## Smartlead API — What We Need

Endpoints (all authenticated with `SMARTLEAD_API_KEY`):

| Action | Endpoint |
|--------|----------|
| Create campaign | `POST /api/v1/campaigns` |
| Add email sequence | `POST /api/v1/campaigns/{id}/sequences` |
| Add leads | `POST /api/v1/campaigns/{id}/leads` |
| Get campaign status | `GET /api/v1/campaigns/{id}` |

The existing `outreach/smartlead.py` already handles leads. Extend it for campaign creation + sequence upload.

---

## Build Order

1. [ ] Extend `outreach/smartlead.py` — add `create_campaign()` and `upload_sequence()` functions
2. [ ] Write `outreach/sequence_generator.py` — Claude call + sequence parser
3. [ ] Add `/admin/generate-sequence` endpoint to `api/main.py`
4. [ ] Wire phase transition alert to auto-call endpoint (optional — start manual, automate later)
5. [ ] Test: trigger for Defense sector, verify campaign created in Smartlead

---

## When to Build This

Build when:
- Power & Grid campaign has delivered first leads (validates sequence format/tone)
- Defense sector crosses 55/100 (imminent need to activate)
- OR you want to generate sequences for a new niche without touching the codebase

Estimated build: ~4 hours. Blocked on nothing — Smartlead API key is already live.

---

## Alternative: Skill Wrapper

If you want to generate sequences outside of Railway (e.g., for a new client vertical),
wrap this as a Claude Code skill:

```
~/.claude/skills/ecas-sequence-generator.md
```

Trigger: "generate outreach sequence for [niche]"
Input: ICP description + pain points + signal hooks
Output: Formatted 4-email sequence in Smartlead-ready format

This is the portable version — no ECAS engine required. Good for ENT Agency clients
who want signal-aware outreach for their own verticals.
