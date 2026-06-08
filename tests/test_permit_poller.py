import json
import pytest
from unittest.mock import patch, MagicMock
from signals.permit_poller import parse_municipal_permits, poll_and_enrich_permits

def test_parse_municipal_permits():
    raw_data = [
        {"permit_num": "123", "contractor_name": "Dallas Custom Builders", "valuation": "150000", "permit_type": "New Construction"}
    ]
    parsed = parse_municipal_permits(raw_data)
    assert len(parsed) == 1
    assert parsed[0]["company_name"] == "Dallas Custom Builders"
    assert parsed[0]["valuation"] == 150000.0

@patch("signals.permit_poller.urllib.request.urlopen")
@patch("signals.permit_poller.resolve_domain")
@patch("signals.permit_poller.find_contacts_for_domain")
@patch("signals.permit_poller.verify_email_cascade")
@patch("signals.permit_poller.route_lead_to_n8n")
def test_poll_and_enrich_permits_success(
    mock_route, mock_verify, mock_find, mock_resolve, mock_urlopen
):
    # Mock urlopen context manager
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps([
        {"permit_num": "456", "contractor_name": "Collin County Construction", "valuation": "200000", "permit_type": "New Construction"}
    ]).encode()
    mock_urlopen.return_value.__enter__.return_value = mock_response

    mock_resolve.return_value = "collinbuilders.com"
    mock_find.return_value = [
        {"first_name": "John", "last_name": "Doe", "title": "Owner", "email": "john@collinbuilders.com"}
    ]
    mock_verify.return_value = ("verified_clean", "million_verifier")

    poll_and_enrich_permits()

    mock_resolve.assert_called_once_with("Collin County Construction")
    mock_find.assert_called_once_with("collinbuilders.com", ["Owner", "President", "VP of Construction", "Chief Estimator", "Project Executive"])
    mock_verify.assert_called_once_with("john@collinbuilders.com")
    mock_route.assert_called_once()
    
    # Assert route payload
    called_payload = mock_route.call_args[0][0]
    assert called_payload["email"] == "john@collinbuilders.com"
    assert called_payload["sector"] == "Custom Builders"
    assert called_payload["parent_project_valuation"] == 200000.0
    assert called_payload["parent_project_num"] == "456"
