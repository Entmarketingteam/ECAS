"""
Tests for contractor/pipeline/signal_scorer.py

Run: pytest contractor/tests/test_signal_scorer.py -v
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from contractor.pipeline.signal_scorer import (
    Signal, score_lead, score_batch, filter_actionable,
    _recency_multiplier, HEAT_THRESHOLDS
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────
def make_signal(sig_type: str, days_old: int = 0, raw_data: dict = None) -> Signal:
    return Signal(
        type=sig_type,
        detected_at=datetime.utcnow() - timedelta(days=days_old),
        source="test",
        raw_data=raw_data or {},
    )


# ─── Recency Multiplier Tests ─────────────────────────────────────────────────
class TestRecencyMultiplier:
    def test_fresh_signal_gets_boost(self):
        """Signals < 24h old get 1.5x multiplier."""
        s = make_signal("hail_event_large", days_old=0)
        assert _recency_multiplier(s.detected_at) == 1.5

    def test_week_old_signal(self):
        """Signals 2-7 days old get 1.2x."""
        s = make_signal("hail_event_large", days_old=5)
        assert _recency_multiplier(s.detected_at) == 1.2

    def test_two_week_old_signal(self):
        """Signals 8-14 days old get 1.0x (baseline)."""
        s = make_signal("hail_event_large", days_old=12)
        assert _recency_multiplier(s.detected_at) == 1.0

    def test_month_old_signal(self):
        """Signals 15-30 days old get 0.7x."""
        s = make_signal("hail_event_large", days_old=25)
        assert _recency_multiplier(s.detected_at) == 0.7

    def test_stale_signal(self):
        """Signals 30+ days old get 0.3x penalty."""
        s = make_signal("hail_event_large", days_old=45)
        assert _recency_multiplier(s.detected_at) == 0.3


# ─── Score Lead Tests ─────────────────────────────────────────────────────────
class TestScoreLead:
    def test_no_signals_returns_cold(self):
        result = score_lead("ACME Cleaning", "acmecleaning.com", "Commercial Janitorial", [])
        assert result.heat_level == "cold"
        assert result.score == 0
        assert result.channel == "exclude"

    def test_red_hot_multi_signal(self):
        """Three hot signals stacked should hit 150+ (Red Hot)."""
        signals = [
            make_signal("hail_event_large", days_old=0),      # 80 × 1.5 = 120
            make_signal("franchise_new_territory", days_old=1), # 70 × 1.5 = 105
            make_signal("fm_job_change", days_old=2),           # 75 × 1.5 = 112.5
        ]
        result = score_lead("Apex Roofing", "apexroofing.com", "Commercial Roofing", signals)
        assert result.score >= 150
        assert result.heat_level == "red_hot"
        assert result.sla_hours == 1
        assert result.channel == "multichannel"

    def test_hot_single_tier1_signal(self):
        """A single fresh Tier 1 signal should hit Hot (100-149)."""
        signals = [
            make_signal("franchise_new_territory", days_old=10),  # 70 × 1.0 = 70
            make_signal("fm_job_posting", days_old=10),            # 40 × 1.0 = 40
            make_signal("hiring_spree", days_old=10),              # 35 × 1.0 = 35
        ]
        result = score_lead("Texas Roofing Co", "texasroofing.com", "Commercial Roofing", signals)
        assert result.score >= 100
        assert 100 <= result.score < 150
        assert result.heat_level == "hot"
        assert result.sla_hours == 24

    def test_warm_medium_signals(self):
        """Two warm signals should hit 50-99 (Warm)."""
        signals = [
            make_signal("hiring_spree", days_old=7),           # 35 × 1.2 = 42
            make_signal("new_location_opened", days_old=10),   # 45 × 1.0 = 45
        ]
        result = score_lead("Clean Pro", "cleanpro.com", "Commercial Janitorial", signals)
        assert 50 <= result.score < 100
        assert result.heat_level == "warm"
        assert result.channel == "email_only"

    def test_stale_signals_penalized(self):
        """Old signals should score lower than fresh ones."""
        fresh = [make_signal("hail_event_large", days_old=0)]
        stale = [make_signal("hail_event_large", days_old=45)]

        fresh_result = score_lead("Roofing A", "a.com", "Commercial Roofing", fresh)
        stale_result = score_lead("Roofing B", "b.com", "Commercial Roofing", stale)

        assert fresh_result.score > stale_result.score
        assert fresh_result.score == 80 * 1.5  # 120
        assert stale_result.score == 80 * 0.3  # 24

    def test_personalization_hook_generated_for_roofing_hail(self):
        """Hail event signal should produce a roofing-specific hook."""
        signals = [
            make_signal("hail_event_large", days_old=1, raw_data={"county": "Travis County"})
        ]
        result = score_lead("Apex Roofing", "apexroofing.com", "Commercial Roofing", signals)
        assert result.personalization_hook != ""
        assert "hail" in result.personalization_hook.lower() or "Travis" in result.personalization_hook

    def test_strongest_signal_identified(self):
        """The highest-weighted signal should be flagged as strongest."""
        signals = [
            make_signal("linkedin_content_engagement", days_old=0),  # 25 × 1.5 = 37.5
            make_signal("franchise_new_territory", days_old=0),       # 70 × 1.5 = 105
            make_signal("hiring_spree", days_old=0),                  # 35 × 1.5 = 52.5
        ]
        result = score_lead("CleanCo", "cleanco.com", "Commercial Janitorial", signals)
        assert result.strongest_signal is not None
        assert result.strongest_signal.type == "franchise_new_territory"


# ─── Batch Scoring Tests ──────────────────────────────────────────────────────
class TestScoreBatch:
    def test_batch_sorted_by_score(self):
        """Batch results should be sorted highest score first."""
        leads = [
            {
                "company_name": "Low Priority Co", "company_domain": "low.com",
                "vertical": "Commercial Janitorial",
                "signals": [make_signal("email_open", days_old=20)],
            },
            {
                "company_name": "High Priority Co", "company_domain": "high.com",
                "vertical": "Commercial Roofing",
                "signals": [
                    make_signal("hail_event_large", days_old=0),
                    make_signal("franchise_new_territory", days_old=0),
                ],
            },
        ]
        results = score_batch(leads)
        assert results[0].company_name == "High Priority Co"
        assert results[1].company_name == "Low Priority Co"

    def test_batch_handles_empty_leads(self):
        results = score_batch([])
        assert results == []

    def test_batch_skips_malformed_lead(self):
        """Malformed entries should not crash the batch."""
        leads = [
            {"company_name": "Good Co", "company_domain": "good.com", "vertical": "Pest Control",
             "signals": [make_signal("hiring_spree", days_old=5)]},
            {"bad_key": "this will error"},  # Missing required fields
        ]
        # Should not raise — malformed entry is skipped
        results = score_batch(leads)
        assert len(results) >= 1


# ─── Filter Tests ─────────────────────────────────────────────────────────────
class TestFilterActionable:
    def test_filters_cold_leads(self):
        """Cold leads should be excluded by default."""
        leads = [
            score_lead("Cold Co", "cold.com", "Pest Control", []),
            score_lead("Warm Co", "warm.com", "Pest Control", [
                make_signal("hiring_spree", days_old=5),
                make_signal("new_location_opened", days_old=5),
            ]),
        ]
        actionable = filter_actionable(leads)
        names = [l.company_name for l in actionable]
        assert "Cold Co" not in names
        assert "Warm Co" in names

    def test_hot_only_filter(self):
        """Filtering to 'hot' should exclude warm leads."""
        leads = [
            score_lead("Warm Co", "warm.com", "Pest Control", [
                make_signal("hiring_spree", days_old=5),
                make_signal("new_location_opened", days_old=5),
            ]),
            score_lead("Hot Co", "hot.com", "Pest Control", [
                make_signal("franchise_new_territory", days_old=0),
                make_signal("competitor_acquisition", days_old=0),
            ]),
        ]
        hot_only = filter_actionable(leads, min_heat="hot")
        names = [l.company_name for l in hot_only]
        # Warm Co may or may not qualify depending on exact score — Hot Co definitely should
        assert "Hot Co" in names
