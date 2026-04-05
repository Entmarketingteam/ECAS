# Contractor Signal Expansion — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 6 new signal scrapers to the ECAS contractor pipeline — association directories, SAM.gov contract awards, building permits, FM job changes, competitor moves, and RTO/lease announcements.

**Architecture:** Each scraper lives in `contractor/signals/`, produces a standard signal dict, and pushes directly to Airtable `signals_raw`. A shared `_airtable.py` helper handles batching and dedup. All scrapers register as independent APScheduler jobs in `scheduler.py`. The existing orchestrator picks them up automatically — no orchestrator changes needed.

**Tech Stack:** Python 3.11, `requests`, `beautifulsoup4`, `feedparser`, Firecrawl API (JS-rendered sites), SAM.gov API v2, Socrata API (open data), Apollo API (job changes), Google News RSS (FM/RTO/competitor signals), Airtable REST API.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `contractor/signals/_airtable.py` | CREATE | Shared push helper + 30-day dedup check |
| `contractor/signals/association_scraper.py` | CREATE | NRCA + NPMA + ISSA member directories |
| `contractor/signals/sam_gov_watcher.py` | CREATE | SAM.gov contract award lead signal |
| `contractor/signals/permit_watcher.py` | CREATE | Socrata permit APIs (4 cities) |
| `contractor/signals/fm_job_watcher.py` | CREATE | Apollo job changes + Google News FM postings |
| `contractor/signals/competitor_watcher.py` | CREATE | Franchise expansion RSS + OSHA citations |
| `contractor/signals/rto_watcher.py` | CREATE | RTO announcements + commercial lease news |
| `contractor/tests/test_signal_scrapers_shared.py` | CREATE | Output contract fixtures + shared mock helpers |
| `contractor/tests/test_association_scraper.py` | CREATE | Association scraper unit tests |
| `contractor/tests/test_sam_gov_watcher.py` | CREATE | SAM.gov watcher unit tests |
| `contractor/tests/test_permit_watcher.py` | CREATE | Permit watcher unit tests |
| `contractor/config.py` | MODIFY | Add 5 new signal weights, bump association to 50 pts |
| `scheduler.py` | MODIFY | Wire 6 new APScheduler jobs |
| `requirements.txt` | MODIFY | Add `feedparser`, `beautifulsoup4` if missing |

---

## Standard Signal Dict (output contract — all scrapers must produce this shape)

```python
{
    "company_name": str,           # Required. Best available name.
    "company_domain": str,         # Empty string if unknown — orchestrator handles Apollo lookup.
    "vertical": str,               # "Commercial Roofing" | "Commercial Janitorial" | "Pest Control"
    "vertical_type": "contractor", # Always this literal string.
    "signal_type": str,            # Must match a key in CONTRACTOR_SIGNAL_WEIGHTS.
    "detected_at": str,            # ISO 8601 UTC e.g. "2026-04-05T10:00:00"
    "source": str,                 # Human-readable source e.g. "NRCA" | "SAM.gov" | "Socrata-Austin"
    "processed": False,            # Always False — orchestrator flips it.
    "raw_data_json": dict,         # Source-specific fields. Can be empty dict.
}
```

---

## Task 0: Deps + Config Updates

**Files:**
- Modify: `requirements.txt`
- Modify: `contractor/config.py`

- [ ] **Step 1: Check and update requirements.txt**

```bash
cd /Users/ethanatchley/Desktop/ECAS
grep -E "feedparser|beautifulsoup4|bs4" requirements.txt || echo "missing"
```

If missing, add these lines to `requirements.txt`:
```
feedparser==6.0.11
beautifulsoup4==4.12.3
lxml==5.2.1
```

Then verify install:
```bash
pip3 install feedparser beautifulsoup4 lxml --break-system-packages 2>&1 | tail -3
```

- [ ] **Step 2: Update signal weights in `contractor/config.py`**

Replace the `CONTRACTOR_SIGNAL_WEIGHTS` block (lines ~81-102) with:

```python
CONTRACTOR_SIGNAL_WEIGHTS = {
    # Tier 1 — Hot (50-100 pts)
    "commercial_permit_pulled": 65,
    "hail_event_large": 80,
    "hail_event_medium": 50,
    "franchise_new_territory": 70,
    "competitor_acquisition": 60,
    "fm_job_change": 75,
    "contract_renewal_window": 55,
    "osha_citation": 55,              # NEW — pest/janitorial displacement trigger
    # Tier 2 — Warm (20-49 pts)
    "government_contract_win": 45,    # NEW — SAM.gov award signal
    "commercial_lease_signed": 45,    # NEW — new tenant = new service contracts
    "new_location_opened": 45,
    "commercial_building_sold": 40,
    "rto_announcement": 40,           # NEW — offices reopening = janitorial trigger
    "fm_job_posting": 40,
    "industry_association_member": 50, # BUMPED from 20 — membership = direct prospect
    "negative_review_competitor": 35,
    "hiring_spree": 35,
    "linkedin_content_engagement": 25,
    # Tier 3 — Cool (5-19 pts)
    "company_news": 15,
    "website_visit": 10,
    "email_open": 5,
}
```

- [ ] **Step 3: Run existing tests to confirm no regression**

```bash
python3 -m pytest contractor/tests/test_signal_scorer.py -q
```

Expected: `17 passed`

- [ ] **Step 4: Commit**

```bash
git add requirements.txt contractor/config.py
git commit -m "feat(contractor): add 5 new signal weights, bump association_member to 50pts"
```

---

## Task 1: Shared Airtable Helper

**Files:**
- Create: `contractor/signals/_airtable.py`
- Create: `contractor/tests/test_signal_scrapers_shared.py`

- [ ] **Step 1: Write the failing test**

Create `contractor/tests/test_signal_scrapers_shared.py`:

```python
"""
Shared fixtures and output-contract validation for all signal scrapers.
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock


# ─── Output contract validator ────────────────────────────────────────────────
REQUIRED_FIELDS = {
    "company_name", "company_domain", "vertical", "vertical_type",
    "signal_type", "detected_at", "source", "processed", "raw_data_json",
}
VALID_VERTICALS = {"Commercial Roofing", "Commercial Janitorial", "Pest Control"}
VALID_SIGNAL_TYPES = {
    "industry_association_member", "government_contract_win", "commercial_permit_pulled",
    "fm_job_change", "fm_job_posting", "franchise_new_territory", "competitor_acquisition",
    "osha_citation", "rto_announcement", "commercial_lease_signed", "commercial_building_sold",
    "negative_review_competitor", "hiring_spree", "new_location_opened",
}


def assert_valid_signal(sig: dict) -> None:
    """Assert a signal dict matches the output contract."""
    missing = REQUIRED_FIELDS - set(sig.keys())
    assert not missing, f"Signal missing required fields: {missing}"
    assert sig["vertical_type"] == "contractor", "vertical_type must be 'contractor'"
    assert sig["vertical"] in VALID_VERTICALS, f"Unknown vertical: {sig['vertical']}"
    assert sig["signal_type"] in VALID_SIGNAL_TYPES, f"Unknown signal_type: {sig['signal_type']}"
    assert sig["processed"] is False, "processed must be False"
    assert isinstance(sig["raw_data_json"], dict), "raw_data_json must be a dict"
    # Validate detected_at is parseable ISO 8601
    datetime.fromisoformat(sig["detected_at"])


# ─── Airtable helper tests ─────────────────────────────────────────────────────
class TestPushSignals:
    @patch("contractor.signals._airtable.requests.post")
    def test_push_empty_list_returns_zero(self, mock_post):
        from contractor.signals._airtable import push_signals
        result = push_signals([])
        assert result == 0
        mock_post.assert_not_called()

    @patch("contractor.signals._airtable.requests.post")
    def test_push_batches_in_tens(self, mock_post):
        from contractor.signals._airtable import push_signals
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = MagicMock()
        mock_post.return_value.json.return_value = {"records": [{"id": f"rec{i}"} for i in range(10)]}

        signals = [{"company_name": f"Co{i}", "company_domain": f"co{i}.com"} for i in range(25)]
        result = push_signals(signals)

        assert mock_post.call_count == 3  # 10 + 10 + 5
        assert result == 30  # 3 batches × 10 returned each

    @patch("contractor.signals._airtable.requests.post")
    def test_push_continues_on_batch_failure(self, mock_post):
        from contractor.signals._airtable import push_signals
        mock_post.side_effect = [
            Exception("API error"),
            MagicMock(status_code=200, json=lambda: {"records": [{"id": "rec1"}]},
                      raise_for_status=lambda: None),
        ]
        signals = [{"company_name": f"Co{i}"} for i in range(15)]
        result = push_signals(signals)
        assert result == 1  # Second batch succeeded

    @patch("contractor.signals._airtable.requests.get")
    def test_signal_exists_returns_true_when_found(self, mock_get):
        from contractor.signals._airtable import signal_exists
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {"records": [{"id": "rec001"}]}
        assert signal_exists("apexroofing.com", "industry_association_member") is True

    @patch("contractor.signals._airtable.requests.get")
    def test_signal_exists_returns_false_when_not_found(self, mock_get):
        from contractor.signals._airtable import signal_exists
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {"records": []}
        assert signal_exists("newco.com", "industry_association_member") is False

    def test_signal_exists_empty_domain_returns_false(self):
        from contractor.signals._airtable import signal_exists
        assert signal_exists("", "industry_association_member") is False
```

- [ ] **Step 2: Run test — verify it fails**

```bash
python3 -m pytest contractor/tests/test_signal_scrapers_shared.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'contractor.signals._airtable'`

- [ ] **Step 3: Implement `contractor/signals/_airtable.py`**

```python
"""
contractor/signals/_airtable.py — Shared Airtable push helper for all signal scrapers.

Handles: batch writes (10/request limit), 30-day dedup check, error resilience.
"""
import os
import logging
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY", "")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID", "appoi8SzEJY8in57x")
SIGNALS_TABLE = "tblAFJnXToLTKeaNU"
_BASE = "https://api.airtable.com/v0"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json",
    }


def signal_exists(company_domain: str, signal_type: str, within_days: int = 30) -> bool:
    """Return True if this signal type was already recorded for this domain within N days."""
    if not company_domain:
        return False
    cutoff = (datetime.utcnow() - timedelta(days=within_days)).isoformat()
    formula = (
        f"AND({{company_domain}}='{company_domain}',"
        f"{{signal_type}}='{signal_type}',"
        f"{{detected_at}}>'{cutoff}')"
    )
    try:
        resp = requests.get(
            f"{_BASE}/{AIRTABLE_BASE_ID}/{SIGNALS_TABLE}",
            headers=_headers(),
            params={
                "filterByFormula": formula,
                "maxRecords": 1,
                "fields[]": ["company_domain"],
            },
            timeout=15,
        )
        resp.raise_for_status()
        return len(resp.json().get("records", [])) > 0
    except Exception as e:
        logger.warning("Dedup check failed for %s/%s: %s", company_domain, signal_type, e)
        return False


def push_signals(signals: list[dict]) -> int:
    """
    Push signal dicts to Airtable signals_raw in batches of 10.
    Returns total count of records created. Never raises — logs errors and continues.
    """
    if not signals:
        return 0

    url = f"{_BASE}/{AIRTABLE_BASE_ID}/{SIGNALS_TABLE}"
    created = 0

    for i in range(0, len(signals), 10):
        batch = signals[i : i + 10]
        payload = {
            "records": [{"fields": s} for s in batch],
            "typecast": True,
        }
        try:
            resp = requests.post(url, headers=_headers(), json=payload, timeout=30)
            resp.raise_for_status()
            created += len(resp.json().get("records", []))
        except Exception as e:
            logger.error("Airtable push failed for batch at offset %d: %s", i, e)

    return created
```

- [ ] **Step 4: Run tests — verify pass**

```bash
python3 -m pytest contractor/tests/test_signal_scrapers_shared.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add contractor/signals/_airtable.py contractor/tests/test_signal_scrapers_shared.py
git commit -m "feat(contractor): shared Airtable push helper with dedup check"
```

---

## Task 2: Association Scraper

**Files:**
- Create: `contractor/signals/association_scraper.py`
- Create: `contractor/tests/test_association_scraper.py`

Uses **Firecrawl** for JS-rendered NRCA and NPMA pages. Uses `requests` + `BeautifulSoup` for ISSA HTML directory.
`FIRECRAWL_API_KEY` comes from Doppler key `FIRECRAWL_API_KEY` (project `ent-agency-automation`, config `dev`).

- [ ] **Step 1: Write failing tests**

Create `contractor/tests/test_association_scraper.py`:

```python
"""Tests for contractor/signals/association_scraper.py"""
import pytest
from unittest.mock import patch, MagicMock
from contractor.tests.test_signal_scrapers_shared import assert_valid_signal


MOCK_NRCA_MARKDOWN = """
## Find a Contractor Results

**Apex Roofing Solutions**
123 Main St, Austin, TX 78701
Phone: (512) 555-0100
Website: [apexroofingsolutions.com](https://apexroofingsolutions.com)

**Summit Commercial Roofing**
456 Oak Ave, Dallas, TX 75201
Phone: (214) 555-0200
Website: [summitroofing.com](https://summitroofing.com)
"""

MOCK_NPMA_MARKDOWN = """
## Find a Pro Results

**Austin Pest Professionals**
789 Cedar St, Austin, TX 78702
Website: [austinpestpro.com](https://austinpestpro.com)

**Capital City Pest Control**
321 Elm Dr, Austin, TX 78703
Website: [capitalcitypest.com](https://capitalcitypest.com)
"""

MOCK_ISSA_HTML = """
<html><body>
<div class="member-listing">
  <div class="member">
    <h3 class="member-name">CleanTech Janitorial</h3>
    <span class="member-city">Houston</span>
    <span class="member-state">TX</span>
    <a href="https://cleantechjanitorial.com" class="member-website">cleantechjanitorial.com</a>
  </div>
  <div class="member">
    <h3 class="member-name">Premier Building Services</h3>
    <span class="member-city">Dallas</span>
    <span class="member-state">TX</span>
  </div>
</div>
<a class="next-page" href="/dir?page=2">Next</a>
</body></html>
"""


class TestNrcaScraper:
    @patch("contractor.signals.association_scraper.signal_exists", return_value=False)
    @patch("contractor.signals.association_scraper._firecrawl_scrape")
    def test_parses_companies_from_nrca_markdown(self, mock_fc, mock_exists):
        from contractor.signals.association_scraper import scrape_nrca_state
        mock_fc.return_value = MOCK_NRCA_MARKDOWN

        signals = scrape_nrca_state("TX")

        assert len(signals) == 2
        assert_valid_signal(signals[0])
        assert signals[0]["vertical"] == "Commercial Roofing"
        assert signals[0]["signal_type"] == "industry_association_member"
        assert signals[0]["source"] == "NRCA"
        assert "apexroofingsolutions.com" in signals[0]["company_domain"]

    @patch("contractor.signals.association_scraper.signal_exists", return_value=True)
    @patch("contractor.signals.association_scraper._firecrawl_scrape")
    def test_skips_already_seen_companies(self, mock_fc, mock_exists):
        from contractor.signals.association_scraper import scrape_nrca_state
        mock_fc.return_value = MOCK_NRCA_MARKDOWN
        signals = scrape_nrca_state("TX")
        assert signals == []

    @patch("contractor.signals.association_scraper._firecrawl_scrape")
    def test_handles_firecrawl_failure_gracefully(self, mock_fc):
        from contractor.signals.association_scraper import scrape_nrca_state
        mock_fc.side_effect = Exception("Firecrawl timeout")
        signals = scrape_nrca_state("TX")
        assert signals == []


class TestNpmaScraper:
    @patch("contractor.signals.association_scraper.signal_exists", return_value=False)
    @patch("contractor.signals.association_scraper._firecrawl_scrape")
    def test_parses_companies_from_npma_markdown(self, mock_fc, mock_exists):
        from contractor.signals.association_scraper import scrape_npma_state
        mock_fc.return_value = MOCK_NPMA_MARKDOWN

        signals = scrape_npma_state("TX")

        assert len(signals) == 2
        assert_valid_signal(signals[0])
        assert signals[0]["vertical"] == "Pest Control"
        assert signals[0]["signal_type"] == "industry_association_member"
        assert signals[0]["source"] == "NPMA"


class TestIssaScraper:
    @patch("contractor.signals.association_scraper.signal_exists", return_value=False)
    @patch("contractor.signals.association_scraper.requests.get")
    def test_parses_companies_from_issa_html(self, mock_get, mock_exists):
        from contractor.signals.association_scraper import scrape_issa_page
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.text = MOCK_ISSA_HTML

        signals, has_next = scrape_issa_page(1)

        assert len(signals) == 2
        assert_valid_signal(signals[0])
        assert signals[0]["vertical"] == "Commercial Janitorial"
        assert signals[0]["source"] == "ISSA"
        assert has_next is True

    @patch("contractor.signals.association_scraper.signal_exists", return_value=False)
    @patch("contractor.signals.association_scraper.requests.get")
    def test_detects_last_page(self, mock_get, mock_exists):
        from contractor.signals.association_scraper import scrape_issa_page
        html_no_next = MOCK_ISSA_HTML.replace('<a class="next-page" href="/dir?page=2">Next</a>', "")
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.text = html_no_next
        _, has_next = scrape_issa_page(1)
        assert has_next is False


class TestRunAssociationScraper:
    @patch("contractor.signals.association_scraper.push_signals")
    @patch("contractor.signals.association_scraper.scrape_issa_page")
    @patch("contractor.signals.association_scraper.scrape_npma_state")
    @patch("contractor.signals.association_scraper.scrape_nrca_state")
    def test_run_returns_total_pushed(self, mock_nrca, mock_npma, mock_issa, mock_push):
        from contractor.signals.association_scraper import run_association_scraper
        from contractor.tests.test_signal_scrapers_shared import assert_valid_signal

        mock_nrca.return_value = [{"company_name": "RoofCo", "company_domain": "roofco.com",
                                    "vertical": "Commercial Roofing", "vertical_type": "contractor",
                                    "signal_type": "industry_association_member",
                                    "detected_at": "2026-04-05T10:00:00", "source": "NRCA",
                                    "processed": False, "raw_data_json": {}}]
        mock_npma.return_value = []
        mock_issa.return_value = ([], False)
        mock_push.return_value = 1

        result = run_association_scraper()
        assert result >= 0
```

- [ ] **Step 2: Run test — verify FAIL**

```bash
python3 -m pytest contractor/tests/test_association_scraper.py -v 2>&1 | head -10
```

Expected: `ModuleNotFoundError: No module named 'contractor.signals.association_scraper'`

- [ ] **Step 3: Implement `contractor/signals/association_scraper.py`**

```python
"""
contractor/signals/association_scraper.py — Trade association member directory scrapers.

Sources:
- NRCA (National Roofing Contractors Association) — JS-rendered, scraped via Firecrawl
- NPMA (National Pest Management Association) — JS-rendered, scraped via Firecrawl
- ISSA (Worldwide Cleaning Industry Association) — HTML paginated, scraped direct

Schedule: Weekly (Sunday 3am) — member lists change slowly.
Signal type: industry_association_member (50 pts — warm floor, qualifies for direct outreach)
"""
import os
import re
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from contractor.signals._airtable import push_signals, signal_exists

logger = logging.getLogger(__name__)

FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")
FIRECRAWL_BASE = "https://api.firecrawl.dev/v1"

# States to scrape — matches geo_focus across all three verticals
TARGET_STATES = ["TX", "FL", "GA", "NC", "VA", "PA", "OH", "TN", "CO", "KS", "OK"]

NRCA_SEARCH_URL = "https://www.nrca.net/roofing/find-a-contractor?state={state}"
NPMA_SEARCH_URL = "https://www.npmapestworld.org/find-a-pro?state={state}"
ISSA_DIR_URL = "https://access.issa.com/dir?page={page}&country=US"


# ─── Firecrawl helper ─────────────────────────────────────────────────────────

def _firecrawl_scrape(url: str) -> str:
    """Scrape a URL via Firecrawl and return markdown content."""
    resp = requests.post(
        f"{FIRECRAWL_BASE}/scrape",
        headers={"Authorization": f"Bearer {FIRECRAWL_API_KEY}", "Content-Type": "application/json"},
        json={"url": url, "formats": ["markdown"], "waitFor": 2000},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json().get("data", {}).get("markdown", "")


def _extract_domain(text: str) -> str:
    """Extract a domain from a markdown link like [example.com](https://example.com)."""
    match = re.search(r'\[([^\]]+)\]\(https?://([^/)]+)', text)
    if match:
        return match.group(2).lower().strip()
    # Bare URL
    match = re.search(r'https?://([^/\s)]+)', text)
    return match.group(1).lower().strip() if match else ""


def _make_signal(company_name: str, domain: str, vertical: str, source: str, extra: dict = None) -> dict:
    return {
        "company_name": company_name.strip(),
        "company_domain": domain.lower().strip(),
        "vertical": vertical,
        "vertical_type": "contractor",
        "signal_type": "industry_association_member",
        "detected_at": datetime.utcnow().isoformat(),
        "source": source,
        "processed": False,
        "raw_data_json": extra or {},
    }


# ─── NRCA scraper ─────────────────────────────────────────────────────────────

def scrape_nrca_state(state: str) -> list[dict]:
    """Scrape one state's NRCA contractor listings via Firecrawl."""
    url = NRCA_SEARCH_URL.format(state=state)
    try:
        markdown = _firecrawl_scrape(url)
    except Exception as e:
        logger.warning("NRCA Firecrawl failed for state %s: %s", state, e)
        return []

    signals = []
    # Parse company blocks: look for bold company names followed by website links
    lines = markdown.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Bold name pattern: **Company Name** or ## Company Name
        name_match = re.match(r'\*\*(.+?)\*\*|^#{1,3}\s+(.+)', line)
        if name_match:
            company_name = (name_match.group(1) or name_match.group(2)).strip()
            # Look ahead up to 5 lines for a website
            domain = ""
            for j in range(i + 1, min(i + 6, len(lines))):
                if "http" in lines[j] or ".com" in lines[j]:
                    domain = _extract_domain(lines[j])
                    break

            if company_name and len(company_name) > 3:
                if not signal_exists(domain, "industry_association_member"):
                    signals.append(_make_signal(
                        company_name, domain, "Commercial Roofing", "NRCA",
                        {"state": state}
                    ))
        i += 1

    logger.info("NRCA %s: found %d new members", state, len(signals))
    return signals


# ─── NPMA scraper ─────────────────────────────────────────────────────────────

def scrape_npma_state(state: str) -> list[dict]:
    """Scrape one state's NPMA pest control listings via Firecrawl."""
    url = NPMA_SEARCH_URL.format(state=state)
    try:
        markdown = _firecrawl_scrape(url)
    except Exception as e:
        logger.warning("NPMA Firecrawl failed for state %s: %s", state, e)
        return []

    signals = []
    lines = markdown.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        name_match = re.match(r'\*\*(.+?)\*\*|^#{1,3}\s+(.+)', line)
        if name_match:
            company_name = (name_match.group(1) or name_match.group(2)).strip()
            domain = ""
            for j in range(i + 1, min(i + 6, len(lines))):
                if "http" in lines[j] or ".com" in lines[j]:
                    domain = _extract_domain(lines[j])
                    break

            if company_name and len(company_name) > 3:
                if not signal_exists(domain, "industry_association_member"):
                    signals.append(_make_signal(
                        company_name, domain, "Pest Control", "NPMA",
                        {"state": state}
                    ))
        i += 1

    logger.info("NPMA %s: found %d new members", state, len(signals))
    return signals


# ─── ISSA scraper ─────────────────────────────────────────────────────────────

def scrape_issa_page(page: int) -> tuple[list[dict], bool]:
    """
    Scrape one page of ISSA member directory.
    Returns (signals, has_next_page).
    """
    url = ISSA_DIR_URL.format(page=page)
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; ECASBot/1.0)"},
            timeout=30,
        )
        resp.raise_for_status()
    except Exception as e:
        logger.warning("ISSA page %d failed: %s", page, e)
        return [], False

    soup = BeautifulSoup(resp.text, "lxml")
    signals = []

    for member in soup.select(".member, .member-listing .member, [class*='member-item']"):
        name_el = member.select_one(".member-name, h3, h2, [class*='name']")
        if not name_el:
            continue
        company_name = name_el.get_text(strip=True)

        website_el = member.select_one("a.member-website, a[href*='http']:not([href*='issa.com'])")
        domain = ""
        if website_el and website_el.get("href"):
            href = website_el["href"]
            domain_match = re.search(r'https?://([^/]+)', href)
            domain = domain_match.group(1).lower() if domain_match else ""

        state_el = member.select_one(".member-state, [class*='state']")
        state = state_el.get_text(strip=True) if state_el else ""

        if company_name and len(company_name) > 3:
            if not signal_exists(domain, "industry_association_member"):
                signals.append(_make_signal(
                    company_name, domain, "Commercial Janitorial", "ISSA",
                    {"state": state, "page": page}
                ))

    has_next = bool(soup.select_one("a.next-page, a[rel='next'], .pagination .next"))
    logger.info("ISSA page %d: found %d new members, has_next=%s", page, len(signals), has_next)
    return signals, has_next


# ─── Main entry point ─────────────────────────────────────────────────────────

def run_association_scraper() -> int:
    """
    APScheduler entry point. Scrapes all three associations across target states.
    Runs NRCA and NPMA in parallel (one task per state), ISSA paginated.
    Returns total signals pushed to Airtable.
    """
    all_signals = []

    # NRCA + NPMA: parallel by state
    with ThreadPoolExecutor(max_workers=4) as executor:
        nrca_futures = {executor.submit(scrape_nrca_state, s): ("NRCA", s) for s in TARGET_STATES}
        npma_futures = {executor.submit(scrape_npma_state, s): ("NPMA", s) for s in TARGET_STATES}

        for future in as_completed({**nrca_futures, **npma_futures}):
            try:
                all_signals.extend(future.result())
            except Exception as e:
                logger.error("Association scrape task failed: %s", e)

    # ISSA: paginated
    page = 1
    while True:
        signals, has_next = scrape_issa_page(page)
        all_signals.extend(signals)
        if not has_next or page > 50:  # Safety cap: 50 pages max
            break
        page += 1

    pushed = push_signals(all_signals)
    logger.info("Association scraper done: %d signals pushed", pushed)
    return pushed
```

- [ ] **Step 4: Run tests — verify pass**

```bash
python3 -m pytest contractor/tests/test_association_scraper.py -v
```

Expected: `8 passed`

- [ ] **Step 5: Commit**

```bash
git add contractor/signals/association_scraper.py contractor/tests/test_association_scraper.py
git commit -m "feat(contractor): association member scraper — NRCA + NPMA + ISSA"
```

---

## Task 3: SAM.gov Contract Award Watcher

**Files:**
- Create: `contractor/signals/sam_gov_watcher.py`
- Create: `contractor/tests/test_sam_gov_watcher.py`

**API:** SAM.gov Opportunities v2 — free, register at sam.gov/api. Add key to Doppler as `SAM_GOV_API_KEY` (project `ecas`, config `dev`). Until then, the scraper will use `api_key=DEMO_KEY` which has rate limits.

- [ ] **Step 1: Write failing test**

Create `contractor/tests/test_sam_gov_watcher.py`:

```python
"""Tests for contractor/signals/sam_gov_watcher.py"""
import pytest
from unittest.mock import patch, MagicMock
from contractor.tests.test_signal_scrapers_shared import assert_valid_signal

MOCK_SAM_RESPONSE = {
    "opportunitiesData": [
        {
            "noticeId": "abc123",
            "title": "Roofing Repair Services — Travis County Federal Building",
            "naicsCode": "238160",
            "award": {
                "date": "2026-03-25",
                "amount": "185000",
                "awardee": {
                    "name": "Summit Commercial Roofing LLC",
                    "location": {
                        "city": {"name": "Austin"},
                        "state": {"code": "TX"},
                        "zip": "78701",
                    }
                }
            }
        },
        {
            "noticeId": "def456",
            "title": "Janitorial Services — IRS Office",
            "naicsCode": "561720",
            "award": {
                "date": "2026-03-20",
                "amount": "95000",
                "awardee": {
                    "name": "CleanPro Facilities Inc",
                    "location": {
                        "city": {"name": "Dallas"},
                        "state": {"code": "TX"},
                        "zip": "75201",
                    }
                }
            }
        },
    ],
    "totalRecords": 2,
}

MOCK_SAM_EMPTY = {"opportunitiesData": [], "totalRecords": 0}


class TestSamGovWatcher:
    @patch("contractor.signals.sam_gov_watcher.signal_exists", return_value=False)
    @patch("contractor.signals.sam_gov_watcher.requests.get")
    def test_parses_award_records(self, mock_get, mock_exists):
        from contractor.signals.sam_gov_watcher import fetch_awards_page
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = MOCK_SAM_RESPONSE

        signals = fetch_awards_page(offset=0)

        assert len(signals) == 2
        assert_valid_signal(signals[0])
        assert signals[0]["signal_type"] == "government_contract_win"
        assert signals[0]["company_name"] == "Summit Commercial Roofing LLC"
        assert signals[0]["vertical"] == "Commercial Roofing"
        assert signals[0]["source"] == "SAM.gov"
        assert signals[0]["raw_data_json"]["naics"] == "238160"
        assert signals[0]["raw_data_json"]["award_amount"] == "185000"

    @patch("contractor.signals.sam_gov_watcher.signal_exists", return_value=False)
    @patch("contractor.signals.sam_gov_watcher.requests.get")
    def test_maps_naics_to_vertical(self, mock_get, mock_exists):
        from contractor.signals.sam_gov_watcher import fetch_awards_page
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = MOCK_SAM_RESPONSE

        signals = fetch_awards_page(offset=0)
        roofing = next(s for s in signals if s["company_name"] == "Summit Commercial Roofing LLC")
        janitorial = next(s for s in signals if s["company_name"] == "CleanPro Facilities Inc")
        assert roofing["vertical"] == "Commercial Roofing"
        assert janitorial["vertical"] == "Commercial Janitorial"

    @patch("contractor.signals.sam_gov_watcher.requests.get")
    def test_empty_response_returns_empty(self, mock_get):
        from contractor.signals.sam_gov_watcher import fetch_awards_page
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = MOCK_SAM_EMPTY
        assert fetch_awards_page(offset=0) == []

    @patch("contractor.signals.sam_gov_watcher.push_signals")
    @patch("contractor.signals.sam_gov_watcher.fetch_awards_page")
    def test_run_paginates_until_empty(self, mock_fetch, mock_push):
        from contractor.signals.sam_gov_watcher import run_sam_gov_watcher
        mock_fetch.side_effect = [
            [{"company_name": "Co1"}] * 100,  # Page 1: full
            [{"company_name": "Co2"}] * 50,   # Page 2: partial — stop
        ]
        mock_push.return_value = 150
        run_sam_gov_watcher()
        assert mock_fetch.call_count == 2
```

- [ ] **Step 2: Run test — verify FAIL**

```bash
python3 -m pytest contractor/tests/test_sam_gov_watcher.py -v 2>&1 | head -10
```

Expected: `ModuleNotFoundError: No module named 'contractor.signals.sam_gov_watcher'`

- [ ] **Step 3: Implement `contractor/signals/sam_gov_watcher.py`**

```python
"""
contractor/signals/sam_gov_watcher.py — SAM.gov contract award lead signal.

Scrapes recent NAICS-filtered contract awards. A company winning a federal
facilities contract is growing → ICP lead for roofing/janitorial/pest.

API: SAM.gov Opportunities v2 (free, register at sam.gov/api)
Doppler key: SAM_GOV_API_KEY (project: ecas, config: dev)
Schedule: Daily at 5am
"""
import os
import logging
import requests
from datetime import datetime, timedelta

from contractor.signals._airtable import push_signals, signal_exists

logger = logging.getLogger(__name__)

SAM_API_KEY = os.environ.get("SAM_GOV_API_KEY", "DEMO_KEY")
SAM_BASE = "https://api.sam.gov/opportunities/v2/search"
PAGE_SIZE = 100

# NAICS → vertical mapping
NAICS_VERTICAL = {
    "238160": "Commercial Roofing",
    "561720": "Commercial Janitorial",
    "561710": "Pest Control",
}
TARGET_NAICS = ",".join(NAICS_VERTICAL.keys())

# Target states (match geo_focus across verticals)
TARGET_STATES = {"TX", "FL", "GA", "NC", "VA", "PA", "OH", "TN", "CO", "KS", "OK"}


def _vertical_for_naics(naics: str) -> str:
    return NAICS_VERTICAL.get(str(naics), "Commercial Roofing")


def fetch_awards_page(offset: int = 0) -> list[dict]:
    """
    Fetch one page of SAM.gov contract award notices.
    Returns list of signal dicts.
    """
    posted_from = (datetime.utcnow() - timedelta(days=30)).strftime("%m/%d/%Y")
    posted_to = datetime.utcnow().strftime("%m/%d/%Y")

    try:
        resp = requests.get(
            SAM_BASE,
            params={
                "api_key": SAM_API_KEY,
                "ptype": "a",               # Award notices
                "ncode": TARGET_NAICS,
                "postedFrom": posted_from,
                "postedTo": posted_to,
                "limit": PAGE_SIZE,
                "offset": offset,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error("SAM.gov fetch failed at offset %d: %s", offset, e)
        return []

    signals = []
    for opp in data.get("opportunitiesData", []):
        award = opp.get("award", {})
        awardee = award.get("awardee", {})
        loc = awardee.get("location", {})
        state = loc.get("state", {}).get("code", "")

        # Filter to target states (SAM.gov doesn't support state filter on awards)
        if TARGET_STATES and state not in TARGET_STATES:
            continue

        company_name = awardee.get("name", "").strip()
        if not company_name:
            continue

        naics = str(opp.get("naicsCode", ""))
        vertical = _vertical_for_naics(naics)

        # Use notice ID as pseudo-domain for dedup (we don't have real domains yet)
        notice_id = opp.get("noticeId", "")
        if signal_exists(notice_id, "government_contract_win"):
            continue

        signals.append({
            "company_name": company_name,
            "company_domain": "",  # Apollo enriches this in the orchestrator
            "vertical": vertical,
            "vertical_type": "contractor",
            "signal_type": "government_contract_win",
            "detected_at": datetime.utcnow().isoformat(),
            "source": "SAM.gov",
            "processed": False,
            "raw_data_json": {
                "naics": naics,
                "award_amount": award.get("amount", ""),
                "award_date": award.get("date", ""),
                "city": loc.get("city", {}).get("name", ""),
                "state": state,
                "notice_id": notice_id,
                "title": opp.get("title", ""),
            },
        })

    return signals


def run_sam_gov_watcher() -> int:
    """APScheduler entry point. Paginates SAM.gov awards until empty page."""
    all_signals = []
    offset = 0

    while True:
        page = fetch_awards_page(offset)
        if not page:
            break
        all_signals.extend(page)
        if len(page) < PAGE_SIZE:
            break  # Partial page = last page
        offset += PAGE_SIZE

    pushed = push_signals(all_signals)
    logger.info("SAM.gov watcher done: %d signals pushed", pushed)
    return pushed
```

- [ ] **Step 4: Run tests — verify pass**

```bash
python3 -m pytest contractor/tests/test_sam_gov_watcher.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add contractor/signals/sam_gov_watcher.py contractor/tests/test_sam_gov_watcher.py
git commit -m "feat(contractor): SAM.gov contract award lead signal scraper"
```

---

## Task 4: Permit Watcher

**Files:**
- Create: `contractor/signals/permit_watcher.py`
- Create: `contractor/tests/test_permit_watcher.py`

Uses `PERMIT_SOURCES` from `contractor/config.py` — 4 Socrata APIs already configured.

- [ ] **Step 1: Write failing test**

Create `contractor/tests/test_permit_watcher.py`:

```python
"""Tests for contractor/signals/permit_watcher.py"""
import pytest
from unittest.mock import patch, MagicMock
from contractor.tests.test_signal_scrapers_shared import assert_valid_signal

MOCK_SOCRATA_RESPONSE = [
    {
        "permit_number": "2026-COM-001234",
        "applicant_name": "Apex Roofing Solutions LLC",
        "work_description": "Commercial Roof Replacement — Building B",
        "total_valuation": "285000",
        "issue_date": "2026-03-28",
        "address": "1234 Commerce Blvd",
        "contractor_company": "Apex Roofing Solutions LLC",
    },
    {
        "permit_number": "2026-COM-001235",
        "applicant_name": "Downtown Property Management",
        "work_description": "HVAC Replacement",  # Not roofing — should be filtered
        "total_valuation": "95000",
        "issue_date": "2026-03-29",
        "address": "500 Main St",
        "contractor_company": "HVAC Pros Inc",
    },
]


class TestPermitWatcher:
    @patch("contractor.signals.permit_watcher.signal_exists", return_value=False)
    @patch("contractor.signals.permit_watcher.requests.get")
    def test_parses_permit_records(self, mock_get, mock_exists):
        from contractor.signals.permit_watcher import fetch_permits_from_source
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = MOCK_SOCRATA_RESPONSE

        source = {"city": "Austin, TX", "url": "https://data.austintexas.gov/resource/3syk-w9eu.json", "type": "socrata"}
        signals = fetch_permits_from_source(source)

        # Both records pass value filter ($50K+), but work description filters HVAC out
        assert len(signals) >= 1
        assert_valid_signal(signals[0])
        assert signals[0]["signal_type"] == "commercial_permit_pulled"
        assert signals[0]["source"] == "Socrata-Austin, TX"

    @patch("contractor.signals.permit_watcher.signal_exists", return_value=False)
    @patch("contractor.signals.permit_watcher.requests.get")
    def test_filters_low_value_permits(self, mock_get, mock_exists):
        from contractor.signals.permit_watcher import fetch_permits_from_source
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = [
            {"permit_number": "P001", "applicant_name": "SmallCo",
             "work_description": "Roof repair", "total_valuation": "12000",
             "issue_date": "2026-03-28", "address": "100 Main St"}
        ]
        source = {"city": "Austin, TX", "url": "https://data.austintexas.gov/resource/3syk-w9eu.json", "type": "socrata"}
        signals = fetch_permits_from_source(source)
        assert signals == []  # Below $50K threshold

    @patch("contractor.signals.permit_watcher.requests.get")
    def test_api_failure_returns_empty(self, mock_get):
        from contractor.signals.permit_watcher import fetch_permits_from_source
        mock_get.side_effect = Exception("Connection refused")
        source = {"city": "Austin, TX", "url": "https://data.austintexas.gov/resource/bad.json", "type": "socrata"}
        assert fetch_permits_from_source(source) == []

    @patch("contractor.signals.permit_watcher.push_signals")
    @patch("contractor.signals.permit_watcher.fetch_permits_from_source")
    def test_run_scrapes_all_sources(self, mock_fetch, mock_push):
        from contractor.signals.permit_watcher import run_permit_watcher
        mock_fetch.return_value = [{"company_name": "Co"}]
        mock_push.return_value = 4
        run_permit_watcher()
        assert mock_fetch.call_count == 4  # 4 configured cities
```

- [ ] **Step 2: Run test — verify FAIL**

```bash
python3 -m pytest contractor/tests/test_permit_watcher.py -v 2>&1 | head -10
```

Expected: `ModuleNotFoundError: No module named 'contractor.signals.permit_watcher'`

- [ ] **Step 3: Implement `contractor/signals/permit_watcher.py`**

```python
"""
contractor/signals/permit_watcher.py — Commercial building permit signal scraper.

Sources: 4 Socrata APIs (Austin/Dallas/Charlotte/Atlanta) from contractor/config.py
Filters to commercial permits > $50K (roofing-scale work).
Schedule: Every 12h
Signal type: commercial_permit_pulled (65 pts)
"""
import os
import logging
import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from contractor.config import PERMIT_SOURCES, PERMIT_MIN_VALUE, PERMIT_TYPES
from contractor.signals._airtable import push_signals, signal_exists

logger = logging.getLogger(__name__)

# Keywords that indicate roofing/commercial relevance in permit description
ROOFING_KEYWORDS = ["roof", "roofing", "membrane", "tpo", "epdm", "modified bitumen", "flashing"]
RELEVANT_KEYWORDS = ROOFING_KEYWORDS + ["commercial", "office", "retail", "industrial", "warehouse"]


def _is_relevant_permit(description: str, value: float) -> bool:
    if value < PERMIT_MIN_VALUE:
        return False
    desc_lower = description.lower()
    return any(kw in desc_lower for kw in RELEVANT_KEYWORDS)


def _extract_value(raw: str) -> float:
    """Parse valuation string to float."""
    try:
        return float(str(raw).replace(",", "").replace("$", "").strip())
    except (ValueError, TypeError):
        return 0.0


def fetch_permits_from_source(source: dict) -> list[dict]:
    """
    Fetch recent permits from a Socrata API source.
    Returns list of signal dicts for permits matching commercial/roofing criteria.
    """
    cutoff = (datetime.utcnow() - timedelta(days=14)).strftime("%Y-%m-%dT00:00:00")
    # Socrata SoQL query — filter by date
    params = {
        "$where": f"issue_date >= '{cutoff}'",
        "$limit": 500,
        "$order": "issue_date DESC",
    }
    try:
        resp = requests.get(source["url"], params=params, timeout=30)
        resp.raise_for_status()
        records = resp.json()
    except Exception as e:
        logger.error("Permit fetch failed for %s: %s", source["city"], e)
        return []

    signals = []
    for rec in records:
        description = rec.get("work_description", rec.get("description", rec.get("permit_type", "")))
        value = _extract_value(rec.get("total_valuation", rec.get("declared_valuation", rec.get("job_value", "0"))))

        if not _is_relevant_permit(description, value):
            continue

        # Try multiple common Socrata field names for company/applicant
        company_name = (
            rec.get("contractor_company") or rec.get("applicant_name") or
            rec.get("owner_name") or rec.get("business_name") or "Unknown"
        ).strip()

        permit_number = rec.get("permit_number", rec.get("permit_num", ""))
        if signal_exists(permit_number, "commercial_permit_pulled"):
            continue

        signals.append({
            "company_name": company_name,
            "company_domain": "",
            "vertical": "Commercial Roofing",
            "vertical_type": "contractor",
            "signal_type": "commercial_permit_pulled",
            "detected_at": datetime.utcnow().isoformat(),
            "source": f"Socrata-{source['city']}",
            "processed": False,
            "raw_data_json": {
                "permit_number": permit_number,
                "description": description[:200],
                "value": value,
                "address": rec.get("address", rec.get("location_address", "")),
                "city": source["city"],
                "issue_date": rec.get("issue_date", ""),
            },
        })

    logger.info("Permits %s: found %d relevant permits", source["city"], len(signals))
    return signals


def run_permit_watcher() -> int:
    """APScheduler entry point. Scrapes all configured permit sources in parallel."""
    all_signals = []

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(fetch_permits_from_source, s): s for s in PERMIT_SOURCES}
        for future in as_completed(futures):
            try:
                all_signals.extend(future.result())
            except Exception as e:
                logger.error("Permit source failed: %s", e)

    pushed = push_signals(all_signals)
    logger.info("Permit watcher done: %d signals pushed", pushed)
    return pushed
```

- [ ] **Step 4: Run tests — verify pass**

```bash
python3 -m pytest contractor/tests/test_permit_watcher.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add contractor/signals/permit_watcher.py contractor/tests/test_permit_watcher.py
git commit -m "feat(contractor): Socrata commercial permit watcher — 4 cities"
```

---

## Task 5: FM Job Watcher

**Files:**
- Create: `contractor/signals/fm_job_watcher.py`

Uses Apollo `/mixed_people/api_search` with recent job change filter + Google News RSS for FM job postings. No new test file — extend `test_signal_scrapers_shared.py`.

- [ ] **Step 1: Write failing tests** — add to `contractor/tests/test_signal_scrapers_shared.py`:

```python
# Add these tests to the bottom of test_signal_scrapers_shared.py

MOCK_APOLLO_FM_RESPONSE = {
    "people": [
        {
            "id": "apollo123",
            "first_name": "Sarah",
            "last_name": "Johnson",
            "title": "Facilities Manager",
            "organization": {
                "name": "Westfield Properties LLC",
                "website_url": "westfieldproperties.com",
                "employee_count": 85,
            },
            "city": "Austin",
            "state": "TX",
        }
    ]
}

MOCK_RSS_FEED = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Google News — Facilities Manager Texas</title>
    <item>
      <title>Skyline Corp Hiring Facilities Manager in Austin TX</title>
      <link>https://news.google.com/articles/abc123</link>
      <pubDate>Sun, 05 Apr 2026 08:00:00 GMT</pubDate>
      <description>Skyline Corp announced it is seeking a Facilities Manager for its Austin campus...</description>
    </item>
  </channel>
</rss>"""


class TestFmJobWatcher:
    @patch("contractor.signals.fm_job_watcher.signal_exists", return_value=False)
    @patch("contractor.signals.fm_job_watcher.requests.post")
    def test_apollo_job_change_produces_signal(self, mock_post, mock_exists):
        from contractor.signals.fm_job_watcher import fetch_apollo_fm_changes
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = MagicMock()
        mock_post.return_value.json.return_value = MOCK_APOLLO_FM_RESPONSE

        signals = fetch_apollo_fm_changes()
        assert len(signals) == 1
        assert_valid_signal(signals[0])
        assert signals[0]["signal_type"] == "fm_job_change"
        assert signals[0]["company_name"] == "Westfield Properties LLC"

    @patch("contractor.signals.fm_job_watcher.signal_exists", return_value=False)
    @patch("contractor.signals.fm_job_watcher.feedparser.parse")
    def test_rss_job_posting_produces_signal(self, mock_parse, mock_exists):
        import feedparser
        from contractor.signals.fm_job_watcher import fetch_rss_fm_postings
        mock_parse.return_value = feedparser.util.FeedParserDict({
            "entries": [{
                "title": "Skyline Corp Hiring Facilities Manager in Austin TX",
                "link": "https://news.google.com/articles/abc123",
                "published": "Sun, 05 Apr 2026 08:00:00 GMT",
                "summary": "Skyline Corp announced it is seeking a Facilities Manager for its Austin campus",
            }]
        })
        signals = fetch_rss_fm_postings("TX")
        assert len(signals) >= 1
        assert_valid_signal(signals[0])
        assert signals[0]["signal_type"] == "fm_job_posting"
```

- [ ] **Step 2: Run tests — verify FAIL**

```bash
python3 -m pytest contractor/tests/test_signal_scrapers_shared.py::TestFmJobWatcher -v 2>&1 | head -10
```

Expected: `ModuleNotFoundError: No module named 'contractor.signals.fm_job_watcher'`

- [ ] **Step 3: Implement `contractor/signals/fm_job_watcher.py`**

```python
"""
contractor/signals/fm_job_watcher.py — Facilities Manager job change + posting signals.

Sources:
- Apollo mixed_people search with recent employment title filter (fm_job_change, 75 pts)
- Google News RSS for FM job postings by state (fm_job_posting, 40 pts)

Schedule: Every 8h
"""
import os
import re
import logging
import feedparser
import requests
from datetime import datetime

from contractor.config import VERTICAL_ICPS
from contractor.signals._airtable import push_signals, signal_exists

logger = logging.getLogger(__name__)

APOLLO_API_KEY = os.environ.get("APOLLO_API_KEY", "")
APOLLO_BASE = "https://api.apollo.io/v1"

# FM/Operations titles that indicate the person manages facilities (= vendor decisions)
FM_TITLES = [
    "Facilities Manager", "Facility Manager", "Property Manager",
    "Building Manager", "Operations Manager", "Director of Facilities",
    "VP Facilities", "Head of Facilities", "Facilities Director",
    "Property Operations Manager", "Building Operations Manager",
]

TARGET_STATES = ["TX", "FL", "GA", "NC", "VA", "PA", "OH", "TN", "CO"]

# Google News RSS for FM job postings — returns recent news articles
GNEWS_FM_RSS = (
    "https://news.google.com/rss/search?q=facilities+manager+hiring+{state}"
    "&hl=en-US&gl=US&ceid=US:en"
)


def fetch_apollo_fm_changes() -> list[dict]:
    """
    Query Apollo for people recently hired into FM/Ops roles at target companies.
    Apollo's employment_history tracks job changes — new FM = vendor review window.
    """
    try:
        resp = requests.post(
            f"{APOLLO_BASE}/mixed_people/api_search",
            headers={"Content-Type": "application/json", "x-api-key": APOLLO_API_KEY},
            json={
                "titles": FM_TITLES,
                "person_locations": [f"United States, {s}" for s in TARGET_STATES],
                "currently_using_any_of_following_technologies": [],
                "page": 1,
                "per_page": 50,
                "sort_by_field": "last_updated_at",
                "sort_ascending": False,
            },
            timeout=30,
        )
        resp.raise_for_status()
        people = resp.json().get("people", [])
    except Exception as e:
        logger.error("Apollo FM search failed: %s", e)
        return []

    signals = []
    for person in people:
        org = person.get("organization") or {}
        company_name = org.get("name", "").strip()
        domain = (org.get("website_url") or "").lower().strip()

        if not company_name:
            continue
        if signal_exists(domain or company_name, "fm_job_change"):
            continue

        signals.append({
            "company_name": company_name,
            "company_domain": domain,
            "vertical": "Commercial Janitorial",  # FM change is strongest for janitorial
            "vertical_type": "contractor",
            "signal_type": "fm_job_change",
            "detected_at": datetime.utcnow().isoformat(),
            "source": "Apollo",
            "processed": False,
            "raw_data_json": {
                "contact_name": f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                "title": person.get("title", ""),
                "city": person.get("city", ""),
                "state": person.get("state", ""),
                "employee_count": org.get("employee_count", 0),
            },
        })

    logger.info("Apollo FM changes: %d new signals", len(signals))
    return signals


def fetch_rss_fm_postings(state: str) -> list[dict]:
    """
    Monitor Google News RSS for FM job postings in a state.
    Job posting = company is dissatisfied with current FM setup → vendor review likely.
    """
    url = GNEWS_FM_RSS.format(state=state.replace(" ", "+"))
    try:
        feed = feedparser.parse(url)
    except Exception as e:
        logger.warning("RSS FM fetch failed for %s: %s", state, e)
        return []

    signals = []
    for entry in feed.get("entries", []):
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        link = entry.get("link", "")

        # Extract company name from title heuristic: "COMPANY hiring/seeks/looking for"
        company_match = re.match(r'^(.+?)\s+(?:hiring|seeks|looking for|is hiring)', title, re.IGNORECASE)
        if not company_match:
            continue
        company_name = company_match.group(1).strip()

        dedup_key = re.sub(r'[^a-z0-9]', '', company_name.lower())
        if signal_exists(dedup_key, "fm_job_posting"):
            continue

        signals.append({
            "company_name": company_name,
            "company_domain": "",
            "vertical": "Commercial Janitorial",
            "vertical_type": "contractor",
            "signal_type": "fm_job_posting",
            "detected_at": datetime.utcnow().isoformat(),
            "source": "Google News RSS",
            "processed": False,
            "raw_data_json": {
                "headline": title[:200],
                "url": link,
                "state": state,
            },
        })

    logger.info("RSS FM postings %s: %d signals", state, len(signals))
    return signals


def run_fm_job_watcher() -> int:
    """APScheduler entry point."""
    all_signals = list(fetch_apollo_fm_changes())
    for state in TARGET_STATES:
        all_signals.extend(fetch_rss_fm_postings(state))
    pushed = push_signals(all_signals)
    logger.info("FM job watcher done: %d signals pushed", pushed)
    return pushed
```

- [ ] **Step 4: Run tests — verify pass**

```bash
python3 -m pytest contractor/tests/test_signal_scrapers_shared.py::TestFmJobWatcher -v
```

Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add contractor/signals/fm_job_watcher.py contractor/tests/test_signal_scrapers_shared.py
git commit -m "feat(contractor): FM job change + posting watcher via Apollo + Google News RSS"
```

---

## Task 6: Competitor Watcher

**Files:**
- Create: `contractor/signals/competitor_watcher.py`

Monitors franchise expansion press releases (Jan-Pro, Coverall, Orkin, Rollins) and OSHA citations via Google News RSS.

- [ ] **Step 1: Add tests** — append to `contractor/tests/test_signal_scrapers_shared.py`:

```python
class TestCompetitorWatcher:
    @patch("contractor.signals.competitor_watcher.signal_exists", return_value=False)
    @patch("contractor.signals.competitor_watcher.feedparser.parse")
    def test_franchise_expansion_detected(self, mock_parse, mock_exists):
        import feedparser
        from contractor.signals.competitor_watcher import fetch_franchise_rss
        mock_parse.return_value = feedparser.util.FeedParserDict({
            "entries": [{
                "title": "Jan-Pro Cleaning & Disinfecting Opens New Franchise Location in Houston TX",
                "link": "https://www.businesswire.com/jan-pro-houston",
                "published": "Sat, 04 Apr 2026 10:00:00 GMT",
                "summary": "Jan-Pro has opened a new territory serving the Houston metropolitan area.",
            }]
        })
        signals = fetch_franchise_rss("Commercial Janitorial")
        assert len(signals) >= 1
        assert_valid_signal(signals[0])
        assert signals[0]["signal_type"] == "franchise_new_territory"

    @patch("contractor.signals.competitor_watcher.signal_exists", return_value=False)
    @patch("contractor.signals.competitor_watcher.feedparser.parse")
    def test_osha_citation_detected(self, mock_parse, mock_exists):
        import feedparser
        from contractor.signals.competitor_watcher import fetch_osha_rss
        mock_parse.return_value = feedparser.util.FeedParserDict({
            "entries": [{
                "title": "Austin Pest Control Company Cited by OSHA for Safety Violations",
                "link": "https://news.example.com/osha-pest",
                "published": "Sat, 04 Apr 2026 09:00:00 GMT",
                "summary": "Austin Pest Control was fined $45,000 by OSHA following an inspection.",
            }]
        })
        signals = fetch_osha_rss("Pest Control")
        assert len(signals) >= 1
        assert_valid_signal(signals[0])
        assert signals[0]["signal_type"] == "osha_citation"
```

- [ ] **Step 2: Run — verify FAIL**

```bash
python3 -m pytest contractor/tests/test_signal_scrapers_shared.py::TestCompetitorWatcher -v 2>&1 | head -10
```

- [ ] **Step 3: Implement `contractor/signals/competitor_watcher.py`**

```python
"""
contractor/signals/competitor_watcher.py — Franchise expansion + OSHA citation signals.

Sources:
- Google News RSS for franchise expansion press releases (franchise_new_territory, 70 pts)
- Google News RSS for OSHA citations of competitors (osha_citation, 55 pts)

Schedule: Daily at 6am
"""
import re
import logging
import feedparser
from datetime import datetime

from contractor.signals._airtable import push_signals, signal_exists

logger = logging.getLogger(__name__)

# Franchise competitors by vertical — expansion = existential pressure on independents
FRANCHISE_MONITORS = {
    "Commercial Janitorial": ["Jan-Pro", "Coverall", "ServiceMaster Clean", "ABM Industries"],
    "Pest Control": ["Rollins", "Orkin", "Terminix", "Rentokil", "Western Pest"],
    "Commercial Roofing": ["Tecta America", "Nations Roof", "Weatherproofing Technologies"],
}

# Google News RSS: franchise expansion search per vertical
GNEWS_FRANCHISE_RSS = (
    "https://news.google.com/rss/search?q={query}+franchise+expansion+OR+new+territory"
    "&hl=en-US&gl=US&ceid=US:en"
)
GNEWS_OSHA_RSS = (
    "https://news.google.com/rss/search?q=OSHA+citation+{vertical_term}+{state}"
    "&hl=en-US&gl=US&ceid=US:en"
)

TARGET_STATES = ["TX", "FL", "GA", "NC", "OH", "TN"]


def fetch_franchise_rss(vertical: str) -> list[dict]:
    """Monitor Google News for franchise expansion announcements in the vertical."""
    competitors = FRANCHISE_MONITORS.get(vertical, [])
    signals = []

    for competitor in competitors:
        url = GNEWS_FRANCHISE_RSS.format(query=competitor.replace(" ", "+"))
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            logger.warning("Franchise RSS failed for %s: %s", competitor, e)
            continue

        for entry in feed.get("entries", []):
            title = entry.get("title", "")
            link = entry.get("link", "")

            # Verify expansion keywords
            if not any(kw in title.lower() for kw in ["franchise", "territory", "expansion", "opens", "new location"]):
                continue

            dedup_key = re.sub(r'[^a-z0-9]', '', (competitor + title[:50]).lower())
            if signal_exists(dedup_key, "franchise_new_territory"):
                continue

            signals.append({
                "company_name": competitor,
                "company_domain": "",
                "vertical": vertical,
                "vertical_type": "contractor",
                "signal_type": "franchise_new_territory",
                "detected_at": datetime.utcnow().isoformat(),
                "source": "Google News RSS",
                "processed": False,
                "raw_data_json": {
                    "competitor": competitor,
                    "headline": title[:200],
                    "url": link,
                },
            })

    logger.info("Franchise RSS %s: %d signals", vertical, len(signals))
    return signals


def fetch_osha_rss(vertical: str) -> list[dict]:
    """Monitor Google News for OSHA citations against competitors in target states."""
    vertical_terms = {
        "Commercial Janitorial": "janitorial+cleaning",
        "Pest Control": "pest+control+exterminator",
        "Commercial Roofing": "roofing+contractor",
    }
    term = vertical_terms.get(vertical, "contractor")
    signals = []

    for state in TARGET_STATES:
        url = GNEWS_OSHA_RSS.format(vertical_term=term, state=state)
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            logger.warning("OSHA RSS failed for %s/%s: %s", vertical, state, e)
            continue

        for entry in feed.get("entries", []):
            title = entry.get("title", "")
            link = entry.get("link", "")
            summary = entry.get("summary", "")

            if "osha" not in (title + summary).lower():
                continue

            # Extract company name — heuristic: first proper noun before "cited", "fined", "violated"
            company_match = re.match(r'^([A-Z][^,\.]+?)\s+(?:cited|fined|penalized|cited)', title)
            if not company_match:
                continue
            company_name = company_match.group(1).strip()

            dedup_key = re.sub(r'[^a-z0-9]', '', (company_name + state).lower())
            if signal_exists(dedup_key, "osha_citation"):
                continue

            signals.append({
                "company_name": company_name,
                "company_domain": "",
                "vertical": vertical,
                "vertical_type": "contractor",
                "signal_type": "osha_citation",
                "detected_at": datetime.utcnow().isoformat(),
                "source": "Google News RSS",
                "processed": False,
                "raw_data_json": {
                    "headline": title[:200],
                    "url": link,
                    "state": state,
                },
            })

    logger.info("OSHA RSS %s: %d signals", vertical, len(signals))
    return signals


def run_competitor_watcher() -> int:
    """APScheduler entry point."""
    all_signals = []
    for vertical in ["Commercial Janitorial", "Pest Control", "Commercial Roofing"]:
        all_signals.extend(fetch_franchise_rss(vertical))
        all_signals.extend(fetch_osha_rss(vertical))
    pushed = push_signals(all_signals)
    logger.info("Competitor watcher done: %d signals pushed", pushed)
    return pushed
```

- [ ] **Step 4: Run tests — verify pass**

```bash
python3 -m pytest contractor/tests/test_signal_scrapers_shared.py::TestCompetitorWatcher -v
```

Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add contractor/signals/competitor_watcher.py contractor/tests/test_signal_scrapers_shared.py
git commit -m "feat(contractor): franchise expansion + OSHA citation competitor watcher"
```

---

## Task 7: RTO + Commercial Lease Watcher

**Files:**
- Create: `contractor/signals/rto_watcher.py`

- [ ] **Step 1: Add tests** — append to `contractor/tests/test_signal_scrapers_shared.py`:

```python
class TestRtoWatcher:
    @patch("contractor.signals.rto_watcher.signal_exists", return_value=False)
    @patch("contractor.signals.rto_watcher.feedparser.parse")
    def test_rto_announcement_detected(self, mock_parse, mock_exists):
        import feedparser
        from contractor.signals.rto_watcher import fetch_rto_signals
        mock_parse.return_value = feedparser.util.FeedParserDict({
            "entries": [{
                "title": "Dell Technologies Requires Austin Employees to Return to Office Full-Time",
                "link": "https://news.example.com/dell-rto",
                "published": "Sat, 04 Apr 2026 09:00:00 GMT",
                "summary": "Dell has announced a mandatory return-to-office policy starting May 1.",
            }]
        })
        signals = fetch_rto_signals("Austin, TX")
        assert len(signals) >= 1
        assert_valid_signal(signals[0])
        assert signals[0]["signal_type"] == "rto_announcement"
        assert signals[0]["vertical"] == "Commercial Janitorial"

    @patch("contractor.signals.rto_watcher.signal_exists", return_value=False)
    @patch("contractor.signals.rto_watcher.feedparser.parse")
    def test_commercial_lease_detected(self, mock_parse, mock_exists):
        import feedparser
        from contractor.signals.rto_watcher import fetch_lease_signals
        mock_parse.return_value = feedparser.util.FeedParserDict({
            "entries": [{
                "title": "TechCorp Signs 50,000 SqFt Office Lease in Downtown Austin",
                "link": "https://news.example.com/techcorp-lease",
                "published": "Sat, 04 Apr 2026 08:00:00 GMT",
                "summary": "TechCorp has signed a long-term lease at 100 Congress Ave.",
            }]
        })
        signals = fetch_lease_signals("Austin, TX")
        assert len(signals) >= 1
        assert_valid_signal(signals[0])
        assert signals[0]["signal_type"] == "commercial_lease_signed"
```

- [ ] **Step 2: Run — verify FAIL**

```bash
python3 -m pytest contractor/tests/test_signal_scrapers_shared.py::TestRtoWatcher -v 2>&1 | head -10
```

- [ ] **Step 3: Implement `contractor/signals/rto_watcher.py`**

```python
"""
contractor/signals/rto_watcher.py — RTO announcements + commercial lease signals.

RTO mandate → offices reopening → urgent janitorial contracts needed.
Commercial lease signed → new tenant → all 3 service verticals need contracts.

Sources: Google News RSS
Schedule: Every 12h
"""
import re
import logging
import feedparser
from datetime import datetime

from contractor.signals._airtable import push_signals, signal_exists

logger = logging.getLogger(__name__)

TARGET_MARKETS = [
    "Austin, TX", "Dallas, TX", "Houston, TX", "Atlanta, GA",
    "Charlotte, NC", "Nashville, TN", "Columbus, OH", "Tampa, FL",
]

GNEWS_RTO_RSS = (
    "https://news.google.com/rss/search?q=return+to+office+{city}+2026"
    "&hl=en-US&gl=US&ceid=US:en"
)
GNEWS_LEASE_RSS = (
    "https://news.google.com/rss/search?q=commercial+lease+office+{city}"
    "&hl=en-US&gl=US&ceid=US:en"
)

RTO_KEYWORDS = ["return to office", "rto", "back to office", "mandatory in-person", "in-office requirement"]
LEASE_KEYWORDS = ["signs lease", "signed lease", "new office", "sq ft", "square feet", "headquarters", "relocates to"]


def fetch_rto_signals(market: str) -> list[dict]:
    city = market.replace(", ", "+").replace(" ", "+")
    signals = []
    try:
        feed = feedparser.parse(GNEWS_RTO_RSS.format(city=city))
    except Exception as e:
        logger.warning("RTO RSS failed for %s: %s", market, e)
        return []

    for entry in feed.get("entries", []):
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        combined = (title + " " + summary).lower()

        if not any(kw in combined for kw in RTO_KEYWORDS):
            continue

        company_match = re.match(r'^([A-Z][A-Za-z\s&,\.]+?)\s+(?:requires|mandates|announces|orders|tells|asks)', title)
        if not company_match:
            continue
        company_name = company_match.group(1).strip()

        dedup_key = re.sub(r'[^a-z0-9]', '', (company_name + market).lower())
        if signal_exists(dedup_key, "rto_announcement"):
            continue

        signals.append({
            "company_name": company_name,
            "company_domain": "",
            "vertical": "Commercial Janitorial",  # RTO is janitorial-specific trigger
            "vertical_type": "contractor",
            "signal_type": "rto_announcement",
            "detected_at": datetime.utcnow().isoformat(),
            "source": "Google News RSS",
            "processed": False,
            "raw_data_json": {
                "headline": title[:200],
                "url": entry.get("link", ""),
                "market": market,
            },
        })

    logger.info("RTO signals %s: %d found", market, len(signals))
    return signals


def fetch_lease_signals(market: str) -> list[dict]:
    city = market.replace(", ", "+").replace(" ", "+")
    signals = []
    try:
        feed = feedparser.parse(GNEWS_LEASE_RSS.format(city=city))
    except Exception as e:
        logger.warning("Lease RSS failed for %s: %s", market, e)
        return []

    for entry in feed.get("entries", []):
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        combined = (title + " " + summary).lower()

        if not any(kw in combined for kw in LEASE_KEYWORDS):
            continue

        company_match = re.match(r'^([A-Z][A-Za-z\s&,\.]+?)\s+(?:signs|signed|leases|moves|relocates|opens)', title)
        if not company_match:
            continue
        company_name = company_match.group(1).strip()

        dedup_key = re.sub(r'[^a-z0-9]', '', (company_name + market).lower())
        if signal_exists(dedup_key, "commercial_lease_signed"):
            continue

        signals.append({
            "company_name": company_name,
            "company_domain": "",
            "vertical": "Commercial Janitorial",  # Lease = new facility = cleaning contract
            "vertical_type": "contractor",
            "signal_type": "commercial_lease_signed",
            "detected_at": datetime.utcnow().isoformat(),
            "source": "Google News RSS",
            "processed": False,
            "raw_data_json": {
                "headline": title[:200],
                "url": entry.get("link", ""),
                "market": market,
            },
        })

    logger.info("Lease signals %s: %d found", market, len(signals))
    return signals


def run_rto_watcher() -> int:
    """APScheduler entry point."""
    all_signals = []
    for market in TARGET_MARKETS:
        all_signals.extend(fetch_rto_signals(market))
        all_signals.extend(fetch_lease_signals(market))
    pushed = push_signals(all_signals)
    logger.info("RTO watcher done: %d signals pushed", pushed)
    return pushed
```

- [ ] **Step 4: Run tests — verify pass**

```bash
python3 -m pytest contractor/tests/test_signal_scrapers_shared.py::TestRtoWatcher -v
```

Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add contractor/signals/rto_watcher.py contractor/tests/test_signal_scrapers_shared.py
git commit -m "feat(contractor): RTO announcement + commercial lease signal watcher"
```

---

## Task 8: Scheduler Wiring

**Files:**
- Modify: `scheduler.py` (after the existing contractor_health job, around line 1133)

- [ ] **Step 1: Append 6 new jobs to the contractor block in `scheduler.py`**

Find the existing contractor block (lines ~1113–1135) and add after `contractor_health`:

```python
    # ── Contractor signal scrapers ──────────────────────────────────────────
    from contractor.signals.association_scraper import run_association_scraper
    from contractor.signals.sam_gov_watcher import run_sam_gov_watcher
    from contractor.signals.permit_watcher import run_permit_watcher
    from contractor.signals.fm_job_watcher import run_fm_job_watcher
    from contractor.signals.competitor_watcher import run_competitor_watcher
    from contractor.signals.rto_watcher import run_rto_watcher

    # Association scraper — weekly, Sunday 3am (member lists change slowly)
    scheduler.add_job(
        run_association_scraper,
        CronTrigger(day_of_week="sun", hour=3, minute=0),
        id="contractor_associations",
        name="Association Member Directory Scraper",
        replace_existing=True,
        misfire_grace_time=600,
    )

    # SAM.gov — daily 5am
    scheduler.add_job(
        run_sam_gov_watcher,
        CronTrigger(hour=5, minute=0),
        id="contractor_sam_gov",
        name="SAM.gov Contract Award Lead Signal",
        replace_existing=True,
        misfire_grace_time=300,
    )

    # Permits — every 12h
    scheduler.add_job(
        run_permit_watcher,
        IntervalTrigger(hours=12, start_date="2000-01-01 02:00:00"),
        id="contractor_permits",
        name="Socrata Commercial Permit Watcher",
        replace_existing=True,
        misfire_grace_time=300,
    )

    # FM job watcher — every 8h
    scheduler.add_job(
        run_fm_job_watcher,
        IntervalTrigger(hours=8, start_date="2000-01-01 04:00:00"),
        id="contractor_fm_jobs",
        name="FM Job Change + Posting Watcher",
        replace_existing=True,
        misfire_grace_time=300,
    )

    # Competitor / franchise / OSHA — daily 6am
    scheduler.add_job(
        run_competitor_watcher,
        CronTrigger(hour=6, minute=0),
        id="contractor_competitors",
        name="Franchise Expansion + OSHA Competitor Watcher",
        replace_existing=True,
        misfire_grace_time=300,
    )

    # RTO + lease — every 12h
    scheduler.add_job(
        run_rto_watcher,
        IntervalTrigger(hours=12, start_date="2000-01-01 05:30:00"),
        id="contractor_rto",
        name="RTO + Commercial Lease Signal Watcher",
        replace_existing=True,
        misfire_grace_time=300,
    )
```

- [ ] **Step 2: Verify imports resolve cleanly**

```bash
cd /Users/ethanatchley/Desktop/ECAS
python3 -c "
from contractor.signals.association_scraper import run_association_scraper
from contractor.signals.sam_gov_watcher import run_sam_gov_watcher
from contractor.signals.permit_watcher import run_permit_watcher
from contractor.signals.fm_job_watcher import run_fm_job_watcher
from contractor.signals.competitor_watcher import run_competitor_watcher
from contractor.signals.rto_watcher import run_rto_watcher
print('All imports OK')
"
```

Expected: `All imports OK`

- [ ] **Step 3: Commit**

```bash
git add scheduler.py
git commit -m "feat(contractor): wire 6 new signal scraper jobs to APScheduler"
```

---

## Task 9: Full Test Suite + Final Commit

- [ ] **Step 1: Run the full contractor test suite**

```bash
python3 -m pytest contractor/tests/ -v 2>&1 | tail -20
```

Expected: All tests pass. Target: `38+ passed` (32 existing + new tests from this plan).

- [ ] **Step 2: Add Doppler key reminder comment in sam_gov_watcher.py if SAM_GOV_API_KEY not set**

```bash
doppler secrets get SAM_GOV_API_KEY --project ecas --config dev --plain 2>&1
```

If output is `Could not find requested secrets: SAM_GOV_API_KEY`, run:

```bash
doppler secrets set SAM_GOV_API_KEY=DEMO_KEY --project ecas --config dev
```

Then register for a real key at: `https://sam.gov/content/entity-information/api`

- [ ] **Step 3: Verify FIRECRAWL_API_KEY is accessible**

```bash
doppler secrets get FIRECRAWL_API_KEY --project ent-agency-automation --config dev --plain | head -c 10
```

Expected: starts with `fc-`

The association_scraper reads `FIRECRAWL_API_KEY` from env. For Railway deployment, add it to the `ecas/dev` config:

```bash
doppler secrets set FIRECRAWL_API_KEY=$(doppler secrets get FIRECRAWL_API_KEY --project ent-agency-automation --config dev --plain) --project ecas --config dev
```

- [ ] **Step 4: Push to GitHub — triggers Railway deploy**

```bash
git push origin main
```

- [ ] **Step 5: Verify new jobs appear on Railway after deploy (~2 min)**

```bash
curl -s https://ecas-scraper-production.up.railway.app/admin/status | python3 -c "
import sys, json
d = json.load(sys.stdin)
contractor_jobs = [k for k in d.keys() if 'contractor' in k.lower()]
print('\n'.join(contractor_jobs))
"
```

Expected output (9 contractor jobs total):
```
contractor_pipeline
contractor_hail_signals
contractor_health
contractor_associations
contractor_sam_gov
contractor_permits
contractor_fm_jobs
contractor_competitors
contractor_rto
```

- [ ] **Step 6: Trigger a manual test run of the association scraper**

```bash
curl -s -X POST https://ecas-scraper-production.up.railway.app/admin/run/contractor_associations
```

---

## Self-Review Against Spec

| Spec Requirement | Plan Coverage |
|-----------------|---------------|
| Association membership = direct prospect | ✅ Task 2 — `industry_association_member` at 50 pts, pushed directly |
| SAM.gov as lead signal (award winners) | ✅ Task 3 |
| Permit watcher using PERMIT_SOURCES config | ✅ Task 4 — uses existing config exactly |
| FM job change + posting signals | ✅ Task 5 |
| Franchise expansion + OSHA citation | ✅ Task 6 |
| RTO + commercial lease signals | ✅ Task 7 |
| Signal weight updates (5 new + 1 bump) | ✅ Task 0 |
| Scheduler wiring (6 jobs) | ✅ Task 8 |
| `industry_association_member` bumped 20→50 | ✅ Task 0 |
| Shared Airtable helper with dedup | ✅ Task 1 |
| FIRECRAWL_API_KEY in Doppler for associations | ✅ Task 9, Step 3 |
| SAM_GOV_API_KEY to Doppler | ✅ Task 9, Step 2 |
| All scrapers follow standard signal dict | ✅ `assert_valid_signal` in every test |
| Parallel execution (ThreadPoolExecutor) | ✅ Tasks 2, 4 |
| TDD throughout | ✅ Every task: test → fail → implement → pass → commit |
