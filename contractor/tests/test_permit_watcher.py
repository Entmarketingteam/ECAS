"""Tests for contractor/signals/permit_watcher.py"""
import pytest
from unittest.mock import patch, MagicMock
from contractor.tests.test_signal_scrapers_shared import assert_valid_signal

MOCK_SOCRATA_RESPONSE = [
    {
        "permit_number": "2026-COM-001234",
        "applicant_name": "Apex Roofing Solutions LLC",
        "work_description": "Commercial Roof Replacement — Building B",
        "total_valuation": "285000",
        "issue_date": "2026-03-28",
        "address": "1234 Commerce Blvd",
        "contractor_company": "Apex Roofing Solutions LLC",
    },
    {
        "permit_number": "2026-COM-001235",
        "applicant_name": "Downtown Property Management",
        "work_description": "HVAC Replacement",
        "total_valuation": "95000",
        "issue_date": "2026-03-29",
        "address": "500 Main St",
        "contractor_company": "HVAC Pros Inc",
    },
]


class TestPermitWatcher:
    @patch("contractor.signals.permit_watcher.signal_exists", return_value=False)
    @patch("contractor.signals.permit_watcher.requests.get")
    def test_parses_permit_records(self, mock_get, mock_exists):
        from contractor.signals.permit_watcher import fetch_permits_from_source
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = MOCK_SOCRATA_RESPONSE

        source = {"city": "Austin, TX", "url": "https://data.austintexas.gov/resource/3syk-w9eu.json", "type": "socrata"}
        signals = fetch_permits_from_source(source)

        # Roof record passes; HVAC record fails keyword filter
        assert len(signals) >= 1
        assert_valid_signal(signals[0])
        assert signals[0]["signal_type"] == "commercial_permit_pulled"
        assert signals[0]["source"] == "Socrata-Austin, TX"

    @patch("contractor.signals.permit_watcher.signal_exists", return_value=False)
    @patch("contractor.signals.permit_watcher.requests.get")
    def test_filters_low_value_permits(self, mock_get, mock_exists):
        from contractor.signals.permit_watcher import fetch_permits_from_source
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = [
            {"permit_number": "P001", "applicant_name": "SmallCo",
             "work_description": "Roof repair", "total_valuation": "12000",
             "issue_date": "2026-03-28", "address": "100 Main St"}
        ]
        source = {"city": "Austin, TX", "url": "https://data.austintexas.gov/resource/3syk-w9eu.json", "type": "socrata"}
        signals = fetch_permits_from_source(source)
        assert signals == []  # Below $50K threshold

    @patch("contractor.signals.permit_watcher.requests.get")
    def test_api_failure_returns_empty(self, mock_get):
        from contractor.signals.permit_watcher import fetch_permits_from_source
        mock_get.side_effect = Exception("Connection refused")
        source = {"city": "Austin, TX", "url": "https://data.austintexas.gov/resource/bad.json", "type": "socrata"}
        assert fetch_permits_from_source(source) == []

    @patch("contractor.signals.permit_watcher.push_signals")
    @patch("contractor.signals.permit_watcher.fetch_permits_from_source")
    def test_run_scrapes_all_sources(self, mock_fetch, mock_push):
        from contractor.signals.permit_watcher import run_permit_watcher
        mock_fetch.return_value = [{"company_name": "Co"}]
        mock_push.return_value = 4
        run_permit_watcher()
        assert mock_fetch.call_count == 4  # 4 configured cities
