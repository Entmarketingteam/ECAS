"""
intelligence/sector_scoring.py
Calculates sector heat scores (0-100) by combining all signal types.
Pushes scored signals to Airtable for qualifying companies.
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import TARGET_SECTORS, SCORING_WEIGHTS, ALERT_THRESHOLDS, DB_PATH, TIMELINE_PHASES

logger = logging.getLogger(__name__)


def _normalize(value: float, min_val: float, max_val: float) -> float:
    """Normalize a value to 0-1 range."""
    if max_val <= min_val:
        return 0.0
    return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))


def score_politician_signal(sector: str) -> float:
    """
    Score politician trading activity for a sector (0-100).
    Based on trade count and unique politician count.
    """
    try:
        from signals.political.house_senate_trades import get_sector_stats
        stats = get_sector_stats(sector, ALERT_THRESHOLDS["politician_lookback_days"])
    except Exception as e:
        logger.warning(f"[Scoring] Could not get politician stats for {sector}: {e}")
        return 0.0

    trade_count = stats.get("trade_count", 0)
    unique_pols = stats.get("unique_politicians", 0)

    # Normalize
    trade_score = _normalize(trade_count, 0, 50) * 60  # Up to 60 pts
    pol_score = _normalize(unique_pols, 0, 15) * 40    # Up to 40 pts

    raw = trade_score + pol_score
    logger.debug(f"[Scoring] {sector} politician: {raw:.1f} ({trade_count} trades, {unique_pols} pols)")
    return min(raw, 100.0)


def score_hedge_fund_signal(sector: str) -> float:
    """Score institutional investor (13F) activity for a sector (0-100)."""
    try:
        from signals.political.sec_13f import get_sector_stats
        stats = get_sector_stats(sector, ALERT_THRESHOLDS["hedge_fund_lookback_days"])
    except Exception as e:
        logger.warning(f"[Scoring] Could not get 13F stats for {sector}: {e}")
        return 0.0

    position_count = stats.get("position_count", 0)
    unique_funds = stats.get("unique_funds", 0)

    pos_score = _normalize(position_count, 0, 150) * 60
    fund_score = _normalize(unique_funds, 0, 10) * 40
    raw = pos_score + fund_score

    logger.debug(f"[Scoring] {sector} hedge fund: {raw:.1f} ({position_count} positions, {unique_funds} funds)")
    return min(raw, 100.0)


def score_contract_signal(sector: str) -> float:
    """Score government contract activity for a sector (0-100)."""
    try:
        from signals.political.government_contracts import get_sector_stats
        stats = get_sector_stats(sector, ALERT_THRESHOLDS.get("contract_lookback_days", 90))
    except Exception as e:
        logger.warning(f"[Scoring] Could not get contract stats for {sector}: {e}")
        return 0.0

    contract_count = stats.get("contract_count", 0)
    total_value_m = stats.get("total_value_m", 0.0)

    count_score = _normalize(contract_count, 0, 100) * 40
    value_score = _normalize(total_value_m, 0, 5000) * 60  # $5B = max score
    raw = count_score + value_score

    logger.debug(f"[Scoring] {sector} contracts: {raw:.1f} ({contract_count} contracts, ${total_value_m:.0f}M)")
    return min(raw, 100.0)


def score_airtable_signals(sector: str) -> float:
    """Score based on recent Airtable signals (FERC + RSS)."""
    try:
        from storage.airtable import get_client
        at = get_client()
        signals = at.get_signals_by_sector(sector, days=30)
    except Exception as e:
        logger.warning(f"[Scoring] Could not get Airtable signals for {sector}: {e}")
        return 0.0

    if not signals:
        return 0.0

    # Average the heat scores from recent signals, capped at 100
    scores = [s.get("fields", {}).get("heat_score", 0) for s in signals]
    avg = sum(scores) / len(scores) if scores else 0
    recency_bonus = min(len(signals) * 2, 20)  # More signals = slight bonus
    return min(avg + recency_bonus, 100.0)


def calculate_sector_heat(sector: str) -> dict:
    """
    Calculate composite heat score for a sector.
    Returns dict with score, phase, and component breakdown.
    """
    weights = SCORING_WEIGHTS

    politician = score_politician_signal(sector) * weights.get("politician_signal", 0.25)
    hedge_fund = score_hedge_fund_signal(sector) * weights.get("hedge_fund_signal", 0.25)
    contract = score_contract_signal(sector) * weights.get("contract_signal", 0.30)
    airtable = score_airtable_signals(sector) * (
        weights.get("ferc_signal", 0.10) + weights.get("news_signal", 0.10)
    )

    composite = politician + hedge_fund + contract + airtable

    # Determine phase
    phase = "early_signal"
    for phase_name, phase_cfg in TIMELINE_PHASES.items():
        lo, hi = phase_cfg["heat_score_range"]
        if lo <= composite <= hi:
            phase = phase_name
            break
    if composite >= 80:
        phase = "active_spend"

    logger.info(f"[Scoring] {sector}: {composite:.1f}/100 → {phase}")
    return {
        "sector": sector,
        "heat_score": round(composite, 1),
        "phase": phase,
        "phase_config": TIMELINE_PHASES.get(phase, {}),
        "components": {
            "politician": round(politician, 1),
            "hedge_fund": round(hedge_fund, 1),
            "contract": round(contract, 1),
            "ferc_and_news": round(airtable, 1),
        },
        "scored_at": datetime.utcnow().isoformat(),
    }


def run_analysis() -> list[dict]:
    """Score all target sectors and return results."""
    results = []
    for sector in TARGET_SECTORS:
        try:
            result = calculate_sector_heat(sector)
            results.append(result)
        except Exception as e:
            logger.error(f"[Scoring] Failed to score {sector}: {e}")

    results.sort(key=lambda x: x["heat_score"], reverse=True)

    # Log summary
    logger.info("\n" + "=" * 60)
    logger.info("  SECTOR HEAT SCORES")
    logger.info("=" * 60)
    for r in results:
        logger.info(
            f"  {r['sector']}: {r['heat_score']}/100 "
            f"[{r['phase'].replace('_', ' ').title()}]"
        )
    logger.info("=" * 60)

    return results


if __name__ == "__main__":
    import json
    import logging
    logging.basicConfig(level=logging.INFO)
    results = run_analysis()
    print(json.dumps(results, indent=2))
