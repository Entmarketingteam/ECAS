"""
signals/building_permits.py
Large-project building-permit signal → EPC contractor leads.

Pulls recently-issued, high-valuation COMMERCIAL/INDUSTRIAL building permits from
municipal Socrata open-data portals, keeps only those whose work description maps
to an ECAS sector (Power/Data Center/Water/Industrial), and extracts the
CONTRACTOR named on the permit — a mid-tier EPC actively executing infra work =
ContractMotion's ICP, captured the moment money starts flowing on a project.

Output mirrors epc_lead_engine.py:
  - SQLite dedup in `database/tracker.db` (table building_permits_seen, by permit uid)
  - Supabase upsert into `epc_company_leads` (on_conflict=domain,source)
  - CSV to signals/output/permit_leads_{date}.csv
The daily `h1b_pipeline` scheduler job already bridges ALL epc_company_leads →
Airtable projects → enrichment → sector-routed Smartlead, so permit leads flow
through the live pipeline with no extra wiring.

ADDING A SOURCE: every municipal permit dataset uses different field names, so a
new entry in SOURCES MUST be verified against the live endpoint before enabling
(confirm contractor-name field, valuation field, and work-description field exist
and populate). Do not add unverified datasets — empty/placeholder sources are the
classic failure mode here.

CLI:
  doppler run --project ecas --config dev -- python3 signals/building_permits.py --dry-run
  doppler run --project ecas --config dev -- python3 signals/building_permits.py --metro chicago --days 14 --min-cost 1000000
"""

import argparse
import csv
import json
import logging
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DB_PATH

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("building_permits")

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_TABLE = "epc_company_leads"
SOURCE_TAG = "building_permits"

# Optional Socrata app token (raises rate limits; not required for daily volume)
SOCRATA_APP_TOKEN = os.environ.get("SOCRATA_APP_TOKEN", "")

# Defaults — overridable via CLI
DEFAULT_MIN_COST = 1_000_000   # $1M+ permits = mid-tier EPC scale
DEFAULT_LOOKBACK_DAYS = 30
PAGE_SIZE = 1000
MAX_RECORDS_PER_SOURCE = 5000  # bound cost/runtime
RATE_LIMIT_SECONDS = 0.4

# ── ECAS sector classification ──────────────────────────────────────────────
# Canonical sector names MUST match config.SECTOR_CAMPAIGN_MAP / Smartlead routing.
# Most-specific sectors first; first keyword hit wins.
# HIGH-PRECISION ONLY: generic terms (generator, solar, transformer, factory,
# warehouse, manufacturing, industrial) were removed after live testing showed
# they fire on incidental building equipment and brand names ("Burlington Coat
# Factory", rooftop solar, backup generators) — mis-routing campaigns. Keep only
# terms that unambiguously denote a sector facility/project.
SECTOR_KEYWORDS = [
    ("Data Center & AI Infrastructure", [
        "data center", "datacenter", "data centre", "colocation",
        "hyperscale", "server farm",
    ]),
    ("Power & Grid Infrastructure", [
        "substation", "switchgear", "transmission line", "power plant",
        "battery storage", "energy storage system", "microgrid", "solar farm",
        "solar array", "utility-scale",
    ]),
    ("Water & Wastewater Infrastructure", [
        "water treatment plant", "wastewater", "waste water treatment",
        "sewage treatment", "lift station", "pump station",
    ]),
    ("Industrial & Manufacturing Facilities", [
        "semiconductor", "chip fab", "fabrication plant", "manufacturing plant",
        "distribution center", "distribution centre", "fulfillment center",
        "cold storage facility", "refinery", "processing plant",
    ]),
]


def classify_sector(text: str) -> str | None:
    """Map a permit work description to an ECAS sector, or None if not infra."""
    t = (text or "").lower()
    for sector, kws in SECTOR_KEYWORDS:
        for kw in kws:
            if kw in t:
                return sector
    return None


# ── Source registry ─────────────────────────────────────────────────────────
# Each adapter parses one verified Socrata dataset into normalized permit dicts:
#   {permit_id, company_name, valuation, description, city, state, url, issue_date}
# VERIFIED 2026-05-25 against live endpoints (field names confirmed present).

def _chicago_adapter(min_cost: int, cutoff: str) -> list[dict]:
    """data.cityofchicago.org — Building Permits (ydr8-5enu).

    Has reported_cost (valuation), work_description, and up to 4 typed contacts.
    We take the first CONTRACTOR-type contact (electrical / general / etc.) as the
    lead, skipping owner/architect/expeditor.
    """
    base = "https://data.cityofchicago.org/resource/ydr8-5enu.json"
    where = f"reported_cost > {min_cost} AND issue_date > '{cutoff}'"
    out: list[dict] = []
    offset = 0
    while offset < MAX_RECORDS_PER_SOURCE:
        rows = _socrata_get(base, where, offset)
        if not rows:
            break
        for r in rows:
            company = _chicago_contractor(r)
            if not company:
                continue
            out.append({
                "permit_id": r.get("permit_", ""),
                "company_name": company,
                "valuation": _to_int(r.get("reported_cost")),
                "description": r.get("work_description", "") or "",
                "permit_type": r.get("permit_type", "") or "",
                "city": (r.get("contact_1_city") or "Chicago").title(),
                "state": (r.get("contact_1_state") or "IL").upper()[:2],
                "issue_date": (r.get("issue_date", "") or "")[:10],
                "url": f"https://data.cityofchicago.org/resource/ydr8-5enu/{r.get('id', '')}"
                       if r.get("id") else base,
            })
        if len(rows) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return out


CONTRACTOR_TYPE_RE = re.compile(r"CONTRACTOR", re.I)
OWNER_CONTRACTOR_RE = re.compile(r"OWNER", re.I)  # exclude "OWNER AS GENERAL CONTRACTOR"


def _chicago_contractor(r: dict) -> str | None:
    """Return the first real contractor company across Chicago's 4 contact slots."""
    for i in (1, 2, 3, 4):
        ctype = r.get(f"contact_{i}_type", "") or ""
        cname = (r.get(f"contact_{i}_name", "") or "").strip()
        if not cname:
            continue
        if CONTRACTOR_TYPE_RE.search(ctype) and not OWNER_CONTRACTOR_RE.search(ctype):
            return cname
    return None


def _charlotte_adapter(min_cost: int, cutoff: str) -> list[dict]:
    """meckgis.mecklenburgcountync.gov — Mecklenburg County (Charlotte) Building
    Permits (ArcGIS FeatureServer). Rich: bldgcost (valuation), projname, projdesc,
    workdesc, usdcdesc, ownname.

    NOTE: Charlotte exposes the OWNER/developer (`ownname`/`projname`), NOT the EPC
    contractor. These are owner-side project signals (intro/ABM targets), a weaker
    fit than Chicago's contractor contacts for ContractMotion's sell-to-EPC ICP.
    """
    base = ("https://meckgis.mecklenburgcountync.gov/server/rest/services/"
            "BuildingPermits/FeatureServer/0/query")
    cutoff_date = cutoff[:10]  # ArcGIS DATE 'YYYY-MM-DD'
    where = f"bldgcost > {min_cost} AND issuedate > DATE '{cutoff_date}'"
    out: list[dict] = []
    offset = 0
    while offset < MAX_RECORDS_PER_SOURCE:
        rows = _arcgis_get(base, where, offset)
        if not rows:
            break
        for r in rows:
            company = (r.get("projname") or r.get("ownname") or "").strip()
            if not company:
                continue
            out.append({
                "permit_id": r.get("permitnum") or r.get("projnum", ""),
                "company_name": company,
                "valuation": _to_int(r.get("bldgcost")),
                "description": " ".join(filter(None, [
                    r.get("usdcdesc", ""), r.get("workdesc", ""), r.get("projdesc", ""),
                ])),
                "permit_type": r.get("permittype", "") or "",
                "city": (r.get("owncity") or "Charlotte").title(),
                "state": (r.get("ownstate") or "NC").upper()[:2],
                "issue_date": _epoch_ms_to_date(r.get("issuedate")),
                "url": "https://www.mecknc.gov/LUESA/CodeEnforcement",
            })
        if len(rows) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return out


SOURCES = {
    "chicago": _chicago_adapter,      # Socrata — has CONTRACTOR contacts (best fit)
    "charlotte": _charlotte_adapter,  # ArcGIS — owner-side only (weaker fit)
    # NOT viable as of 2026-05-25:
    #   "nashville": migrated off Socrata → hub.arcgis.com/legacy; permits behind
    #                Accela Citizen Access portal, no clean bulk API.
    #   "austin": Socrata 3syk-w9eu carries no contractor name or valuation.
    #   "nyc": ipu4-2q9a has permittee_s_business_name but no valuation (flaky pulls).
}


# ── Socrata HTTP ─────────────────────────────────────────────────────────────

def _socrata_get(base: str, where: str, offset: int) -> list[dict]:
    params = {"$where": where, "$limit": PAGE_SIZE, "$offset": offset,
              "$order": "issue_date DESC"}
    headers = {"X-App-Token": SOCRATA_APP_TOKEN} if SOCRATA_APP_TOKEN else {}
    try:
        time.sleep(RATE_LIMIT_SECONDS)
        resp = requests.get(base, params=params, headers=headers, timeout=45)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning("[Socrata] GET failed (offset=%d): %s", offset, e)
        return []


def _arcgis_get(base: str, where: str, offset: int) -> list[dict]:
    params = {
        "where": where, "outFields": "*", "orderByFields": "bldgcost DESC",
        "resultRecordCount": PAGE_SIZE, "resultOffset": offset, "f": "json",
    }
    try:
        time.sleep(RATE_LIMIT_SECONDS)
        resp = requests.get(base, params=params, timeout=45)
        resp.raise_for_status()
        data = resp.json()
        return [f.get("attributes", {}) for f in data.get("features", [])]
    except Exception as e:
        logger.warning("[ArcGIS] GET failed (offset=%d): %s", offset, e)
        return []


def _epoch_ms_to_date(v) -> str:
    try:
        return datetime.utcfromtimestamp(int(v) / 1000).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return ""


def _to_int(v) -> int:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return 0


def _slug(name: str) -> str:
    """Dotless company slug → unique, collision-free Supabase key per contractor.
    The bridge (populate_projects.py) treats dotless domains as 'no website'."""
    return re.sub(r"[^a-z0-9]", "", name.lower())[:60]


# ── Dedup (SQLite) ───────────────────────────────────────────────────────────

def _ensure_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS building_permits_seen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            permit_uid TEXT UNIQUE,
            scraped_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def _is_new(conn: sqlite3.Connection, uid: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM building_permits_seen WHERE permit_uid=?", (uid,)
    ).fetchone() is None


def _mark_seen(conn: sqlite3.Connection, uid: str) -> None:
    try:
        conn.execute(
            "INSERT INTO building_permits_seen (permit_uid, scraped_at) VALUES (?,?)",
            (uid, datetime.utcnow().isoformat()),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass


# ── Lead build + storage ─────────────────────────────────────────────────────

def _make_lead(p: dict, sector: str, metro: str) -> dict | None:
    name = (p.get("company_name") or "").strip()
    slug = _slug(name)
    if not slug:
        return None
    raw = {
        "permit_id": p.get("permit_id", ""),
        "permit_type": p.get("permit_type", ""),
        "valuation": p.get("valuation", 0),
        "work_description": (p.get("description", "") or "")[:1500],
        "issue_date": p.get("issue_date", ""),
        "metro": metro,
        "permit_url": p.get("url", ""),
    }
    return {
        "company_name": name,
        "domain": slug,                 # dotless → unique key, no real website
        "source": SOURCE_TAG,
        "sector": sector,
        "state": p.get("state", ""),
        "city": p.get("city", ""),
        "raw_data": json.dumps(raw),
        "scraped_at": datetime.utcnow().isoformat(),
        "enrolled_smartlead": False,
    }


def _save_to_supabase(leads: list[dict]) -> int:
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.warning("Supabase not configured — skipping remote save")
        return 0
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }
    saved = 0
    for i in range(0, len(leads), 100):
        batch = leads[i : i + 100]
        try:
            r = requests.post(
                f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}?on_conflict=domain,source",
                headers=headers, json=batch, timeout=20,
            )
            if r.status_code in (200, 201):
                saved += len(batch)
            else:
                logger.error("Supabase batch failed %d: %s", r.status_code, r.text[:200])
        except Exception as e:
            logger.error("Supabase batch error: %s", e)
    return saved


def _save_to_csv(leads: list[dict]) -> Path:
    fname = OUTPUT_DIR / f"permit_leads_{datetime.now().date().isoformat()}.csv"
    if not leads:
        return fname
    with open(fname, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=leads[0].keys())
        w.writeheader()
        w.writerows(leads)
    logger.info("CSV saved: %s (%d rows)", fname, len(leads))
    return fname


# ── Entry point ──────────────────────────────────────────────────────────────

def run(metros: list[str] | None = None, min_cost: int = DEFAULT_MIN_COST,
        days: int = DEFAULT_LOOKBACK_DAYS, dry_run: bool = False) -> dict:
    """Scan permit sources, classify to ECAS sectors, write contractor leads."""
    _ensure_db(DB_PATH)
    conn = sqlite3.connect(str(DB_PATH))

    metros = metros or list(SOURCES.keys())
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00.000")

    leads: list[dict] = []
    scanned = 0
    sector_counts: dict[str, int] = {}

    for metro in metros:
        adapter = SOURCES.get(metro)
        if not adapter:
            logger.warning("[%s] no verified source adapter — skipping", metro)
            continue
        logger.info("[%s] fetching permits > $%s issued since %s", metro, f"{min_cost:,}", cutoff[:10])
        permits = adapter(min_cost, cutoff)
        scanned += len(permits)
        logger.info("[%s] %d candidate permits with a contractor", metro, len(permits))

        for p in permits:
            uid = f"{metro}::{p.get('permit_id', '')}"
            if not p.get("permit_id") or not _is_new(conn, uid):
                continue
            sector = classify_sector(f"{p.get('description','')} {p.get('permit_type','')}")
            if not sector:
                continue
            lead = _make_lead(p, sector, metro)
            if not lead:
                continue
            leads.append(lead)
            sector_counts[sector] = sector_counts.get(sector, 0) + 1
            if not dry_run:
                _mark_seen(conn, uid)

    conn.close()

    # Collapse to one lead per (contractor, source) before write
    unique: dict[str, dict] = {}
    for ld in leads:
        unique.setdefault(ld["domain"], ld)
    leads = list(unique.values())

    saved = 0
    csv_path = None
    if leads and not dry_run:
        csv_path = _save_to_csv(leads)
        saved = _save_to_supabase(leads)

    logger.info(
        "[building_permits] Done: %d scanned | %d infra leads | %d saved to Supabase | %s%s",
        scanned, len(leads), saved, sector_counts, " (DRY RUN)" if dry_run else "",
    )
    return {
        "permits_scanned": scanned,
        "infra_leads": len(leads),
        "saved_supabase": saved,
        "sector_breakdown": sector_counts,
        "csv": str(csv_path) if csv_path else None,
        "dry_run": dry_run,
    }


def main():
    p = argparse.ArgumentParser(description="Building-permit → EPC contractor lead signal")
    p.add_argument("--metro", default="all", help="comma-sep metros (default: all). e.g. chicago")
    p.add_argument("--min-cost", type=int, default=DEFAULT_MIN_COST, help="min permit valuation USD")
    p.add_argument("--days", type=int, default=DEFAULT_LOOKBACK_DAYS, help="issued-since lookback days")
    p.add_argument("--dry-run", action="store_true", help="scan + classify, no writes")
    args = p.parse_args()
    metros = None if args.metro == "all" else [m.strip() for m in args.metro.split(",")]
    result = run(metros=metros, min_cost=args.min_cost, days=args.days, dry_run=args.dry_run)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
