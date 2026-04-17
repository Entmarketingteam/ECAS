"""Tests for industry orchestrator."""
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from signals.industry_runner import run_industry


def _mk_fixture_yaml(tmp_path: Path) -> Path:
    p = tmp_path / "fixture.yaml"
    p.write_text(
        "slug: fixture\n"
        "display_name: Fixture\n"
        "track: contract_motion\n"
        "campaign_id: '1234'\n"
        "revenue_range_m: [10, 100]\n"
        "naics: ['237130']\n"
        "titles: [CEO]\n"
        "states: [TX]\n"
        "apollo_keywords: [test]\n"
        "scoring_mode: positive\n"
        "directory_auto_discovery: false\n"
        "directory_seeds: ['https://example.com']\n"
        "budget_cap_per_run: 5\n"
    )
    return p


def test_dry_run_does_not_call_pipeline(tmp_path):
    _mk_fixture_yaml(tmp_path)

    with patch("signals.industry_runner._preflight") as pf, \
         patch("signals.industry_runner._discover_and_scrape") as scrape, \
         patch("signals.industry_runner._populate_projects") as pop:
        pf.return_value = {"status": "healthy", "failures": {}}
        mock_company = MagicMock()
        mock_company.name = "ABC"
        mock_company.website = "abc.com"
        mock_company.source_url = "x"
        scrape.return_value = [mock_company]

        result = run_industry("fixture", industries_dir=tmp_path, dry_run=True)

    pop.assert_not_called()
    assert result["status"] == "dry_run_ok"


def test_preflight_blocked_aborts(tmp_path):
    _mk_fixture_yaml(tmp_path)

    with patch("signals.industry_runner._preflight") as pf:
        pf.return_value = {"status": "blocked", "failures": {"apollo": {"detail": "dead"}}}
        result = run_industry("fixture", industries_dir=tmp_path, dry_run=False)

    assert result["status"] == "blocked"
    assert "apollo" in result["reason"]


def test_first_live_run_without_dryrun_raises(tmp_path):
    _mk_fixture_yaml(tmp_path)

    with patch("signals.industry_runner._has_dryrun_on_record") as hdr, \
         patch("signals.industry_runner._preflight") as pf:
        hdr.return_value = False
        pf.return_value = {"status": "healthy", "failures": {}}
        with pytest.raises(RuntimeError, match="Dry-run required"):
            run_industry("fixture", industries_dir=tmp_path, dry_run=False)


def test_budget_cap_truncates_companies(tmp_path):
    _mk_fixture_yaml(tmp_path)

    with patch("signals.industry_runner._preflight") as pf, \
         patch("signals.industry_runner._has_dryrun_on_record") as hdr, \
         patch("signals.industry_runner._discover_and_scrape") as scrape, \
         patch("signals.industry_runner._populate_projects") as pop, \
         patch("signals.industry_runner._run_downstream_pipeline") as pipe:
        pf.return_value = {"status": "healthy", "failures": {}}
        hdr.return_value = True
        companies = []
        for i in range(10):
            m = MagicMock()
            m.name = f"C{i}"
            m.website = f"c{i}.com"
            m.source_url = "x"
            companies.append(m)
        scrape.return_value = companies
        pop.return_value = {"created": 5, "existing": 0}
        pipe.return_value = {"status": "complete", "contacts_enrolled": 0}

        result = run_industry("fixture", industries_dir=tmp_path, dry_run=False)

    populated = pop.call_args[0][0]
    assert len(populated) == 5
