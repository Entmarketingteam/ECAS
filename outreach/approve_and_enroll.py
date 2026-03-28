"""
approve_and_enroll.py — Approve pending_review contacts in Airtable and enroll them in Smartlead.

Steps:
1. Fetch all pending_review contacts from Airtable (with pagination)
2. Filter to only those with an email address
3. Update outreach_status → approved in Airtable
4. Enroll in Smartlead campaign 3005694 in batches of 20
5. Update outreach_status → in_sequence in Airtable
"""

import sys
import time
import json
import requests

# ── Credentials (injected at runtime) ─────────────────────────────────────────
AIRTABLE_PAT = sys.argv[1]
SMARTLEAD_API_KEY = sys.argv[2]

AIRTABLE_BASE = "appoi8SzEJY8in57x"
CONTACTS_TABLE = "tblPBvTBuhwlS8AnS"
SMARTLEAD_CAMPAIGN_ID = 3005694

AT_HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
    "Content-Type": "application/json",
}


# ── 1. Fetch all pending_review contacts (paginated) ──────────────────────────
def fetch_pending_contacts():
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{CONTACTS_TABLE}"
    params = {
        "filterByFormula": "{outreach_status}='pending_review'",
        "pageSize": 100,
        "fields[]": [
            "first_name", "last_name", "email", "title",
            "company_name", "outreach_status", "linkedin_url",
        ],
    }
    all_records = []
    offset = None

    while True:
        if offset:
            params["offset"] = offset
        resp = requests.get(url, headers=AT_HEADERS, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        all_records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break

    return all_records


# ── 2. Airtable bulk update (up to 10 records per PATCH) ──────────────────────
def airtable_update_status(record_ids: list[str], status: str):
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{CONTACTS_TABLE}"
    for i in range(0, len(record_ids), 10):
        batch = record_ids[i:i+10]
        payload = {
            "records": [
                {"id": rid, "fields": {"outreach_status": status}}
                for rid in batch
            ]
        }
        resp = requests.patch(url, headers=AT_HEADERS, json=payload, timeout=30)
        if not resp.ok:
            print(f"  [WARN] Airtable update failed for batch {i//10}: {resp.status_code} {resp.text[:200]}")
        else:
            print(f"  [OK] Airtable: set {len(batch)} records → '{status}'")
        time.sleep(0.25)  # stay under 5 req/sec


# ── 3. Smartlead enroll in batches of 20 ──────────────────────────────────────
def smartlead_enroll(contacts: list[dict]) -> tuple[int, list[str]]:
    """Returns (enrolled_count, failed_emails)."""
    url = f"https://server.smartlead.ai/api/v1/campaigns/{SMARTLEAD_CAMPAIGN_ID}/leads"
    enrolled = 0
    failed = []

    for i in range(0, len(contacts), 20):
        batch = contacts[i:i+20]
        lead_list = []
        for c in batch:
            lead = {
                "email": c["email"],
                "first_name": c.get("first_name", ""),
                "last_name": c.get("last_name", ""),
                "company_name": c.get("company_name", ""),
            }
            custom = {}
            if c.get("title"):
                custom["title"] = c["title"]
            if c.get("linkedin_url"):
                custom["linkedin_url"] = c["linkedin_url"]
            if custom:
                lead["custom_fields"] = custom
            lead_list.append(lead)

        payload = {
            "lead_list": lead_list,
            "settings": {
                "ignore_global_block_list": False,
                "ignore_unsubscribe_list": False,
                "ignore_community_bounce_list": False,
            },
        }

        resp = requests.post(
            url,
            params={"api_key": SMARTLEAD_API_KEY},
            json=payload,
            timeout=30,
        )

        if resp.ok:
            result = resp.json()
            # Smartlead returns upload_count or similar
            print(f"  [OK] Smartlead batch {i//20 + 1}: enrolled {len(batch)} leads | response: {json.dumps(result)[:200]}")
            enrolled += len(batch)
        else:
            print(f"  [ERR] Smartlead batch {i//20 + 1} failed: {resp.status_code} {resp.text[:300]}")
            failed.extend([c["email"] for c in batch])

        time.sleep(0.5)

    return enrolled, failed


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("=== ECAS: Approve & Enroll Pending Contacts ===\n")

    # Step 1: Fetch
    print("Step 1: Fetching pending_review contacts from Airtable...")
    records = fetch_pending_contacts()
    print(f"  Found {len(records)} pending_review records\n")

    if not records:
        print("Nothing to do.")
        return

    # Step 2: Filter to contacts WITH email
    with_email = []
    skipped_no_email = []
    for rec in records:
        fields = rec.get("fields", {})
        email = (fields.get("email") or "").strip()
        if email:
            with_email.append({
                "record_id": rec["id"],
                "email": email,
                "first_name": fields.get("first_name", ""),
                "last_name": fields.get("last_name", ""),
                "company_name": fields.get("company_name", ""),
                "title": fields.get("title", ""),
                "linkedin_url": fields.get("linkedin_url", ""),
            })
        else:
            skipped_no_email.append(rec["id"])

    print(f"Step 2: Email filter")
    print(f"  With email:    {len(with_email)}")
    print(f"  Missing email: {len(skipped_no_email)} (skipped)\n")

    if not with_email:
        print("No contacts with email addresses to process.")
        return

    # Step 3: Mark approved in Airtable
    print(f"Step 3: Updating {len(with_email)} contacts → 'approved' in Airtable...")
    approved_ids = [c["record_id"] for c in with_email]
    airtable_update_status(approved_ids, "approved")
    print(f"  Done — {len(approved_ids)} contacts marked approved\n")

    # Step 4: Enroll in Smartlead
    print(f"Step 4: Enrolling {len(with_email)} contacts in Smartlead campaign {SMARTLEAD_CAMPAIGN_ID}...")
    enrolled_count, failed_emails = smartlead_enroll(with_email)
    print(f"  Enrolled: {enrolled_count} | Failed: {len(failed_emails)}\n")

    # Step 5: Mark in_sequence (only successfully enrolled ones)
    successfully_enrolled = [
        c["record_id"] for c in with_email
        if c["email"] not in failed_emails
    ]

    if successfully_enrolled:
        print(f"Step 5: Updating {len(successfully_enrolled)} contacts → 'in_sequence' in Airtable...")
        airtable_update_status(successfully_enrolled, "in_sequence")
        print(f"  Done\n")

    # Summary
    print("=" * 50)
    print("SUMMARY")
    print(f"  Total pending_review found:  {len(records)}")
    print(f"  Skipped (no email):          {len(skipped_no_email)}")
    print(f"  Approved in Airtable:        {len(approved_ids)}")
    print(f"  Enrolled in Smartlead:       {enrolled_count}")
    print(f"  Marked in_sequence:          {len(successfully_enrolled)}")
    if failed_emails:
        print(f"  Failed enrollment emails:    {', '.join(failed_emails)}")
    print("=" * 50)


if __name__ == "__main__":
    main()
