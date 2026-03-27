"""
cleanup_signal_dupes.py — Delete duplicate records from signals_raw.

Groups all records by (company_name + signal_type + signal_date).
Keeps the record with the lowest Airtable record ID (i.e. created first).
Deletes all others. Prints a summary.
"""

import os
import sys
import time
from collections import defaultdict

import requests

AIRTABLE_PAT = os.environ.get("AIRTABLE_API_KEY") or os.environ.get("AIRTABLE_PAT")
BASE_ID = "appoi8SzEJY8in57x"
TABLE_ID = "tblAFJnXToLTKeaNU"
BASE_URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}"
RATE_LIMIT_DELAY = 0.25

if not AIRTABLE_PAT:
    print("ERROR: AIRTABLE_API_KEY not set")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
    "Content-Type": "application/json",
}


def get_all_records() -> list[dict]:
    records = []
    offset = None
    page = 0
    while True:
        params = {
            "fields[]": ["company_name", "signal_type", "captured_at"],
        }
        if offset:
            params["offset"] = offset
        time.sleep(RATE_LIMIT_DELAY)
        resp = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("records", [])
        records.extend(batch)
        page += 1
        print(f"  Fetched page {page}: {len(batch)} records (total so far: {len(records)})")
        offset = data.get("offset")
        if not offset:
            break
    return records


def delete_records(record_ids: list[str]) -> int:
    """Delete up to 10 records per request (Airtable batch limit). Returns count deleted."""
    deleted = 0
    for i in range(0, len(record_ids), 10):
        batch = record_ids[i:i+10]
        params = [("records[]", rid) for rid in batch]
        time.sleep(RATE_LIMIT_DELAY)
        resp = requests.delete(BASE_URL, headers=HEADERS, params=params, timeout=30)
        if resp.ok:
            deleted += len(batch)
            print(f"  Deleted batch of {len(batch)}: {batch[:3]}{'...' if len(batch) > 3 else ''}")
        else:
            print(f"  ERROR deleting batch: {resp.status_code} {resp.text[:200]}")
    return deleted


def main():
    print("Fetching all signals_raw records...")
    records = get_all_records()
    print(f"\nTotal records fetched: {len(records)}\n")

    # Group by (company_name, signal_type, date_only)
    groups: dict[tuple, list[str]] = defaultdict(list)
    for rec in records:
        fields = rec.get("fields", {})
        company = (fields.get("company_name") or "").strip().lower()
        sig_type = (fields.get("signal_type") or "").strip().lower()
        captured_at = fields.get("captured_at") or ""
        date_only = captured_at[:10]  # YYYY-MM-DD
        key = (company, sig_type, date_only)
        groups[key].append(rec["id"])

    # Find groups with duplicates
    dupe_groups = {k: v for k, v in groups.items() if len(v) > 1}
    print(f"Duplicate groups found: {len(dupe_groups)}")

    if not dupe_groups:
        print("No duplicates — nothing to clean up.")
        return

    to_delete = []
    for key, ids in sorted(dupe_groups.items()):
        # Sort by record ID (recXXX — lexicographic order approximates creation order)
        ids_sorted = sorted(ids)
        keep = ids_sorted[0]
        dupes = ids_sorted[1:]
        company, sig_type, date_only = key
        print(f"  [{company} | {sig_type} | {date_only}] keep={keep}, delete {len(dupes)}: {dupes}")
        to_delete.extend(dupes)

    print(f"\nTotal records to delete: {len(to_delete)}")
    print("Deleting...")
    deleted = delete_records(to_delete)
    print(f"\nDone. Deleted {deleted} duplicate signal records.")


if __name__ == "__main__":
    main()
