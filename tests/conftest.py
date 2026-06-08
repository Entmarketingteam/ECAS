"""Shared pytest fixtures for Industry Factory tests."""
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture(autouse=True)
def _mock_env(monkeypatch):
    """Default env vars so config.py loads cleanly in tests."""
    defaults = {
        "AIRTABLE_API_KEY": "test_at_key",
        "APOLLO_API_KEY": "test_apollo_key",
        "FINDYMAIL_API_KEY": "test_fm_key",
        "SMARTLEAD_API_KEY": "test_sl_key",
        "ANTHROPIC_API_KEY": "test_anthropic_key",
        "PERPLEXITY_API_KEY": "test_pplx_key",
        "FIRECRAWL_API_KEY": "test_fc_key",
        "BROWSERBASE_API_KEY": "test_bb_key",
        "BROWSERBASE_PROJECT_ID": "test_bb_proj",
        "AIRTOP_API_KEY": "test_airtop_key",
        "SLACK_ACCESS_TOKEN": "test_slack_token",
    }
    for k, v in defaults.items():
        if not os.environ.get(k):
            monkeypatch.setenv(k, v)


@pytest.fixture
def fixtures_dir():
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def industries_fixture_dir(fixtures_dir):
    return fixtures_dir / "industries"
