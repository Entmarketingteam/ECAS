#!/usr/bin/env python3
"""
ECAS Airtable setup script.
- Checks and creates linked record fields
- Checks and creates formula fields on the projects table
- Deletes "Table 1" if it exists
"""

import json
import subprocess
import sys
import time

import requests

# ── Config ────────────────────────────────────────────────────────────────────
PAT_CMD = ["doppler", "secrets", "get", "AIRTABLE_TOKEN",
           "--project", "ent-agency-automation", "--config", "dev", "--plain"]
BASE_ID = "appoi8SzEJY8in57x"
META_URL = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}"
DATA_URL = f"https://api.airtable.com/v0/{BASE_ID}"

TABLE_IDS = {
    "signals_raw": "tblAFJnXToLTKeaNU",
    "projects":    "tbloen0rEkHttejnC",
    "contacts":    "tblPBvTBuhwlS8AnS",
    "deals":       "tbl2ZkD20cf6zMxJj",
}
TABLE_1_ID = "tblLug5dfjpq32MSk"

# ── Auth ──────────────────────────────────────────────────────────────────────
pat = subprocess.run(PAT_CMD, capture_output=True, text=True, check=True).stdout.strip()
HEADERS = {"Authorization": f"Bearer {pat}", "Content-Type": "application/json"}


def get_tables():
    r = requests.get(f"{META_URL}/tables", headers=HEADERS)
    r.raise_for_status()
    return r.json()["tables"]


def existing_field_names(table_fields):
    return {f["name"].lower(): f for f in table_fields}


def create_field(table_id, payload, label):
    url = f"{META_URL}/tables/{table_id}/fields"
    r = requests.post(url, headers=HEADERS, json=payload)
    if r.status_code in (200, 201):
        data = r.json()
        print(f"  ✓ CREATED  {label}  (id={data.get('id')})")
        return data
    else:
        print(f"  ✗ FAILED   {label}  → {r.status_code}: {r.text[:200]}")
        return None


def delete_table(table_id, name):
    url = f"{META_URL}/tables/{table_id}"
    r = requests.delete(url, headers=HEADERS)
    if r.status_code in (200, 204):
        print(f"  ✓ DELETED  table '{name}' ({table_id})")
    else:
        print(f"  ✗ FAILED to delete table '{name}' → {r.status_code}: {r.text[:200]}")


# ── Fetch current schema ──────────────────────────────────────────────────────
print("\n=== Fetching current ECAS schema ===")
tables = get_tables()
table_map = {t["id"]: t for t in tables}
table_name_map = {t["name"]: t for t in tables}

for t in tables:
    print(f"  Table: {t['name']} ({t['id']}) — {len(t['fields'])} fields")

# ── 1. Linked record fields ───────────────────────────────────────────────────
print("\n=== Linked record fields ===")

linked_specs = [
    # (table_id, field_name, linked_table_id, description)
    (TABLE_IDS["projects"],  "signals",  TABLE_IDS["signals_raw"], "projects → signals_raw"),
    (TABLE_IDS["projects"],  "contacts", TABLE_IDS["contacts"],    "projects → contacts"),
    (TABLE_IDS["projects"],  "deals",    TABLE_IDS["deals"],       "projects → deals"),
    (TABLE_IDS["contacts"],  "project",  TABLE_IDS["projects"],    "contacts → projects (singular)"),
    (TABLE_IDS["deals"],     "project",  TABLE_IDS["projects"],    "deals → projects (singular)"),
    (TABLE_IDS["deals"],     "contact",  TABLE_IDS["contacts"],    "deals → contacts"),
]

for (tbl_id, field_name, linked_tbl_id, desc) in linked_specs:
    tbl = table_map.get(tbl_id)
    if not tbl:
        print(f"  ! Table {tbl_id} not found, skipping {desc}")
        continue
    existing = existing_field_names(tbl["fields"])
    if field_name.lower() in existing:
        fld = existing[field_name.lower()]
        print(f"  — EXISTS   {desc}  (name='{fld['name']}', id={fld['id']})")
    else:
        payload = {
            "name": field_name,
            "type": "multipleRecordLinks",
            "options": {"linkedTableId": linked_tbl_id}
        }
        create_field(tbl_id, payload, desc)
        time.sleep(0.3)  # small rate-limit buffer

# ── Re-fetch schema after link creation (fields may have changed) ─────────────
print("\n=== Re-fetching schema for formula field planning ===")
tables = get_tables()
table_map = {t["id"]: t for t in tables}

projects_table = table_map[TABLE_IDS["projects"]]
projects_fields = {f["name"]: f for f in projects_table["fields"]}

print("  Projects fields found:")
for name, fld in sorted(projects_fields.items()):
    print(f"    {name} ({fld['type']})")

# ── 2. Formula fields on projects ─────────────────────────────────────────────
print("\n=== Formula fields on projects ===")

# days_in_stage
# stage_entered_at exists — use it
if "stage_entered_at" in projects_fields:
    days_formula = "DATETIME_DIFF(NOW(), {stage_entered_at}, 'days')"
    print("  Using stage_entered_at for days_in_stage formula")
else:
    days_formula = "DATETIME_DIFF(NOW(), CREATED_TIME(), 'days')"
    print("  stage_entered_at not found — falling back to CREATED_TIME() for days_in_stage")

# weighted_value
# Look for estimated_value and win_probability equivalents
# From schema we see: estimated_contract_value_band (singleSelect — no good for math)
# No numeric estimated_value or win_probability fields exist yet.
# Use a safe formula that references fields only if they exist.
# We'll check and create the formula referencing whatever is present.
has_estimated_value = "estimated_value" in projects_fields
has_win_probability = "win_probability" in projects_fields
has_confidence_score = "confidence_score" in projects_fields

if has_estimated_value and has_win_probability:
    weighted_formula = "{estimated_value} * {win_probability}"
elif has_estimated_value and has_confidence_score:
    weighted_formula = "{estimated_value} * {confidence_score}"
else:
    # Neither exists — create a placeholder formula
    # Use confidence_score (exists) as a proxy; estimated_value doesn't exist
    # We'll note this in the output
    weighted_formula = "IF({confidence_score}, {confidence_score}, 0)"
    print("  WARNING: No estimated_value or win_probability fields found.")
    print("  Using confidence_score as placeholder for weighted_value formula.")
    print("  Add numeric estimated_value and win_probability fields for proper calculation.")

# guarantee_end_date
# deals table has contract_signed_date — but that's on deals, not projects
# projects does NOT have contract_start_date or created_at
# We'll use CREATED_TIME() as the base
has_contract_start = "contract_start_date" in projects_fields
if has_contract_start:
    guarantee_formula = "DATEADD({contract_start_date}, 90, 'days')"
else:
    guarantee_formula = "DATEADD(CREATED_TIME(), 90, 'days')"
    print("  No contract_start_date on projects — using CREATED_TIME() + 90 days for guarantee_end_date")

# guarantee_days_remaining depends on guarantee_end_date existing
guarantee_remaining_formula = "MAX(0, DATETIME_DIFF({guarantee_end_date}, NOW(), 'days'))"

formula_specs = [
    ("days_in_stage",          days_formula,               "Days project has been in current stage"),
    ("weighted_value",         weighted_formula,           "Estimated value weighted by probability"),
    ("guarantee_end_date",     guarantee_formula,          "90 days from contract start / project creation"),
    ("guarantee_days_remaining", guarantee_remaining_formula, "Days remaining in guarantee period"),
]

for (field_name, formula, description) in formula_specs:
    existing = {f["name"].lower(): f for f in projects_table["fields"]}
    if field_name.lower() in existing:
        fld = existing[field_name.lower()]
        print(f"  — EXISTS   {field_name}  (id={fld['id']})")
    else:
        payload = {
            "name": field_name,
            "type": "formula",
            "description": description,
            "options": {"formula": formula}
        }
        result = create_field(TABLE_IDS["projects"], payload, field_name)
        if result:
            # Refresh projects table so next formula can reference just-created field
            tables = get_tables()
            table_map = {t["id"]: t for t in tables}
            projects_table = table_map[TABLE_IDS["projects"]]
        time.sleep(0.3)

# ── 3. Delete "Table 1" ───────────────────────────────────────────────────────
print("\n=== Checking for 'Table 1' ===")
if TABLE_1_ID in table_map or "Table 1" in {t["name"] for t in tables}:
    print("  Found 'Table 1' — deleting...")
    delete_table(TABLE_1_ID, "Table 1")
else:
    print("  'Table 1' not found — nothing to delete")

# ── Final summary ─────────────────────────────────────────────────────────────
print("\n=== Done ===")
print("Final projects table fields:")
tables = get_tables()
projects_final = next(t for t in tables if t["id"] == TABLE_IDS["projects"])
for f in projects_final["fields"]:
    print(f"  {f['name']} ({f['type']})")

print("""
=== MANUAL STEPS REQUIRED ===
1. Formula fields (Airtable API does not support creating formula fields):
   Open projects table in Airtable UI and add these fields manually:

   a) days_in_stage (Formula):
      DATETIME_DIFF(NOW(), {stage_entered_at}, 'days')

   b) weighted_value (Formula):
      NOTE: You need numeric fields 'estimated_value' (number) and 'win_probability' (percent)
      first. Then: {estimated_value} * {win_probability}
      Currently using confidence_score as placeholder.

   c) guarantee_end_date (Formula):
      NOTE: Add a date field 'contract_start_date' to projects if needed.
      Formula: DATEADD(CREATED_TIME(), 90, 'days')
      Or with contract_start_date: DATEADD({contract_start_date}, 90, 'days')

   d) guarantee_days_remaining (Formula — must be added AFTER guarantee_end_date):
      MAX(0, DATETIME_DIFF({guarantee_end_date}, NOW(), 'days'))

2. Delete 'Table 1' (tblLug5dfjpq32MSk):
   Airtable API does not support table deletion.
   Go to: https://airtable.com/appoi8SzEJY8in57x
   Right-click 'Table 1' tab → Delete table

3. Clean up optional: 'contacts_from_project_link' and 'deals_from_project_link'
   on the projects table are auto-created inverse links from contacts.project and
   deals.project. They are functional but redundant with existing contacts/deals fields.
   You may hide or delete them via the UI.
""")
