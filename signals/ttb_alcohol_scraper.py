import csv
import io
import urllib.request
from tools.domain_resolver import resolve_domain
from tools.contact_finder import find_contacts_for_domain
from tools.verify_cascade import verify_email_cascade
from tools.n8n_router import route_lead_to_n8n, send_discord_alert, sync_dead_letter_queue_to_airtable
from tools.seen_tracker import SeenTracker
from config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID

# TTB overwrites this file in place each Monday ("updates posted weekly"); the
# 2025-04 directory in the path is frozen and does NOT indicate stale data.
TTB_INCREMENTAL_CSV = (
    "https://www.ttb.gov/system/files/2025-04/"
    "FRL_Basic_Permits_Issued_Since_the_Last_Publication.csv"
)


def parse_ttb_permits(csv_text: str) -> list[dict]:
    """Parse the TTB "permits issued since last publication" CSV.

    TTB serves a malformed CSV: only the header line is newline-terminated, then
    every data record is comma-concatenated onto ONE physical line. A naive
    split("\\n") sees a single giant row and keeps only the first permit (the
    original bug: 1 of 142 captured). Column count is fixed by the header, so we
    flatten all data fields and re-chunk by column count.
    """
    if not csv_text.strip():
        return []
    rows = list(csv.reader(io.StringIO(csv_text)))
    if len(rows) < 2:
        return []
    header = rows[0]
    ncol = len(header)
    if ncol < 9:
        return []
    flat = [f for row in rows[1:] for f in row]
    permits = []
    for i in range(0, len(flat) - ncol + 1, ncol):
        rec = flat[i:i + ncol]
        owner_name = rec[1].strip()
        operating_name = rec[2].strip()
        company_name = operating_name or owner_name
        if not company_name or company_name.lower() in ("owner_name", "operating_name"):
            continue
        permits.append({
            "company_name": company_name,
            "permit_type": rec[8].strip(),
            "state": rec[5].strip(),
            "city": rec[4].strip(),
            "permit_number": rec[0].strip(),
        })
    return permits


def scrape_active_ttb_permits() -> list[dict]:
    """Download the current TTB incremental permit CSV and parse it.

    File is overwritten weekly in place, so the URL is stable. Covers FAA Basic
    Permit holders: distilleries (Distilled Spirits Plant), wholesalers,
    importers, wine producers. NOTE: breweries are NOT in this source (separate
    Brewer's Notice registry)."""
    print("=== Scraping TTB.gov Newly Issued Alcohol Permits ===")
    req = urllib.request.Request(
        TTB_INCREMENTAL_CSV,
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            csv_data = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  [Error] TTB CSV download failed: {e}")
        return []
    permits = parse_ttb_permits(csv_data)
    print(f"  [Success] Parsed {len(permits)} newly issued TTB permits")
    return permits


def run_ttb_outbound_pipeline():
    """Process newly issued TTB permits, resolve domains, find Owners/Makers,
    route to Smartlead. Dedups on permit number so the same permit is never
    routed twice across weekly runs."""
    permits = scrape_active_ttb_permits()
    if not permits:
        return

    seen = SeenTracker("ttb_leads_seen")

    for p in permits:
        dedup_key = f"ttb::{p['permit_number'] or p['company_name']}"
        if seen.is_seen(dedup_key):
            continue

        company_name = p["company_name"]
        print(f"Processing New Permit: {company_name} | Type: {p['permit_type']} | Location: {p['city']}, {p['state']}")

        domain = resolve_domain(company_name)
        if not domain:
            sync_dead_letter_queue_to_airtable(p, "Domain not resolved", AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
            seen.mark_seen(dedup_key)
            continue

        target_titles = ["Founder", "Owner", "Head Distiller", "General Manager"]
        contacts = find_contacts_for_domain(domain, target_titles)
        if not contacts:
            sync_dead_letter_queue_to_airtable({"company_name": company_name, "domain": domain}, "No contacts found", AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
            seen.mark_seen(dedup_key)
            continue

        for c in contacts:
            email = c.get("email")
            status, source = verify_email_cascade(email)

            c["verification_status"] = status
            c["source"] = source
            c["sector"] = "Craft Spirits & Beverage Logistics"
            c["custom_fields"] = {
                "permit_type": p["permit_type"],
                "state": p["state"],
                "city": p["city"],
            }

            if status in ["verified_clean", "catch_all_verified"]:
                print(f"  [Success] routing {email} ({status}) for newly issued {p['permit_type']} permit to Smartlead")
                route_lead_to_n8n(c)
            else:
                sync_dead_letter_queue_to_airtable(c, f"Email verification returned: {status}", AIRTABLE_API_KEY, AIRTABLE_BASE_ID)

        seen.mark_seen(dedup_key)


if __name__ == "__main__":
    run_ttb_outbound_pipeline()
