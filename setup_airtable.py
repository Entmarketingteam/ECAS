#!/usr/bin/env python3
"""
ECAS Airtable Setup Script
Creates all 4 tables with fields and views in an existing base.

Usage:
  1. Create a new base in Airtable named "ECAS — Enterprise Contract Acquisition System"
  2. Copy the base ID from the URL (appXXX...)
  3. Run: python3 setup_airtable.py <BASE_ID>
     OR: BASE_ID=appXXX python3 setup_airtable.py

The script is idempotent — safe to run multiple times. It will skip
fields/tables that already exist.
"""

import os
import sys
import json
import time
import httpx

# ── Config ────────────────────────────────────────────────────────────────────

PAT = os.environ.get("AIRTABLE_API_KEY") or os.environ.get("AIRTABLE_TOKEN") or os.environ.get("AIRTABLE_PAT")
BASE_ID = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("ECAS_BASE_ID")

if not PAT:
    print("ERROR: Set AIRTABLE_API_KEY env var (your Airtable PAT)")
    sys.exit(1)

if not BASE_ID:
    print("ERROR: Pass base ID as first arg or set ECAS_BASE_ID env var")
    print("  Usage: python3 setup_airtable.py appXXXXXXXXXXXXXX")
    sys.exit(1)

HEADERS = {"Authorization": f"Bearer {PAT}", "Content-Type": "application/json"}
BASE_URL = "https://api.airtable.com/v0/meta"


# ── Helpers ───────────────────────────────────────────────────────────────────

def api(method: str, path: str, body: dict = None) -> dict:
    url = f"{BASE_URL}/{path}"
    resp = httpx.request(
        method, url, headers=HEADERS,
        json=body, timeout=30
    )
    if resp.status_code not in (200, 201):
        print(f"  API error {resp.status_code}: {resp.text[:300]}")
        return {}
    return resp.json()


def get_existing_tables() -> dict:
    """Returns {table_name: table_id}"""
    data = api("GET", f"bases/{BASE_ID}/tables")
    return {t["name"]: t["id"] for t in data.get("tables", [])}


def get_existing_fields(table_id: str) -> set:
    """Returns set of existing field names"""
    data = api("GET", f"bases/{BASE_ID}/tables")
    for t in data.get("tables", []):
        if t["id"] == table_id:
            return {f["name"] for f in t.get("fields", [])}
    return set()


def create_table(name: str, fields: list) -> str:
    """Creates table, returns table ID"""
    print(f"  Creating table: {name}")
    result = api("POST", f"bases/{BASE_ID}/tables", {
        "name": name,
        "fields": fields,
    })
    table_id = result.get("id", "")
    if table_id:
        print(f"  ✓ Created {name} ({table_id})")
    return table_id


def add_field(table_id: str, field: dict):
    """Adds a single field to a table"""
    result = api("POST", f"bases/{BASE_ID}/tables/{table_id}/fields", field)
    if result.get("id"):
        print(f"    + field: {field['name']}")
    else:
        print(f"    ! skipped: {field['name']} (may already exist)")
    time.sleep(0.2)  # rate limit


def create_view(table_id: str, view: dict):
    """Creates a view in a table"""
    result = api("POST", f"bases/{BASE_ID}/tables/{table_id}/views", view)
    if result.get("id"):
        print(f"    + view: {view['name']}")
    time.sleep(0.2)


# ── Table Definitions ─────────────────────────────────────────────────────────

# Initial fields passed at table creation (required by API — first field is primary)
# Additional fields added via add_field after table creation

TABLES = {
    "signals_raw": {
        "initial_fields": [
            {"name": "signal_id", "type": "singleLineText"},
        ],
        "additional_fields": [
            # signal_id as autonumber — add manually in Airtable UI (API doesn't support creation)
            {"name": "source", "type": "singleSelect", "options": {"choices": [
                {"name": "ferc_efts"}, {"name": "pjm_queue"}, {"name": "ercot_queue"},
                {"name": "rss_feed"}, {"name": "manual"},
            ]}},
            {"name": "url", "type": "url"},
            {"name": "raw_text", "type": "multilineText"},
            {"name": "captured_at", "type": "dateTime", "options": {
                "dateFormat": {"name": "iso"}, "timeFormat": {"name": "24hour"}, "timeZone": "utc"
            }},
            {"name": "processed", "type": "checkbox", "options": {"icon": "check", "color": "greenBright"}},
            {"name": "confidence_score", "type": "number", "options": {"precision": 2}},
            {"name": "notes", "type": "multilineText"},
        ],
        "views": [
            {"name": "Unprocessed Queue", "type": "grid"},
            {"name": "All Signals", "type": "grid"},
        ]
    },

    "projects": {
        "initial_fields": [
            {"name": "project_name", "type": "singleLineText"},
        ],
        "additional_fields": [
            {"name": "state", "type": "singleSelect", "options": {"choices": [
                {"name": "VA"}, {"name": "TX"},
            ]}},
            {"name": "county", "type": "singleLineText"},
            {"name": "mw_capacity", "type": "number", "options": {"precision": 1}},
            {"name": "estimated_contract_value_band", "type": "singleSelect", "options": {"choices": [
                {"name": "<$1M"}, {"name": "$1M-$5M"}, {"name": "$5M-$25M"},
                {"name": "$25M-$100M"}, {"name": ">$100M"},
            ]}},
            {"name": "project_type", "type": "singleSelect", "options": {"choices": [
                {"name": "transmission"}, {"name": "substation"}, {"name": "generation"},
                {"name": "distribution"}, {"name": "interconnection"},
                {"name": "data_center_power"}, {"name": "other"},
            ]}},
            {"name": "signal_type", "type": "singleSelect", "options": {"choices": [
                {"name": "ferc_filing"}, {"name": "interconnection_queue"},
                {"name": "rate_case"}, {"name": "ppa"}, {"name": "job_posting"},
                {"name": "press_release"}, {"name": "earnings_call"},
                {"name": "permit"}, {"name": "other"},
            ]}},
            {"name": "owner_company", "type": "singleLineText"},
            {"name": "epc_company", "type": "singleLineText"},
            {"name": "rfp_expected_date", "type": "singleLineText"},
            {"name": "positioning_window_open", "type": "singleLineText"},
            {"name": "positioning_window_close", "type": "singleLineText"},
            {"name": "scope_summary", "type": "multilineText"},
            {"name": "source_url", "type": "url"},
            {"name": "confidence_score", "type": "number", "options": {"precision": 2}},
            {"name": "stage", "type": "singleSelect", "options": {"choices": [
                {"name": "Identified", "color": "blueBright2"},
                {"name": "Researching", "color": "cyanBright2"},
                {"name": "Outreach", "color": "yellowBright2"},
                {"name": "Meeting Set", "color": "orangeBright2"},
                {"name": "Proposal Sent", "color": "pinkBright2"},
                {"name": "Negotiating", "color": "redBright2"},
                {"name": "Won", "color": "greenBright2"},
                {"name": "Lost", "color": "grayBright2"},
                {"name": "Dormant", "color": "gray"},
            ]}},
            {"name": "assigned_to", "type": "singleLineText"},
            {"name": "priority", "type": "singleSelect", "options": {"choices": [
                {"name": "High", "color": "redBright2"},
                {"name": "Medium", "color": "yellowBright2"},
                {"name": "Low", "color": "grayBright2"},
            ]}},
            {"name": "stage_entered_at", "type": "dateTime", "options": {
                "dateFormat": {"name": "iso"}, "timeFormat": {"name": "24hour"}, "timeZone": "utc"
            }},
            {"name": "icp_fit", "type": "singleSelect", "options": {"choices": [
                {"name": "Strong", "color": "greenBright2"}, {"name": "Moderate", "color": "yellowBright2"},
                {"name": "Weak", "color": "redBright2"}, {"name": "Unknown", "color": "grayBright2"},
            ]}},
            {"name": "analyst_notes", "type": "multilineText"},
            {"name": "positioning_notes", "type": "multilineText"},
        ],
        "views": [
            {"name": "High Priority", "type": "grid"},
            {"name": "Virginia Projects", "type": "grid"},
            {"name": "Texas Projects", "type": "grid"},
            {"name": "Needs Outreach", "type": "grid"},
        ]
    },

    "contacts": {
        "initial_fields": [
            {"name": "full_name", "type": "singleLineText"},
        ],
        "additional_fields": [
            # full_name is now the primary field — formula version added below in FORMULA_FIELDS
            {"name": "first_name", "type": "singleLineText"},
            {"name": "last_name", "type": "singleLineText"},
            {"name": "email", "type": "email"},
            {"name": "email_verified", "type": "checkbox", "options": {"icon": "check", "color": "greenBright"}},
            {"name": "title", "type": "singleLineText"},
            {"name": "company_name", "type": "singleLineText"},
            {"name": "company_role", "type": "singleSelect", "options": {"choices": [
                {"name": "owner"}, {"name": "epc"},
            ]}},
            {"name": "linkedin_url", "type": "url"},
            {"name": "phone", "type": "phoneNumber"},
            {"name": "city", "type": "singleLineText"},
            {"name": "state", "type": "singleLineText"},
            {"name": "headline", "type": "singleLineText"},
            {"name": "summary", "type": "multilineText"},
            {"name": "follower_count", "type": "number", "options": {"precision": 0}},
            {"name": "connections", "type": "number", "options": {"precision": 0}},
            {"name": "outreach_status", "type": "singleSelect", "options": {"choices": [
                {"name": "pending_review", "color": "grayBright2"},
                {"name": "approved", "color": "greenBright2"},
                {"name": "do_not_contact", "color": "redBright2"},
                {"name": "in_sequence", "color": "blueBright2"},
                {"name": "replied", "color": "cyanBright2"},
                {"name": "meeting_booked", "color": "yellowBright2"},
                {"name": "not_interested", "color": "orangeBright2"},
                {"name": "unsubscribed", "color": "grayBright2"},
            ]}},
            {"name": "smartlead_campaign_id", "type": "singleLineText"},
            {"name": "expandi_campaign_id", "type": "singleLineText"},
            {"name": "apollo_id", "type": "singleLineText"},
            {"name": "last_outreach_date", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
            {"name": "response_received", "type": "checkbox", "options": {"icon": "check", "color": "greenBright"}},
            {"name": "response_notes", "type": "multilineText"},
            {"name": "analyst_notes", "type": "multilineText"},
        ],
        "views": [
            {"name": "Pending Review", "type": "grid"},
            {"name": "Approved for Outreach", "type": "grid"},
            {"name": "In Sequence", "type": "grid"},
            {"name": "Replied", "type": "grid"},
        ]
    },

    "deals": {
        "initial_fields": [
            {"name": "deal_name", "type": "singleLineText"},
        ],
        "additional_fields": [
            {"name": "company_name", "type": "singleLineText"},
            {"name": "stage", "type": "singleSelect", "options": {"choices": [
                {"name": "Proposal Sent", "color": "blueBright2"},
                {"name": "Negotiating", "color": "yellowBright2"},
                {"name": "Contract Out", "color": "orangeBright2"},
                {"name": "Closed Won", "color": "greenBright2"},
                {"name": "Closed Lost", "color": "redBright2"},
            ]}},
            {"name": "contract_value", "type": "currency", "options": {
                "precision": 0, "symbol": "$"
            }},
            {"name": "guaranteed_revenue", "type": "currency", "options": {
                "precision": 0, "symbol": "$"
            }},
            {"name": "performance_upside", "type": "currency", "options": {
                "precision": 0, "symbol": "$"
            }},
            {"name": "contract_sent_date", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
            {"name": "contract_signed_date", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
            {"name": "guarantee_period_days", "type": "number", "options": {"precision": 0}},
            {"name": "close_probability", "type": "percent", "options": {"precision": 0}},
            {"name": "expected_close_date", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
            {"name": "lost_reason", "type": "singleSelect", "options": {"choices": [
                {"name": "No budget"}, {"name": "Went with competitor"},
                {"name": "Project cancelled"}, {"name": "No response"},
                {"name": "Scope mismatch"}, {"name": "Other"},
            ]}},
            {"name": "lost_notes", "type": "multilineText"},
            {"name": "close_notes", "type": "multilineText"},
            {"name": "next_step", "type": "singleLineText"},
            {"name": "next_step_due", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
        ],
        "views": [
            {"name": "Active Deals", "type": "grid"},
            {"name": "Guarantees Expiring", "type": "grid"},
            {"name": "Won Deals", "type": "grid"},
            {"name": "Pipeline Value", "type": "grid"},
        ]
    }
}

# Formula fields added after all tables exist (they reference other tables via linked records)
FORMULA_FIELDS = {
    "projects": [
        {
            "name": "days_in_stage",
            "type": "formula",
            "options": {"formula": "DATETIME_DIFF(NOW(), {stage_entered_at}, 'days')"}
        }
    ],
    "contacts": [
        # full_name is the primary text field — no formula needed
    ],
    "deals": [
        {
            "name": "guarantee_end_date",
            "type": "formula",
            "options": {"formula": "DATEADD({contract_signed_date}, {guarantee_period_days}, 'days')"}
        },
        {
            "name": "weighted_value",
            "type": "formula",
            "options": {"formula": "{contract_value} * {close_probability} / 100"}
        },
        {
            "name": "guarantee_days_remaining",
            "type": "formula",
            "options": {"formula": "IF({contract_signed_date}, MAX(0, DATETIME_DIFF({guarantee_end_date}, NOW(), 'days')), BLANK())"}
        },
    ]
}


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"\nECAS Airtable Setup")
    print(f"Base: {BASE_ID}\n")

    existing = get_existing_tables()
    print(f"Existing tables: {list(existing.keys()) or 'none'}\n")

    table_ids = dict(existing)

    # Step 1: Create tables
    for table_name, config in TABLES.items():
        if table_name in existing:
            print(f"  ✓ Table exists: {table_name} ({existing[table_name]})")
            table_ids[table_name] = existing[table_name]
        else:
            tid = create_table(table_name, config["initial_fields"])
            if tid:
                table_ids[table_name] = tid
            time.sleep(0.5)

    print()

    # Step 2: Add additional fields to each table
    for table_name, config in TABLES.items():
        tid = table_ids.get(table_name)
        if not tid:
            print(f"  SKIP {table_name} — no table ID")
            continue

        print(f"Adding fields to {table_name}...")
        existing_fields = get_existing_fields(tid)

        for field in config.get("additional_fields", []):
            if field["name"] in existing_fields:
                print(f"    ~ skip existing: {field['name']}")
                continue
            add_field(tid, field)

    print()

    # Step 3: Add formula fields
    print("Adding formula fields...")
    for table_name, fields in FORMULA_FIELDS.items():
        tid = table_ids.get(table_name)
        if not tid:
            continue
        existing_fields = get_existing_fields(tid)
        for field in fields:
            if field["name"] in existing_fields:
                print(f"    ~ skip existing: {field['name']}")
                continue
            add_field(tid, field)

    print()

    # Step 4: Add views
    print("Creating views...")
    for table_name, config in TABLES.items():
        tid = table_ids.get(table_name)
        if not tid:
            continue
        for view in config.get("views", []):
            create_view(tid, view)

    print()
    print("=" * 50)
    print("DONE")
    print()
    print("Base IDs for n8n workflow setup:")
    print(f"  ECAS_BASE_ID = {BASE_ID}")
    for name, tid in table_ids.items():
        print(f"  {name} = {tid}")
    print()
    print("Next steps:")
    print("  1. Copy ECAS_BASE_ID above")
    print("  2. In n8n, find-replace ECAS_BASE_ID in all 5 workflow JSONs")
    print("  3. Import workflows from Desktop/ECAS/n8n-workflows/")
    print("  4. Add linked record fields manually in Airtable UI:")
    print("     - projects.signals (→ signals_raw)")
    print("     - projects.contacts (→ contacts)")
    print("     - projects.deals (→ deals)")
    print("     - contacts.project_id (→ projects)")
    print("     - deals.project_id (→ projects)")
    print("     - deals.primary_contact (→ contacts)")


if __name__ == "__main__":
    main()
