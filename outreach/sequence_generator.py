"""
outreach/sequence_generator.py
Generates sector-specific cold email sequences via Claude, using live signal data.
Optionally creates a Smartlead campaign and uploads all emails automatically.

Usage:
    # Generate only (preview)
    seq = generate_sequence("Defense")

    # Generate + push to Smartlead
    result = generate_and_push("Defense", from_name="Ethan", from_email="ethan@contractmotion.com")
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    ANTHROPIC_API_KEY, TARGET_SECTORS, ICP, TIMELINE_PHASES, SCORING_WEIGHTS
)

logger = logging.getLogger(__name__)

# Day delays for each email in the sequence
SEQUENCE_DELAYS = [0, 3, 7, 14]

SEQUENCE_PROMPT = """You are a B2B cold email copywriter. You write concise, signal-driven outreach for a marketing agency called ContractMotion that helps mid-tier EPC (engineering, procurement, construction) contractors win government and utility contracts.

ContractMotion's positioning: "We get you on the short list before the RFP drops."
Core offer: Full-year engagement at $66K. ROI framing = one new pre-qualification that leads to a contract pays for it many times over.
Tone: Direct, credible, no hype. Never use marketing buzzwords. Sound like a smart insider, not a vendor.

## Current Sector Intelligence

Sector: {sector}
Description: {description}
Heat Score: {heat_score}/100
Phase: {phase} — {phase_description}
Months to procurement unlock: {months_to_unlock}

Signal Breakdown:
- Politician trading activity: {politician_score}/25 pts
- Institutional investor positioning: {hedge_fund_score}/25 pts
- Government contracts awarded: {contract_score}/25 pts
- FERC/news signals: {ferc_score}/15 pts

Top Signal Context:
{signal_context}

## ICP (who we're emailing)

Company type: EPC contractors in {sector} adjacent work
Revenue range: $20M–$300M
Titles: VP Operations, VP Business Development, President, CEO, Owner, Director of BD, COO
States: VA, TX, NC, GA, FL, MD, PA

## Task

Write a 4-email cold email sequence (Day 0, Day 3, Day 7, Day 14) targeting these EPC contractors.

Rules:
- Email 1 (Day 0): Hook using the sector signal. Reference that their company appeared in our scan. Don't name specific politicians or funds — just reference the activity. Offer a "one-page breakdown" as the CTA. Under 150 words.
- Email 2 (Day 3): Competitive intelligence angle. 3 competitors updated their positioning, now showing up in procurement searches. The gap we fix. Soft CTA: 10-minute call. Under 130 words.
- Email 3 (Day 7): Math anchor. One new pre-qualification → contract value → gross profit at 20% margin → compare to $66K engagement cost. Breakup framing: "if Q2 is better, fine." Under 120 words.
- Email 4 (Day 14): True breakup. Door open. Leave them with one sector-specific urgency fact. Under 110 words.

Each email uses {FirstName} and {Company} as the only personalization variables.
Sign off with: [Your Name]

Return ONLY valid JSON in this exact format:
{{
  "emails": [
    {{
      "day": 0,
      "subject": "subject line here",
      "body": "full email body here with \\n for line breaks"
    }},
    {{
      "day": 3,
      "subject": "subject line here",
      "body": "full email body here"
    }},
    {{
      "day": 7,
      "subject": "subject line here",
      "body": "full email body here"
    }},
    {{
      "day": 14,
      "subject": "subject line here",
      "body": "full email body here"
    }}
  ]
}}"""


def _get_signal_context(sector: str) -> str:
    """Pull recent signals from Airtable for prompt context."""
    try:
        from storage.airtable import get_client
        at = get_client()
        signals = at.get_signals_by_sector(sector, days=30)
        if not signals:
            return "No recent signals in last 30 days — sector is early stage."

        lines = []
        for s in signals[:5]:
            f = s.get("fields", {})
            sig_type = f.get("signal_type", "")
            company = f.get("company_name", "")
            hook = f.get("outreach_hook") or f.get("summary", "")
            score = f.get("confidence_score", 0)
            if hook:
                lines.append(f"- [{sig_type}] {company}: {hook} (confidence: {score})")
            elif company:
                lines.append(f"- [{sig_type}] {company} (confidence: {score})")

        return "\n".join(lines) if lines else "Signals present but no detail available."
    except Exception as e:
        logger.warning(f"[SequenceGen] Could not fetch signal context: {e}")
        return "Signal data temporarily unavailable."


def _get_score_components(sector: str) -> dict:
    """Get component scores for prompt context."""
    try:
        from intelligence.sector_scoring import (
            score_politician_signal, score_hedge_fund_signal,
            score_contract_signal, score_airtable_signals
        )
        return {
            "politician": round(score_politician_signal(sector) * SCORING_WEIGHTS.get("politician_signal", 0.25), 1),
            "hedge_fund": round(score_hedge_fund_signal(sector) * SCORING_WEIGHTS.get("hedge_fund_signal", 0.25), 1),
            "contract": round(score_contract_signal(sector) * SCORING_WEIGHTS.get("contract_signal", 0.25), 1),
            "ferc": round(score_airtable_signals(sector) * (
                SCORING_WEIGHTS.get("ferc_signal", 0.10) + SCORING_WEIGHTS.get("news_signal", 0.05)
            ), 1),
        }
    except Exception as e:
        logger.warning(f"[SequenceGen] Could not get component scores: {e}")
        return {"politician": 0, "hedge_fund": 0, "contract": 0, "ferc": 0}


def generate_sequence(sector: str) -> dict:
    """
    Generate a 4-email cold email sequence for a sector using live signal data.

    Returns:
        {
            "sector": str,
            "heat_score": float,
            "phase": str,
            "emails": [{"day": int, "subject": str, "body": str}, ...]
            "generated_at": str
        }
    """
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not set")

    sector_cfg = TARGET_SECTORS.get(sector)
    if not sector_cfg:
        available = list(TARGET_SECTORS.keys())
        raise ValueError(f"Unknown sector '{sector}'. Available: {available}")

    # Get live data
    try:
        from intelligence.sector_scoring import calculate_sector_heat
        score_data = calculate_sector_heat(sector)
    except Exception as e:
        logger.warning(f"[SequenceGen] Scoring failed, using defaults: {e}")
        score_data = {"heat_score": 0, "phase": "early_signal", "components": {}}

    heat_score = score_data.get("heat_score", 0)
    phase = score_data.get("phase", "early_signal")
    phase_cfg = TIMELINE_PHASES.get(phase, {})
    components = _get_score_components(sector)
    signal_context = _get_signal_context(sector)

    # Build prompt
    prompt = SEQUENCE_PROMPT.format(
        sector=sector,
        description=sector_cfg.get("description", ""),
        heat_score=heat_score,
        phase=phase.replace("_", " ").title(),
        phase_description=phase_cfg.get("description", ""),
        months_to_unlock=phase_cfg.get("months_to_unlock", "unknown"),
        politician_score=components["politician"],
        hedge_fund_score=components["hedge_fund"],
        contract_score=components["contract"],
        ferc_score=components["ferc"],
        signal_context=signal_context,
    )

    # Call Claude
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    logger.info(f"[SequenceGen] Generating sequence for '{sector}' (heat: {heat_score})")

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()

    # Parse JSON — strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"[SequenceGen] JSON parse failed: {e}\nRaw: {raw[:500]}")
        raise ValueError(f"Claude returned invalid JSON: {e}")

    emails = parsed.get("emails", [])
    if len(emails) != 4:
        raise ValueError(f"Expected 4 emails, got {len(emails)}")

    logger.info(f"[SequenceGen] Generated {len(emails)} emails for '{sector}'")

    return {
        "sector": sector,
        "heat_score": heat_score,
        "phase": phase,
        "emails": emails,
        "signal_context": signal_context,
        "generated_at": datetime.utcnow().isoformat(),
    }


def generate_and_push(
    sector: str,
    from_name: str,
    from_email: str,
    campaign_name: str = None,
) -> dict:
    """
    Generate sequence + create Smartlead campaign + upload all emails.

    Returns:
        {
            "sequence": {...},
            "campaign_id": str,
            "campaign_name": str,
            "emails_uploaded": int,
            "smartlead_url": str
        }
    """
    from outreach.smartlead import create_campaign, upload_sequence

    # Generate
    sequence = generate_sequence(sector)

    # Campaign name default
    if not campaign_name:
        phase_label = sequence["phase"].replace("_", " ").title()
        campaign_name = f"ECAS — {sector} EPC 2026 [{phase_label}]"

    # Create Smartlead campaign
    campaign_id = create_campaign(campaign_name, from_name, from_email)
    logger.info(f"[SequenceGen] Created Smartlead campaign {campaign_id}: {campaign_name}")

    # Upload sequence emails
    uploaded = upload_sequence(campaign_id, sequence["emails"])
    logger.info(f"[SequenceGen] Uploaded {uploaded} emails to campaign {campaign_id}")

    return {
        "sequence": sequence,
        "campaign_id": campaign_id,
        "campaign_name": campaign_name,
        "emails_uploaded": uploaded,
        "smartlead_url": f"https://app.smartlead.ai/app/email-campaign/{campaign_id}/sequence",
    }
