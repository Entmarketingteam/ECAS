# ContractMotion Autonomous Outbound Engine — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Google Maps discovery layer to ECAS that scrapes 42K US zip codes for electrical/general/mechanical contractors, enriches found companies with decision-maker contacts via Blitz→Prospeo→Apollo waterfall, validates emails via MillionVerifier, and automatically enrolls qualified leads into existing Smartlead campaigns — fully scheduled on Railway with n8n orchestration.

**Architecture:** Google Maps scraper runs weekly as a Railway APScheduler job, writing deduplicated company records to Supabase. Blitz/Prospeo enricher runs daily against new companies, finding decision-makers and validating emails. An n8n workflow orchestrates the final quality gate → Smartlead enrollment loop. coldoutboundskills is installed as a Claude Code plugin for manual skill invocation (campaign strategy, deliverability audits, experiment design).

**Tech Stack:** Python 3.11, APScheduler, RapidAPI (Google Maps Extractor 2), Blitz API, Prospeo API, MillionVerifier API, Supabase REST, Smartlead API, n8n, Doppler for secrets.

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| **Create** | `storage/supabase_leads.py` | Supabase write client — upsert companies, contacts, log enrollments, query unenrolled |
| **Create** | `signals/gmaps_scraper.py` | Maps scraper — pulls zips from Supabase, searches RapidAPI, deduplicates by place_id |
| **Create** | `enrichment/blitz_enricher.py` | Blitz → Prospeo domain-to-contacts waterfall |
| **Create** | `enrichment/millionverifier.py` | Email validation module (replaces silent Findymail pass-through) |
| **Create** | `n8n-workflows/08-maps-to-smartlead.json` | n8n: weekly cron → Supabase contacts → Smartlead enroll → Slack alert |
| **Modify** | `config.py` | Add RAPIDAPI_KEY, BLITZ_API_KEY, BLITZ_BASE_URL, PROSPEO_API_KEY, MILLIONVERIFIER_API_KEY |
| **Modify** | `scheduler.py` | Add Maps scraper job (weekly) + Blitz enricher job (daily) |
| **Modify** | `enrichment/clay_enricher.py:155,172` | Replace silent `return True` with MillionVerifier fallback |
| **Modify** | `smartlead_enroll.py:15` | Remove hardcoded key, use `os.environ["SMARTLEAD_API_KEY"]` |

---

## Phase 0 — Security Fix (Do This First)

### Task 0: Rotate leaked Smartlead key + fix hardcode

**Files:**
- Modify: `smartlead_enroll.py:15`

- [ ] **Step 1: Rotate the Smartlead API key**

Log into Smartlead → Settings → API Keys → rotate/regenerate the key. Copy the new value.

- [ ] **Step 2: Update Doppler with new key**

```bash
doppler secrets set SMARTLEAD_API_KEY="<new-key>" --project example-project --config prd
```

- [ ] **Step 3: Fix the hardcode in smartlead_enroll.py**

Find line 15 which reads something like:
```python
SMARTLEAD_KEY = "17a34ec2-b253-45a8-9f0c-707333b745ad_3eex9gg"
```

Replace with:
```python
SMARTLEAD_KEY = os.environ.get("SMARTLEAD_API_KEY", "")
if not SMARTLEAD_KEY:
    raise ValueError("SMARTLEAD_API_KEY not set")
```

Make sure `import os` is at the top of `smartlead_enroll.py`.

- [ ] **Step 4: Commit**

```bash
git add smartlead_enroll.py
git commit -m "fix: remove hardcoded Smartlead key, use SMARTLEAD_API_KEY env var"
```

---

## Phase 1 — Doppler + Config

### Task 1: Add new API keys to Doppler and config.py

**Files:**
- Modify: `config.py` (bottom of API Keys section)

- [ ] **Step 1: Add new keys to Doppler**

```bash
doppler secrets set \
  RAPIDAPI_KEY="<your-rapidapi-key>" \
  BLITZ_API_KEY="<your-blitz-key>" \
  BLITZ_BASE_URL="https://api.useblitz.com" \
  PROSPEO_API_KEY="<your-prospeo-key>" \
  MILLIONVERIFIER_API_KEY="<your-millionverifier-key>" \
  --project example-project --config prd
```

Get keys from:
- RapidAPI: subscribe to "Google Maps Extractor 2" by flybyapi1 at rapidapi.com
- Blitz: app.useblitz.com → Settings → API
- Prospeo: app.prospeo.io → Settings → API Key
- MillionVerifier: app.millionverifier.com → API

- [ ] **Step 2: Add to config.py** — after the existing `FINDYMAIL_API_KEY` line:

```python
# Google Maps / RapidAPI
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "")

# Blitz — domain → decision-maker contacts
BLITZ_API_KEY = os.environ.get("BLITZ_API_KEY", "")
BLITZ_BASE_URL = os.environ.get("BLITZ_BASE_URL", "https://api.useblitz.com")

# Prospeo — domain search fallback
PROSPEO_API_KEY = os.environ.get("PROSPEO_API_KEY", "")

# MillionVerifier — email validation
MILLIONVERIFIER_API_KEY = os.environ.get("MILLIONVERIFIER_API_KEY", "")

# Google Maps target queries mapped to ECAS sectors
GMAPS_QUERIES: list[dict] = [
    {"query": "electrical contractor",       "sector": "Power & Grid Infrastructure"},
    {"query": "solar contractor",            "sector": "Power & Grid Infrastructure"},
    {"query": "data center construction",    "sector": "Data Center & AI Infrastructure"},
    {"query": "general contractor",          "sector": "Industrial & Manufacturing Facilities"},
    {"query": "mechanical contractor",       "sector": "Industrial & Manufacturing Facilities"},
    {"query": "water treatment contractor",  "sector": "Water & Wastewater Infrastructure"},
    {"query": "engineering firm",            "sector": "Power & Grid Infrastructure"},
    {"query": "construction company",        "sector": "Industrial & Manufacturing Facilities"},
]
```

- [ ] **Step 3: Commit**

```bash
git add config.py
git commit -m "feat: add Maps/Blitz/Prospeo/MillionVerifier keys to config"
```

---

## Phase 2 — Supabase Schema

### Task 2: Create 3 new Supabase tables

**Files:**
- Create: `database/migrations/001_gmaps_tables.sql`

- [ ] **Step 1: Write the migration file**

Create `database/migrations/001_gmaps_tables.sql`:

```sql
-- Google Maps discovered companies
create table if not exists gmaps_companies (
  id               uuid primary key default gen_random_uuid(),
  place_id         text unique not null,
  name             text,
  address          text,
  phone            text,
  website_domain   text,
  rating           numeric(3,1),
  total_reviews    integer,
  zip_code         text,
  state            text,
  query            text,
  sector           text,
  created_at       timestamptz default now(),
  enriched_at      timestamptz,
  enrichment_status text default 'pending'
);

create index if not exists gmaps_companies_status_idx on gmaps_companies(enrichment_status);
create index if not exists gmaps_companies_zip_idx on gmaps_companies(zip_code);

-- Decision-maker contacts found via Blitz/Prospeo enrichment
create table if not exists gmaps_contacts (
  id               uuid primary key default gen_random_uuid(),
  place_id         text references gmaps_companies(place_id),
  company_name     text,
  website_domain   text,
  first_name       text,
  last_name        text,
  title            text,
  email            text,
  email_quality    text,
  linkedin_url     text,
  source           text,
  created_at       timestamptz default now(),
  enrolled_at      timestamptz,
  smartlead_campaign_id text
);

create index if not exists gmaps_contacts_enrolled_idx on gmaps_contacts(enrolled_at);
create index if not exists gmaps_contacts_quality_idx on gmaps_contacts(email_quality);

-- Enrollment event log (audit trail)
create table if not exists enrollment_log (
  id               uuid primary key default gen_random_uuid(),
  contact_email    text not null,
  smartlead_campaign_id text,
  source           text,
  enrolled_at      timestamptz default now(),
  lead_data        jsonb
);
```

- [ ] **Step 2: Run migration in Supabase**

Go to Supabase → SQL Editor → paste and run `001_gmaps_tables.sql`.

Or via CLI if configured:
```bash
doppler run --project example-project --config prd -- \
  psql "$DB_URL" -f database/migrations/001_gmaps_tables.sql
```

- [ ] **Step 3: Verify tables exist**

In Supabase Table Editor, confirm `gmaps_companies`, `gmaps_contacts`, `enrollment_log` appear.

- [ ] **Step 4: Commit**

```bash
git add database/migrations/001_gmaps_tables.sql
git commit -m "feat: add gmaps_companies, gmaps_contacts, enrollment_log tables"
```

---

## Phase 3 — Supabase Write Client

### Task 3: Create storage/supabase_leads.py

**Files:**
- Create: `storage/supabase_leads.py`

- [ ] **Step 1: Write the module**

Create `storage/supabase_leads.py`:

```python
"""
storage/supabase_leads.py
Supabase write client for Google Maps discovery pipeline.
Handles upsert/query for gmaps_companies, gmaps_contacts, enrollment_log.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional

import requests

logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")


def _headers() -> dict:
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates",
    }


def _sb_upsert(table: str, records: list[dict], on_conflict: str) -> bool:
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.warning("[SupabaseLeads] SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set")
        return False
    headers = _headers()
    headers["Prefer"] = f"resolution=merge-duplicates,return=minimal"
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/{table}?on_conflict={on_conflict}",
        headers=headers,
        json=records,
        timeout=15,
    )
    if r.status_code not in (200, 201):
        logger.error(f"[SupabaseLeads] upsert {table} failed {r.status_code}: {r.text[:200]}")
        return False
    return True


def _sb_get(table: str, params: dict) -> list:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/{table}",
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
        params=params,
        timeout=15,
    )
    if r.status_code != 200:
        logger.error(f"[SupabaseLeads] get {table} failed {r.status_code}")
        return []
    return r.json()


def _sb_patch(table: str, match_params: dict, update: dict) -> bool:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return False
    r = requests.patch(
        f"{SUPABASE_URL}/rest/v1/{table}",
        headers={**_headers(), "Prefer": "return=minimal"},
        params=match_params,
        json=update,
        timeout=15,
    )
    if r.status_code not in (200, 204):
        logger.error(f"[SupabaseLeads] patch {table} failed {r.status_code}: {r.text[:200]}")
        return False
    return True


def upsert_companies(companies: list[dict]) -> int:
    """Upsert a batch of gmaps_companies. Returns count written."""
    if not companies:
        return 0
    ok = _sb_upsert("gmaps_companies", companies, "place_id")
    return len(companies) if ok else 0


def upsert_contacts(contacts: list[dict]) -> int:
    """Upsert a batch of gmaps_contacts. Returns count written."""
    if not contacts:
        return 0
    ok = _sb_upsert("gmaps_contacts", contacts, "email")
    return len(contacts) if ok else 0


def mark_company_enriched(place_id: str) -> None:
    _sb_patch(
        "gmaps_companies",
        {"place_id": f"eq.{place_id}"},
        {"enrichment_status": "enriched", "enriched_at": datetime.now(timezone.utc).isoformat()},
    )


def mark_company_enrichment_failed(place_id: str) -> None:
    _sb_patch(
        "gmaps_companies",
        {"place_id": f"eq.{place_id}"},
        {"enrichment_status": "failed"},
    )


def get_pending_companies(limit: int = 100) -> list[dict]:
    """Return companies waiting for contact enrichment."""
    return _sb_get("gmaps_companies", {
        "enrichment_status": "eq.pending",
        "website_domain": "not.is.null",
        "select": "place_id,name,website_domain,sector,state",
        "limit": limit,
        "order": "created_at.asc",
    })


def get_unenrolled_contacts(limit: int = 200) -> list[dict]:
    """Return good-quality contacts not yet enrolled in Smartlead."""
    return _sb_get("gmaps_contacts", {
        "enrolled_at": "is.null",
        "email_quality": "eq.good",
        "select": "id,place_id,company_name,website_domain,first_name,last_name,title,email,linkedin_url",
        "limit": limit,
        "order": "created_at.asc",
    })


def mark_contact_enrolled(contact_id: str, campaign_id: str) -> None:
    _sb_patch(
        "gmaps_contacts",
        {"id": f"eq.{contact_id}"},
        {"enrolled_at": datetime.now(timezone.utc).isoformat(), "smartlead_campaign_id": campaign_id},
    )


def log_enrollment(email: str, campaign_id: str, source: str, lead_data: dict) -> None:
    _sb_upsert("enrollment_log", [{
        "contact_email": email,
        "smartlead_campaign_id": campaign_id,
        "source": source,
        "lead_data": lead_data,
    }], "contact_email")
```

- [ ] **Step 2: Smoke test manually**

```bash
cd /c/Users/ethan.atchley/projects/ECAS
doppler run --project example-project --config prd -- python -c "
from storage.supabase_leads import get_pending_companies
print(get_pending_companies(limit=1))
"
```

Expected: `[]` (table is empty — that's correct)

- [ ] **Step 3: Commit**

```bash
git add storage/supabase_leads.py
git commit -m "feat: add supabase_leads write client for Maps pipeline"
```

---

## Phase 4 — Google Maps Scraper

### Task 4: Create signals/gmaps_scraper.py

**Files:**
- Create: `signals/gmaps_scraper.py`

- [ ] **Step 1: Write the scraper**

Create `signals/gmaps_scraper.py`:

```python
"""
signals/gmaps_scraper.py
Google Maps business scraper for EPC contractor discovery.

Uses RapidAPI Google Maps Extractor 2 to search for EPC-related businesses
across US zip codes. Pulls zip codes from Supabase zip_codes table (already
populated by zip-demographics pipeline) filtered by population.

Results are deduplicated by place_id and written to Supabase gmaps_companies.
"""

import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
from typing import Optional

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import RAPIDAPI_KEY, GMAPS_QUERIES
from storage.supabase_leads import upsert_companies

logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

RAPIDAPI_HOST = "google-maps-extractor2.p.rapidapi.com"
RAPIDAPI_HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": RAPIDAPI_HOST,
}

MIN_POPULATION = 10_000
MAX_WORKERS = 5
RESULTS_PER_ZIP = 20


class _RateLimiter:
    def __init__(self, max_per_second: int = 5):
        self._lock = Lock()
        self._timestamps: list[float] = []
        self._max = max_per_second

    def wait(self):
        with self._lock:
            now = time.time()
            self._timestamps = [t for t in self._timestamps if now - t < 1.0]
            if len(self._timestamps) >= self._max:
                sleep_for = 1.0 - (now - self._timestamps[0]) + 0.01
                if sleep_for > 0:
                    time.sleep(sleep_for)
                self._timestamps = self._timestamps[1:]
            self._timestamps.append(time.time())


_rate_limiter = _RateLimiter(max_per_second=5)


def _get_zips_from_supabase(state: Optional[str] = None) -> list[dict]:
    """Pull zip codes from Supabase zip_codes table with population filter."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("[GMapsScraper] Supabase not configured")
        return []
    params = {
        "select": "zip,city,state_id",
        "population": f"gte.{MIN_POPULATION}",
        "limit": 5000,
        "order": "population.desc",
    }
    if state:
        params["state_id"] = f"eq.{state.upper()}"
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/zip_codes",
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
        params=params,
        timeout=15,
    )
    if r.status_code != 200:
        logger.error(f"[GMapsScraper] zip fetch failed: {r.status_code}")
        return []
    return r.json()


def _search_maps(query: str, zip_code: str) -> list[dict]:
    """Search Google Maps for a query in a given zip code."""
    _rate_limiter.wait()
    try:
        r = requests.get(
            f"https://{RAPIDAPI_HOST}/locate_and_search",
            headers=RAPIDAPI_HEADERS,
            params={"query": f"{query} in {zip_code}", "limit": RESULTS_PER_ZIP},
            timeout=20,
        )
        if r.status_code == 429:
            logger.warning("[GMapsScraper] Rate limited — sleeping 5s")
            time.sleep(5)
            return []
        if r.status_code != 200:
            return []
        data = r.json()
        return data if isinstance(data, list) else data.get("results", [])
    except Exception as e:
        logger.debug(f"[GMapsScraper] search error {zip_code}: {e}")
        return []


def _extract_domain(website_url: Optional[str]) -> Optional[str]:
    if not website_url:
        return None
    try:
        from urllib.parse import urlparse
        parsed = urlparse(website_url if "://" in website_url else f"https://{website_url}")
        domain = parsed.netloc.lower().lstrip("www.")
        return domain if domain else None
    except Exception:
        return None


def _scrape_zip(query_config: dict, zip_info: dict) -> list[dict]:
    """Scrape one (query, zip) pair. Returns list of company dicts ready for Supabase."""
    query = query_config["query"]
    sector = query_config["sector"]
    zip_code = zip_info["zip"]
    state = zip_info.get("state_id", "")

    results = _search_maps(query, zip_code)
    companies = []
    for biz in results:
        place_id = biz.get("place_id") or biz.get("business_id")
        if not place_id:
            continue
        name = biz.get("name") or biz.get("title")
        website = biz.get("website")
        companies.append({
            "place_id":       place_id,
            "name":           name,
            "address":        biz.get("address") or biz.get("full_address"),
            "phone":          biz.get("phone"),
            "website_domain": _extract_domain(website),
            "rating":         biz.get("rating"),
            "total_reviews":  biz.get("reviews") or biz.get("total_reviews"),
            "zip_code":       zip_code,
            "state":          state,
            "query":          query,
            "sector":         sector,
        })
    return companies


def run_scraper(states: Optional[list[str]] = None, max_zips: Optional[int] = None) -> dict:
    """
    Main entry point. Scrapes all GMAPS_QUERIES × matching zip codes.
    
    Args:
        states: List of state codes to limit scope (e.g. ["TX", "CA"]). None = all states.
        max_zips: Cap total zips per query for testing. None = no cap.
    
    Returns summary dict.
    """
    if not RAPIDAPI_KEY:
        logger.error("[GMapsScraper] RAPIDAPI_KEY not set")
        return {"error": "RAPIDAPI_KEY not set"}

    totals = {"companies_found": 0, "companies_written": 0, "zips_processed": 0}
    batch: list[dict] = []
    BATCH_SIZE = 200

    for query_config in GMAPS_QUERIES:
        target_states = states or [None]  # None = all states in one query
        for state in target_states:
            zips = _get_zips_from_supabase(state=state)
            if max_zips:
                zips = zips[:max_zips]
            if not zips:
                continue

            logger.info(f"[GMapsScraper] '{query_config['query']}' × {len(zips)} zips" +
                       (f" in {state}" if state else ""))

            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
                futures = {pool.submit(_scrape_zip, query_config, z): z for z in zips}
                for future in as_completed(futures):
                    try:
                        companies = future.result()
                        batch.extend(companies)
                        totals["companies_found"] += len(companies)
                        totals["zips_processed"] += 1
                    except Exception as e:
                        logger.debug(f"[GMapsScraper] future error: {e}")

                    if len(batch) >= BATCH_SIZE:
                        written = upsert_companies(batch)
                        totals["companies_written"] += written
                        batch.clear()

    if batch:
        written = upsert_companies(batch)
        totals["companies_written"] += written

    logger.info(f"[GMapsScraper] Done — {totals}")
    return totals


if __name__ == "__main__":
    # Quick test: 10 zips in Texas only
    logging.basicConfig(level=logging.INFO)
    result = run_scraper(states=["TX"], max_zips=10)
    print(result)
```

- [ ] **Step 2: Run a quick test (10 zips, Texas only)**

```bash
cd /c/Users/ethan.atchley/projects/ECAS
doppler run --project example-project --config prd -- python signals/gmaps_scraper.py
```

Expected output (approximate):
```
[GMapsScraper] 'electrical contractor' × 10 zips in TX
[GMapsScraper] Done — {'companies_found': 120, 'companies_written': 120, 'zips_processed': 10}
```

Then verify in Supabase Table Editor → `gmaps_companies` has rows.

- [ ] **Step 3: Commit**

```bash
git add signals/gmaps_scraper.py
git commit -m "feat: add Google Maps scraper for EPC contractor discovery"
```

---

## Phase 5 — Email Validator

### Task 5: Create enrichment/millionverifier.py

**Files:**
- Create: `enrichment/millionverifier.py`

- [ ] **Step 1: Write the module**

Create `enrichment/millionverifier.py`:

```python
"""
enrichment/millionverifier.py
Email validation via MillionVerifier API.

Returns True for "good" emails, False for "bad".
"risky" emails (catch-all, unknown) are accepted by default — set
REJECT_RISKY=True via env var to tighten quality gates.
"""

import logging
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import MILLIONVERIFIER_API_KEY

logger = logging.getLogger(__name__)

REJECT_RISKY = os.environ.get("REJECT_RISKY", "false").lower() == "true"


def verify_email(email: str) -> tuple[bool, str]:
    """
    Validate an email address.
    
    Returns:
        (is_valid, quality) where quality is 'good', 'risky', or 'bad'
    """
    if not MILLIONVERIFIER_API_KEY:
        logger.debug("[MillionVerifier] No API key — passing email through as risky")
        return True, "risky"

    try:
        r = requests.get(
            "https://api.millionverifier.com/api/v3/",
            params={"api": MILLIONVERIFIER_API_KEY, "email": email},
            timeout=10,
        )
        if r.status_code != 200:
            logger.warning(f"[MillionVerifier] {r.status_code} for {email} — treating as risky")
            return True, "risky"

        data = r.json()
        quality = data.get("quality", "risky").lower()
        result_code = data.get("result", "")

        if quality == "good":
            return True, "good"
        if quality == "bad" or result_code in ("invalid", "disposable", "spamtrap"):
            return False, "bad"
        # risky / catch-all / unknown
        return not REJECT_RISKY, "risky"

    except Exception as e:
        logger.debug(f"[MillionVerifier] error for {email}: {e} — treating as risky")
        return True, "risky"


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    test_email = sys.argv[1] if len(sys.argv) > 1 else "test@example.com"
    valid, quality = verify_email(test_email)
    print(f"{test_email} → valid={valid}, quality={quality}")
```

- [ ] **Step 2: Test it**

```bash
doppler run --project example-project --config prd -- \
  python enrichment/millionverifier.py info@generalelectric.com
```

Expected:
```
info@generalelectric.com → valid=True, quality=good
```

- [ ] **Step 3: Commit**

```bash
git add enrichment/millionverifier.py
git commit -m "feat: add MillionVerifier email validation module"
```

---

## Phase 6 — Blitz/Prospeo Enricher

### Task 6: Create enrichment/blitz_enricher.py

**Files:**
- Create: `enrichment/blitz_enricher.py`

- [ ] **Step 1: Write the enricher**

Create `enrichment/blitz_enricher.py`:

```python
"""
enrichment/blitz_enricher.py
Domain-to-contacts enrichment waterfall for Google Maps companies.

Waterfall order:
  1. Blitz API (domain → owner/decision-maker, best for SMB/owner-operated contractors)
  2. Prospeo domain search (fallback, title-filtered)
  3. Mark failed if both return nothing

Contacts are validated via MillionVerifier before being written to Supabase.
"""

import logging
import sys
import time
from pathlib import Path
from typing import Optional

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import BLITZ_API_KEY, BLITZ_BASE_URL, PROSPEO_API_KEY
from enrichment.millionverifier import verify_email
from storage.supabase_leads import (
    get_pending_companies,
    mark_company_enriched,
    mark_company_enrichment_failed,
    upsert_contacts,
)

logger = logging.getLogger(__name__)

TARGET_TITLES = [
    "owner", "president", "ceo", "founder", "principal",
    "vp", "vice president", "director", "operations manager",
    "project manager", "business development",
]


def _blitz_search(domain: str) -> list[dict]:
    """Search Blitz API for contacts at a domain."""
    if not BLITZ_API_KEY:
        return []
    try:
        r = requests.post(
            f"{BLITZ_BASE_URL}/v1/people/search",
            headers={"Authorization": f"Bearer {BLITZ_API_KEY}", "Content-Type": "application/json"},
            json={"domain": domain, "titles": TARGET_TITLES, "limit": 5},
            timeout=15,
        )
        if r.status_code != 200:
            logger.debug(f"[BlitzEnricher] Blitz {r.status_code} for {domain}")
            return []
        data = r.json()
        return data.get("people", data) if isinstance(data, dict) else data
    except Exception as e:
        logger.debug(f"[BlitzEnricher] Blitz error for {domain}: {e}")
        return []


def _prospeo_search(domain: str) -> list[dict]:
    """Prospeo domain search fallback."""
    if not PROSPEO_API_KEY:
        return []
    try:
        r = requests.post(
            "https://api.prospeo.io/domain-search",
            headers={"X-KEY": PROSPEO_API_KEY, "Content-Type": "application/json"},
            json={"url": domain, "limit": 10},
            timeout=15,
        )
        if r.status_code != 200:
            logger.debug(f"[BlitzEnricher] Prospeo {r.status_code} for {domain}")
            return []
        data = r.json()
        people = data.get("response", {}).get("emails", [])
        return [
            {
                "first_name": p.get("first_name"),
                "last_name":  p.get("last_name"),
                "title":      p.get("position"),
                "email":      p.get("email"),
                "linkedin_url": p.get("linkedin_url"),
            }
            for p in people
            if p.get("email")
        ]
    except Exception as e:
        logger.debug(f"[BlitzEnricher] Prospeo error for {domain}: {e}")
        return []


def _normalize_contact(raw: dict) -> Optional[dict]:
    """Normalize a raw contact dict from either API into a consistent shape."""
    email = (raw.get("email") or "").strip().lower()
    if not email or "@" not in email:
        return None
    return {
        "first_name":   raw.get("first_name") or raw.get("firstName"),
        "last_name":    raw.get("last_name") or raw.get("lastName"),
        "title":        raw.get("title") or raw.get("job_title") or raw.get("position"),
        "email":        email,
        "linkedin_url": raw.get("linkedin_url") or raw.get("linkedin"),
    }


def enrich_company(place_id: str, company_name: str, domain: str, sector: str, state: str) -> int:
    """
    Enrich one company. Returns count of contacts written.
    """
    # Try Blitz first, fall back to Prospeo
    raw_contacts = _blitz_search(domain)
    source = "blitz"
    if not raw_contacts:
        raw_contacts = _prospeo_search(domain)
        source = "prospeo"

    if not raw_contacts:
        mark_company_enrichment_failed(place_id)
        return 0

    contacts_to_write = []
    for raw in raw_contacts[:5]:  # max 5 contacts per company
        contact = _normalize_contact(raw)
        if not contact:
            continue
        is_valid, quality = verify_email(contact["email"])
        if not is_valid:
            continue
        contacts_to_write.append({
            **contact,
            "place_id":      place_id,
            "company_name":  company_name,
            "website_domain": domain,
            "email_quality": quality,
            "source":        source,
        })
        time.sleep(0.1)  # small delay between MillionVerifier calls

    written = upsert_contacts(contacts_to_write)
    mark_company_enriched(place_id)
    return written


def run_enricher(batch_size: int = 50) -> dict:
    """
    Process a batch of pending companies from Supabase.
    Called by APScheduler daily.
    """
    companies = get_pending_companies(limit=batch_size)
    if not companies:
        logger.info("[BlitzEnricher] No pending companies")
        return {"processed": 0, "contacts_written": 0}

    totals = {"processed": 0, "contacts_written": 0}
    for company in companies:
        domain = company.get("website_domain")
        if not domain:
            mark_company_enrichment_failed(company["place_id"])
            continue
        written = enrich_company(
            place_id=company["place_id"],
            company_name=company.get("name", ""),
            domain=domain,
            sector=company.get("sector", ""),
            state=company.get("state", ""),
        )
        totals["processed"] += 1
        totals["contacts_written"] += written
        time.sleep(0.5)  # be gentle with APIs

    logger.info(f"[BlitzEnricher] Done — {totals}")
    return totals


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run_enricher(batch_size=5)
    print(result)
```

- [ ] **Step 2: Test against a real domain (after Task 4 has written companies)**

```bash
doppler run --project example-project --config prd -- \
  python enrichment/blitz_enricher.py
```

Expected: processes up to 5 companies, prints contacts_written count. Check Supabase `gmaps_contacts` table for results.

- [ ] **Step 3: Commit**

```bash
git add enrichment/blitz_enricher.py
git commit -m "feat: add Blitz/Prospeo enrichment waterfall for Maps companies"
```

---

## Phase 7 — Fix clay_enricher Silent Pass-Through

### Task 7: Replace Findymail silent return True with MillionVerifier fallback

**Files:**
- Modify: `enrichment/clay_enricher.py:155,172`

- [ ] **Step 1: Add MillionVerifier import at top of clay_enricher.py**

Find the imports section and add:
```python
from enrichment.millionverifier import verify_email as _mv_verify
```

- [ ] **Step 2: Replace the two `return True` lines**

Line 155 (inside `_findymail_verify` when no key is set):

Old:
```python
        return True  # no key → don't block, pass through
```

New:
```python
        # No Findymail key — fall back to MillionVerifier
        is_valid, _ = _mv_verify(email)
        return is_valid
```

Line 172 (network error fallback):

Old:
```python
    return True  # network error → don't block
```

New:
```python
    # Findymail network error — fall back to MillionVerifier
    is_valid, _ = _mv_verify(email)
    return is_valid
```

- [ ] **Step 3: Commit**

```bash
git add enrichment/clay_enricher.py
git commit -m "fix: replace Findymail silent pass-through with MillionVerifier fallback"
```

---

## Phase 8 — Wire APScheduler

### Task 8: Add Maps and Blitz jobs to scheduler.py

**Files:**
- Modify: `scheduler.py`

- [ ] **Step 1: Add the two job functions**

After the last `job_` function in `scheduler.py`, add:

```python
def job_gmaps_scraper():
    """Weekly: scrape Google Maps for EPC contractors across all US zips."""
    logger.info("=== JOB: Google Maps Scraper ===")
    try:
        from signals.gmaps_scraper import run_scraper
        # Full US run on Sunday nights — use state rotation if API costs are a concern
        result = run_scraper()
        logger.info(f"[GMapsScraper] Completed: {result}")
    except Exception as e:
        logger.error(f"[GMapsScraper] Job failed: {e}", exc_info=True)


def job_blitz_enricher():
    """Daily: enrich pending Google Maps companies with decision-maker contacts."""
    logger.info("=== JOB: Blitz Enricher ===")
    try:
        from enrichment.blitz_enricher import run_enricher
        result = run_enricher(batch_size=100)
        logger.info(f"[BlitzEnricher] Completed: {result}")
    except Exception as e:
        logger.error(f"[BlitzEnricher] Job failed: {e}", exc_info=True)
```

- [ ] **Step 2: Register both jobs in start_scheduler()**

Find the `start_scheduler()` function where other jobs are added (look for `_scheduler.add_job(...)`). Add at the end of that block:

```python
    # Google Maps discovery — weekly Sunday at 2am UTC
    _scheduler.add_job(
        job_gmaps_scraper,
        trigger=CronTrigger(day_of_week="sun", hour=2, minute=0),
        id="gmaps_scraper",
        name="Google Maps EPC Scraper",
        replace_existing=True,
    )

    # Blitz enricher — daily at 8am UTC (after scraper has run)
    _scheduler.add_job(
        job_blitz_enricher,
        trigger=CronTrigger(hour=8, minute=0),
        id="blitz_enricher",
        name="Blitz/Prospeo Contact Enricher",
        replace_existing=True,
    )
```

- [ ] **Step 3: Verify scheduler starts cleanly**

```bash
doppler run --project example-project --config prd -- \
  python -c "from scheduler import start_scheduler, stop_scheduler; start_scheduler(); print('OK'); stop_scheduler()"
```

Expected: `OK` with no errors.

- [ ] **Step 4: Commit**

```bash
git add scheduler.py
git commit -m "feat: add gmaps_scraper and blitz_enricher to APScheduler"
```

---

## Phase 9 — n8n Orchestration Workflow

### Task 9: Create n8n workflow 08 (Maps discovery → Smartlead enrollment)

**Files:**
- Create: `n8n-workflows/08-maps-to-smartlead.json`

- [ ] **Step 1: Write the workflow JSON**

Create `n8n-workflows/08-maps-to-smartlead.json`:

```json
{
  "name": "08 — Maps Discovery → Smartlead Enrollment",
  "nodes": [
    {
      "name": "Weekly Cron",
      "type": "n8n-nodes-base.scheduleTrigger",
      "position": [250, 300],
      "parameters": {
        "rule": {
          "interval": [{"field": "weeks", "triggerAtDay": [1], "triggerAtHour": 9}]
        }
      }
    },
    {
      "name": "Get Unenrolled Contacts",
      "type": "n8n-nodes-base.httpRequest",
      "position": [500, 300],
      "parameters": {
        "method": "GET",
        "url": "={{ $env.SUPABASE_URL }}/rest/v1/gmaps_contacts",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {"name": "apikey", "value": "={{ $env.SUPABASE_SERVICE_ROLE_KEY }}"},
            {"name": "Authorization", "value": "=Bearer {{ $env.SUPABASE_SERVICE_ROLE_KEY }}"}
          ]
        },
        "sendQuery": true,
        "queryParameters": {
          "parameters": [
            {"name": "enrolled_at", "value": "is.null"},
            {"name": "email_quality", "value": "eq.good"},
            {"name": "select", "value": "id,place_id,company_name,website_domain,first_name,last_name,title,email,linkedin_url"},
            {"name": "limit", "value": "100"},
            {"name": "order", "value": "created_at.asc"}
          ]
        }
      }
    },
    {
      "name": "IF Has Contacts",
      "type": "n8n-nodes-base.if",
      "position": [750, 300],
      "parameters": {
        "conditions": {
          "number": [{"value1": "={{ $json.length }}", "operation": "larger", "value2": 0}]
        }
      }
    },
    {
      "name": "Split Into Batches",
      "type": "n8n-nodes-base.splitInBatches",
      "position": [1000, 250],
      "parameters": {"batchSize": 1}
    },
    {
      "name": "Get Company Sector",
      "type": "n8n-nodes-base.httpRequest",
      "position": [1250, 250],
      "parameters": {
        "method": "GET",
        "url": "={{ $env.SUPABASE_URL }}/rest/v1/gmaps_companies",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {"name": "apikey", "value": "={{ $env.SUPABASE_SERVICE_ROLE_KEY }}"},
            {"name": "Authorization", "value": "=Bearer {{ $env.SUPABASE_SERVICE_ROLE_KEY }}"}
          ]
        },
        "sendQuery": true,
        "queryParameters": {
          "parameters": [
            {"name": "place_id", "value": "=eq.{{ $json.place_id }}"},
            {"name": "select", "value": "sector"}
          ]
        }
      }
    },
    {
      "name": "Enroll in Smartlead",
      "type": "n8n-nodes-base.httpRequest",
      "position": [1500, 250],
      "parameters": {
        "method": "POST",
        "url": "https://server.smartlead.ai/api/v1/campaigns/{{ $node['Get Company Sector'].json[0].sector === 'Power & Grid Infrastructure' ? '3005694' : $node['Get Company Sector'].json[0].sector === 'Data Center & AI Infrastructure' ? '3040599' : $node['Get Company Sector'].json[0].sector === 'Water & Wastewater Infrastructure' ? '3040600' : '3040601' }}/leads",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {"name": "Content-Type", "value": "application/json"}
          ]
        },
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {"name": "api_key", "value": "={{ $env.SMARTLEAD_API_KEY }}"},
            {"name": "lead_list", "value": "=[{\"email\": \"{{ $json.email }}\", \"first_name\": \"{{ $json.first_name }}\", \"last_name\": \"{{ $json.last_name }}\", \"company_name\": \"{{ $json.company_name }}\", \"website\": \"{{ $json.website_domain }}\", \"custom_fields\": {\"title\": \"{{ $json.title }}\", \"source\": \"google_maps\"}}]"}
          ]
        }
      }
    },
    {
      "name": "Mark Enrolled in Supabase",
      "type": "n8n-nodes-base.httpRequest",
      "position": [1750, 250],
      "parameters": {
        "method": "PATCH",
        "url": "={{ $env.SUPABASE_URL }}/rest/v1/gmaps_contacts",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {"name": "apikey", "value": "={{ $env.SUPABASE_SERVICE_ROLE_KEY }}"},
            {"name": "Authorization", "value": "=Bearer {{ $env.SUPABASE_SERVICE_ROLE_KEY }}"},
            {"name": "Content-Type", "value": "application/json"},
            {"name": "Prefer", "value": "return=minimal"}
          ]
        },
        "sendQuery": true,
        "queryParameters": {
          "parameters": [{"name": "id", "value": "=eq.{{ $node['Split Into Batches'].json.id }}"}]
        },
        "sendBody": true,
        "specifyBody": "json",
        "jsonBody": "={\"enrolled_at\": \"{{ new Date().toISOString() }}\"}"
      }
    },
    {
      "name": "Slack Summary",
      "type": "n8n-nodes-base.slack",
      "position": [1000, 450],
      "parameters": {
        "operation": "post",
        "channel": "#ecas-signals",
        "text": "=:satellite: *ContractMotion Maps Enrollment*\n{{ $node['Get Unenrolled Contacts'].json.length }} contacts queued from Google Maps discovery this week."
      }
    }
  ],
  "connections": {
    "Weekly Cron": {"main": [[{"node": "Get Unenrolled Contacts", "type": "main", "index": 0}]]},
    "Get Unenrolled Contacts": {"main": [[{"node": "IF Has Contacts", "type": "main", "index": 0}]]},
    "IF Has Contacts": {
      "main": [
        [{"node": "Split Into Batches", "type": "main", "index": 0}],
        [{"node": "Slack Summary", "type": "main", "index": 0}]
      ]
    },
    "Split Into Batches": {"main": [[{"node": "Get Company Sector", "type": "main", "index": 0}]]},
    "Get Company Sector": {"main": [[{"node": "Enroll in Smartlead", "type": "main", "index": 0}]]},
    "Enroll in Smartlead": {"main": [[{"node": "Mark Enrolled in Supabase", "type": "main", "index": 0}]]}
  },
  "active": false,
  "settings": {"executionOrder": "v1"}
}
```

- [ ] **Step 2: Import workflow to n8n**

```bash
doppler run --project ent-agency-automation --config prd -- bash -c '
curl -s -X POST https://entagency.app.n8n.cloud/api/v1/workflows \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  -d @/c/Users/ethan.atchley/projects/ECAS/n8n-workflows/08-maps-to-smartlead.json
'
```

Note the workflow ID from the response.

- [ ] **Step 3: Verify in n8n UI**

Go to https://entagency.app.n8n.cloud — workflow "08 — Maps Discovery → Smartlead Enrollment" should appear as inactive. Activate manually after confirming first scraper run has populated data.

- [ ] **Step 4: Commit**

```bash
git add n8n-workflows/08-maps-to-smartlead.json
git commit -m "feat: add n8n workflow 08 Maps discovery → Smartlead enrollment"
```

---

## Phase 10 — Install coldoutboundskills Plugin

### Task 10: Clone coldoutboundskills and register with Claude Code

**Files:**
- Modify: `~/.claude/settings.json` (global Claude Code settings)

- [ ] **Step 1: Clone the repo**

```bash
git clone https://github.com/growthenginenowoslawski/coldoutboundskills \
  /c/Users/ethan.atchley/projects/coldoutboundskills
```

- [ ] **Step 2: Install deps for the starter kit scripts**

```bash
cd /c/Users/ethan.atchley/projects/coldoutboundskills/skills/cold-email-starter-kit
npm install
```

- [ ] **Step 3: Register as a Claude Code plugin**

Add the skills directory to `~/.claude/settings.json` under `"pluginDirectories"` (or the equivalent skills path key). Open the file and add:

```json
{
  "pluginDirectories": [
    "/c/Users/ethan.atchley/projects/coldoutboundskills"
  ]
}
```

If `pluginDirectories` already exists, append the path to the array.

- [ ] **Step 4: Verify skills load**

Start a new Claude Code session and run:
```
/list-quality-scorecard
```

If it loads, all 29 skills are available.

- [ ] **Step 5: Verify credentials**

```bash
cd /c/Users/ethan.atchley/projects/coldoutboundskills/skills/cold-email-starter-kit
doppler run --project example-project --config prd -- npx tsx scripts/verify-credentials.ts
```

- [ ] **Step 6: Note the pre-built 12M business scrape**

The repo ships with pre-built data at `skills/cold-email-starter-kit/Common\ Outbound\ Lists/`. These zip files contain 12M US business leads already scraped. Filter for your verticals:

```bash
# Extract and filter for construction/electrical/contractor keywords
unzip -p "skills/cold-email-starter-kit/Common Outbound Lists/*.zip" | \
  grep -i "electrical\|contractor\|construction\|engineering" > \
  /c/Users/ethan.atchley/projects/ECAS/data/prebuilt_contractors.csv
```

Import filtered CSV to Supabase `gmaps_companies` to skip weeks of scraping:
```bash
# Use Supabase CSV import: Table Editor → gmaps_companies → Import CSV
```

---

## Execution Order

Run phases in this order — each is independently deployable:

1. **Task 0** (security) — do immediately, before anything else
2. **Task 1** (Doppler) — needed for all subsequent tasks
3. **Task 2** (schema) — needed before any Supabase writes
4. **Task 3** (storage client) — needed by Tasks 4 and 6
5. **Task 5** (MillionVerifier) — needed by Task 6 and Task 7
6. **Task 6** (Blitz enricher) — needs Tasks 3 and 5
7. **Task 4** (Maps scraper) — needs Tasks 2 and 3; run test with max_zips=10
8. **Task 7** (fix clay_enricher) — independent of Maps pipeline, quick fix
9. **Task 8** (scheduler) — wire up after Tasks 4 and 6 are tested
10. **Task 9** (n8n) — activate only after first scraper + enricher run produces data
11. **Task 10** (plugin) — independent, do any time

---

## Doppler Keys to Add (summary)

```bash
doppler secrets set \
  RAPIDAPI_KEY="..." \
  BLITZ_API_KEY="..." \
  BLITZ_BASE_URL="https://api.useblitz.com" \
  PROSPEO_API_KEY="..." \
  MILLIONVERIFIER_API_KEY="..." \
  --project example-project --config prd

# Rotate this (leaked in repo):
doppler secrets set SMARTLEAD_API_KEY="<new-rotated-key>" --project example-project --config prd
```

---

## Expected Outcome After Full Deployment

- **Weekly**: Railway scrapes 8 queries × ~15K populated US zips = up to 120K contractor company records, deduplicated into `gmaps_companies`
- **Daily**: Blitz/Prospeo enriches 100 pending companies/day → decision-maker contacts with verified emails in `gmaps_contacts`
- **Weekly (n8n)**: All good-quality unenrolled contacts auto-enrolled into sector-matched Smartlead campaigns
- **On demand**: `/list-quality-scorecard`, `/email-deliverability-audit`, `/experiment-design` available in Claude Code
- **Pre-built data**: 12M business scrape importable immediately to jumpstart pipeline before first Railway cron runs
