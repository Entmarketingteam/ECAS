import pytest
from unittest.mock import patch, MagicMock
from tools.n8n_router import route_lead_to_n8n, send_discord_alert, sync_dead_letter_queue_to_airtable

@patch("urllib.request.urlopen")
def test_route_lead_to_n8n(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.getcode.return_value = 200
    mock_resp.read.return_value = b'{"status": "success"}'
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    success = route_lead_to_n8n({
        "first_name": "John",
        "last_name": "Smith",
        "email": "john@builders.com",
        "sector": "Custom Builders"
    }, webhook_url="http://test-webhook")
    
    assert success is True

@patch("urllib.request.urlopen")
def test_send_discord_alert(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.getcode.return_value = 200
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    success = send_discord_alert("⚠️ Test Alert", webhook_url="http://discord-webhook")
    assert success is True

@patch("urllib.request.urlopen")
def test_sync_dead_letter_queue_to_airtable(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.getcode.return_value = 200
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    success = sync_dead_letter_queue_to_airtable(
        lead_data={
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@builders.com",
            "company_name": "Doe Builders",
            "title": "Owner",
            "linkedin_url": "https://linkedin.com/in/jane"
        },
        error_msg="Failed to route",
        airtable_key="test-key",
        base_id="test-base"
    )
    assert success is True
