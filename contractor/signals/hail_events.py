"""
contractor/signals/hail_events.py — NOAA Storm Events hail signal scraper.

Fetches recent hail events from NOAA's Storm Events API and scores them
as signals for the Commercial Roofing vertical.

NOAA Storm Events API: https://www.ncdc.noaa.gov/stormevents/
Free — no API key required for CSV export endpoint.

Schedule: Every 6 hours via APScheduler.
"""

import logging
import csv
import io
import requests
from datetime import datetime, timedelta
from dataclasses import dataclass

from contractor.config import NOAA_API_CONFIG, CONTRACTOR_SIGNAL_WEIGHTS

logger = logging.getLogger(__name__)


@dataclass
class HailEvent:
    state: str
    county: str
    date: datetime
    magnitude_inches: float
    city: str
    injuries: int
    property_damage_str: str
    source: str = "NOAA Storm Events"


def fetch_hail_events(lookback_days: int = None) -> list[HailEvent]:
    """
    Fetch recent hail events from NOAA Storm Events CSV export.

    Args:
        lookback_days: How many days back to look (default from config)

    Returns:
        List of HailEvent objects sorted by date descending
    """
    lookback = lookback_days or NOAA_API_CONFIG["lookback_days"]
    target_states = set(NOAA_API_CONFIG["target_states"])

    # NOAA Storm Events bulk CSV — current year
    current_year = datetime.utcnow().year
    url = f"https://www.ncdc.noaa.gov/stormevents/csv?eventType=Hail&beginDate_mm=01&beginDate_dd=01&beginDate_yyyy={current_year}&endDate_mm=12&endDate_dd=31&endDate_yyyy={current_year}&hailfilter=0.00&tornfilter=0&windfilter=000&sort=DT&submitbutton=Search&statefips=-99%2CALL"

    try:
        resp = requests.get(url, timeout=30, headers={"User-Agent": "ContractMotion Signal Engine admin@contractmotion.com"})
        resp.raise_for_status()
    except Exception as e:
        logger.error("Failed to fetch NOAA hail data: %s", e)
        return []

    events = []
    cutoff = datetime.utcnow() - timedelta(days=lookback)

    try:
        reader = csv.DictReader(io.StringIO(resp.text))
        for row in reader:
            try:
                # Parse date
                begin_date_str = row.get("BEGIN_DATE_TIME", "")
                if not begin_date_str:
                    continue
                event_date = datetime.strptime(begin_date_str[:19], "%d-%b-%y %H:%M:%S")
                if event_date < cutoff:
                    continue

                # Filter to target states
                state = row.get("STATE", "").strip()
                state_abbrev = _state_to_abbrev(state)
                if state_abbrev not in target_states:
                    continue

                # Parse magnitude
                mag_str = row.get("MAGNITUDE", "0") or "0"
                try:
                    magnitude = float(mag_str)
                except ValueError:
                    magnitude = 0.0

                if magnitude < NOAA_API_CONFIG["hail_threshold_medium_inches"]:
                    continue  # Too small to be actionable

                events.append(HailEvent(
                    state=state_abbrev,
                    county=row.get("CZ_NAME", "").title(),
                    date=event_date,
                    magnitude_inches=magnitude,
                    city=row.get("BEGIN_LOCATION", "").title(),
                    injuries=int(row.get("INJURIES_DIRECT", 0) or 0),
                    property_damage_str=row.get("DAMAGE_PROPERTY", "0"),
                ))
            except Exception as row_err:
                logger.debug("Skipping malformed NOAA row: %s", row_err)
                continue

    except Exception as e:
        logger.error("Failed to parse NOAA CSV: %s", e)
        return []

    # Sort by date descending
    events.sort(key=lambda x: x.date, reverse=True)
    logger.info("Fetched %d hail events from NOAA (last %d days, target states)", len(events), lookback)
    return events


def classify_hail_event(event: HailEvent) -> str:
    """
    Classify hail event as a signal type for scoring.

    Returns signal type string for use in SignalScorer.
    """
    if event.magnitude_inches >= NOAA_API_CONFIG["hail_threshold_large_inches"]:
        return "hail_event_large"
    return "hail_event_medium"


def _state_to_abbrev(state_name: str) -> str:
    """Convert full state name to 2-letter abbreviation."""
    mapping = {
        "TEXAS": "TX", "FLORIDA": "FL", "GEORGIA": "GA", "NORTH CAROLINA": "NC",
        "VIRGINIA": "VA", "PENNSYLVANIA": "PA", "OHIO": "OH", "TENNESSEE": "TN",
        "COLORADO": "CO", "KANSAS": "KS", "OKLAHOMA": "OK", "ALABAMA": "AL",
        "SOUTH CAROLINA": "SC", "MISSISSIPPI": "MS",
    }
    return mapping.get(state_name.upper(), state_name[:2].upper())


def run_hail_signal_job() -> list[dict]:
    """
    Main job function called by APScheduler.

    Returns list of signal dicts ready for the signal scorer:
    [{"type": "hail_event_large", "detected_at": datetime, "source": "NOAA", "raw_data": {...}}]
    """
    events = fetch_hail_events()
    signals = []

    for event in events:
        signal_type = classify_hail_event(event)
        signals.append({
            "type": signal_type,
            "detected_at": event.date,
            "source": "NOAA Storm Events",
            "raw_data": {
                "state": event.state,
                "county": event.county,
                "city": event.city,
                "magnitude_inches": event.magnitude_inches,
                "property_damage": event.property_damage_str,
            },
            "vertical": "Commercial Roofing",
        })

    logger.info("Hail signal job: %d actionable events found", len(signals))
    return signals
