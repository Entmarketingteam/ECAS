"""
contractor/signals/_airtable.py — Shared Airtable push helper for all signal scrapers.

Handles: batch writes (10/request limit), 30-day dedup check, error resilience.
"""
import os
import logging
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY", "")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID", "appoi8SzEJY8in57x")
SIGNALS_TABLE = "tblAFJnXToLTKeaNU"
_BASE = "https://api.airtable.com/v0"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json",
    }


def signal_exists(company_domain: str, signal_type: str, within_days: int = 30) -> bool:
    """Return True if this signal type was already recorded for this domain within N days."""
    if not company_domain:
        return False
    cutoff = (datetime.utcnow() - timedelta(days=within_days)).isoformat()
    formula = (
        f"AND({{company_domain}}='{company_domain}',"
        f"{{signal_type}}='{signal_type}',"
        f"{{detected_at}}>'{cutoff}')"
    )
    try:
        resp = requests.get(
            f"{_BASE}/{AIRTABLE_BASE_ID}/{SIGNALS_TABLE}",
            headers=_headers(),
            params={
                "filterByFormula": formula,
                "maxRecords": 1,
                "fields[]": ["company_domain"],
            },
            timeout=15,
        )
        resp.raise_for_status()
        return len(resp.json().get("records", [])) > 0
    except Exception as e:
        logger.warning("Dedup check failed for %s/%s: %s", company_domain, signal_type, e)
        return False


def push_signals(signals: list[dict]) -> int:
    """
    Push signal dicts to Airtable signals_raw in batches of 10.
    Returns total count of records created. Never raises — logs errors and continues.
    """
    if not signals:
        return 0

    url = f"{_BASE}/{AIRTABLE_BASE_ID}/{SIGNALS_TABLE}"
    created = 0

    for i in range(0, len(signals), 10):
        batch = signals[i : i + 10]
        payload = {
            "records": [{"fields": s} for s in batch],
            "typecast": True,
        }
        try:
            resp = requests.post(url, headers=_headers(), json=payload, timeout=30)
            resp.raise_for_status()
            created += len(resp.json().get("records", []))
        except Exception as e:
            logger.error("Airtable push failed for batch at offset %d: %s", i, e)

    return created
