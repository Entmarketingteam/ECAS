import json
from tools.domain_resolver import resolve_domain
from tools.contact_finder import find_contacts_for_domain
from tools.verify_cascade import verify_email_cascade
from tools.n8n_router import route_lead_to_n8n, sync_dead_letter_queue_to_airtable
from config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID

def load_commercial_shredding_leads(raw_lists: list[dict]):
    """Loads target lists (law firms, medical clinics) requiring recurring document destruction."""
    print("=== Loading Commercial Shredding Lead Targets ===")
    for item in raw_lists:
        company_name = item.get("company_name")
        print(f"Targeting: {company_name}")
        
        domain = resolve_domain(company_name)
        if not domain:
            sync_dead_letter_queue_to_airtable({"company_name": company_name}, "Domain not resolved", AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
            continue
            
        target_titles = ["Office Manager", "Facilities Manager", "HR Director", "General Counsel"]
        contacts = find_contacts_for_domain(domain, target_titles)
        if not contacts:
            sync_dead_letter_queue_to_airtable({"company_name": company_name, "domain": domain}, "No contacts found", AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
            continue
            
        for c in contacts:
            email = c.get("email")
            status, source = verify_email_cascade(email)
            c["verification_status"] = status
            c["source"] = source
            c["sector"] = "Document Destruction"
            
            if status in ["verified_clean", "catch_all_verified"]:
                print(f"  [Success] routing {email} ({status}) to Smartlead")
                route_lead_to_n8n(c)
            else:
                sync_dead_letter_queue_to_airtable(c, f"Email verification returned: {status}", AIRTABLE_API_KEY, AIRTABLE_BASE_ID)

if __name__ == "__main__":
    # Test dataset mapping regional law firms and clinics
    dummy_leads = [
        {"company_name": "Dallas Premium Legal Partners"},
        {"company_name": "DFW Family Medical Center"}
    ]
    load_commercial_shredding_leads(dummy_leads)
