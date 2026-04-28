"""
verification/entity_resolver.py — Multi-source company identity verification.

The problem this solves:
  "CDM Smith" and "CDM Constructors" are different companies.
  "Garney Construction" and "Garney Companies" are the same company.
  "AECOM" scraped from one source might be the wrong AECOM subsidiary.

Resolution strategy (in order, short-circuit on high confidence):
  1. SAM.gov entity lookup by legal business name — federal registration = authoritative
  2. USASpending recipient lookup — confirms they actually won federal EPC work
  3. Domain discovery via Tavily web search → homepage title match
  4. Similarity check against all other companies in the active list

All data comes from primary sources. Claude is used ONLY for:
  - Name normalization ("CDM CONSTRUCTORS INC" → "CDM Constructors")
  - Disambiguation when two sources return different legal names for same entity
  NOT for generating or guessing company facts.
"""

import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from verification.confidence import (
    ConfidenceScore, has_generic_name, find_similar_names, levenshtein
)

logger = logging.getLogger(__name__)

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "") or os.environ.get("ANTHROPIC_2_API_KEY", "")
SAM_GOV_API_KEY = os.environ.get("SAM_GOV_API_KEY", "")

REQUEST_DELAY = 0.8


# ── SAM.gov entity lookup ──────────────────────────────────────────────────────

def lookup_sam_gov(company_name: str) -> Optional[dict]:
    """
    Query SAM.gov for an exact or near-exact legal business name match.
    Returns entity data dict or None.
    """
    url = "https://api.sam.gov/entity-information/v3/entities"
    params = {
        "legalBusinessName": company_name,
        "registrationStatus": "A",
        "includeSections": "entityRegistration,coreData",
    }
    if SAM_GOV_API_KEY:
        params["api_key"] = SAM_GOV_API_KEY

    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        entities = data.get("entityData", [])
        if not entities:
            return None
        # Take the first (closest) match
        entity = entities[0]
        reg = entity.get("entityRegistration", {})
        core = entity.get("coreData", {})
        return {
            "legal_name": reg.get("legalBusinessName", ""),
            "cage": reg.get("cageCode", ""),
            "uei": reg.get("ueiSAM", ""),
            "state": (core.get("physicalAddress") or {}).get("stateOrProvinceCode", ""),
            "city": (core.get("physicalAddress") or {}).get("city", ""),
            "naics_codes": [
                n.get("naicsCode") for n in
                (core.get("businessTypes", {}).get("naicsCode", []) or [])
            ],
        }
    except Exception as e:
        logger.debug("SAM.gov lookup failed for '%s': %s", company_name, e)
        return None


# ── USASpending recipient lookup ───────────────────────────────────────────────

def lookup_usaspending(company_name: str) -> Optional[dict]:
    """
    Search USASpending for this recipient — confirms real federal EPC work.
    Returns summary of contract history or None.
    """
    url = "https://api.usaspending.gov/api/v2/recipient/"
    try:
        r = requests.post(
            url,
            json={"keyword": company_name, "limit": 5},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        if not results:
            return None
        # Find closest name match
        best = min(results, key=lambda x: levenshtein(x.get("name", ""), company_name))
        if levenshtein(best.get("name", ""), company_name) > 8:
            return None  # Too different — not the same company
        return {
            "name": best.get("name", ""),
            "uei": best.get("uei", ""),
            "total_obligated": best.get("total_obligated_amount", 0),
            "state": best.get("location", {}).get("state_code", ""),
        }
    except Exception as e:
        logger.debug("USASpending lookup failed for '%s': %s", company_name, e)
        return None


# ── Domain discovery via Tavily ────────────────────────────────────────────────

def discover_domain(company_name: str) -> tuple[str, bool]:
    """
    Find the company's official website via Tavily search.
    Returns (domain, verified) where verified means homepage title matches company name.
    """
    if not TAVILY_API_KEY:
        logger.debug("TAVILY_API_KEY not set — domain discovery skipped")
        return "", False

    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_API_KEY,
                "query": f'"{company_name}" official website contractor EPC',
                "search_depth": "basic",
                "max_results": 5,
                "include_domains": [],
                "exclude_domains": ["linkedin.com", "facebook.com", "twitter.com",
                                     "indeed.com", "glassdoor.com", "bloomberg.com"],
            },
            timeout=15,
        )
        r.raise_for_status()
        results = r.json().get("results", [])

        for result in results:
            url = result.get("url", "")
            title = result.get("title", "").lower()
            content = result.get("content", "").lower()

            # Extract domain
            m = re.search(r"https?://(?:www\.)?([^/]+)", url)
            if not m:
                continue
            domain = m.group(1).lower()

            # Skip noise domains
            if any(x in domain for x in ["linkedin", "facebook", "indeed", "glassdoor",
                                           "bloomberg", "dnb.com", "manta.com", "bizapedia"]):
                continue

            # Verify: company name words appear in page title or content
            name_words = [w.lower() for w in company_name.split()
                          if len(w) > 3 and w.lower() not in {"inc", "llc", "corp", "ltd", "the"}]
            match_count = sum(1 for w in name_words if w in title or w in content[:500])
            match_ratio = match_count / max(len(name_words), 1)

            if match_ratio >= 0.6:
                return domain, True
            elif match_ratio >= 0.4:
                return domain, False  # Possible match, lower confidence

        return "", False
    except Exception as e:
        logger.debug("Domain discovery failed for '%s': %s", company_name, e)
        return "", False


# ── Claude disambiguation ──────────────────────────────────────────────────────

def disambiguate_with_claude(
    company_name: str,
    sam_result: Optional[dict],
    usaspending_result: Optional[dict],
    similar_names: list[str],
) -> dict:
    """
    When sources conflict or similar names exist, ask Claude to reason through
    the ambiguity using ONLY the data provided — no internet access, no guessing.

    Claude is explicitly instructed: if you cannot determine with certainty
    from the provided data, say UNCERTAIN rather than guess.
    """
    if not ANTHROPIC_API_KEY:
        return {"verdict": "UNCERTAIN", "reasoning": "No Claude API key"}

    context_parts = []
    if sam_result:
        context_parts.append(f"SAM.gov legal name: {sam_result['legal_name']} (CAGE: {sam_result['cage']}, State: {sam_result['state']})")
    if usaspending_result:
        context_parts.append(f"USASpending recipient: {usaspending_result['name']} (total contracts: ${usaspending_result['total_obligated']:,.0f})")
    if similar_names:
        context_parts.append(f"Similar company names also in our list: {', '.join(similar_names)}")

    context = "\n".join(context_parts) if context_parts else "No additional data available."

    prompt = f"""You are verifying company identity for an outbound sales system. Your job is to determine if the following company name is correctly identified based ONLY on the data provided below. Do NOT use any knowledge outside of what is given.

Company name we scraped: "{company_name}"

Data from primary sources:
{context}

Answer in JSON with these exact fields:
{{
  "verdict": "CONFIRMED" | "UNCERTAIN" | "WRONG",
  "canonical_name": "the most accurate legal name for this company, or null if UNCERTAIN/WRONG",
  "reasoning": "one sentence explaining your determination",
  "risk": "LOW" | "MEDIUM" | "HIGH"
}}

Rules:
- CONFIRMED: sources clearly identify this as the correct company
- UNCERTAIN: data is ambiguous or sources conflict — do NOT guess
- WRONG: sources clearly indicate this is a different company
- If similar names exist and you cannot distinguish them from provided data alone, verdict must be UNCERTAIN
- Never invent facts. Never use outside knowledge."""

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",  # Fast + cheap for verification tasks
                "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=20,
        )
        r.raise_for_status()
        text = r.json()["content"][0]["text"]
        # Extract JSON
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            import json
            return json.loads(m.group())
        return {"verdict": "UNCERTAIN", "reasoning": "Could not parse Claude response"}
    except Exception as e:
        logger.warning("Claude disambiguation failed: %s", e)
        return {"verdict": "UNCERTAIN", "reasoning": str(e)}


# ── Main resolver ──────────────────────────────────────────────────────────────

def resolve_entity_parallel(company_name: str, all_company_names: list[str],
                            domain_hint: str = "") -> ConfidenceScore:
    """Parallel version: runs SAM.gov, USASpending, and domain discovery concurrently."""
    import concurrent.futures
    cs = ConfidenceScore(company_name=company_name, domain=domain_hint)
    cs.generic_name = has_generic_name(company_name)

    similar = find_similar_names(company_name, all_company_names, threshold=4)
    if similar:
        cs.similar_name_found = True
        cs.flags.append(f"SIMILAR_NAMES: {', '.join(similar[:3])}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        f_sam = ex.submit(lookup_sam_gov, company_name)
        f_spend = ex.submit(lookup_usaspending, company_name)
        f_domain = ex.submit(discover_domain, company_name) if not domain_hint else None

    sam_result = f_sam.result()
    spending_result = f_spend.result()
    domain, verified = (domain_hint, True) if domain_hint else (f_domain.result() if f_domain else ("", False))

    if sam_result:
        if levenshtein(sam_result["legal_name"].lower(), company_name.lower()) <= 5:
            cs.sam_gov_confirmed = True
            cs.company_name = sam_result["legal_name"]
    if spending_result:
        cs.usaspending_confirmed = True
    if domain:
        cs.domain = domain
        if verified:
            cs.domain_verified = True

    if cs.similar_name_found or (sam_result and not cs.sam_gov_confirmed):
        result = disambiguate_with_claude(company_name, sam_result, spending_result, similar)
        if result.get("verdict") == "CONFIRMED":
            if result.get("canonical_name"):
                cs.company_name = result["canonical_name"]
            cs.similar_name_found = False
        elif result.get("verdict") == "UNCERTAIN":
            cs.flags.append(f"DISAMBIGUATION_UNCERTAIN: {result.get('reasoning', '')}")
        elif result.get("verdict") == "WRONG":
            cs.flags.append(f"WRONG_ENTITY: {result.get('reasoning', '')}")
            cs.score = 0
            return cs

    cs.compute()
    return cs


def resolve_entity(
    company_name: str,
    all_company_names: list[str],
    domain_hint: str = "",
) -> ConfidenceScore:
    """
    Full entity resolution pipeline for one company.
    Returns a ConfidenceScore with all checks populated.
    """
    cs = ConfidenceScore(company_name=company_name, domain=domain_hint)
    cs.generic_name = has_generic_name(company_name)

    # 1. Similar name check
    similar = find_similar_names(company_name, all_company_names, threshold=4)
    if similar:
        cs.similar_name_found = True
        cs.flags.append(f"SIMILAR_NAMES: {', '.join(similar[:3])}")
        logger.debug("'%s' has similar names: %s", company_name, similar)

    # 2. SAM.gov lookup
    time.sleep(REQUEST_DELAY)
    sam_result = lookup_sam_gov(company_name)
    if sam_result:
        # Verify the returned name actually matches
        edit_dist = levenshtein(sam_result["legal_name"].lower(), company_name.lower())
        if edit_dist <= 5:
            cs.sam_gov_confirmed = True
            # Use SAM.gov's canonical legal name going forward
            cs.company_name = sam_result["legal_name"]
        else:
            cs.flags.append(f"SAM_NAME_MISMATCH: scraped='{company_name}' sam='{sam_result['legal_name']}'")

    # 3. USASpending lookup
    time.sleep(REQUEST_DELAY)
    spending_result = lookup_usaspending(company_name)
    if spending_result:
        cs.usaspending_confirmed = True

    # 4. Domain discovery
    if domain_hint:
        domain, verified = domain_hint, True  # Caller already has a domain
    else:
        time.sleep(REQUEST_DELAY)
        domain, verified = discover_domain(company_name)

    if domain:
        cs.domain = domain
        if verified:
            cs.domain_verified = True
        else:
            cs.flags.append(f"DOMAIN_UNVERIFIED: found {domain} but homepage match was weak")

    # 5. Claude disambiguation if ambiguous
    if cs.similar_name_found or (sam_result and not cs.sam_gov_confirmed):
        result = disambiguate_with_claude(company_name, sam_result, spending_result, similar)
        if result.get("verdict") == "CONFIRMED":
            if result.get("canonical_name"):
                cs.company_name = result["canonical_name"]
            cs.similar_name_found = False  # Claude resolved it
            cs.flags = [f for f in cs.flags if "SIMILAR_NAMES" not in f]
        elif result.get("verdict") == "UNCERTAIN":
            cs.flags.append(f"DISAMBIGUATION_UNCERTAIN: {result.get('reasoning', '')}")
        elif result.get("verdict") == "WRONG":
            cs.flags.append(f"WRONG_ENTITY: {result.get('reasoning', '')}")
            cs.score = 0
            cs.checks_failed.append("entity_wrong_per_claude")
            return cs

    cs.compute()
    logger.debug(
        "Entity '%s': score=%d route=%s flags=%s",
        cs.company_name, cs.score, cs.route, cs.flags
    )
    return cs


def resolve_batch(
    companies: list[dict],
    domain_field: str = "domain",
    name_field: str = "company_name",
    max_workers: int = 8,
) -> list[tuple[dict, ConfidenceScore]]:
    """
    Resolve a batch of company records in parallel.
    Returns list of (original_record, confidence_score) tuples in original order.
    max_workers=8 runs 8 companies concurrently, cutting wall time by ~8x.
    """
    import concurrent.futures
    all_names = [c[name_field] for c in companies]
    results = [None] * len(companies)

    def _resolve_one(args):
        idx, company = args
        logger.info("Resolving [%d/%d]: %s", idx + 1, len(companies), company[name_field])
        cs = resolve_entity_parallel(
            company_name=company[name_field],
            all_company_names=all_names,
            domain_hint=company.get(domain_field, ""),
        )
        return idx, (company, cs)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_resolve_one, (i, c)): i for i, c in enumerate(companies)}
        for future in concurrent.futures.as_completed(futures):
            try:
                idx, result = future.result()
                results[idx] = result
            except Exception as e:
                logger.error("Resolution failed for record %d: %s", futures[future], e)

    return [r for r in results if r is not None]
