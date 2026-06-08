"""Tests for directory auto-discovery."""
from unittest.mock import patch

import pytest

from discovery.directory_finder import (
    DirectoryCandidate,
    ScraperType,
    discover_directories,
    classify_url,
)


def test_classify_static_url():
    assert classify_url("https://www.nrca.net/directory") == ScraperType.STATIC


def test_classify_linkedin_as_gated():
    assert classify_url("https://www.linkedin.com/events/123") == ScraperType.GATED


def test_classify_js_heavy_as_browserbase():
    for url in [
        "https://app.swapcard.com/event/xyz",
        "https://eventmobi.com/xyz",
    ]:
        assert classify_url(url) == ScraperType.JS_HEAVY


def test_discover_returns_candidates_with_confidence():
    mock_urls = [
        "https://www.nrca.net/directory",
        "https://www.roofingcontractor.com/top-100",
    ]

    with patch("discovery.directory_finder._perplexity_search") as pplx, \
         patch("discovery.directory_finder._extract_urls_with_claude") as claude:
        pplx.return_value = "Perplexity free-form response mentioning the URLs"
        claude.return_value = mock_urls

        candidates = discover_directories(
            industry_display_name="Commercial Roofing",
            keywords=["commercial roofing contractor"],
            min_confidence=0.0,
            min_results=1,
        )

    assert len(candidates) == 2
    assert all(isinstance(c, DirectoryCandidate) for c in candidates)


def test_discover_aborts_on_too_few_candidates():
    with patch("discovery.directory_finder._perplexity_search") as pplx, \
         patch("discovery.directory_finder._extract_urls_with_claude") as claude:
        pplx.return_value = "no results"
        claude.return_value = []

        with pytest.raises(RuntimeError, match="Insufficient directory candidates"):
            discover_directories(
                industry_display_name="Nonexistent Industry",
                keywords=["xyz"],
                min_results=3,
            )
