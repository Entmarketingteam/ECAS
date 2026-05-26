#!/usr/bin/env python3
"""
signals/h1b_signal_engine.py — EPC intent signal from H-1B LCA disclosure data.

THESIS
──────
An H-1B sponsorship is expensive (legal + DOL/USCIS fees, multi-month process).
When an EPC firm spends that money on a *pipeline / revenue* role — Estimator,
Preconstruction Manager, Business Development, Proposal Manager, Capture Manager —
it is a leading indicator that the firm is:
  1. funded enough to commit visa spend,
  2. actively investing in *winning more work* (not just delivering it),
  3. scaling the exact function ContractMotion makes more effective.

That makes them a prime ContractMotion buyer BEFORE they show up in any RFP feed.

SIGNAL LOGIC (per the two chosen scorers)
─────────────────────────────────────────
  • ROLE       — filing is for a high-intent pipeline/revenue role (gates inclusion)
  • VOLUME     — total such filings by the employer (more = bigger GTM investment)
  • VELOCITY   — distinct years with filings (sustained multi-year hiring = funded)
Wage is intentionally NOT scored (not a selected signal; also absent from the
server-rendered record links — see DATA SOURCE).

DATA SOURCE
───────────
https://h1bdata.info indexes DOL OFLC LCA disclosure data (~4.8M records,
Oct-2013 → Sep-2025). A query `index.php?em=&job=<ROLE>&city=&year=<YYYY>`
returns records server-rendered as <a> link triplets (employer / role / city).
We query each high-intent ROLE × YEAR, parse employer occurrences, and aggregate
per employer into volume + velocity. The per-record salary lives only in the
JS-hydrated table (not the link triplets) and is not needed here.

  NOTE: this is the convenience index. For an audit-grade rebuild, swap the
  fetch layer for the authoritative DOL OFLC quarterly disclosure files
  (dol.gov/agencies/eta/foreign-labor/performance) — same schema, no scraping.

STORAGE (matches epc_lead_engine.py conventions)
────────────────────────────────────────────────
  • SQLite tracker.db   — dedup on (source + employer slug)
  • Supabase epc_company_leads — upsert on (domain, source); domain = name slug
    placeholder (Apollo resolves the real domain downstream, keyed on company_name)
  • CSV → signals/output/h1b_epc_leads_{date}.csv

USAGE
─────
  python signals/h1b_signal_engine.py                      # all roles, last 3 yrs
  python signals/h1b_signal_engine.py --years 2022 2023 2024 2025
  python signals/h1b_signal_engine.py --role estimator     # single role keyword
  python signals/h1b_signal_engine.py --min-score 50       # only hotter leads
  python signals/h1b_signal_engine.py --dry-run            # print, don't save
"""

import argparse
import csv
import json
import logging
import os
import re
import sqlite3
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime
from pathlib import Path
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("h1b_signal_engine")

# ── Config ──────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "database" / "tracker.db"
OUTPUT_DIR = BASE_DIR / "signals" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_TABLE = "epc_company_leads"
SOURCE = "h1b_lca"

BASE_URL = "https://h1bdata.info/index.php"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ECAS-signal/1.0)"}

# High-intent role keywords → weight. These are pipeline/revenue-investment
# roles. Construction-specific ones (estimator/precon) also act as an EPC filter:
# almost no non-construction employer sponsors an H-1B "estimator".
ROLE_KEYWORDS = {
    "estimator": 3,                      # construction-specific, core pipeline
    "chief estimator": 4,
    "preconstruction manager": 4,        # construction-specific, senior pursuit
    "business development manager": 3,
    "director of business development": 4,
    "proposal manager": 3,
    "capture manager": 4,                # explicit federal pursuit role
    "project executive": 2,
}

# Employer-name tokens that confirm an EPC / construction / engineering firm.
# Used to flag is_epc; estimator/precon roles auto-pass even without a match.
EPC_NAME_TOKENS = (
    "construction", "constructors", "builders", "building", "contractor",
    "contracting", "engineering", "engineers", "mechanical", "electric",
    "electrical", "civil", "infrastructure", "industrial", "energy", "power",
    "utility", "utilities", "concrete", "steel", "piping", "plumbing", "hvac",
    "epc", "general contractor", "design build", "design-build", "facilities",
)

ROLE_AUTO_EPC = ("estimator", "preconstruction")  # role substrings that imply EPC

# Light sector inference from employer name → ECAS sector slugs.
SECTOR_TOKENS = {
    "power": ("power", "grid", "electric", "transmission", "substation", "energy"),
    "water": ("water", "wastewater", "sewer", "utilities", "utility"),
    "dc": ("data center", "datacenter", "mission critical"),
    "defense": ("defense", "federal", "nuclear", "government"),
    "industrial": ("industrial", "manufacturing", "process", "mechanical", "piping"),
}


# ── Dedup (SQLite) ────────────────────────────────────────────────────────────

def _init_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS h1b_leads_seen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dedup_key TEXT UNIQUE,
            scraped_at TEXT
        )
    """)
    conn.commit()
    return conn


def _is_seen(conn: sqlite3.Connection, dedup_key: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM h1b_leads_seen WHERE dedup_key=?", (dedup_key,)
    ).fetchone() is not None


def _mark_seen(conn: sqlite3.Connection, dedup_key: str) -> None:
    try:
        conn.execute(
            "INSERT INTO h1b_leads_seen (dedup_key, scraped_at) VALUES (?,?)",
            (dedup_key, datetime.utcnow().isoformat()),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass


# ── Helpers ────────────────────────────────────────────────────────────────────

def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "unknown"


def _clean_employer(raw: str) -> str:
    # h1bdata appends " - CITY ST - <id>" to some employer strings; strip it,
    # then collapse whitespace so " TURNER CO " and "TURNER CO" merge.
    name = re.split(r"\s+-\s+[A-Z .]+\s+[A-Z]{2}\s+-\s+\d+", raw)[0]
    return re.sub(r"\s+", " ", name).strip()


def _infer_sector(name: str) -> str:
    low = name.lower()
    for sector, tokens in SECTOR_TOKENS.items():
        if any(t in low for t in tokens):
            return sector
    return "general_epc"


def _is_epc(name: str, roles: set) -> bool:
    low = name.lower()
    if any(r_sub in role for role in roles for r_sub in ROLE_AUTO_EPC):
        return True
    return any(tok in low for tok in EPC_NAME_TOKENS)


# ── Fetch + parse one (role, year) page ─────────────────────────────────────────

def _fetch_role_year(role: str, year: int) -> list[dict]:
    """Parse the per-employer summary list for one (role, year) page.

    Each summary entry is an <a> with the queried job= param, an empty city,
    containing a `span.label` (Median $X) and a `span.badge` (filing count).
    Returns one dict per employer: {employer, role, year, count, median}.
    Sidebar 'popular employer' links lack the job param + badge → excluded.
    """
    url = f"{BASE_URL}?em=&job={quote_plus(role)}&city=&year={year}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
    except Exception as e:
        logger.warning("fetch failed role=%s year=%s: %s", role, year, e)
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    out = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "job=" not in href or "em=&" in href.replace("&amp;", "&"):
            continue  # not a per-employer link
        badge = a.find("span", class_="badge")
        if badge is None:
            continue  # not a summary entry (record-row / sidebar link)
        m = re.match(r"index\.php\?em=([^&]+)&", href)
        if not m or not m.group(1):
            continue
        # employer = anchor's own text, excluding the pull-right span children
        emp_text = "".join(a.find_all(string=True, recursive=False))
        employer = _clean_employer(emp_text)
        if not employer or employer.upper() == role.upper():
            continue
        try:
            count = int(re.sub(r"[^\d]", "", badge.get_text()))
        except ValueError:
            count = 1
        label = a.find("span", class_="label")
        median = ""
        if label:
            mm = re.search(r"\$[\d,]+", label.get_text())
            median = mm.group(0) if mm else ""
        out.append({"employer": employer, "role": role, "year": year,
                    "count": count, "median": median})
    logger.info("role=%s year=%s → %d employers", role, year, len(out))
    return out


# ── Scoring ──────────────────────────────────────────────────────────────────

def _score(volume: int, velocity: int, roles: set) -> tuple[int, str]:
    """intent_score from VOLUME + VELOCITY (+ role weight). Returns (score, tier)."""
    role_weight = sum(ROLE_KEYWORDS.get(r, 1) for r in roles)
    score = min(100, volume * 6 + velocity * 12 + role_weight * 4)
    if score >= 60:
        tier = "High"
    elif score >= 35:
        tier = "Medium"
    else:
        tier = "Low"
    return score, tier


def _aggregate(records: list[dict]) -> list[dict]:
    """Collapse per-employer records into scored leads.

    volume   = sum of filing counts across roles/years
    velocity = number of distinct years the employer filed
    """
    by_emp = defaultdict(
        lambda: {"volume": 0, "years": set(), "roles": set(), "medians": []})
    for rec in records:
        e = by_emp[rec["employer"]]
        e["volume"] += rec["count"]
        e["years"].add(rec["year"])
        e["roles"].add(rec["role"])
        if rec["median"]:
            e["medians"].append(rec["median"])

    leads = []
    for employer, agg in by_emp.items():
        volume = agg["volume"]
        velocity = len(agg["years"])
        roles = agg["roles"]
        score, tier = _score(volume, velocity, roles)
        leads.append({
            "company_name": employer,
            "domain": _slug(employer),          # placeholder; Apollo resolves real
            "source": SOURCE,
            "sector": _infer_sector(employer),
            "state": "",
            "city": "",
            "raw_data": json.dumps({
                "intent_score": score,
                "intent_tier": tier,
                "h1b_volume": volume,
                "h1b_velocity_years": velocity,
                "years": sorted(agg["years"]),
                "roles": sorted(roles),
                "median_wages": agg["medians"],
                "is_epc": _is_epc(employer, roles),
                "signal": "h1b_pipeline_role_sponsorship",
                "needs_domain_resolution": True,
            }),
            "scraped_at": datetime.utcnow().isoformat(),
            "enrolled_smartlead": False,
            # convenience flat fields for CSV / sorting (dropped before Supabase)
            "_score": score,
            "_tier": tier,
            "_volume": volume,
            "_velocity": velocity,
            "_is_epc": _is_epc(employer, roles),
        })
    leads.sort(key=lambda x: x["_score"], reverse=True)
    return leads


# ── Storage ────────────────────────────────────────────────────────────────────

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
    payload = [{k: v for k, v in l.items() if not k.startswith("_")} for l in leads]
    saved = 0
    for i in range(0, len(payload), 100):
        batch = payload[i : i + 100]
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}?on_conflict=domain,source",
            headers=headers, json=batch, timeout=20,
        )
        if r.status_code in (200, 201):
            saved += len(batch)
        else:
            logger.error("Supabase batch failed %d: %s", r.status_code, r.text[:200])
    return saved


def _save_to_csv(leads: list[dict]) -> Path:
    fname = OUTPUT_DIR / f"h1b_epc_leads_{date.today().isoformat()}.csv"
    if not leads:
        return fname
    cols = ["company_name", "_tier", "_score", "_volume", "_velocity",
            "_is_epc", "sector", "domain"]
    with open(fname, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(leads)
    logger.info("CSV saved: %s (%d rows)", fname, len(leads))
    return fname


# ── Orchestration ────────────────────────────────────────────────────────────

def run(roles: list[str], years: list[int], min_score: int,
        epc_only: bool, dry_run: bool) -> dict:
    jobs = [(role, year) for role in roles for year in years]
    logger.info("Fetching %d (role × year) pages with 6 workers…", len(jobs))

    records = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(_fetch_role_year, r, y): (r, y) for r, y in jobs}
        for fut in as_completed(futures):
            records.extend(fut.result())

    leads = _aggregate(records)
    logger.info("Aggregated %d unique employers", len(leads))

    if epc_only:
        leads = [l for l in leads if l["_is_epc"]]
    leads = [l for l in leads if l["_score"] >= min_score]
    logger.info("After filters (epc_only=%s, min_score=%d): %d leads",
                epc_only, min_score, len(leads))

    if dry_run:
        for l in leads[:40]:
            logger.info("  [%-6s %3d] vol=%-2d vel=%d %s  (%s)",
                        l["_tier"], l["_score"], l["_volume"], l["_velocity"],
                        l["company_name"], l["sector"])
        return {"total": len(leads), "saved_supabase": 0, "csv": None}

    conn = _init_db()
    fresh = [l for l in leads if not _is_seen(conn, f"{SOURCE}::{l['domain']}")]
    for l in fresh:
        _mark_seen(conn, f"{SOURCE}::{l['domain']}")
    conn.close()
    logger.info("%d new (de-duped against tracker.db)", len(fresh))

    saved = _save_to_supabase(leads)  # upsert all (refresh scores), merge-dupes
    csv_path = _save_to_csv(leads)
    return {"total": len(leads), "new": len(fresh),
            "saved_supabase": saved, "csv": str(csv_path)}


def main():
    p = argparse.ArgumentParser(description="H-1B EPC intent signal engine")
    p.add_argument("--role", help="single role keyword (default: all high-intent)")
    p.add_argument("--years", type=int, nargs="+",
                   help="years to query (default: last 3 full years)")
    p.add_argument("--min-score", type=int, default=0, help="min intent_score")
    p.add_argument("--all-employers", action="store_true",
                   help="keep non-EPC employers too (default: EPC-only)")
    p.add_argument("--dry-run", action="store_true", help="print, don't save")
    args = p.parse_args()

    roles = [args.role] if args.role else list(ROLE_KEYWORDS)
    if args.years:
        years = args.years
    else:
        this_year = date.today().year
        years = [this_year - 3, this_year - 2, this_year - 1]

    result = run(roles, years, args.min_score,
                 epc_only=not args.all_employers, dry_run=args.dry_run)
    logger.info("DONE: %s", json.dumps(result))


if __name__ == "__main__":
    main()
