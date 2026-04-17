"""Tests for universal scraper router."""
from unittest.mock import patch

from discovery.directory_finder import DirectoryCandidate, ScraperType
from discovery.universal_scraper import scrape_candidates, ScrapedCompany


def test_routes_static_to_firecrawl():
    candidate = DirectoryCandidate(
        url="https://www.nrca.net/directory",
        scraper_type=ScraperType.STATIC,
        confidence=0.8,
    )
    with patch("discovery.universal_scraper._firecrawl_scrape") as fc, \
         patch("discovery.universal_scraper._airtop_scrape") as airtop, \
         patch("discovery.universal_scraper._browserbase_scrape") as bb:
        fc.return_value = [
            ScrapedCompany(name="ABC Roofing", website="abcroofing.com", source_url=candidate.url),
        ]
        results = scrape_candidates([candidate])

    fc.assert_called_once()
    airtop.assert_not_called()
    bb.assert_not_called()
    assert len(results) == 1
    assert results[0].name == "ABC Roofing"


def test_routes_gated_to_airtop():
    candidate = DirectoryCandidate(
        url="https://www.linkedin.com/events/123",
        scraper_type=ScraperType.GATED,
        confidence=0.9,
    )
    with patch("discovery.universal_scraper._firecrawl_scrape") as fc, \
         patch("discovery.universal_scraper._airtop_scrape") as airtop, \
         patch("discovery.universal_scraper._browserbase_scrape") as bb:
        airtop.return_value = []
        scrape_candidates([candidate])

    airtop.assert_called_once()
    fc.assert_not_called()
    bb.assert_not_called()


def test_routes_js_heavy_to_browserbase():
    candidate = DirectoryCandidate(
        url="https://app.swapcard.com/event/abc",
        scraper_type=ScraperType.JS_HEAVY,
        confidence=0.7,
    )
    with patch("discovery.universal_scraper._firecrawl_scrape") as fc, \
         patch("discovery.universal_scraper._airtop_scrape") as airtop, \
         patch("discovery.universal_scraper._browserbase_scrape") as bb:
        bb.return_value = []
        scrape_candidates([candidate])

    bb.assert_called_once()
    fc.assert_not_called()
    airtop.assert_not_called()


def test_dedupes_by_normalized_website():
    c1 = DirectoryCandidate(url="https://a.com", scraper_type=ScraperType.STATIC, confidence=0.8)
    c2 = DirectoryCandidate(url="https://b.com", scraper_type=ScraperType.STATIC, confidence=0.8)
    with patch("discovery.universal_scraper._firecrawl_scrape") as fc:
        fc.side_effect = [
            [ScrapedCompany(name="ABC", website="https://abc.com", source_url="a")],
            [ScrapedCompany(name="ABC Corp", website="abc.com/", source_url="b")],
        ]
        results = scrape_candidates([c1, c2])

    assert len(results) == 1
