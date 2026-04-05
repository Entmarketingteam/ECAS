"""
enrichment/diagnosis.py
LLM-powered error diagnosis + smart Slack alerts.
When retries exhaust, Claude reads the error context and generates actionable diagnostics.
"""

import json
import logging
import os
from datetime import datetime

import requests

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
SLACK_ACCESS_TOKEN = os.environ.get("SLACK_ACCESS_TOKEN", "")
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL", "#ecas-signals")
RAILWAY_URL = os.environ.get("RAILWAY_STATIC_URL", "https://ecas-scraper-production.up.railway.app")


def diagnose_error(error: Exception, context: dict) -> str:
    """
    Send error + context to Claude for diagnosis.
    Returns human-readable diagnosis with root cause + suggested fix.
    Falls back to raw error if Claude is unavailable.
    """
    if not ANTHROPIC_API_KEY:
        return f"Claude diagnosis unavailable (no API key). Raw error: {error}"

    auto_fix_log = getattr(error, "auto_fix_log", [])

    prompt = f"""You are an SRE diagnosing a pipeline failure in the ECAS outbound system.
This system enriches B2B leads via Apollo + Findymail and enrolls them in Smartlead campaigns.

ERROR: {type(error).__name__}: {error}

CONTEXT:
- Stage: {context.get('stage', 'unknown')}
- API: {context.get('api', 'unknown')}
- Company: {context.get('company', 'N/A')}
- Batch progress: {context.get('progress', 'N/A')}

AUTO-FIX ATTEMPTS:
{chr(10).join(f'  {i+1}. {a}' for i, a in enumerate(auto_fix_log)) or '  None'}

Provide in this exact format:
ROOT CAUSE: (1-2 sentences — what broke and why)
WHAT WAS TRIED: (list auto-fix attempts)
SUGGESTED FIX: (specific steps — CLI commands, URLs, config changes)
URGENCY: (critical/high/medium/low)

Be specific. Include exact commands or URLs where possible. Keep it under 200 words."""

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["content"][0]["text"]
    except Exception as e:
        logger.warning(f"[Diagnosis] Claude unavailable: {e}")
        return (
            f"Claude diagnosis unavailable ({e}).\n"
            f"Raw error: {type(error).__name__}: {error}\n"
            f"Auto-fix attempts: {auto_fix_log}"
        )


def post_slack_alert(message: str, channel: str = None) -> bool:
    """Post a message to Slack. Returns True on success."""
    token = SLACK_ACCESS_TOKEN
    if not token:
        logger.warning("[Slack] No SLACK_ACCESS_TOKEN — logging to stdout instead")
        logger.critical(f"[SLACK FALLBACK]\n{message}")
        return False

    try:
        resp = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"channel": channel or SLACK_CHANNEL, "text": message, "unfurl_links": False},
            timeout=10,
        )
        data = resp.json()
        if not data.get("ok"):
            logger.warning(f"[Slack] Post failed: {data.get('error')}")
            return False
        return True
    except Exception as e:
        logger.warning(f"[Slack] Error: {e}")
        logger.critical(f"[SLACK FALLBACK]\n{message}")
        return False


def escalate(error: Exception, context: dict) -> None:
    """
    Full escalation: diagnose with Claude → post rich Slack alert.
    Called when all retries and fallbacks are exhausted.
    """
    diagnosis = diagnose_error(error, context)

    company = context.get("company", "batch run")
    stage = context.get("stage", "unknown")
    progress = context.get("progress", "N/A")

    message = (
        f"*ECAS Pipeline — Escalation Required*\n\n"
        f"*{stage}* failed for *{company}*\n"
        f"Progress: {progress}\n\n"
        f"```{diagnosis}```\n\n"
        f"_Trigger manual retry:_\n"
        f"`curl -X POST {RAILWAY_URL}/api/enrich-and-enroll "
        f'-H "Content-Type: application/json" '
        f"-d '{{\"company_filter\": \"{company}\", \"min_heat\": 0}}'`"
    )

    post_slack_alert(message)
    logger.error(f"[Escalation] {stage} failed for {company}: {diagnosis}")


def post_summary(results: dict) -> None:
    """Post pipeline completion summary to Slack."""
    enrolled = results.get("contacts_enrolled", 0)
    found = results.get("contacts_found", 0)
    companies = results.get("companies_processed", 0)
    skipped = results.get("skipped", 0)
    errors = results.get("errors", [])
    campaigns = results.get("campaigns", {})
    status = results.get("status", "unknown")

    # Build campaign breakdown
    campaign_lines = []
    for cid, count in campaigns.items():
        campaign_lines.append(f"  • Campaign `{cid}`: {count} leads")

    error_section = ""
    if errors:
        error_section = f"\n*Errors ({len(errors)}):*\n" + "\n".join(f"  • {e}" for e in errors[:5])
        if len(errors) > 5:
            error_section += f"\n  _...and {len(errors) - 5} more_"

    emoji = "✅" if status == "complete" and not errors else "⚠️" if errors else "ℹ️"

    message = (
        f"{emoji} *ECAS Enrichment Pipeline — {status.upper()}*\n\n"
        f"• Companies processed: {companies} ({skipped} skipped)\n"
        f"• Contacts found: {found}\n"
        f"• Contacts enrolled: {enrolled}\n"
    )
    if campaign_lines:
        message += "*Campaigns:*\n" + "\n".join(campaign_lines) + "\n"
    message += error_section

    post_slack_alert(message)


def post_preflight_alert(preflight_result: dict) -> None:
    """Post pre-flight check results to Slack when issues are found."""
    status = preflight_result["status"]
    failures = preflight_result.get("failures", {})

    if status == "healthy":
        return  # Don't spam Slack on healthy runs

    emoji = "🛑" if status == "blocked" else "⚠️"
    action = "Pipeline BLOCKED" if status == "blocked" else "Pipeline running DEGRADED"

    lines = [f"{emoji} *ECAS Pre-Flight Check — {action}*\n"]
    for service, detail in failures.items():
        lines.append(f"• *{service}*: {detail.get('detail', 'unknown')}")

    if status == "blocked":
        lines.append("\n_Pipeline will not run until critical services are restored._")

    post_slack_alert("\n".join(lines))
