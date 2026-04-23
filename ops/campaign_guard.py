"""Auto-pause Smartlead campaigns that underperform, plus warmup pool helpers."""
from __future__ import annotations

import logging
import os

import requests

logger = logging.getLogger(__name__)


def _fetch_all_campaign_stats() -> list[dict]:
    key = os.environ.get("SMARTLEAD_API_KEY", "")
    if not key:
        raise RuntimeError("SMARTLEAD_API_KEY not set")
    resp = requests.get(
        "https://server.smartlead.ai/api/v1/campaigns/analytics",
        params={"api_key": key},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json() or []


def _pause_campaign(campaign_id: str) -> None:
    key = os.environ.get("SMARTLEAD_API_KEY", "")
    resp = requests.post(
        f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}/status",
        params={"api_key": key},
        json={"status": "PAUSED"},
        timeout=15,
    )
    resp.raise_for_status()
    logger.warning("[CampaignGuard] Paused campaign %s", campaign_id)


def _slack_alert(message: str) -> None:
    token = os.environ.get("SLACK_ACCESS_TOKEN", "")
    channel = os.environ.get("SLACK_CHANNEL", "#ecas-ops")
    if not token:
        logger.warning("[CampaignGuard] No Slack token: %s", message)
        return
    try:
        requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"channel": channel, "text": message},
            timeout=10,
        )
    except Exception as exc:
        logger.error("[CampaignGuard] Slack post failed: %s", exc)


def check_and_pause_underperformers(
    min_sent_threshold: int = 200,
    reply_rate_floor: float = 0.01,
) -> dict:
    """Pause any campaign with >=min_sent_threshold sends and reply rate < floor."""
    stats = _fetch_all_campaign_stats()
    paused: list[str] = []
    skipped_low_volume: list[str] = []
    for s in stats:
        cid = str(s.get("id", ""))
        sent = int(s.get("total_sent", 0) or 0)
        replies = int(s.get("total_replies", 0) or 0)
        if sent < min_sent_threshold:
            skipped_low_volume.append(cid)
            continue
        rate = (replies / sent) if sent else 0
        if rate < reply_rate_floor:
            _pause_campaign(cid)
            _slack_alert(
                f":warning: Auto-paused Smartlead campaign {cid} ({s.get('name','')}) — "
                f"reply rate {rate:.2%} on {sent} sent (floor {reply_rate_floor:.0%})"
            )
            paused.append(cid)
    return {"paused": paused, "skipped_low_volume": skipped_low_volume}


def warmup_pool_status() -> dict:
    """Return list of warmed-and-idle Smartlead email accounts."""
    key = os.environ.get("SMARTLEAD_API_KEY", "")
    resp = requests.get(
        "https://server.smartlead.ai/api/v1/email-accounts",
        params={"api_key": key},
        timeout=30,
    )
    resp.raise_for_status()
    accounts = resp.json() or []
    ready = [
        a for a in accounts
        if a.get("warmup_details", {}).get("status") == "COMPLETED"
        and not a.get("assigned_to_campaign_id")
    ]
    return {"ready_count": len(ready), "ready_accounts": ready}
