"""
signals/healthcare_job_posting_monitor.py — Healthcare referral pipeline hiring signal detector.

Monitors job postings for healthcare businesses that are actively scaling capacity —
the exact moment they need a physician referral pipeline built.

Signal logic:
  A compounding pharmacy posting for a "business development" rep is failing to grow
  organically. A med spa posting for an injector just doubled its chair count. These
  companies are in investment mode — physician outreach timed to this moment converts
  at a materially higher rate than cold outreach with no timing signal.

Niche coverage:
  1. Compounding pharmacies — technician/pharmacist/business development hires
  2. Infusion pharmacies / IV therapy — nurse/coordinator/admissions hires
  3. Sleep centers / sleep labs — coordinator/technician/RPSGT hires
  4. Medical spas — injector/aesthetic nurse/PA/NP hires
  5. LASIK / refractive surgery centers — coordinator/counselor hires
  6. Pain clinics — coordinator/manager/director hires

Flow:
  1. ThreadPoolExecutor (6 workers) — parallel RapidAPI Indeed searches per keyword set
  2. Filter: posted within 3 days, US only
  3. Extract: company name, location, job title, posting date, website
  4. NPI Registry cross-reference: get NPI number, phone, address by company name
  5. Map job title → outreach angle
  6. Airtable dedup check against signals_raw (company_name)
  7. Push new signals to Airtable signals_raw with source=job_posting
  8. Enroll in Smartlead niche-matched sequence
  9. Slack notify #ecas-ops: digest of new signals

Cron: 0 8 * * 2,5  (Tuesday + Friday 8am CT)

Usage:
    python3 signals/healthcare_job_posting_monitor.py --dry-run
    python3 signals/healthcare_job_posting_monitor.py --niche compounding
    python3 signals/healthcare_job_posting_monitor.py        # all niches
"""

import argparse
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

# ── Env / secrets ──────────────────────────────────────────────────────────────

RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "")
AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY", "")
SMARTLEAD_API_KEY = os.environ.get("SMARTLEAD_API_KEY", "")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")

# Airtable — ECAS base, signals_raw table (appoi8SzEJY8in57x)
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID", "appoi8SzEJY8in57x")
AIRTABLE_SIGNALS_TABLE = "tblAFJnXToLTKeaNU"

# ── Keyword sets per niche ─────────────────────────────────────────────────────
#
# Each entry is a (niche_key, query, niche_label) tuple.
# query is sent verbatim to the Indeed API search endpoint.

HEALTHCARE_KEYWORD_SETS = [
    # Compounding pharmacy — technician or pharmacist hire = scaling production capacity
    (
        "compounding",
        '"compounding pharmacy" AND ("technician" OR "pharmacist" OR "business development")',
        "Compounding Pharmacy",
    ),
    # Infusion pharmacy / IV therapy — nurse/coordinator hire = scaling patient volume
    (
        "infusion",
        '"infusion pharmacy" AND ("nurse" OR "coordinator" OR "admissions")',
        "Infusion Pharmacy / IV Therapy",
    ),
    # Sleep center — RPSGT or coordinator hire = bed capacity expansion
    (
        "sleep",
        '("sleep center" OR "sleep lab") AND ("coordinator" OR "technician" OR "RPSGT")',
        "Sleep Center / Sleep Lab",
    ),
    # Medical spa — injector hire = adding provider capacity
    (
        "medspa",
        '"medical spa" AND ("injector" OR "aesthetic nurse" OR "PA" OR "NP")',
        "Medical Spa",
    ),
    # LASIK / refractive surgery — coordinator hire = front-end volume growth
    (
        "lasik",
        '("LASIK" OR "refractive surgery") AND ("coordinator" OR "counselor")',
        "LASIK / Refractive Surgery Center",
    ),
    # Pain clinic — coordinator/manager/director hire = scaling referral intake
    (
        "pain",
        '"pain clinic" AND ("coordinator" OR "manager" OR "director")',
        "Pain Clinic",
    ),
]

# ── Outreach angle mapping ─────────────────────────────────────────────────────
#
# Maps job title keywords → outreach angle label.
# The angle gets pushed to Airtable and used to select the right email copy.

TITLE_TO_ANGLE = [
    # High-intent: explicitly trying to build BD function
    (["business development", "bd rep", "sales rep", "account executive"], "scaling_prescriber_network"),
    # Director/manager hire = building leadership layer to support growth
    (["director", "manager", "administrator"], "growth_leadership_hire"),
    # Clinical coordinator = adding intake/referral handling capacity
    (["coordinator", "admissions", "patient coordinator"], "referral_intake_expansion"),
    # Injector/aesthetic provider = adding revenue-generating capacity
    (["injector", "aesthetic nurse", "aesthetic provider", "np ", "pa "], "provider_capacity_expansion"),
    # Technician = scaling production volume
    (["technician", "tech ", "pharmacist", "rpsgt", "polysomnography"], "volume_growth"),
    # Counselor = pre-sales / conversion function being built out
    (["counselor", "consultant"], "conversion_function_build"),
]

# ── Smartlead campaign IDs per niche (healthcare referral pipeline) ────────────
#
# Placeholder IDs — replace with actual Smartlead campaign IDs once created.
# Each niche gets its own sequence variant.

NICHE_CAMPAIGN_MAP = {
    "compounding": os.environ.get("SL_CAMPAIGN_COMPOUNDING", ""),
    "infusion":    os.environ.get("SL_CAMPAIGN_INFUSION", ""),
    "sleep":       os.environ.get("SL_CAMPAIGN_SLEEP", ""),
    "medspa":      os.environ.get("SL_CAMPAIGN_MEDSPA", ""),
    "lasik":       os.environ.get("SL_CAMPAIGN_LASIK", ""),
    "pain":        os.environ.get("SL_CAMPAIGN_PAIN", ""),
}

# ── Indeed API via RapidAPI ────────────────────────────────────────────────────

INDEED_RAPIDAPI_HOST = "indeed12.p.rapidapi.com"
INDEED_API_URL = "https://indeed12.p.rapidapi.com/jobs/search"

# Maximum posting age to accept (days)
MAX_POSTING_AGE_DAYS = 3


def search_indeed(query: str, location: str = "United States", num: int = 20) -> list[dict]:
    """
    Search Indeed jobs via RapidAPI.
    Returns raw list of job posting dicts.
    """
    if not RAPIDAPI_KEY:
        logger.warning("[Indeed] RAPIDAPI_KEY not set — skipping search")
        return []

    try:
        resp = requests.get(
            INDEED_API_URL,
            headers={
                "x-rapidapi-host": INDEED_RAPIDAPI_HOST,
                "x-rapidapi-key": RAPIDAPI_KEY,
            },
            params={
                "query": query,
                "location": location,
                "page_id": "1",
                "country": "us",
                "fromage": str(MAX_POSTING_AGE_DAYS),   # days: 1, 3, 7, 14
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        hits = data.get("hits", [])
        logger.debug(f"[Indeed] '{query[:60]}': {len(hits)} postings")
        return hits

    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "?"
        if status == 429:
            logger.warning("[Indeed] Rate limited — sleeping 30s")
            time.sleep(30)
        else:
            logger.warning(f"[Indeed] HTTP {status} for query '{query[:60]}': {e}")
        return []
    except Exception as e:
        logger.warning(f"[Indeed] Error for query '{query[:60]}': {e}")
        return []


# ── Job data normalization ─────────────────────────────────────────────────────

def _is_us_location(location: str) -> bool:
    """Basic US location check. Rejects obvious non-US postings."""
    if not location:
        return True  # No location = assume US if we searched US
    location_lower = location.lower()
    non_us_indicators = [
        "canada", "ontario", "british columbia", "alberta", "uk", "united kingdom",
        "london", "australia", "remote - anywhere",
    ]
    return not any(ind in location_lower for ind in non_us_indicators)


def _extract_company_website(job: dict) -> str:
    """Try to extract company domain from job posting data."""
    # RapidAPI Indeed may include company URL in various fields
    for field in ["company_url", "employer_url", "company_homepage", "url"]:
        val = job.get(field, "")
        if val and "indeed.com" not in val:
            return val.strip()
    return ""


def _map_title_to_angle(title: str) -> str:
    """Map job title string to outreach angle."""
    title_lower = title.lower()
    for keywords, angle in TITLE_TO_ANGLE:
        if any(kw in title_lower for kw in keywords):
            return angle
    return "general_growth_hire"


def normalize_job(raw: dict) -> Optional[dict]:
    """
    Normalize a RapidAPI Indeed job result into our signal schema.
    Returns None if the posting should be filtered out.
    """
    company = (
        raw.get("company_name", "")
        or raw.get("employer", {}).get("name", "")
        or raw.get("company", "")
    ).strip()

    title = (raw.get("job_title", "") or raw.get("title", "")).strip()
    location = (raw.get("location", "") or raw.get("formatted_location", "")).strip()

    if not company or not title:
        return None

    # US filter
    if not _is_us_location(location):
        return None

    # Skip obvious chains / hospital systems — we want independent practices
    company_lower = company.lower()
    skip_if_contains = [
        "cvs", "walgreens", "rite aid", "walmart", "kroger",
        "hospital system", "health system", "hca ", "tenet health",
        "staffing", "recruiting", "talent solutions", "executive search",
        "indeed", "ziprecruiter",
    ]
    if any(skip in company_lower for skip in skip_if_contains):
        return None

    website = _extract_company_website(raw)
    posting_date = raw.get("date", raw.get("post_date", ""))

    return {
        "company_name": company,
        "job_title": title,
        "location": location,
        "website": website,
        "posting_date": posting_date,
        "outreach_angle": _map_title_to_angle(title),
        "raw_job_id": str(raw.get("id", raw.get("job_id", ""))),
    }


# ── NPI Registry cross-reference ──────────────────────────────────────────────

NPI_API_URL = "https://npiregistry.cms.hhs.gov/api/"

# Taxonomy codes for healthcare businesses (client targets)
NICHE_TAXONOMY_MAP = {
    "compounding": ["3336C0003X"],
    "infusion":    ["3336H0001X"],
    "sleep":       ["261QS1200X"],
    "medspa":      ["261QD0000X"],   # Closest available code (clinical/outpatient)
    "lasik":       ["261QO0400X"],   # Optometry / LASIK centers
    "pain":        ["261QP3300X"],
}


def lookup_npi(company_name: str, state: str = "") -> dict:
    """
    Search NPI Registry by organization name.
    Returns first matching record with NPI, phone, address.
    Falls back gracefully — NPI is useful but not required for enrollment.
    """
    try:
        params = {
            "version": "2.1",
            "organization_name": company_name[:50],  # API max
            "limit": 5,
        }
        if state:
            params["state"] = state

        resp = requests.get(NPI_API_URL, params=params, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("results", [])

        if not results:
            return {}

        # Prefer exact-ish name match
        best = results[0]
        basic = best.get("basic", {})
        addresses = best.get("addresses", [{}])
        addr = addresses[0] if addresses else {}

        return {
            "npi": best.get("number", ""),
            "npi_org_name": basic.get("organization_name", ""),
            "npi_phone": addr.get("telephone_number", ""),
            "npi_address": addr.get("address_1", ""),
            "npi_city": addr.get("city", ""),
            "npi_state": addr.get("state", ""),
            "npi_zip": addr.get("postal_code", ""),
        }

    except Exception as e:
        logger.debug(f"[NPI] Lookup failed for '{company_name}': {e}")
        return {}


def _extract_state_from_location(location: str) -> str:
    """Pull 2-letter state abbreviation from a location string like 'Austin, TX'."""
    if not location:
        return ""
    parts = location.replace(",", " ").split()
    us_states = {
        "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN",
        "IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV",
        "NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN",
        "TX","UT","VT","VA","WA","WV","WI","WY","DC",
    }
    for part in reversed(parts):
        if part.upper() in us_states:
            return part.upper()
    return ""


# ── Airtable dedup + push ──────────────────────────────────────────────────────

def _airtable_headers() -> dict:
    return {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json",
    }


def _company_already_in_signals(company_name: str) -> bool:
    """
    Check if company is already in ECAS signals_raw table.
    Simple name match — good enough for dedup purposes.
    """
    if not AIRTABLE_API_KEY:
        return False

    try:
        url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_SIGNALS_TABLE}"
        # Airtable formula: exact company name match (case-insensitive via LOWER)
        formula = f"LOWER({{company_name}})=LOWER('{company_name.replace(chr(39), '')}')"
        resp = requests.get(
            url,
            headers=_airtable_headers(),
            params={"filterByFormula": formula, "maxRecords": 1},
            timeout=15,
        )
        resp.raise_for_status()
        records = resp.json().get("records", [])
        return len(records) > 0
    except Exception as e:
        logger.debug(f"[Airtable dedup] Error checking '{company_name}': {e}")
        return False  # On error, allow through (avoid silent drops)


def push_signal_to_airtable(signal: dict, dry_run: bool = False) -> bool:
    """
    Create a new record in signals_raw with job posting signal data.
    Returns True on success.
    """
    if dry_run:
        logger.info(f"  [DRY RUN] Would push: {signal['company_name']} | {signal['job_title']} | {signal['outreach_angle']}")
        return True

    if not AIRTABLE_API_KEY:
        return False

    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_SIGNALS_TABLE}"

    # Build a single descriptive raw_content string for the signal
    npi_info = ""
    if signal.get("npi"):
        npi_info = (
            f"\nNPI: {signal['npi']} | {signal.get('npi_address', '')} "
            f"{signal.get('npi_city', '')}, {signal.get('npi_state', '')} {signal.get('npi_zip', '')}"
            f"\nPhone: {signal.get('npi_phone', '')}"
        )

    raw_content = (
        f"Job Posting Signal — {signal['niche_label']}\n"
        f"Company: {signal['company_name']}\n"
        f"Job Title: {signal['job_title']}\n"
        f"Location: {signal['location']}\n"
        f"Posting Date: {signal.get('posting_date', '')}\n"
        f"Outreach Angle: {signal['outreach_angle']}\n"
        f"Website: {signal.get('website', '')}"
        + npi_info
        + f"\n\nSource: Indeed (RapidAPI) | Signal type: job_posting_growth_hire"
        + f"\nNiche: {signal['niche_label']}"
    )

    fields = {
        "company_name": signal["company_name"],
        "signal_type": "job_posting",
        "source": "indeed_rapidapi",
        "signal_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "raw_content": raw_content,
        "heat_score": _angle_to_heat_score(signal["outreach_angle"]),
        "sector": signal.get("niche_label", "Healthcare"),
        # Extended fields for healthcare pipeline
        "npi_number": signal.get("npi", ""),
        "job_title_signal": signal.get("job_title", ""),
        "outreach_angle": signal.get("outreach_angle", ""),
        "phone": signal.get("npi_phone", ""),
        "address": (
            f"{signal.get('npi_address', '')} {signal.get('npi_city', '')}, "
            f"{signal.get('npi_state', '')} {signal.get('npi_zip', '')}".strip(", ")
        ),
    }

    # Remove empty strings to avoid Airtable validation errors on typed fields
    fields = {k: v for k, v in fields.items() if v not in ("", None)}

    try:
        resp = requests.post(
            url,
            headers=_airtable_headers(),
            json={"fields": fields},
            timeout=15,
        )
        resp.raise_for_status()
        logger.info(f"[Airtable] Created signal: {signal['company_name']} ({signal['outreach_angle']})")
        return True
    except Exception as e:
        logger.error(f"[Airtable] Failed to create signal for {signal['company_name']}: {e}")
        return False


def _angle_to_heat_score(angle: str) -> float:
    """
    Convert outreach angle to a heat score for prioritization.
    Business development hire = highest intent.
    """
    scores = {
        "scaling_prescriber_network": 72.0,
        "growth_leadership_hire":     65.0,
        "provider_capacity_expansion": 60.0,
        "referral_intake_expansion":  58.0,
        "conversion_function_build":  55.0,
        "volume_growth":              50.0,
        "general_growth_hire":        45.0,
    }
    return scores.get(angle, 45.0)


# ── Smartlead enrollment ───────────────────────────────────────────────────────

SMARTLEAD_API_URL = "https://server.smartlead.ai/api/v1"


def enroll_in_smartlead(signal: dict, campaign_id: str, dry_run: bool = False) -> bool:
    """
    Enroll a new signal contact in the appropriate Smartlead campaign.
    Uses company name + NPI phone as lead data (email enrichment happens separately).
    """
    if dry_run:
        logger.info(f"  [DRY RUN] Would enroll in Smartlead campaign {campaign_id}: {signal['company_name']}")
        return True

    if not SMARTLEAD_API_KEY or not campaign_id:
        return False

    lead_data = {
        "company_name": signal["company_name"],
        "location": signal.get("location", ""),
        "phone": signal.get("npi_phone", ""),
        "website": signal.get("website", ""),
        "custom_fields": {
            "npi_number":       signal.get("npi", ""),
            "job_title_signal": signal.get("job_title", ""),
            "outreach_angle":   signal.get("outreach_angle", ""),
            "niche":            signal.get("niche_label", ""),
            "signal_source":    "job_posting",
        },
    }

    # Smartlead requires email — use placeholder if not available yet.
    # Email enrichment is a separate step (Findymail waterfall or Clay).
    lead_data["email"] = signal.get("email", f"pending-{signal['raw_job_id']}@enrich.later")

    try:
        resp = requests.post(
            f"{SMARTLEAD_API_URL}/campaigns/{campaign_id}/leads",
            params={"api_key": SMARTLEAD_API_KEY},
            json={"lead_list": [lead_data]},
            timeout=15,
        )
        resp.raise_for_status()
        logger.info(f"[Smartlead] Enrolled {signal['company_name']} in campaign {campaign_id}")
        return True
    except Exception as e:
        logger.warning(f"[Smartlead] Enroll failed for {signal['company_name']}: {e}")
        return False


# ── Slack notification ─────────────────────────────────────────────────────────

def send_slack_digest(new_signals: list[dict], dry_run: bool = False) -> None:
    """
    Post a digest of new job posting signals to #ecas-ops.
    """
    if dry_run or not new_signals:
        return

    if not SLACK_WEBHOOK_URL:
        logger.warning("[Slack] SLACK_WEBHOOK_URL not set — skipping notification")
        return

    lines = [f"*{len(new_signals)} new healthcare job posting signals*"]
    for s in new_signals[:20]:   # cap at 20 to keep Slack readable
        angle_label = s["outreach_angle"].replace("_", " ")
        lines.append(
            f"• *{s['company_name']}* ({s.get('niche_label', '')})"
            f" — _{s['job_title']}_ → {angle_label}"
            f" | {s.get('location', 'location unknown')}"
        )

    if len(new_signals) > 20:
        lines.append(f"_...and {len(new_signals) - 20} more_")

    lines.append(f"_Run: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_")

    try:
        resp = requests.post(
            SLACK_WEBHOOK_URL,
            json={"text": "\n".join(lines)},
            timeout=10,
        )
        resp.raise_for_status()
        logger.info(f"[Slack] Digest sent: {len(new_signals)} signals")
    except Exception as e:
        logger.warning(f"[Slack] Failed to send digest: {e}")


# ── Parallel search runner ─────────────────────────────────────────────────────

def _search_one_keyword_set(args: tuple) -> list[dict]:
    """
    Worker function: search Indeed for one keyword set, normalize results.
    Returns list of normalized job dicts.
    """
    niche_key, query, niche_label = args
    raw_results = search_indeed(query)
    normalized = []
    for raw in raw_results:
        job = normalize_job(raw)
        if job:
            job["niche_key"] = niche_key
            job["niche_label"] = niche_label
            normalized.append(job)
    return normalized


def run_parallel_searches(target_niches: Optional[list[str]] = None) -> list[dict]:
    """
    Run all keyword set searches in parallel (6 workers).
    Returns deduplicated list of normalized job postings.
    """
    keyword_sets = [
        kset for kset in HEALTHCARE_KEYWORD_SETS
        if target_niches is None or kset[0] in target_niches
    ]

    all_jobs: list[dict] = []
    seen_ids: set[str] = set()

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(_search_one_keyword_set, kset): kset for kset in keyword_sets}
        for future in as_completed(futures):
            try:
                jobs = future.result()
                for job in jobs:
                    # Dedup by raw_job_id within this run
                    jid = job.get("raw_job_id", "")
                    if jid and jid in seen_ids:
                        continue
                    if jid:
                        seen_ids.add(jid)
                    all_jobs.append(job)
                logger.info(f"[Search] {futures[future][2]}: {len(jobs)} results")
            except Exception as e:
                logger.warning(f"[Search] Worker error: {e}")

    return all_jobs


# ── NPI enrichment (parallel) ─────────────────────────────────────────────────

def enrich_with_npi(jobs: list[dict]) -> list[dict]:
    """
    Cross-reference each job against NPI Registry.
    Adds npi, npi_phone, npi_address fields.
    Runs in parallel (6 workers) — NPI API handles concurrent requests fine.
    """
    def _lookup(job: dict) -> dict:
        state = _extract_state_from_location(job.get("location", ""))
        npi_data = lookup_npi(job["company_name"], state)
        job.update(npi_data)
        time.sleep(0.1)   # Light throttle to be a good citizen
        return job

    enriched = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(_lookup, job): job for job in jobs}
        for future in as_completed(futures):
            try:
                enriched.append(future.result())
            except Exception as e:
                logger.debug(f"[NPI enrich] Worker error: {e}")
                enriched.append(futures[future])

    return enriched


# ── Main pipeline ──────────────────────────────────────────────────────────────

def run_healthcare_job_monitor(
    niche: Optional[str] = None,
    dry_run: bool = False,
) -> dict:
    """
    Run the healthcare job posting signal monitor.

    Args:
        niche: specific niche key to run, or None for all niches
        dry_run: search + log results without writing to Airtable/Smartlead

    Returns:
        Summary dict with counts
    """
    if not RAPIDAPI_KEY:
        logger.error("[HealthcareJobMonitor] RAPIDAPI_KEY not set — cannot run")
        return {"error": "RAPIDAPI_KEY not configured"}

    target_niches = [niche] if niche else None

    logger.info(f"[HealthcareJobMonitor] Starting search — niches: {target_niches or 'all'}")
    all_jobs = run_parallel_searches(target_niches)
    logger.info(f"[HealthcareJobMonitor] Raw results: {len(all_jobs)} job postings")

    if not all_jobs:
        logger.info("[HealthcareJobMonitor] No job postings found — nothing to process")
        return {"searched": 0, "new_signals": 0, "skipped_dedup": 0, "errors": 0}

    # NPI enrichment
    logger.info("[HealthcareJobMonitor] Enriching with NPI Registry...")
    all_jobs = enrich_with_npi(all_jobs)

    # Dedup against Airtable + push new signals
    new_signals: list[dict] = []
    skipped_dedup = 0
    errors = 0

    for job in all_jobs:
        if _company_already_in_signals(job["company_name"]):
            logger.debug(f"[Dedup] Skipping {job['company_name']} — already in signals_raw")
            skipped_dedup += 1
            continue

        # Push to Airtable
        ok = push_signal_to_airtable(job, dry_run=dry_run)
        if not ok:
            errors += 1
            continue

        # Enroll in Smartlead niche campaign
        campaign_id = NICHE_CAMPAIGN_MAP.get(job["niche_key"], "")
        if campaign_id:
            enroll_in_smartlead(job, campaign_id, dry_run=dry_run)
        else:
            logger.debug(f"[Smartlead] No campaign configured for niche '{job['niche_key']}' — skipping enrollment")

        new_signals.append(job)
        time.sleep(0.15)   # Airtable rate limit

    # Slack digest
    if new_signals:
        send_slack_digest(new_signals, dry_run=dry_run)

    summary = {
        "searched": len(all_jobs),
        "new_signals": len(new_signals),
        "skipped_dedup": skipped_dedup,
        "errors": errors,
        "niches_run": target_niches or "all",
    }

    logger.info(
        f"[HealthcareJobMonitor] Done — "
        f"{summary['new_signals']} new signals, "
        f"{summary['skipped_dedup']} dupes skipped, "
        f"{summary['errors']} errors"
    )

    return summary


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import logging as _logging
    _logging.basicConfig(
        level=_logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Healthcare Referral Pipeline — Job Posting Signal Monitor",
        epilog="Cron: 0 8 * * 2,5  (Tuesday + Friday 8am CT)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Search and log results without writing to Airtable or Smartlead",
    )
    parser.add_argument(
        "--niche",
        choices=["compounding", "infusion", "sleep", "medspa", "lasik", "pain"],
        default=None,
        help="Run a single niche instead of all (default: all)",
    )
    args = parser.parse_args()

    result = run_healthcare_job_monitor(niche=args.niche, dry_run=args.dry_run)
    print(f"\nResult: {result}")
