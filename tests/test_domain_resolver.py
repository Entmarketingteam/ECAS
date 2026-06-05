import pytest
from unittest.mock import patch, MagicMock
from tools.domain_resolver import resolve_domain, extract_domain_from_url

def test_extract_domain():
    assert extract_domain_from_url("https://www.smithbuilders.com/about") == "smithbuilders.com"
    assert extract_domain_from_url("http://dallasshredding.co.uk/contact?id=1") == "dallasshredding.co.uk"
    assert extract_domain_from_url("invalid_url") is None
    assert extract_domain_from_url(None) is None
    assert extract_domain_from_url(123) is None

@patch("urllib.request.urlopen")
def test_resolve_domain_serpapi_success(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'{"organic_results": [{"link": "https://www.dallascustomhomes.com"}]}'
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    domain = resolve_domain("Dallas Custom Homes Inc", api_key="test_key")
    assert domain == "dallascustomhomes.com"

@patch("urllib.request.urlopen")
def test_resolve_domain_ddg_fallback_success(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'<html><body><a class="result__url" href="https://html.duckduckgo.com/html/?uddg=https%3A%2F%2Fwww.fallbackbuilders.com">fallback</a></body></html>'
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    domain = resolve_domain("Fallback Builders", api_key="")
    assert domain == "fallbackbuilders.com"

@patch("urllib.request.urlopen")
def test_resolve_domain_serpapi_fails_ddg_fallback_success(mock_urlopen):
    def side_effect(req, *args, **kwargs):
        url_str = req.full_url if hasattr(req, "full_url") else str(req)
        if "serpapi.com" in url_str:
            raise Exception("SerpAPI limit exceeded")
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'<html><body><a class="result__url" href="https://html.duckduckgo.com/html/?uddg=https%3A%2F%2Fwww.ddgbuilders.com">ddg</a></body></html>'
        mock_enter = MagicMock()
        mock_enter.__enter__.return_value = mock_resp
        return mock_enter

    mock_urlopen.side_effect = side_effect

    domain = resolve_domain("DDG Builders", api_key="test_key")
    assert domain == "ddgbuilders.com"

def test_resolve_domain_empty_inputs():
    assert resolve_domain("") is None
    assert resolve_domain(None) is None
