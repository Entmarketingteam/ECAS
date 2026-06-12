import urllib.request
import urllib.parse
import re
import json
import xml.etree.ElementTree as ET
from tools.domain_resolver import resolve_domain
from tools.contact_finder import find_contacts_for_domain
from tools.verify_cascade import verify_email_cascade
from tools.n8n_router import route_lead_to_n8n, send_discord_alert, sync_dead_letter_queue_to_airtable
from tools.seen_tracker import SeenTracker
from config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID

# Discovery source: FMCSA Company Census via Socrata (no API key needed). This
# is the missing front-half — it yields ICP DOT numbers; the SAFER per-DOT HTML
# scrape below is now only a fallback (census already carries power_units).
SOCRATA_CENSUS_URL = "https://data.transportation.gov/resource/az4n-8mr2.json"


def build_icp_where(min_pu: int = 5, max_pu: int = 50, states=None, since_date: str = None) -> str:
    """Build the Socrata SoQL $where clause for ICP carriers.

    power_units is stored as text in the census, so it must be cast to number.
    status_code='A' is mandatory — 42% of the raw 5-50 band are Inactive.
    carrier_operation='A' restricts to interstate (the clean cold-email ICP).
    """
    clauses = [
        f"(power_units::number) >= {min_pu}",
        f"(power_units::number) <= {max_pu}",
        "status_code = 'A'",
        "carrier_operation = 'A'",
        "phy_country = 'US'",
    ]
    if states:
        joined = ", ".join(f"'{s}'" for s in states)
        clauses.append(f"phy_state in ({joined})")
    if since_date:
        clauses.append(f"mcs150_date > '{since_date}'")
    return " AND ".join(clauses)


def discover_icp_carriers(min_pu: int = 5, max_pu: int = 50, states=None,
                          since_date: str = None, max_records: int = 500) -> list[dict]:
    """Query the census for ICP carriers. Returns census rows (already carrying
    dot_number + power_units + name + state + email), capped at max_records to
    keep scheduled volume sane (the unbounded active band is ~230k)."""
    where = build_icp_where(min_pu, max_pu, states, since_date)
    select = "dot_number,legal_name,dba_name,power_units,phy_state,email_address,phone,mcs150_date"
    rows, offset, page = [], 0, 1000
    while len(rows) < max_records:
        limit = min(page, max_records - len(rows))
        qs = urllib.parse.urlencode({
            "$where": where, "$select": select,
            "$order": "mcs150_date DESC", "$limit": limit, "$offset": offset,
        })
        req = urllib.request.Request(
            f"{SOCRATA_CENSUS_URL}?{qs}",
            headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                batch = json.loads(resp.read().decode("utf-8", errors="ignore"))
        except Exception as e:
            print(f"  [Error] FMCSA census query failed: {e}")
            break
        if not batch:
            break
        rows.extend(batch)
        offset += len(batch)
        if len(batch) < limit:
            break
    return rows[:max_records]


def run_fmcsa_discovery_pipeline(states=None, since_date: str = None, max_records: int = 500):
    """Discover ICP carriers from the census, dedup on DOT number, resolve
    domains, find decision-makers, route to Smartlead. Uses census power_units
    directly — no SAFER scrape needed for the filter."""
    print("=== FMCSA Fleet Discovery (census) ===")
    carriers = discover_icp_carriers(states=states, since_date=since_date, max_records=max_records)
    if not carriers:
        print("  No ICP carriers returned.")
        return

    seen = SeenTracker("fmcsa_leads_seen")

    for car in carriers:
        dot = car.get("dot_number")
        dedup_key = f"fmcsa_census::{dot}"
        if seen.is_seen(dedup_key):
            continue

        company_name = (car.get("dba_name") or car.get("legal_name") or "").strip()
        power_units = car.get("power_units")
        if not company_name:
            seen.mark_seen(dedup_key)
            continue

        print(f"Found Carrier: {company_name} | DOT {dot} | Power Units {power_units}")

        domain = resolve_domain(company_name)
        if not domain:
            sync_dead_letter_queue_to_airtable({"company_name": company_name, "dot_number": dot}, "Domain not resolved", AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
            seen.mark_seen(dedup_key)
            continue

        target_titles = ["Owner", "President", "Operations Director", "Fleet Manager", "General Manager"]
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
            c["sector"] = "Fleet Logistics & Pest Control"
            c["custom_fields"] = {"truck_count": str(power_units), "dot_number": dot}

            if status in ["verified_clean", "catch_all_verified"]:
                print(f"  [Success] routing {email} ({status}) with {power_units} trucks to Smartlead")
                route_lead_to_n8n(c)
            else:
                sync_dead_letter_queue_to_airtable(c, f"Email verification returned: {status}", AIRTABLE_API_KEY, AIRTABLE_BASE_ID)

        seen.mark_seen(dedup_key)

def scrape_fmcsa_carrier_by_dot(dot_number: str) -> dict:
    """
    Query the FMCSA SAFER system Company Snapshot for a carrier's active fleet size.
    Uses the stable public query.asp endpoint.
    """
    print(f"  [SAFER] Querying DOT: {dot_number}")
    url = "https://safer.fmcsa.dot.gov/query.asp"
    
    # Format the exact POST parameters expected by query.asp
    params = {
        "searchtype": "ANY",
        "query_type": "queryCarrierSnapshot",
        "query_param": "USDOT",
        "query_string": str(dot_number)
    }
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode("utf-8", errors="ignore")
            
            # Extract carrier legal name from page title
            name_match = re.search(r'<TITLE>SAFER Web - Company Snapshot\s+([^<]+)</TITLE>', html, re.IGNORECASE)
            carrier_name = name_match.group(1).strip() if name_match else None
            
            # Extract Power Units (Truck Count)
            truck_match = re.search(r'PowerUnits">Power Units:</A></TH>\s*<TD class="queryfield"[^>]*>([0-9,]+)&nbsp;</TD>', html, re.DOTALL | re.IGNORECASE)
            power_units = int(truck_match.group(1).replace(",", "")) if truck_match else 0
            
            # Extract Drivers count
            driver_match = re.search(r'Drivers">Drivers:</A></TH>.*?<TD[^>]*>(?:<FONT[^>]*><B>)?([0-9,]+)&nbsp;</TD>', html, re.DOTALL | re.IGNORECASE)
            drivers = int(driver_match.group(1).replace(",", "")) if driver_match else 0
            
            return {
                "company_name": carrier_name,
                "power_units": power_units,
                "drivers": drivers,
                "dot_number": dot_number
            }
    except Exception as e:
        print(f"  [Error] FMCSA DOT query failed for {dot_number}: {e}")
        return None

def process_fmcsa_fleets(dot_list: list[str]):
    """
    Core pipeline: Takes a list of DOT numbers (from SAFER registry scrapes),
    resolves domains, finds key decision-makers, runs email cascade, and routes to Smartlead/n8n.
    """
    print("=== Launching FMCSA Fleet Signal Processing ===")
    
    for dot in dot_list:
        carrier = scrape_fmcsa_carrier_by_dot(dot)
        if not carrier or not carrier["company_name"]:
            continue
            
        print(f"Found Carrier: {carrier['company_name']} | Trucks (Power Units): {carrier['power_units']}")
        
        # ICP Threshold: Only target companies with 5 to 50 active route trucks (Power Units)
        if not (5 <= carrier["power_units"] <= 50):
            print(f"  [Filtered] Truck count {carrier['power_units']} outside ICP range (5-50)")
            continue
            
        domain = resolve_domain(carrier["company_name"])
        if not domain:
            sync_dead_letter_queue_to_airtable(carrier, "Domain not resolved", AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
            continue
            
        # Target Decision Makers for route-based businesses
        target_titles = ["Owner", "President", "Operations Director", "Fleet Manager", "General Manager"]
        contacts = find_contacts_for_domain(domain, target_titles)
        if not contacts:
            sync_dead_letter_queue_to_airtable({"company_name": carrier["company_name"], "domain": domain}, "No contacts found", AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
            continue
            
        for c in contacts:
            email = c.get("email")
            status, source = verify_email_cascade(email)
            
            c["verification_status"] = status
            c["source"] = source
            c["sector"] = "Fleet Logistics & Pest Control"
            c["custom_fields"] = {
                "truck_count": str(carrier["power_units"]),
                "dot_number": dot
            }
            
            if status in ["verified_clean", "catch_all_verified"]:
                print(f"  [Success] routing {email} ({status}) with {carrier['power_units']} trucks to Smartlead")
                route_lead_to_n8n(c)
            else:
                sync_dead_letter_queue_to_airtable(c, f"Email verification returned: {status}", AIRTABLE_API_KEY, AIRTABLE_BASE_ID)

if __name__ == "__main__":
    import sys
    # With DOT args: enrich those specific carriers via SAFER (manual path).
    # No args: run census discovery (the real scheduled/on-demand entry).
    if len(sys.argv) > 1:
        dots_to_process = sys.argv[1:]
        print(f"Processing command-line USDOT numbers: {dots_to_process}")
        process_fmcsa_fleets(dots_to_process)
    else:
        run_fmcsa_discovery_pipeline()
