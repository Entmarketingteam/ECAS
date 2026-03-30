"""
signals/epa_compliance.py
EPA ECHO enforcement and compliance signals for water/wastewater infrastructure.

Non-compliant major facilities are forced to invest in capital upgrades —
consent decrees and formal enforcement actions are tier-1 EPC demand signals.

API: EPA ECHO CWA REST services (no API key needed).
Stores in SQLite for deduplication. Top signals pushed to Airtable signals_raw.
Runs weekly.
"""

import json
import logging
import re
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DB_PATH

logger = logging.getLogger(__name__)

ECHO_BASE_URL = "https://echodata.epa.gov/echo/cwa_rest_services"

# Target states for water/wastewater EPC opportunities
TARGET_STATES = "VA,TX,NC,GA,FL,MD,PA,OH,IN,IL,CA,AZ,NV"

SECTOR = "Water & Wastewater Infrastructure"
SIGNAL_TYPE = "epa_compliance"

# Rate limit: be polite to EPA servers
REQUEST_DELAY = 1.5  # seconds between requests


def _ensure_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS epa_compliance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            registry_id TEXT UNIQUE,
            facility_name TEXT,
            city TEXT,
            state TEXT,
            violation_type TEXT,
            compliance_status TEXT,
            penalty_amount REAL,
            enforcement_type TEXT,
            heat_score REAL,
            raw_text TEXT,
            scraped_at TEXT
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_epa_state ON epa_compliance(state)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_epa_score ON epa_compliance(heat_score)")
    conn.commit()
    conn.close()


def _score_facility(compliance_status: str, enforcement_type: str, penalty_amount: float) -> float:
    """
    Score a non-compliant facility based on severity.
    Higher score = higher likelihood of forced capital upgrades.
    """
    score = 0.0

    # Compliance status scoring
    status_lower = (compliance_status or "").lower()
    if "consent" in status_lower or "decree" in status_lower:
        score = 25.0
    elif "formal" in status_lower or "enforcement" in status_lower:
        score = 20.0
    elif "significant" in status_lower:
        score = 15.0
    elif "non-compliance" in status_lower or "violation" in status_lower:
        score = 10.0

    # Enforcement type bonus
    enf_lower = (enforcement_type or "").lower()
    if "consent decree" in enf_lower:
        score = max(score, 25.0)
    elif "formal enforcement" in enf_lower or "judicial" in enf_lower:
        score = max(score, 20.0)
    elif "administrative order" in enf_lower:
        score = max(score, 18.0)

    # Penalty amount bonus (large penalties = serious violations = big upgrades)
    if penalty_amount and penalty_amount > 0:
        if penalty_amount >= 1_000_000:
            score += 10.0
        elif penalty_amount >= 100_000:
            score += 5.0
        elif penalty_amount >= 10_000:
            score += 2.0

    return min(score, 50.0)


def _build_raw_text(facility: dict) -> str:
    """Build raw_text field from facility data."""
    parts = [
        f"Facility: {facility.get('facility_name', 'Unknown')}",
        f"Location: {facility.get('city', '')}, {facility.get('state', '')}",
        f"Violation Type: {facility.get('violation_type', 'N/A')}",
        f"Compliance Status: {facility.get('compliance_status', 'N/A')}",
        f"Enforcement: {facility.get('enforcement_type', 'N/A')}",
    ]
    penalty = facility.get("penalty_amount", 0)
    if penalty and penalty > 0:
        parts.append(f"Penalty Amount: ${penalty:,.0f}")
    return "\n".join(parts)


def _fetch_facilities(params: dict) -> list[dict]:
    """Fetch facilities from EPA ECHO CWA REST services."""
    url = f"{ECHO_BASE_URL}.get_facilities"
    params["output"] = "JSON"

    try:
        time.sleep(REQUEST_DELAY)
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.error(f"[EPA] ECHO API error: {e}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"[EPA] ECHO JSON parse error: {e}")
        return []

    # ECHO returns results nested under Results.Facilities
    results = data.get("Results", {})
    facilities_raw = results.get("Facilities", [])

    facilities = []
    for f in facilities_raw:
        registry_id = f.get("RegistryId") or f.get("SourceID") or f.get("CWPName", "")
        if not registry_id:
            continue

        facility_name = f.get("CWPName", "") or f.get("FacName", "") or ""
        city = f.get("CWPCity", "") or f.get("FacCity", "") or ""
        state = f.get("CWPState", "") or f.get("FacState", "") or ""

        # Compliance and violation info
        compliance_status = f.get("CWPSNCStatus", "") or f.get("CWPStatus", "") or ""
        violation_type = f.get("CWPViolStatus", "") or ""
        enforcement_type = f.get("CWPFormalEaCt", "") or ""

        # Penalty amount
        penalty_str = f.get("CWPPenalties", "") or f.get("TotalPenalties", "") or "0"
        try:
            penalty_amount = float(re.sub(r"[^\d.]", "", str(penalty_str)) or "0")
        except (ValueError, TypeError):
            penalty_amount = 0.0

        facilities.append({
            "registry_id": str(registry_id),
            "facility_name": facility_name,
            "city": city,
            "state": state,
            "violation_type": violation_type,
            "compliance_status": compliance_status,
            "enforcement_type": enforcement_type,
            "penalty_amount": penalty_amount,
        })

    return facilities


def fetch_noncompliant_facilities() -> list[dict]:
    """
    Fetch major CWA facilities in significant non-compliance across target states.
    """
    logger.info(f"[EPA] Fetching SNC facilities in {TARGET_STATES}")

    params = {
        "p_maj": "Y",
        "p_qnc_status": "Significant",
        "p_st": TARGET_STATES,
    }
    facilities = _fetch_facilities(params)
    logger.info(f"[EPA] SNC query returned {len(facilities)} facilities")
    return facilities


def fetch_enforcement_actions() -> list[dict]:
    """
    Fetch facilities with formal enforcement actions (consent decrees, admin orders).
    """
    logger.info(f"[EPA] Fetching formal enforcement actions in {TARGET_STATES}")

    params = {
        "p_maj": "Y",
        "p_st": TARGET_STATES,
        "p_fetefct": "Y",  # Formal enforcement in effect
    }
    facilities = _fetch_facilities(params)
    logger.info(f"[EPA] Formal enforcement query returned {len(facilities)} facilities")
    return facilities


def run(push_to_airtable: bool = True) -> dict:
    """
    Run EPA compliance signal collector.
    1. Fetch SNC facilities
    2. Fetch formal enforcement actions
    3. Deduplicate, score, store in SQLite
    4. Push top signals to Airtable

    Returns dict with stats.
    """
    _ensure_db(DB_PATH)

    # Collect from both queries
    snc_facilities = fetch_noncompliant_facilities()
    enforcement_facilities = fetch_enforcement_actions()

    # Merge and deduplicate by registry_id
    all_facilities: dict[str, dict] = {}

    for f in snc_facilities:
        rid = f["registry_id"]
        all_facilities[rid] = f

    for f in enforcement_facilities:
        rid = f["registry_id"]
        if rid in all_facilities:
            # Merge enforcement info into existing record
            existing = all_facilities[rid]
            if f.get("enforcement_type"):
                existing["enforcement_type"] = f["enforcement_type"]
            if f.get("penalty_amount", 0) > existing.get("penalty_amount", 0):
                existing["penalty_amount"] = f["penalty_amount"]
        else:
            all_facilities[rid] = f

    # Score all facilities
    scored = []
    for rid, f in all_facilities.items():
        heat_score = _score_facility(
            f.get("compliance_status", ""),
            f.get("enforcement_type", ""),
            f.get("penalty_amount", 0),
        )
        f["heat_score"] = heat_score
        f["raw_text"] = _build_raw_text(f)
        scored.append(f)

    scored.sort(key=lambda x: x["heat_score"], reverse=True)
    logger.info(f"[EPA] {len(scored)} unique facilities after dedup")

    # Store in SQLite
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    inserted = 0
    for f in scored:
        try:
            c.execute("""
                INSERT OR IGNORE INTO epa_compliance
                (registry_id, facility_name, city, state, violation_type,
                 compliance_status, penalty_amount, enforcement_type,
                 heat_score, raw_text, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f["registry_id"], f["facility_name"], f["city"], f["state"],
                f["violation_type"], f["compliance_status"], f["penalty_amount"],
                f["enforcement_type"], f["heat_score"], f["raw_text"],
                datetime.now().isoformat(),
            ))
            if c.rowcount > 0:
                inserted += 1
        except sqlite3.Error as e:
            logger.warning(f"[EPA] DB error: {e}")
    conn.commit()
    conn.close()

    logger.info(f"[EPA] {inserted} new inserts to SQLite")

    # Push top signals to Airtable
    signals_pushed = 0
    if push_to_airtable and scored:
        try:
            from storage.airtable import get_client
            at = get_client()
        except Exception as e:
            logger.error(f"[EPA] Airtable client error: {e}")
            at = None

        if at:
            # Push facilities with heat_score >= 15 (significant or worse)
            top = [f for f in scored if f["heat_score"] >= 15.0][:50]
            for f in top:
                try:
                    at.insert_signal(
                        signal_type=SIGNAL_TYPE,
                        source="EPA ECHO / CWA Enforcement",
                        company_name=f["facility_name"] or "Unknown Facility",
                        sector=SECTOR,
                        signal_date=datetime.now().strftime("%Y-%m-%d"),
                        raw_content=f["raw_text"],
                        heat_score=f["heat_score"],
                        notes=f"Registry ID: {f['registry_id']} | {f['city']}, {f['state']}",
                    )
                    signals_pushed += 1
                except Exception as e:
                    logger.warning(f"[EPA] Airtable insert failed: {e}")

            logger.info(f"[EPA] Pushed {signals_pushed} signals to Airtable")

    # State breakdown
    state_counts: dict[str, int] = {}
    for f in scored:
        st = f.get("state", "??")
        state_counts[st] = state_counts.get(st, 0) + 1

    return {
        "total_facilities": len(scored),
        "new_inserts": inserted,
        "signals_pushed": signals_pushed,
        "state_breakdown": state_counts,
        "top_facilities": [
            {
                "name": f["facility_name"],
                "state": f["state"],
                "score": f["heat_score"],
                "status": f["compliance_status"],
            }
            for f in scored[:5]
        ],
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run(push_to_airtable=False)
    print(json.dumps(result, indent=2))
