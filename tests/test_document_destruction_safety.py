from unittest.mock import MagicMock, patch

from signals.shredding_association_scraper import scrape_shredding_members
from tools.n8n_router import build_pending_review_fields
from outreach.smartlead import _resolve_campaign_id


def test_verified_shredding_leads_are_queued_for_review_not_routed_to_n8n():
    html = '<div class="member-name"><h2>Metro Shredding Corp</h2></div>'

    with patch("urllib.request.urlopen") as mock_urlopen, \
        patch("signals.shredding_association_scraper.resolve_domain", return_value="metroshredding.com"), \
        patch("signals.shredding_association_scraper.find_contacts_for_domain", return_value=[{
            "first_name": "Jane",
            "last_name": "Doe",
            "title": "Office Manager",
            "email": "jane@metroshredding.com",
            "company_name": "Metro Shredding Corp",
        }]), \
        patch("signals.shredding_association_scraper.verify_email_cascade", return_value=("verified_clean", "million_verifier")), \
        patch("signals.shredding_association_scraper.route_lead_to_n8n") as mock_route_n8n, \
        patch("signals.shredding_association_scraper.sync_pending_review_to_airtable") as mock_pending_review:
        mock_resp = MagicMock()
        mock_resp.read.return_value = html.encode()
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        scrape_shredding_members()

        mock_route_n8n.assert_not_called()
        mock_pending_review.assert_called_once()
        lead = mock_pending_review.call_args[0][0]
        assert lead["sector"] == "Document Destruction"
        assert lead["verification_status"] == "verified_clean"


def test_pending_review_fields_preserve_sector_and_reason_without_smartlead_id():
    fields = build_pending_review_fields(
        {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@metroshredding.com",
            "company_name": "Metro Shredding Corp",
            "title": "Office Manager",
            "sector": "Document Destruction",
            "verification_status": "verified_clean",
            "source": "million_verifier",
        },
        "Verified document destruction lead queued for manual approval",
    )

    assert fields["outreach_status"] == "pending_review"
    assert "smartlead_campaign_id" not in fields
    assert "Document Destruction" in fields["analyst_notes"]
    assert "manual approval" in fields["analyst_notes"]


def test_unmapped_sector_does_not_fallback_to_power_grid_campaign():
    assert _resolve_campaign_id("Totally Unknown Vertical") is None
    assert _resolve_campaign_id("Document Destruction") is None
