#!/usr/bin/env python3
"""
populate_projects.py — the missing bridge: Supabase epc_company_leads → Airtable projects.

Both lead engines (signals/epc_lead_engine.py and signals/h1b_signal_engine.py)
write company leads to Supabase `epc_company_leads`, but nothing moved them into
the Airtable `projects` table where enrichment + Smartlead enrollment pick up.
This script closes that gap.

Flow:
  Supabase epc_company_leads  ──(this script)──▶  Airtable projects
                                                    │
                                  lead_priority_scoring.py refines priority
                                                    ▼
                                  enrichment/pipeline.py → Smartlead

Mapping (per lead → storage.airtable.AirtableClient.upsert_project):
  company_name              → owner_company + project_name   (dedup key)
  sector slug               → canonical sector name (scope_summary)
  raw_data.intent_score     → confidence_score (heat_score)
  raw_data.intent_tier      → priority + icp_fit  (High→Strong, etc.)
  domain (if real)          → source_url
  raw_data {roles,years,…}  → analyst_notes
  state                     → stored in positioning_notes JSON by upsert_project

upsert_project dedupes on owner_company and PATCHes existing records (preserving
analyst-set priority/stage), so this script is safe to re-run.

Usage:
  python populate_projects.py                          # all sources, all sectors
  python populate_projects.py --source h1b_lca         # only H-1B intent leads
  python populate_projects.py --min-score 60           # only hotter leads
  python populate_projects.py --sector power           # one sector
  python populate_projects.py --dry-run                # print, no Airtable writes
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("populate_projects")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_TABLE = "epc_company_leads"

# Lead-engine sector slugs → canonical sector names (match Smartlead/CLAUDE.md).
SECTOR_NAMES = {
    "power": "Power & Grid Infrastructure",
    "dc": "Data Center & AI Infrastructure",
    "water": "Water & Wastewater Infrastructure",
    "industrial": "Industrial & Manufacturing Facilities",
    "defense": "Defense & Federal Infrastructure",
    "general_epc": "General EPC",
}

# intent_tier → (priority, icp_fit) — both lowercased for upsert_project's maps.
TIER_MAP = {
    "High": ("high", "high"),       # → priority High, icp_fit Strong
    "Medium": ("medium", "medium"), # → priority Medium, icp_fit Moderate
    "Low": ("low", "low"),          # → priority Low, icp_fit Weak
}


def _fetch_leads(source: str, sector: str) -> list[dict]:
    """Page through epc_company_leads with optional server-side filters."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Supabase not configured (SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY)")
        return []
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    base = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}?select=*"
    if source != "all":
        base += f"&source=eq.{source}"
    if sector:
        base += f"&sector=eq.{sector}"

    leads, offset, page = [], 0, 1000
    while True:
        r = requests.get(f"{base}&limit={page}&offset={offset}",
                         headers=headers, timeout=30)
        if r.status_code != 200:
            logger.error("Supabase fetch failed %d: %s", r.status_code, r.text[:200])
            break
        batch = r.json()
        leads.extend(batch)
        if len(batch) < page:
            break
        offset += page
    logger.info("Fetched %d leads (source=%s, sector=%s)", len(leads), source, sector or "all")
    return leads


def _parse_raw(lead: dict) -> dict:
    raw = lead.get("raw_data")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (ValueError, TypeError):
            raw = {}
    return raw or {}


def _build_notes(lead: dict, raw: dict) -> str:
    parts = [f"Source: {lead.get('source', '')}"]
    if raw.get("signal"):
        parts.append(f"Signal: {raw['signal']}")
    if raw.get("h1b_volume") is not None:
        parts.append(f"H1B volume: {raw['h1b_volume']}, velocity: "
                     f"{raw.get('h1b_velocity_years', '?')}yr")
    if raw.get("roles"):
        parts.append(f"Roles: {', '.join(raw['roles'])}")
    if raw.get("years"):
        parts.append(f"Years: {', '.join(map(str, raw['years']))}")
    return " | ".join(parts)


def run(source: str = "all", sector_filter: str = "", min_score: float = 0,
        limit: int = 0, dry_run: bool = False) -> dict:
    leads = _fetch_leads(source, sector_filter)

    # Client-side score filter (intent_score lives in raw_data JSON).
    scored = []
    for lead in leads:
        raw = _parse_raw(lead)
        score = float(raw.get("intent_score", 0) or 0)
        if score >= min_score:
            scored.append((lead, raw, score))
    scored.sort(key=lambda x: x[2], reverse=True)
    if limit:
        scored = scored[:limit]
    logger.info("%d leads pass min_score=%s", len(scored), min_score)

    if dry_run:
        for lead, raw, score in scored[:40]:
            sector_name = SECTOR_NAMES.get(lead.get("sector", ""), lead.get("sector", ""))
            tier = raw.get("intent_tier", "—")
            logger.info("  [%-6s %3.0f] %-45s %s",
                        tier, score, lead.get("company_name", "?")[:45], sector_name)
        return {"total": len(scored), "upserted": 0, "dry_run": True}

    from storage.airtable import get_client
    at = get_client()

    upserted = 0
    for lead, raw, score in scored:
        name = (lead.get("company_name") or "").strip()
        if not name:
            continue
        priority, icp_fit = TIER_MAP.get(raw.get("intent_tier", ""), ("medium", "medium"))
        domain = (lead.get("domain") or "").strip()
        website = domain if "." in domain else ""  # skip name-slug placeholders
        sector_name = SECTOR_NAMES.get(lead.get("sector", ""), lead.get("sector", ""))

        rec_id = at.upsert_project(
            company_name=name,
            sector=sector_name,
            heat_score=score,
            priority=priority,
            icp_fit=icp_fit,
            notes=_build_notes(lead, raw),
            website=website,
            state=lead.get("state", "") or "",
        )
        if rec_id:
            upserted += 1
    logger.info("Upserted %d/%d leads to Airtable projects", upserted, len(scored))
    return {"total": len(scored), "upserted": upserted, "dry_run": False}


def main():
    p = argparse.ArgumentParser(
        description="Bridge: Supabase epc_company_leads → Airtable projects")
    p.add_argument("--source", default="all",
                   help="lead source filter, e.g. h1b_lca (default: all)")
    p.add_argument("--sector", default="", help="sector slug filter, e.g. power")
    p.add_argument("--min-score", type=float, default=0, help="min intent_score")
    p.add_argument("--limit", type=int, default=0, help="cap leads processed")
    p.add_argument("--dry-run", action="store_true", help="print, no Airtable writes")
    args = p.parse_args()

    result = run(source=args.source, sector_filter=args.sector,
                 min_score=args.min_score, limit=args.limit, dry_run=args.dry_run)
    logger.info("DONE: %s", json.dumps(result))


if __name__ == "__main__":
    main()
