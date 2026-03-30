"""
signals/census_construction.py
Census Bureau construction spending and building permits tracker.

Construction Spending API: https://api.census.gov/data/timeseries/eits/vip
Building Permits API: https://api.census.gov/data/2024/cbp

Tracks month-over-month changes in construction spending categories:
  - Power (private), Manufacturing (private), Highway/street,
    Water supply, Sewage/waste disposal
Flags spending jumps >5% MoM as capex signals for EPC demand.

heat_score: 5-10% increase=10, 10-20%=15, >20%=20
Deduplicates by time_period in SQLite table `census_construction`.
"""

import json
import logging
import os
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DB_PATH

logger = logging.getLogger(__name__)

# Census API base URLs
CONSTRUCTION_SPENDING_URL = "https://api.census.gov/data/timeseries/eits/vip"
BUILDING_PERMITS_URL = "https://api.census.gov/data/2024/cbp"

# API key from env (free registration at api.census.gov)
CENSUS_API_KEY = os.environ.get("CENSUS_API_KEY", "")

# Rate limit between API calls
RATE_LIMIT_SECONDS = 0.5

# Construction spending category codes and their ECAS sector mappings
# These are VIP (Value of Construction Put in Place) category codes
SPENDING_CATEGORIES = {
    # Private construction
    "PVT_POWER": {
        "code": "PVT_POWER",  # Private power construction
        "label": "Private Power Construction",
        "sector": "Power & Grid Infrastructure",
    },
    "PVT_MFG": {
        "code": "PVT_MFG",  # Private manufacturing construction
        "label": "Private Manufacturing Construction",
        "sector": "Industrial & Manufacturing Facilities",
    },
    # Public construction
    "PUB_HWY": {
        "code": "PUB_HWY",  # Public highway and street
        "label": "Public Highway & Street Construction",
        "sector": "Power & Grid Infrastructure",
    },
    "PUB_WS": {
        "code": "PUB_WS",  # Public water supply
        "label": "Public Water Supply Construction",
        "sector": "Water & Wastewater Infrastructure",
    },
    "PUB_SWD": {
        "code": "PUB_SWD",  # Public sewage and waste disposal
        "label": "Public Sewage & Waste Disposal Construction",
        "sector": "Water & Wastewater Infrastructure",
    },
}

# MoM change thresholds and heat scores
THRESHOLDS = {
    "min_change_pct": 5.0,   # Minimum MoM % change to flag
    "tier1_pct": 5.0,        # 5-10% → heat_score 10
    "tier2_pct": 10.0,       # 10-20% → heat_score 15
    "tier3_pct": 20.0,       # >20% → heat_score 20
}

# Building permits NAICS code for power line construction
PERMITS_NAICS = "237130"  # Power line and communication line construction


def _ensure_db(db_path: Path) -> None:
    """Create SQLite table for deduplication."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS census_construction (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time_period TEXT,
            category_code TEXT,
            category_label TEXT,
            sector TEXT,
            cell_value REAL,
            prev_value REAL,
            change_pct REAL,
            heat_score REAL,
            scraped_at TEXT,
            UNIQUE(time_period, category_code)
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_cc_sector ON census_construction(sector)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_cc_period ON census_construction(time_period)")
    conn.commit()
    conn.close()


def _calculate_heat_score(change_pct: float) -> float:
    """Determine heat score based on MoM spending change percentage."""
    abs_change = abs(change_pct)
    if abs_change >= THRESHOLDS["tier3_pct"]:
        return 20.0
    elif abs_change >= THRESHOLDS["tier2_pct"]:
        return 15.0
    elif abs_change >= THRESHOLDS["tier1_pct"]:
        return 10.0
    return 0.0


def _fetch_construction_spending() -> list[dict]:
    """
    Fetch construction spending data from Census VIP API.
    Returns list of time-series data points per category.
    """
    results = []

    for cat_key, cat_info in SPENDING_CATEGORIES.items():
        time.sleep(RATE_LIMIT_SECONDS)

        params = {
            "get": "cell_value,data_type_code,time_slot_id,category_code",
            "time": "from+2025-01",
            "for": "us:*",
            "category_code": cat_info["code"],
        }
        if CENSUS_API_KEY:
            params["key"] = CENSUS_API_KEY

        try:
            resp = requests.get(
                CONSTRUCTION_SPENDING_URL,
                params=params,
                timeout=30,
            )

            if resp.status_code == 429:
                logger.warning("[Census] Rate limited — backing off")
                time.sleep(5)
                continue

            if resp.status_code != 200:
                logger.warning(
                    f"[Census] HTTP {resp.status_code} for {cat_key}: {resp.text[:200]}"
                )
                continue

            data = resp.json()

            # Census API returns array of arrays: first row is headers, rest are data
            if not data or len(data) < 2:
                logger.info(f"[Census] No data for {cat_key}")
                continue

            headers = data[0]
            rows = data[1:]

            # Parse rows into dicts
            parsed = []
            for row in rows:
                record = dict(zip(headers, row))
                try:
                    value = float(record.get("cell_value", 0))
                except (ValueError, TypeError):
                    continue

                time_slot = record.get("time_slot_id") or record.get("time", "")
                parsed.append({
                    "time_period": time_slot,
                    "value": value,
                    "category_code": cat_key,
                    "category_label": cat_info["label"],
                    "sector": cat_info["sector"],
                })

            # Sort by time period to calculate MoM
            parsed.sort(key=lambda x: x["time_period"])

            # Calculate MoM changes
            for i in range(1, len(parsed)):
                curr = parsed[i]
                prev = parsed[i - 1]

                if prev["value"] == 0:
                    continue

                change_pct = ((curr["value"] - prev["value"]) / prev["value"]) * 100.0

                if abs(change_pct) >= THRESHOLDS["min_change_pct"]:
                    results.append({
                        "time_period": curr["time_period"],
                        "category_code": curr["category_code"],
                        "category_label": curr["category_label"],
                        "sector": curr["sector"],
                        "cell_value": curr["value"],
                        "prev_value": prev["value"],
                        "change_pct": round(change_pct, 2),
                        "heat_score": _calculate_heat_score(change_pct),
                    })

            logger.info(f"[Census] {cat_key}: {len(parsed)} data points, {sum(1 for r in results if r['category_code'] == cat_key)} flagged")

        except requests.exceptions.Timeout:
            logger.warning(f"[Census] Timeout for {cat_key}")
        except ValueError as e:
            logger.warning(f"[Census] JSON parse error for {cat_key}: {e}")
        except Exception as e:
            logger.error(f"[Census] Error for {cat_key}: {e}")

    return results


def _fetch_building_permits() -> list[dict]:
    """
    Fetch building permits data for power line construction NAICS.
    Returns summary-level data (national aggregate).
    """
    time.sleep(RATE_LIMIT_SECONDS)

    params = {
        "get": "ESTAB,EMP,PAYANN",
        "for": "county:*",
        "in": "state:*",
        "NAICS2017": PERMITS_NAICS,
    }
    if CENSUS_API_KEY:
        params["key"] = CENSUS_API_KEY

    try:
        resp = requests.get(
            BUILDING_PERMITS_URL,
            params=params,
            timeout=60,
        )

        if resp.status_code != 200:
            logger.warning(f"[Census Permits] HTTP {resp.status_code}: {resp.text[:200]}")
            return []

        data = resp.json()

        if not data or len(data) < 2:
            logger.info("[Census Permits] No data returned")
            return []

        headers = data[0]
        rows = data[1:]

        # Aggregate by state for top-level view
        state_totals: dict[str, dict] = {}
        for row in rows:
            record = dict(zip(headers, row))
            state = record.get("state", "??")
            try:
                estab = int(record.get("ESTAB", 0) or 0)
                emp = int(record.get("EMP", 0) or 0)
                payann = int(record.get("PAYANN", 0) or 0)
            except (ValueError, TypeError):
                continue

            if state not in state_totals:
                state_totals[state] = {"establishments": 0, "employment": 0, "payroll": 0}
            state_totals[state]["establishments"] += estab
            state_totals[state]["employment"] += emp
            state_totals[state]["payroll"] += payann

        # Return top states by employment (proxy for construction activity)
        sorted_states = sorted(
            state_totals.items(),
            key=lambda x: x[1]["employment"],
            reverse=True,
        )

        results = []
        for state, totals in sorted_states[:20]:
            results.append({
                "state": state,
                "establishments": totals["establishments"],
                "employment": totals["employment"],
                "payroll_thousands": totals["payroll"],
            })

        logger.info(f"[Census Permits] {len(rows)} counties, {len(state_totals)} states for NAICS {PERMITS_NAICS}")
        return results

    except requests.exceptions.Timeout:
        logger.warning("[Census Permits] Timeout")
        return []
    except ValueError as e:
        logger.warning(f"[Census Permits] JSON parse error: {e}")
        return []
    except Exception as e:
        logger.error(f"[Census Permits] Error: {e}")
        return []


def run(push_to_airtable: bool = True) -> dict:
    """
    Fetch Census construction spending data, detect MoM changes,
    store in SQLite, push flagged signals to Airtable.
    Returns summary dict.
    """
    _ensure_db(DB_PATH)

    logger.info("[Census] Starting construction spending scan")

    # Fetch construction spending with MoM changes
    spending_signals = _fetch_construction_spending()

    # Fetch building permits (context data)
    permits_data = _fetch_building_permits()

    # Store in SQLite (dedup by time_period + category_code)
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    new_signals: list[dict] = []

    for sig in spending_signals:
        try:
            c.execute("""
                INSERT OR IGNORE INTO census_construction
                (time_period, category_code, category_label, sector,
                 cell_value, prev_value, change_pct, heat_score, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sig["time_period"], sig["category_code"],
                sig["category_label"], sig["sector"],
                sig["cell_value"], sig["prev_value"],
                sig["change_pct"], sig["heat_score"],
                datetime.utcnow().isoformat(),
            ))
            if c.rowcount > 0:
                new_signals.append(sig)
        except sqlite3.Error as e:
            logger.warning(f"[Census] DB error: {e}")

    conn.commit()
    conn.close()

    # Push to Airtable
    signals_pushed = 0
    if push_to_airtable and new_signals:
        try:
            from storage.airtable import get_client
            at = get_client()

            for sig in new_signals:
                try:
                    direction = "increase" if sig["change_pct"] > 0 else "decrease"
                    raw_content = (
                        f"Census Construction Spending: {sig['category_label']}\n"
                        f"Period: {sig['time_period']}\n"
                        f"Value: ${sig['cell_value']:,.0f}M → "
                        f"{sig['change_pct']:+.1f}% MoM {direction}\n"
                        f"Previous: ${sig['prev_value']:,.0f}M\n"
                        f"Threshold: >{THRESHOLDS['min_change_pct']}% triggers signal"
                    )

                    # Add permits context if available
                    if permits_data:
                        top_states = ", ".join(
                            f"{p['state']}({p['employment']:,})" for p in permits_data[:5]
                        )
                        raw_content += f"\n\nTop states by power-line construction employment: {top_states}"

                    at.insert_signal(
                        signal_type="census_construction",
                        source="Census Bureau / Construction Spending",
                        company_name=f"US Construction — {sig['category_label']}",
                        sector=sig["sector"],
                        signal_date=sig["time_period"][:10] if len(sig["time_period"]) >= 10 else datetime.utcnow().strftime("%Y-%m-%d"),
                        raw_content=raw_content,
                        heat_score=sig["heat_score"],
                        notes=f"MoM change: {sig['change_pct']:+.1f}% | Category: {sig['category_code']}",
                    )
                    signals_pushed += 1
                except Exception as e:
                    logger.warning(f"[Census] Airtable insert failed: {e}")

        except Exception as e:
            logger.error(f"[Census] Airtable client error: {e}")

    # Summary
    sector_counts: dict[str, int] = {}
    for sig in new_signals:
        s = sig["sector"]
        sector_counts[s] = sector_counts.get(s, 0) + 1

    logger.info(
        f"[Census] Done: {len(new_signals)} new signals, "
        f"{signals_pushed} pushed to Airtable | {sector_counts}"
    )

    return {
        "total_spending_signals": len(spending_signals),
        "new_signals": len(new_signals),
        "signals_pushed": signals_pushed,
        "sector_breakdown": sector_counts,
        "permits_states_tracked": len(permits_data),
        "categories_scanned": len(SPENDING_CATEGORIES),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run(push_to_airtable=False)
    print(json.dumps(result, indent=2))
