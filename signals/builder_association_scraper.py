import re
import urllib.request
from tools.domain_resolver import resolve_domain
from tools.contact_finder import find_contacts_for_domain
from tools.verify_cascade import verify_email_cascade
from tools.n8n_router import route_lead_to_n8n, send_discord_alert, sync_dead_letter_queue_to_airtable
from config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID

def parse_association_page(html: str) -> list[str]:
    # Match Dallas BA directory layout pattern
    matches = re.findall(r'<h3><a[^>]*>([^<]+)</a></h3>', html)
    return [m.strip() for m in matches if m.strip()]

def scrape_and_enrich_association_builders():
    """Scrape Dallas Builders Association member directory, resolve corporate links, find contacts and verify."""
    print("=== Scraping Dallas Builders Association ===")
    url = "https://dallasbuilders.org/member-directory/?category=Builders"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})
    
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            html = response.read().decode("utf-8", errors="ignore")
            builders = parse_association_page(html)
            print(f"  Crawled {len(builders)} builder profiles")
            
            for b_name in builders:
                print(f"Processing Profile: {b_name}")
                domain = resolve_domain(b_name)
                if not domain:
                    sync_dead_letter_queue_to_airtable({"company_name": b_name}, "Domain not resolved", AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
                    continue
                    
                target_titles = ["Owner", "President", "VP of Construction", "Chief Estimator"]
                contacts = find_contacts_for_domain(domain, target_titles)
                if not contacts:
                    sync_dead_letter_queue_to_airtable({"company_name": b_name, "domain": domain}, "No contacts found", AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
                    continue
                    
                for c in contacts:
                    email = c.get("email")
                    status, source = verify_email_cascade(email)
                    c["verification_status"] = status
                    c["source"] = source
                    c["sector"] = "Custom Builders"
                    
                    if status in ["verified_clean", "catch_all_verified"]:
                        print(f"  [Success] routing {email} ({status}) to Smartlead")
                        route_lead_to_n8n(c)
                    else:
                        sync_dead_letter_queue_to_airtable(c, f"Email verification returned: {status}", AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
                        
    except Exception as e:
        print(f"[Error] Association scraper failed: {e}")
        send_discord_alert(f"🚨 *CRITICAL SCRAPER EXCEPTION*: Builder Association scraper stopped. Error: {e}")

if __name__ == "__main__":
    scrape_and_enrich_association_builders()
