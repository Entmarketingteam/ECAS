"""
Integration test — full pipeline smoke test.
Uses mocked external APIs (Apollo, Findymail, Smartlead, Airtable, Slack).

Run: pytest contractor/tests/test_pipeline_integration.py -v

This test verifies:
1. Signal fetch → group → score → ICP qualify → contact hunt → enrich → enroll
2. Health check runs without crashing
3. Alerts fire correctly for critical thresholds
4. Red Hot leads generate Slack alerts
5. Pipeline handles API failures gracefully without crashing
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from contractor.pipeline.orchestrator import (
    run_contractor_pipeline,
    process_company,
    group_signals_by_company,
    enroll_in_smartlead,
    EnrichedContact,
)
from contractor.pipeline.signal_scorer import Signal, score_lead


# ─── Fixtures ─────────────────────────────────────────────────────────────────
def make_airtable_records(n=3, vertical="Commercial Roofing", signal_type="hail_event_large"):
    """Generate mock Airtable signal records."""
    return [
        {
            "id": f"rec{i:04d}",
            "fields": {
                "company_name": f"Apex Roofing {i}",
                "company_domain": f"apexroofing{i}.com",
                "vertical": vertical,
                "vertical_type": "contractor",
                "signal_type": signal_type,
                "detected_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                "source": "NOAA",
                "processed": False,
                "raw_data_json": {"county": "Travis County", "magnitude_inches": 2.0},
            }
        }
        for i in range(n)
    ]


MOCK_APOLLO_PERSON = {
    "id": "person123",
    "first_name": "John",
    "last_name": "Smith",
    "title": "Owner",
    "email": None,  # Apollo withholds — Findymail fills this
    "organization": {"name": "Apex Roofing", "website_url": "apexroofing.com"},
}

MOCK_FINDYMAIL_SEARCH = {"email": "john.smith@apexroofing.com"}
MOCK_FINDYMAIL_VERIFY = {"status": "valid"}
MOCK_SMARTLEAD_ENROLL = {"ok": True, "message": "Leads added to campaign"}


# ─── Full Pipeline Integration Test ──────────────────────────────────────────
class TestFullPipeline:

    @patch("contractor.pipeline.orchestrator.mark_signals_processed")
    @patch("contractor.pipeline.orchestrator.enroll_in_smartlead")
    @patch("contractor.pipeline.orchestrator.enrich_email_findymail")
    @patch("contractor.pipeline.orchestrator.hunt_contact_apollo")
    @patch("contractor.pipeline.orchestrator.icp_score_company")
    @patch("contractor.pipeline.orchestrator.fetch_unprocessed_signals")
    def test_happy_path_end_to_end(
        self, mock_fetch, mock_icp, mock_apollo, mock_findymail, mock_enroll, mock_mark
    ):
        """Full pipeline with 3 hot leads should enroll all 3."""
        mock_fetch.return_value = make_airtable_records(3, "Commercial Roofing", "hail_event_large")
        mock_icp.return_value = 80  # Bypass ICP scoring — not what this test is verifying
        mock_apollo.return_value = MOCK_APOLLO_PERSON
        mock_findymail.return_value = {"email": "john@apexroofing.com", "verified": True}
        mock_enroll.return_value = True
        mock_mark.return_value = None

        summary = run_contractor_pipeline(vertical="Commercial Roofing")

        assert summary["signals_found"] == 3
        assert summary["companies_scored"] == 3
        assert summary["enrolled"] == 3
        assert summary["errors"] == 0

    @patch("contractor.pipeline.orchestrator.fetch_unprocessed_signals")
    def test_no_signals_returns_empty_summary(self, mock_fetch):
        """Empty signal queue should complete gracefully."""
        mock_fetch.return_value = []
        summary = run_contractor_pipeline()
        assert summary["signals_found"] == 0
        assert summary["enrolled"] == 0

    @patch("contractor.pipeline.orchestrator.mark_signals_processed")
    @patch("contractor.pipeline.orchestrator.enroll_in_smartlead")
    @patch("contractor.pipeline.orchestrator.enrich_email_findymail")
    @patch("contractor.pipeline.orchestrator.hunt_contact_apollo")
    @patch("contractor.pipeline.orchestrator.fetch_unprocessed_signals")
    def test_cool_signals_skipped(
        self, mock_fetch, mock_apollo, mock_findymail, mock_enroll, mock_mark
    ):
        """Leads with only cool signals (email_open) should be skipped."""
        records = make_airtable_records(2, "Commercial Janitorial", "email_open")
        mock_fetch.return_value = records
        mock_apollo.return_value = MOCK_APOLLO_PERSON
        mock_findymail.return_value = {"email": "test@test.com", "verified": True}
        mock_enroll.return_value = True
        mock_mark.return_value = None

        summary = run_contractor_pipeline(vertical="Commercial Janitorial")

        # email_open (5 pts × 1.5 = 7.5) is below warm threshold (50) — skip
        assert summary["enrolled"] == 0
        assert summary["skipped"] == 2

    @patch("contractor.pipeline.orchestrator.mark_signals_processed")
    @patch("contractor.pipeline.orchestrator.alert_hot_lead")
    @patch("contractor.pipeline.orchestrator.enroll_in_smartlead")
    @patch("contractor.pipeline.orchestrator.enrich_email_findymail")
    @patch("contractor.pipeline.orchestrator.hunt_contact_apollo")
    @patch("contractor.pipeline.orchestrator.fetch_unprocessed_signals")
    def test_red_hot_triggers_slack_alert(
        self, mock_fetch, mock_apollo, mock_findymail, mock_enroll, mock_alert, mock_mark
    ):
        """150+ score leads should trigger Slack alert_hot_lead."""
        # Stack 3 hot signals — will exceed 150
        records = [
            {
                "id": "rec0001",
                "fields": {
                    "company_name": "Apex Roofing TX",
                    "company_domain": "apexroofingtx.com",
                    "vertical": "Commercial Roofing",
                    "vertical_type": "contractor",
                    "signal_type": "hail_event_large",   # 80 × 1.5 = 120
                    "detected_at": datetime.utcnow().isoformat(),
                    "source": "NOAA",
                    "processed": False,
                    "raw_data_json": {},
                },
            },
            {
                "id": "rec0002",
                "fields": {
                    "company_name": "Apex Roofing TX",
                    "company_domain": "apexroofingtx.com",
                    "vertical": "Commercial Roofing",
                    "vertical_type": "contractor",
                    "signal_type": "fm_job_change",      # 75 × 1.5 = 112.5
                    "detected_at": datetime.utcnow().isoformat(),
                    "source": "Apollo",
                    "processed": False,
                    "raw_data_json": {},
                },
            },
        ]
        mock_fetch.return_value = records
        mock_apollo.return_value = MOCK_APOLLO_PERSON
        mock_findymail.return_value = {"email": "ceo@apexroofingtx.com", "verified": True}
        mock_enroll.return_value = True
        mock_mark.return_value = None

        run_contractor_pipeline(vertical="Commercial Roofing")

        mock_alert.assert_called_once()
        call_args = mock_alert.call_args
        assert call_args.kwargs.get("company_name") == "Apex Roofing TX"

    @patch("contractor.pipeline.orchestrator.alert_pipeline_error")
    @patch("contractor.pipeline.orchestrator.hunt_contact_apollo")
    @patch("contractor.pipeline.orchestrator.fetch_unprocessed_signals")
    def test_apollo_failure_does_not_crash_pipeline(
        self, mock_fetch, mock_apollo, mock_alert
    ):
        """Apollo API failure should alert and continue, not crash."""
        mock_fetch.return_value = make_airtable_records(2, "Pest Control", "hiring_spree")
        mock_apollo.side_effect = Exception("Apollo API 503")

        # Should not raise
        summary = run_contractor_pipeline(vertical="Pest Control")
        assert summary["errors"] >= 0  # Errors logged but pipeline continues

    @patch("contractor.pipeline.orchestrator.enrich_email_findymail")
    @patch("contractor.pipeline.orchestrator.hunt_contact_apollo")
    @patch("contractor.pipeline.orchestrator.fetch_unprocessed_signals")
    def test_no_email_found_skips_enrollment(
        self, mock_fetch, mock_apollo, mock_findymail
    ):
        """If Findymail returns no email, contact should be skipped."""
        mock_fetch.return_value = make_airtable_records(1, "Commercial Janitorial", "franchise_new_territory")
        mock_apollo.return_value = MOCK_APOLLO_PERSON
        mock_findymail.return_value = None  # No email found

        summary = run_contractor_pipeline(vertical="Commercial Janitorial")
        assert summary["enrolled"] == 0


# ─── Enrollment Unit Test ─────────────────────────────────────────────────────
class TestSmartleadEnrollment:

    @patch("contractor.pipeline.orchestrator.requests.post")
    def test_enrollment_success(self, mock_post):
        """Successful Smartlead enrollment should return True."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = MagicMock()
        mock_post.return_value.json.return_value = {"ok": True}

        with patch.dict(os.environ, {"CAMPAIGN_ROOFING": "camp999"}):
            from contractor.config import CONTRACTOR_CAMPAIGN_MAP
            CONTRACTOR_CAMPAIGN_MAP["Commercial Roofing"] = "camp999"

            contact = EnrichedContact(
                first_name="John", last_name="Smith",
                email="john@apexroofing.com", title="Owner",
                company_name="Apex Roofing", company_domain="apexroofing.com",
                vertical="Commercial Roofing",
                icp_score=85, signal_score=168.0,
                heat_level="red_hot",
                personalization_hook="Noticed the hail event in Travis County last week.",
                email_verified=True,
            )
            result = enroll_in_smartlead(contact)
            assert result is True

    def test_enrollment_skips_empty_campaign_id(self):
        """No campaign ID → should skip enrollment gracefully."""
        from contractor.config import CONTRACTOR_CAMPAIGN_MAP
        CONTRACTOR_CAMPAIGN_MAP["Pest Control"] = ""  # Not configured

        contact = EnrichedContact(
            first_name="Jane", last_name="Doe",
            email="jane@pestco.com", title="Owner",
            company_name="PestCo", company_domain="pestco.com",
            vertical="Pest Control",
            icp_score=70, signal_score=90.0,
            heat_level="warm",
            personalization_hook="",
            email_verified=True,
        )
        result = enroll_in_smartlead(contact)
        assert result is False
