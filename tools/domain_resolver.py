import json
import urllib.request
import urllib.parse as up
import re
from config import SERPAPI_API_KEY

def extract_domain_from_url(url: str) -> str | None:
    if not url or not isinstance(url, str):
        return None
    match = re.search(r"https?://(?:www\.)?([^/]+)", url)
    return match.group(1).lower() if match else None

def resolve_domain(company_name: str, api_key: str = SERPAPI_API_KEY) -> str | None:
    """Look up website domain for a company name using SerpAPI with fallbacks."""
    if not company_name:
        return None
        
    query = f"{company_name} corporate website"
    
    # 1. Primary path: SerpAPI Google search
    if api_key:
        try:
            url = f"https://serpapi.com/search.json?q={up.quote(query)}&engine=google&api_key={api_key}"
            req = urllib.request.Request(url, headers={"User-Agent": "ECAS-Domain-Resolver/1.0"})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                results = data.get("organic_results", [])
                if results and len(results) > 0:
                    link = results[0].get("link")
                    if link:
                        domain = extract_domain_from_url(link)
                        if domain and "google.com" not in domain:
                            return domain
        except Exception as e:
            print(f"[Warning] SerpAPI lookup failed for {company_name}: {e}. Falling back to DuckDuckGo HTML scraper.")

    # 2. Fallback path: DuckDuckGo HTML Scraper
    try:
        ddg_url = f"https://html.duckduckgo.com/html/?q={up.quote(query)}"
        req = urllib.request.Request(ddg_url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode("utf-8", errors="ignore")
            # Pull first few result URLs from DDG layout
            links = re.findall(r'class="result__url"[^>]*href="([^"]+)"', html)
            for link in links:
                # Decrypt direct DDG outgoing redirects if needed
                match = re.search(r"uddg=([^&]+)", link)
                actual_url = up.unquote(match.group(1)) if match else link
                domain = extract_domain_from_url(actual_url)
                if domain and not any(sub in domain for sub in ["duckduckgo.com", "google.com", "bing.com"]):
                    return domain
    except Exception as e:
        print(f"[Error] Fallback DuckDuckGo scraper failed for {company_name}: {e}")
        
    return None
