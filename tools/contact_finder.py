import json
import urllib.request
from config import APOLLO_API_KEY

def find_contacts_for_domain(domain: str, titles: list[str], api_key: str = APOLLO_API_KEY) -> list[dict]:
    """Find corporate decision-makers matching titles for a domain using Apollo API."""
    if not domain or not api_key:
        return []
        
    url = "https://api.apollo.io/v1/people/search"
    payload = {
        "api_key": api_key,
        "q_organization_domains": domain,
        "person_titles": titles,
        "page": 1,
        "per_page": 5
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "no-cache"
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
            results = []
            for person in data.get("people", []):
                results.append({
                    "first_name": person.get("first_name"),
                    "last_name": person.get("last_name"),
                    "title": person.get("title"),
                    "email": person.get("email"),
                    "linkedin_url": person.get("linkedin_url"),
                    "company_name": person.get("organization", {}).get("name")
                })
            return results
    except Exception as e:
        print(f"[Error] Apollo Contact lookup failed for domain {domain}: {e}")
        return []
