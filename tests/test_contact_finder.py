import pytest
from unittest.mock import patch, MagicMock
from tools.contact_finder import find_contacts_for_domain

@patch("urllib.request.urlopen")
def test_find_contacts_success(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = b"""{
        "people": [{
            "first_name": "John",
            "last_name": "Smith",
            "title": "Owner",
            "email": "john.smith@custombuilders.com",
            "linkedin_url": "https://linkedin.com/in/johnsmith"
        }]
    }"""
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    contacts = find_contacts_for_domain("custombuilders.com", ["owner"], api_key="test_key")
    assert len(contacts) == 1
    assert contacts[0]["first_name"] == "John"
    assert contacts[0]["email"] == "john.smith@custombuilders.com"
