"""Single-URL health dashboard for the Industry Factory.

Exposes: /admin/dashboard (JSON) and /admin/dashboard.html (rendered).
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


REQUIRED_KEYS = [
    "APOLLO_API_KEY", "FINDYMAIL_API_KEY", "SMARTLEAD_API_KEY",
    "AIRTABLE_API_KEY", "ANTHROPIC_API_KEY", "PERPLEXITY_API_KEY",
    "FIRECRAWL_API_KEY", "BROWSERBASE_API_KEY", "BROWSERBASE_PROJECT_ID",
    "AIRTOP_API_KEY", "SLACK_ACCESS_TOKEN",
]


def _doppler_key_presence() -> dict[str, bool]:
    return {k: bool(os.environ.get(k)) for k in REQUIRED_KEYS}


def _campaign_summaries() -> list[dict]:
    """Pull minimal per-campaign stats from Smartlead."""
    import requests
    key = os.environ.get("SMARTLEAD_API_KEY", "")
    if not key:
        return []
    try:
        resp = requests.get(
            "https://server.smartlead.ai/api/v1/campaigns/analytics",
            params={"api_key": key},
            timeout=15,
        )
        resp.raise_for_status()
        raw = resp.json() or []
        return [
            {
                "id": s.get("id"),
                "name": s.get("name"),
                "status": s.get("status"),
                "sent_7d": s.get("sent_last_7_days", 0),
                "replies_7d": s.get("replies_last_7_days", 0),
            }
            for s in raw
        ]
    except Exception as e:
        logger.warning("[Dashboard] campaign summaries failed: %s", e)
        return []


def pre_flight_check():
    """Thin indirection for test mocking."""
    from enrichment.health import pre_flight_check as _pfc
    return _pfc()


def load_all_industries():
    """Thin indirection for test mocking."""
    from industries.loader import load_all_industries as _lai
    return _lai()


def build_dashboard_payload() -> dict[str, Any]:
    """Assemble single JSON payload describing system health."""
    pf = pre_flight_check()
    industries = load_all_industries()
    industries_view = {
        slug: {
            "display_name": ind.display_name,
            "track": ind.track.value,
            "campaign_id": ind.campaign_id,
            "scoring_mode": ind.scoring_mode.value,
        }
        for slug, ind in industries.items()
    }

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "preflight": pf,
        "industries": industries_view,
        "campaigns": _campaign_summaries(),
        "doppler_keys": _doppler_key_presence(),
    }


def render_html(payload: dict[str, Any]) -> str:
    """Simple HTML table view."""
    def _status(b: bool) -> str:
        return '<span style="color:green">&#10003;</span>' if b else '<span style="color:red">&#10007;</span>'

    rows_keys = "".join(
        f"<tr><td>{k}</td><td>{_status(v)}</td></tr>"
        for k, v in payload["doppler_keys"].items()
    )
    rows_inds = "".join(
        f"<tr><td>{s}</td><td>{v['display_name']}</td><td>{v['track']}</td>"
        f"<td>{v['campaign_id']}</td><td>{v['scoring_mode']}</td></tr>"
        for s, v in payload["industries"].items()
    )
    rows_camps = "".join(
        f"<tr><td>{c.get('id','')}</td><td>{c.get('name','')}</td>"
        f"<td>{c.get('status','')}</td><td>{c.get('sent_7d',0)}</td>"
        f"<td>{c.get('replies_7d',0)}</td></tr>"
        for c in payload["campaigns"]
    )
    pf_status = payload["preflight"]["status"]
    pf_color = {"healthy": "green", "degraded": "orange", "blocked": "red"}.get(pf_status, "gray")

    return f"""
<!DOCTYPE html>
<html><head><title>ECAS Factory — Health</title>
<style>body{{font-family:system-ui,sans-serif;margin:2rem;max-width:1100px}}
table{{border-collapse:collapse;margin:1rem 0;width:100%}}
td,th{{border:1px solid #ddd;padding:6px 10px}}
th{{background:#f4f4f4;text-align:left}}</style></head>
<body>
<h1>Industry Factory Health</h1>
<p>Generated: {payload['generated_at']}</p>
<h2>Pre-flight: <span style="color:{pf_color}">{pf_status}</span></h2>
<pre>{payload['preflight']['checks']}</pre>
<h2>Doppler keys</h2>
<table><thead><tr><th>Key</th><th>Present</th></tr></thead><tbody>{rows_keys}</tbody></table>
<h2>Industries</h2>
<table><thead><tr><th>Slug</th><th>Display</th><th>Track</th><th>Campaign</th><th>Mode</th></tr></thead>
<tbody>{rows_inds}</tbody></table>
<h2>Campaigns (last 7d)</h2>
<table><thead><tr><th>ID</th><th>Name</th><th>Status</th><th>Sent</th><th>Replies</th></tr></thead>
<tbody>{rows_camps}</tbody></table>
</body></html>
"""
