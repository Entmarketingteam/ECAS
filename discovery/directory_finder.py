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
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)


class ScraperType(str, Enum):
    STATIC = "static"
    GATED = "gated"
    JS_HEAVY = "js_heavy"


@dataclass
class DirectoryCandidate:
    url: str
    scraper_type: ScraperType
    confidence: float
    source: str = "perplexity+claude"


GATED_HOSTS = {
    "linkedin.com", "zoominfo.com", "sales-navigator.com",
}
JS_HEAVY_HOSTS = {
    "swapcard.com", "eventmobi.com", "hopin.com", "cvent.com",
    "bizzabo.com", "pheedloop.com",
}


def classify_url(url: str) -> ScraperType:
    host = (urlparse(url).hostname or "").lower()
    for gated in GATED_HOSTS:
        if gated in host:
            return ScraperType.GATED
    for js in JS_HEAVY_HOSTS:
        if js in host:
            return ScraperType.JS_HEAVY
    return ScraperType.STATIC


def _perplexity_search(query: str) -> str:
    """Call Perplexity API for a research query."""
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
    """Ask Claude to extract candidate directory URLs."""
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
    if any(bad in url_lower for bad in ["wikipedia.org", "reddit.com", "youtube.com"]):
        return 0.0
    return round(base + boost, 2)


def discover_directories(
    industry_display_name: str,
    keywords: list[str],
    min_confidence: float = 0.5,
    min_results: int = 3,
) -> list[DirectoryCandidate]:
    """Discover directory URLs for an industry."""
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
            f"got {len(candidates)}, need >={min_results} at confidence >={min_confidence}. "
            f"Raw URLs: {urls}"
        )

    return candidates
