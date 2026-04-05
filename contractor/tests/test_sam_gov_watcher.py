"""Tests for contractor/signals/sam_gov_watcher.py"""
import pytest
from unittest.mock import patch, MagicMock
from contractor.tests.test_signal_scrapers_shared import assert_valid_signal

MOCK_SAM_RESPONSE = {
    "opportunitiesData": [
        {
            "noticeId": "abc123",
            "title": "Roofing Repair Services — Travis County Federal Building",
            "naicsCode": "238160",
            "award": {
                "date": "2026-03-25",
                "amount": "185000",
                "awardee": {
                    "name": "Summit Commercial Roofing LLC",
                    "location": {
                        "city": {"name": "Austin"},
                        "state": {"code": "TX"},
                        "zip": "78701",
                    }
                }
            }
        },
        {
            "noticeId": "def456",
            "title": "Janitorial Services — IRS Office",
            "naicsCode": "561720",
            "award": {
                "date": "2026-03-20",
                "amount": "95000",
                "awardee": {
                    "name": "CleanPro Facilities Inc",
                    "location": {
                        "city": {"name": "Dallas"},
                        "state": {"code": "TX"},
                        "zip": "75201",
                    }
                }
            }
        },
    ],
    "totalRecords": 2,
}

MOCK_SAM_EMPTY = {"opportunitiesData": [], "totalRecords": 0}


class TestSamGovWatcher:
    @patch("contractor.signals.sam_gov_watcher.signal_exists", return_value=False)
    @patch("contractor.signals.sam_gov_watcher.requests.get")
    def test_parses_award_records(self, mock_get, mock_exists):
        from contractor.signals.sam_gov_watcher import fetch_awards_page
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = MOCK_SAM_RESPONSE

        signals = fetch_awards_page(offset=0)

        assert len(signals) == 2
        assert_valid_signal(signals[0])
        assert signals[0]["signal_type"] == "government_contract_win"
        assert signals[0]["company_name"] == "Summit Commercial Roofing LLC"
        assert signals[0]["vertical"] == "Commercial Roofing"
        assert signals[0]["source"] == "SAM.gov"
        assert signals[0]["raw_data_json"]["naics"] == "238160"
        assert signals[0]["raw_data_json"]["award_amount"] == "185000"

    @patch("contractor.signals.sam_gov_watcher.signal_exists", return_value=False)
    @patch("contractor.signals.sam_gov_watcher.requests.get")
    def test_maps_naics_to_vertical(self, mock_get, mock_exists):
        from contractor.signals.sam_gov_watcher import fetch_awards_page
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = MOCK_SAM_RESPONSE

        signals = fetch_awards_page(offset=0)
        roofing = next(s for s in signals if s["company_name"] == "Summit Commercial Roofing LLC")
        janitorial = next(s for s in signals if s["company_name"] == "CleanPro Facilities Inc")
        assert roofing["vertical"] == "Commercial Roofing"
        assert janitorial["vertical"] == "Commercial Janitorial"

    @patch("contractor.signals.sam_gov_watcher.requests.get")
    def test_empty_response_returns_empty(self, mock_get):
        from contractor.signals.sam_gov_watcher import fetch_awards_page
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = MOCK_SAM_EMPTY
        assert fetch_awards_page(offset=0) == []

    @patch("contractor.signals.sam_gov_watcher.push_signals")
    @patch("contractor.signals.sam_gov_watcher.fetch_awards_page")
    def test_run_paginates_until_empty(self, mock_fetch, mock_push):
        from contractor.signals.sam_gov_watcher import run_sam_gov_watcher
        mock_fetch.side_effect = [
            [{"company_name": "Co1"}] * 100,  # Page 1: full
            [{"company_name": "Co2"}] * 50,   # Page 2: partial — stop
        ]
        mock_push.return_value = 150
        run_sam_gov_watcher()
        assert mock_fetch.call_count == 2
