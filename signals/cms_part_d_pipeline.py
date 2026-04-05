"""
signals/cms_part_d_pipeline.py
CMS Part D Prescribing Data Pipeline — Physician Targeting for Pharmacy Clients.

Pulls Medicare Part D prescribing data from CMS API to identify physicians
already writing the exact scripts a compounding pharmacy client wants to compound.
This is what pharma reps pay IQVIA $50k+/year to access — free via CMS.

Data source: https://data.cms.gov/provider-summary-by-type-of-service/medicare-part-d-prescribers
API: https://data.cms.gov/data-api/v1/dataset/{dataset_id}/data

Usage:
    doppler run --project ent-agency-automation --config dev -- \\
        python signals/cms_part_d_pipeline.py --state TX --drugs semaglutide,estradiol,testosterone

    python signals/cms_part_d_pipeline.py --help
"""

import argparse
import csv
import json
import logging
import os
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CMS API config
# ---------------------------------------------------------------------------

# 2022 dataset: "Part D Prescribers by Provider and Drug"
# Confirmed ID: 9552919b-5568-4b4b-8f82-8e4d2e0a0ef4
# Note: check data.cms.gov for updated dataset IDs when newer years release
CMS_DATASET_ID = "9552919b-5568-4b4b-8f82-8e4d2e0a0ef4"
CMS_API_BASE = f"https://data.cms.gov/data-api/v1/dataset/{CMS_DATASET_ID}/data"
CMS_API_KEY = os.environ.get("CMS_API_KEY", "")  # Optional — increases rate limits

CMS_PAGE_SIZE = 1000  # Max rows per CMS API call
CMS_MAX_PAGES = 50    # Safety cap — 50k rows per drug per state is plenty
CMS_TIMEOUT = 30      # Seconds per request

# NPI Registry API (public, no key required)
NPI_REGISTRY_URL = "https://npiregistry.cms.hhs.gov/api/"
NPI_TIMEOUT = 20
NPI_BATCH_SIZE = 50   # NPIs to look up in one registry call (API supports individual lookups only)

# CMS field names
FIELD_NPI = "Prscrbr_NPI"
FIELD_LAST_NAME = "Prscrbr_Last_Org_Name"
FIELD_FIRST_NAME = "Prscrbr_First_Name"
FIELD_CITY = "Prscrbr_City"
FIELD_STATE = "Prscrbr_State_Abrvtn"
FIELD_ZIP = "Prscrbr_Zip5"
FIELD_SPECIALTY = "Prscrbr_Type"
FIELD_DRUG_GENERIC = "Gnrc_Name"
FIELD_DRUG_BRAND = "Brnd_Name"
FIELD_TOTAL_CLAIMS = "Tot_Clms"
FIELD_TOTAL_DAY_SUPPLY = "Tot_Day_Suply"
FIELD_TOTAL_BENES = "Tot_Benes"

# Default target drugs for compounding pharmacy (BHRT + GLP-1)
DEFAULT_DRUGS = [
    "semaglutide",
    "tirzepatide",
    "estradiol",
    "progesterone",
    "testosterone",
    "naltrexone",
]

# Specialty → priority weight for scoring
SPECIALTY_WEIGHTS: dict[str, float] = {
    # Exact match keys are lowercased for comparison
    "ob-gyn": 10.0,
    "obstetrics/gynecology": 10.0,
    "obstetrics & gynecology": 10.0,
    "gynecology": 10.0,
    "obesity medicine": 10.0,
    "integrative medicine": 9.0,
    "functional medicine": 9.0,
    "preventive medicine": 9.0,
    "internal medicine": 8.0,
    "endocrinology": 8.0,
    "family medicine": 7.0,
    "family practice": 7.0,
    "general practice": 6.0,
    "nurse practitioner": 6.0,
    "physician assistant": 6.0,
}

SPECIALTY_WEIGHT_DEFAULT = 5.0


# ---------------------------------------------------------------------------
# CMS API helpers
# ---------------------------------------------------------------------------

def _cms_headers() -> dict:
    """Build request headers, including API key if available."""
    headers = {"Accept": "application/json"}
    if CMS_API_KEY:
        headers["X-API-Key"] = CMS_API_KEY
    return headers


def _fetch_cms_page(drug: str, state: str, min_claims: int, offset: int) -> list[dict]:
    """
    Fetch a single page of CMS Part D data for one drug in one state.

    Args:
        drug: Generic drug name (case-insensitive, will be title-cased for API).
        state: 2-letter state abbreviation (e.g. "TX").
        min_claims: Minimum total claims threshold.
        offset: Pagination offset (0-indexed).

    Returns:
        List of row dicts from CMS API, or empty list on error.
    """
    # CMS API uses OData-style $filter — drug names are title-cased in the dataset
    drug_title = drug.strip().title()

    params = {
        "filter": (
            f"{FIELD_DRUG_GENERIC} eq '{drug_title}'"
            f" and {FIELD_STATE} eq '{state.upper()}'"
            f" and {FIELD_TOTAL_CLAIMS} ge '{min_claims}'"
        ),
        "select": ",".join([
            FIELD_NPI,
            FIELD_LAST_NAME,
            FIELD_FIRST_NAME,
            FIELD_CITY,
            FIELD_STATE,
            FIELD_ZIP,
            FIELD_SPECIALTY,
            FIELD_DRUG_GENERIC,
            FIELD_TOTAL_CLAIMS,
            FIELD_TOTAL_DAY_SUPPLY,
            FIELD_TOTAL_BENES,
        ]),
        "size": CMS_PAGE_SIZE,
        "offset": offset,
    }

    try:
        resp = requests.get(
            CMS_API_BASE,
            params=params,
            headers=_cms_headers(),
            timeout=CMS_TIMEOUT,
        )

        if resp.status_code == 429:
            logger.warning(f"[CMS] Rate limited on {drug_title} offset={offset} — backing off 10s")
            time.sleep(10)
            return []

        if resp.status_code != 200:
            logger.warning(
                f"[CMS] HTTP {resp.status_code} for {drug_title} offset={offset}: {resp.text[:200]}"
            )
            return []

        data = resp.json()

        # CMS API returns a list directly
        if isinstance(data, list):
            return data

        # Some response formats wrap in a dict
        if isinstance(data, dict) and "data" in data:
            return data["data"]

        logger.warning(f"[CMS] Unexpected response shape for {drug_title}: {type(data)}")
        return []

    except requests.exceptions.Timeout:
        logger.warning(f"[CMS] Timeout for {drug_title} offset={offset}")
        return []
    except requests.exceptions.RequestException as e:
        logger.warning(f"[CMS] Request error for {drug_title}: {e}")
        return []
    except (ValueError, json.JSONDecodeError) as e:
        logger.warning(f"[CMS] JSON parse error for {drug_title}: {e}")
        return []


def fetch_drug_all_pages(drug: str, state: str, min_claims: int) -> list[dict]:
    """
    Fetch all paginated results for a single drug in a given state.

    Handles CMS pagination by looping with offset until we get fewer than
    CMS_PAGE_SIZE rows (last page) or hit CMS_MAX_PAGES safety cap.

    Args:
        drug: Generic drug name.
        state: 2-letter state abbreviation.
        min_claims: Minimum total claims threshold.

    Returns:
        Flat list of all row dicts for this drug.
    """
    all_rows: list[dict] = []
    offset = 0

    for page_num in range(CMS_MAX_PAGES):
        page_rows = _fetch_cms_page(drug, state, min_claims, offset)

        if not page_rows:
            break

        all_rows.extend(page_rows)
        logger.info(
            f"[CMS] {drug.title()} | page {page_num + 1} | "
            f"+{len(page_rows)} rows | total={len(all_rows)}"
        )

        if len(page_rows) < CMS_PAGE_SIZE:
            # Last page — no more data
            break

        offset += CMS_PAGE_SIZE
        # Polite rate limiting between pages
        time.sleep(0.25)

    return all_rows


def fetch_all_drugs_concurrent(
    drugs: list[str],
    state: str,
    min_claims: int,
    workers: int = 6,
) -> list[dict]:
    """
    Fetch CMS Part D data for all target drugs concurrently.

    Uses ThreadPoolExecutor with one worker per drug (default 6).
    Each thread independently paginates through its drug's results.

    Args:
        drugs: List of generic drug names to query.
        state: 2-letter state abbreviation.
        min_claims: Minimum total claims threshold.
        workers: Number of concurrent threads (default 6 — one per drug).

    Returns:
        Combined flat list of all rows across all drugs.
    """
    all_rows: list[dict] = []

    logger.info(
        f"[CMS] Fetching {len(drugs)} drugs in {state} "
        f"(min_claims={min_claims}) | {workers} workers"
    )

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(fetch_drug_all_pages, drug, state, min_claims): drug
            for drug in drugs
        }

        for future in as_completed(futures):
            drug = futures[future]
            try:
                rows = future.result()
                all_rows.extend(rows)
                logger.info(f"[CMS] Done: {drug.title()} → {len(rows)} rows")
            except Exception as e:
                logger.error(f"[CMS] Unexpected error for {drug}: {e}")

    logger.info(f"[CMS] Total rows fetched: {len(all_rows)}")
    return all_rows


# ---------------------------------------------------------------------------
# NPI Registry cross-reference
# ---------------------------------------------------------------------------

def lookup_npi(npi: str) -> dict:
    """
    Query the NPI Registry for a single NPI number.

    Returns a dict with: address, city, state, zip, phone, practice_name.
    Returns empty dict on error or not found.

    Args:
        npi: 10-digit NPI number as a string.
    """
    try:
        params = {
            "number": npi,
            "version": "2.1",
            "limit": 1,
        }
        resp = requests.get(NPI_REGISTRY_URL, params=params, timeout=NPI_TIMEOUT)

        if resp.status_code != 200:
            return {}

        data = resp.json()
        results = data.get("results", [])

        if not results:
            return {}

        r = results[0]

        # Basic info
        basic = r.get("basic", {})
        practice_name = basic.get("organization_name", "") or (
            f"{basic.get('first_name', '')} {basic.get('last_name', '')}".strip()
        )

        # Practice address (type "LOCATION" preferred over "MAILING")
        addresses = r.get("addresses", [])
        location_addr = None
        mailing_addr = None

        for addr in addresses:
            if addr.get("address_purpose") == "LOCATION":
                location_addr = addr
            elif addr.get("address_purpose") == "MAILING":
                mailing_addr = addr

        addr = location_addr or mailing_addr or {}

        address_line = addr.get("address_1", "")
        if addr.get("address_2"):
            address_line = f"{address_line}, {addr['address_2']}"

        phone_raw = addr.get("telephone_number", "")
        # Normalize phone format
        phone = phone_raw.replace("-", "").replace("(", "").replace(")", "").replace(" ", "")
        if len(phone) == 10:
            phone = f"({phone[:3]}) {phone[3:6]}-{phone[6:]}"

        return {
            "practice_name": practice_name,
            "address": address_line,
            "city": addr.get("city", ""),
            "state": addr.get("state", ""),
            "zip": addr.get("postal_code", "")[:5],  # Trim to 5-digit
            "phone": phone,
        }

    except requests.exceptions.Timeout:
        return {}
    except (ValueError, KeyError, requests.exceptions.RequestException):
        return {}


def enrich_npis_concurrent(npis: list[str], workers: int = 10) -> dict[str, dict]:
    """
    Batch-enrich a list of NPIs via the NPI Registry API using concurrent lookups.

    Args:
        npis: List of NPI strings to look up.
        workers: Number of concurrent threads (default 10).

    Returns:
        Dict mapping npi → enrichment dict (address, phone, etc.).
    """
    npi_data: dict[str, dict] = {}

    logger.info(f"[NPI] Enriching {len(npis)} unique NPIs | {workers} workers")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(lookup_npi, npi): npi for npi in npis}

        done = 0
        for future in as_completed(futures):
            npi = futures[future]
            try:
                npi_data[npi] = future.result()
            except Exception as e:
                logger.warning(f"[NPI] Error for {npi}: {e}")
                npi_data[npi] = {}

            done += 1
            if done % 50 == 0:
                logger.info(f"[NPI] Progress: {done}/{len(npis)}")

    logger.info(f"[NPI] Enrichment complete: {len(npi_data)} NPIs resolved")
    return npi_data


# ---------------------------------------------------------------------------
# Data processing
# ---------------------------------------------------------------------------

def _safe_int(val) -> int:
    """Safely parse a value to int, returning 0 on failure."""
    try:
        return int(float(str(val).replace(",", "")))
    except (ValueError, TypeError):
        return 0


def _safe_float(val) -> float:
    """Safely parse a value to float, returning 0.0 on failure."""
    try:
        return float(str(val).replace(",", ""))
    except (ValueError, TypeError):
        return 0.0


def _specialty_weight(specialty: str) -> float:
    """
    Map a CMS specialty string to a priority weight.

    Checks lowercase substring matches against SPECIALTY_WEIGHTS dict.
    Returns SPECIALTY_WEIGHT_DEFAULT if no match found.
    """
    s = specialty.lower().strip()
    # Exact match first
    if s in SPECIALTY_WEIGHTS:
        return SPECIALTY_WEIGHTS[s]
    # Substring match
    for key, weight in SPECIALTY_WEIGHTS.items():
        if key in s or s in key:
            return weight
    return SPECIALTY_WEIGHT_DEFAULT


def dedupe_and_score(rows: list[dict]) -> list[dict]:
    """
    Deduplicate CMS rows by NPI, keeping the highest-claim drug as primary.

    When a physician appears for multiple drugs, the highest-claim drug becomes
    primary_drug. All other drugs are listed in secondary_drugs.

    Adds priority_score = (total_claims * 0.5) + specialty_weight.

    Args:
        rows: Raw CMS API rows (list of dicts).

    Returns:
        Deduplicated list of physician dicts, sorted by priority_score descending.
    """
    # Group by NPI
    by_npi: dict[str, list[dict]] = defaultdict(list)

    for row in rows:
        npi = str(row.get(FIELD_NPI, "")).strip()
        if not npi:
            continue
        by_npi[npi].append(row)

    physicians: list[dict] = []

    for npi, npi_rows in by_npi.items():
        # Sort by claim count descending — highest becomes primary
        npi_rows.sort(key=lambda r: _safe_int(r.get(FIELD_TOTAL_CLAIMS, 0)), reverse=True)
        primary = npi_rows[0]

        total_claims = _safe_int(primary.get(FIELD_TOTAL_CLAIMS, 0))
        total_day_supply = _safe_int(primary.get(FIELD_TOTAL_DAY_SUPPLY, 0))
        specialty = str(primary.get(FIELD_SPECIALTY, "")).strip()

        # Accumulate day supply across all drugs for this physician
        total_day_supply_all = sum(_safe_int(r.get(FIELD_TOTAL_DAY_SUPPLY, 0)) for r in npi_rows)

        # Secondary drugs (all except primary)
        secondary_drugs = []
        for r in npi_rows[1:]:
            drug = str(r.get(FIELD_DRUG_GENERIC, "")).strip()
            claims = _safe_int(r.get(FIELD_TOTAL_CLAIMS, 0))
            if drug:
                secondary_drugs.append(f"{drug} ({claims} claims)")

        spec_weight = _specialty_weight(specialty)
        priority_score = round((total_claims * 0.5) + spec_weight, 2)

        physicians.append({
            "npi": npi,
            "last_name": str(primary.get(FIELD_LAST_NAME, "")).strip(),
            "first_name": str(primary.get(FIELD_FIRST_NAME, "")).strip(),
            "specialty": specialty,
            "city": str(primary.get(FIELD_CITY, "")).strip().title(),
            "state": str(primary.get(FIELD_STATE, "")).strip(),
            "zip": str(primary.get(FIELD_ZIP, "")).strip(),
            "primary_drug": str(primary.get(FIELD_DRUG_GENERIC, "")).strip(),
            "total_claims": total_claims,
            "total_day_supply": total_day_supply_all,
            "secondary_drugs": " | ".join(secondary_drugs),
            "specialty_weight": spec_weight,
            "priority_score": priority_score,
            # NPI enrichment fields (filled in later)
            "practice_name": "",
            "address": "",
            "phone": "",
        })

    # Sort by priority score descending
    physicians.sort(key=lambda p: p["priority_score"], reverse=True)
    return physicians


def merge_npi_enrichment(physicians: list[dict], npi_data: dict[str, dict]) -> list[dict]:
    """
    Merge NPI Registry enrichment data into physician records.

    NPI Registry data overrides city/state/zip with practice location
    data (more accurate than CMS billing address).

    Args:
        physicians: List of physician dicts from dedupe_and_score().
        npi_data: Dict mapping npi → enrichment dict from enrich_npis_concurrent().

    Returns:
        Updated list of physician dicts with practice address + phone filled in.
    """
    for phys in physicians:
        npi = phys["npi"]
        enrichment = npi_data.get(npi, {})

        if enrichment:
            phys["practice_name"] = enrichment.get("practice_name", "")
            phys["address"] = enrichment.get("address", "")
            phys["phone"] = enrichment.get("phone", "")

            # Use NPI Registry location data when available (more precise)
            if enrichment.get("city"):
                phys["city"] = enrichment["city"].title()
            if enrichment.get("state"):
                phys["state"] = enrichment["state"]
            if enrichment.get("zip"):
                phys["zip"] = enrichment["zip"]

    return physicians


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

CSV_COLUMNS = [
    "npi",
    "first_name",
    "last_name",
    "specialty",
    "practice_name",
    "address",
    "city",
    "state",
    "zip",
    "phone",
    "primary_drug",
    "total_claims",
    "total_day_supply",
    "secondary_drugs",
    "priority_score",
    "specialty_weight",
]


def save_csv(physicians: list[dict], output_path: Path) -> None:
    """
    Write the physician list to a CSV file.

    Args:
        physicians: List of physician dicts (sorted by priority_score).
        output_path: Absolute path to the output CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(physicians)

    logger.info(f"[OUTPUT] Saved {len(physicians)} physicians → {output_path}")


def print_summary(physicians: list[dict], state: str, drugs: list[str]) -> None:
    """
    Print a summary of the pipeline results to stdout.

    Args:
        physicians: Deduplicated list of physician dicts.
        state: State abbreviation used for the pull.
        drugs: Drug names that were queried.
    """
    total = len(physicians)
    print(f"\n{'='*60}")
    print(f"  CMS Part D Pipeline — {state} Physician Targeting")
    print(f"{'='*60}")
    print(f"  Total unique physicians: {total:,}")
    print(f"  Drugs queried: {', '.join(d.title() for d in drugs)}")

    if not physicians:
        print("  No results found.")
        return

    # Breakdown by specialty
    spec_counts: dict[str, int] = defaultdict(int)
    for p in physicians:
        spec = p["specialty"] or "Unknown"
        spec_counts[spec] += 1

    print(f"\n  Top specialties:")
    for spec, count in sorted(spec_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"    {spec:<40} {count:>5}")

    # Breakdown by primary drug
    drug_counts: dict[str, int] = defaultdict(int)
    for p in physicians:
        drug = p["primary_drug"] or "Unknown"
        drug_counts[drug] += 1

    print(f"\n  Physicians by primary drug (highest-claim):")
    for drug, count in sorted(drug_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"    {drug:<40} {count:>5}")

    # Top 10 physicians by priority score
    print(f"\n  Top 10 by priority score:")
    header = f"    {'Name':<30} {'Specialty':<30} {'Drug':<20} {'Claims':>7} {'Score':>8}"
    print(header)
    print(f"    {'-'*95}")
    for p in physicians[:10]:
        name = f"{p['first_name']} {p['last_name']}".strip() or p["npi"]
        print(
            f"    {name:<30} {p['specialty'][:29]:<30} "
            f"{p['primary_drug'][:19]:<20} {p['total_claims']:>7,} {p['priority_score']:>8.1f}"
        )

    print(f"\n{'='*60}\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "CMS Part D physician targeting pipeline. "
            "Pulls prescribing data to identify physicians for compounding pharmacy campaigns."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full TX pull with default drugs
  python signals/cms_part_d_pipeline.py --state TX

  # Custom drugs and higher minimum claims
  python signals/cms_part_d_pipeline.py --state TX --drugs semaglutide,tirzepatide --min-claims 25

  # Custom output directory
  python signals/cms_part_d_pipeline.py --state TX --output-dir /tmp/cms_output

  # Skip NPI registry enrichment (faster, less data)
  python signals/cms_part_d_pipeline.py --state TX --skip-npi-lookup
        """,
    )

    parser.add_argument(
        "--state",
        default="TX",
        help="2-letter state abbreviation (default: TX)",
    )
    parser.add_argument(
        "--drugs",
        default=",".join(DEFAULT_DRUGS),
        help=(
            "Comma-separated list of generic drug names "
            f"(default: {','.join(DEFAULT_DRUGS)})"
        ),
    )
    parser.add_argument(
        "--min-claims",
        type=int,
        default=10,
        dest="min_claims",
        help="Minimum total claims threshold — filters low-volume prescribers (default: 10)",
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).parent / "output"),
        dest="output_dir",
        help="Directory for output CSV (default: signals/output/)",
    )
    parser.add_argument(
        "--dataset-id",
        default=CMS_DATASET_ID,
        dest="dataset_id",
        help=f"CMS dataset ID (default: {CMS_DATASET_ID} — 2022 Part D by Provider and Drug)",
    )
    parser.add_argument(
        "--cms-workers",
        type=int,
        default=6,
        dest="cms_workers",
        help="Concurrent CMS API workers — one per drug (default: 6)",
    )
    parser.add_argument(
        "--npi-workers",
        type=int,
        default=10,
        dest="npi_workers",
        help="Concurrent NPI registry lookup workers (default: 10)",
    )
    parser.add_argument(
        "--skip-npi-lookup",
        action="store_true",
        dest="skip_npi",
        help="Skip NPI registry enrichment (faster but no phone/practice address)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG logging",
    )

    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(
    state: str = "TX",
    drugs: list[str] | None = None,
    min_claims: int = 10,
    output_dir: str | None = None,
    dataset_id: str = CMS_DATASET_ID,
    cms_workers: int = 6,
    npi_workers: int = 10,
    skip_npi: bool = False,
) -> dict:
    """
    Main pipeline entry point.

    1. Fetches CMS Part D prescribing data for target drugs concurrently.
    2. Deduplicates by NPI, calculates priority scores.
    3. Enriches with NPI Registry practice address + phone (concurrent).
    4. Saves output CSV sorted by priority_score descending.
    5. Prints summary.

    Args:
        state: 2-letter state abbreviation.
        drugs: List of generic drug names to query.
        min_claims: Minimum total claims threshold.
        output_dir: Directory path for output CSV.
        dataset_id: CMS dataset ID (annual — update when new year releases).
        cms_workers: Concurrent CMS API workers.
        npi_workers: Concurrent NPI lookup workers.
        skip_npi: If True, skips NPI registry enrichment step.

    Returns:
        Summary dict with counts and output file path.
    """
    if drugs is None:
        drugs = DEFAULT_DRUGS

    if output_dir is None:
        output_dir = str(Path(__file__).parent / "output")

    # Override dataset ID in URL if custom one provided
    global CMS_API_BASE
    CMS_API_BASE = f"https://data.cms.gov/data-api/v1/dataset/{dataset_id}/data"

    start_time = time.time()
    date_str = datetime.now().strftime("%Y%m%d")
    output_path = Path(output_dir) / f"cms_{state.lower()}_physicians_{date_str}.csv"

    logger.info(
        f"[PIPELINE] Starting CMS Part D pipeline | "
        f"state={state} | drugs={drugs} | min_claims={min_claims}"
    )

    # Step 1: Fetch CMS data for all drugs concurrently
    raw_rows = fetch_all_drugs_concurrent(drugs, state, min_claims, workers=cms_workers)

    if not raw_rows:
        logger.warning("[PIPELINE] No CMS data returned — check dataset ID and drug names")
        print_summary([], state, drugs)
        return {
            "total_physicians": 0,
            "raw_rows": 0,
            "output_path": None,
            "elapsed_seconds": round(time.time() - start_time, 1),
        }

    # Step 2: Deduplicate by NPI and compute priority scores
    logger.info(f"[PIPELINE] Deduplicating {len(raw_rows)} raw rows by NPI...")
    physicians = dedupe_and_score(raw_rows)
    logger.info(f"[PIPELINE] {len(physicians)} unique physicians after dedup")

    # Step 3: NPI Registry enrichment (concurrent)
    if not skip_npi:
        unique_npis = [p["npi"] for p in physicians]
        npi_data = enrich_npis_concurrent(unique_npis, workers=npi_workers)
        physicians = merge_npi_enrichment(physicians, npi_data)
    else:
        logger.info("[PIPELINE] Skipping NPI registry enrichment (--skip-npi-lookup)")

    # Step 4: Save CSV
    save_csv(physicians, output_path)

    # Step 5: Print summary
    print_summary(physicians, state, drugs)

    elapsed = round(time.time() - start_time, 1)
    logger.info(f"[PIPELINE] Complete in {elapsed}s | output: {output_path}")

    return {
        "total_physicians": len(physicians),
        "raw_rows": len(raw_rows),
        "output_path": str(output_path),
        "elapsed_seconds": elapsed,
    }


if __name__ == "__main__":
    args = parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    drugs_list = [d.strip() for d in args.drugs.split(",") if d.strip()]

    result = run(
        state=args.state,
        drugs=drugs_list,
        min_claims=args.min_claims,
        output_dir=args.output_dir,
        dataset_id=args.dataset_id,
        cms_workers=args.cms_workers,
        npi_workers=args.npi_workers,
        skip_npi=args.skip_npi,
    )

    print(json.dumps(result, indent=2))
    sys.exit(0)
