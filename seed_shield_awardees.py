"""
seed_shield_awardees.py
One-time seed: parse MDA SHIELD IDIQ awardees → Apollo enrichment → Airtable projects.

SHIELD = Missile Defense Agency Multiple Award IDIQ (HQ085925RE001)
Dec 18, 2025 award list: 1,079 companies with active DoD contracts.

Filters for EPC-adjacent companies (engineering, construction, systems, technical,
solutions, services, infrastructure, facility) before Apollo lookup.

Usage:
    python3 seed_shield_awardees.py --dry-run        # print matches only
    python3 seed_shield_awardees.py --limit 50       # seed first 50 to Airtable
    python3 seed_shield_awardees.py                  # seed all EPC-adjacent
"""

import argparse
import json
import logging
import re
import sys
import time
from pathlib import Path

import pypdf
import requests

sys.path.insert(0, str(Path(__file__).parent))
from config import APOLLO_API_KEY, AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLES

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────

SHIELD_PDF = Path(__file__).parent.parent / "Downloads" / "Missile+Defense+Agency+(MDA)+SHIELD+Multiple+Award+IDIQ+Contract" / "SHIELD Awardees - 18 Dec 25.pdf.pdf"
SHIELD_PDF_ALT = Path.home() / "Downloads" / "Missile+Defense+Agency+(MDA)+SHIELD+Multiple+Award+IDIQ+Contract" / "SHIELD Awardees - 18 Dec 25.pdf.pdf"

SECTOR = "Defense"
CONTRACT_VEHICLE = "MDA SHIELD IDIQ HQ085925RE001"

# Companies that match these keywords are EPC-adjacent
EPC_ADJACENT_KW = [
    "engineering", "construction", "systems", "technical", "technology", "technologies",
    "solutions", "services", "integrated", "integration", "infrastructure", "facility",
    "electrical", "mechanical", "environmental", "management", "logistics", "support",
    "mission", "operations", "sciences", "research", "analytics", "consulting",
]

# Skip obvious pure-software/non-facility companies
SKIP_KW = [
    "software", "cyber", "data science", "artificial intelligence", "cloud", "saas",
    "staffing", "recruiting", "training", "education", "media", "communications media",
]


# ── PDF Parsing ────────────────────────────────────────────────────────────────

def parse_shield_pdf(pdf_path: Path) -> list[dict]:
    """Extract all awardees from the SHIELD PDF."""
    reader = pypdf.PdfReader(str(pdf_path))
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"

    matches = re.findall(
        r"^\d+\s+([A-Z0-9]{5})\s+(.+?)\s+(HQ\d+\w*)\s*$",
        text,
        re.MULTILINE,
    )
    awardees = [
        {"cage": m[0], "name": m[1].strip(), "contract": m[2]}
        for m in matches
    ]
    logger.info(f"[SHIELD] Parsed {len(awardees)} awardees from PDF")
    return awardees


def filter_epc_adjacent(awardees: list[dict]) -> list[dict]:
    """Filter to EPC-adjacent companies only."""
    filtered = []
    for a in awardees:
        name_lower = a["name"].lower()
        if any(kw in name_lower for kw in EPC_ADJACENT_KW):
            if not any(sk in name_lower for sk in SKIP_KW):
                filtered.append(a)
    logger.info(f"[SHIELD] {len(filtered)} EPC-adjacent after filter")
    return filtered


# ── Apollo Enrichment ──────────────────────────────────────────────────────────

def apollo_search_org(company_name: str):
    """Search Apollo for a company by name. Returns first match or None."""
    if not APOLLO_API_KEY:
        return None

    try:
        resp = requests.post(
            "https://api.apollo.io/api/v1/organizations/search",
            headers={"X-Api-Key": APOLLO_API_KEY, "Content-Type": "application/json"},
            json={
                "q_organization_name": company_name,
                "per_page": 1,
                "page": 1,
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        orgs = data.get("organizations", [])
        return orgs[0] if orgs else None
    except Exception as e:
        logger.warning(f"[Apollo] Search failed for '{company_name}': {e}")
        return None


# ── Airtable ───────────────────────────────────────────────────────────────────

def airtable_project_exists(company_name: str) -> bool:
    """Check if a project record already exists for this company."""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLES['projects']}"
    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
    params = {
        "filterByFormula": f"{{owner_company}}='{company_name.replace(chr(39), '')}'"
    }
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        return len(resp.json().get("records", [])) > 0
    except Exception:
        return False


def airtable_create_project(company: dict, org=None) :
    """Create an Airtable project record for a SHIELD awardee."""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLES['projects']}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json",
    }

    # Build fields from Apollo data if available
    fields = {
        "owner_company": company["name"],
        "sector": SECTOR,
        "stage": "Identified",
        "priority": "Medium",
        "icp_fit": "Unknown",
        "notes": (
            f"Source: MDA SHIELD IDIQ ({CONTRACT_VEHICLE})\n"
            f"CAGE: {company['cage']}\n"
            f"Contract: {company['contract']}\n"
            "Active DoD contract as of Dec 2025. EPC-adjacent — confirm revenue range before outreach."
        ),
        "signal_type": "government_contract",
        "confidence_score": 60,  # Confirmed DoD contract = meaningful signal
    }

    if org:
        fields["owner_company"] = org.get("name", company["name"])
        if org.get("estimated_num_employees"):
            fields["notes"] += f"\nEstimated employees: {org['estimated_num_employees']}"
        if org.get("annual_revenue_printed"):
            fields["notes"] += f"\nRevenue: {org['annual_revenue_printed']}"
        if org.get("primary_domain"):
            fields["notes"] += f"\nWebsite: {org['primary_domain']}"
        if org.get("city") and org.get("state"):
            fields["notes"] += f"\nLocation: {org['city']}, {org['state']}"

    try:
        resp = requests.post(
            url,
            headers=headers,
            json={"fields": fields},
            timeout=15,
        )
        resp.raise_for_status()
        record_id = resp.json().get("id")
        logger.info(f"[Airtable] Created project: {company['name']} → {record_id}")
        return record_id
    except Exception as e:
        logger.error(f"[Airtable] Failed to create project for {company['name']}: {e}")
        return None


# ── Main ───────────────────────────────────────────────────────────────────────

def run(dry_run: bool = False, limit=None, skip_apollo: bool = False):
    # Find PDF
    pdf_path = SHIELD_PDF if SHIELD_PDF.exists() else SHIELD_PDF_ALT
    if not pdf_path.exists():
        logger.error(f"SHIELD PDF not found at {pdf_path}")
        sys.exit(1)

    awardees = parse_shield_pdf(pdf_path)
    filtered = filter_epc_adjacent(awardees)

    if limit:
        filtered = filtered[:limit]

    if dry_run:
        print(f"\nDRY RUN — {len(filtered)} EPC-adjacent SHIELD awardees:\n")
        for a in filtered:
            print(f"  {a['cage']} | {a['name']}")
        return

    results = {"created": 0, "skipped": 0, "errors": 0}

    for i, company in enumerate(filtered):
        logger.info(f"[{i+1}/{len(filtered)}] Processing: {company['name']}")

        # Check for existing project
        if airtable_project_exists(company["name"]):
            logger.info(f"  → Already exists, skipping")
            results["skipped"] += 1
            continue

        # Apollo enrichment
        org = None
        if not skip_apollo and APOLLO_API_KEY:
            org = apollo_search_org(company["name"])
            time.sleep(0.3)  # Rate limit

        # Create Airtable project
        record_id = airtable_create_project(company, org)
        if record_id:
            results["created"] += 1
        else:
            results["errors"] += 1

        # Rate limit
        time.sleep(0.2)

    logger.info(f"\n[SHIELD Seed] Done: {results}")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed SHIELD IDIQ awardees into ECAS")
    parser.add_argument("--dry-run", action="store_true", help="Print matches without writing")
    parser.add_argument("--limit", type=int, default=None, help="Max companies to process")
    parser.add_argument("--skip-apollo", action="store_true", help="Skip Apollo enrichment")
    args = parser.parse_args()

    run(dry_run=args.dry_run, limit=args.limit, skip_apollo=args.skip_apollo)
