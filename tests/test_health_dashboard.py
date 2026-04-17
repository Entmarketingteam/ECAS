"""Tests for health dashboard endpoint."""
from unittest.mock import patch

from ops.health_dashboard import build_dashboard_payload, render_html


def test_dashboard_payload_structure():
    with patch("ops.health_dashboard.pre_flight_check") as pf, \
         patch("ops.health_dashboard.load_all_industries") as industries, \
         patch("ops.health_dashboard._campaign_summaries") as camps, \
         patch("ops.health_dashboard._doppler_key_presence") as doppler:
        pf.return_value = {"status": "healthy", "checks": {"apollo": {"healthy": True}}, "failures": {}}
        industries.return_value = {}
        camps.return_value = []
        doppler.return_value = {"APOLLO_API_KEY": True, "PERPLEXITY_API_KEY": False}
        payload = build_dashboard_payload()

    assert "preflight" in payload
    assert "industries" in payload
    assert "campaigns" in payload
    assert "doppler_keys" in payload
    assert payload["preflight"]["status"] == "healthy"
    assert payload["doppler_keys"]["PERPLEXITY_API_KEY"] is False


def test_render_html_contains_sections():
    payload = {
        "generated_at": "2026-04-16T00:00:00",
        "preflight": {"status": "healthy", "checks": {}, "failures": {}},
        "industries": {
            "x": {"display_name": "X", "track": "contract_motion", "campaign_id": "1", "scoring_mode": "positive"},
        },
        "campaigns": [{"id": 1, "name": "Test", "status": "ACTIVE", "sent_7d": 10, "replies_7d": 1}],
        "doppler_keys": {"APOLLO_API_KEY": True},
    }
    html = render_html(payload)
    assert "Industry Factory Health" in html
    assert "contract_motion" in html
    assert "APOLLO_API_KEY" in html
