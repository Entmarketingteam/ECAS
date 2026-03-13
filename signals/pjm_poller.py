"""
signals/pjm_poller.py
PJM interconnection queue poller — uses EIA API as data source.

PJM Dataminer2 (dataminer2.pjm.com) is an Angular SPA that requires auth
and returns HTML, not JSON. This poller instead uses EIA operating generator
capacity data filtered to PJM balancing authority territory, which covers
the same geographic footprint (PJM states: PA, OH, NJ, MD, DE, VA, WV, KY,
IN, MI, IL, NC, TN).

The EIA data includes recently added generators in PJM territory — a strong
proxy for interconnection queue activity and upcoming EPC procurement.

API: https://api.eia.gov/v2/electricity/operating-generator-capacity/data/
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import EIA_API_KEY  # noqa: E402

logger = logging.getLogger(__name__)

EIA_BASE_URL = "https://api.eia.gov/v2"
CAPACITY_ENDPOINT = "/electricity/operating-generator-capacity/data/"

# PJM territory states (core footprint)
PJM_STATES = ["PA", "OH", "NJ", "MD", "DE", "VA", "WV", "KY", "IN", "MI", "IL", "NC"]

# PJM balancing authority codes
PJM_BA_CODES = ["PJM"]

# Fuel types with high EPC procurement signal in PJM territory
PJM_FUEL_TYPES = ["SUN", "WND", "NG", "NUC", "MWH"]

# Minimum MW for a signal to be worth tracking
MIN_MW_THRESHOLD = 25.0

# Lookback window — PJM data updates slower, 6 months is appropriate
LOOKBACK_MONTHS = 6


def _get_cutoff_period() -> str:
    """Return YYYY-MM for the lookback start."""
    cutoff = datetime.now() - timedelta(days=LOOKBACK_MONTHS * 30)
    return cutoff.strftime("%Y-%m")


def _calculate_heat_score(capacity_mw: float) -> float:
    """
    Base 12.0 for PJM signals (interconnection queue = earlier stage).
    +0.15 per 10 MW, capped at 45.0.
    """
    base = 12.0
    bonus = min((capacity_mw / 10.0) * 0.15, 33.0)
    return round(base + bonus, 1)


def _fuel_label(code: str) -> str:
    labels = {
        "SUN": "Solar",
        "WND": "Wind",
        "NG": "Natural Gas",
        "NUC": "Nuclear",
        "MWH": "Battery Storage",
    }
    return labels.get(code, code)


def fetch_pjm_territory_capacity(months_back: int = LOOKBACK_MONTHS) -> list[dict]:
    """
    Query EIA for recently added generator capacity in PJM territory states.
    Filters to large-scale projects (>=25 MW) which require EPC contractors.
    """
    api_key = EIA_API_KEY
    if not api_key:
        # TODO: Register a real EIA API key at https://www.eia.gov/opendata/register.php
        # and set EIA_API_KEY in Doppler (ecas/dev) + Railway env vars.
        logger.warning("[PJM] EIA_API_KEY not set — falling back to DEMO_KEY (rate-limited)")
        api_key = "DEMO_KEY"

    cutoff = _get_cutoff_period()
    signals = []
    seen_plants = set()

    for state in PJM_STATES:
        for fuel in PJM_FUEL_TYPES:
            try:
                params = {
                    "api_key": api_key,
                    "frequency": "monthly",
                    "data[0]": "nameplate-capacity-mw",
                    "facets[stateid][]": state,
                    "facets[energy_source_code][]": fuel,
                    "facets[status][]": "OP",
                    "start": cutoff,
                    "sort[0][column]": "period",
                    "sort[0][direction]": "desc",
                    "length": 30,
                }

                resp = requests.get(
                    EIA_BASE_URL + CAPACITY_ENDPOINT,
                    params=params,
                    timeout=30,
                )

                if resp.status_code == 429:
                    logger.warning(f"[PJM/EIA] Rate limited for {state}/{fuel} — skipping")
                    continue
                if resp.status_code != 200:
                    logger.warning(f"[PJM/EIA] HTTP {resp.status_code} for {state}/{fuel}: {resp.text[:200]}")
                    continue

                data = resp.json()
                rows = data.get("response", {}).get("data", [])

                for row in rows:
                    try:
                        capacity_mw = float(row.get("nameplate-capacity-mw") or 0)
                    except (ValueError, TypeError):
                        continue

                    if capacity_mw < MIN_MW_THRESHOLD:
                        continue

                    # Filter to PJM balancing authority if available
                    ba_code = row.get("balancing_authority_code", "")
                    if ba_code and ba_code != "PJM":
                        continue

                    plant_id = row.get("plantid", "")
                    period = row.get("period", "")
                    dedup_key = f"{plant_id}:{period}:{fuel}"
                    if dedup_key in seen_plants:
                        continue
                    seen_plants.add(dedup_key)

                    entity_name = row.get("entityName", "Unknown Utility")
                    plant_name = row.get("plantName", "Unknown Plant")
                    state_name = row.get("stateName", state)
                    ba_name = row.get("balancing-authority-name", "PJM")
                    fuel_label = _fuel_label(fuel)
                    technology = row.get("technology", fuel_label)

                    raw_content = (
                        f"PJM Territory Plant: {plant_name} | Capacity: {capacity_mw} MW | "
                        f"Fuel: {fuel_label} ({technology}) | State: {state_name} | "
                        f"Balancing Authority: {ba_name} | Period: {period} | "
                        f"Entity: {entity_name} | Status: Operating"
                    )

                    signals.append({
                        "signal_type": "pjm_capacity_addition",
                        "source": "EIA Open Data (PJM Territory)",
                        "company_name": entity_name,
                        "sector": "Power & Grid Infrastructure",
                        "signal_date": period + "-01",
                        "raw_content": raw_content,
                        "heat_score": _calculate_heat_score(capacity_mw),
                        "notes": (
                            f"EIA Plant ID: {plant_id} | PJM State: {state} | "
                            f"Fuel: {fuel} | MW: {capacity_mw} | BA: {ba_code or 'PJM'}"
                        ),
                    })

            except requests.exceptions.Timeout:
                logger.warning(f"[PJM/EIA] Timeout for {state}/{fuel}")
            except Exception as e:
                logger.warning(f"[PJM/EIA] Error fetching {state}/{fuel}: {e}")

    logger.info(
        f"[PJM] {len(signals)} PJM territory capacity signals found "
        f"(>={MIN_MW_THRESHOLD} MW, last {months_back} months)"
    )
    return signals


def run_poller(push_to_airtable: bool = True) -> dict:
    """
    Poll EIA for new generator capacity additions in PJM territory.
    Standard interface: run_poller(push_to_airtable=True) -> dict
    """
    signals = fetch_pjm_territory_capacity(months_back=LOOKBACK_MONTHS)

    signals_pushed = 0
    if push_to_airtable and signals:
        try:
            from storage.airtable import get_client
            at = get_client()

            for sig in signals:
                try:
                    at.insert_signal(
                        signal_type=sig["signal_type"],
                        source=sig["source"],
                        company_name=sig["company_name"],
                        sector=sig["sector"],
                        signal_date=sig["signal_date"],
                        raw_content=sig["raw_content"],
                        heat_score=sig["heat_score"],
                        notes=sig["notes"],
                    )
                    signals_pushed += 1
                except Exception as e:
                    logger.warning(f"[PJM] Airtable insert failed: {e}")

        except Exception as e:
            logger.error(f"[PJM] Airtable client error: {e}")

    return {
        "pjm_signals_found": len(signals),
        "signals_pushed": signals_pushed,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import json
    result = run_poller(push_to_airtable=False)
    print(json.dumps(result, indent=2))
