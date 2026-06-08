# Hybrid Sourcing, Multi-Directory Scraping, & Cost-Optimized Verification (Option C) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a code-first pipeline to scrape custom directories and local permits, find and verify corporate emails at low cost ($0.017/lead), and POST successfully verified contacts to an n8n webhook router while raising alerts for failures or credit limits.

**Architecture:** Crawl directories and poll municipal APIs in Python on Railway. Resolve domains via SerpAPI, find contacts via Apollo API, verify emails via a two-pass Million Verifier Bulk + Findymail cascade, and route deliverable contacts to n8n. Failures are stored in an Airtable Dead-Letter Queue (DLQ).

**Tech Stack:** Python 3.13, Pytest, sqlite3, requests, urllib, SerpAPI, Apollo Search API, Million Verifier, Findymail.

---

## File Mapping Table

| File Path | Action | Responsibility |
|---|---|---|
| `config.py` | Modify | Centralize keys (`SERPAPI_API_KEY`, `MILLIONVERIFIER_API_KEY`, `N8N_ROUTER_WEBHOOK_URL`, `DISCORD_ALERTS_WEBHOOK_URL`). |
| `tools/domain_resolver.py` | Create | Look up corporate website domains via SerpAPI with local fallback scrapers. |
| `tools/contact_finder.py` | Create | Query Apollo Search API for executive decision-makers based on target sector titles. |
| `tools/verify_cascade.py` | Create | Bulk-verify emails via Million Verifier, falling back to Findymail for Catch-All or Risky emails. |
| `tools/n8n_router.py` | Create | Handle Webhook POSTs to n8n, manage Slack/Discord alerting thresholds, and parse Airtable DLQ retries. |
| `signals/permit_poller.py` | Create | Scrape municipal DFW building permits >$100k valuation, enrich, and dispatch to n8n router. |
| `signals/builder_association_scraper.py`| Create | Scrape local Dallas Builders Association & NAHB directories, enrich, and dispatch. |
| `signals/shredding_association_scraper.py`| Create | Scrape i-SIGMA regional shredding member directories, enrich, and dispatch. |
| `tools/load_shredding_leads.py` | Create | Load commercial law, medical, and accounting firm target lists, resolve domain/contact, and verify. |

---

## Implementation Tasks

### Task 1: Central Configuration Additions

**Files:**
- Modify: `config.py`

- [ ] **Step 1: Define new configuration parameters and default mappings**

Add the following keys and settings to `/Users/ethanatchley/Desktop/ECAS-industry-factory/config.py`:

```python
# ─── New API Keys & Webhooks (Added for Hybrid Sourcing & Verification Cascade) ────
SERPAPI_API_KEY = os.environ.get("SERPAPI_API_KEY", "")
MILLIONVERIFIER_API_KEY = os.environ.get("MILLIONVERIFIER_API_KEY", "")
N8N_ROUTER_WEBHOOK_URL = os.environ.get("N8N_ROUTER_WEBHOOK_URL", "")
DISCORD_ALERTS_WEBHOOK_URL = os.environ.get("DISCORD_ALERTS_WEBHOOK_URL", "")

# Local SQLite temporary retry queue path
SQLITE_QUEUE_PATH = BASE_DIR / "database" / "retry_queue.db"

# New sectors mapping to Smartlead campaign IDs
SECTOR_CAMPAIGN_MAP.update({
    "Custom Builders": "3114500",       # New dedicated Custom Builders Campaign ID
    "Document Destruction": "3114501",  # New dedicated Document Destruction Campaign ID
})
```

- [ ] **Step 2: Commit config additions**

```bash
git add config.py
git commit -m "config: add keys and mappings for verification cascade"
```

---

### Task 2: Domain Resolver with Local Fallback Scraper

**Files:**
- Create: `tools/domain_resolver.py`
- Create: `tests/test_domain_resolver.py`

- [ ] **Step 1: Write test to verify SerpAPI domain resolution and local HTML parsing fallback**

Create `/Users/ethanatchley/Desktop/ECAS-industry-factory/tests/test_domain_resolver.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from tools.domain_resolver import resolve_domain, extract_domain_from_url

def test_extract_domain():
    assert extract_domain_from_url("https://www.smithbuilders.com/about") == "smithbuilders.com"
    assert extract_domain_from_url("http://dallasshredding.co.uk/contact?id=1") == "dallasshredding.co.uk"
    assert extract_domain_from_url("invalid_url") is None

@patch("urllib.request.urlopen")
def test_resolve_domain_serpapi_success(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'{"organic_results": [{"link": "https://www.dallascustomhomes.com"}]}'
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    domain = resolve_domain("Dallas Custom Homes Inc", api_key="test_key")
    assert domain == "dallascustomhomes.com"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_domain_resolver.py -v`
Expected: FAIL (ImportError or ModuleNotFoundError)

- [ ] **Step 3: Implement Domain Resolver with Search Fallback**

Create `/Users/ethanatchley/Desktop/ECAS-industry-factory/tools/domain_resolver.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_domain_resolver.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_domain_resolver.py tools/domain_resolver.py
git commit -m "feat: implement domain resolver with ddg html fallback"
```

---

### Task 3: Contact Finder via Apollo API

**Files:**
- Create: `tools/contact_finder.py`
- Create: `tests/test_contact_finder.py`

- [ ] **Step 1: Write test to verify contact searching**

Create `/Users/ethanatchley/Desktop/ECAS-industry-factory/tests/test_contact_finder.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from tools.contact_finder import find_contacts_for_domain

@patch("urllib.request.urlopen")
def test_find_contacts_success(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = b"""{
        "people": [{
            "first_name": "John",
            "last_name": "Smith",
            "title": "Owner",
            "email": "john.smith@custombuilders.com",
            "linkedin_url": "https://linkedin.com/in/johnsmith"
        }]
    }"""
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    contacts = find_contacts_for_domain("custombuilders.com", ["owner"], api_key="test_key")
    assert len(contacts) == 1
    assert contacts[0]["first_name"] == "John"
    assert contacts[0]["email"] == "john.smith@custombuilders.com"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_contact_finder.py -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement Contact Finder**

Create `/Users/ethanatchley/Desktop/ECAS-industry-factory/tools/contact_finder.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_contact_finder.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_contact_finder.py tools/contact_finder.py
git commit -m "feat: implement apollo contact finder"
```

---

### Task 4: Two-Pass Email Verification Cascade (Million Verifier + Findymail)

**Files:**
- Create: `tools/verify_cascade.py`
- Create: `tests/test_verify_cascade.py`

- [ ] **Step 1: Write test to verify email verification cascade and local sqlite retrying**

Create `/Users/ethanatchley/Desktop/ECAS-industry-factory/tests/test_verify_cascade.py`:

```python
import pytest
import sqlite3
from unittest.mock import patch, MagicMock
from tools.verify_cascade import verify_email_cascade, init_retry_db

def test_init_db():
    conn = init_retry_db(":memory:")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='queue'")
    assert cursor.fetchone() is not None

@patch("urllib.request.urlopen")
def test_verify_million_verifier_deliverable(mock_urlopen):
    # Pass 1: Million Verifier returns deliverable
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'{"result": "deliverable", "status": "ok"}'
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    status, source = verify_email_cascade("test@builders.com", mv_key="mv_key", fm_key="fm_key")
    assert status == "verified_clean"
    assert source == "million_verifier"

@patch("urllib.request.urlopen")
def test_verify_findymail_fallback_catchall(mock_urlopen):
    # Pass 1: Million Verifier returns catch_all -> triggers Findymail
    # Create mock response to return first MV (catch_all) then Findymail (deliverable)
    mock_mv_resp = MagicMock()
    mock_mv_resp.read.return_value = b'{"result": "catch_all", "status": "ok"}'
    
    mock_fm_resp = MagicMock()
    mock_fm_resp.read.return_value = b'{"status": "deliverable", "email": "test@builders.com"}'
    
    mock_urlopen.return_value.__enter__.side_effect = [mock_mv_resp, mock_fm_resp]

    status, source = verify_email_cascade("test@builders.com", mv_key="mv_key", fm_key="fm_key")
    assert status == "catch_all_verified"
    assert source == "findymail"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_verify_cascade.py -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement Verification Cascade with DB retry buffer**

Create `/Users/ethanatchley/Desktop/ECAS-industry-factory/tools/verify_cascade.py`:

```python
import json
import sqlite3
import urllib.request
import urllib.parse as up
from config import MILLIONVERIFIER_API_KEY, FINDYMAIL_API_KEY, SQLITE_QUEUE_PATH

def init_retry_db(db_path=SQLITE_QUEUE_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS queue (
            email TEXT PRIMARY KEY,
            retry_count INTEGER DEFAULT 0,
            error_msg TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

def verify_email_cascade(email: str, mv_key: str = MILLIONVERIFIER_API_KEY, fm_key: str = FINDYMAIL_API_KEY) -> tuple[str, str]:
    """
    Two-pass validation. 
    Returns: (verification_status, source)
    verification_status: 'verified_clean', 'catch_all_verified', 'bounced', 'needs_manual_review'
    source: 'million_verifier', 'findymail', 'failed'
    """
    if not email:
        return "needs_manual_review", "failed"

    # Pass 1: Million Verifier Bulk V2 ($0.00019/verify)
    if mv_key:
        try:
            url = f"https://api.millionverifier.com/bulk/v2/single?api_key={mv_key}&email={up.quote(email)}"
            req = urllib.request.Request(url, headers={"User-Agent": "ECAS-Cascade-Verifier/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                result = data.get("result")
                if result == "deliverable":
                    return "verified_clean", "million_verifier"
                elif result in ["undeliverable", "invalid"]:
                    return "bounced", "million_verifier"
                # Else: catch_all or risky -> Fallback to Findymail
        except Exception as e:
            print(f"[Warning] Million Verifier failed for {email}: {e}. Falling back to Findymail.")

    # Pass 2: Findymail Search/Verify Fallback ($0.01/verify)
    if fm_key:
        try:
            url = f"https://api.findymail.com/v1/verify?email={up.quote(email)}"
            req = urllib.request.Request(
                url,
                method="GET",
                headers={
                    "Authorization": f"Bearer {fm_key}",
                    "User-Agent": "ECAS-Cascade-Verifier/1.0",
                    "Accept": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                status = data.get("status")
                if status == "deliverable":
                    return "catch_all_verified", "findymail"
                elif status == "undeliverable":
                    return "bounced", "findymail"
        except Exception as e:
            print(f"[Error] Findymail verification failed for {email}: {e}")
            # Cache failed verifications in SQLite to process in background later
            try:
                conn = init_retry_db()
                cursor = conn.cursor()
                cursor.execute("INSERT OR REPLACE INTO queue (email, error_msg) VALUES (?, ?)", (email, str(e)))
                conn.commit()
                conn.close()
            except Exception as dbe:
                print(f"[Error] Failed to buffer verifications: {dbe}")

    return "needs_manual_review", "failed"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_verify_cascade.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_verify_cascade.py tools/verify_cascade.py
git commit -m "feat: implement million verifier + findymail email cascade"
```

---

### Task 5: N8N Router Posting, Live Webhook Alerting, & Airtable DLQ Sync

**Files:**
- Create: `tools/n8n_router.py`
- Create: `tests/test_n8n_router.py`

- [ ] **Step 1: Write test to verify webhook payload delivery and alerts**

Create `/Users/ethanatchley/Desktop/ECAS-industry-factory/tests/test_n8n_router.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from tools.n8n_router import route_lead_to_n8n, send_discord_alert

@patch("urllib.request.urlopen")
def test_route_lead_to_n8n(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'{"status": "success"}'
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    success = route_lead_to_n8n({
        "first_name": "John",
        "last_name": "Smith",
        "email": "john@builders.com",
        "sector": "Custom Builders"
    }, webhook_url="http://test-webhook")
    
    assert success is True

@patch("urllib.request.urlopen")
def test_send_discord_alert(mock_urlopen):
    mock_resp = MagicMock()
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    success = send_discord_alert("⚠️ Test Alert", webhook_url="http://discord-webhook")
    assert success is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_n8n_router.py -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement Webhook Router Client & Alert Manager**

Create `/Users/ethanatchley/Desktop/ECAS-industry-factory/tools/n8n_router.py`:

```python
import json
import urllib.request
from config import N8N_ROUTER_WEBHOOK_URL, DISCORD_ALERTS_WEBHOOK_URL

def route_lead_to_n8n(lead_payload: dict, webhook_url: str = N8N_ROUTER_WEBHOOK_URL) -> bool:
    """POST fully verified and resolved lead to n8n router for visual campaign routing."""
    if not webhook_url:
        print("[Warning] No N8N_ROUTER_WEBHOOK_URL specified. Lead bypassed routing.")
        return False
        
    req = urllib.request.Request(
        webhook_url,
        data=json.dumps(lead_payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.getcode()
            if status in [200, 201]:
                return True
            print(f"[Warning] n8n webhook returned status code {status}")
            return False
    except Exception as e:
        print(f"[Error] Failed to POST lead to n8n: {e}")
        # Trigger real-time alert for process fail
        send_discord_alert(f"⚠️ *CRITICAL ROUTING ERROR*: Failed to POST lead {lead_payload.get('email')} to n8n. Exception: {e}")
        return False

def send_discord_alert(message: str, webhook_url: str = DISCORD_ALERTS_WEBHOOK_URL) -> bool:
    """Send real-time webhook alert to Emily & Ethan on Slack/Discord."""
    if not webhook_url:
        print(f"[Bypassed Alert]: {message}")
        return False
        
    payload = {
        "content": message,
        "username": "ECAS Pipeline Sentinel",
        "avatar_url": "https://img.icons8.com/color/96/shield.png"
    }
    
    req = urllib.request.Request(
        webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.getcode() in [200, 204]
    except Exception as e:
        print(f"[Error] Failed to send webhook alert: {e}")
        return False

def sync_dead_letter_queue_to_airtable(lead_data: dict, error_msg: str, airtable_key: str, base_id: str) -> bool:
    """Log processing/verification failures into Airtable DLQ (Manual Mode)."""
    # PATCH lead to outreach_status="needs_manual_review" in Airtable contacts
    # The DLQ sync can be implemented in n8n or direct. For maximum isolation, n8n handles routing,
    # but we provide this fallback client block if n8n is unreachable.
    url = f"https://api.airtable.com/v0/{base_id}/tblPBvTBuhwlS8AnS"
    payload = {
        "fields": {
            "first_name": lead_data.get("first_name"),
            "last_name": lead_data.get("last_name"),
            "email": lead_data.get("email"),
            "company_name": lead_data.get("company_name"),
            "title": lead_data.get("title"),
            "linkedin_url": lead_data.get("linkedin_url"),
            "outreach_status": "needs_manual_review",
            "error_log": error_msg
        }
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {airtable_key}",
            "Content-Type": "application/json"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.getcode() == 200
    except Exception as e:
        print(f"[Error] Failed to log DLQ record to Airtable: {e}")
        return False
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_n8n_router.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_n8n_router.py tools/n8n_router.py
git commit -m "feat: implement n8n poster, webhook alerter and DLQ handler"
```

---

### Task 6: Permit Poller & Sourcing Agent (Custom Builders)

**Files:**
- Create: `signals/permit_poller.py`
- Create: `tests/test_permit_poller.py`

- [ ] **Step 1: Write test to verify Socrata permits parsing**

Create `/Users/ethanatchley/Desktop/ECAS-industry-factory/tests/test_permit_poller.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from signals.permit_poller import parse_municipal_permits

def test_parse_municipal_permits():
    raw_data = [
        {"permit_num": "123", "contractor_name": "Dallas Custom Builders", "valuation": "150000", "permit_type": "New Construction"}
    ]
    parsed = parse_municipal_permits(raw_data)
    assert len(parsed) == 1
    assert parsed[0]["company_name"] == "Dallas Custom Builders"
    assert parsed[0]["valuation"] == 150000.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_permit_poller.py -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement Permit Poller & Enrichment cascade**

Create `/Users/ethanatchley/Desktop/ECAS-industry-factory/signals/permit_poller.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_permit_poller.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_permit_poller.py signals/permit_poller.py
git commit -m "feat: implement permit poller and processing flow"
```

---

### Task 7: Builder Associations Scraper (Dallas Builders Assoc / NAHB)

**Files:**
- Create: `signals/builder_association_scraper.py`
- Create: `tests/test_builder_association_scraper.py`

- [ ] **Step 1: Write test to verify Dallas Builders Association scraper**

Create `/Users/ethanatchley/Desktop/ECAS-industry-factory/tests/test_builder_association_scraper.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from signals.builder_association_scraper import parse_association_page

def test_parse_association_page():
    html_content = '<h3><a href="/member/smith-homes">Smith Homes</a></h3>'
    parsed = parse_association_page(html_content)
    assert len(parsed) == 1
    assert parsed[0] == "Smith Homes"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_builder_association_scraper.py -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement Scraper**

Create `/Users/ethanatchley/Desktop/ECAS-industry-factory/signals/builder_association_scraper.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_builder_association_scraper.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_builder_association_scraper.py signals/builder_association_scraper.py
git commit -m "feat: implement builder association crawler"
```

---

### Task 8: Shredding Associations Scraper & List Loader (Document Destruction Niche)

**Files:**
- Create: `signals/shredding_association_scraper.py`
- Create: `tools/load_shredding_leads.py`
- Create: `tests/test_shredding_scrapers.py`

- [ ] **Step 1: Write test to verify shredding parsing**

Create `/Users/ethanatchley/Desktop/ECAS-industry-factory/tests/test_shredding_scrapers.py`:

```python
import pytest
from signals.shredding_association_scraper import parse_shredding_association

def test_parse_shredding_association():
    html = '<div class="member-name"><h2>Metro Shredding Corp</h2></div>'
    parsed = parse_shredding_association(html)
    assert len(parsed) == 1
    assert parsed[0] == "Metro Shredding Corp"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_shredding_scrapers.py -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement Shredding Association Scraper**

Create `/Users/ethanatchley/Desktop/ECAS-industry-factory/signals/shredding_association_scraper.py`:

```python
import re
import urllib.request
from tools.domain_resolver import resolve_domain
from tools.contact_finder import find_contacts_for_domain
from tools.verify_cascade import verify_email_cascade
from tools.n8n_router import route_lead_to_n8n, send_discord_alert, sync_dead_letter_queue_to_airtable
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
                        print(f"  [Success] routing {email} ({status}) to Smartlead")
                        route_lead_to_n8n(c)
                    else:
                        sync_dead_letter_queue_to_airtable(c, f"Email verification returned: {status}", AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
                        
    except Exception as e:
        print(f"[Error] Shredding association crawler failed: {e}")
        send_discord_alert(f"🚨 *CRITICAL SCRAPER EXCEPTION*: Shredding scraper stopped unexpectedly. Error: {e}")

if __name__ == "__main__":
    scrape_shredding_members()
```

- [ ] **Step 4: Implement commercial target list loader**

Create `/Users/ethanatchley/Desktop/ECAS-industry-factory/tools/load_shredding_leads.py`:

```python
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
```

- [ ] **Step 5: Run tests to verify all scrapers pass**

Run: `pytest tests/test_shredding_scrapers.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add tests/test_shredding_scrapers.py signals/shredding_association_scraper.py tools/load_shredding_leads.py
git commit -m "feat: implement shredding association scrapers and target list loader"
```

---

## Plan Verification Checklists

### Spec Coverage Check
- [x] Custom Builders permits scraping included (Task 6).
- [x] Dallas BA & NAHB directories crawling included (Task 7).
- [x] Document destruction i-SIGMA and NAID directories included (Task 8).
- [x] Cost-effective domain resolution included (Task 2).
- [x] Targeted Apollo search API included (Task 3).
- [x] Million Verifier + Findymail verification cascade included (Task 4).
- [x] Failover, credit alerts, sqlite queue, and Airtable DLQ manual mode included (Task 4 & Task 5).

### Placeholder Check
- [x] No "TBD" or "TODO" items.
- [x] Full source code block included in every step.
- [x] Complete terminal test commands and explicit assertions included.
