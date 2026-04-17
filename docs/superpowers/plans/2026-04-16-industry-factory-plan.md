# Industry Factory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a YAML-driven Industry Factory that onboards new industries (ContractMotion EPC track + AI Automation for blue-collar track) end-to-end with ≤5 min human work per industry and zero first-run debugging.

**Architecture:** Config-as-data (one YAML per industry) → orchestrator (`industry_runner.py`) → directory auto-discovery (Perplexity + Claude) → universal scraper (Firecrawl/Airtop/Browserbase) → tech-stack enrichment (Wappalyzer + BuiltWith) → scoring (positive OR negative-tech-stack mode) → existing Apollo/FindyMail/Smartlead pipeline → post-run watchdogs + health dashboard.

**Tech Stack:** Python 3.11, FastAPI, Pydantic v2, pytest, PyYAML, python-Wappalyzer, requests, APScheduler, SQLite (cache), Doppler (secrets), Railway (deploy).

**Spec:** `docs/superpowers/specs/2026-04-16-industry-factory-design.md`

**Branch/Worktree:** Work in `~/Desktop/ECAS-industry-factory/` worktree on branch `industry-factory`. Do not touch live ECAS until Wave 3 validation passes.

---

## File Structure

### New files

| Path | Purpose |
|---|---|
| `industries/_schema.py` | Pydantic model for industry YAML |
| `industries/loader.py` | YAML load + validate + defaults |
| `industries/data_center.yaml` | DC config (migrated from config.py) |
| `industries/water.yaml` | Water config (migrated from config.py) |
| `industries/commercial_roofing.yaml` | Blue-collar AI automation vertical |
| `industries/commercial_glass.yaml` | Blue-collar AI automation vertical |
| `industries/commercial_cleaning.yaml` | Blue-collar AI automation vertical |
| `discovery/__init__.py` | Package init |
| `discovery/directory_finder.py` | Perplexity + Claude URL discovery |
| `discovery/universal_scraper.py` | Firecrawl/Airtop/Browserbase router |
| `enrichment/tech_stack.py` | Wappalyzer + optional BuiltWith + SQLite cache |
| `enrichment/compliance.py` | EU/CA pre-enrollment filter |
| `enrichment/signal_ttl.py` | Stale-lead sweeper |
| `signals/industry_runner.py` | Orchestrator entrypoint |
| `ops/__init__.py` | Package init |
| `ops/campaign_guard.py` | Auto-pause + warmup pool |
| `ops/deliverability_watchdog.py` | GlockApps/Mailreach daily check |
| `ops/oauth_refresh.py` | Gmail/GWS token refresh cron |
| `ops/health_dashboard.py` | `/admin/dashboard` endpoint |
| `tests/conftest.py` | Pytest fixtures (shared) |
| `tests/test_industries_schema.py` | YAML schema tests |
| `tests/test_industries_loader.py` | Loader tests |
| `tests/test_directory_finder.py` | Directory discovery tests |
| `tests/test_universal_scraper.py` | Scraper router tests |
| `tests/test_tech_stack.py` | Tech-stack enrichment tests |
| `tests/test_scoring_modes.py` | Scoring mode tests |
| `tests/test_industry_runner.py` | Orchestrator tests |
| `tests/test_compliance.py` | EU/CA filter tests |
| `tests/test_campaign_guard.py` | Auto-pause tests |
| `tests/test_health_dashboard.py` | Dashboard tests |
| `tests/fixtures/industries/test_industry.yaml` | Fixture YAML |

### Modified files

| Path | Lines | Change |
|---|---|---|
| `config.py` | +10 | Add `INDUSTRIES_DIR`, remove hardcoded `SECTOR_CAMPAIGN_MAP` (loader replaces) |
| `enrichment/health.py` | +90 | Add probes: Perplexity, Firecrawl, Browserbase, Airtop, Wappalyzer, landing-page, campaign-state, sender-pool, OAuth |
| `lead_priority_scoring.py` | +80 | Add `negative_tech_stack` + `hybrid` scoring modes |
| `api/main.py` | +30 | Add `POST /admin/run/industry/{slug}`, `GET /admin/dashboard` |
| `scheduler.py` | +25 | Register warmup-pool, deliverability, OAuth-refresh, TTL-sweep cron jobs |
| `requirements.txt` | +7 | Add deps |

---

## Wave 1 — Foundation (4 parallel task groups)

### Task 1.1: Dependencies + test infrastructure

**Files:**
- Modify: `requirements.txt`
- Create: `tests/__init__.py`, `tests/conftest.py`

- [ ] **Step 1: Add new dependencies**

Edit `requirements.txt`, append:

```
# Industry Factory
pydantic>=2.5.0
pyyaml>=6.0
python-Wappalyzer>=0.4.0
pytest>=7.4.0
pytest-mock>=3.12.0
pytest-asyncio>=0.23.0
```

- [ ] **Step 2: Install locally**

Run: `cd ~/Desktop/ECAS && pip install -r requirements.txt`
Expected: all packages install, no errors.

- [ ] **Step 3: Create tests directory**

Run:
```bash
mkdir -p /Users/ethanatchley/Desktop/ECAS/tests/fixtures/industries
touch /Users/ethanatchley/Desktop/ECAS/tests/__init__.py
```

- [ ] **Step 4: Create conftest.py**

Create `tests/conftest.py`:

```python
"""Shared pytest fixtures for Industry Factory tests."""
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture(autouse=True)
def _mock_env(monkeypatch):
    """Default env vars so config.py loads cleanly in tests."""
    defaults = {
        "AIRTABLE_API_KEY": "test_at_key",
        "APOLLO_API_KEY": "test_apollo_key",
        "FINDYMAIL_API_KEY": "test_fm_key",
        "SMARTLEAD_API_KEY": "test_sl_key",
        "ANTHROPIC_API_KEY": "test_anthropic_key",
        "PERPLEXITY_API_KEY": "test_pplx_key",
        "FIRECRAWL_API_KEY": "test_fc_key",
        "BROWSERBASE_API_KEY": "test_bb_key",
        "BROWSERBASE_PROJECT_ID": "test_bb_proj",
        "AIRTOP_API_KEY": "test_airtop_key",
        "SLACK_ACCESS_TOKEN": "test_slack_token",
    }
    for k, v in defaults.items():
        if not os.environ.get(k):
            monkeypatch.setenv(k, v)


@pytest.fixture
def fixtures_dir():
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def industries_fixture_dir(fixtures_dir):
    return fixtures_dir / "industries"
```

- [ ] **Step 5: Verify pytest runs (empty collection)**

Run: `cd ~/Desktop/ECAS && pytest tests/ -v`
Expected: `no tests ran in 0.0s` (no test files yet, but collection works).

- [ ] **Step 6: Commit**

```bash
git add requirements.txt tests/__init__.py tests/conftest.py
git commit -m "feat(factory): add test infra and deps for Industry Factory"
```

---

### Task 1.2: Industry YAML schema

**Files:**
- Create: `industries/__init__.py`, `industries/_schema.py`
- Test: `tests/test_industries_schema.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_industries_schema.py`:

```python
"""Tests for industry YAML schema."""
import pytest
from pydantic import ValidationError

from industries._schema import Industry, ScoringMode, Track


def test_valid_industry_parses():
    data = {
        "slug": "data_center",
        "display_name": "Data Center & AI Infrastructure",
        "track": "contract_motion",
        "campaign_id": "3040599",
        "revenue_range_m": [20, 300],
        "naics": ["236220", "237130"],
        "titles": ["VP Operations", "Director BD"],
        "states": ["VA", "TX"],
        "apollo_keywords": ["data center epc"],
        "scoring_mode": "positive",
        "min_heat": 50.0,
    }
    ind = Industry(**data)
    assert ind.slug == "data_center"
    assert ind.scoring_mode == ScoringMode.POSITIVE
    assert ind.track == Track.CONTRACT_MOTION


def test_slug_must_be_lowercase_underscore():
    with pytest.raises(ValidationError):
        Industry(
            slug="Data-Center",  # invalid — caps + dash
            display_name="x", track="contract_motion", campaign_id="1",
            revenue_range_m=[1, 10], naics=["1"], titles=["x"],
            states=["TX"], apollo_keywords=["x"], scoring_mode="positive",
        )


def test_revenue_range_must_have_two_values():
    with pytest.raises(ValidationError):
        Industry(
            slug="x", display_name="x", track="contract_motion", campaign_id="1",
            revenue_range_m=[1],  # invalid
            naics=["1"], titles=["x"], states=["TX"],
            apollo_keywords=["x"], scoring_mode="positive",
        )


def test_negative_scoring_requires_expected_stack():
    with pytest.raises(ValidationError) as exc:
        Industry(
            slug="x", display_name="x", track="ai_automation", campaign_id="1",
            revenue_range_m=[1, 10], naics=["1"], titles=["x"], states=["TX"],
            apollo_keywords=["x"], scoring_mode="negative_tech_stack",
            # expected_stack_if_mature missing
        )
    assert "expected_stack_if_mature" in str(exc.value)


def test_defaults_applied():
    ind = Industry(
        slug="x", display_name="x", track="contract_motion", campaign_id="1",
        revenue_range_m=[1, 10], naics=["1"], titles=["x"], states=["TX"],
        apollo_keywords=["x"], scoring_mode="positive",
    )
    assert ind.signal_ttl_days == 90
    assert ind.budget_cap_per_run == 50
    assert ind.directory_auto_discovery is True
    assert ind.min_heat == 50.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_industries_schema.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'industries._schema'`

- [ ] **Step 3: Create package init**

Create `industries/__init__.py` (empty file):

```bash
touch /Users/ethanatchley/Desktop/ECAS/industries/__init__.py
```

- [ ] **Step 4: Create schema module**

Create `industries/_schema.py`:

```python
"""Pydantic schema for industry YAML configs."""
from __future__ import annotations

import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


SLUG_RE = re.compile(r"^[a-z][a-z0-9_]*$")


class Track(str, Enum):
    CONTRACT_MOTION = "contract_motion"
    AI_AUTOMATION = "ai_automation"


class ScoringMode(str, Enum):
    POSITIVE = "positive"
    NEGATIVE_TECH_STACK = "negative_tech_stack"
    HYBRID = "hybrid"


class ExpectedStack(BaseModel):
    fsm: list[str] = Field(default_factory=list)
    crm: list[str] = Field(default_factory=list)
    sms: list[str] = Field(default_factory=list)
    marketing_automation: list[str] = Field(default_factory=list)
    analytics: list[str] = Field(default_factory=list)


class Industry(BaseModel):
    # Identity
    slug: str
    display_name: str
    track: Track
    campaign_id: str

    # ICP
    revenue_range_m: list[float] = Field(min_length=2, max_length=2)
    naics: list[str]
    titles: list[str]
    states: list[str]

    # Discovery
    apollo_keywords: list[str]
    directory_seeds: list[str] = Field(default_factory=list)
    directory_auto_discovery: bool = True

    # Scoring
    scoring_mode: ScoringMode
    expected_stack_if_mature: ExpectedStack | None = None
    prioritize_when_missing: list[str] = Field(default_factory=list)
    min_heat: float = 50.0

    # Guardrails
    signal_ttl_days: int = 90
    budget_cap_per_run: int = 50
    landing_page_url: str | None = None

    # Deliverability
    sender_pool: str = "default"

    @field_validator("slug")
    @classmethod
    def _slug_format(cls, v: str) -> str:
        if not SLUG_RE.match(v):
            raise ValueError(
                f"slug must match {SLUG_RE.pattern}: got {v!r}"
            )
        return v

    @field_validator("revenue_range_m")
    @classmethod
    def _revenue_order(cls, v: list[float]) -> list[float]:
        if v[0] >= v[1]:
            raise ValueError("revenue_range_m must be [low, high] with low < high")
        return v

    @model_validator(mode="after")
    def _scoring_consistency(self) -> "Industry":
        if self.scoring_mode in (ScoringMode.NEGATIVE_TECH_STACK, ScoringMode.HYBRID):
            if self.expected_stack_if_mature is None:
                raise ValueError(
                    f"scoring_mode={self.scoring_mode.value} requires expected_stack_if_mature"
                )
        return self
```

- [ ] **Step 5: Run tests, verify pass**

Run: `pytest tests/test_industries_schema.py -v`
Expected: all 4 tests pass.

- [ ] **Step 6: Commit**

```bash
git add industries/__init__.py industries/_schema.py tests/test_industries_schema.py
git commit -m "feat(factory): industry YAML schema with scoring-mode consistency rules"
```

---

### Task 1.3: Industry YAML loader

**Files:**
- Create: `industries/loader.py`
- Create: `tests/fixtures/industries/test_industry.yaml`
- Test: `tests/test_industries_loader.py`

- [ ] **Step 1: Create fixture YAML**

Create `tests/fixtures/industries/test_industry.yaml`:

```yaml
slug: test_industry
display_name: "Test Industry"
track: contract_motion
campaign_id: "9999999"
revenue_range_m: [10, 100]
naics: ["237130"]
titles: [Owner, CEO]
states: [TX, VA]
apollo_keywords: [test contractor]
scoring_mode: positive
min_heat: 40.0
```

- [ ] **Step 2: Write failing tests**

Create `tests/test_industries_loader.py`:

```python
"""Tests for industry loader."""
from pathlib import Path

import pytest

from industries._schema import Industry
from industries.loader import (
    load_industry,
    load_all_industries,
    IndustryNotFoundError,
)


def test_load_industry_from_fixture(industries_fixture_dir):
    ind = load_industry("test_industry", directory=industries_fixture_dir)
    assert isinstance(ind, Industry)
    assert ind.slug == "test_industry"
    assert ind.campaign_id == "9999999"


def test_load_missing_raises(industries_fixture_dir):
    with pytest.raises(IndustryNotFoundError):
        load_industry("no_such_industry", directory=industries_fixture_dir)


def test_load_all_industries_returns_dict(industries_fixture_dir):
    mapping = load_all_industries(directory=industries_fixture_dir)
    assert "test_industry" in mapping
    assert isinstance(mapping["test_industry"], Industry)


def test_load_all_ignores_private_and_non_yaml(tmp_path):
    (tmp_path / "_private.yaml").write_text("slug: x")
    (tmp_path / "readme.txt").write_text("ignore me")
    (tmp_path / "valid.yaml").write_text(
        "slug: valid\n"
        "display_name: Valid\n"
        "track: contract_motion\n"
        "campaign_id: '1'\n"
        "revenue_range_m: [1, 10]\n"
        "naics: ['1']\n"
        "titles: [x]\n"
        "states: [TX]\n"
        "apollo_keywords: [x]\n"
        "scoring_mode: positive\n"
    )
    mapping = load_all_industries(directory=tmp_path)
    assert "valid" in mapping
    assert "_private" not in mapping
    assert "readme" not in mapping
```

- [ ] **Step 3: Run, verify fails**

Run: `pytest tests/test_industries_loader.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'industries.loader'`

- [ ] **Step 4: Implement loader**

Create `industries/loader.py`:

```python
"""Load and validate industry YAML configs."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import yaml

from industries._schema import Industry

logger = logging.getLogger(__name__)

DEFAULT_DIRECTORY = Path(__file__).parent


class IndustryNotFoundError(FileNotFoundError):
    pass


def load_industry(
    slug: str,
    directory: Optional[Path] = None,
) -> Industry:
    """Load and validate a single industry YAML by slug."""
    d = directory or DEFAULT_DIRECTORY
    path = d / f"{slug}.yaml"
    if not path.exists():
        raise IndustryNotFoundError(f"No industry YAML at {path}")
    with path.open("r") as f:
        raw = yaml.safe_load(f) or {}
    try:
        return Industry(**raw)
    except Exception as exc:
        logger.error("[Industries] Failed to parse %s: %s", path, exc)
        raise


def load_all_industries(
    directory: Optional[Path] = None,
) -> dict[str, Industry]:
    """Load every .yaml file in directory, returning {slug: Industry}."""
    d = directory or DEFAULT_DIRECTORY
    result: dict[str, Industry] = {}
    for path in sorted(d.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        try:
            with path.open("r") as f:
                raw = yaml.safe_load(f) or {}
            ind = Industry(**raw)
            result[ind.slug] = ind
        except Exception as exc:
            logger.warning("[Industries] Skipping %s: %s", path.name, exc)
            continue
    return result
```

- [ ] **Step 5: Run tests, verify pass**

Run: `pytest tests/test_industries_loader.py -v`
Expected: 4 tests pass.

- [ ] **Step 6: Commit**

```bash
git add industries/loader.py tests/test_industries_loader.py tests/fixtures/industries/test_industry.yaml
git commit -m "feat(factory): industry YAML loader with fixture-based tests"
```

---

### Task 1.4: Directory finder (Perplexity + Claude)

**Files:**
- Create: `discovery/__init__.py`, `discovery/directory_finder.py`
- Test: `tests/test_directory_finder.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_directory_finder.py`:

```python
"""Tests for directory auto-discovery."""
from unittest.mock import patch, MagicMock

import pytest

from discovery.directory_finder import (
    DirectoryCandidate,
    ScraperType,
    discover_directories,
    classify_url,
)


def test_classify_static_url():
    """URLs that look like normal article/directory pages → static (Firecrawl)."""
    assert classify_url("https://www.nrca.net/directory") == ScraperType.STATIC


def test_classify_linkedin_as_gated():
    """LinkedIn / gated directories → Airtop."""
    assert classify_url("https://www.linkedin.com/events/123") == ScraperType.GATED


def test_classify_js_heavy_as_browserbase():
    """Known JS-heavy / SPA URLs → Browserbase."""
    for url in [
        "https://app.swapcard.com/event/xyz",
        "https://eventmobi.com/xyz",
    ]:
        assert classify_url(url) == ScraperType.JS_HEAVY


def test_discover_returns_candidates_with_confidence():
    mock_urls = [
        "https://www.nrca.net/directory",
        "https://www.roofingcontractor.com/top-100",
    ]

    with patch("discovery.directory_finder._perplexity_search") as pplx, \
         patch("discovery.directory_finder._extract_urls_with_claude") as claude:
        pplx.return_value = "Perplexity free-form response mentioning the URLs"
        claude.return_value = mock_urls

        candidates = discover_directories(
            industry_display_name="Commercial Roofing",
            keywords=["commercial roofing contractor"],
            min_confidence=0.5,
        )

    assert len(candidates) == 2
    assert all(isinstance(c, DirectoryCandidate) for c in candidates)
    assert all(c.confidence >= 0.5 for c in candidates)


def test_discover_aborts_on_too_few_candidates():
    """If fewer than min_results candidates pass confidence, raise."""
    with patch("discovery.directory_finder._perplexity_search") as pplx, \
         patch("discovery.directory_finder._extract_urls_with_claude") as claude:
        pplx.return_value = "no results"
        claude.return_value = []

        with pytest.raises(RuntimeError, match="Insufficient directory candidates"):
            discover_directories(
                industry_display_name="Nonexistent Industry",
                keywords=["xyz"],
                min_results=3,
            )
```

- [ ] **Step 2: Run, verify fails**

Run: `pytest tests/test_directory_finder.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'discovery'`

- [ ] **Step 3: Implement package + module**

Create `discovery/__init__.py` (empty):

```bash
mkdir -p /Users/ethanatchley/Desktop/ECAS/discovery
touch /Users/ethanatchley/Desktop/ECAS/discovery/__init__.py
```

Create `discovery/directory_finder.py`:

```python
"""Auto-discover directory/association/conference URLs for a given industry.

Flow:
  1. Perplexity search with targeted query
  2. Claude extracts candidate URLs from response
  3. Classify each URL by scraper type (static/gated/JS-heavy)
  4. Score confidence; filter by min_confidence; require min_results
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)


class ScraperType(str, Enum):
    STATIC = "static"        # Firecrawl
    GATED = "gated"          # Airtop (login/auth)
    JS_HEAVY = "js_heavy"    # Browserbase (SPA)


@dataclass
class DirectoryCandidate:
    url: str
    scraper_type: ScraperType
    confidence: float
    source: str = "perplexity+claude"


# Known patterns for classification
GATED_HOSTS = {
    "linkedin.com", "zoominfo.com", "sales-navigator.com",
}
JS_HEAVY_HOSTS = {
    "swapcard.com", "eventmobi.com", "hopin.com", "cvent.com",
    "bizzabo.com", "pheedloop.com",
}


def classify_url(url: str) -> ScraperType:
    """Classify a URL by inferred scraper strategy."""
    host = (urlparse(url).hostname or "").lower()
    for gated in GATED_HOSTS:
        if gated in host:
            return ScraperType.GATED
    for js in JS_HEAVY_HOSTS:
        if js in host:
            return ScraperType.JS_HEAVY
    return ScraperType.STATIC


def _perplexity_search(query: str) -> str:
    """Call Perplexity API for a research query. Returns free-form text."""
    key = os.environ.get("PERPLEXITY_API_KEY", "")
    if not key:
        raise RuntimeError("PERPLEXITY_API_KEY not set")
    resp = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "sonar-pro",
            "messages": [
                {"role": "system", "content": "You are a GTM research assistant. Return concise URLs and context."},
                {"role": "user", "content": query},
            ],
            "max_tokens": 2000,
            "return_citations": True,
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    citations = data.get("citations", [])
    return content + "\n\nCitations:\n" + "\n".join(citations)


def _extract_urls_with_claude(pplx_response: str, industry: str) -> list[str]:
    """Ask Claude to extract candidate directory URLs from Perplexity output."""
    import anthropic

    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=key)
    prompt = (
        f"Extract directory, association, or exhibitor-list URLs relevant to finding "
        f"{industry} companies from the research below. Return JSON array of URL strings only. "
        f"Exclude generic blog posts, news articles, and social media profiles.\n\n"
        f"Research:\n{pplx_response}"
    )
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    text = msg.content[0].text
    # Strip any markdown fencing
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        return []
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        logger.warning("[DirectoryFinder] Claude returned unparseable JSON: %s", text[:300])
        return []


def _confidence(url: str, industry: str) -> float:
    """Heuristic confidence — prefers industry keywords in host/path."""
    url_lower = url.lower()
    industry_tokens = [t.lower() for t in industry.split() if len(t) > 3]
    hits = sum(1 for t in industry_tokens if t in url_lower)
    base = 0.4
    boost = min(hits * 0.2, 0.5)
    # Penalty for obviously generic sources
    if any(bad in url_lower for bad in ["wikipedia.org", "reddit.com", "youtube.com"]):
        return 0.0
    return round(base + boost, 2)


def discover_directories(
    industry_display_name: str,
    keywords: list[str],
    min_confidence: float = 0.5,
    min_results: int = 3,
) -> list[DirectoryCandidate]:
    """Discover directory URLs for an industry.

    Raises RuntimeError if fewer than min_results candidates pass min_confidence.
    """
    query = (
        f"List the top 15 public directories, industry associations, and trade show "
        f"exhibitor lists where I can find {industry_display_name} companies in the US. "
        f"Focus on: {', '.join(keywords)}. Return URLs and a one-line description each. "
        f"Exclude LinkedIn and generic Google results."
    )

    logger.info("[DirectoryFinder] Perplexity query for %s", industry_display_name)
    pplx_output = _perplexity_search(query)

    urls = _extract_urls_with_claude(pplx_output, industry_display_name)
    logger.info("[DirectoryFinder] Claude extracted %d URLs", len(urls))

    candidates: list[DirectoryCandidate] = []
    for url in urls:
        conf = _confidence(url, industry_display_name)
        if conf < min_confidence:
            continue
        candidates.append(DirectoryCandidate(
            url=url,
            scraper_type=classify_url(url),
            confidence=conf,
        ))

    candidates.sort(key=lambda c: c.confidence, reverse=True)

    if len(candidates) < min_results:
        raise RuntimeError(
            f"Insufficient directory candidates for {industry_display_name!r}: "
            f"got {len(candidates)}, need ≥{min_results} at confidence ≥{min_confidence}. "
            f"Raw URLs: {urls}"
        )

    return candidates
```

- [ ] **Step 4: Run tests, verify pass**

Run: `pytest tests/test_directory_finder.py -v`
Expected: 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add discovery/__init__.py discovery/directory_finder.py tests/test_directory_finder.py
git commit -m "feat(factory): directory auto-discovery via Perplexity + Claude"
```

---

### Task 1.5: Universal scraper (router)

**Files:**
- Create: `discovery/universal_scraper.py`
- Test: `tests/test_universal_scraper.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_universal_scraper.py`:

```python
"""Tests for universal scraper router."""
from unittest.mock import patch

import pytest

from discovery.directory_finder import DirectoryCandidate, ScraperType
from discovery.universal_scraper import scrape_candidates, ScrapedCompany


def test_routes_static_to_firecrawl():
    candidate = DirectoryCandidate(
        url="https://www.nrca.net/directory",
        scraper_type=ScraperType.STATIC,
        confidence=0.8,
    )
    with patch("discovery.universal_scraper._firecrawl_scrape") as fc, \
         patch("discovery.universal_scraper._airtop_scrape") as airtop, \
         patch("discovery.universal_scraper._browserbase_scrape") as bb:
        fc.return_value = [
            ScrapedCompany(name="ABC Roofing", website="abcroofing.com", source_url=candidate.url),
        ]
        results = scrape_candidates([candidate])

    fc.assert_called_once()
    airtop.assert_not_called()
    bb.assert_not_called()
    assert len(results) == 1
    assert results[0].name == "ABC Roofing"


def test_routes_gated_to_airtop():
    candidate = DirectoryCandidate(
        url="https://www.linkedin.com/events/123",
        scraper_type=ScraperType.GATED,
        confidence=0.9,
    )
    with patch("discovery.universal_scraper._firecrawl_scrape") as fc, \
         patch("discovery.universal_scraper._airtop_scrape") as airtop, \
         patch("discovery.universal_scraper._browserbase_scrape") as bb:
        airtop.return_value = []
        scrape_candidates([candidate])

    airtop.assert_called_once()
    fc.assert_not_called()
    bb.assert_not_called()


def test_routes_js_heavy_to_browserbase():
    candidate = DirectoryCandidate(
        url="https://app.swapcard.com/event/abc",
        scraper_type=ScraperType.JS_HEAVY,
        confidence=0.7,
    )
    with patch("discovery.universal_scraper._firecrawl_scrape") as fc, \
         patch("discovery.universal_scraper._airtop_scrape") as airtop, \
         patch("discovery.universal_scraper._browserbase_scrape") as bb:
        bb.return_value = []
        scrape_candidates([candidate])

    bb.assert_called_once()
    fc.assert_not_called()
    airtop.assert_not_called()


def test_dedupes_by_normalized_website():
    c1 = DirectoryCandidate(url="https://a.com", scraper_type=ScraperType.STATIC, confidence=0.8)
    c2 = DirectoryCandidate(url="https://b.com", scraper_type=ScraperType.STATIC, confidence=0.8)
    with patch("discovery.universal_scraper._firecrawl_scrape") as fc:
        fc.side_effect = [
            [ScrapedCompany(name="ABC", website="https://abc.com", source_url="a")],
            [ScrapedCompany(name="ABC Corp", website="abc.com/", source_url="b")],
        ]
        results = scrape_candidates([c1, c2])

    # Same normalized host → deduped
    assert len(results) == 1
```

- [ ] **Step 2: Run, verify fails**

Run: `pytest tests/test_universal_scraper.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement scraper**

Create `discovery/universal_scraper.py`:

```python
"""Universal scraper router: routes URLs to Firecrawl/Airtop/Browserbase."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

import requests

from discovery.directory_finder import DirectoryCandidate, ScraperType

logger = logging.getLogger(__name__)


@dataclass
class ScrapedCompany:
    name: str
    website: str
    source_url: str
    extras: dict = field(default_factory=dict)


def _normalize_host(url_or_host: str) -> str:
    if not url_or_host:
        return ""
    s = url_or_host.strip().lower()
    if not s.startswith("http"):
        s = "https://" + s
    host = (urlparse(s).hostname or "").lower()
    return host.removeprefix("www.")


def _firecrawl_scrape(url: str) -> list[ScrapedCompany]:
    """Scrape a static directory page via Firecrawl API."""
    key = os.environ.get("FIRECRAWL_API_KEY", "")
    if not key:
        raise RuntimeError("FIRECRAWL_API_KEY not set")
    resp = requests.post(
        "https://api.firecrawl.dev/v1/scrape",
        headers={"Authorization": f"Bearer {key}"},
        json={
            "url": url,
            "formats": ["extract"],
            "extract": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "companies": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "website": {"type": "string"},
                                },
                                "required": ["name"],
                            },
                        },
                    },
                },
                "prompt": "Extract all companies/vendors/exhibitors listed on this page.",
            },
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    extracted = (data.get("data", {}) or {}).get("extract", {}) or {}
    companies = extracted.get("companies", []) or []
    return [
        ScrapedCompany(
            name=c["name"],
            website=c.get("website", ""),
            source_url=url,
        )
        for c in companies
        if c.get("name")
    ]


def _airtop_scrape(url: str) -> list[ScrapedCompany]:
    """Scrape a gated directory via Airtop browser session."""
    key = os.environ.get("AIRTOP_API_KEY", "")
    if not key:
        logger.warning("[Scraper] AIRTOP_API_KEY not set — skipping %s", url)
        return []
    # Airtop session → visit URL → extract. This is a thin wrapper;
    # real session management (login, cookies) is handled per-source later.
    resp = requests.post(
        "https://api.airtop.ai/api/v1/sessions/scrape",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "url": url,
            "prompt": "Extract company names and websites from all visible listings.",
        },
        timeout=180,
    )
    if resp.status_code >= 400:
        logger.warning("[Scraper] Airtop %s: %s", url, resp.status_code)
        return []
    data = resp.json()
    return [
        ScrapedCompany(
            name=c["name"],
            website=c.get("website", ""),
            source_url=url,
        )
        for c in data.get("companies", [])
        if c.get("name")
    ]


def _browserbase_scrape(url: str) -> list[ScrapedCompany]:
    """Scrape a JS-heavy SPA via Browserbase session."""
    key = os.environ.get("BROWSERBASE_API_KEY", "")
    project = os.environ.get("BROWSERBASE_PROJECT_ID", "")
    if not (key and project):
        logger.warning("[Scraper] Browserbase creds missing — skipping %s", url)
        return []
    # Browserbase session URL → we use their proxied fetch with JS execution.
    # Playwright-over-Browserbase integration is a future optimization.
    resp = requests.post(
        "https://api.browserbase.com/v1/scrape",
        headers={"X-BB-API-Key": key},
        json={"projectId": project, "url": url},
        timeout=180,
    )
    if resp.status_code >= 400:
        logger.warning("[Scraper] Browserbase %s: %s", url, resp.status_code)
        return []
    data = resp.json()
    return [
        ScrapedCompany(
            name=c["name"],
            website=c.get("website", ""),
            source_url=url,
        )
        for c in data.get("companies", [])
        if c.get("name")
    ]


_ROUTER = {
    ScraperType.STATIC: _firecrawl_scrape,
    ScraperType.GATED: _airtop_scrape,
    ScraperType.JS_HEAVY: _browserbase_scrape,
}


def scrape_candidates(candidates: list[DirectoryCandidate]) -> list[ScrapedCompany]:
    """Scrape every candidate, dedupe by normalized host, return unified list."""
    seen: set[str] = set()
    results: list[ScrapedCompany] = []
    for c in candidates:
        try:
            scraper = _ROUTER[c.scraper_type]
        except KeyError:
            logger.error("[Scraper] No router for %s", c.scraper_type)
            continue
        try:
            companies = scraper(c.url)
        except Exception as exc:
            logger.error("[Scraper] %s failed on %s: %s", c.scraper_type, c.url, exc)
            continue
        for company in companies:
            host = _normalize_host(company.website) or company.name.lower().strip()
            if host in seen:
                continue
            seen.add(host)
            results.append(company)
    return results
```

- [ ] **Step 4: Run tests, verify pass**

Run: `pytest tests/test_universal_scraper.py -v`
Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add discovery/universal_scraper.py tests/test_universal_scraper.py
git commit -m "feat(factory): universal scraper router w/ Firecrawl/Airtop/Browserbase"
```

---

### Task 1.6: Tech-stack enrichment

**Files:**
- Create: `enrichment/tech_stack.py`
- Test: `tests/test_tech_stack.py`
- Modify: `database/` (add cache table)

- [ ] **Step 1: Write failing tests**

Create `tests/test_tech_stack.py`:

```python
"""Tests for tech-stack enrichment."""
import sqlite3
from unittest.mock import patch

import pytest

from enrichment.tech_stack import (
    TechStackProfile,
    enrich_company,
    enrich_batch,
    _init_cache,
    _cache_get,
    _cache_put,
)


@pytest.fixture
def temp_cache_db(tmp_path):
    db = tmp_path / "tech_stack_cache.db"
    _init_cache(db)
    return db


def test_profile_derives_flags():
    p = TechStackProfile(
        domain="abcroofing.com",
        detected=["ServiceTitan", "HubSpot"],
    )
    # Expected-stack lookup map (normalized) is applied later via apply_expected()
    assert p.domain == "abcroofing.com"
    assert "ServiceTitan" in p.detected


def test_apply_expected_sets_flags():
    p = TechStackProfile(domain="x.com", detected=["ServiceTitan"])
    p.apply_expected({
        "fsm": ["ServiceTitan", "Jobber"],
        "crm": ["HubSpot"],
        "sms": ["Twilio"],
    })
    assert p.has_category["fsm"] is True
    assert p.has_category["crm"] is False
    assert p.has_category["sms"] is False
    assert set(p.missing_categories) == {"crm", "sms"}


def test_cache_roundtrip(temp_cache_db):
    profile = TechStackProfile(domain="test.com", detected=["HubSpot"])
    _cache_put(temp_cache_db, profile)
    cached = _cache_get(temp_cache_db, "test.com", ttl_days=90)
    assert cached is not None
    assert cached.domain == "test.com"
    assert "HubSpot" in cached.detected


def test_cache_expires(temp_cache_db):
    profile = TechStackProfile(domain="expire.com", detected=["x"])
    _cache_put(temp_cache_db, profile)
    # Force a fake stale timestamp
    with sqlite3.connect(temp_cache_db) as conn:
        conn.execute(
            "UPDATE tech_stack_cache SET cached_at = datetime('now', '-100 days') WHERE domain = ?",
            ("expire.com",),
        )
    assert _cache_get(temp_cache_db, "expire.com", ttl_days=90) is None


def test_enrich_company_uses_cache(temp_cache_db):
    cached = TechStackProfile(domain="cached.com", detected=["HubSpot"])
    _cache_put(temp_cache_db, cached)
    with patch("enrichment.tech_stack._wappalyzer_scan") as scan:
        profile = enrich_company("https://cached.com", db=temp_cache_db)
    scan.assert_not_called()
    assert "HubSpot" in profile.detected


def test_enrich_company_scans_on_miss(temp_cache_db):
    with patch("enrichment.tech_stack._wappalyzer_scan") as scan:
        scan.return_value = ["ServiceTitan"]
        profile = enrich_company("https://fresh.com", db=temp_cache_db)
    assert profile.detected == ["ServiceTitan"]
    # Second call uses cache
    with patch("enrichment.tech_stack._wappalyzer_scan") as scan2:
        enrich_company("https://fresh.com", db=temp_cache_db)
        scan2.assert_not_called()
```

- [ ] **Step 2: Run, verify fails**

Run: `pytest tests/test_tech_stack.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'enrichment.tech_stack'`

- [ ] **Step 3: Implement module**

Create `enrichment/tech_stack.py`:

```python
"""Tech-stack enrichment via Wappalyzer (primary) + BuiltWith (optional) + SQLite cache.

Given a company website, return what software they run. Used to detect
low-maturity blue-collar businesses (targets for AI Automation track).
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

DEFAULT_CACHE_DB = Path(__file__).parent.parent / "database" / "tech_stack_cache.db"


@dataclass
class TechStackProfile:
    domain: str
    detected: list[str] = field(default_factory=list)
    has_category: dict[str, bool] = field(default_factory=dict)
    missing_categories: list[str] = field(default_factory=list)
    stack_maturity_score: float = 0.0

    def apply_expected(self, expected: dict[str, list[str]]) -> None:
        """Populate has_category/missing_categories from detected vs expected."""
        detected_lower = {d.lower() for d in self.detected}
        self.has_category = {}
        self.missing_categories = []
        for category, tools in expected.items():
            hit = any(t.lower() in detected_lower for t in tools)
            self.has_category[category] = hit
            if not hit:
                self.missing_categories.append(category)
        total = len(expected) or 1
        self.stack_maturity_score = round(
            sum(1 for v in self.has_category.values() if v) / total * 10,
            2,
        )


# ── Cache ────────────────────────────────────────────────────────────────────

def _init_cache(db: Path) -> None:
    db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tech_stack_cache (
                domain TEXT PRIMARY KEY,
                detected_json TEXT NOT NULL,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def _cache_get(db: Path, domain: str, ttl_days: int = 90) -> Optional[TechStackProfile]:
    if not db.exists():
        _init_cache(db)
        return None
    with sqlite3.connect(db) as conn:
        row = conn.execute(
            """
            SELECT detected_json FROM tech_stack_cache
            WHERE domain = ?
              AND cached_at >= datetime('now', ?)
            """,
            (domain, f"-{ttl_days} days"),
        ).fetchone()
    if not row:
        return None
    return TechStackProfile(domain=domain, detected=json.loads(row[0]))


def _cache_put(db: Path, profile: TechStackProfile) -> None:
    _init_cache(db)
    with sqlite3.connect(db) as conn:
        conn.execute(
            """
            INSERT INTO tech_stack_cache (domain, detected_json, cached_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(domain) DO UPDATE SET
                detected_json = excluded.detected_json,
                cached_at = excluded.cached_at
            """,
            (profile.domain, json.dumps(profile.detected)),
        )


# ── Scanners ─────────────────────────────────────────────────────────────────

def _normalize_domain(url_or_domain: str) -> str:
    s = url_or_domain.strip().lower()
    if not s.startswith("http"):
        s = "https://" + s
    host = (urlparse(s).hostname or "").lower()
    return host.removeprefix("www.")


def _wappalyzer_scan(url: str) -> list[str]:
    """Run Wappalyzer on a live URL. Returns list of detected technology names."""
    try:
        from Wappalyzer import Wappalyzer, WebPage
    except ImportError:
        logger.error("[TechStack] python-Wappalyzer not installed")
        return []
    try:
        wa = Wappalyzer.latest()
        page = WebPage.new_from_url(url, verify=False, timeout=30)
        techs = wa.analyze(page)
        return sorted(list(techs))
    except Exception as exc:
        logger.warning("[TechStack] Wappalyzer failed on %s: %s", url, exc)
        return []


def _builtwith_scan(domain: str) -> list[str]:
    """Optional BuiltWith enrichment (deeper data than Wappalyzer)."""
    key = os.environ.get("BUILTWITH_API_KEY", "")
    if not key:
        return []
    import requests
    try:
        resp = requests.get(
            "https://api.builtwith.com/v20/api.json",
            params={"KEY": key, "LOOKUP": domain},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        techs = set()
        for result in (data.get("Results") or []):
            for path in (result.get("Result", {}).get("Paths") or []):
                for t in (path.get("Technologies") or []):
                    name = t.get("Name")
                    if name:
                        techs.add(name)
        return sorted(list(techs))
    except Exception as exc:
        logger.warning("[TechStack] BuiltWith failed on %s: %s", domain, exc)
        return []


# ── Public API ───────────────────────────────────────────────────────────────

def enrich_company(
    website: str,
    db: Optional[Path] = None,
    ttl_days: int = 90,
) -> TechStackProfile:
    """Enrich a single company's tech stack, using cache when possible."""
    db = db or DEFAULT_CACHE_DB
    domain = _normalize_domain(website)
    if not domain:
        return TechStackProfile(domain=website, detected=[])

    cached = _cache_get(db, domain, ttl_days=ttl_days)
    if cached is not None:
        return cached

    wa_techs = _wappalyzer_scan(f"https://{domain}")
    bw_techs = _builtwith_scan(domain)
    all_techs = sorted(set(wa_techs) | set(bw_techs))

    profile = TechStackProfile(domain=domain, detected=all_techs)
    _cache_put(db, profile)
    return profile


def enrich_batch(
    websites: list[str],
    db: Optional[Path] = None,
    ttl_days: int = 90,
) -> list[TechStackProfile]:
    """Enrich many companies sequentially (Wappalyzer is local — no rate limit)."""
    return [enrich_company(w, db=db, ttl_days=ttl_days) for w in websites]
```

- [ ] **Step 4: Run tests, verify pass**

Run: `pytest tests/test_tech_stack.py -v`
Expected: 6 tests pass.

- [ ] **Step 5: Commit**

```bash
git add enrichment/tech_stack.py tests/test_tech_stack.py
git commit -m "feat(factory): tech-stack enrichment via Wappalyzer + BuiltWith + SQLite cache"
```

---

### Task 1.7: Scoring mode extension

**Files:**
- Modify: `lead_priority_scoring.py`
- Test: `tests/test_scoring_modes.py`

- [ ] **Step 1: Read current `lead_priority_scoring.py` to understand surface area**

Run: `head -80 /Users/ethanatchley/Desktop/ECAS/lead_priority_scoring.py`

- [ ] **Step 2: Write failing tests**

Create `tests/test_scoring_modes.py`:

```python
"""Tests for Industry Factory scoring modes."""
from enrichment.tech_stack import TechStackProfile
from lead_priority_scoring import score_company_by_mode


def test_positive_mode_uses_heat_only():
    score = score_company_by_mode(
        mode="positive",
        heat_score=75.0,
        tech_stack=None,
        prioritize_when_missing=[],
    )
    assert score == 75.0


def test_negative_tech_stack_boosts_when_missing_fsm():
    p = TechStackProfile(domain="x.com", detected=["HubSpot"])
    p.apply_expected({
        "fsm": ["ServiceTitan", "Jobber"],
        "crm": ["HubSpot"],
        "sms": ["Twilio"],
    })
    score = score_company_by_mode(
        mode="negative_tech_stack",
        heat_score=30.0,
        tech_stack=p,
        prioritize_when_missing=["fsm", "sms"],
    )
    # Base 30 + boost for missing fsm + missing sms (20 each, cap at 100)
    assert 60 <= score <= 100


def test_negative_tech_stack_deprioritizes_mature():
    p = TechStackProfile(domain="mature.com", detected=["ServiceTitan", "HubSpot", "Twilio"])
    p.apply_expected({
        "fsm": ["ServiceTitan"],
        "crm": ["HubSpot"],
        "sms": ["Twilio"],
    })
    score = score_company_by_mode(
        mode="negative_tech_stack",
        heat_score=30.0,
        tech_stack=p,
        prioritize_when_missing=["fsm"],
    )
    # Has FSM → no boost, low base stays low
    assert score <= 30.0


def test_hybrid_averages_positive_and_negative():
    p = TechStackProfile(domain="x.com", detected=[])
    p.apply_expected({"fsm": ["ServiceTitan"], "crm": ["HubSpot"]})
    score = score_company_by_mode(
        mode="hybrid",
        heat_score=60.0,
        tech_stack=p,
        prioritize_when_missing=["fsm", "crm"],
    )
    # Hybrid = (positive + negative) / 2. negative mode would return ~100, positive 60 → ~80
    assert 70 <= score <= 90


def test_unknown_mode_raises():
    import pytest
    with pytest.raises(ValueError, match="Unknown scoring_mode"):
        score_company_by_mode(
            mode="nonsense",
            heat_score=50.0,
            tech_stack=None,
            prioritize_when_missing=[],
        )
```

- [ ] **Step 3: Run, verify fails**

Run: `pytest tests/test_scoring_modes.py -v`
Expected: FAIL — `ImportError: cannot import name 'score_company_by_mode'`

- [ ] **Step 4: Extend `lead_priority_scoring.py`**

Append to `lead_priority_scoring.py`:

```python
# ─── Industry Factory: Scoring Modes ─────────────────────────────────────────
# Added 2026-04-16. Extends existing scoring with mode-based logic.

from typing import Optional

def score_company_by_mode(
    mode: str,
    heat_score: float,
    tech_stack=None,
    prioritize_when_missing: Optional[list[str]] = None,
) -> float:
    """Score a company based on industry's scoring_mode.

    Modes:
      - positive: heat_score only (existing EPC logic)
      - negative_tech_stack: boost for missing software in prioritized categories
      - hybrid: average of positive and negative
    """
    prioritize_when_missing = prioritize_when_missing or []
    mode = (mode or "positive").lower()

    if mode == "positive":
        return float(heat_score)

    if mode in ("negative_tech_stack", "hybrid"):
        negative = _negative_tech_stack_score(
            heat_score=heat_score,
            tech_stack=tech_stack,
            prioritize_when_missing=prioritize_when_missing,
        )
        if mode == "negative_tech_stack":
            return negative
        return round((float(heat_score) + negative) / 2, 2)

    raise ValueError(f"Unknown scoring_mode: {mode!r}")


def _negative_tech_stack_score(
    heat_score: float,
    tech_stack,
    prioritize_when_missing: list[str],
) -> float:
    """Higher score when company is missing expected software.

    Assumes tech_stack has `has_category: dict[str, bool]` populated via
    TechStackProfile.apply_expected(). Each prioritized missing category
    adds 20 points. Cap at 100.
    """
    if tech_stack is None or not getattr(tech_stack, "has_category", None):
        return float(heat_score)
    boost = 0
    for cat in prioritize_when_missing:
        has = tech_stack.has_category.get(cat, True)
        if not has:
            boost += 20
    return float(min(heat_score + boost, 100.0))
```

- [ ] **Step 5: Run tests, verify pass**

Run: `pytest tests/test_scoring_modes.py -v`
Expected: 5 tests pass.

- [ ] **Step 6: Commit**

```bash
git add lead_priority_scoring.py tests/test_scoring_modes.py
git commit -m "feat(factory): scoring modes (positive/negative_tech_stack/hybrid)"
```

---

## Wave 2 — Orchestration + Guardrails (4 parallel task groups)

### Task 2.1: Industry runner (orchestrator)

**Files:**
- Create: `signals/industry_runner.py`
- Test: `tests/test_industry_runner.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_industry_runner.py`:

```python
"""Tests for industry orchestrator."""
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from signals.industry_runner import run_industry


def _mk_fixture_yaml(tmp_path: Path) -> Path:
    p = tmp_path / "fixture.yaml"
    p.write_text(
        "slug: fixture\n"
        "display_name: Fixture\n"
        "track: contract_motion\n"
        "campaign_id: '1234'\n"
        "revenue_range_m: [10, 100]\n"
        "naics: ['237130']\n"
        "titles: [CEO]\n"
        "states: [TX]\n"
        "apollo_keywords: [test]\n"
        "scoring_mode: positive\n"
        "directory_auto_discovery: false\n"
        "directory_seeds: ['https://example.com']\n"
        "budget_cap_per_run: 5\n"
    )
    return p


def test_dry_run_does_not_call_pipeline(tmp_path):
    _mk_fixture_yaml(tmp_path)

    with patch("signals.industry_runner._preflight") as pf, \
         patch("signals.industry_runner._discover_and_scrape") as scrape, \
         patch("signals.industry_runner._populate_projects") as pop, \
         patch("signals.industry_runner.run_pipeline") as pipe:
        pf.return_value = {"status": "healthy", "failures": {}}
        scrape.return_value = [MagicMock(name="ABC", website="abc.com", source_url="x")]

        result = run_industry("fixture", industries_dir=tmp_path, dry_run=True)

    pipe.assert_not_called()
    pop.assert_not_called()
    assert result["status"] == "dry_run_ok"


def test_preflight_blocked_aborts(tmp_path):
    _mk_fixture_yaml(tmp_path)

    with patch("signals.industry_runner._preflight") as pf:
        pf.return_value = {"status": "blocked", "failures": {"apollo": {"detail": "dead"}}}
        result = run_industry("fixture", industries_dir=tmp_path, dry_run=False)

    assert result["status"] == "blocked"
    assert "apollo" in result["reason"]


def test_first_live_run_without_dryrun_raises(tmp_path):
    _mk_fixture_yaml(tmp_path)

    with patch("signals.industry_runner._has_dryrun_on_record") as hdr, \
         patch("signals.industry_runner._preflight") as pf:
        hdr.return_value = False
        pf.return_value = {"status": "healthy", "failures": {}}
        with pytest.raises(RuntimeError, match="Dry-run required"):
            run_industry("fixture", industries_dir=tmp_path, dry_run=False)


def test_budget_cap_truncates_companies(tmp_path):
    _mk_fixture_yaml(tmp_path)

    with patch("signals.industry_runner._preflight") as pf, \
         patch("signals.industry_runner._has_dryrun_on_record") as hdr, \
         patch("signals.industry_runner._discover_and_scrape") as scrape, \
         patch("signals.industry_runner._populate_projects") as pop, \
         patch("signals.industry_runner.run_pipeline") as pipe:
        pf.return_value = {"status": "healthy", "failures": {}}
        hdr.return_value = True
        # Return 10 companies, but budget_cap = 5
        scrape.return_value = [
            MagicMock(name=f"C{i}", website=f"c{i}.com", source_url="x")
            for i in range(10)
        ]
        pop.return_value = {"created": 5, "existing": 0}
        pipe.return_value = {"status": "complete", "contacts_enrolled": 0}

        result = run_industry("fixture", industries_dir=tmp_path, dry_run=False)

    populated = pop.call_args[0][0]
    assert len(populated) == 5
```

- [ ] **Step 2: Run, verify fails**

Run: `pytest tests/test_industry_runner.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement orchestrator**

Create `signals/industry_runner.py`:

```python
"""Industry Factory orchestrator.

Single entrypoint that takes an industry slug, loads its YAML config, runs
discovery → scraping → tech-stack enrichment → project population → existing
Apollo/FindyMail/Smartlead pipeline → post-run watchdogs.

Invocation:
    python -m signals.industry_runner <slug> [--dry-run|--live]

    # or via Railway admin API:
    POST /admin/run/industry/<slug>
"""
from __future__ import annotations

import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_DRYRUN_DB = Path(__file__).parent.parent / "database" / "industry_dryrun_log.db"


def _preflight() -> dict:
    """Thin wrapper — Task 2.2 extends this with new probes."""
    from enrichment.health import pre_flight_check
    return pre_flight_check()


def _has_dryrun_on_record(slug: str, db: Path = _DRYRUN_DB) -> bool:
    """Returns True if slug has a successful dry-run logged previously."""
    if not db.exists():
        return False
    with sqlite3.connect(db) as conn:
        row = conn.execute(
            "SELECT 1 FROM dryrun_log WHERE slug = ? AND status = 'ok' LIMIT 1",
            (slug,),
        ).fetchone()
    return row is not None


def _log_dryrun(slug: str, status: str, db: Path = _DRYRUN_DB) -> None:
    db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dryrun_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL,
                status TEXT NOT NULL,
                ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            "INSERT INTO dryrun_log (slug, status) VALUES (?, ?)",
            (slug, status),
        )


def _discover_and_scrape(industry):
    """Run directory discovery + scraping for an industry."""
    from discovery.directory_finder import (
        DirectoryCandidate,
        ScraperType,
        classify_url,
        discover_directories,
    )
    from discovery.universal_scraper import scrape_candidates

    # Seed-only path (when auto-discovery disabled)
    seeds: list[DirectoryCandidate] = [
        DirectoryCandidate(url=u, scraper_type=classify_url(u), confidence=1.0, source="seed")
        for u in industry.directory_seeds
    ]

    auto: list[DirectoryCandidate] = []
    if industry.directory_auto_discovery:
        auto = discover_directories(
            industry_display_name=industry.display_name,
            keywords=industry.apollo_keywords,
        )

    candidates = seeds + auto
    if not candidates:
        raise RuntimeError(f"No directory candidates for {industry.slug}")

    return scrape_candidates(candidates)


def _populate_projects(scraped_companies, industry):
    """Upsert scraped companies into Airtable projects table with correct sector."""
    from storage.airtable import get_client

    at = get_client()
    created = 0
    existing = 0
    for company in scraped_companies:
        name = company.name.strip()
        if not name:
            continue
        # Dedup by owner_company
        hits = at._get(
            "projects",
            {
                "filterByFormula": f"{{owner_company}}='{name.replace(chr(39), chr(39) + chr(39))}'",
                "maxRecords": 1,
            },
        )
        if hits:
            existing += 1
            continue
        at.upsert_project({
            "owner_company": name,
            "stage": "Identified",
            "confidence_score": industry.min_heat,
            "positioning_notes": '{"sector": "' + industry.display_name + '"}',
            "priority": "Medium",
        })
        created += 1
    return {"created": created, "existing": existing}


def run_industry(
    slug: str,
    industries_dir: Optional[Path] = None,
    dry_run: bool = True,
) -> dict:
    """Run the full Industry Factory pipeline for a given industry."""
    from industries.loader import load_industry

    industry = load_industry(slug, directory=industries_dir)
    logger.info("[Factory] Running %s (dry_run=%s)", slug, dry_run)

    # 1. Pre-flight
    pf = _preflight()
    if pf["status"] == "blocked":
        return {
            "status": "blocked",
            "reason": f"Pre-flight failed: {pf['failures']}",
            "industry": slug,
        }

    # 2. First-live-run gate
    if not dry_run and not _has_dryrun_on_record(slug):
        raise RuntimeError(
            f"Dry-run required before live run for {slug!r}. "
            f"Execute with dry_run=True first."
        )

    # 3. Discovery + scrape
    scraped = _discover_and_scrape(industry)
    logger.info("[Factory] %s: %d companies scraped", slug, len(scraped))

    # Apply budget cap
    if len(scraped) > industry.budget_cap_per_run:
        scraped = scraped[: industry.budget_cap_per_run]

    if dry_run:
        _log_dryrun(slug, "ok")
        return {
            "status": "dry_run_ok",
            "industry": slug,
            "scraped_count": len(scraped),
            "preview": [c.name for c in scraped[:10]],
        }

    # 4. Populate Airtable projects
    pop_result = _populate_projects(scraped, industry)

    # 5. Hand off to existing pipeline
    from enrichment.pipeline import run_pipeline
    pipeline_result = run_pipeline(
        min_heat=industry.min_heat,
        company_filter=None,
        dry_run=False,
    )

    return {
        "status": "complete",
        "industry": slug,
        "scraped_count": len(scraped),
        "projects_created": pop_result["created"],
        "projects_existing": pop_result["existing"],
        "pipeline": pipeline_result,
        "ran_at": datetime.utcnow().isoformat(),
    }


# CLI entrypoint ──────────────────────────────────────────────────────────────

def _main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("slug")
    parser.add_argument("--live", action="store_true", help="Live run (default: dry-run)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    result = run_industry(args.slug, dry_run=not args.live)
    import json
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    _main()
```

- [ ] **Step 4: Run tests, verify pass**

Run: `pytest tests/test_industry_runner.py -v`
Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add signals/industry_runner.py tests/test_industry_runner.py
git commit -m "feat(factory): industry orchestrator w/ dry-run gate + budget cap"
```

---

### Task 2.2: Extended pre-flight probes

**Files:**
- Modify: `enrichment/health.py`
- Test: `tests/test_extended_preflight.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_extended_preflight.py`:

```python
"""Tests for extended pre-flight probes."""
from unittest.mock import patch, MagicMock

from enrichment.health import (
    check_perplexity,
    check_firecrawl,
    check_browserbase,
    check_airtop,
    check_wappalyzer,
    check_landing_page,
    check_campaign_state,
)


def test_check_perplexity_ok():
    with patch("enrichment.health.requests.post") as post:
        post.return_value = MagicMock(status_code=200, json=lambda: {"id": "ok"})
        r = check_perplexity()
    assert r["healthy"] is True


def test_check_perplexity_auth_fail():
    with patch("enrichment.health.requests.post") as post:
        post.return_value = MagicMock(status_code=401)
        r = check_perplexity()
    assert r["healthy"] is False
    assert "401" in r["detail"]


def test_check_firecrawl_ok():
    with patch("enrichment.health.requests.get") as get:
        get.return_value = MagicMock(status_code=200)
        r = check_firecrawl()
    assert r["healthy"] is True


def test_check_landing_page_200():
    with patch("enrichment.health.requests.head") as head:
        head.return_value = MagicMock(status_code=200)
        r = check_landing_page("https://entagency.co/ai-automation/roofing")
    assert r["healthy"] is True


def test_check_landing_page_404_fails():
    with patch("enrichment.health.requests.head") as head:
        head.return_value = MagicMock(status_code=404)
        r = check_landing_page("https://entagency.co/missing")
    assert r["healthy"] is False


def test_check_campaign_state_active():
    with patch("enrichment.health.requests.get") as get:
        get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"status": "ACTIVE", "sending_accounts": [{"id": 1}]},
        )
        r = check_campaign_state("3040599")
    assert r["healthy"] is True


def test_check_campaign_state_paused_fails():
    with patch("enrichment.health.requests.get") as get:
        get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"status": "PAUSED", "sending_accounts": [{"id": 1}]},
        )
        r = check_campaign_state("3040599")
    assert r["healthy"] is False
    assert "PAUSED" in r["detail"]


def test_check_wappalyzer_importable():
    r = check_wappalyzer()
    # Pytest env has it installed via requirements
    assert r["healthy"] is True
```

- [ ] **Step 2: Run, verify fails**

Run: `pytest tests/test_extended_preflight.py -v`
Expected: FAIL — missing functions

- [ ] **Step 3: Extend `enrichment/health.py`**

Append to `enrichment/health.py`:

```python
# ─── Industry Factory: Extended probes ───────────────────────────────────────

def check_perplexity() -> dict:
    """Perplexity API probe."""
    key = os.environ.get("PERPLEXITY_API_KEY", "")
    if not key:
        return {"healthy": False, "detail": "PERPLEXITY_API_KEY not set"}
    try:
        resp = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "sonar-pro",
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 10,
            },
            timeout=15,
        )
        if resp.status_code in (401, 403):
            return {"healthy": False, "detail": f"Perplexity auth failed ({resp.status_code})"}
        resp.raise_for_status()
        return {"healthy": True, "detail": "API responding"}
    except Exception as e:
        return {"healthy": False, "detail": str(e)}


def check_firecrawl() -> dict:
    """Firecrawl API probe."""
    key = os.environ.get("FIRECRAWL_API_KEY", "")
    if not key:
        return {"healthy": False, "detail": "FIRECRAWL_API_KEY not set"}
    try:
        resp = requests.get(
            "https://api.firecrawl.dev/v1/team/credit-usage",
            headers={"Authorization": f"Bearer {key}"},
            timeout=15,
        )
        if resp.status_code in (401, 403):
            return {"healthy": False, "detail": f"Firecrawl auth failed ({resp.status_code})"}
        return {"healthy": True, "detail": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"healthy": False, "detail": str(e)}


def check_browserbase() -> dict:
    """Browserbase creds presence check (no cheap probe)."""
    key = os.environ.get("BROWSERBASE_API_KEY", "")
    proj = os.environ.get("BROWSERBASE_PROJECT_ID", "")
    if not (key and proj):
        return {"healthy": False, "detail": "BROWSERBASE_API_KEY or BROWSERBASE_PROJECT_ID missing"}
    return {"healthy": True, "detail": "Creds present"}


def check_airtop() -> dict:
    """Airtop creds presence check."""
    key = os.environ.get("AIRTOP_API_KEY", "")
    if not key:
        return {"healthy": False, "detail": "AIRTOP_API_KEY not set"}
    return {"healthy": True, "detail": "Creds present"}


def check_wappalyzer() -> dict:
    """Wappalyzer library importable."""
    try:
        from Wappalyzer import Wappalyzer  # noqa: F401
        return {"healthy": True, "detail": "python-Wappalyzer importable"}
    except ImportError as e:
        return {"healthy": False, "detail": f"python-Wappalyzer not importable: {e}"}


def check_landing_page(url: str) -> dict:
    """Verify a landing page URL returns 200."""
    if not url:
        return {"healthy": False, "detail": "No landing_page_url configured"}
    try:
        resp = requests.head(url, timeout=15, allow_redirects=True)
        if resp.status_code == 200:
            return {"healthy": True, "detail": f"200 OK"}
        return {"healthy": False, "detail": f"HTTP {resp.status_code} on {url}"}
    except Exception as e:
        return {"healthy": False, "detail": str(e)}


def check_campaign_state(campaign_id: str) -> dict:
    """Verify Smartlead campaign exists, is ACTIVE, has ≥1 sending account."""
    key = os.environ.get("SMARTLEAD_API_KEY", "")
    if not key:
        return {"healthy": False, "detail": "SMARTLEAD_API_KEY not set"}
    try:
        resp = requests.get(
            f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}",
            params={"api_key": key},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if str(data.get("status", "")).upper() == "PAUSED":
            return {"healthy": False, "detail": f"Campaign {campaign_id} is PAUSED"}
        if not data.get("sending_accounts"):
            return {"healthy": False, "detail": f"Campaign {campaign_id} has no sending accounts"}
        return {"healthy": True, "detail": f"Campaign {campaign_id} active"}
    except Exception as e:
        return {"healthy": False, "detail": str(e)}
```

- [ ] **Step 4: Run tests, verify pass**

Run: `pytest tests/test_extended_preflight.py -v`
Expected: 8 tests pass.

- [ ] **Step 5: Commit**

```bash
git add enrichment/health.py tests/test_extended_preflight.py
git commit -m "feat(factory): extend pre-flight w/ Perplexity, Firecrawl, landing-page, campaign-state probes"
```

---

### Task 2.3: Compliance + signal TTL + campaign guard

**Files:**
- Create: `enrichment/compliance.py`, `enrichment/signal_ttl.py`, `ops/__init__.py`, `ops/campaign_guard.py`
- Test: `tests/test_compliance.py`, `tests/test_campaign_guard.py`

- [ ] **Step 1: Write compliance test**

Create `tests/test_compliance.py`:

```python
"""Tests for EU/CA compliance filter."""
from enrichment.compliance import filter_contacts_for_compliance


def test_drops_eu_contacts():
    contacts = [
        {"email": "a@us.com", "country": "US"},
        {"email": "b@de.com", "country": "Germany"},
        {"email": "c@fr.com", "country": "France"},
        {"email": "d@ca.com", "country": "Canada"},
        {"email": "e@nl.com", "country": "Netherlands"},
    ]
    filtered, dropped = filter_contacts_for_compliance(contacts)
    assert len(filtered) == 1
    assert filtered[0]["email"] == "a@us.com"
    assert len(dropped) == 4


def test_explicit_optin_allows_eu():
    contacts = [
        {"email": "a@de.com", "country": "Germany", "optin_verified": True},
    ]
    filtered, dropped = filter_contacts_for_compliance(contacts)
    assert len(filtered) == 1
    assert len(dropped) == 0


def test_unknown_country_is_permissive():
    contacts = [{"email": "a@example.com", "country": None}]
    filtered, dropped = filter_contacts_for_compliance(contacts)
    assert len(filtered) == 1
```

- [ ] **Step 2: Implement compliance filter**

Create `enrichment/compliance.py`:

```python
"""Drop EU/CA contacts before Smartlead enrollment unless explicit opt-in."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# ISO-like country names that require opt-in (GDPR + CASL)
RESTRICTED_COUNTRIES = {
    "germany", "france", "netherlands", "belgium", "italy", "spain",
    "portugal", "austria", "sweden", "denmark", "finland", "norway",
    "ireland", "poland", "czech republic", "greece", "hungary",
    "united kingdom", "uk", "gb",
    "canada", "ca",
}


def filter_contacts_for_compliance(
    contacts: list[dict],
) -> tuple[list[dict], list[dict]]:
    """Split contacts into (ok_to_enroll, dropped_for_compliance)."""
    ok: list[dict] = []
    dropped: list[dict] = []
    for c in contacts:
        country = (c.get("country") or "").strip().lower()
        if country in RESTRICTED_COUNTRIES and not c.get("optin_verified"):
            dropped.append({**c, "compliance_reason": f"Restricted country: {country}"})
            continue
        ok.append(c)
    if dropped:
        logger.info("[Compliance] Dropped %d/%d contacts for region rules",
                    len(dropped), len(contacts))
    return ok, dropped
```

- [ ] **Step 3: Run compliance tests**

Run: `pytest tests/test_compliance.py -v`
Expected: 3 tests pass.

- [ ] **Step 4: Write signal TTL test**

Create `tests/test_signal_ttl.py`:

```python
"""Tests for signal TTL sweeper."""
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from enrichment.signal_ttl import sweep_stale_projects


def test_sweeps_projects_older_than_ttl():
    fake_now = datetime(2026, 4, 16)
    cutoff = (fake_now - timedelta(days=120)).isoformat()

    mock_at = MagicMock()
    mock_at._get.return_value = [
        {"id": "rec1", "fields": {"owner_company": "Old", "last_signal_at": "2025-10-01"}},
        {"id": "rec2", "fields": {"owner_company": "Fresh", "last_signal_at": "2026-04-01"}},
    ]

    with patch("enrichment.signal_ttl.get_client", return_value=mock_at), \
         patch("enrichment.signal_ttl.datetime") as dt:
        dt.utcnow.return_value = fake_now
        dt.fromisoformat.side_effect = datetime.fromisoformat
        result = sweep_stale_projects(ttl_days=120)

    assert result["swept"] == 1
    mock_at.update_record.assert_called_once()
```

- [ ] **Step 5: Implement signal TTL**

Create `enrichment/signal_ttl.py`:

```python
"""Drop stale projects/leads that are past their signal TTL."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def sweep_stale_projects(ttl_days: int = 90) -> dict:
    """Find projects with last_signal_at older than ttl_days and mark stage='Archived'."""
    from storage.airtable import get_client

    at = get_client()
    cutoff = datetime.utcnow() - timedelta(days=ttl_days)

    projects = at._get(
        "projects",
        {"filterByFormula": "AND({stage}!='Archived', {last_signal_at}!='')"},
    )

    swept = 0
    for p in projects:
        last = p.get("fields", {}).get("last_signal_at", "")
        try:
            last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            continue
        if last_dt.replace(tzinfo=None) < cutoff:
            at.update_record("projects", p["id"], {"stage": "Archived"})
            swept += 1
    logger.info("[SignalTTL] Swept %d stale projects", swept)
    return {"swept": swept, "cutoff": cutoff.isoformat()}
```

- [ ] **Step 6: Write campaign guard test**

Create `tests/test_campaign_guard.py`:

```python
"""Tests for campaign auto-pause guard."""
from unittest.mock import patch, MagicMock

from ops.campaign_guard import check_and_pause_underperformers


def test_pauses_campaign_below_floor():
    mock_stats = [
        {"id": "3040599", "name": "DC", "total_sent": 250, "total_replies": 1},  # 0.4% — pause
        {"id": "3040600", "name": "Water", "total_sent": 300, "total_replies": 5},  # 1.7% — keep
        {"id": "3040601", "name": "Industrial", "total_sent": 50, "total_replies": 0},  # too few — skip
    ]
    with patch("ops.campaign_guard._fetch_all_campaign_stats", return_value=mock_stats), \
         patch("ops.campaign_guard._pause_campaign") as pause, \
         patch("ops.campaign_guard._slack_alert") as alert:
        result = check_and_pause_underperformers(
            min_sent_threshold=200,
            reply_rate_floor=0.01,
        )

    pause.assert_called_once_with("3040599")
    alert.assert_called_once()
    assert result["paused"] == ["3040599"]
    assert result["skipped_low_volume"] == ["3040601"]
```

- [ ] **Step 7: Implement campaign guard**

Create `ops/__init__.py` (empty):

```bash
mkdir -p /Users/ethanatchley/Desktop/ECAS/ops
touch /Users/ethanatchley/Desktop/ECAS/ops/__init__.py
```

Create `ops/campaign_guard.py`:

```python
"""Auto-pause Smartlead campaigns that underperform, plus warmup pool helpers."""
from __future__ import annotations

import logging
import os
from typing import Optional

import requests

logger = logging.getLogger(__name__)


def _fetch_all_campaign_stats() -> list[dict]:
    key = os.environ.get("SMARTLEAD_API_KEY", "")
    if not key:
        raise RuntimeError("SMARTLEAD_API_KEY not set")
    resp = requests.get(
        "https://server.smartlead.ai/api/v1/campaigns/analytics",
        params={"api_key": key},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json() or []


def _pause_campaign(campaign_id: str) -> None:
    key = os.environ.get("SMARTLEAD_API_KEY", "")
    resp = requests.post(
        f"https://server.smartlead.ai/api/v1/campaigns/{campaign_id}/status",
        params={"api_key": key},
        json={"status": "PAUSED"},
        timeout=15,
    )
    resp.raise_for_status()
    logger.warning("[CampaignGuard] Paused campaign %s", campaign_id)


def _slack_alert(message: str) -> None:
    token = os.environ.get("SLACK_ACCESS_TOKEN", "")
    channel = os.environ.get("SLACK_CHANNEL", "#ecas-ops")
    if not token:
        logger.warning("[CampaignGuard] No Slack token — skipping alert: %s", message)
        return
    try:
        requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"channel": channel, "text": message},
            timeout=10,
        )
    except Exception as exc:
        logger.error("[CampaignGuard] Slack post failed: %s", exc)


def check_and_pause_underperformers(
    min_sent_threshold: int = 200,
    reply_rate_floor: float = 0.01,
) -> dict:
    """Iterate campaigns; pause any with ≥min_sent_threshold sends and reply rate < floor."""
    stats = _fetch_all_campaign_stats()
    paused: list[str] = []
    skipped_low_volume: list[str] = []
    for s in stats:
        cid = str(s.get("id", ""))
        sent = int(s.get("total_sent", 0) or 0)
        replies = int(s.get("total_replies", 0) or 0)
        if sent < min_sent_threshold:
            skipped_low_volume.append(cid)
            continue
        rate = (replies / sent) if sent else 0
        if rate < reply_rate_floor:
            _pause_campaign(cid)
            _slack_alert(
                f":warning: Auto-paused Smartlead campaign {cid} ({s.get('name','')}) — "
                f"reply rate {rate:.2%} on {sent} sent (floor {reply_rate_floor:.0%})"
            )
            paused.append(cid)
    return {"paused": paused, "skipped_low_volume": skipped_low_volume}


def warmup_pool_status() -> dict:
    """Return list of warmed-and-idle domains ready for new campaign assignment.

    A domain is considered 'ready' when all of its inboxes have completed
    Smartlead's 3-week warmup and are not currently attached to an active campaign.
    Implementation is a thin wrapper over Smartlead's warmup-settings endpoint
    plus a per-inbox 'in_use' flag we track in Doppler.
    """
    key = os.environ.get("SMARTLEAD_API_KEY", "")
    resp = requests.get(
        "https://server.smartlead.ai/api/v1/email-accounts",
        params={"api_key": key},
        timeout=30,
    )
    resp.raise_for_status()
    accounts = resp.json() or []
    ready = [
        a for a in accounts
        if a.get("warmup_details", {}).get("status") == "COMPLETED"
        and not a.get("assigned_to_campaign_id")
    ]
    return {"ready_count": len(ready), "ready_accounts": ready}
```

- [ ] **Step 8: Run all Wave 2.3 tests**

Run: `pytest tests/test_compliance.py tests/test_signal_ttl.py tests/test_campaign_guard.py -v`
Expected: all tests pass.

- [ ] **Step 9: Commit**

```bash
git add enrichment/compliance.py enrichment/signal_ttl.py ops/__init__.py ops/campaign_guard.py \
        tests/test_compliance.py tests/test_signal_ttl.py tests/test_campaign_guard.py
git commit -m "feat(factory): compliance filter + signal-TTL sweep + campaign auto-pause"
```

---

### Task 2.4: Health dashboard + OAuth refresh + API routes

**Files:**
- Create: `ops/oauth_refresh.py`, `ops/health_dashboard.py`
- Modify: `api/main.py`, `scheduler.py`
- Test: `tests/test_health_dashboard.py`

- [ ] **Step 1: Write dashboard test**

Create `tests/test_health_dashboard.py`:

```python
"""Tests for health dashboard endpoint."""
from unittest.mock import patch

from ops.health_dashboard import build_dashboard_payload


def test_dashboard_payload_structure():
    with patch("ops.health_dashboard.pre_flight_check") as pf, \
         patch("ops.health_dashboard.load_all_industries") as industries, \
         patch("ops.health_dashboard._campaign_summaries") as camps, \
         patch("ops.health_dashboard._doppler_key_presence") as doppler:
        pf.return_value = {"status": "healthy", "checks": {"apollo": {"healthy": True}}, "failures": {}}
        industries.return_value = {}
        camps.return_value = []
        doppler.return_value = {"APOLLO_API_KEY": True, "PERPLEXITY_API_KEY": False}
        payload = build_dashboard_payload()

    assert "preflight" in payload
    assert "industries" in payload
    assert "campaigns" in payload
    assert "doppler_keys" in payload
    assert payload["preflight"]["status"] == "healthy"
    assert payload["doppler_keys"]["PERPLEXITY_API_KEY"] is False
```

- [ ] **Step 2: Implement OAuth refresh**

Create `ops/oauth_refresh.py`:

```python
"""Refresh Gmail + Google Workspace OAuth tokens before expiration."""
from __future__ import annotations

import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)


def refresh_google_oauth_tokens() -> dict:
    """Best-effort token refresh across Google integrations.

    Primary targets:
      - GWS CLI (`gws`) — token in `~/.config/gws/`
      - Gmail API creds used by enrichment/outreach

    Calls `gws` CLI's internal refresh helper if available, else logs a miss.
    """
    import subprocess

    results = {"refreshed": [], "errors": []}

    try:
        r = subprocess.run(
            ["gws", "auth", "refresh"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if r.returncode == 0:
            results["refreshed"].append("gws")
        else:
            results["errors"].append(f"gws: {r.stderr.strip()[:200]}")
    except FileNotFoundError:
        results["errors"].append("gws CLI not installed")
    except Exception as e:
        results["errors"].append(f"gws: {e}")

    logger.info("[OAuthRefresh] %s", results)
    return results
```

- [ ] **Step 3: Implement health dashboard**

Create `ops/health_dashboard.py`:

```python
"""Single-URL health dashboard for the Industry Factory.

Exposes: /admin/dashboard (JSON) and /admin/dashboard.html (rendered).
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


REQUIRED_KEYS = [
    "APOLLO_API_KEY", "FINDYMAIL_API_KEY", "SMARTLEAD_API_KEY",
    "AIRTABLE_API_KEY", "ANTHROPIC_API_KEY", "PERPLEXITY_API_KEY",
    "FIRECRAWL_API_KEY", "BROWSERBASE_API_KEY", "BROWSERBASE_PROJECT_ID",
    "AIRTOP_API_KEY", "SLACK_ACCESS_TOKEN",
]


def _doppler_key_presence() -> dict[str, bool]:
    return {k: bool(os.environ.get(k)) for k in REQUIRED_KEYS}


def _campaign_summaries() -> list[dict]:
    """Pull minimal per-campaign stats from Smartlead."""
    import requests
    key = os.environ.get("SMARTLEAD_API_KEY", "")
    if not key:
        return []
    try:
        resp = requests.get(
            "https://server.smartlead.ai/api/v1/campaigns/analytics",
            params={"api_key": key},
            timeout=15,
        )
        resp.raise_for_status()
        raw = resp.json() or []
        return [
            {
                "id": s.get("id"),
                "name": s.get("name"),
                "status": s.get("status"),
                "sent_7d": s.get("sent_last_7_days", 0),
                "replies_7d": s.get("replies_last_7_days", 0),
            }
            for s in raw
        ]
    except Exception as e:
        logger.warning("[Dashboard] campaign summaries failed: %s", e)
        return []


def build_dashboard_payload() -> dict[str, Any]:
    """Assemble single JSON payload describing system health."""
    from enrichment.health import pre_flight_check
    from industries.loader import load_all_industries

    pf = pre_flight_check()
    industries = load_all_industries()
    industries_view = {
        slug: {
            "display_name": ind.display_name,
            "track": ind.track.value,
            "campaign_id": ind.campaign_id,
            "scoring_mode": ind.scoring_mode.value,
        }
        for slug, ind in industries.items()
    }

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "preflight": pf,
        "industries": industries_view,
        "campaigns": _campaign_summaries(),
        "doppler_keys": _doppler_key_presence(),
    }


def render_html(payload: dict[str, Any]) -> str:
    """Simple HTML table view — no JS framework needed."""
    def _status(b: bool) -> str:
        return '<span style="color:green">&#10003;</span>' if b else '<span style="color:red">&#10007;</span>'

    rows_keys = "".join(
        f"<tr><td>{k}</td><td>{_status(v)}</td></tr>"
        for k, v in payload["doppler_keys"].items()
    )
    rows_inds = "".join(
        f"<tr><td>{s}</td><td>{v['display_name']}</td><td>{v['track']}</td>"
        f"<td>{v['campaign_id']}</td><td>{v['scoring_mode']}</td></tr>"
        for s, v in payload["industries"].items()
    )
    rows_camps = "".join(
        f"<tr><td>{c.get('id','')}</td><td>{c.get('name','')}</td>"
        f"<td>{c.get('status','')}</td><td>{c.get('sent_7d',0)}</td>"
        f"<td>{c.get('replies_7d',0)}</td></tr>"
        for c in payload["campaigns"]
    )
    pf_status = payload["preflight"]["status"]
    pf_color = {"healthy": "green", "degraded": "orange", "blocked": "red"}.get(pf_status, "gray")

    return f"""
<!DOCTYPE html>
<html><head><title>ECAS Factory — Health</title>
<style>body{{font-family:system-ui,sans-serif;margin:2rem;max-width:1100px}}
table{{border-collapse:collapse;margin:1rem 0;width:100%}}
td,th{{border:1px solid #ddd;padding:6px 10px}}
th{{background:#f4f4f4;text-align:left}}</style></head>
<body>
<h1>Industry Factory Health</h1>
<p>Generated: {payload['generated_at']}</p>
<h2>Pre-flight: <span style="color:{pf_color}">{pf_status}</span></h2>
<pre>{payload['preflight']['checks']}</pre>
<h2>Doppler keys</h2>
<table><thead><tr><th>Key</th><th>Present</th></tr></thead><tbody>{rows_keys}</tbody></table>
<h2>Industries</h2>
<table><thead><tr><th>Slug</th><th>Display</th><th>Track</th><th>Campaign</th><th>Mode</th></tr></thead>
<tbody>{rows_inds}</tbody></table>
<h2>Campaigns (last 7d)</h2>
<table><thead><tr><th>ID</th><th>Name</th><th>Status</th><th>Sent</th><th>Replies</th></tr></thead>
<tbody>{rows_camps}</tbody></table>
</body></html>
"""
```

- [ ] **Step 4: Run dashboard test**

Run: `pytest tests/test_health_dashboard.py -v`
Expected: 1 test passes.

- [ ] **Step 5: Add API routes**

In `api/main.py`, after the existing `@app.post("/admin/run/{job_id}")` handler, add:

```python
# ── Industry Factory endpoints ──────────────────────────────────────────────

@app.post("/admin/run/industry/{slug}")
async def run_industry_endpoint(slug: str, live: bool = False):
    """Execute the Industry Factory pipeline for a given industry slug."""
    from signals.industry_runner import run_industry
    try:
        result = run_industry(slug, dry_run=not live)
        return {"ok": True, "result": result}
    except FileNotFoundError as e:
        return {"ok": False, "error": f"Unknown industry: {e}"}
    except Exception as e:
        logger.exception("Industry run failed")
        return {"ok": False, "error": str(e)}


@app.get("/admin/dashboard")
async def admin_dashboard():
    from ops.health_dashboard import build_dashboard_payload
    return build_dashboard_payload()


@app.get("/admin/dashboard.html", response_class=HTMLResponse)
async def admin_dashboard_html():
    from fastapi.responses import HTMLResponse
    from ops.health_dashboard import build_dashboard_payload, render_html
    return HTMLResponse(render_html(build_dashboard_payload()))
```

Also add to `api/main.py` imports (if not already present):

```python
from fastapi.responses import HTMLResponse
```

- [ ] **Step 6: Register cron jobs in scheduler.py**

In `scheduler.py`, after existing `scheduler.add_job` calls for populate_projects etc., add:

```python
    # ── Industry Factory: Guardrail cron jobs (added 2026-04-16) ─────────────
    from ops.campaign_guard import check_and_pause_underperformers
    from ops.oauth_refresh import refresh_google_oauth_tokens
    from enrichment.signal_ttl import sweep_stale_projects

    def job_campaign_guard():
        try:
            check_and_pause_underperformers()
        except Exception as e:
            logger.error("[Scheduler] campaign_guard failed: %s", e)

    def job_oauth_refresh():
        try:
            refresh_google_oauth_tokens()
        except Exception as e:
            logger.error("[Scheduler] oauth_refresh failed: %s", e)

    def job_signal_ttl():
        try:
            sweep_stale_projects(ttl_days=90)
        except Exception as e:
            logger.error("[Scheduler] signal_ttl failed: %s", e)

    scheduler.add_job(job_campaign_guard, CronTrigger(hour=6, minute=30), id="campaign_guard")
    scheduler.add_job(job_oauth_refresh, CronTrigger(hour=5, minute=30), id="oauth_refresh")
    scheduler.add_job(job_signal_ttl, CronTrigger(day_of_week="mon", hour=4, minute=0), id="signal_ttl")
```

- [ ] **Step 7: Commit**

```bash
git add ops/oauth_refresh.py ops/health_dashboard.py api/main.py scheduler.py \
        tests/test_health_dashboard.py
git commit -m "feat(factory): health dashboard + OAuth refresh + API endpoints + cron jobs"
```

---

## Wave 3 — Industry Configs + First Live Runs

Configuration-heavy wave. Each industry follows a checklist. Use `superpowers:verification-before-completion` before marking any task done — evidence required.

### Task 3.1: Migrate Data Center YAML

**Files:**
- Create: `industries/data_center.yaml`

- [ ] **Step 1: Write the YAML**

Create `industries/data_center.yaml`:

```yaml
slug: data_center
display_name: "Data Center & AI Infrastructure"
track: contract_motion
campaign_id: "3040599"
revenue_range_m: [20, 300]
naics: ["236220", "237130", "238210", "518210", "541513"]
titles:
  - VP Operations
  - VP Business Development
  - Director of Operations
  - President
  - CEO
  - Owner
  - COO
  - VP Preconstruction
  - Director of Business Development
states: [VA, TX, NC, GA, FL, MD, PA]
apollo_keywords:
  - data center contractor
  - critical facility contractor
  - data center epc
  - mission critical contractor
  - electrical contractor data center
  - power infrastructure contractor
  - substation contractor
  - electrical construction
directory_seeds: []
directory_auto_discovery: true
scoring_mode: positive
min_heat: 50.0
signal_ttl_days: 90
budget_cap_per_run: 25
landing_page_url: https://contractmotion-site-production.up.railway.app/data-center
sender_pool: contractmotion
```

- [ ] **Step 2: Verify loader picks it up**

Run: `cd ~/Desktop/ECAS && python -c "from industries.loader import load_all_industries; print(list(load_all_industries().keys()))"`
Expected: output includes `data_center`.

- [ ] **Step 3: Dry-run**

Run: `cd ~/Desktop/ECAS && doppler run --project ecas --config dev -- python -m signals.industry_runner data_center`
Expected: JSON output with `"status": "dry_run_ok"` and `"scraped_count" > 0`.

- [ ] **Step 4: Live run (only after dry-run logged)**

Run: `cd ~/Desktop/ECAS && doppler run --project ecas --config dev -- python -m signals.industry_runner data_center --live`
Expected: `"status": "complete"`, `projects_created > 0`, `pipeline.contacts_enrolled >= 1`.

- [ ] **Step 5: Verify in Smartlead**

Open Smartlead dashboard, campaign `3040599`. Confirm new leads appeared with today's date.

- [ ] **Step 6: Commit**

```bash
git add industries/data_center.yaml
git commit -m "feat(factory): data_center industry YAML + first live run validated"
```

---

### Task 3.2: Migrate Water YAML

Same structure as 3.1. Create `industries/water.yaml`:

```yaml
slug: water
display_name: "Water & Wastewater Infrastructure"
track: contract_motion
campaign_id: "3040600"
revenue_range_m: [20, 300]
naics: ["221310", "221320", "237110", "237120", "562212"]
titles:
  - VP Operations
  - VP Business Development
  - Director of Operations
  - President
  - CEO
  - Owner
  - COO
states: [VA, TX, NC, GA, FL, MD, PA, CA, NY]
apollo_keywords:
  - water treatment contractor
  - wastewater contractor
  - municipal utility contractor
  - water infrastructure contractor
  - civil contractor water
  - water epc
  - environmental contractor
  - water system contractor
directory_seeds: []
directory_auto_discovery: true
scoring_mode: positive
min_heat: 50.0
signal_ttl_days: 90
budget_cap_per_run: 25
landing_page_url: https://contractmotion-site-production.up.railway.app/water
sender_pool: contractmotion
```

Execute same 6-step checklist: loader check → dry-run → live run → verify → commit.

---

### Task 3.3: Commercial Roofing YAML + Smartlead setup

**Pre-req (human step, ~20 min):**
1. Create new Smartlead campaign: "ENT — AI Automation for Commercial Roofers." Get its ID.
2. Author 5-email sequence focused on: missed-call recovery, SMS follow-up, review generation, quote-to-close automation. Use `superpowers:brainstorming` → `email-sequences` skill for copy.
3. Attach a sending account from the `ai_automation` pool (separate warmed domain — see Task 4.2).
4. Publish landing page at e.g. `https://entagency.co/ai-automation/commercial-roofing`.

- [ ] **Step 1: Create YAML**

Create `industries/commercial_roofing.yaml`:

```yaml
slug: commercial_roofing
display_name: "Commercial Roofing"
track: ai_automation
campaign_id: "REPLACE_WITH_NEW_CAMPAIGN_ID"
revenue_range_m: [2, 25]
naics: ["238160"]
titles:
  - Owner
  - President
  - General Manager
  - Operations Manager
  - Vice President
states: [TX, FL, GA, NC, VA, AZ, TN, SC]
apollo_keywords:
  - commercial roofing contractor
  - flat roof contractor
  - industrial roofing
  - commercial re-roofing
  - tpo roofing contractor
  - epdm roofing contractor
directory_seeds:
  - https://www.nrca.net/nrca-members
directory_auto_discovery: true
scoring_mode: negative_tech_stack
expected_stack_if_mature:
  fsm: [ServiceTitan, Jobber, HousecallPro, FieldEdge, Buildertrend, JobNimbus]
  crm: [HubSpot, Salesforce, Zoho, Pipedrive, Copper]
  sms: [Twilio, Podium, Textline, ClickSend]
  marketing_automation: [Mailchimp, ActiveCampaign, ConvertKit, HubSpot]
prioritize_when_missing: [fsm, sms]
min_heat: 30.0
signal_ttl_days: 120
budget_cap_per_run: 40
landing_page_url: https://entagency.co/ai-automation/commercial-roofing
sender_pool: ai_automation
```

- [ ] **Step 2: Dry-run, verify scraped_count > 10**

Run: `doppler run --project ecas --config dev -- python -m signals.industry_runner commercial_roofing`
Expected: JSON output, `scraped_count >= 10`.

- [ ] **Step 3: Replace campaign_id placeholder with real ID in YAML**

After Smartlead campaign is created, edit `campaign_id` field.

- [ ] **Step 4: Live run**

Run: `doppler run --project ecas --config dev -- python -m signals.industry_runner commercial_roofing --live`
Expected: `projects_created > 0`, `pipeline.contacts_enrolled > 0`.

- [ ] **Step 5: Verify tech-stack scoring applied**

Query Airtable `projects` — recent entries should have low-maturity companies prioritized. Spot-check 3 enrolled contacts; their companies should NOT have ServiceTitan/Jobber detected.

- [ ] **Step 6: Commit**

```bash
git add industries/commercial_roofing.yaml
git commit -m "feat(factory): commercial_roofing YAML + first live run w/ negative tech-stack scoring"
```

---

### Task 3.4: Commercial Glass YAML

Same 6-step pattern as 3.3. NAICS `238150`. Directory seeds include `https://www.glass.org/` (GANA). Target titles emphasize Owner/President. Reference `industries/commercial_roofing.yaml` structure exactly.

### Task 3.5: Commercial Cleaning & Janitorial YAML

Same 6-step pattern. NAICS `561720`, `561740`. Directory seeds include `https://www.issa.com/` and `https://www.bscai.org/`. Higher `budget_cap_per_run: 50` because market is larger.

---

## Wave 4 — Deliverability + Warmup Pool

### Task 4.1: Deliverability watchdog

**Files:**
- Create: `ops/deliverability_watchdog.py`
- Test: `tests/test_deliverability_watchdog.py`

Stub test + implementation follow the same TDD rhythm as Task 2.3. Integrates with **GlockApps** or **Mailreach** API — user chooses provider during setup. Alerts `#ecas-ops` on Primary-inbox placement < 70%.

**Decision point:** Which provider? GlockApps ($59+/mo) is simpler. Mailreach ($25+/mo per inbox) has better auto-remediation. Default to GlockApps; switch if budget pressure.

- [ ] Acquire API key, add `GLOCKAPPS_API_KEY` to Doppler
- [ ] Write test: `test_pauses_on_low_placement`
- [ ] Implement `_fetch_latest_placement_report()` + `check_deliverability()`
- [ ] Register cron in `scheduler.py` — daily at 07:00
- [ ] Commit

---

### Task 4.2: Warmed domain pool for AI Automation track

**Files:** Domain provisioning is operational, not code. Doc-as-code.

- [ ] Purchase 2 new domains for AI Automation positioning (e.g. `crewopshub.com`, `fieldflowai.com` — confirm with user during Wave 3)
- [ ] Set up Google Workspace + 2 inboxes per domain
- [ ] Configure SPF, DKIM, DMARC for each
- [ ] Add to Smartlead
- [ ] Start 3-week warmup
- [ ] Once warmup completes, mark `sender_pool: ai_automation` ready
- [ ] Update `industries/commercial_*.yaml` campaign_id fields
- [ ] Write runbook in `docs/ops/domain-warmup-runbook.md` for future industry pools

---

## Success Criteria Verification

At the end of implementation, these must ALL be green:

- [ ] `pytest tests/ -v` — every test passes
- [ ] `curl https://ecas-scraper-production.up.railway.app/admin/dashboard.html` — renders without errors, shows all 5 industries + doppler key presence
- [ ] `POST /admin/run/industry/data_center` (live) — returns `status: complete` with `contacts_enrolled >= 1`
- [ ] `POST /admin/run/industry/water` (live) — same
- [ ] `POST /admin/run/industry/commercial_roofing` (live) — same + spot-check confirms low-tech-maturity targeting
- [ ] Slack `#ecas-ops` receives a run-summary post for each live run
- [ ] Scheduler has 4 new jobs registered: `campaign_guard`, `oauth_refresh`, `signal_ttl`, `deliverability_watchdog`
- [ ] No `SECTOR_CAMPAIGN_MAP` in `config.py` — removed in favor of YAML loader

---

## Out of Scope (explicit deferrals — do NOT implement)

- Multi-client tenancy (different Airtable base per client)
- LinkedIn multichannel outreach
- Closed-loop scoring-weight learning from outcomes
- Known-failure fingerprint self-healing library
- Lookalike expansion from closed deals
- Objection-auto-reply library
- Invoice handoff on deal close (separate existing workflow)

These are captured in the spec's "Out of Scope" section. A future spec + plan cycle will address them.
