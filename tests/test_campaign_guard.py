"""Tests for campaign auto-pause guard."""
from unittest.mock import patch

from ops.campaign_guard import check_and_pause_underperformers


def test_pauses_campaign_below_floor():
    mock_stats = [
        {"id": "3040599", "name": "DC", "total_sent": 250, "total_replies": 1},
        {"id": "3040600", "name": "Water", "total_sent": 300, "total_replies": 5},
        {"id": "3040601", "name": "Industrial", "total_sent": 50, "total_replies": 0},
    ]
    with patch("ops.campaign_guard._fetch_all_campaign_stats", return_value=mock_stats), \
         patch("ops.campaign_guard._pause_campaign") as pause, \
         patch("ops.campaign_guard._slack_alert") as alert:
        result = check_and_pause_underperformers(
            min_sent_threshold=200,
            reply_rate_floor=0.01,
        )

    pause.assert_called_once_with("3040599")
    alert.assert_called_once()
    assert result["paused"] == ["3040599"]
    assert result["skipped_low_volume"] == ["3040601"]
