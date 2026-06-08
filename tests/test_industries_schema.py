"""Tests for industry YAML schema."""
import pytest
from pydantic import ValidationError

from industries._schema import Industry, ScoringMode, Track


def test_valid_industry_parses():
    data = {
        "slug": "data_center",
        "display_name": "Data Center & AI Infrastructure",
        "track": "contract_motion",
        "campaign_id": "3040599",
        "revenue_range_m": [20, 300],
        "naics": ["236220", "237130"],
        "titles": ["VP Operations", "Director BD"],
        "states": ["VA", "TX"],
        "apollo_keywords": ["data center epc"],
        "scoring_mode": "positive",
        "min_heat": 50.0,
    }
    ind = Industry(**data)
    assert ind.slug == "data_center"
    assert ind.scoring_mode == ScoringMode.POSITIVE
    assert ind.track == Track.CONTRACT_MOTION


def test_slug_must_be_lowercase_underscore():
    with pytest.raises(ValidationError):
        Industry(
            slug="Data-Center",
            display_name="x", track="contract_motion", campaign_id="1",
            revenue_range_m=[1, 10], naics=["1"], titles=["x"],
            states=["TX"], apollo_keywords=["x"], scoring_mode="positive",
        )


def test_revenue_range_must_have_two_values():
    with pytest.raises(ValidationError):
        Industry(
            slug="x", display_name="x", track="contract_motion", campaign_id="1",
            revenue_range_m=[1],
            naics=["1"], titles=["x"], states=["TX"],
            apollo_keywords=["x"], scoring_mode="positive",
        )


def test_negative_scoring_requires_expected_stack():
    with pytest.raises(ValidationError) as exc:
        Industry(
            slug="x", display_name="x", track="ai_automation", campaign_id="1",
            revenue_range_m=[1, 10], naics=["1"], titles=["x"], states=["TX"],
            apollo_keywords=["x"], scoring_mode="negative_tech_stack",
        )
    assert "expected_stack_if_mature" in str(exc.value)


def test_defaults_applied():
    ind = Industry(
        slug="x", display_name="x", track="contract_motion", campaign_id="1",
        revenue_range_m=[1, 10], naics=["1"], titles=["x"], states=["TX"],
        apollo_keywords=["x"], scoring_mode="positive",
    )
    assert ind.signal_ttl_days == 90
    assert ind.budget_cap_per_run == 50
    assert ind.directory_auto_discovery is True
    assert ind.min_heat == 50.0
