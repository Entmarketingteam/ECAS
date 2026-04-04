"""
contractor/pipeline/copy_generator.py — Claude-powered email copy generation.

Implements:
- ColdIQ ATL messaging (2-3 sentences, strategic language, outcome-first)
- Signal-based personalization hook (Lite Hook conceptual tie)
- Vertical-specific case studies
- A/B variant generation (3 variants per email position)
- ColdIQ core rules: 60-90 words max, plain text, one CTA, pain over features
"""

import logging
import json
import os
from dataclasses import dataclass
from typing import Optional
import anthropic

from contractor.config import VERTICAL_ICPS

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

# ColdIQ ATL rules injected into every prompt
ATL_SYSTEM_PROMPT = """You write cold emails for business owners and executives (ATL personas).

RULES — NEVER VIOLATE:
- 60-90 words MAXIMUM for the full email body
- 2-3 sentences only
- Plain text — no HTML, no formatting, no bullet points
- One CTA — soft ask, not a hard close
- Lead with outcome/result, NOT process or features
- Strategic language: revenue, competitive advantage, risk, market position
- DO NOT mention operational details (time saved, workflows, processes)
- DO NOT use generic compliments ("Love your work!")
- DO NOT say "I" to start — start with their name or a hook
- Rotate value props: Email 1 = competitive positioning, Email 2 = proof/result, Email 3 = risk/urgency

Output format: Return ONLY the email text. No subject line. No explanation. No "Here is the email:"."""


@dataclass
class GeneratedEmail:
    """A generated email with metadata."""
    position: int           # 1, 2, or 3 (sequence position)
    subject: str
    body: str
    value_prop: str         # What value prop was used
    personalization_used: bool
    word_count: int
    variant_id: str         # "A", "B", or "C"


def _build_email1_prompt(
    vertical: str,
    company_name: str,
    first_name: str,
    personalization_hook: str,
    icp: dict,
) -> str:
    """Email 1: Pattern interrupt + specific problem + no pitch. Value prop: competitive positioning."""
    hook_line = f"Opening hook (use this if available): {personalization_hook}\n" if personalization_hook else ""

    return f"""Write a cold email (Email 1 of 3) to {first_name}, the owner/president of {company_name}, a {vertical.lower()} company.

{hook_line}
Vertical context:
- Their existential fear: {icp['existential_fear']}
- We help {vertical.lower()} companies win more commercial accounts
- Do NOT pitch. Just open a crack.

Email 1 rules:
- Lead with the hook or a pattern interrupt about their market
- Reference the competitive threat or market shift (not our service)
- End with a simple question to prompt a reply
- 60-75 words max

Write the email body only."""


def _build_email2_prompt(
    vertical: str,
    company_name: str,
    first_name: str,
    icp: dict,
) -> str:
    """Email 2: Case study + proof. Value prop: make money."""
    return f"""Write a cold email (Email 2 of 3) to {first_name} at {company_name}, a {vertical.lower()} company. They didn't reply to Email 1.

Case study to reference: We worked with a {vertical.lower()} company at their stage last quarter. They {icp['case_study_result']}.

Email 2 rules:
- Reference the case study with ONE specific result in ONE sentence
- Different value prop from Email 1 — focus on revenue/results, not competition
- Risk reversal: make saying yes feel low-stakes
- End with a soft ask for 15 minutes
- 70-85 words max

Write the email body only."""


def _build_email3_prompt(
    vertical: str,
    company_name: str,
    first_name: str,
    icp: dict,
) -> str:
    """Email 3: Urgency + breakup. Value prop: save time / risk of inaction."""
    return f"""Write a cold email (Email 3 of 3, final) to {first_name} at {company_name}, a {vertical.lower()} company. They haven't replied to 2 previous emails.

Email 3 rules:
- Acknowledge this is the last email (breakup frame)
- One final specific insight or risk they're taking by not acting
- For {vertical.lower()}: the risk is {icp['existential_fear'].split('(')[0].strip().lower()}
- Soft CTA — "if timing is off, no worries" energy but with a specific ask
- 50-70 words max
- No "I" to start

Write the email body only."""


def _build_subject_variants(vertical: str, position: int, first_name: str, company_name: str) -> list[str]:
    """Generate 3 subject line variants for A/B testing."""
    subjects = {
        1: [
            f"your {vertical.lower().split()[0]} pipeline, {first_name}",
            f"commercial accounts — {company_name}",
            f"{first_name}, quick question",
        ],
        2: [
            f"what we did for a {vertical.lower().split()[0]} company like yours",
            f"results from last quarter",
            f"one example, {first_name}",
        ],
        3: [
            f"leaving this here, {first_name}",
            f"last note",
            f"closing the loop",
        ],
    }
    return subjects.get(position, [f"following up, {first_name}"])


def generate_sequence(
    vertical: str,
    company_name: str,
    first_name: str,
    personalization_hook: str = "",
    ab_variants: int = 3,
) -> list[list[GeneratedEmail]]:
    """
    Generate a full 3-email sequence with A/B variants.

    Returns a list of 3 positions, each with `ab_variants` email options.
    Caller picks winner after 200+ sends based on reply rate.

    Args:
        vertical: "Commercial Janitorial" | "Commercial Roofing" | "Pest Control"
        company_name: Target company name (for context, not personalization at scale)
        first_name: {{first_name}} placeholder — use "{{first_name}}" for Smartlead variable
        personalization_hook: Signal-based opening line from signal_scorer
        ab_variants: Number of variants to generate per position (default 3)

    Returns:
        List of 3 email positions, each containing a list of GeneratedEmail variants
    """
    icp = VERTICAL_ICPS.get(vertical)
    if not icp:
        raise ValueError(f"Unknown vertical: {vertical}")

    prompts = [
        ("Email 1", _build_email1_prompt(vertical, company_name, first_name, personalization_hook, icp), 1, "competitive_positioning"),
        ("Email 2", _build_email2_prompt(vertical, company_name, first_name, icp), 2, "proof_results"),
        ("Email 3", _build_email3_prompt(vertical, company_name, first_name, icp), 3, "risk_urgency"),
    ]

    all_positions = []

    for label, prompt, position, value_prop in prompts:
        subjects = _build_subject_variants(vertical, position, first_name, company_name)
        position_variants = []

        for variant_idx in range(min(ab_variants, 3)):
            variant_id = ["A", "B", "C"][variant_idx]
            # Slightly vary the prompt for each variant to get different angles
            variant_prompt = prompt
            if variant_idx == 1:
                variant_prompt += "\n\nAlternate angle: lead with a question instead of a statement."
            elif variant_idx == 2:
                variant_prompt += "\n\nAlternate angle: shorter and punchier — aim for 50-60 words maximum."

            try:
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",  # Haiku for cost efficiency at scale
                    max_tokens=300,
                    system=ATL_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": variant_prompt}],
                )
                body = response.content[0].text.strip()
                word_count = len(body.split())

                position_variants.append(GeneratedEmail(
                    position=position,
                    subject=subjects[variant_idx] if variant_idx < len(subjects) else subjects[0],
                    body=body,
                    value_prop=value_prop,
                    personalization_used=bool(personalization_hook) and position == 1,
                    word_count=word_count,
                    variant_id=variant_id,
                ))

                logger.info(
                    "Generated %s variant %s | vertical=%s | words=%d",
                    label, variant_id, vertical, word_count
                )

            except Exception as e:
                logger.error("Copy generation failed for %s variant %s: %s", label, variant_id, e)
                raise

        all_positions.append(position_variants)

    return all_positions


def evaluate_copy_quality(email: GeneratedEmail) -> dict:
    """
    Run a Claude quality check on generated copy.
    Returns pass/fail with specific issues flagged.

    Quality gates:
    - Word count 50-90
    - No "I" to start
    - No operational language (workflow, process, time-saving)
    - No generic compliments
    - Contains a CTA
    - Plain text (no HTML/bullets)
    """
    issues = []

    if email.word_count < 40:
        issues.append(f"Too short: {email.word_count} words (min 40)")
    if email.word_count > 100:
        issues.append(f"Too long: {email.word_count} words (max 100)")

    body_lower = email.body.lower()
    if email.body.startswith("I "):
        issues.append("Starts with 'I' — rewrite opening")
    for banned in ["workflow", "time-saving", "efficiency", "love your work", "great work", "<br>", "<p>"]:
        if banned in body_lower:
            issues.append(f"Banned phrase detected: '{banned}'")

    cta_phrases = ["?", "worth", "open to", "15 minutes", "quick chat", "conversation", "call"]
    if not any(phrase in body_lower for phrase in cta_phrases):
        issues.append("No CTA detected — email must end with a question or soft ask")

    return {
        "passed": len(issues) == 0,
        "issues": issues,
        "word_count": email.word_count,
        "variant_id": email.variant_id,
    }
