import os
#!/usr/bin/env python3
"""
Deduplicate ECAS Airtable projects table.
Groups by owner_company (case-insensitive, stripped),
keeps highest confidence_score (or most recently created if tied),
deletes the rest.
"""

import sys
import time
import requests
from collections import defaultdict

AIRTABLE_PAT = os.environ["AIRTABLE_API_KEY"]
BASE_ID = "appoi8SzEJY8in57x"
TABLE_ID = "tbloen0rEkHttejnC"
BASE_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}"
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
    "Content-Type": "application/json",
}
RATE_LIMIT_DELAY = 0.25


def get_all_records():
    records = []
    offset = None
    page = 1
    while True:
        params = {"pageSize": 100}
        if offset:
            params["offset"] = offset
        time.sleep(RATE_LIMIT_DELAY)
        resp = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("records", [])
        records.extend(batch)
        print(f"  Page {page}: fetched {len(batch)} records (total so far: {len(records)})")
        offset = data.get("offset")
        page += 1
        if not offset:
            break
    return records


def delete_record(record_id):
    time.sleep(RATE_LIMIT_DELAY)
    resp = requests.delete(f"{BASE_URL}/{record_id}", headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def main():
    print("Fetching all records from projects table...")
    records = get_all_records()
    print(f"\nTotal records fetched: {len(records)}\n")

    # Group by owner_company (case-insensitive, stripped)
    groups = defaultdict(list)
    no_company = []
    for r in records:
        fields = r.get("fields", {})
        company = fields.get("owner_company", "").strip().lower()
        if not company:
            no_company.append(r["id"])
            continue
        groups[company].append(r)

    if no_company:
        print(f"Records with no owner_company (skipping): {len(no_company)}")
        for rid in no_company:
            print(f"  - {rid}")
        print()

    # Find duplicates
    dupes = {k: v for k, v in groups.items() if len(v) > 1}
    print(f"Companies with duplicates: {len(dupes)}")

    if not dupes:
        print("No duplicates found. Nothing to do.")
        return

    total_deleted = 0
    deleted_summary = []

    for company_lower, recs in sorted(dupes.items()):
        # Sort: highest confidence_score first, then by created_at descending (most recent first)
        def sort_key(r):
            fields = r.get("fields", {})
            score = fields.get("confidence_score", 0) or 0
            created = r.get("createdTime", "") or ""
            return (score, created)

        recs_sorted = sorted(recs, key=sort_key, reverse=True)
        keeper = recs_sorted[0]
        to_delete = recs_sorted[1:]

        keeper_fields = keeper.get("fields", {})
        display_name = keeper_fields.get("owner_company", company_lower)
        keeper_score = keeper_fields.get("confidence_score", 0)
        keeper_created = keeper.get("createdTime", "")

        print(f"\n  Company: {display_name}")
        print(f"    Total records: {len(recs)} | Keeping: {keeper['id']} (score={keeper_score}, created={keeper_created[:10]})")

        for r in to_delete:
            f = r.get("fields", {})
            score = f.get("confidence_score", 0)
            created = r.get("createdTime", "")[:10]
            print(f"    Deleting: {r['id']} (score={score}, created={created})")
            try:
                delete_record(r["id"])
                total_deleted += 1
                print(f"      -> Deleted OK")
            except Exception as e:
                print(f"      -> ERROR: {e}", file=sys.stderr)

        deleted_summary.append({
            "company": display_name,
            "total": len(recs),
            "deleted": len(to_delete),
        })

    print("\n" + "=" * 60)
    print("DEDUPLICATION SUMMARY")
    print("=" * 60)
    print(f"Total companies with dupes: {len(dupes)}")
    print(f"Total records deleted:      {total_deleted}")
    print()
    print("Companies that had duplicates:")
    for item in deleted_summary:
        print(f"  - {item['company']}  ({item['total']} records → kept 1, deleted {item['deleted']})")


if __name__ == "__main__":
    main()
