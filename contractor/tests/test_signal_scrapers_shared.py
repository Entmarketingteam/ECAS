"""
Shared fixtures and output-contract validation for all signal scrapers.
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock


# ─── Output contract validator ────────────────────────────────────────────────
REQUIRED_FIELDS = {
    "company_name", "company_domain", "vertical", "vertical_type",
    "signal_type", "detected_at", "source", "processed", "raw_data_json",
}
VALID_VERTICALS = {"Commercial Roofing", "Commercial Janitorial", "Pest Control"}
VALID_SIGNAL_TYPES = {
    "industry_association_member", "government_contract_win", "commercial_permit_pulled",
    "fm_job_change", "fm_job_posting", "franchise_new_territory", "competitor_acquisition",
    "osha_citation", "rto_announcement", "commercial_lease_signed", "commercial_building_sold",
    "negative_review_competitor", "hiring_spree", "new_location_opened",
}


def assert_valid_signal(sig: dict) -> None:
    """Assert a signal dict matches the output contract."""
    missing = REQUIRED_FIELDS - set(sig.keys())
    assert not missing, f"Signal missing required fields: {missing}"
    assert sig["vertical_type"] == "contractor", "vertical_type must be 'contractor'"
    assert sig["vertical"] in VALID_VERTICALS, f"Unknown vertical: {sig['vertical']}"
    assert sig["signal_type"] in VALID_SIGNAL_TYPES, f"Unknown signal_type: {sig['signal_type']}"
    assert sig["processed"] is False, "processed must be False"
    assert isinstance(sig["raw_data_json"], dict), "raw_data_json must be a dict"
    # Validate detected_at is parseable ISO 8601
    datetime.fromisoformat(sig["detected_at"])


# ─── Airtable helper tests ─────────────────────────────────────────────────────
class TestPushSignals:
    @patch("contractor.signals._airtable.requests.post")
    def test_push_empty_list_returns_zero(self, mock_post):
        from contractor.signals._airtable import push_signals
        result = push_signals([])
        assert result == 0
        mock_post.assert_not_called()

    @patch("contractor.signals._airtable.requests.post")
    def test_push_batches_in_tens(self, mock_post):
        from contractor.signals._airtable import push_signals
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = MagicMock()
        mock_post.return_value.json.return_value = {"records": [{"id": f"rec{i}"} for i in range(10)]}

        signals = [{"company_name": f"Co{i}", "company_domain": f"co{i}.com"} for i in range(25)]
        result = push_signals(signals)

        assert mock_post.call_count == 3  # 10 + 10 + 5
        assert result == 30  # 3 batches × 10 returned each

    @patch("contractor.signals._airtable.requests.post")
    def test_push_continues_on_batch_failure(self, mock_post):
        from contractor.signals._airtable import push_signals
        mock_post.side_effect = [
            Exception("API error"),
            MagicMock(status_code=200, json=lambda: {"records": [{"id": "rec1"}]},
                      raise_for_status=lambda: None),
        ]
        signals = [{"company_name": f"Co{i}"} for i in range(15)]
        result = push_signals(signals)
        assert result == 1  # Second batch succeeded

    @patch("contractor.signals._airtable.requests.get")
    def test_signal_exists_returns_true_when_found(self, mock_get):
        from contractor.signals._airtable import signal_exists
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {"records": [{"id": "rec001"}]}
        assert signal_exists("apexroofing.com", "industry_association_member") is True

    @patch("contractor.signals._airtable.requests.get")
    def test_signal_exists_returns_false_when_not_found(self, mock_get):
        from contractor.signals._airtable import signal_exists
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {"records": []}
        assert signal_exists("newco.com", "industry_association_member") is False

    def test_signal_exists_empty_domain_returns_false(self):
        from contractor.signals._airtable import signal_exists
        assert signal_exists("", "industry_association_member") is False
