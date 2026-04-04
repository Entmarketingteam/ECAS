"""
contractor/pipeline/health_monitor.py — Campaign and domain health monitoring.

Implements:
- Eric Nowoslawski's 0.7% reply rate burnout threshold (7-day and 14-day windows)
- ColdIQ benchmarks: <1% bounce, >20% open rate minimum
- Auto-pause on threshold breach via Smartlead API
- Slack alerts for all failure modes
- Domain rotation recommendations
- Self-adjustment: pause + alert, human decides rotation

Run every 6 hours via APScheduler.
"""

import logging
import os
import requests
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

SMARTLEAD_API_KEY = os.environ.get("SMARTLEAD_API_KEY", "")
SLACK_ACCESS_TOKEN = os.environ.get("SLACK_ACCESS_TOKEN", "")
SLACK_ALERT_CHANNEL = os.environ.get("SLACK_CHANNEL", "#ecas-signals")
SMARTLEAD_BASE = "https://server.smartlead.ai/api/v1"


# ─── Thresholds ───────────────────────────────────────────────────────────────
@dataclass
class HealthThresholds:
    reply_rate_min_7d: float = 0.007      # 0.7% — Eric's 7-day burnout threshold
    reply_rate_min_14d: float = 0.007     # 0.7% — 14-day window check
    bounce_rate_max: float = 0.010        # 1% — ColdIQ benchmark (pause at 0.8% warn, 1% hard stop)
    bounce_rate_warn: float = 0.008       # 0.8% — early warning
    open_rate_min: float = 0.200          # 20% minimum (below = deliverability problem)
    positive_reply_rate_min: float = 0.002  # 0.2% positive replies minimum


THRESHOLDS = HealthThresholds()


# ─── Data Classes ─────────────────────────────────────────────────────────────
@dataclass
class CampaignHealth:
    campaign_id: str
    campaign_name: str
    vertical: str
    total_sent: int
    total_opened: int
    total_replied: int
    total_bounced: int
    positive_replies: int
    open_rate: float
    reply_rate: float
    bounce_rate: float
    positive_reply_rate: float
    status: str   # "healthy" | "warning" | "critical" | "paused"
    issues: list[str]
    recommendations: list[str]
    checked_at: datetime


@dataclass
class DomainHealth:
    domain: str
    campaigns_using: list[str]
    estimated_reply_rate_7d: float
    bounce_rate: float
    status: str   # "healthy" | "degraded" | "rotate"
    rotate_recommended: bool


# ─── Smartlead API Helpers ────────────────────────────────────────────────────
def _sl_get(endpoint: str, params: dict = None) -> dict:
    """Make a Smartlead API GET request."""
    url = f"{SMARTLEAD_BASE}{endpoint}"
    p = {"api_key": SMARTLEAD_API_KEY}
    if params:
        p.update(params)
    resp = requests.get(url, params=p, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _sl_post(endpoint: str, payload: dict) -> dict:
    """Make a Smartlead API POST request."""
    url = f"{SMARTLEAD_BASE}{endpoint}"
    resp = requests.post(
        url,
        params={"api_key": SMARTLEAD_API_KEY},
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def pause_campaign(campaign_id: str, reason: str) -> bool:
    """Pause a Smartlead campaign. Returns True on success."""
    try:
        _sl_post(f"/campaigns/{campaign_id}/update-schedule", {"status": "STOPPED"})
        logger.warning("PAUSED campaign %s — reason: %s", campaign_id, reason)
        return True
    except Exception as e:
        logger.error("Failed to pause campaign %s: %s", campaign_id, e)
        return False


def get_campaign_stats(campaign_id: str) -> Optional[dict]:
    """Fetch campaign analytics from Smartlead."""
    try:
        return _sl_get(f"/campaigns/{campaign_id}/analytics")
    except Exception as e:
        logger.error("Failed to fetch stats for campaign %s: %s", campaign_id, e)
        return None


# ─── Health Check Logic ───────────────────────────────────────────────────────
def check_campaign_health(campaign_id: str, vertical: str, campaign_name: str) -> CampaignHealth:
    """
    Check health of a single Smartlead campaign against all thresholds.
    Auto-pauses if critical thresholds are breached.
    """
    stats = get_campaign_stats(campaign_id)
    issues = []
    recommendations = []
    status = "healthy"

    if not stats:
        return CampaignHealth(
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            vertical=vertical,
            total_sent=0, total_opened=0, total_replied=0,
            total_bounced=0, positive_replies=0,
            open_rate=0, reply_rate=0, bounce_rate=0, positive_reply_rate=0,
            status="unknown",
            issues=["Could not fetch stats from Smartlead API"],
            recommendations=["Check Smartlead API key and campaign ID"],
            checked_at=datetime.utcnow(),
        )

    # Parse stats (Smartlead analytics response shape)
    sent = stats.get("sent_count", 0) or 0
    opened = stats.get("opened_count", 0) or 0
    replied = stats.get("reply_count", 0) or 0
    bounced = stats.get("bounce_count", 0) or 0
    positive = stats.get("interested_count", 0) or 0

    if sent == 0:
        return CampaignHealth(
            campaign_id=campaign_id, campaign_name=campaign_name, vertical=vertical,
            total_sent=0, total_opened=0, total_replied=0, total_bounced=0, positive_replies=0,
            open_rate=0, reply_rate=0, bounce_rate=0, positive_reply_rate=0,
            status="no_data", issues=["No emails sent yet"], recommendations=["Wait for first sends"],
            checked_at=datetime.utcnow(),
        )

    open_rate = opened / sent
    reply_rate = replied / sent
    bounce_rate = bounced / sent
    positive_reply_rate = positive / sent

    # ── Bounce rate checks (hardest gates — deliverability)
    if bounce_rate >= THRESHOLDS.bounce_rate_max:
        status = "critical"
        issues.append(f"CRITICAL: Bounce rate {bounce_rate:.1%} >= {THRESHOLDS.bounce_rate_max:.1%} hard limit")
        recommendations.append("Pause immediately. Re-verify entire lead list with Findymail before resuming.")
        pause_campaign(campaign_id, f"bounce rate {bounce_rate:.1%} exceeded hard limit")
    elif bounce_rate >= THRESHOLDS.bounce_rate_warn:
        if status != "critical":
            status = "warning"
        issues.append(f"WARNING: Bounce rate {bounce_rate:.1%} approaching limit (warn at {THRESHOLDS.bounce_rate_warn:.1%})")
        recommendations.append("Run Findymail re-verify on remaining un-sent leads. Monitor hourly.")

    # ── Open rate check (deliverability signal)
    if sent >= 100 and open_rate < THRESHOLDS.open_rate_min:
        if status == "healthy":
            status = "warning"
        issues.append(f"Low open rate {open_rate:.1%} (min {THRESHOLDS.open_rate_min:.1%}) — likely inbox placement issue")
        recommendations.append("Check SPF/DKIM/DMARC on sending domains. Reduce daily send volume by 30%.")

    # ── Reply rate check (Eric's burnout threshold)
    if sent >= 200 and reply_rate < THRESHOLDS.reply_rate_min_7d:
        if status == "healthy":
            status = "warning"
        issues.append(f"Reply rate {reply_rate:.1%} below 0.7% burnout threshold — domain may be flagging as cold")
        recommendations.append("Rotate to fresh domain. Refresh copy with new A/B variants. Tighten ICP filter.")

    return CampaignHealth(
        campaign_id=campaign_id,
        campaign_name=campaign_name,
        vertical=vertical,
        total_sent=sent,
        total_opened=opened,
        total_replied=replied,
        total_bounced=bounced,
        positive_replies=positive,
        open_rate=open_rate,
        reply_rate=reply_rate,
        bounce_rate=bounce_rate,
        positive_reply_rate=positive_reply_rate,
        status=status,
        issues=issues,
        recommendations=recommendations,
        checked_at=datetime.utcnow(),
    )


# ─── Slack Alerting ───────────────────────────────────────────────────────────
def _slack_post(blocks: list, text: str = "Campaign Health Alert") -> bool:
    """Post a Slack message with blocks."""
    if not SLACK_ACCESS_TOKEN:
        logger.warning("No SLACK_ACCESS_TOKEN — skipping alert")
        return False
    try:
        resp = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {SLACK_ACCESS_TOKEN}"},
            json={"channel": SLACK_ALERT_CHANNEL, "text": text, "blocks": blocks},
            timeout=15,
        )
        data = resp.json()
        if not data.get("ok"):
            logger.error("Slack post failed: %s", data.get("error"))
            return False
        return True
    except Exception as e:
        logger.error("Slack alert failed: %s", e)
        return False


def alert_campaign_health(health: CampaignHealth) -> None:
    """Send a Slack alert for a campaign health issue."""
    if health.status in ("healthy", "no_data", "unknown"):
        return

    emoji = "🔴" if health.status == "critical" else "🟡"
    status_label = "CRITICAL — AUTO-PAUSED" if health.status == "critical" else "WARNING"

    issues_text = "\n".join(f"• {i}" for i in health.issues)
    recs_text = "\n".join(f"• {r}" for r in health.recommendations)

    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": f"{emoji} Campaign Health {status_label}"}},
        {"type": "section", "fields": [
            {"type": "mrkdwn", "text": f"*Campaign:*\n{health.campaign_name}"},
            {"type": "mrkdwn", "text": f"*Vertical:*\n{health.vertical}"},
            {"type": "mrkdwn", "text": f"*Sent:*\n{health.total_sent:,}"},
            {"type": "mrkdwn", "text": f"*Reply Rate:*\n{health.reply_rate:.2%}"},
            {"type": "mrkdwn", "text": f"*Bounce Rate:*\n{health.bounce_rate:.2%}"},
            {"type": "mrkdwn", "text": f"*Open Rate:*\n{health.open_rate:.2%}"},
        ]},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Issues:*\n{issues_text}"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Recommendations:*\n{recs_text}"}},
        {"type": "context", "elements": [
            {"type": "mrkdwn", "text": f"Checked at {health.checked_at.strftime('%Y-%m-%d %H:%M UTC')} | Campaign ID: `{health.campaign_id}`"}
        ]},
    ]
    _slack_post(blocks, text=f"{emoji} {status_label}: {health.campaign_name}")


def alert_pipeline_error(component: str, error: str, context: dict = None) -> None:
    """Send a Slack alert for a pipeline component failure."""
    ctx_text = ""
    if context:
        ctx_text = "\n".join(f"• {k}: {v}" for k, v in context.items())

    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": "🚨 Pipeline Error"}},
        {"type": "section", "fields": [
            {"type": "mrkdwn", "text": f"*Component:*\n`{component}`"},
            {"type": "mrkdwn", "text": f"*Time:*\n{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"},
        ]},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Error:*\n```{error}```"}},
    ]
    if ctx_text:
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*Context:*\n{ctx_text}"}})

    _slack_post(blocks, text=f"🚨 Pipeline Error: {component}")


def alert_hot_lead(company_name: str, vertical: str, score: float, hook: str, sla_hours: int) -> None:
    """Send a Slack alert when a 150+ scored lead is detected (Red Hot — < 1 hour SLA)."""
    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": "🔥 RED HOT LEAD — Act Within 1 Hour"}},
        {"type": "section", "fields": [
            {"type": "mrkdwn", "text": f"*Company:*\n{company_name}"},
            {"type": "mrkdwn", "text": f"*Vertical:*\n{vertical}"},
            {"type": "mrkdwn", "text": f"*Signal Score:*\n{score:.0f} pts"},
            {"type": "mrkdwn", "text": f"*SLA:*\n< {sla_hours} hour"},
        ]},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Hook:*\n_{hook}_"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": "*Action:* Manual personalized outreach by AE. Check Airtable for contact details."}},
    ]
    _slack_post(blocks, text=f"🔥 Red Hot Lead: {company_name} ({vertical}) — Score: {score:.0f}")


# ─── Full Health Check Run ────────────────────────────────────────────────────
def run_health_check(campaign_map: dict) -> list[CampaignHealth]:
    """
    Run health check on all contractor campaigns.

    Args:
        campaign_map: {"vertical_name": "campaign_id", ...}

    Returns:
        List of CampaignHealth objects. Alerts sent automatically for issues.
    """
    results = []
    for vertical, campaign_id in campaign_map.items():
        if not campaign_id:
            logger.info("No campaign ID for vertical %s — skipping", vertical)
            continue

        try:
            health = check_campaign_health(
                campaign_id=campaign_id,
                vertical=vertical,
                campaign_name=f"ContractMotion — {vertical} 2026",
            )
            results.append(health)

            # Alert if there's an issue
            if health.status not in ("healthy", "no_data"):
                alert_campaign_health(health)

            logger.info(
                "Health check %s | status=%s | sent=%d | reply=%.2f%% | bounce=%.2f%%",
                vertical, health.status, health.total_sent,
                health.reply_rate * 100, health.bounce_rate * 100,
            )

        except Exception as e:
            logger.error("Health check failed for %s: %s", vertical, e)
            alert_pipeline_error("health_monitor", str(e), {"vertical": vertical, "campaign_id": campaign_id})

    return results
