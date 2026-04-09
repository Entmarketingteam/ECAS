"""
signals/ferc_poller.py
EIA Open Data API poller — replaces broken FERC eLibrary implementation.

Tracks new generator capacity additions by state and fuel type using the
EIA Operating Generator Capacity dataset (Form EIA-860/860M).
High MW additions in target states signal upstream EPC procurement activity.

API: https://api.eia.gov/v2/electricity/operating-generator-capacity/data/
Docs: https://www.eia.gov/opendata/
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

# Target states — high grid activity markets for EPC procurement
TARGET_STATES = ["VA", "TX", "PA", "OH", "NC", "GA", "FL", "NY", "IL", "CA"]

# Fuel type codes that signal EPC procurement (solar, wind, NG, nuclear, hydro, storage)
EPC_FUEL_TYPES = ["SUN", "WND", "NG", "NUC", "WAT", "MWH", "OTH"]

# EIA status codes — only track operating generators (newly added = first period appearing)
ACTIVE_STATUSES = ["OP"]

# Minimum MW threshold to create a signal (avoids noise from tiny rooftop installs)
MIN_MW_THRESHOLD = 10.0

# How many months back to look for "new" capacity entries
LOOKBACK_MONTHS = 3


def _get_cutoff_period() -> str:
    """Return YYYY-MM string for the lookback period start."""
    cutoff = datetime.now() - timedelta(days=LOOKBACK_MONTHS * 30)
    return cutoff.strftime("%Y-%m")


def _calculate_heat_score(capacity_mw: float) -> float:
    """
    Score based on capacity size.
    Base 15.0, +0.1 per 10 MW, capped at 50.0.
    """
    base = 15.0
    bonus = min((capacity_mw / 10.0) * 0.1, 35.0)
    return round(base + bonus, 1)


def _fuel_label(code: str) -> str:
    labels = {
        "SUN": "Solar",
        "WND": "Wind",
        "NG": "Natural Gas",
        "NUC": "Nuclear",
        "WAT": "Hydro",
        "MWH": "Battery Storage",
        "OTH": "Other",
    }
    return labels.get(code, code)


def fetch_eia_capacity_additions(months_back: int = LOOKBACK_MONTHS) -> list[dict]:
    """
    Query EIA API for recently added generator capacity in target states.
    Returns list of signal dicts ready for Airtable insertion.
    """
    api_key = EIA_API_KEY
    if not api_key:
        # TODO: Register a real EIA API key at https://www.eia.gov/opendata/register.php
        # and set EIA_API_KEY in Doppler (ecas/dev) + Railway env vars.
        logger.warning("[EIA] EIA_API_KEY not set — falling back to DEMO_KEY (rate-limited)")
        api_key = "DEMO_KEY"

    cutoff = _get_cutoff_period()
    signals = []
    seen_plants = set()  # Deduplicate by plant+period+fuel

    # Query each target state to keep response sizes manageable
    for state in TARGET_STATES:
        for fuel in EPC_FUEL_TYPES:
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
                    "length": 50,
                }

                resp = requests.get(
                    EIA_BASE_URL + CAPACITY_ENDPOINT,
                    params=params,
                    timeout=30,
                )

                if resp.status_code == 429:
                    logger.warning(f"[EIA] Rate limited for {state}/{fuel} — skipping")
                    continue
                if resp.status_code != 200:
                    logger.warning(f"[EIA] HTTP {resp.status_code} for {state}/{fuel}: {resp.text[:200]}")
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

                    plant_id = row.get("plantid", "")
                    period = row.get("period", "")
                    dedup_key = f"{plant_id}:{period}:{fuel}"
                    if dedup_key in seen_plants:
                        continue
                    seen_plants.add(dedup_key)

                    entity_name = row.get("entityName", "Unknown Utility")
                    plant_name = row.get("plantName", "Unknown Plant")
                    state_name = row.get("stateName", state)
                    ba_name = row.get("balancing-authority-name", "")
                    fuel_label = _fuel_label(fuel)
                    technology = row.get("technology", fuel_label)

                    raw_content = (
                        f"Plant: {plant_name} | Capacity: {capacity_mw} MW | "
                        f"Fuel: {fuel_label} ({technology}) | State: {state_name} | "
                        f"Balancing Authority: {ba_name} | Period: {period} | "
                        f"Entity: {entity_name} | Status: Operating"
                    )

                    signals.append({
                        "signal_type": "eia_capacity_addition",
                        "source": "EIA Open Data",
                        "company_name": entity_name,
                        "sector": "Power & Grid Infrastructure",
                        "signal_date": period + "-01",  # YYYY-MM → YYYY-MM-01
                        "raw_content": raw_content,
                        "heat_score": _calculate_heat_score(capacity_mw),
                        "notes": (
                            f"EIA Plant ID: {plant_id} | State: {state} | "
                            f"Fuel: {fuel} | MW: {capacity_mw}"
                        ),
                    })

            except requests.exceptions.Timeout:
                logger.warning(f"[EIA] Timeout for {state}/{fuel}")
            except Exception as e:
                logger.warning(f"[EIA] Error fetching {state}/{fuel}: {e}")

    logger.info(f"[EIA] {len(signals)} capacity signals found (>={MIN_MW_THRESHOLD} MW, last {months_back} months)")
    return signals


def run_poller(push_to_airtable: bool = True) -> dict:
    """
    Poll EIA for new generator capacity additions.
    Keeps same interface as the original FERC poller so the scheduler requires no changes.
    """
    signals = fetch_eia_capacity_additions(months_back=LOOKBACK_MONTHS)

    signals_pushed = 0
    if push_to_airtable and signals:
        try:
            from storage.airtable import get_client
            at = get_client()

            for sig in signals:
                try:
                    rid = at.insert_signal(
                        signal_type=sig["signal_type"],
                        source=sig["source"],
                        company_name=sig["company_name"],
                        sector=sig["sector"],
                        signal_date=sig["signal_date"],
                        raw_content=sig["raw_content"],
                        heat_score=sig["heat_score"],
                        notes=sig["notes"],
                    )
                    if rid:
                        signals_pushed += 1
                except Exception as e:
                    logger.warning(f"[EIA] Airtable insert failed: {e}")

        except Exception as e:
            logger.error(f"[EIA] Airtable client error: {e}")

    return {
        "eia_signals_found": len(signals),
        "signals_pushed": signals_pushed,
        # Keep backward-compat keys from old FERC poller
        "ferc_filings": 0,
        "rss_items": 0,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import json
    result = run_poller(push_to_airtable=False)
    print(json.dumps(result, indent=2))
