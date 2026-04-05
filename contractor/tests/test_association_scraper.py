"""Tests for contractor/signals/association_scraper.py"""
import pytest
from unittest.mock import patch, MagicMock
from contractor.tests.test_signal_scrapers_shared import assert_valid_signal


MOCK_NRCA_MARKDOWN = """
## Find a Contractor Results

**Apex Roofing Solutions**
123 Main St, Austin, TX 78701
Phone: (512) 555-0100
Website: [apexroofingsolutions.com](https://apexroofingsolutions.com)

**Summit Commercial Roofing**
456 Oak Ave, Dallas, TX 75201
Phone: (214) 555-0200
Website: [summitroofing.com](https://summitroofing.com)
"""

MOCK_NPMA_MARKDOWN = """
## Find a Pro Results

**Austin Pest Professionals**
789 Cedar St, Austin, TX 78702
Website: [austinpestpro.com](https://austinpestpro.com)

**Capital City Pest Control**
321 Elm Dr, Austin, TX 78703
Website: [capitalcitypest.com](https://capitalcitypest.com)
"""

MOCK_ISSA_HTML = """
<html><body>
<div class="member-listing">
  <div class="member">
    <h3 class="member-name">CleanTech Janitorial</h3>
    <span class="member-city">Houston</span>
    <span class="member-state">TX</span>
    <a href="https://cleantechjanitorial.com" class="member-website">cleantechjanitorial.com</a>
  </div>
  <div class="member">
    <h3 class="member-name">Premier Building Services</h3>
    <span class="member-city">Dallas</span>
    <span class="member-state">TX</span>
  </div>
</div>
<a class="next-page" href="/dir?page=2">Next</a>
</body></html>
"""


class TestNrcaScraper:
    @patch("contractor.signals.association_scraper.signal_exists", return_value=False)
    @patch("contractor.signals.association_scraper._firecrawl_scrape")
    def test_parses_companies_from_nrca_markdown(self, mock_fc, mock_exists):
        from contractor.signals.association_scraper import scrape_nrca_state
        mock_fc.return_value = MOCK_NRCA_MARKDOWN

        signals = scrape_nrca_state("TX")

        assert len(signals) == 2
        assert_valid_signal(signals[0])
        assert signals[0]["vertical"] == "Commercial Roofing"
        assert signals[0]["signal_type"] == "industry_association_member"
        assert signals[0]["source"] == "NRCA"
        assert "apexroofingsolutions.com" in signals[0]["company_domain"]

    @patch("contractor.signals.association_scraper.signal_exists", return_value=True)
    @patch("contractor.signals.association_scraper._firecrawl_scrape")
    def test_skips_already_seen_companies(self, mock_fc, mock_exists):
        from contractor.signals.association_scraper import scrape_nrca_state
        mock_fc.return_value = MOCK_NRCA_MARKDOWN
        signals = scrape_nrca_state("TX")
        assert signals == []

    @patch("contractor.signals.association_scraper._firecrawl_scrape")
    def test_handles_firecrawl_failure_gracefully(self, mock_fc):
        from contractor.signals.association_scraper import scrape_nrca_state
        mock_fc.side_effect = Exception("Firecrawl timeout")
        signals = scrape_nrca_state("TX")
        assert signals == []


class TestNpmaScraper:
    @patch("contractor.signals.association_scraper.signal_exists", return_value=False)
    @patch("contractor.signals.association_scraper._firecrawl_scrape")
    def test_parses_companies_from_npma_markdown(self, mock_fc, mock_exists):
        from contractor.signals.association_scraper import scrape_npma_state
        mock_fc.return_value = MOCK_NPMA_MARKDOWN

        signals = scrape_npma_state("TX")

        assert len(signals) == 2
        assert_valid_signal(signals[0])
        assert signals[0]["vertical"] == "Pest Control"
        assert signals[0]["signal_type"] == "industry_association_member"
        assert signals[0]["source"] == "NPMA"


class TestIssaScraper:
    @patch("contractor.signals.association_scraper.signal_exists", return_value=False)
    @patch("contractor.signals.association_scraper.requests.get")
    def test_parses_companies_from_issa_html(self, mock_get, mock_exists):
        from contractor.signals.association_scraper import scrape_issa_page
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.text = MOCK_ISSA_HTML

        signals, has_next = scrape_issa_page(1)

        assert len(signals) == 2
        assert_valid_signal(signals[0])
        assert signals[0]["vertical"] == "Commercial Janitorial"
        assert signals[0]["source"] == "ISSA"
        assert has_next is True

    @patch("contractor.signals.association_scraper.signal_exists", return_value=False)
    @patch("contractor.signals.association_scraper.requests.get")
    def test_detects_last_page(self, mock_get, mock_exists):
        from contractor.signals.association_scraper import scrape_issa_page
        html_no_next = MOCK_ISSA_HTML.replace('<a class="next-page" href="/dir?page=2">Next</a>', "")
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.text = html_no_next
        _, has_next = scrape_issa_page(1)
        assert has_next is False


class TestRunAssociationScraper:
    @patch("contractor.signals.association_scraper.push_signals")
    @patch("contractor.signals.association_scraper.scrape_issa_page")
    @patch("contractor.signals.association_scraper.scrape_npma_state")
    @patch("contractor.signals.association_scraper.scrape_nrca_state")
    def test_run_returns_total_pushed(self, mock_nrca, mock_npma, mock_issa, mock_push):
        from contractor.signals.association_scraper import run_association_scraper

        mock_nrca.return_value = [{"company_name": "RoofCo", "company_domain": "roofco.com",
                                    "vertical": "Commercial Roofing", "vertical_type": "contractor",
                                    "signal_type": "industry_association_member",
                                    "detected_at": "2026-04-05T10:00:00", "source": "NRCA",
                                    "processed": False, "raw_data_json": {}}]
        mock_npma.return_value = []
        mock_issa.return_value = ([], False)
        mock_push.return_value = 1

        result = run_association_scraper()
        assert result >= 0
