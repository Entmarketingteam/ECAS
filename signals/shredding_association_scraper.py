import re
import urllib.request
from tools.domain_resolver import resolve_domain
from tools.contact_finder import find_contacts_for_domain
from tools.verify_cascade import verify_email_cascade
from tools.n8n_router import (
    route_lead_to_n8n,
    send_discord_alert,
    sync_dead_letter_queue_to_airtable,
    sync_pending_review_to_airtable,
)
from config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID

def parse_shredding_association(html: str) -> list[str]:
    matches = re.findall(r'<div class="member-name"><h2>([^<]+)</h2></div>', html)
    return [m.strip() for m in matches if m.strip()]

def scrape_shredding_members():
    """Scrape regional i-SIGMA secure shredding associations directories for security targets."""
    print("=== Scraping Regional Shredding Directories (i-SIGMA/NAID) ===")
    url = "https://isigmaonline.org/directories/member-directory/"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})
    
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            html = response.read().decode("utf-8", errors="ignore")
            members = parse_shredding_association(html)
            print(f"  Crawled {len(members)} security providers")
            
            for m_name in members:
                print(f"Processing: {m_name}")
                domain = resolve_domain(m_name)
                if not domain:
                    sync_dead_letter_queue_to_airtable({"company_name": m_name}, "Domain not resolved", AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
                    continue
                    
                target_titles = ["Office Manager", "VP Operations", "HR Director", "Facilities Manager", "General Counsel"]
                contacts = find_contacts_for_domain(domain, target_titles)
                if not contacts:
                    sync_dead_letter_queue_to_airtable({"company_name": m_name, "domain": domain}, "No contacts found", AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
                    continue
                    
                for c in contacts:
                    email = c.get("email")
                    status, source = verify_email_cascade(email)
                    c["verification_status"] = status
                    c["source"] = source
                    c["sector"] = "Document Destruction"
                    
                    if status in ["verified_clean", "catch_all_verified"]:
                        print(f"  [Review] queueing {email} ({status}) for manual approval")
                        sync_pending_review_to_airtable(
                            c,
                            "Verified Document Destruction lead queued for manual approval before Smartlead enrollment",
                            AIRTABLE_API_KEY,
                            AIRTABLE_BASE_ID,
                        )
                    else:
                        sync_dead_letter_queue_to_airtable(c, f"Email verification returned: {status}", AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
                        
    except Exception as e:
        print(f"[Error] Shredding association crawler failed: {e}")
        send_discord_alert(f"🚨 *CRITICAL SCRAPER EXCEPTION*: Shredding scraper stopped unexpectedly. Error: {e}")

if __name__ == "__main__":
    scrape_shredding_members()
