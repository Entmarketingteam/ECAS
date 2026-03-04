"""
intelligence/claude_extractor.py
Uses Claude to extract structured insights from raw signals.
Processes unprocessed signals from Airtable and enriches them.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

import anthropic

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """You are an intelligence analyst for ECAS — a B2B sales intelligence system targeting mid-tier electrical EPC contractors ($20M-$300M revenue) in the power and grid infrastructure sector.

Analyze this raw signal and extract structured intelligence:

SIGNAL TYPE: {signal_type}
SOURCE: {source}
COMPANY: {company_name}
SECTOR: {sector}
DATE: {signal_date}
CONTENT:
{raw_content}

Extract the following in JSON format:
{{
  "is_relevant": true/false,
  "relevance_reason": "Why this signal matters (or doesn't) for grid EPC vendor opportunities",
  "capex_signal": true/false,
  "estimated_spend_m": null or dollar amount in millions if mentioned,
  "timeline_months": null or estimated months until vendor budgets unlock,
  "target_epc_types": ["types of EPC contractors that would benefit"],
  "geographic_focus": "states/regions affected",
  "key_insight": "One sentence insight for sales team",
  "urgency": "low/medium/high",
  "recommended_action": "Specific action for ECAS outreach team"
}}

Be concise. Only include JSON, no additional text."""


def extract_signal_intel(record: dict) -> dict | None:
    """
    Run Claude extraction on a single Airtable signal record.
    Returns extracted intel dict or None if extraction fails.
    """
    if not ANTHROPIC_API_KEY:
        logger.error("[Claude] ANTHROPIC_API_KEY not set")
        return None

    fields = record.get("fields", {})
    prompt = EXTRACTION_PROMPT.format(
        signal_type=fields.get("signal_type", "unknown"),
        source=fields.get("source", "unknown"),
        company_name=fields.get("company_name", "unknown"),
        sector=fields.get("sector", "unknown"),
        signal_date=fields.get("signal_date", "unknown"),
        raw_content=fields.get("raw_content", "")[:3000],
    )

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text.strip()

        # Parse JSON response
        import json
        # Strip markdown code blocks if present
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        intel = json.loads(text.strip())
        return intel

    except Exception as e:
        logger.error(f"[Claude] Extraction error: {e}")
        return None


def format_notes(intel: dict) -> str:
    """Format extracted intel into a readable notes string for Airtable."""
    lines = []
    if not intel:
        return "Extraction failed."

    if not intel.get("is_relevant"):
        return f"Not relevant: {intel.get('relevance_reason', 'No reason given')}"

    lines.append(f"INSIGHT: {intel.get('key_insight', '')}")
    lines.append(f"URGENCY: {intel.get('urgency', 'unknown').upper()}")

    if intel.get("capex_signal"):
        spend = intel.get("estimated_spend_m")
        lines.append(f"CAPEX SIGNAL: Yes" + (f" (~${spend}M)" if spend else ""))

    if intel.get("timeline_months"):
        lines.append(f"TIMELINE: ~{intel['timeline_months']} months to budget unlock")

    if intel.get("geographic_focus"):
        lines.append(f"GEOGRAPHY: {intel['geographic_focus']}")

    epc_types = intel.get("target_epc_types", [])
    if epc_types:
        lines.append(f"EPC TYPES: {', '.join(epc_types)}")

    if intel.get("recommended_action"):
        lines.append(f"ACTION: {intel['recommended_action']}")

    return "\n".join(lines)


def process_unprocessed_signals(batch_size: int = 20) -> dict:
    """
    Pull unprocessed signals from Airtable, run Claude extraction,
    and update the records with extracted notes.
    """
    from storage.airtable import get_client
    at = get_client()

    records = at.get_unprocessed_signals(limit=batch_size)
    logger.info(f"[Claude] Processing {len(records)} unprocessed signals")

    processed = 0
    skipped = 0

    for record in records:
        record_id = record.get("id")
        fields = record.get("fields", {})

        # Skip if no content
        if not fields.get("raw_content"):
            at.mark_signal_processed(record_id, "Skipped: no content")
            skipped += 1
            continue

        intel = extract_signal_intel(record)

        if intel and intel.get("is_relevant"):
            notes = format_notes(intel)

            # Update heat score based on urgency
            urgency_boost = {"high": 20, "medium": 10, "low": 0}.get(
                intel.get("urgency", "low"), 0
            )
            current_score = fields.get("heat_score", 0)
            new_score = min(current_score + urgency_boost, 100)

            # Update signal with extracted intel + boosted score
            at._patch("signals_raw", record_id, {
                "processed": True,
                "extracted_at": datetime.utcnow().isoformat(),
                "notes": notes,
                "heat_score": new_score,
            })

            # If high urgency + capex signal → auto-create project record
            if intel.get("urgency") == "high" and intel.get("capex_signal"):
                company = fields.get("company_name", "")
                if company and company not in ("FERC / Grid Sector",):
                    at.upsert_project(
                        company_name=company,
                        sector=fields.get("sector", "Power & Grid Infrastructure"),
                        heat_score=new_score,
                        signal_count=1,
                        priority="high",
                        notes=notes,
                    )
            processed += 1
        else:
            reason = "Not relevant" if intel else "Extraction failed"
            at.mark_signal_processed(record_id, reason)
            skipped += 1

    logger.info(f"[Claude] Processed: {processed} | Skipped: {skipped}")
    return {
        "records_processed": processed,
        "records_skipped": skipped,
        "total_records": len(records),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import json
    result = process_unprocessed_signals(batch_size=5)
    print(json.dumps(result, indent=2))
