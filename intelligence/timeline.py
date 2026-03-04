"""
intelligence/timeline.py
Determines cascade phase and recommended outreach timing for each sector.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import TIMELINE_PHASES, TARGET_SECTORS

logger = logging.getLogger(__name__)


def get_phase(heat_score: float) -> tuple[str, dict]:
    """Return (phase_name, phase_config) for a given heat score."""
    for phase_name, cfg in TIMELINE_PHASES.items():
        lo, hi = cfg["heat_score_range"]
        if lo <= heat_score < hi:
            return phase_name, cfg
    # Default to active_spend for score >= 80
    if heat_score >= 80:
        return "active_spend", TIMELINE_PHASES["active_spend"]
    return "early_signal", TIMELINE_PHASES["early_signal"]


def generate_outreach_plan(sector: str, heat_score: float, top_companies: list[dict] = None) -> dict:
    """
    Generate a concrete outreach plan for a sector based on heat score.
    Returns actionable next steps for the ECAS sales team.
    """
    phase_name, phase_cfg = get_phase(heat_score)

    plan = {
        "sector": sector,
        "heat_score": heat_score,
        "phase": phase_name,
        "months_to_unlock": phase_cfg.get("months_to_unlock", "unknown"),
        "phase_description": phase_cfg.get("description", ""),
        "immediate_action": phase_cfg.get("action", ""),
        "generated_at": datetime.utcnow().isoformat(),
    }

    # Phase-specific outreach tactics
    if phase_name == "early_signal":
        plan["tactics"] = [
            "Build sector-specific case studies (grid modernization ROI)",
            "Join utility/EPC LinkedIn groups and engage 2-3x/week",
            "Map decision-makers at top 20 EPCs in target geography (VA, TX)",
            "Set Google Alerts for target company names + 'contract', 'awarded', 'expansion'",
        ]
        plan["outreach_message"] = (
            "Not yet — build credibility first. "
            "Publish 2 case studies on grid EPC BD challenges."
        )

    elif phase_name == "confirmed_signal":
        plan["tactics"] = [
            "Launch warm LinkedIn outreach to VP Ops and VPs BD at target EPCs",
            "Use voice notes on LinkedIn to collapse trust curve",
            "Lead with: 'I track grid capex movements — Duke Energy just committed $2.1B in your region'",
            "Frame as 'competitive insurance' — show what competitors are doing",
        ]
        plan["outreach_message"] = (
            "Start warm outreach NOW. 50 personalized LinkedIn touches/week. "
            "Reference the specific capital signals you've tracked."
        )

    elif phase_name == "imminent_unlock":
        plan["tactics"] = [
            "Direct outreach to VP Operations + Owner/CEO at target EPCs",
            "Quantify the bleed: 'Every month without positioned BD = $200K missed in pipeline'",
            "Offer 90-day pilots tied to specific contract opportunities you've identified",
            "Present your pre-bid intelligence as the pitch — not your service, your data",
        ]
        plan["outreach_message"] = (
            "Aggressive outreach. RFPs dropping in 1-3 months. "
            "Call, email, LinkedIn — multi-channel. Lead with the intelligence."
        )

    elif phase_name == "active_spend":
        plan["tactics"] = [
            "Close deals this week — budgets are deploying NOW",
            "Contact before any RFPs publish — position as already-trusted advisor",
            "Chain reaction pitch: 'Your competitors are already in conversations with [Utility]'",
            "Offer 30-day rapid deployment — they don't have 6 months to evaluate",
        ]
        plan["outreach_message"] = (
            "Emergency mode. Budget windows are open. "
            "Every day of delay = lost revenue. Close fast."
        )

    # Add company-specific targeting if provided
    if top_companies:
        plan["target_companies"] = [
            {
                "company": c.get("company", ""),
                "score": c.get("score", 0),
                "reason": c.get("reason", ""),
            }
            for c in top_companies[:10]
        ]

    return plan


def run_analysis(sector_scores: list[dict] = None) -> list[dict]:
    """
    Generate timeline predictions for all sectors.
    If sector_scores provided, uses them; otherwise runs scoring.
    """
    if not sector_scores:
        from intelligence.sector_scoring import run_analysis as score_sectors
        sector_scores = score_sectors()

    plans = []
    for sector_data in sector_scores:
        plan = generate_outreach_plan(
            sector=sector_data["sector"],
            heat_score=sector_data["heat_score"],
        )
        plan["components"] = sector_data.get("components", {})
        plans.append(plan)

    logger.info(f"[Timeline] Generated plans for {len(plans)} sectors")
    return plans


if __name__ == "__main__":
    import json
    import logging
    logging.basicConfig(level=logging.INFO)
    results = run_analysis()
    print(json.dumps(results, indent=2))
