"""
contractor/pipeline/signal_scorer.py — Multi-signal scoring engine.
Implements ColdIQ's compound scoring framework: 150+ Red Hot, 100-149 Hot, 50-99 Warm, 20-49 Cool.

Benchmark targets:
- Cold outreach: 6-8% reply rate
- Single signal: 18-22% reply rate
- Multi-signal (3+): 35-40% reply rate
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from contractor.config import CONTRACTOR_SIGNAL_WEIGHTS

logger = logging.getLogger(__name__)


@dataclass
class Signal:
    """A single detected signal for a company/contact."""
    type: str                          # Signal type key from CONTRACTOR_SIGNAL_WEIGHTS
    detected_at: datetime              # When the signal was first detected
    source: str                        # Where it came from (NOAA, permit API, Apollo, etc.)
    raw_data: dict = field(default_factory=dict)  # Original payload
    notes: str = ""                    # Human-readable context


@dataclass
class ScoredLead:
    """A lead with a compound signal score and routing instructions."""
    company_name: str
    company_domain: str
    vertical: str
    signals: list[Signal]
    score: float
    heat_level: str                    # "red_hot" | "hot" | "warm" | "cool" | "cold"
    sla_hours: int                     # How quickly to act
    action: str                        # What to do
    channel: str                       # "multichannel" | "email_only" | "nurture" | "exclude"
    personalization_hook: str = ""     # Signal-based opening line for copy gen
    strongest_signal: Optional[Signal] = None


# Recency multiplier table — stale signals lose value fast
RECENCY_MULTIPLIERS = [
    (1,  1.5),   # Last 24 hours → 1.5x
    (7,  1.2),   # Last 7 days → 1.2x
    (14, 1.0),   # Last 14 days → 1.0x (baseline)
    (30, 0.7),   # Last 30 days → 0.7x
]
STALE_MULTIPLIER = 0.3  # 30+ days old


# Action thresholds (ColdIQ framework)
HEAT_THRESHOLDS = [
    (150, "red_hot",  1,   "Immediate manual outreach by AE",          "multichannel"),
    (100, "hot",      24,  "Personalized Smartlead sequence + LinkedIn", "multichannel"),
    (50,  "warm",     72,  "Automated Smartlead sequence",               "email_only"),
    (20,  "cool",     168, "Marketing nurture, monitor for more signals","nurture"),
    (0,   "cold",     720, "Monitor only — no outreach",                 "exclude"),
]


def _recency_multiplier(detected_at: datetime) -> float:
    """Return the recency multiplier based on signal age."""
    age_days = (datetime.utcnow() - detected_at).days
    for days, multiplier in RECENCY_MULTIPLIERS:
        if age_days <= days:
            return multiplier
    return STALE_MULTIPLIER


def _heat_level(score: float) -> tuple[str, int, str, str]:
    """Return (heat_level, sla_hours, action, channel) for a given score."""
    for threshold, heat, sla, action, channel in HEAT_THRESHOLDS:
        if score >= threshold:
            return heat, sla, action, channel
    return "cold", 720, "Monitor only", "exclude"


def _build_personalization_hook(signals: list[Signal], vertical: str) -> str:
    """
    Build a signal-based personalization hook using the strongest signal.
    Uses ColdIQ's 'Lite Hook (Conceptual Tie)' pattern — reference the theme without quoting.
    """
    # Priority order for hook building
    hook_priority = [
        "hail_event_large",
        "franchise_new_territory",
        "competitor_acquisition",
        "fm_job_change",
        "commercial_permit_pulled",
        "hail_event_medium",
        "fm_job_posting",
        "new_location_opened",
        "commercial_building_sold",
        "hiring_spree",
        "contract_renewal_window",
    ]

    signal_by_type = {s.type: s for s in signals}

    for signal_type in hook_priority:
        if signal_type in signal_by_type:
            s = signal_by_type[signal_type]
            hooks = {
                "hail_event_large": f"Noticed the hail event in {s.raw_data.get('county', 'your area')} last week — the replacement window is short.",
                "hail_event_medium": f"Saw the hail activity in {s.raw_data.get('county', 'your region')} recently.",
                "franchise_new_territory": f"Noticed {s.raw_data.get('franchise', 'a national franchise')} just opened territory in your market.",
                "competitor_acquisition": f"Saw that {s.raw_data.get('acquirer', 'a national operator')} just acquired {s.raw_data.get('target', 'a local competitor')} in your area.",
                "fm_job_change": f"Looks like {s.raw_data.get('company', 'a building')} in your area just brought on a new facility manager.",
                "commercial_permit_pulled": f"Noticed {s.raw_data.get('address', 'a commercial property')} pulled a permit recently — new construction or major renovation.",
                "fm_job_posting": f"Saw {s.raw_data.get('company', 'a company')} is hiring a facility manager — usually signals a vendor change is coming.",
                "new_location_opened": f"Noticed {s.raw_data.get('company', 'a business')} just opened a new location nearby.",
                "hiring_spree": f"Saw {s.raw_data.get('company', 'a company')} is scaling fast — more locations usually means more facility needs.",
                "contract_renewal_window": f"Based on typical contract cycles, {s.raw_data.get('company', 'your target account')} is likely in renewal window.",
            }
            return hooks.get(signal_type, "")

    return ""  # Fallback: no hook (use core-static relevance in copy gen)


def score_lead(
    company_name: str,
    company_domain: str,
    vertical: str,
    signals: list[Signal],
) -> ScoredLead:
    """
    Score a lead using the ColdIQ multi-signal compound scoring framework.

    Args:
        company_name: Target company name
        company_domain: Company website domain (for dedup)
        vertical: "Commercial Janitorial" | "Commercial Roofing" | "Pest Control"
        signals: List of detected signals for this company

    Returns:
        ScoredLead with compound score, heat level, routing, and personalization hook
    """
    if not signals:
        return ScoredLead(
            company_name=company_name,
            company_domain=company_domain,
            vertical=vertical,
            signals=[],
            score=0,
            heat_level="cold",
            sla_hours=720,
            action="Monitor only — no signals",
            channel="exclude",
        )

    # Compound scoring: sum(signal_weight × recency_multiplier) for all signals
    compound_score = 0.0
    strongest_signal = None
    strongest_points = 0.0

    for signal in signals:
        base_points = CONTRACTOR_SIGNAL_WEIGHTS.get(signal.type, 5)
        multiplier = _recency_multiplier(signal.detected_at)
        weighted = base_points * multiplier
        compound_score += weighted

        if weighted > strongest_points:
            strongest_points = weighted
            strongest_signal = signal

    heat, sla, action, channel = _heat_level(compound_score)
    hook = _build_personalization_hook(signals, vertical)

    logger.info(
        "Scored %s | vertical=%s | signals=%d | score=%.1f | heat=%s",
        company_name, vertical, len(signals), compound_score, heat
    )

    return ScoredLead(
        company_name=company_name,
        company_domain=company_domain,
        vertical=vertical,
        signals=signals,
        score=compound_score,
        heat_level=heat,
        sla_hours=sla,
        action=action,
        channel=channel,
        personalization_hook=hook,
        strongest_signal=strongest_signal,
    )


def score_batch(leads: list[dict]) -> list[ScoredLead]:
    """
    Score a batch of leads. Each dict must have:
    - company_name, company_domain, vertical, signals (list of Signal objects)

    Returns list sorted by score descending (highest priority first).
    """
    scored = []
    for lead in leads:
        try:
            result = score_lead(
                company_name=lead["company_name"],
                company_domain=lead["company_domain"],
                vertical=lead["vertical"],
                signals=lead["signals"],
            )
            scored.append(result)
        except Exception as e:
            logger.error("Failed to score lead %s: %s", lead.get("company_name", "?"), e)

    # Sort by score descending — highest priority first
    scored.sort(key=lambda x: x.score, reverse=True)
    return scored


def filter_actionable(scored_leads: list[ScoredLead], min_heat: str = "warm") -> list[ScoredLead]:
    """
    Filter to only actionable leads (warm or above by default).

    min_heat options: "red_hot" | "hot" | "warm" | "cool"
    """
    heat_order = {"red_hot": 4, "hot": 3, "warm": 2, "cool": 1, "cold": 0}
    min_level = heat_order.get(min_heat, 2)
    return [lead for lead in scored_leads if heat_order.get(lead.heat_level, 0) >= min_level]
