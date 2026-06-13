import pytest
from unittest.mock import patch, MagicMock
from signals.shredding_association_scraper import (
    parse_shredding_association,
    scrape_shredding_members
)
from tools.load_shredding_leads import load_commercial_shredding_leads

def test_parse_shredding_association():
    html = '<div class="member-name"><h2>Metro Shredding Corp</h2></div>'
    parsed = parse_shredding_association(html)
    assert len(parsed) == 1
    assert parsed[0] == "Metro Shredding Corp"

# Tests for scrape_shredding_members

@patch("signals.shredding_association_scraper.sync_dead_letter_queue_to_airtable")
@patch("signals.shredding_association_scraper.sync_pending_review_to_airtable")
@patch("signals.shredding_association_scraper.route_lead_to_n8n")
@patch("signals.shredding_association_scraper.verify_email_cascade")
@patch("signals.shredding_association_scraper.find_contacts_for_domain")
@patch("signals.shredding_association_scraper.resolve_domain")
@patch("urllib.request.urlopen")
def test_scrape_shredding_members_success(
    mock_urlopen,
    mock_resolve_domain,
    mock_find_contacts,
    mock_verify_cascade,
    mock_route_n8n,
    mock_pending_review,
    mock_sync_dlq
):
    # Mock urlopen
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'<div class="member-name"><h2>Metro Shredding Corp</h2></div>'
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    # Mock resolving domain
    mock_resolve_domain.return_value = "metroshredding.com"

    # Mock finding contacts
    mock_find_contacts.return_value = [
        {
            "first_name": "Jane",
            "last_name": "Doe",
            "title": "Office Manager",
            "email": "jane@metroshredding.com"
        }
    ]

    # Mock email verifier
    mock_verify_cascade.return_value = ("verified_clean", "million_verifier")

    scrape_shredding_members()

    mock_resolve_domain.assert_called_once_with("Metro Shredding Corp")
    mock_find_contacts.assert_called_once_with("metroshredding.com", ["Office Manager", "VP Operations", "HR Director", "Facilities Manager", "General Counsel"])
    mock_verify_cascade.assert_called_once_with("jane@metroshredding.com")
    
    # Verify lead is held for manual review, not routed to n8n/Smartlead
    mock_route_n8n.assert_not_called()
    mock_pending_review.assert_called_once()
    routed_lead = mock_pending_review.call_args[0][0]
    assert routed_lead["email"] == "jane@metroshredding.com"
    assert routed_lead["verification_status"] == "verified_clean"
    assert routed_lead["source"] == "million_verifier"
    assert routed_lead["sector"] == "Document Destruction"
    mock_sync_dlq.assert_not_called()

@patch("signals.shredding_association_scraper.sync_dead_letter_queue_to_airtable")
@patch("signals.shredding_association_scraper.route_lead_to_n8n")
@patch("signals.shredding_association_scraper.find_contacts_for_domain")
@patch("signals.shredding_association_scraper.resolve_domain")
@patch("urllib.request.urlopen")
def test_scrape_shredding_members_no_domain(
    mock_urlopen,
    mock_resolve_domain,
    mock_find_contacts,
    mock_route_n8n,
    mock_sync_dlq
):
    # Mock urlopen
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'<div class="member-name"><h2>Metro Shredding Corp</h2></div>'
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    mock_resolve_domain.return_value = None

    scrape_shredding_members()

    mock_resolve_domain.assert_called_once_with("Metro Shredding Corp")
    mock_find_contacts.assert_not_called()
    mock_route_n8n.assert_not_called()
    
    # Log to DLQ
    mock_sync_dlq.assert_called_once()
    lead_data = mock_sync_dlq.call_args[0][0]
    assert lead_data["company_name"] == "Metro Shredding Corp"
    assert mock_sync_dlq.call_args[0][1] == "Domain not resolved"

@patch("signals.shredding_association_scraper.sync_dead_letter_queue_to_airtable")
@patch("signals.shredding_association_scraper.route_lead_to_n8n")
@patch("signals.shredding_association_scraper.find_contacts_for_domain")
@patch("signals.shredding_association_scraper.resolve_domain")
@patch("urllib.request.urlopen")
def test_scrape_shredding_members_no_contacts(
    mock_urlopen,
    mock_resolve_domain,
    mock_find_contacts,
    mock_route_n8n,
    mock_sync_dlq
):
    # Mock urlopen
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'<div class="member-name"><h2>Metro Shredding Corp</h2></div>'
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    mock_resolve_domain.return_value = "metroshredding.com"
    mock_find_contacts.return_value = []

    scrape_shredding_members()

    mock_resolve_domain.assert_called_once_with("Metro Shredding Corp")
    mock_find_contacts.assert_called_once()
    mock_route_n8n.assert_not_called()
    
    # Log to DLQ
    mock_sync_dlq.assert_called_once()
    lead_data = mock_sync_dlq.call_args[0][0]
    assert lead_data["company_name"] == "Metro Shredding Corp"
    assert lead_data["domain"] == "metroshredding.com"
    assert mock_sync_dlq.call_args[0][1] == "No contacts found"

@patch("signals.shredding_association_scraper.send_discord_alert")
@patch("urllib.request.urlopen")
def test_scrape_shredding_members_critical_exception(
    mock_urlopen,
    mock_send_alert
):
    # Mock urlopen to raise exception
    mock_urlopen.side_effect = Exception("Connection timed out")

    scrape_shredding_members()

    # Verify exception is handled and discord alert sent
    mock_send_alert.assert_called_once()
    assert "CRITICAL" in mock_send_alert.call_args[0][0]
    assert "Connection timed out" in mock_send_alert.call_args[0][0]


# Tests for load_commercial_shredding_leads

@patch("tools.load_shredding_leads.sync_dead_letter_queue_to_airtable")
@patch("tools.load_shredding_leads.sync_pending_review_to_airtable")
@patch("tools.load_shredding_leads.route_lead_to_n8n")
@patch("tools.load_shredding_leads.verify_email_cascade")
@patch("tools.load_shredding_leads.find_contacts_for_domain")
@patch("tools.load_shredding_leads.resolve_domain")
def test_load_commercial_shredding_leads_success(
    mock_resolve_domain,
    mock_find_contacts,
    mock_verify_cascade,
    mock_route_n8n,
    mock_pending_review,
    mock_sync_dlq
):
    raw_lists = [{"company_name": "Dallas Premium Legal Partners"}]

    # Mock resolving domain
    mock_resolve_domain.return_value = "dallaslegal.com"

    # Mock finding contacts
    mock_find_contacts.return_value = [
        {
            "first_name": "John",
            "last_name": "Smith",
            "title": "General Counsel",
            "email": "john@dallaslegal.com"
        }
    ]

    # Mock email verifier
    mock_verify_cascade.return_value = ("catch_all_verified", "findymail")

    load_commercial_shredding_leads(raw_lists)

    mock_resolve_domain.assert_called_once_with("Dallas Premium Legal Partners")
    mock_find_contacts.assert_called_once_with("dallaslegal.com", ["Office Manager", "Facilities Manager", "HR Director", "General Counsel"])
    mock_verify_cascade.assert_called_once_with("john@dallaslegal.com")
    
    # Verify lead is held for manual review, not routed to n8n/Smartlead
    mock_route_n8n.assert_not_called()
    mock_pending_review.assert_called_once()
    routed_lead = mock_pending_review.call_args[0][0]
    assert routed_lead["email"] == "john@dallaslegal.com"
    assert routed_lead["verification_status"] == "catch_all_verified"
    assert routed_lead["source"] == "findymail"
    assert routed_lead["sector"] == "Document Destruction"
    mock_sync_dlq.assert_not_called()

@patch("tools.load_shredding_leads.sync_dead_letter_queue_to_airtable")
@patch("tools.load_shredding_leads.route_lead_to_n8n")
@patch("tools.load_shredding_leads.find_contacts_for_domain")
@patch("tools.load_shredding_leads.resolve_domain")
def test_load_commercial_shredding_leads_no_domain(
    mock_resolve_domain,
    mock_find_contacts,
    mock_route_n8n,
    mock_sync_dlq
):
    raw_lists = [{"company_name": "Dallas Premium Legal Partners"}]
    mock_resolve_domain.return_value = None

    load_commercial_shredding_leads(raw_lists)

    mock_resolve_domain.assert_called_once_with("Dallas Premium Legal Partners")
    mock_find_contacts.assert_not_called()
    mock_route_n8n.assert_not_called()
    
    # Log to DLQ
    mock_sync_dlq.assert_called_once()
    lead_data = mock_sync_dlq.call_args[0][0]
    assert lead_data["company_name"] == "Dallas Premium Legal Partners"
    assert mock_sync_dlq.call_args[0][1] == "Domain not resolved"
