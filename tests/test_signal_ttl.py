"""Tests for signal TTL sweeper."""
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from enrichment.signal_ttl import sweep_stale_projects


def test_sweeps_projects_older_than_ttl():
    fake_now = datetime(2026, 4, 16)

    mock_at = MagicMock()
    mock_at._get.return_value = [
        {"id": "rec1", "fields": {"owner_company": "Old", "last_signal_at": "2025-10-01"}},
        {"id": "rec2", "fields": {"owner_company": "Fresh", "last_signal_at": "2026-04-01"}},
    ]

    with patch("enrichment.signal_ttl._get_client", return_value=mock_at), \
         patch("enrichment.signal_ttl.datetime") as dt:
        dt.utcnow.return_value = fake_now
        dt.fromisoformat.side_effect = datetime.fromisoformat
        result = sweep_stale_projects(ttl_days=120)

    assert result["swept"] == 1
    mock_at.update_record.assert_called_once()
