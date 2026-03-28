"""
run_apollo_enrichment.py
Standalone script: Apollo contact enrichment for all ECAS projects with no contacts.
Uses existing helpers from storage/airtable.py and enrichment/clay_enricher.py.
Processes top 40 projects (by confidence_score descending) that still have NO contacts.
Any project that was previously enriched will now have contacts and will be skipped
automatically — so this script is safe to re-run as "batch 2, 3, …" without manual offset.
"""

import logging
import subprocess
import sys
from pathlib import Path

# ── Pull secrets from Doppler ────────────────────────────────────────────────

def get_doppler_secret(key: str, project: str = "ecas", config: str = "dev") -> str:
    result = subprocess.run(
        ["doppler", "secrets", "get", key, "--project", project, "--config", config, "--plain"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Doppler failed for {key}: {result.stderr.strip()}")
    return result.stdout.strip()

import os
os.environ["APOLLO_API_KEY"] = get_doppler_secret("APOLLO_API_KEY")
os.environ["AIRTABLE_API_KEY"] = get_doppler_secret("AIRTABLE_API_KEY")
os.environ["AIRTABLE_BASE_ID"] = "appoi8SzEJY8in57x"

# ── Add ECAS root to path ────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

import requests
from storage.airtable import get_client
from enrichment.clay_enricher import enrich_and_store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

MAX_PROJECTS = 50

# Target titles for Apollo people search (batch 2 spec)
TARGET_TITLES = [
    "VP Operations",
    "VP Business Development",
    "Director of Operations",
    "President",
    "CEO",
    "Owner",
    "Principal",
    "Chief Operating Officer",
    "Project Executive",
]

def main():
    at = get_client()
    logger.info("Fetching all projects from Airtable...")
    all_projects = at.get_projects()
    logger.info(f"Total projects fetched: {len(all_projects)}")

    # Filter to projects with no contacts linked
    no_contacts = []
    for rec in all_projects:
        fields = rec.get("fields", {})
        contacts = fields.get("contacts", [])
        if not contacts:
            no_contacts.append(rec)

    # Sort by confidence_score descending
    no_contacts.sort(
        key=lambda r: float(r["fields"].get("confidence_score") or 0),
        reverse=True
    )

    logger.info(f"Projects without contacts: {len(no_contacts)}")
    to_process = no_contacts[:MAX_PROJECTS]
    logger.info(f"Processing top {len(to_process)} by confidence score...")

    total_found = 0
    total_stored = 0
    projects_with_contacts = 0
    skipped = 0

    for i, rec in enumerate(to_process, 1):
        fields = rec["fields"]
        company = fields.get("owner_company") or fields.get("project_name", "")
        record_id = rec["id"]
        score = float(fields.get("confidence_score") or 0)

        if not company:
            logger.warning(f"[{i}/{len(to_process)}] Skipping record {record_id} — no company name")
            skipped += 1
            continue

        logger.info(f"[{i}/{len(to_process)}] Enriching: {company} (score={score:.1f})")
        try:
            result = enrich_and_store(company, project_record_id=record_id, titles=TARGET_TITLES)
            found = result["contacts_found"]
            stored = result["contacts_stored"]
            total_found += found
            total_stored += stored
            if stored > 0:
                projects_with_contacts += 1
            logger.info(f"  → {found} found, {stored} stored")
        except Exception as e:
            logger.error(f"  → Error enriching {company}: {e}")
            skipped += 1

    print("\n" + "=" * 60)
    print("APOLLO ENRICHMENT COMPLETE")
    print("=" * 60)
    print(f"Projects processed:          {len(to_process) - skipped}")
    print(f"Projects with new contacts:  {projects_with_contacts}")
    print(f"Total contacts found:        {total_found}")
    print(f"Total contacts stored:       {total_stored}")
    print(f"Skipped (no name / error):   {skipped}")
    print("=" * 60)

if __name__ == "__main__":
    main()
