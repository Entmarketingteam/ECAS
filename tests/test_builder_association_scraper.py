import pytest
from unittest.mock import patch, MagicMock
from signals.builder_association_scraper import (
    parse_association_page,
    scrape_and_enrich_association_builders
)

def test_parse_association_page():
    html_content = '<h3><a href="/member/smith-homes">Smith Homes</a></h3>'
    parsed = parse_association_page(html_content)
    assert len(parsed) == 1
    assert parsed[0] == "Smith Homes"

@patch("signals.builder_association_scraper.sync_dead_letter_queue_to_airtable")
@patch("signals.builder_association_scraper.route_lead_to_n8n")
@patch("signals.builder_association_scraper.verify_email_cascade")
@patch("signals.builder_association_scraper.find_contacts_for_domain")
@patch("signals.builder_association_scraper.resolve_domain")
@patch("urllib.request.urlopen")
def test_scrape_and_enrich_association_builders_success(
    mock_urlopen,
    mock_resolve_domain,
    mock_find_contacts,
    mock_verify_cascade,
    mock_route_n8n,
    mock_sync_dlq
):
    # Mock urlopen for fetching the directory page
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'<h3><a href="/member/smith-homes">Smith Homes</a></h3>'
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    # Mock domain resolver
    mock_resolve_domain.return_value = "smithhomes.com"

    # Mock contact finder
    mock_find_contacts.return_value = [
        {
            "first_name": "John",
            "last_name": "Smith",
            "title": "President",
            "email": "john@smithhomes.com",
            "linkedin_url": "https://linkedin.com/in/johnsmith"
        }
    ]

    # Mock email verifier
    mock_verify_cascade.return_value = ("verified_clean", "million_verifier")

    scrape_and_enrich_association_builders()

    # Verify calls
    mock_resolve_domain.assert_called_once_with("Smith Homes")
    mock_find_contacts.assert_called_once_with("smithhomes.com", ["Owner", "President", "VP of Construction", "Chief Estimator"])
    mock_verify_cascade.assert_called_once_with("john@smithhomes.com")
    
    # Verify successfully routed lead
    mock_route_n8n.assert_called_once()
    routed_lead = mock_route_n8n.call_args[0][0]
    assert routed_lead["email"] == "john@smithhomes.com"
    assert routed_lead["verification_status"] == "verified_clean"
    assert routed_lead["source"] == "million_verifier"
    assert routed_lead["sector"] == "Custom Builders"
    mock_sync_dlq.assert_not_called()

@patch("signals.builder_association_scraper.sync_dead_letter_queue_to_airtable")
@patch("signals.builder_association_scraper.route_lead_to_n8n")
@patch("signals.builder_association_scraper.find_contacts_for_domain")
@patch("signals.builder_association_scraper.resolve_domain")
@patch("urllib.request.urlopen")
def test_scrape_and_enrich_association_builders_no_domain(
    mock_urlopen,
    mock_resolve_domain,
    mock_find_contacts,
    mock_route_n8n,
    mock_sync_dlq
):
    # Mock urlopen
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'<h3><a href="/member/smith-homes">Smith Homes</a></h3>'
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    # Domain resolution fails
    mock_resolve_domain.return_value = None

    scrape_and_enrich_association_builders()

    mock_resolve_domain.assert_called_once_with("Smith Homes")
    mock_find_contacts.assert_not_called()
    mock_route_n8n.assert_not_called()
    
    # Log to DLQ
    mock_sync_dlq.assert_called_once()
    lead_data = mock_sync_dlq.call_args[0][0]
    assert lead_data["company_name"] == "Smith Homes"
    assert mock_sync_dlq.call_args[0][1] == "Domain not resolved"

@patch("signals.builder_association_scraper.sync_dead_letter_queue_to_airtable")
@patch("signals.builder_association_scraper.route_lead_to_n8n")
@patch("signals.builder_association_scraper.find_contacts_for_domain")
@patch("signals.builder_association_scraper.resolve_domain")
@patch("urllib.request.urlopen")
def test_scrape_and_enrich_association_builders_no_contacts(
    mock_urlopen,
    mock_resolve_domain,
    mock_find_contacts,
    mock_route_n8n,
    mock_sync_dlq
):
    # Mock urlopen
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'<h3><a href="/member/smith-homes">Smith Homes</a></h3>'
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    mock_resolve_domain.return_value = "smithhomes.com"
    
    # Contact lookup fails to find contacts
    mock_find_contacts.return_value = []

    scrape_and_enrich_association_builders()

    mock_resolve_domain.assert_called_once_with("Smith Homes")
    mock_find_contacts.assert_called_once()
    mock_route_n8n.assert_not_called()
    
    # Log to DLQ
    mock_sync_dlq.assert_called_once()
    lead_data = mock_sync_dlq.call_args[0][0]
    assert lead_data["company_name"] == "Smith Homes"
    assert lead_data["domain"] == "smithhomes.com"
    assert mock_sync_dlq.call_args[0][1] == "No contacts found"

@patch("signals.builder_association_scraper.sync_dead_letter_queue_to_airtable")
@patch("signals.builder_association_scraper.route_lead_to_n8n")
@patch("signals.builder_association_scraper.verify_email_cascade")
@patch("signals.builder_association_scraper.find_contacts_for_domain")
@patch("signals.builder_association_scraper.resolve_domain")
@patch("urllib.request.urlopen")
def test_scrape_and_enrich_association_builders_invalid_email(
    mock_urlopen,
    mock_resolve_domain,
    mock_find_contacts,
    mock_verify_cascade,
    mock_route_n8n,
    mock_sync_dlq
):
    # Mock urlopen
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'<h3><a href="/member/smith-homes">Smith Homes</a></h3>'
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    mock_resolve_domain.return_value = "smithhomes.com"
    mock_find_contacts.return_value = [
        {
            "first_name": "John",
            "last_name": "Smith",
            "title": "President",
            "email": "john@smithhomes.com"
        }
    ]
    
    # Email is risky/bounced
    mock_verify_cascade.return_value = ("bounced", "million_verifier")

    scrape_and_enrich_association_builders()

    mock_route_n8n.assert_not_called()
    
    # Log to DLQ
    mock_sync_dlq.assert_called_once()
    lead_data = mock_sync_dlq.call_args[0][0]
    assert lead_data["email"] == "john@smithhomes.com"
    assert lead_data["verification_status"] == "bounced"
    assert mock_sync_dlq.call_args[0][1] == "Email verification returned: bounced"

@patch("signals.builder_association_scraper.send_discord_alert")
@patch("urllib.request.urlopen")
def test_scrape_and_enrich_association_builders_critical_exception(
    mock_urlopen,
    mock_send_alert
):
    # Mock urlopen to raise exception
    mock_urlopen.side_effect = Exception("Connection timed out")

    scrape_and_enrich_association_builders()

    # Verify exception is handled and discord alert sent
    mock_send_alert.assert_called_once()
    assert "CRITICAL" in mock_send_alert.call_args[0][0]
    assert "Connection timed out" in mock_send_alert.call_args[0][0]
