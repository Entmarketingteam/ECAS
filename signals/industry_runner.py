"""Industry Factory orchestrator.

Single entrypoint that takes an industry slug, loads its YAML config, runs
discovery -> scraping -> tech-stack enrichment -> project population -> existing
Apollo/FindyMail/Smartlead pipeline -> post-run watchdogs.

Invocation:
    python -m signals.industry_runner <slug> [--live]
    POST /admin/run/industry/<slug>
"""
from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_DRYRUN_DB = Path(__file__).parent.parent / "database" / "industry_dryrun_log.db"


def _preflight() -> dict:
    """Thin wrapper over pre_flight_check for easy mocking in tests."""
    from enrichment.health import pre_flight_check
    return pre_flight_check()


def _has_dryrun_on_record(slug: str, db: Path = _DRYRUN_DB) -> bool:
    if not db.exists():
        return False
    with sqlite3.connect(db) as conn:
        try:
            row = conn.execute(
                "SELECT 1 FROM dryrun_log WHERE slug = ? AND status = 'ok' LIMIT 1",
                (slug,),
            ).fetchone()
        except sqlite3.OperationalError:
            return False
    return row is not None


def _log_dryrun(slug: str, status: str, db: Path = _DRYRUN_DB) -> None:
    db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dryrun_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL,
                status TEXT NOT NULL,
                ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            "INSERT INTO dryrun_log (slug, status) VALUES (?, ?)",
            (slug, status),
        )


def _discover_and_scrape(industry):
    """Run directory discovery + scraping for an industry."""
    from discovery.directory_finder import (
        DirectoryCandidate,
        classify_url,
        discover_directories,
    )
    from discovery.universal_scraper import scrape_candidates

    seeds: list[DirectoryCandidate] = [
        DirectoryCandidate(url=u, scraper_type=classify_url(u), confidence=1.0, source="seed")
        for u in industry.directory_seeds
    ]

    auto: list[DirectoryCandidate] = []
    if industry.directory_auto_discovery:
        auto = discover_directories(
            industry_display_name=industry.display_name,
            keywords=industry.apollo_keywords,
        )

    candidates = seeds + auto
    if not candidates:
        raise RuntimeError(f"No directory candidates for {industry.slug}")

    return scrape_candidates(candidates)


def _populate_projects(scraped_companies, industry):
    """Upsert scraped companies into Airtable projects table."""
    from storage.airtable import get_client

    at = get_client()
    created = 0
    existing = 0
    for company in scraped_companies:
        name = (company.name or "").strip()
        if not name:
            continue
        name_escaped = name.replace("'", "''")
        hits = at._get(
            "projects",
            {
                "filterByFormula": f"{{owner_company}}='{name_escaped}'",
                "maxRecords": 1,
            },
        )
        if hits:
            existing += 1
            continue
        at.upsert_project({
            "owner_company": name,
            "stage": "Identified",
            "confidence_score": industry.min_heat,
            "positioning_notes": '{"sector": "' + industry.display_name + '"}',
            "priority": "Medium",
        })
        created += 1
    return {"created": created, "existing": existing}


def _run_downstream_pipeline(industry):
    """Hand off to the existing Apollo/FindyMail/Smartlead pipeline."""
    from enrichment.pipeline import run_pipeline
    return run_pipeline(
        min_heat=industry.min_heat,
        company_filter=None,
        dry_run=False,
    )


def run_industry(
    slug: str,
    industries_dir: Optional[Path] = None,
    dry_run: bool = True,
) -> dict:
    """Run the full Industry Factory pipeline for a given industry."""
    from industries.loader import load_industry

    industry = load_industry(slug, directory=industries_dir)
    logger.info("[Factory] Running %s (dry_run=%s)", slug, dry_run)

    pf = _preflight()
    if pf["status"] == "blocked":
        return {
            "status": "blocked",
            "reason": f"Pre-flight failed: {pf['failures']}",
            "industry": slug,
        }

    if not dry_run and not _has_dryrun_on_record(slug):
        raise RuntimeError(
            f"Dry-run required before live run for {slug!r}. "
            f"Execute with dry_run=True first."
        )

    scraped = _discover_and_scrape(industry)
    logger.info("[Factory] %s: %d companies scraped", slug, len(scraped))

    if len(scraped) > industry.budget_cap_per_run:
        scraped = scraped[: industry.budget_cap_per_run]

    if dry_run:
        _log_dryrun(slug, "ok")
        return {
            "status": "dry_run_ok",
            "industry": slug,
            "scraped_count": len(scraped),
            "preview": [c.name for c in scraped[:10]],
        }

    pop_result = _populate_projects(scraped, industry)
    pipeline_result = _run_downstream_pipeline(industry)

    return {
        "status": "complete",
        "industry": slug,
        "scraped_count": len(scraped),
        "projects_created": pop_result["created"],
        "projects_existing": pop_result["existing"],
        "pipeline": pipeline_result,
        "ran_at": datetime.utcnow().isoformat(),
    }


def _main():
    import argparse
    import json
    parser = argparse.ArgumentParser()
    parser.add_argument("slug")
    parser.add_argument("--live", action="store_true", help="Live run (default: dry-run)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    result = run_industry(args.slug, dry_run=not args.live)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    _main()
