"""Tests for Industry Factory scoring modes."""
import pytest

from enrichment.tech_stack import TechStackProfile
from lead_priority_scoring import score_company_by_mode


def test_positive_mode_uses_heat_only():
    score = score_company_by_mode(
        mode="positive",
        heat_score=75.0,
        tech_stack=None,
        prioritize_when_missing=[],
    )
    assert score == 75.0


def test_negative_tech_stack_boosts_when_missing_fsm():
    p = TechStackProfile(domain="x.com", detected=["HubSpot"])
    p.apply_expected({
        "fsm": ["ServiceTitan", "Jobber"],
        "crm": ["HubSpot"],
        "sms": ["Twilio"],
    })
    score = score_company_by_mode(
        mode="negative_tech_stack",
        heat_score=30.0,
        tech_stack=p,
        prioritize_when_missing=["fsm", "sms"],
    )
    assert 60 <= score <= 100


def test_negative_tech_stack_deprioritizes_mature():
    p = TechStackProfile(domain="mature.com", detected=["ServiceTitan", "HubSpot", "Twilio"])
    p.apply_expected({
        "fsm": ["ServiceTitan"],
        "crm": ["HubSpot"],
        "sms": ["Twilio"],
    })
    score = score_company_by_mode(
        mode="negative_tech_stack",
        heat_score=30.0,
        tech_stack=p,
        prioritize_when_missing=["fsm"],
    )
    assert score <= 30.0


def test_hybrid_averages_positive_and_negative():
    p = TechStackProfile(domain="x.com", detected=[])
    p.apply_expected({"fsm": ["ServiceTitan"], "crm": ["HubSpot"]})
    score = score_company_by_mode(
        mode="hybrid",
        heat_score=60.0,
        tech_stack=p,
        prioritize_when_missing=["fsm", "crm"],
    )
    assert 70 <= score <= 90


def test_unknown_mode_raises():
    with pytest.raises(ValueError, match="Unknown scoring_mode"):
        score_company_by_mode(
            mode="nonsense",
            heat_score=50.0,
            tech_stack=None,
            prioritize_when_missing=[],
        )
