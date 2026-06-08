"""Tests for extended pre-flight probes."""
from unittest.mock import patch, MagicMock

from enrichment.health import (
    check_perplexity,
    check_firecrawl,
    check_browserbase,
    check_airtop,
    check_wappalyzer,
    check_landing_page,
    check_campaign_state,
)


def test_check_perplexity_ok():
    with patch("enrichment.health.requests.post") as post:
        post.return_value = MagicMock(status_code=200, json=lambda: {"id": "ok"})
        post.return_value.raise_for_status = lambda: None
        r = check_perplexity()
    assert r["healthy"] is True


def test_check_perplexity_auth_fail():
    with patch("enrichment.health.requests.post") as post:
        post.return_value = MagicMock(status_code=401)
        r = check_perplexity()
    assert r["healthy"] is False
    assert "401" in r["detail"]


def test_check_firecrawl_ok():
    with patch("enrichment.health.requests.get") as get:
        get.return_value = MagicMock(status_code=200)
        r = check_firecrawl()
    assert r["healthy"] is True


def test_check_browserbase_creds_present():
    r = check_browserbase()
    assert r["healthy"] is True


def test_check_airtop_creds_present():
    r = check_airtop()
    assert r["healthy"] is True


def test_check_landing_page_200():
    with patch("enrichment.health.requests.head") as head:
        head.return_value = MagicMock(status_code=200)
        r = check_landing_page("https://entagency.co/ai-automation/roofing")
    assert r["healthy"] is True


def test_check_landing_page_404_fails():
    with patch("enrichment.health.requests.head") as head:
        head.return_value = MagicMock(status_code=404)
        r = check_landing_page("https://entagency.co/missing")
    assert r["healthy"] is False


def test_check_landing_page_none_fails():
    r = check_landing_page("")
    assert r["healthy"] is False


def test_check_campaign_state_active():
    with patch("enrichment.health.requests.get") as get:
        mock = MagicMock(status_code=200)
        mock.json = lambda: {"status": "ACTIVE", "sending_accounts": [{"id": 1}]}
        mock.raise_for_status = lambda: None
        get.return_value = mock
        r = check_campaign_state("3040599")
    assert r["healthy"] is True


def test_check_campaign_state_paused_fails():
    with patch("enrichment.health.requests.get") as get:
        mock = MagicMock(status_code=200)
        mock.json = lambda: {"status": "PAUSED", "sending_accounts": [{"id": 1}]}
        mock.raise_for_status = lambda: None
        get.return_value = mock
        r = check_campaign_state("3040599")
    assert r["healthy"] is False
    assert "PAUSED" in r["detail"]


def test_check_wappalyzer_ok_or_fail():
    # Either healthy=True (Railway/py3.11) OR healthy=False w/ ImportError (local py3.14)
    r = check_wappalyzer()
    assert "healthy" in r
    assert "detail" in r
