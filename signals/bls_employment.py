"""
signals/bls_employment.py
BLS employment data by construction NAICS codes.

API: https://api.bls.gov/publicAPI/v2/timeseries/data/
Free (v2 with registration for higher limits, env var BLS_API_KEY optional).

Tracks national, seasonally adjusted employment for:
  - CEU2023713001 — Power line and communication construction
  - CEU2023811001 — Water and sewer construction
  - CEU2023621001 — Electrical contractor employment
  - CEU2023622001 — Plumbing/HVAC contractor employment
  - CEU3133600001 — Computer/electronic manufacturing (data center/fab proxy)

Flags when employment grows >3% YoY as an EPC demand signal.

heat_score: 3-5% growth=8, 5-10%=12, >10%=18
Deduplicates by series_id + period in SQLite table `bls_employment`.
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

# BLS API v2
BLS_API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

# Optional API key for higher rate limits (v2)
BLS_API_KEY = os.environ.get("BLS_API_KEY", "")

# Rate limit between API calls
RATE_LIMIT_SECONDS = 0.5

# Series to track: (series_id, label, sector)
BLS_SERIES = [
    (
        "CEU2023713001",
        "Power Line & Communication Construction Employment",
        "Power & Grid Infrastructure",
    ),
    (
        "CEU2023811001",
        "Water & Sewer Construction Employment",
        "Water & Wastewater Infrastructure",
    ),
    (
        "CEU2023621001",
        "Electrical Contractor Employment",
        "Power & Grid Infrastructure",
    ),
    (
        "CEU2023622001",
        "Plumbing/HVAC Contractor Employment",
        "Power & Grid Infrastructure",
    ),
    (
        "CEU3133600001",
        "Computer & Electronic Manufacturing Employment",
        "Data Center & AI Infrastructure",
    ),
]

# YoY growth thresholds and heat scores
THRESHOLDS = {
    "min_growth_pct": 3.0,  # Minimum YoY % growth to flag
    "tier1_pct": 3.0,       # 3-5% → heat_score 8
    "tier2_pct": 5.0,       # 5-10% → heat_score 12
    "tier3_pct": 10.0,      # >10% → heat_score 18
}


def _ensure_db(db_path: Path) -> None:
    """Create SQLite table for deduplication."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS bls_employment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            series_id TEXT,
            series_label TEXT,
            sector TEXT,
            year INTEGER,
            period TEXT,
            value REAL,
            prev_year_value REAL,
            yoy_change_pct REAL,
            heat_score REAL,
            scraped_at TEXT,
            UNIQUE(series_id, year, period)
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_be_sector ON bls_employment(sector)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_be_series ON bls_employment(series_id)")
    conn.commit()
    conn.close()


def _calculate_heat_score(yoy_pct: float) -> float:
    """Determine heat score based on YoY employment growth percentage."""
    if yoy_pct >= THRESHOLDS["tier3_pct"]:
        return 18.0
    elif yoy_pct >= THRESHOLDS["tier2_pct"]:
        return 12.0
    elif yoy_pct >= THRESHOLDS["tier1_pct"]:
        return 8.0
    return 0.0


def _fetch_bls_data(series_ids: list[str], start_year: int, end_year: int) -> dict:
    """
    Fetch time series data from BLS API v2.
    Returns the full API response dict.
    BLS v2 accepts up to 50 series in a single request.
    """
    payload = {
        "seriesid": series_ids,
        "startyear": str(start_year),
        "endyear": str(end_year),
    }
    if BLS_API_KEY:
        payload["registrationkey"] = BLS_API_KEY

    headers = {"Content-Type": "application/json"}

    try:
        resp = requests.post(
            BLS_API_URL,
            json=payload,
            headers=headers,
            timeout=30,
        )

        if resp.status_code == 429:
            logger.warning("[BLS] Rate limited — backing off")
            time.sleep(10)
            return {}

        if resp.status_code != 200:
            logger.warning(f"[BLS] HTTP {resp.status_code}: {resp.text[:200]}")
            return {}

        data = resp.json()

        if data.get("status") != "REQUEST_SUCCEEDED":
            msg = data.get("message", ["Unknown error"])
            logger.warning(f"[BLS] Request failed: {msg}")
            return {}

        return data

    except requests.exceptions.Timeout:
        logger.warning("[BLS] Timeout")
        return {}
    except ValueError as e:
        logger.warning(f"[BLS] JSON parse error: {e}")
        return {}
    except Exception as e:
        logger.error(f"[BLS] Error: {e}")
        return {}


def _parse_series_data(series_data: dict) -> list[dict]:
    """
    Parse a single BLS series response into a list of data points.
    Each point: {year, period, value, period_name}
    """
    points = []
    for item in series_data.get("data", []):
        try:
            year = int(item.get("year", 0))
            period = item.get("period", "")  # e.g., "M01" for January
            value = float(item.get("value", 0))

            # Skip annual averages (period M13)
            if period == "M13":
                continue

            points.append({
                "year": year,
                "period": period,
                "value": value,
                "period_name": item.get("periodName", ""),
            })
        except (ValueError, TypeError):
            continue

    # Sort by year + period ascending
    points.sort(key=lambda x: (x["year"], x["period"]))
    return points


def run(push_to_airtable: bool = True) -> dict:
    """
    Fetch BLS employment data, detect YoY growth signals,
    store in SQLite, push flagged signals to Airtable.
    Returns summary dict.
    """
    _ensure_db(DB_PATH)

    now = datetime.utcnow()
    end_year = now.year
    start_year = end_year - 1  # Need prior year for YoY comparison

    logger.info(f"[BLS] Fetching {len(BLS_SERIES)} series | {start_year}-{end_year}")

    # Build series lookup
    series_map = {s[0]: {"label": s[1], "sector": s[2]} for s in BLS_SERIES}
    series_ids = [s[0] for s in BLS_SERIES]

    # Fetch all series in one request (BLS v2 allows up to 50)
    time.sleep(RATE_LIMIT_SECONDS)
    api_data = _fetch_bls_data(series_ids, start_year, end_year)

    if not api_data:
        logger.warning("[BLS] No data returned from API")
        return {
            "total_signals": 0,
            "new_signals": 0,
            "signals_pushed": 0,
            "series_scanned": len(BLS_SERIES),
        }

    all_signals: list[dict] = []

    # Process each series
    for series_result in api_data.get("Results", {}).get("series", []):
        series_id = series_result.get("seriesID", "")
        if series_id not in series_map:
            continue

        info = series_map[series_id]
        points = _parse_series_data(series_result)

        # Build lookup by period for YoY comparison
        by_period: dict[str, dict[int, float]] = {}
        for pt in points:
            period = pt["period"]
            if period not in by_period:
                by_period[period] = {}
            by_period[period][pt["year"]] = pt["value"]

        # Calculate YoY for the current year's data
        for period, year_vals in by_period.items():
            if end_year not in year_vals or start_year not in year_vals:
                continue

            curr_val = year_vals[end_year]
            prev_val = year_vals[start_year]

            if prev_val == 0:
                continue

            yoy_pct = ((curr_val - prev_val) / prev_val) * 100.0

            if yoy_pct >= THRESHOLDS["min_growth_pct"]:
                heat = _calculate_heat_score(yoy_pct)
                all_signals.append({
                    "series_id": series_id,
                    "series_label": info["label"],
                    "sector": info["sector"],
                    "year": end_year,
                    "period": period,
                    "value": curr_val,
                    "prev_year_value": prev_val,
                    "yoy_change_pct": round(yoy_pct, 2),
                    "heat_score": heat,
                })

    logger.info(f"[BLS] {len(all_signals)} YoY growth signals detected (>{THRESHOLDS['min_growth_pct']}%)")

    # Store in SQLite (dedup by series_id + year + period)
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    new_signals: list[dict] = []

    for sig in all_signals:
        try:
            c.execute("""
                INSERT OR IGNORE INTO bls_employment
                (series_id, series_label, sector, year, period,
                 value, prev_year_value, yoy_change_pct, heat_score, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sig["series_id"], sig["series_label"], sig["sector"],
                sig["year"], sig["period"],
                sig["value"], sig["prev_year_value"],
                sig["yoy_change_pct"], sig["heat_score"],
                datetime.utcnow().isoformat(),
            ))
            if c.rowcount > 0:
                new_signals.append(sig)
        except sqlite3.Error as e:
            logger.warning(f"[BLS] DB error: {e}")

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
                    # Convert period code to readable month
                    month_num = sig["period"].replace("M", "")
                    period_label = f"{sig['year']}-{month_num.zfill(2)}"

                    raw_content = (
                        f"BLS Employment Signal: {sig['series_label']}\n"
                        f"Series: {sig['series_id']} | Period: {period_label}\n"
                        f"Employment: {sig['value']:,.0f} (current) vs "
                        f"{sig['prev_year_value']:,.0f} (prior year)\n"
                        f"YoY Growth: {sig['yoy_change_pct']:+.1f}%\n"
                        f"Threshold: >{THRESHOLDS['min_growth_pct']}% triggers signal"
                    )

                    at.insert_signal(
                        signal_type="bls_employment",
                        source=f"BLS / {sig['series_id']}",
                        company_name=f"US Employment — {sig['series_label']}",
                        sector=sig["sector"],
                        signal_date=f"{sig['year']}-{month_num.zfill(2)}-01",
                        raw_content=raw_content,
                        heat_score=sig["heat_score"],
                        notes=f"YoY: {sig['yoy_change_pct']:+.1f}% | Series: {sig['series_id']}",
                    )
                    signals_pushed += 1
                except Exception as e:
                    logger.warning(f"[BLS] Airtable insert failed: {e}")

        except Exception as e:
            logger.error(f"[BLS] Airtable client error: {e}")

    # Summary
    sector_counts: dict[str, int] = {}
    for sig in new_signals:
        s = sig["sector"]
        sector_counts[s] = sector_counts.get(s, 0) + 1

    logger.info(
        f"[BLS] Done: {len(new_signals)} new signals, "
        f"{signals_pushed} pushed to Airtable | {sector_counts}"
    )

    return {
        "total_signals": len(all_signals),
        "new_signals": len(new_signals),
        "signals_pushed": signals_pushed,
        "sector_breakdown": sector_counts,
        "series_scanned": len(BLS_SERIES),
        "year_range": f"{start_year}-{end_year}",
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run(push_to_airtable=False)
    print(json.dumps(result, indent=2))
