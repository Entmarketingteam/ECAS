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


# ─── FM Job Watcher tests ─────────────────────────────────────────────────────
MOCK_APOLLO_FM_RESPONSE = {
    "people": [
        {
            "id": "apollo123",
            "first_name": "Sarah",
            "last_name": "Johnson",
            "title": "Facilities Manager",
            "organization": {
                "name": "Westfield Properties LLC",
                "website_url": "westfieldproperties.com",
                "employee_count": 85,
            },
            "city": "Austin",
            "state": "TX",
        }
    ]
}

MOCK_RSS_FEED_ENTRIES = [
    {
        "title": "Skyline Corp hiring Facilities Manager in Austin TX",
        "link": "https://news.google.com/articles/abc123",
        "published": "Sun, 05 Apr 2026 08:00:00 GMT",
        "summary": "Skyline Corp announced it is seeking a Facilities Manager for its Austin campus",
    }
]


class TestFmJobWatcher:
    @patch("contractor.signals.fm_job_watcher.APOLLO_API_KEY", "test-key")
    @patch("contractor.signals.fm_job_watcher.signal_exists", return_value=False)
    @patch("contractor.signals.fm_job_watcher.requests.post")
    def test_apollo_job_change_produces_signal(self, mock_post, mock_exists):
        from contractor.signals.fm_job_watcher import fetch_apollo_fm_changes
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = MagicMock()
        mock_post.return_value.json.return_value = MOCK_APOLLO_FM_RESPONSE

        signals = fetch_apollo_fm_changes()
        assert len(signals) == 1
        assert_valid_signal(signals[0])
        assert signals[0]["signal_type"] == "fm_job_change"
        assert signals[0]["company_name"] == "Westfield Properties LLC"

    @patch("contractor.signals.fm_job_watcher.signal_exists", return_value=False)
    @patch("contractor.signals.fm_job_watcher.feedparser.parse")
    @patch("contractor.signals.fm_job_watcher.requests.get")
    def test_rss_job_posting_produces_signal(self, mock_requests_get, mock_parse, mock_exists):
        from contractor.signals.fm_job_watcher import fetch_rss_fm_postings
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.raise_for_status = MagicMock()
        mock_requests_get.return_value.content = b"<rss/>"
        mock_feed = MagicMock()
        mock_feed.entries = MOCK_RSS_FEED_ENTRIES
        mock_parse.return_value = mock_feed

        signals = fetch_rss_fm_postings("TX")
        assert len(signals) >= 1
        assert_valid_signal(signals[0])
        assert signals[0]["signal_type"] == "fm_job_posting"


class TestCompetitorWatcher:
    @patch("contractor.signals.competitor_watcher.signal_exists", return_value=False)
    @patch("contractor.signals.competitor_watcher.requests.get")
    @patch("contractor.signals.competitor_watcher.feedparser.parse")
    def test_franchise_expansion_detected(self, mock_parse, mock_get, mock_exists):
        import feedparser
        from contractor.signals.competitor_watcher import fetch_franchise_rss
        mock_get.return_value.content = b""
        mock_parse.return_value = feedparser.util.FeedParserDict({
            "entries": [{
                "title": "Jan-Pro Cleaning & Disinfecting Opens New Franchise Location in Houston TX",
                "link": "https://www.businesswire.com/jan-pro-houston",
                "published": "Sat, 04 Apr 2026 10:00:00 GMT",
                "summary": "Jan-Pro has opened a new territory serving the Houston metropolitan area.",
            }]
        })
        signals = fetch_franchise_rss("Commercial Janitorial")
        assert len(signals) >= 1
        assert_valid_signal(signals[0])
        assert signals[0]["signal_type"] == "franchise_new_territory"

    @patch("contractor.signals.competitor_watcher.signal_exists", return_value=False)
    @patch("contractor.signals.competitor_watcher.requests.get")
    @patch("contractor.signals.competitor_watcher.feedparser.parse")
    def test_osha_citation_detected(self, mock_parse, mock_get, mock_exists):
        import feedparser
        from contractor.signals.competitor_watcher import fetch_osha_rss
        mock_get.return_value.content = b""
        mock_parse.return_value = feedparser.util.FeedParserDict({
            "entries": [{
                "title": "Austin Pest Control Company Cited by OSHA for Safety Violations",
                "link": "https://news.example.com/osha-pest",
                "published": "Sat, 04 Apr 2026 09:00:00 GMT",
                "summary": "Austin Pest Control was fined $45,000 by OSHA following an inspection.",
            }]
        })
        signals = fetch_osha_rss("Pest Control")
        assert len(signals) >= 1
        assert_valid_signal(signals[0])
        assert signals[0]["signal_type"] == "osha_citation"


class TestRtoWatcher:
    @patch("contractor.signals.rto_watcher.signal_exists", return_value=False)
    @patch("contractor.signals.rto_watcher.requests.get")
    @patch("contractor.signals.rto_watcher.feedparser.parse")
    def test_rto_announcement_detected(self, mock_parse, mock_get, mock_exists):
        mock_get.return_value.content = b""
        import feedparser
        from contractor.signals.rto_watcher import fetch_rto_signals
        mock_parse.return_value = feedparser.util.FeedParserDict({
            "entries": [{
                "title": "Dell Technologies Requires Austin Employees to Return to Office Full-Time",
                "link": "https://news.example.com/dell-rto",
                "published": "Sat, 04 Apr 2026 09:00:00 GMT",
                "summary": "Dell has announced a mandatory return-to-office policy starting May 1.",
            }]
        })
        signals = fetch_rto_signals("Austin, TX")
        assert len(signals) >= 1
        assert_valid_signal(signals[0])
        assert signals[0]["signal_type"] == "rto_announcement"
        assert signals[0]["vertical"] == "Commercial Janitorial"

    @patch("contractor.signals.rto_watcher.signal_exists", return_value=False)
    @patch("contractor.signals.rto_watcher.requests.get")
    @patch("contractor.signals.rto_watcher.feedparser.parse")
    def test_commercial_lease_detected(self, mock_parse, mock_get, mock_exists):
        mock_get.return_value.content = b""
        import feedparser
        from contractor.signals.rto_watcher import fetch_lease_signals
        mock_parse.return_value = feedparser.util.FeedParserDict({
            "entries": [{
                "title": "TechCorp Signs 50,000 SqFt Office Lease in Austin TX",
                "link": "https://news.example.com/techcorp-lease",
                "published": "Sat, 04 Apr 2026 10:00:00 GMT",
                "summary": "TechCorp has signed a long-term commercial lease in downtown Austin.",
            }]
        })
        signals = fetch_lease_signals("Austin, TX")
        assert len(signals) >= 1
        assert_valid_signal(signals[0])
        assert signals[0]["signal_type"] == "commercial_lease_signed"
        assert signals[0]["vertical"] == "Commercial Janitorial"
