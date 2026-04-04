"""
Tests for contractor/pipeline/health_monitor.py

Run: pytest contractor/tests/test_health_monitor.py -v
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from contractor.pipeline.health_monitor import (
    check_campaign_health, CampaignHealth, THRESHOLDS,
    run_health_check, alert_pipeline_error
)


def make_stats(sent=500, opened=110, replied=12, bounced=3, positive=4):
    return {
        "sent_count": sent,
        "opened_count": opened,
        "reply_count": replied,
        "bounce_count": bounced,
        "interested_count": positive,
    }


class TestCampaignHealth:
    @patch("contractor.pipeline.health_monitor.get_campaign_stats")
    def test_healthy_campaign(self, mock_stats):
        """Campaign within all thresholds should be healthy."""
        mock_stats.return_value = make_stats(sent=500, opened=120, replied=20, bounced=3)
        health = check_campaign_health("camp123", "Pest Control", "ContractMotion — Pest Control 2026")
        assert health.status == "healthy"
        assert health.issues == []
        assert health.bounce_rate < THRESHOLDS.bounce_rate_warn

    @patch("contractor.pipeline.health_monitor.get_campaign_stats")
    @patch("contractor.pipeline.health_monitor.pause_campaign")
    def test_critical_bounce_triggers_pause(self, mock_pause, mock_stats):
        """Bounce rate >= 1% should auto-pause and mark critical."""
        mock_stats.return_value = make_stats(sent=500, bounced=6)  # 1.2% bounce
        mock_pause.return_value = True
        health = check_campaign_health("camp123", "Pest Control", "ContractMotion — Pest Control 2026")
        assert health.status == "critical"
        mock_pause.assert_called_once_with("camp123", "bounce rate 1.2% exceeded hard limit")

    @patch("contractor.pipeline.health_monitor.get_campaign_stats")
    def test_warning_bounce_no_pause(self, mock_stats):
        """Bounce rate 0.8-1% should warn but NOT pause."""
        mock_stats.return_value = make_stats(sent=500, bounced=4)  # 0.8%
        health = check_campaign_health("camp123", "Commercial Roofing", "ContractMotion — Roofing 2026")
        assert health.status == "warning"
        assert health.bounce_rate < THRESHOLDS.bounce_rate_max
        assert any("approaching" in i.lower() for i in health.issues)

    @patch("contractor.pipeline.health_monitor.get_campaign_stats")
    def test_low_reply_rate_warning(self, mock_stats):
        """Reply rate below 0.7% on 200+ sends should warn."""
        mock_stats.return_value = make_stats(sent=300, replied=1, bounced=0)  # 0.33% reply, 0% bounce
        health = check_campaign_health("camp123", "Commercial Janitorial", "ContractMotion — Janitorial 2026")
        assert health.status == "warning"
        assert any("0.7%" in i or "burnout" in i.lower() for i in health.issues)

    @patch("contractor.pipeline.health_monitor.get_campaign_stats")
    def test_no_sends_returns_no_data(self, mock_stats):
        mock_stats.return_value = make_stats(sent=0)
        health = check_campaign_health("camp123", "Pest Control", "ContractMotion — Pest Control 2026")
        assert health.status == "no_data"

    @patch("contractor.pipeline.health_monitor.get_campaign_stats")
    def test_api_failure_returns_unknown(self, mock_stats):
        mock_stats.return_value = None
        health = check_campaign_health("camp123", "Pest Control", "ContractMotion — Pest Control 2026")
        assert health.status == "unknown"
        assert len(health.issues) > 0

    @patch("contractor.pipeline.health_monitor.get_campaign_stats")
    @patch("contractor.pipeline.health_monitor.alert_campaign_health")
    def test_run_health_check_skips_empty_campaign_ids(self, mock_alert, mock_stats):
        """Verticals with no campaign ID should be skipped gracefully."""
        campaign_map = {
            "Commercial Janitorial": "",  # Not set yet
            "Commercial Roofing": "camp456",
        }
        mock_stats.return_value = make_stats()
        results = run_health_check(campaign_map)
        # Only Roofing should be checked (Janitorial has no ID)
        assert len(results) == 1
        assert results[0].vertical == "Commercial Roofing"
