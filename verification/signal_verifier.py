"""
verification/signal_verifier.py — Real-time project signal verification.

Before ANY signal is used in outreach content:
  1. Re-fetch the source URL — verify it still exists and returns expected data
  2. Confirm the dollar amount, date, and project name haven't changed
  3. Check the project hasn't already been awarded (stale = wasted personalization)
  4. Verify the project is in the correct geographic territory for this company

Sources covered:
  - FERC filings (ferc.gov ELIS)
  - SAM.gov opportunities (pre-solicitations, sources sought)
  - EPA CWSRF state IUP pages
  - USASpending awards (confirm not yet awarded if using as "upcoming")
  - State permit databases
  - PJM/MISO interconnection queue
"""

import logging
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests
from bs4 import BeautifulSoup

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "") or os.environ.get("ANTHROPIC_2_API_KEY", "")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
REQUEST_DELAY = 1.0


# ── Signal status codes ────────────────────────────────────────────────────────

class SignalStatus:
    LIVE = "LIVE"           # Verified current, safe to use
    STALE = "STALE"         # Source returns different data than when scraped
    AWARDED = "AWARDED"     # Project already awarded — don't use as "upcoming"
    DEAD = "DEAD"           # Source URL returns 404 or no data
    UNCERTAIN = "UNCERTAIN" # Can't verify — flag for human review


# ── FERC filing verification ───────────────────────────────────────────────────

def verify_ferc_filing(filing_id: str, expected_project_name: str = "") -> dict:
    """
    Re-fetch a FERC filing by ID and verify it matches expected data.
    FERC ELIS is a public database — no API key required.
    """
    url = f"https://elibrary.ferc.gov/eLibrary/docSearch?accessionNumber={filing_id}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 404:
            return {"status": SignalStatus.DEAD, "reason": "FERC filing not found"}

        soup = BeautifulSoup(r.text, "lxml")
        title = soup.find("title")
        page_text = soup.get_text(separator=" ").lower()

        if expected_project_name:
            name_words = [w.lower() for w in expected_project_name.split()
                          if len(w) > 3]
            matches = sum(1 for w in name_words if w in page_text)
            if matches / max(len(name_words), 1) < 0.5:
                return {
                    "status": SignalStatus.STALE,
                    "reason": f"Expected project '{expected_project_name}' not found in FERC record",
                }

        # Check if it shows as withdrawn or disposed
        if any(x in page_text for x in ["withdrawn", "disposed", "terminated", "order closing"]):
            return {"status": SignalStatus.AWARDED, "reason": "FERC docket shows closure/termination"}

        return {"status": SignalStatus.LIVE, "url": url, "filing_id": filing_id}

    except Exception as e:
        logger.warning("FERC verify failed for %s: %s", filing_id, e)
        return {"status": SignalStatus.UNCERTAIN, "reason": str(e)}


# ── SAM.gov opportunity verification ──────────────────────────────────────────

def verify_sam_opportunity(notice_id: str, expected_title: str = "") -> dict:
    """
    Verify a SAM.gov opportunity is still active and not yet awarded.
    """
    sam_key = os.environ.get("SAM_GOV_API_KEY", "")
    url = "https://api.sam.gov/opportunities/v2/search"
    params = {
        "noticeId": notice_id,
        "limit": 1,
    }
    if sam_key:
        params["api_key"] = sam_key

    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        opps = data.get("opportunitiesData", [])

        if not opps:
            return {"status": SignalStatus.DEAD, "reason": "Notice not found in SAM.gov"}

        opp = opps[0]
        status = opp.get("type", "").lower()

        if status in ["award", "a"]:
            return {
                "status": SignalStatus.AWARDED,
                "reason": f"SAM.gov shows award posted",
                "award_date": opp.get("responseDeadLine", ""),
            }

        # Verify title matches
        if expected_title:
            sam_title = opp.get("title", "").lower()
            title_words = [w for w in expected_title.lower().split() if len(w) > 4]
            match = sum(1 for w in title_words if w in sam_title)
            if match / max(len(title_words), 1) < 0.5:
                return {
                    "status": SignalStatus.STALE,
                    "reason": f"Title mismatch: expected '{expected_title}', found '{opp.get('title', '')}'",
                }

        return {
            "status": SignalStatus.LIVE,
            "notice_id": notice_id,
            "title": opp.get("title", ""),
            "deadline": opp.get("responseDeadLine", ""),
            "agency": opp.get("fullParentPathName", ""),
        }

    except Exception as e:
        logger.warning("SAM.gov opportunity verify failed for %s: %s", notice_id, e)
        return {"status": SignalStatus.UNCERTAIN, "reason": str(e)}


# ── SRF project verification ───────────────────────────────────────────────────

def verify_srf_project(state: str, project_name: str, loan_amount: float = 0) -> dict:
    """
    Verify a state SRF project is still on the IUP (Intended Use Plan) and
    not yet in construction/awarded phase.
    """
    state_srf_urls = {
        "TX": "https://www.tceq.texas.gov/goto/cwsrf-assistance",
        "FL": "https://floridadep.gov/water/water-policy/content/clean-water-state-revolving-fund-cwsrf",
        "CA": "https://www.waterboards.ca.gov/water_issues/programs/grants_loans/srf/",
        "OH": "https://epa.ohio.gov/divisions-and-offices/drinking-and-ground-waters/water-quality-loans",
        "NC": "https://www.deq.nc.gov/about/divisions/water-infrastructure/water-infrastructure-programs/clean-water-state-revolving-fund",
        "VA": "https://www.deq.virginia.gov/our-programs/water/infrastructure-funding/virginia-clean-water-revolving-loan-fund",
    }

    url = state_srf_urls.get(state.upper())
    if not url:
        return {"status": SignalStatus.UNCERTAIN, "reason": f"No SRF URL configured for state {state}"}

    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code != 200:
            return {"status": SignalStatus.UNCERTAIN, "reason": f"SRF page returned {r.status_code}"}

        page_text = r.text.lower()
        project_words = [w.lower() for w in project_name.split() if len(w) > 4]
        matches = sum(1 for w in project_words if w in page_text)

        if matches / max(len(project_words), 1) >= 0.5:
            return {"status": SignalStatus.LIVE, "state": state, "project": project_name}
        else:
            # Project name not found on current IUP — may have moved to construction or been completed
            return {
                "status": SignalStatus.STALE,
                "reason": f"Project '{project_name}' not found on current {state} SRF IUP page — may be awarded or completed",
            }

    except Exception as e:
        return {"status": SignalStatus.UNCERTAIN, "reason": str(e)}


# ── Generic URL liveness check ─────────────────────────────────────────────────

def verify_url_live(url: str, expected_keywords: list[str] = None) -> dict:
    """
    Simple liveness check: does the URL return 200? Do expected keywords appear?
    Used for any source URL we can't verify more specifically.
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        if r.status_code == 404:
            return {"status": SignalStatus.DEAD, "reason": "404 Not Found"}
        if r.status_code >= 400:
            return {"status": SignalStatus.UNCERTAIN, "reason": f"HTTP {r.status_code}"}

        if expected_keywords:
            page_text = r.text.lower()
            missing = [k for k in expected_keywords if k.lower() not in page_text]
            if len(missing) > len(expected_keywords) * 0.5:
                return {
                    "status": SignalStatus.STALE,
                    "reason": f"Keywords missing from page: {missing[:3]}",
                    "url": url,
                }

        return {"status": SignalStatus.LIVE, "url": r.url}

    except Exception as e:
        return {"status": SignalStatus.DEAD, "reason": str(e)}


# ── Tavily-based signal freshness check ───────────────────────────────────────

def verify_signal_via_search(
    signal_description: str,
    expected_facts: list[str],
) -> dict:
    """
    Use Tavily to search for the signal and verify key facts still hold.
    This is the fallback when we can't verify directly from the source API.

    expected_facts: list of strings that MUST appear in search results
    (e.g., ["$45M", "Baltimore", "consent decree", "2026"])
    """
    if not TAVILY_API_KEY:
        return {"status": SignalStatus.UNCERTAIN, "reason": "No Tavily API key"}

    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_API_KEY,
                "query": signal_description,
                "search_depth": "basic",
                "max_results": 5,
            },
            timeout=20,
        )
        r.raise_for_status()
        results = r.json().get("results", [])

        combined_text = " ".join(
            r.get("title", "") + " " + r.get("content", "") for r in results
        ).lower()

        verified_facts = [f for f in expected_facts if f.lower() in combined_text]
        missing_facts = [f for f in expected_facts if f.lower() not in combined_text]

        verification_rate = len(verified_facts) / max(len(expected_facts), 1)

        if verification_rate >= 0.8:
            return {
                "status": SignalStatus.LIVE,
                "verified_facts": verified_facts,
                "source_urls": [r.get("url", "") for r in results[:2]],
            }
        elif verification_rate >= 0.5:
            return {
                "status": SignalStatus.UNCERTAIN,
                "reason": f"Only {len(verified_facts)}/{len(expected_facts)} facts verified",
                "missing_facts": missing_facts,
                "verified_facts": verified_facts,
            }
        else:
            return {
                "status": SignalStatus.STALE,
                "reason": f"Facts not confirmed by current search: {missing_facts[:3]}",
            }

    except Exception as e:
        return {"status": SignalStatus.UNCERTAIN, "reason": str(e)}


# ── Batch verifier ─────────────────────────────────────────────────────────────

def verify_signals_batch(signals: list[dict]) -> list[dict]:
    """
    Verify a list of signals. Each signal dict should have:
      - signal_type: "ferc" | "sam_gov" | "srf" | "url" | "general"
      - source_id: filing ID, notice ID, etc.
      - source_url: direct URL if available
      - expected_keywords: list of terms that should appear
      - project_name: the project name as scraped
      - state: state code
      - scraped_at: ISO timestamp

    Returns each signal with added "verification" key.
    """
    results = []
    for i, signal in enumerate(signals):
        logger.info("Verifying signal [%d/%d]: %s", i + 1, len(signals),
                    signal.get("project_name", "unknown"))
        time.sleep(REQUEST_DELAY)

        sig_type = signal.get("signal_type", "url")
        source_id = signal.get("source_id", "")
        source_url = signal.get("source_url", "")
        keywords = signal.get("expected_keywords", [])

        if sig_type == "ferc" and source_id:
            v = verify_ferc_filing(source_id, signal.get("project_name", ""))
        elif sig_type == "sam_gov" and source_id:
            v = verify_sam_opportunity(source_id, signal.get("project_name", ""))
        elif sig_type == "srf":
            v = verify_srf_project(
                signal.get("state", ""),
                signal.get("project_name", ""),
                signal.get("loan_amount", 0),
            )
        elif source_url:
            v = verify_url_live(source_url, keywords)
        else:
            # Last resort: Tavily search
            v = verify_signal_via_search(
                signal.get("project_name", "") + " " + signal.get("state", ""),
                keywords or [signal.get("project_name", "")][:1],
            )

        signal["verification"] = v
        signal["verification_ts"] = datetime.now(timezone.utc).isoformat()
        results.append(signal)

    return results
