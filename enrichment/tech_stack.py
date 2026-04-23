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


def _normalize_domain(url_or_domain: str) -> str:
    s = url_or_domain.strip().lower()
    if not s.startswith("http"):
        s = "https://" + s
    host = (urlparse(s).hostname or "").lower()
    return host.removeprefix("www.")


def _wappalyzer_scan(url: str) -> list[str]:
    """Run Wappalyzer on a live URL. Returns list of detected technology names.

    Gracefully returns [] if python-Wappalyzer isn't available in this env
    (e.g. Python 3.14 removed pkg_resources). Railway uses 3.11 where it works.
    """
    try:
        from Wappalyzer import Wappalyzer, WebPage
    except ImportError:
        logger.debug("[TechStack] python-Wappalyzer not importable in this env")
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
    """Optional BuiltWith enrichment."""
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
    """Enrich many companies sequentially."""
    return [enrich_company(w, db=db, ttl_days=ttl_days) for w in websites]
