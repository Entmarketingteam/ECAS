"""
enrichment/health.py
Pre-flight health checks before pipeline runs.
Tests each external service with a lightweight probe.
"""

import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

logger = logging.getLogger(__name__)


def check_apollo() -> dict:
    """Lightweight Apollo probe — search for a known company."""
    key = os.environ.get("APOLLO_API_KEY", "")
    if not key:
        return {"healthy": False, "detail": "APOLLO_API_KEY not set"}
    try:
        resp = requests.post(
            "https://api.apollo.io/v1/organizations/search",
            headers={"Content-Type": "application/json", "X-Api-Key": key},
            json={"q_organization_name": "Google", "page": 1, "per_page": 1},
            timeout=15,
        )
        if resp.status_code in (401, 403):
            return {"healthy": False, "detail": f"Apollo auth failed ({resp.status_code})"}
        if resp.status_code == 429:
            return {"healthy": False, "detail": "Apollo rate limited"}
        resp.raise_for_status()
        orgs = resp.json().get("organizations", [])
        return {"healthy": len(orgs) > 0, "detail": f"Found {len(orgs)} orgs"}
    except Exception as e:
        return {"healthy": False, "detail": str(e)}


def check_findymail() -> dict:
    """Findymail probe — verify API key is valid."""
    key = os.environ.get("FINDYMAIL_API_KEY", "")
    if not key:
        return {"healthy": False, "detail": "FINDYMAIL_API_KEY not set"}
    try:
        # Verify a known-good email to test API access
        resp = requests.post(
            "https://app.findymail.com/api/verify",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"email": "test@google.com"},
            timeout=15,
        )
        if resp.status_code in (401, 403):
            return {"healthy": False, "detail": f"Findymail auth failed ({resp.status_code})"}
        if resp.status_code == 402:
            return {"healthy": False, "detail": "Findymail credits exhausted"}
        resp.raise_for_status()
        return {"healthy": True, "detail": "API responding"}
    except Exception as e:
        return {"healthy": False, "detail": str(e)}


def check_smartlead() -> dict:
    """Smartlead probe — verify API key by listing campaigns."""
    key = os.environ.get("SMARTLEAD_API_KEY", "")
    if not key:
        return {"healthy": False, "detail": "SMARTLEAD_API_KEY not set"}
    try:
        resp = requests.get(
            "https://server.smartlead.ai/api/v1/campaigns",
            params={"api_key": key},
            timeout=15,
        )
        if resp.status_code in (401, 403):
            return {"healthy": False, "detail": f"Smartlead auth failed ({resp.status_code})"}
        resp.raise_for_status()
        return {"healthy": True, "detail": f"API responding"}
    except Exception as e:
        return {"healthy": False, "detail": str(e)}


def check_airtable() -> dict:
    """Airtable probe — read 1 record from projects table."""
    key = os.environ.get("AIRTABLE_API_KEY", "")
    base_id = os.environ.get("AIRTABLE_BASE_ID", os.environ.get("ECAS_BASE_ID", "appoi8SzEJY8in57x"))
    if not key:
        return {"healthy": False, "detail": "AIRTABLE_API_KEY not set"}
    try:
        resp = requests.get(
            f"https://api.airtable.com/v0/{base_id}/tbloen0rEkHttejnC",
            headers={"Authorization": f"Bearer {key}"},
            params={"maxRecords": 1},
            timeout=15,
        )
        if resp.status_code in (401, 403):
            return {"healthy": False, "detail": f"Airtable auth failed ({resp.status_code})"}
        resp.raise_for_status()
        records = resp.json().get("records", [])
        return {"healthy": True, "detail": f"Read {len(records)} record(s)"}
    except Exception as e:
        return {"healthy": False, "detail": str(e)}


def check_env_vars() -> dict:
    """Verify all required env vars are set (non-empty)."""
    required = ["APOLLO_API_KEY", "FINDYMAIL_API_KEY", "SMARTLEAD_API_KEY", "AIRTABLE_API_KEY", "ANTHROPIC_API_KEY"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        return {"healthy": False, "detail": f"Missing: {', '.join(missing)}"}
    return {"healthy": True, "detail": "All required vars set"}


def pre_flight_check() -> dict:
    """
    Run all health checks in parallel before pipeline execution.
    Returns: {"status": "healthy"|"degraded"|"blocked", "checks": {...}, "failures": {...}}
    """
    check_fns = {
        "env_vars": check_env_vars,
        "apollo": check_apollo,
        "findymail": check_findymail,
        "smartlead": check_smartlead,
        "airtable": check_airtable,
    }

    checks = {}
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(fn): name for name, fn in check_fns.items()}
        for future in as_completed(futures):
            name = futures[future]
            try:
                checks[name] = future.result()
            except Exception as e:
                checks[name] = {"healthy": False, "detail": f"Check crashed: {e}"}

    failures = {k: v for k, v in checks.items() if not v["healthy"]}

    # Critical services — pipeline cannot run without these
    critical = {"apollo", "airtable", "env_vars"}
    critical_failures = set(failures.keys()) & critical

    if critical_failures:
        status = "blocked"
    elif failures:
        status = "degraded"
    else:
        status = "healthy"

    result = {"status": status, "checks": checks, "failures": failures}
    logger.info(f"[PreFlight] Status: {status} | Checks: {checks}")
    return result
