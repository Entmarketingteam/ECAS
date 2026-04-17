"""Tests for tech-stack enrichment."""
import sqlite3
from unittest.mock import patch

import pytest

from enrichment.tech_stack import (
    TechStackProfile,
    enrich_company,
    _init_cache,
    _cache_get,
    _cache_put,
)


@pytest.fixture
def temp_cache_db(tmp_path):
    db = tmp_path / "tech_stack_cache.db"
    _init_cache(db)
    return db


def test_profile_derives_flags():
    p = TechStackProfile(
        domain="abcroofing.com",
        detected=["ServiceTitan", "HubSpot"],
    )
    assert p.domain == "abcroofing.com"
    assert "ServiceTitan" in p.detected


def test_apply_expected_sets_flags():
    p = TechStackProfile(domain="x.com", detected=["ServiceTitan"])
    p.apply_expected({
        "fsm": ["ServiceTitan", "Jobber"],
        "crm": ["HubSpot"],
        "sms": ["Twilio"],
    })
    assert p.has_category["fsm"] is True
    assert p.has_category["crm"] is False
    assert p.has_category["sms"] is False
    assert set(p.missing_categories) == {"crm", "sms"}


def test_cache_roundtrip(temp_cache_db):
    profile = TechStackProfile(domain="test.com", detected=["HubSpot"])
    _cache_put(temp_cache_db, profile)
    cached = _cache_get(temp_cache_db, "test.com", ttl_days=90)
    assert cached is not None
    assert cached.domain == "test.com"
    assert "HubSpot" in cached.detected


def test_cache_expires(temp_cache_db):
    profile = TechStackProfile(domain="expire.com", detected=["x"])
    _cache_put(temp_cache_db, profile)
    with sqlite3.connect(temp_cache_db) as conn:
        conn.execute(
            "UPDATE tech_stack_cache SET cached_at = datetime('now', '-100 days') WHERE domain = ?",
            ("expire.com",),
        )
    assert _cache_get(temp_cache_db, "expire.com", ttl_days=90) is None


def test_enrich_company_uses_cache(temp_cache_db):
    cached = TechStackProfile(domain="cached.com", detected=["HubSpot"])
    _cache_put(temp_cache_db, cached)
    with patch("enrichment.tech_stack._wappalyzer_scan") as scan:
        profile = enrich_company("https://cached.com", db=temp_cache_db)
    scan.assert_not_called()
    assert "HubSpot" in profile.detected


def test_enrich_company_scans_on_miss(temp_cache_db):
    with patch("enrichment.tech_stack._wappalyzer_scan") as scan, \
         patch("enrichment.tech_stack._builtwith_scan") as bw:
        scan.return_value = ["ServiceTitan"]
        bw.return_value = []
        profile = enrich_company("https://fresh.com", db=temp_cache_db)
    assert profile.detected == ["ServiceTitan"]
    with patch("enrichment.tech_stack._wappalyzer_scan") as scan2:
        enrich_company("https://fresh.com", db=temp_cache_db)
        scan2.assert_not_called()
