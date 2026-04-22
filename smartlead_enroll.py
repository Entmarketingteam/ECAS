#!/opt/homebrew/bin/python3.13
"""
Enroll pending_review ECAS contacts into Smartlead campaigns based on project sector.
"""

import os
import json
import time
import urllib.request
import urllib.parse as up
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

AIRTABLE_KEY = os.environ["AIRTABLE_API_KEY"]
SMARTLEAD_KEY = os.environ.get("SMARTLEAD_API_KEY", "")
if not SMARTLEAD_KEY:
    raise ValueError("SMARTLEAD_API_KEY not set")
BASE_ID = "appoi8SzEJY8in57x"
CONTACTS_TABLE = "tblPBvTBuhwlS8AnS"
PROJECTS_TABLE = "tbloen0rEkHttejnC"

# Sector → Campaign mapping
SECTOR_CAMPAIGN = {
    "Power & Grid Infrastructure": 3005694,
    "Data Center & AI Infrastructure": 3040599,
    "Water & Wastewater Infrastructure": 3040600,
    "Industrial & Manufacturing Facilities": 3040601,
    "Defense": 3005694,
}
DEFAULT_CAMPAIGN = 3005694


def airtable_get_all(table_id, filter_formula=None, fields=None):
    """Fetch all records from an Airtable table with pagination."""
    records = []
    offset = None
    while True:
        params_list = [("pageSize", "100")]
        if filter_formula:
            params_list.append(("filterByFormula", filter_formula))
        if fields:
            for f in fields:
                params_list.append(("fields[]", f))
        if offset:
            params_list.append(("offset", offset))
        url = f"https://api.airtable.com/v0/{BASE_ID}/{table_id}?" + up.urlencode(params_list)
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {AIRTABLE_KEY}"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
        records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
    return records


def airtable_patch(table_id, record_id, fields):
    """PATCH a single Airtable record."""
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table_id}/{record_id}"
    payload = json.dumps({"fields": fields}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        method="PATCH",
        headers={
            "Authorization": f"Bearer {AIRTABLE_KEY}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


BROWSER_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def smartlead_enroll_batch(campaign_id, leads):
    """Enroll a batch of leads into a Smartlead campaign. Returns (result, error)."""
    url = f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}/leads?api_key={SMARTLEAD_KEY}"
    payload = json.dumps({
        "lead_list": leads,
        "settings": {
            "ignore_global_block_list": False,
            "ignore_unsubscribe_list": False,
            "ignore_community_bounce_list": False,
        }
    }).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": BROWSER_UA,
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
        return result, None
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return None, f"HTTP {e.code}: {body}"
    except Exception as e:
        return None, str(e)


def get_campaign_for_sector(scope_summary):
    """Map a project's scope_summary to a campaign ID and label."""
    if not scope_summary:
        return DEFAULT_CAMPAIGN, "No sector (default)"
    for sector, cid in SECTOR_CAMPAIGN.items():
        if sector.lower() in scope_summary.lower():
            return cid, sector
    return DEFAULT_CAMPAIGN, f"Other: {scope_summary[:60]}"


def main():
    print("=== ECAS Smartlead Enrollment ===\n")

    # Step 1: Fetch all pending_review contacts with email
    print("Fetching pending_review contacts...")
    contacts = airtable_get_all(
        CONTACTS_TABLE,
        filter_formula="outreach_status='pending_review'",
        fields=["email", "first_name", "last_name", "company_name", "title",
                "linkedin_url", "projects", "outreach_status"],
    )
    # Filter to those with email
    contacts = [c for c in contacts if c.get("fields", {}).get("email")]
    print(f"  Found {len(contacts)} pending_review contacts with email\n")

    if not contacts:
        print("Nothing to enroll.")
        return

    # Step 2: Collect all unique project IDs and fetch them in parallel
    project_ids = set()
    for c in contacts:
        proj_links = c.get("fields", {}).get("projects", [])
        if proj_links:
            # Use first linked project
            project_ids.add(proj_links[0])

    print(f"Fetching {len(project_ids)} linked projects...")

    project_sector = {}  # project_record_id → (campaign_id, sector_label)

    def fetch_project(proj_id):
        # No fields[] filter on individual record endpoint — it causes 422
        url = f"https://api.airtable.com/v0/{BASE_ID}/{PROJECTS_TABLE}/{proj_id}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {AIRTABLE_KEY}"})
        try:
            with urllib.request.urlopen(req) as resp:
                rec = json.loads(resp.read())
            scope = rec.get("fields", {}).get("scope_summary", "")
            return proj_id, scope
        except Exception as e:
            print(f"  Warning: could not fetch project {proj_id}: {e}")
            return proj_id, ""

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(fetch_project, pid): pid for pid in project_ids}
        for fut in as_completed(futures):
            pid, scope = fut.result()
            cid, label = get_campaign_for_sector(scope)
            project_sector[pid] = (cid, label)

    print(f"  {len(project_sector)} projects mapped.\n")

    # Step 3: Group contacts by campaign
    campaign_groups = defaultdict(list)  # campaign_id → list of (record_id, lead_dict, sector_label)

    for c in contacts:
        fields = c.get("fields", {})
        rec_id = c["id"]
        proj_links = fields.get("projects", [])

        if proj_links:
            cid, label = project_sector.get(proj_links[0], (DEFAULT_CAMPAIGN, "Unknown project"))
        else:
            cid, label = DEFAULT_CAMPAIGN, "No project linked (default)"

        lead = {
            "email": fields.get("email", "").strip(),
            "first_name": fields.get("first_name", ""),
            "last_name": fields.get("last_name", ""),
            "company_name": fields.get("company_name", ""),
            "custom_fields": {
                "title": fields.get("title", ""),
                "linkedin_url": fields.get("linkedin_url", ""),
            }
        }
        campaign_groups[cid].append((rec_id, lead, label))

    # Print routing summary
    print("=== Routing Summary ===")
    for cid, items in campaign_groups.items():
        sector_counts = defaultdict(int)
        for _, _, label in items:
            sector_counts[label] += 1
        print(f"  Campaign {cid}: {len(items)} contacts")
        for label, cnt in sorted(sector_counts.items(), key=lambda x: -x[1]):
            print(f"    - {label}: {cnt}")
    print()

    # Step 4: Enroll in batches of 20 per campaign
    BATCH_SIZE = 20
    total_enrolled = 0
    total_failed = 0
    failed_leads = []
    enrolled_record_ids = []

    for campaign_id, items in campaign_groups.items():
        print(f"Enrolling {len(items)} contacts into campaign {campaign_id}...")
        batches = [items[i:i+BATCH_SIZE] for i in range(0, len(items), BATCH_SIZE)]

        for batch_num, batch in enumerate(batches, 1):
            leads = [lead for _, lead, _ in batch]
            rec_ids = [rec_id for rec_id, _, _ in batch]

            result, err = smartlead_enroll_batch(campaign_id, leads)

            if err:
                print(f"  Batch {batch_num}/{len(batches)} FAILED: {err}")
                total_failed += len(batch)
                failed_leads.extend([(rec_id, lead["email"], err) for rec_id, lead, _ in batch])
            else:
                if isinstance(result, dict):
                    # Smartlead returns upload_count
                    ok_count = result.get("upload_count", len(batch))
                    already_exists = result.get("already_added_to_campaign_count", 0)
                    print(f"  Batch {batch_num}/{len(batches)}: enrolled={ok_count}, already_exists={already_exists} | {json.dumps(result)[:200]}")
                else:
                    ok_count = len(batch)
                    print(f"  Batch {batch_num}/{len(batches)}: {ok_count} enrolled.")
                total_enrolled += len(batch)  # Count all in batch as attempted-success
                enrolled_record_ids.extend(rec_ids)

            time.sleep(0.3)

        print()

    print(f"=== Enrollment Complete: {total_enrolled} sent to Smartlead, {total_failed} failed ===\n")

    # Step 5: Update Airtable status to in_sequence for enrolled contacts
    if enrolled_record_ids:
        print(f"Updating {len(enrolled_record_ids)} Airtable records to 'in_sequence'...")

        update_errors = []
        updated = 0

        def update_record(rec_id):
            try:
                airtable_patch(CONTACTS_TABLE, rec_id, {"outreach_status": "in_sequence"})
                return rec_id, None
            except Exception as e:
                return rec_id, str(e)

        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = {pool.submit(update_record, rid): rid for rid in enrolled_record_ids}
            for fut in as_completed(futures):
                rid, err = fut.result()
                if err:
                    update_errors.append((rid, err))
                else:
                    updated += 1
                if updated % 25 == 0 and updated > 0:
                    print(f"  Updated {updated}/{len(enrolled_record_ids)}...")

        print(f"  Done: {updated} updated, {len(update_errors)} errors.\n")
        if update_errors:
            print("  Update errors:")
            for rid, err in update_errors[:10]:
                print(f"    {rid}: {err}")

    # Final report
    print("=" * 50)
    print("FINAL REPORT")
    print("=" * 50)
    print(f"Total contacts fetched:     {len(contacts)}")
    print(f"Successfully sent to SL:    {total_enrolled}")
    print(f"Failed enrollment:          {total_failed}")
    print(f"Airtable updated:           {len(enrolled_record_ids)}")

    print("\nBreakdown by campaign/sector:")
    for cid, items in sorted(campaign_groups.items()):
        sector_counts = defaultdict(int)
        for _, _, label in items:
            sector_counts[label] += 1
        print(f"\n  Campaign {cid} ({len(items)} total):")
        for label, cnt in sorted(sector_counts.items(), key=lambda x: -x[1]):
            print(f"    {label}: {cnt}")

    if failed_leads:
        print(f"\nFailed enrollments ({len(failed_leads)}):")
        for rec_id, email, err in failed_leads[:20]:
            print(f"  {email}: {err[:100]}")
        if len(failed_leads) > 20:
            print(f"  ... and {len(failed_leads)-20} more")


if __name__ == "__main__":
    main()
