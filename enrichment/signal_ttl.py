"""Drop stale projects/leads that are past their signal TTL."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def _get_client():
    from storage.airtable import get_client
    return get_client()


def sweep_stale_projects(ttl_days: int = 90) -> dict:
    """Find projects with last_signal_at older than ttl_days and mark stage='Archived'."""
    at = _get_client()
    cutoff = datetime.utcnow() - timedelta(days=ttl_days)

    projects = at._get(
        "projects",
        {"filterByFormula": "AND({stage}!='Archived', {last_signal_at}!='')"},
    )

    swept = 0
    for p in projects:
        last = p.get("fields", {}).get("last_signal_at", "")
        try:
            last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            continue
        if last_dt.replace(tzinfo=None) < cutoff:
            at.update_record("projects", p["id"], {"stage": "Archived"})
            swept += 1
    logger.info("[SignalTTL] Swept %d stale projects", swept)
    return {"swept": swept, "cutoff": cutoff.isoformat()}
