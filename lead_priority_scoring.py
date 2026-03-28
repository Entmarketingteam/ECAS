#!/usr/bin/env python3
"""
ECAS Lead Priority Scoring System
- Scores projects by company size + sector + ICP fit
- Updates priority field in Airtable projects table
- Scores contacts by title seniority
- Tags top contacts (C-suite at High priority companies) with TIER 1 analyst_notes
"""

import requests
import json
import time
from collections import defaultdict

import os
PAT = os.environ.get("AIRTABLE_API_KEY", "")
BASE_ID = "appoi8SzEJY8in57x"
PROJECTS_TABLE = "tbloen0rEkHttejnC"
CONTACTS_TABLE = "tblPBvTBuhwlS8AnS"

HEADERS = {
    "Authorization": f"Bearer {PAT}",
    "Content-Type": "application/json"
}

# ─── Fetch all records from a table ───────────────────────────────────────────
def fetch_all(table_id, fields):
    records, offset = [], None
    while True:
        params = {"pageSize": 100}
        for f in fields:
            params.setdefault("fields[]", []).append(f)
        if offset:
            params["offset"] = offset
        r = requests.get(
            f"https://api.airtable.com/v0/{BASE_ID}/{table_id}",
            headers=HEADERS, params=params
        )
        r.raise_for_status()
        data = r.json()
        records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
    return records

# ─── Scoring functions ─────────────────────────────────────────────────────────
def company_size_score(emp):
    if emp >= 200:  return 40
    if emp >= 100:  return 30
    if emp >= 50:   return 20
    if emp >= 10:   return 10
    return 5

def sector_score(sector):
    if not sector:
        return 5
    s = sector.strip().lower()
    if "power" in s or "grid" in s:      return 30
    if "data center" in s:               return 25
    if "industrial" in s:                return 20
    if "defense" in s:                   return 15
    if "water" in s or "wastewater" in s: return 10
    return 5

def icp_fit_score(icp):
    if not icp:
        return 10
    i = icp.strip().lower()
    if i == "strong":   return 30
    if i == "moderate": return 20
    if i == "weak":     return 5
    return 10  # unknown

def priority_label(total):
    if total >= 75: return "High"
    if total >= 50: return "Medium"
    return "Low"

# ─── Title seniority tier ──────────────────────────────────────────────────────
C_SUITE_KEYWORDS = ["ceo", "coo", "cfo", "cto", "cmo", "chief", "president", "owner", "founder", "co-founder"]
# "principal" only C-Suite when standalone or "managing principal" — NOT "Principal Engineer/Analyst/etc."
PRINCIPAL_TECHNICAL_EXCLUSIONS = ["engineer", "analyst", "scientist", "architect", "consultant",
                                   "electrical", "mechanical", "structural", "software", "systems",
                                   "researcher", "investigator", "specialist", "associate"]
VP_KEYWORDS      = ["vp ", "vice president", "vp,", "vp-", "v.p."]
DIR_KEYWORDS     = ["director"]

def title_tier(title):
    if not title:
        return "Other"
    t = title.strip().lower()
    if any(k in t for k in C_SUITE_KEYWORDS):
        return "C-Suite"
    # "principal" only C-Suite if standalone or "managing principal"
    # but NOT "Principal Engineer", "Principal Analyst", etc.
    if "principal" in t:
        is_technical = any(ex in t for ex in PRINCIPAL_TECHNICAL_EXCLUSIONS)
        if not is_technical:
            # standalone "principal" or "managing principal" or "principal partner"
            return "C-Suite"
    if any(k in t for k in VP_KEYWORDS):
        return "VP"
    if any(k in t for k in DIR_KEYWORDS):
        return "Director"
    return "Manager/Other"

# ─── Batch PATCH helper ────────────────────────────────────────────────────────
def batch_patch(table_id, updates):
    """
    updates: list of {"id": record_id, "fields": {...}}
    Airtable allows max 10 per PATCH request.
    """
    results = []
    for i in range(0, len(updates), 10):
        chunk = updates[i:i+10]
        payload = {"records": [{"id": u["id"], "fields": u["fields"]} for u in chunk]}
        r = requests.patch(
            f"https://api.airtable.com/v0/{BASE_ID}/{table_id}",
            headers=HEADERS,
            json=payload
        )
        r.raise_for_status()
        results.extend(r.json().get("records", []))
        time.sleep(0.2)  # respect rate limits
    return results

# ─── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("ECAS Lead Priority Scoring System")
    print("=" * 60)

    # ── Step 1: Fetch projects ──────────────────────────────────
    print("\n[1/4] Fetching projects...")
    # 'sector' is embedded in positioning_notes JSON, not a top-level field
    project_fields = ["owner_company", "confidence_score", "icp_fit", "priority", "positioning_notes"]
    projects = fetch_all(PROJECTS_TABLE, project_fields)
    print(f"  Fetched {len(projects)} project records")

    # Parse employee count AND sector from positioning_notes JSON
    for rec in projects:
        notes = {}
        raw = rec["fields"].get("positioning_notes", "")
        if raw:
            try:
                notes = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                pass
        rec["_emp"]    = notes.get("employee_count", 0) or 0
        rec["_sector"] = notes.get("sector", "") or ""

    # ── Step 2: Calculate scores ────────────────────────────────
    print("\n[2/4] Calculating composite priority scores...")
    project_updates = []
    score_details = []

    for rec in projects:
        fields = rec["fields"]
        emp    = rec["_emp"]
        sector = rec["_sector"]
        icp    = fields.get("icp_fit", "")
        company = fields.get("owner_company", "Unknown")

        cs = company_size_score(emp)
        ss = sector_score(sector)
        ic = icp_fit_score(icp)
        total = cs + ss + ic
        label = priority_label(total)

        score_details.append({
            "id": rec["id"],
            "company": company,
            "emp": emp,
            "sector": sector,
            "icp": icp,
            "company_size_score": cs,
            "sector_score": ss,
            "icp_score": ic,
            "total": total,
            "priority": label
        })

        project_updates.append({
            "id": rec["id"],
            "fields": {"priority": label}
        })

    # ── Step 3: Patch project priority fields ───────────────────
    print(f"\n[3/4] Patching priority field on {len(project_updates)} project records...")
    batch_patch(PROJECTS_TABLE, project_updates)

    # Tally
    tally = defaultdict(int)
    for sd in score_details:
        tally[sd["priority"]] += 1

    print(f"\n  Priority Distribution:")
    print(f"    High:   {tally['High']}")
    print(f"    Medium: {tally['Medium']}")
    print(f"    Low:    {tally['Low']}")

    # Build lookup: record_id → score_detail (for contact tagging)
    # Also build company → highest priority mapping
    company_priority = {}
    company_info = {}
    for sd in score_details:
        comp = (sd["company"] or "").strip().lower()
        existing = company_priority.get(comp, "Low")
        # High > Medium > Low
        rank = {"High": 3, "Medium": 2, "Low": 1}
        if rank[sd["priority"]] >= rank[existing]:
            company_priority[comp] = sd["priority"]
            company_info[comp] = sd

    # ── Step 4: Score contacts ──────────────────────────────────
    print("\n[4/4] Fetching and scoring contacts...")
    contact_fields = ["first_name", "last_name", "title", "company_name", "email", "outreach_status"]
    contacts = fetch_all(CONTACTS_TABLE, contact_fields)
    print(f"  Fetched {len(contacts)} contact records")

    tier_tally = defaultdict(int)
    tier1_contacts = []
    contact_updates = []

    for rec in contacts:
        fields = rec["fields"]
        title  = fields.get("title", "")
        company = (fields.get("company_name", "") or "").strip()
        first  = fields.get("first_name", "")
        last   = fields.get("last_name", "")
        name   = f"{first} {last}".strip()

        tier = title_tier(title)
        tier_tally[tier] += 1

        # Tag top contacts: C-Suite at High priority companies
        comp_key = company.lower()
        comp_priority = company_priority.get(comp_key, "Low")

        # Tag TIER 1: C-Suite at High priority companies
        # Also tag TIER 1A: C-Suite at Medium priority companies (High is currently unreachable
        # until employee_count is populated — all companies score size=5 by default)
        if tier == "C-Suite" and comp_priority in ("High", "Medium"):
            info = company_info.get(comp_key, {})
            emp    = info.get("emp", 0)
            sector = info.get("sector", "Unknown")
            tier_label = "TIER 1" if comp_priority == "High" else "TIER 1A"
            note = f"{tier_label} — {company} ({emp} employees) — {sector}"
            tier1_contacts.append({
                "name": name,
                "title": title,
                "company": company,
                "priority": comp_priority,
                "note": note,
                "id": rec["id"]
            })
            contact_updates.append({
                "id": rec["id"],
                "fields": {"analyst_notes": note}
            })

    # Patch contact analyst_notes
    if contact_updates:
        print(f"\n  Tagging {len(contact_updates)} TIER 1 contacts with analyst_notes...")
        try:
            batch_patch(CONTACTS_TABLE, contact_updates)
        except requests.exceptions.HTTPError as e:
            # analyst_notes field may not exist — try notes field instead
            print(f"  [warn] analyst_notes field failed ({e}), trying 'notes' field...")
            fallback = [{"id": u["id"], "fields": {"notes": u["fields"]["analyst_notes"]}} for u in contact_updates]
            try:
                batch_patch(CONTACTS_TABLE, fallback)
            except requests.exceptions.HTTPError as e2:
                print(f"  [warn] notes field also failed ({e2}) — skipping contact patch")

    # ── Print full breakdown ─────────────────────────────────────
    print("\n" + "=" * 60)
    print("FULL BREAKDOWN")
    print("=" * 60)

    print("\n--- PROJECT PRIORITY SCORES ---")
    # Sort by total desc
    for sd in sorted(score_details, key=lambda x: x["total"], reverse=True):
        print(f"  [{sd['priority']:6}] {sd['total']:3}pts | {sd['company'][:35]:<35} | "
              f"emp={sd['emp']:>5} | sector={sd['sector'] or 'N/A'} | icp={sd['icp'] or 'N/A'}")

    print(f"\n--- CONTACT TITLE TIER BREAKDOWN ({len(contacts)} total) ---")
    for tier in ["C-Suite", "VP", "Director", "Manager/Other"]:
        print(f"  {tier:<20}: {tier_tally[tier]}")

    print(f"\n--- TIER 1 CONTACTS (C-Suite @ High/Medium Priority Companies) ---")
    if tier1_contacts:
        for c in sorted(tier1_contacts, key=lambda x: (x["priority"] != "High", x["company"])):
            print(f"  {c['name']:<25} | {c['title']:<35} | {c['note']}")
    else:
        print("  (none found — check company_name matching between tables)")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Projects scored:  {len(projects)}")
    print(f"    High:           {tally['High']}")
    print(f"    Medium:         {tally['Medium']}")
    print(f"    Low:            {tally['Low']}")
    print(f"  Contacts scored:  {len(contacts)}")
    print(f"    C-Suite:        {tier_tally['C-Suite']}")
    print(f"    VP:             {tier_tally['VP']}")
    print(f"    Director:       {tier_tally['Director']}")
    print(f"    Manager/Other:  {tier_tally['Manager/Other']}")
    print(f"  TIER 1 contacts tagged: {len(tier1_contacts)}")
    print("=" * 60)

if __name__ == "__main__":
    main()
