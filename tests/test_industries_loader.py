"""Tests for industry loader."""
from pathlib import Path

import pytest

from industries._schema import Industry
from industries.loader import (
    load_industry,
    load_all_industries,
    IndustryNotFoundError,
)


def test_load_industry_from_fixture(industries_fixture_dir):
    ind = load_industry("test_industry", directory=industries_fixture_dir)
    assert isinstance(ind, Industry)
    assert ind.slug == "test_industry"
    assert ind.campaign_id == "9999999"


def test_load_missing_raises(industries_fixture_dir):
    with pytest.raises(IndustryNotFoundError):
        load_industry("no_such_industry", directory=industries_fixture_dir)


def test_load_all_industries_returns_dict(industries_fixture_dir):
    mapping = load_all_industries(directory=industries_fixture_dir)
    assert "test_industry" in mapping
    assert isinstance(mapping["test_industry"], Industry)


def test_load_all_ignores_private_and_non_yaml(tmp_path):
    (tmp_path / "_private.yaml").write_text("slug: x")
    (tmp_path / "readme.txt").write_text("ignore me")
    (tmp_path / "valid.yaml").write_text(
        "slug: valid\n"
        "display_name: Valid\n"
        "track: contract_motion\n"
        "campaign_id: '1'\n"
        "revenue_range_m: [1, 10]\n"
        "naics: ['1']\n"
        "titles: [x]\n"
        "states: [TX]\n"
        "apollo_keywords: [x]\n"
        "scoring_mode: positive\n"
    )
    mapping = load_all_industries(directory=tmp_path)
    assert "valid" in mapping
    assert "_private" not in mapping
    assert "readme" not in mapping
