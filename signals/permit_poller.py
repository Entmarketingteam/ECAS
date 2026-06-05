import json
import urllib.request
from tools.domain_resolver import resolve_domain
from tools.contact_finder import find_contacts_for_domain
from tools.verify_cascade import verify_email_cascade
from tools.n8n_router import route_lead_to_n8n, send_discord_alert, sync_dead_letter_queue_to_airtable
from config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID

def parse_municipal_permits(raw_records: list) -> list[dict]:
    results = []
    for r in raw_records:
        val_str = r.get("valuation", "0")
        try:
            val = float(val_str)
        except ValueError:
            val = 0.0
            
        comp_name = r.get("contractor_name")
        if comp_name and val >= 100000.0:
            results.append({
                "company_name": comp_name,
                "valuation": val,
                "permit_num": r.get("permit_num"),
                "details": r.get("permit_type", "Residential Remodel")
            })
    return results

def poll_and_enrich_permits():
    """Poll Socrata open permit API for DFW, enrich corporate details, and enroll deliverable contacts."""
    print("=== Polling Municipal Permits (Collin County/Plano) ===")
    # Using open Plano building permit feed
    url = "https://data.plano.gov/resource/7978-szp9.json?$limit=10&$order=issued_date%20DESC"
    req = urllib.request.Request(url, headers={"User-Agent": "ECAS-Permit-Poller/1.0"})
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            raw_data = json.loads(response.read().decode())
            permits = parse_municipal_permits(raw_data)
            print(f"  Found {len(permits)} new high-valuation permit opportunities (>100k)")
            
            for p in permits:
                print(f"Processing: {p['company_name']} (${p['valuation']})")
                # 1. Resolve Corporate Website Domain
                domain = resolve_domain(p["company_name"])
                if not domain:
                    err = "Domain not resolved"
                    sync_dead_letter_queue_to_airtable(p, err, AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
                    continue
                
                # 2. Query Apollo for Custom Builder Decision-Makers
                target_titles = ["Owner", "President", "VP of Construction", "Chief Estimator", "Project Executive"]
                contacts = find_contacts_for_domain(domain, target_titles)
                if not contacts:
                    err = "Decision-maker contacts not found"
                    p["domain"] = domain
                    sync_dead_letter_queue_to_airtable(p, err, AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
                    continue
                    
                # 3. Email Cascade Verification
                for c in contacts:
                    email = c.get("email")
                    status, source = verify_email_cascade(email)
                    c["verification_status"] = status
                    c["source"] = source
                    c["sector"] = "Custom Builders"
                    c["parent_project_valuation"] = p["valuation"]
                    c["parent_project_num"] = p["permit_num"]
                    
                    if status in ["verified_clean", "catch_all_verified"]:
                        # 4. Success -> Post to n8n router for instant enrollment
                        print(f"  [Success] routing {email} ({status}) to Smartlead")
                        route_lead_to_n8n(c)
                    else:
                        print(f"  [Failed] {email} was flagged as {status}")
                        sync_dead_letter_queue_to_airtable(c, f"Email verification returned: {status}", AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
                        
    except Exception as e:
        print(f"[Error] Permit poller execution failed: {e}")
        send_discord_alert(f"🚨 *CRITICAL SCRAPER EXCEPTION*: Permit poller script stopped unexpectedly. Error: {e}")

if __name__ == "__main__":
    poll_and_enrich_permits()
