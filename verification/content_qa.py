"""
verification/content_qa.py — Anti-hallucination content generation pipeline.

The core principle: Claude formats, primary sources provide facts.
Never the other way around.

Architecture:
  1. ASSEMBLE: Pull only verified, cited facts from primary sources
  2. GENERATE: Pass to Claude with strict grounding instructions
  3. EXTRACT: Parse all specific claims from generated content
  4. VERIFY: Every claim must trace back to a source in the input
  5. REJECT/REWRITE: If any ungrounded claim found → regenerate with correction
  6. APPROVE: Content passes QA → route to send queue

Content types supported:
  - physical_mail: one-page signal brief (company-specific)
  - email_personalization: personalization block for Smartlead sequence
  - linkedin_post: trigger-based post about project entering procurement
  - connection_request: LinkedIn connection note (300 char limit)
  - dm_message: LinkedIn DM (pattern interrupt)
"""

import json
import logging
import re
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "") or os.environ.get("ANTHROPIC_2_API_KEY", "")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")

CLAUDE_MODEL = "claude-sonnet-4-6"  # Generation
HAIKU_MODEL = "claude-haiku-4-5-20251001"  # QA checks (faster/cheaper)


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class VerifiedFact:
    claim: str           # The specific claim (e.g., "$45M SRF loan")
    source: str          # Where it came from (e.g., "USASpending.gov award #123")
    source_url: str      # Direct URL to verify
    verified: bool       # Was this fact confirmed in current verification pass?
    confidence: str      # HIGH | MEDIUM | LOW


@dataclass
class ContentPackage:
    content_type: str
    company_name: str
    recipient_name: str = ""
    recipient_title: str = ""
    sector: str = ""

    # Verified facts injected into generation
    facts: list[VerifiedFact] = field(default_factory=list)

    # Generated content
    generated_text: str = ""
    qa_passed: bool = False
    qa_flags: list[str] = field(default_factory=list)
    unverified_claims: list[str] = field(default_factory=list)
    generation_attempts: int = 0
    max_attempts: int = 3

    def add_fact(self, claim: str, source: str, source_url: str = "",
                 verified: bool = True, confidence: str = "HIGH"):
        self.facts.append(VerifiedFact(claim, source, source_url, verified, confidence))

    def facts_as_context(self) -> str:
        lines = []
        for f in self.facts:
            status = "VERIFIED" if f.verified else "UNVERIFIED"
            lines.append(f"[{status}] {f.claim} (Source: {f.source})")
        return "\n".join(lines)


# ── Claude API wrapper ─────────────────────────────────────────────────────────

def _claude(prompt: str, model: str = CLAUDE_MODEL, max_tokens: int = 1000,
            system: str = "") -> Optional[str]:
    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not set")
        return None
    try:
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            payload["system"] = system
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["content"][0]["text"]
    except Exception as e:
        logger.error("Claude API call failed: %s", e)
        return None


# ── Step 1: Content generation with strict grounding ──────────────────────────

SYSTEM_PROMPT_GROUNDED = """You are a content writer for a B2B outbound campaign targeting EPC contractors.

CRITICAL RULES — violation causes immediate rejection:
1. Only use facts explicitly provided in the VERIFIED FACTS section. No exceptions.
2. Do not add any dollar amounts, dates, project names, locations, or metrics not in the facts list.
3. Do not use phrases like "I heard", "I saw", "I noticed" about data not provided.
4. If a fact is marked [UNVERIFIED], do not include it in the content.
5. Do not reference any industry knowledge, trends, or general statements as if they are specific to this company unless that specific data is in the facts list.
6. You may use general professional language and tone freely.
7. Never invent company history, project history, or competitor context.

When you're done, append on a new line: FACTS_USED: followed by a comma-separated list of the exact fact claims you included."""

TEMPLATES = {
    "physical_mail": {
        "char_limit": 800,
        "instruction": """Write a one-page signal brief for {company_name}.
Format as:
- One opening sentence naming the company and referencing their sector
- A header: "Active Pre-Procurement Projects in Your Territory"
- 3-5 bullet points, each being one verified project signal
- One closing sentence inviting them to contact us

Each bullet must follow: [Project Name] — [Dollar Amount] — [Signal Type] — [Timeline Note]
Only use VERIFIED FACTS. Leave a placeholder [PROJECT] if a fact is UNVERIFIED rather than inventing data.""",
    },
    "email_personalization": {
        "char_limit": 300,
        "instruction": """Write a 2-3 sentence personalization opening for a cold email to {recipient_name} at {company_name}.
Tone: direct, peer-to-peer, no fluff.
Reference ONLY the verified facts provided.
Do not start with "I", "Hi", or the person's name.""",
    },
    "linkedin_post": {
        "char_limit": 700,
        "instruction": """Write a LinkedIn post about a project entering procurement in the water/data center infrastructure sector.
Structure: Hook line → 2-3 fact-based lines → Observation → Optional question.
Only use VERIFIED FACTS. Do not add commentary about market trends unless a specific fact supports it.
No hashtags unless they are sector-specific (#WaterInfrastructure, #DataCenter, #EPC).""",
    },
    "connection_request": {
        "char_limit": 300,
        "instruction": """Write a LinkedIn connection request note to {recipient_name} ({recipient_title}) at {company_name}.
Max 300 characters. One sentence about a specific verified project signal relevant to their work.
No pitching. No "I'd love to connect." Just a relevant, specific observation.""",
    },
    "dm_message": {
        "char_limit": 500,
        "instruction": """Write a LinkedIn DM pattern interrupt message to {recipient_name} at {company_name}.
They accepted a connection request but haven't responded to the cold email sequence.
Reference a SPECIFIC verified fact about a project in their territory.
2-3 sentences max. Direct. No filler. End with one specific question.""",
    },
}


def generate_content(pkg: ContentPackage) -> str:
    template = TEMPLATES.get(pkg.content_type)
    if not template:
        raise ValueError(f"Unknown content type: {pkg.content_type}")

    instruction = template["instruction"].format(
        company_name=pkg.company_name,
        recipient_name=pkg.recipient_name or "the reader",
        recipient_title=pkg.recipient_title or "",
    )

    verified_only = [f for f in pkg.facts if f.verified]
    if not verified_only:
        logger.warning("No verified facts for %s — cannot generate grounded content", pkg.company_name)
        return ""

    facts_block = pkg.facts_as_context()
    char_limit = template["char_limit"]

    prompt = f"""VERIFIED FACTS (only use these — do not add any other specific data):
{facts_block}

TASK:
{instruction}

IMPORTANT: Keep output under {char_limit} characters. Do not exceed this limit."""

    return _claude(prompt, system=SYSTEM_PROMPT_GROUNDED) or ""


# ── Step 2: Claim extraction ───────────────────────────────────────────────────

CLAIM_EXTRACTION_PROMPT = """Extract every specific, verifiable claim from this text.
A "specific claim" is: a dollar amount, a date, a project name, a company name (other than the target), a location reference beyond just a state, a metric, a percentage, or a government filing reference.

Return JSON array: [{{"claim": "...", "type": "dollar|date|project|company|location|metric|filing"}}]

Text:
{text}"""


def extract_claims(text: str) -> list[dict]:
    result = _claude(
        CLAIM_EXTRACTION_PROMPT.format(text=text),
        model=HAIKU_MODEL,
        max_tokens=500,
    )
    if not result:
        return []
    m = re.search(r"\[.*\]", result, re.DOTALL)
    if not m:
        return []
    try:
        return json.loads(m.group())
    except Exception:
        return []


# ── Step 3: Claim verification ─────────────────────────────────────────────────

def verify_claim_against_facts(claim: str, facts: list[VerifiedFact]) -> tuple[bool, str]:
    """
    Check if a claim in generated content is supported by the verified facts list.
    Returns (is_grounded, source).
    """
    claim_lower = claim.lower()
    for fact in facts:
        # Direct substring match
        if claim_lower in fact.claim.lower() or fact.claim.lower() in claim_lower:
            return True, fact.source
        # Partial word match (for dollar amounts, project names)
        claim_words = set(re.findall(r"\b\w{4,}\b", claim_lower))
        fact_words = set(re.findall(r"\b\w{4,}\b", fact.claim.lower()))
        overlap = claim_words & fact_words
        if len(overlap) >= 2 and len(overlap) / max(len(claim_words), 1) >= 0.5:
            return True, fact.source
    return False, ""


# ── Step 4: Full QA pass ───────────────────────────────────────────────────────

def qa_content(pkg: ContentPackage) -> ContentPackage:
    """
    Run the full QA pipeline on generated content.
    Extracts claims → verifies each → flags ungrounded → rejects if needed.
    """
    if not pkg.generated_text:
        pkg.qa_flags.append("EMPTY_CONTENT")
        return pkg

    claims = extract_claims(pkg.generated_text)
    ungrounded = []

    verified_facts_only = [f for f in pkg.facts if f.verified]
    for claim_obj in claims:
        claim_text = claim_obj.get("claim", "")
        grounded, source = verify_claim_against_facts(claim_text, verified_facts_only)
        if not grounded:
            ungrounded.append(claim_text)
            logger.warning("Ungrounded claim in %s content: '%s'", pkg.company_name, claim_text)

    pkg.unverified_claims = ungrounded

    if not ungrounded:
        pkg.qa_passed = True
        logger.info("QA PASSED for %s (%s)", pkg.company_name, pkg.content_type)
    else:
        pkg.qa_passed = False
        pkg.qa_flags.append(f"UNGROUNDED_CLAIMS: {ungrounded}")
        logger.warning("QA FAILED for %s: %d ungrounded claims", pkg.company_name, len(ungrounded))

    return pkg


# ── Step 5: Regeneration loop ──────────────────────────────────────────────────

def regenerate_with_corrections(pkg: ContentPackage) -> ContentPackage:
    """
    If QA failed, regenerate with explicit instruction to remove ungrounded claims.
    Retries up to max_attempts times.
    """
    correction_prompt_suffix = f"""

CORRECTIONS REQUIRED — these claims appeared in your previous draft but are NOT in the verified facts:
{json.dumps(pkg.unverified_claims, indent=2)}

Remove or replace each of these with content that only uses the verified facts provided.
Do NOT attempt to verify these claims yourself — if the data isn't in the VERIFIED FACTS section, omit it."""

    template = TEMPLATES.get(pkg.content_type, {})
    instruction = template.get("instruction", "Rewrite the content").format(
        company_name=pkg.company_name,
        recipient_name=pkg.recipient_name or "the reader",
        recipient_title=pkg.recipient_title or "",
    )

    facts_block = pkg.facts_as_context()
    char_limit = template.get("char_limit", 500)

    prompt = f"""VERIFIED FACTS:
{facts_block}

TASK:
{instruction}{correction_prompt_suffix}

Keep under {char_limit} characters."""

    new_text = _claude(prompt, system=SYSTEM_PROMPT_GROUNDED)
    if new_text:
        pkg.generated_text = new_text
        pkg.unverified_claims = []
        pkg.qa_flags = []

    return pkg


# ── Main pipeline ──────────────────────────────────────────────────────────────

def generate_and_verify(pkg: ContentPackage) -> ContentPackage:
    """
    Full generate → QA → regenerate loop.
    Returns ContentPackage with qa_passed=True or exhausted max_attempts.
    """
    if not ANTHROPIC_API_KEY:
        pkg.qa_flags.append("NO_API_KEY: cannot generate content")
        return pkg

    for attempt in range(1, pkg.max_attempts + 1):
        pkg.generation_attempts = attempt
        logger.info("Generating %s content for %s (attempt %d/%d)",
                    pkg.content_type, pkg.company_name, attempt, pkg.max_attempts)

        if attempt == 1:
            pkg.generated_text = generate_content(pkg)
        else:
            pkg = regenerate_with_corrections(pkg)

        if not pkg.generated_text:
            pkg.qa_flags.append("EMPTY_GENERATION")
            continue

        pkg = qa_content(pkg)

        if pkg.qa_passed:
            break
        else:
            logger.warning("QA failed attempt %d, retrying...", attempt)

    if not pkg.qa_passed:
        pkg.qa_flags.append(f"EXHAUSTED_ATTEMPTS: {pkg.max_attempts} tries, still failing QA")
        logger.error("Content QA failed after %d attempts for %s", pkg.max_attempts, pkg.company_name)

    return pkg


# ── Batch content generation ───────────────────────────────────────────────────

def generate_batch(
    records: list[dict],
    content_type: str,
    fact_builder: callable,
) -> list[dict]:
    """
    Generate verified content for a batch of records.

    fact_builder: function(record) -> list[VerifiedFact]
      Caller is responsible for building the fact list from their data sources.
      This separation ensures data retrieval and generation stay decoupled.

    Returns records with added 'content', 'qa_passed', 'qa_flags' keys.
    """
    results = []
    for record in records:
        pkg = ContentPackage(
            content_type=content_type,
            company_name=record.get("company_name", ""),
            recipient_name=record.get("contact_first_name", ""),
            recipient_title=record.get("title", ""),
            sector=record.get("sector", ""),
        )
        pkg.facts = fact_builder(record)
        pkg = generate_and_verify(pkg)

        record["content"] = pkg.generated_text
        record["qa_passed"] = pkg.qa_passed
        record["qa_flags"] = pkg.qa_flags
        record["generation_attempts"] = pkg.generation_attempts
        record["unverified_claims"] = pkg.unverified_claims
        results.append(record)

    passed = sum(1 for r in results if r["qa_passed"])
    logger.info("Batch complete: %d/%d passed QA", passed, len(results))
    return results
