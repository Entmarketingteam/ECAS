"""
enrichment/zip_enricher.py
Enriches ECAS leads with ZIP-level market data from Supabase.

Given a company ZIP code, returns:
- Market strength score (0-100) for lead prioritization
- Key demographic signals for personalization
- Zillow real estate trend (growing/stable/declining market)
- Health/workforce quality signals

Queries: zip_codes, zip_demographics, zip_monthly, zip_health
"""

import logging
import os
import requests
from functools import lru_cache

logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
LATEST_CENSUS_YEAR = 2024


def _sb_get(table: str, params: dict) -> list:
    """Query Supabase REST API."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.warning("[ZipEnricher] SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set")
        return []
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{table}", headers=headers, params=params, timeout=10)
    if r.status_code != 200:
        logger.warning(f"[ZipEnricher] Supabase {table} query failed: {r.status_code}")
        return []
    return r.json()


@lru_cache(maxsize=2000)
def get_zip_demographics(zip_code: str, year: int = LATEST_CENSUS_YEAR) -> dict:
    """Fetch Census ACS demographics for a ZIP code."""
    z = str(zip_code).zfill(5)
    rows = _sb_get("zip_demographics", {
        "zip": f"eq.{z}",
        "year": f"eq.{year}",
        "select": ",".join([
            "population", "age_median", "income_household_median",
            "income_individual_median", "income_household_six_figure",
            "education_college_or_above", "labor_force_participation",
            "unemployment_rate", "poverty", "home_ownership",
            "home_value", "rent_median", "veteran", "self_employed",
            "age_30s", "age_40s", "age_50s", "married",
        ]),
    })
    return rows[0] if rows else {}


@lru_cache(maxsize=2000)
def get_zip_geo(zip_code: str) -> dict:
    """Fetch base geo info for a ZIP code."""
    z = str(zip_code).zfill(5)
    rows = _sb_get("zip_codes", {
        "zip": f"eq.{z}",
        "select": "city,state_id,state_name,county_name,lat,lng,timezone,population,density",
    })
    return rows[0] if rows else {}


@lru_cache(maxsize=500)
def get_zip_health(zip_code: str) -> dict:
    """Fetch CDC PLACES health data for a ZIP code."""
    z = str(zip_code).zfill(5)
    rows = _sb_get("zip_health", {
        "zip": f"eq.{z}",
        "order": "year.desc",
        "limit": "1",
        "select": "obesity,diabetes,smoking,depression,high_blood_pressure,no_healthcare_access,heart_disease,stroke,asthma,no_checkup,physical_inactivity",
    })
    return rows[0] if rows else {}


def get_zip_home_value_trend(zip_code: str, months: int = 12) -> dict:
    """
    Get Zillow home value trend for a ZIP.
    Returns latest value + % change over last N months.
    """
    z = str(zip_code).zfill(5)
    rows = _sb_get("zip_monthly", {
        "zip": f"eq.{z}",
        "order": "date.desc",
        "limit": str(months),
        "select": "date,home_value,rent_index",
    })
    if len(rows) < 2:
        return {}

    latest = rows[0]
    oldest = rows[-1]
    latest_val = latest.get("home_value")
    oldest_val = oldest.get("home_value")

    pct_change = None
    if latest_val and oldest_val and oldest_val > 0:
        pct_change = round((latest_val - oldest_val) / oldest_val * 100, 1)

    trend = "stable"
    if pct_change is not None:
        if pct_change > 5:   trend = "growing"
        elif pct_change < -5: trend = "declining"

    return {
        "home_value_latest": latest_val,
        "home_value_12mo_pct_change": pct_change,
        "rent_index_latest": latest.get("rent_index"),
        "trend": trend,
        "as_of": latest.get("date"),
    }


def score_market_strength(zip_code: str) -> dict:
    """
    Calculate a market strength score (0-100) for ECAS lead prioritization.

    Score components:
    - Labor market strength (25pts): participation rate + low unemployment
    - Economic strength (25pts): median income + six-figure household %
    - Workforce quality (20pts): education + self-employment
    - Market growth (20pts): Zillow home value trend
    - Population density (10pts): active commercial market indicator

    Returns score + breakdown + key signals for personalization.
    """
    z = str(zip_code).zfill(5)
    dem = get_zip_demographics(z)
    geo = get_zip_geo(z)
    trend = get_zip_home_value_trend(z)

    if not dem and not geo:
        return {"zip": z, "market_score": None, "error": "ZIP not found"}

    def safe(val, default=0):
        return val if val is not None else default

    # ── Labor market (25pts) ──────────────────────────────────────
    labor = safe(dem.get("labor_force_participation"), 60)
    unemp = safe(dem.get("unemployment_rate"), 5)
    labor_score = min((labor - 50) / 20 * 15, 15)          # 50-70% range → 0-15pts
    unemp_score = max(0, (10 - unemp) / 10 * 10)           # 0-10% unemployment → 0-10pts
    labor_total = round(labor_score + unemp_score, 1)

    # ── Economic strength (25pts) ─────────────────────────────────
    income = safe(dem.get("income_household_median"), 50000)
    six_fig = safe(dem.get("income_household_six_figure"), 0)
    income_score = min((income - 30000) / 120000 * 15, 15)  # $30K-$150K → 0-15pts
    six_fig_score = min(six_fig / 40 * 10, 10)              # 0-40% six-fig → 0-10pts
    econ_total = round(income_score + six_fig_score, 1)

    # ── Workforce quality (20pts) ─────────────────────────────────
    edu = safe(dem.get("education_college_or_above"), 20)
    self_emp = safe(dem.get("self_employed"), 0)
    edu_score = min(edu / 60 * 15, 15)                      # 0-60% college → 0-15pts
    self_emp_score = min(self_emp / 15 * 5, 5)              # 0-15% self-emp → 0-5pts
    workforce_total = round(edu_score + self_emp_score, 1)

    # ── Market growth (20pts) ─────────────────────────────────────
    pct_change = trend.get("home_value_12mo_pct_change")
    if pct_change is not None:
        growth_score = min(max((pct_change + 10) / 25 * 20, 0), 20)  # -10% to +15% → 0-20pts
    else:
        growth_score = 10  # neutral if no Zillow data

    # ── Population/density (10pts) ────────────────────────────────
    pop = safe(geo.get("population") or dem.get("population"), 5000)
    density = safe(geo.get("density"), 100)
    pop_score = min(pop / 50000 * 5, 5)
    density_score = min(density / 500 * 5, 5)
    market_size_total = round(pop_score + density_score, 1)

    composite = round(labor_total + econ_total + workforce_total + growth_score + market_size_total, 1)

    market_tier = "weak"
    if composite >= 70:   market_tier = "strong"
    elif composite >= 50: market_tier = "moderate"

    return {
        "zip":          z,
        "city":         geo.get("city"),
        "state":        geo.get("state_id"),
        "county":       geo.get("county_name"),
        "market_score": composite,
        "market_tier":  market_tier,
        "components": {
            "labor_market":      labor_total,
            "economic_strength": econ_total,
            "workforce_quality": workforce_total,
            "market_growth":     round(growth_score, 1),
            "market_size":       market_size_total,
        },
        "signals": {
            "income_median":          dem.get("income_household_median"),
            "income_six_figure_pct":  dem.get("income_household_six_figure"),
            "education_college_pct":  dem.get("education_college_or_above"),
            "labor_participation":    dem.get("labor_force_participation"),
            "unemployment_rate":      dem.get("unemployment_rate"),
            "self_employed_pct":      dem.get("self_employed"),
            "home_value":             trend.get("home_value_latest"),
            "home_value_12mo_change": trend.get("home_value_12mo_pct_change"),
            "market_trend":           trend.get("trend", "unknown"),
            "population":             geo.get("population") or dem.get("population"),
        },
    }


def enrich_lead(company_name: str, zip_code: str) -> dict:
    """
    Full enrichment for an ECAS lead.
    Returns market context to plug into lead scoring and email personalization.
    """
    if not zip_code:
        return {"company": company_name, "zip": None, "market_score": None, "error": "No ZIP provided"}

    z = str(zip_code).strip().zfill(5)
    market = score_market_strength(z)
    health = get_zip_health(z)

    result = {
        "company":      company_name,
        "zip":          z,
        "city":         market.get("city"),
        "state":        market.get("state"),
        "county":       market.get("county"),
        "market_score": market.get("market_score"),
        "market_tier":  market.get("market_tier"),
        "components":   market.get("components", {}),
        "signals":      market.get("signals", {}),
    }

    if health:
        result["health_signals"] = {
            "obesity_pct":     health.get("obesity"),
            "smoking_pct":     health.get("smoking"),
            "uninsured_pct":   health.get("no_healthcare_access"),
        }

    return result


def batch_enrich(leads: list[dict], zip_field: str = "zip", name_field: str = "company") -> list[dict]:
    """
    Enrich a list of lead dicts with ZIP market data.
    Each lead dict must have zip_field and name_field keys.
    Returns list with market data merged in.
    """
    results = []
    for lead in leads:
        z = lead.get(zip_field, "")
        name = lead.get(name_field, "")
        enriched = enrich_lead(name, z)
        results.append({**lead, **enriched})
    return results


if __name__ == "__main__":
    import json, sys
    zip_input = sys.argv[1] if len(sys.argv) > 1 else "77002"  # Houston default
    print(json.dumps(enrich_lead("Test Company", zip_input), indent=2))
