#!/usr/bin/env python3
"""
verification/pipeline.py — Full verification + content generation orchestrator.

Flow for every lead before anything is sent:

  STAGE 1 — ENTITY RESOLUTION
    ├─ Similar name dedup check (Levenshtein)
    ├─ SAM.gov legal name lookup
    ├─ USASpending contract history lookup
    ├─ Domain discovery (Tavily)
    └─ Claude disambiguation if ambiguous
    → Confidence score → route: AUTO / REVIEW / HOLD

  STAGE 2 — SIGNAL VERIFICATION
    ├─ Re-fetch source URL for each signal
    ├─ Verify project name, amount, status not changed
    ├─ Check project not already awarded
    └─ Tavily fallback for unstructured signals
    → Signal status: LIVE / STALE / AWARDED / DEAD / UNCERTAIN

  STAGE 3 — CONTACT VERIFICATION
    ├─ Email validation (Findymail → MillionVerifier fallback)
    └─ Email domain vs company domain check
    → Email confidence: valid / risky / invalid

  STAGE 4 — CONTENT GENERATION
    ├─ Assemble only VERIFIED, LIVE facts
    ├─ Generate via Claude with strict grounding
    ├─ Extract all specific claims from output
    ├─ Verify every claim traces back to a source
    └─ Regenerate with corrections if ungrounded claims found
    → Content: approved / needs_review / failed

  STAGE 5 — ROUTING
    ├─ AUTO (score>=70, signals LIVE, email valid, QA passed) → send queue
    ├─ REVIEW (any stage uncertain) → human review queue with flags
    └─ HOLD (score<40, wrong entity, email invalid, QA failed) → quarantine

Usage:
  python verification/pipeline.py --input signals/output/epc_leads_2026-04-28.csv
  python verification/pipeline.py --input leads.csv --content-type email_personalization
  python verification/pipeline.py --input leads.csv --stage entity  # entity only
  python verification/pipeline.py --batch-size 50 --dry-run
"""

import argparse
import csv
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

from verification.confidence import ConfidenceScore, Route
from verification.entity_resolver import resolve_batch
from verification.signal_verifier import verify_signals_batch, SignalStatus
from verification.content_qa import (
    ContentPackage, VerifiedFact, generate_and_verify
)

try:
    from enrichment.millionverifier import verify_email
except ImportError:
    def verify_email(email):
        return False, "unknown"

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
OUTPUT_DIR = Path(__file__).parent.parent / "signals" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ── Stage 3: Contact verification ─────────────────────────────────────────────

def verify_contact(record: dict) -> dict:
    """Validate email and check domain consistency."""
    email = record.get("email", "")
    company_domain = record.get("domain", "")
    result = {"email_valid": False, "email_quality": "unknown", "email_domain_match": True}

    if not email:
        result["email_flag"] = "NO_EMAIL"
        return result

    # Check email domain matches company domain
    email_domain = email.split("@")[-1].lower() if "@" in email else ""
    if company_domain and email_domain:
        import re as _re
        normalized_domain = _re.sub(r"^www\.", "", company_domain.lower())
        if email_domain != normalized_domain:
            result["email_domain_match"] = False
            result["email_flag"] = f"DOMAIN_MISMATCH: email={email_domain} company={company_domain}"

    # Email validation
    try:
        is_valid, quality = verify_email(email)
        result["email_valid"] = is_valid
        result["email_quality"] = quality
        if not is_valid:
            result["email_flag"] = f"EMAIL_INVALID: quality={quality}"
    except Exception as e:
        result["email_flag"] = f"EMAIL_VERIFY_ERROR: {e}"

    return result


# ── Signal → fact builder ──────────────────────────────────────────────────────

def build_facts_from_record(record: dict) -> list[VerifiedFact]:
    """
    Convert a verified record's signals into VerifiedFact objects for content generation.
    Only includes facts from signals with status LIVE.
    """
    facts = []

    # Company identity facts
    if record.get("sam_gov_confirmed"):
        facts.append(VerifiedFact(
            claim=f"{record['company_name']} is registered in SAM.gov as an active federal contractor",
            source="SAM.gov entity registry",
            source_url="https://sam.gov",
            verified=True,
            confidence="HIGH",
        ))

    if record.get("usaspending_total"):
        total = record["usaspending_total"]
        facts.append(VerifiedFact(
            claim=f"{record['company_name']} has been awarded ${total:,.0f} in federal contracts",
            source="USASpending.gov award history",
            source_url="https://usaspending.gov",
            verified=True,
            confidence="HIGH",
        ))

    # Signal facts (only LIVE signals)
    for sig in record.get("signals", []):
        if sig.get("verification", {}).get("status") != SignalStatus.LIVE:
            continue

        project_name = sig.get("project_name", "")
        dollar_amount = sig.get("dollar_amount", "")
        signal_type = sig.get("signal_type", "")
        state = sig.get("state", "")
        source_url = sig.get("source_url", "")
        timeline = sig.get("timeline_note", "")

        claim_parts = [p for p in [project_name, dollar_amount, signal_type, f"in {state}" if state else "", timeline] if p]
        claim = " — ".join(claim_parts)

        if claim:
            facts.append(VerifiedFact(
                claim=claim,
                source=sig.get("source", ""),
                source_url=source_url,
                verified=True,
                confidence="HIGH" if sig.get("verification", {}).get("status") == SignalStatus.LIVE else "MEDIUM",
            ))

    return facts


# ── Routing logic ──────────────────────────────────────────────────────────────

def route_record(
    record: dict,
    cs: ConfidenceScore,
    contact_result: dict,
    content_pkg: Optional[ContentPackage],
) -> str:
    """Determine final routing for a record after all verification stages."""

    # Hard blocks → HOLD
    if cs.score == 0:
        return "HOLD"
    if record.get("entity_verdict") == "WRONG":
        return "HOLD"
    if contact_result.get("email_quality") == "bad":
        return "HOLD"

    # Soft issues → REVIEW
    if cs.route == Route.REVIEW:
        return "REVIEW"
    if not contact_result.get("email_valid", False):
        return "REVIEW"
    if not contact_result.get("email_domain_match", True):
        return "REVIEW"
    if content_pkg and not content_pkg.qa_passed:
        return "REVIEW"

    # All clear → AUTO
    if cs.route == Route.AUTO and contact_result.get("email_valid") and (not content_pkg or content_pkg.qa_passed):
        return "AUTO"

    return "REVIEW"


# ── Main pipeline ──────────────────────────────────────────────────────────────

def run_pipeline(
    records: list[dict],
    content_type: Optional[str] = None,
    stages: list[str] = None,
    dry_run: bool = False,
    output_prefix: str = "",
) -> dict:
    """
    Full verification pipeline. Stages: entity, signal, contact, content, route.
    Pass stages=["entity"] to run only entity resolution.
    """
    if stages is None:
        stages = ["entity", "signal", "contact", "content", "route"]

    results = {
        "total": len(records),
        "auto": [],
        "review": [],
        "hold": [],
        "stage_counts": {},
    }

    logger.info("Pipeline starting: %d records, stages=%s", len(records), stages)

    # STAGE 1: Entity resolution
    if "entity" in stages:
        logger.info("=== STAGE 1: Entity Resolution ===")
        entity_results = resolve_batch(records)
        for record, cs in entity_results:
            record["confidence_score"] = cs.score
            record["confidence_route"] = cs.route.value
            record["confidence_flags"] = cs.flags
            record["company_name"] = cs.company_name  # Use canonical name
            record["domain"] = cs.domain
            record["sam_gov_confirmed"] = cs.sam_gov_confirmed
            record["usaspending_confirmed"] = cs.usaspending_confirmed
        records = [r for r, _ in entity_results]
        results["stage_counts"]["entity"] = len(records)
        logger.info("Entity resolution complete: %d records", len(records))

    # STAGE 2: Signal verification
    if "signal" in stages:
        logger.info("=== STAGE 2: Signal Verification ===")
        # Extract all signals from records, verify, reassign
        all_signals = []
        signal_index = {}  # signal_id → record_idx
        for i, record in enumerate(records):
            for sig in record.get("signals", []):
                sig["_record_idx"] = i
                all_signals.append(sig)

        if all_signals:
            verified_signals = verify_signals_batch(all_signals)
            # Clear existing signals on each record before reassigning verified versions
            for record in records:
                record["signals"] = []
            for sig in verified_signals:
                idx = sig.pop("_record_idx", None)
                if idx is not None:
                    records[idx]["signals"].append(sig)
            live_count = sum(1 for s in verified_signals
                             if s.get("verification", {}).get("status") == SignalStatus.LIVE)
            results["stage_counts"]["signals_verified"] = len(verified_signals)
            results["stage_counts"]["signals_live"] = live_count
            logger.info("Signal verification: %d/%d live", live_count, len(verified_signals))

    # STAGE 3: Contact verification
    if "contact" in stages:
        logger.info("=== STAGE 3: Contact Verification ===")
        for record in records:
            if record.get("email"):
                contact_result = verify_contact(record)
                record.update(contact_result)
        email_valid_count = sum(1 for r in records if r.get("email_valid", False))
        results["stage_counts"]["emails_valid"] = email_valid_count
        logger.info("Contact verification: %d/%d valid emails", email_valid_count, len(records))

    # STAGE 4: Content generation
    content_packages = {}
    if "content" in stages and content_type:
        logger.info("=== STAGE 4: Content Generation (%s) ===", content_type)
        for i, record in enumerate(records):
            # Skip HOLD records — don't waste tokens
            if record.get("confidence_route") == "HOLD":
                continue

            facts = build_facts_from_record(record)
            if not facts:
                logger.debug("No verified facts for %s — skipping content generation", record.get("company_name"))
                continue

            pkg = ContentPackage(
                content_type=content_type,
                company_name=record.get("company_name", ""),
                recipient_name=record.get("contact_first_name", ""),
                recipient_title=record.get("title", ""),
                sector=record.get("sector", ""),
            )
            pkg.facts = facts

            if not dry_run:
                pkg = generate_and_verify(pkg)
                record["content"] = pkg.generated_text
                record["qa_passed"] = pkg.qa_passed
                record["qa_flags"] = pkg.qa_flags
                record["generation_attempts"] = pkg.generation_attempts
            else:
                record["content"] = "[DRY RUN — content not generated]"
                record["qa_passed"] = True
                record["qa_flags"] = []

            content_packages[i] = pkg

        qa_passed = sum(1 for r in records if r.get("qa_passed", True))
        results["stage_counts"]["content_qa_passed"] = qa_passed
        logger.info("Content generation: %d/%d passed QA", qa_passed, len(records))

    # STAGE 5: Final routing
    if "route" in stages:
        logger.info("=== STAGE 5: Final Routing ===")
        for i, record in enumerate(records):
            # Build objects needed for routing
            cs = ConfidenceScore(
                company_name=record.get("company_name", ""),
                score=record.get("confidence_score", 50),
            )
            # Reconstruct route from score
            if cs.score >= 70:
                cs_route = Route.AUTO
            elif cs.score >= 40:
                cs_route = Route.REVIEW
            else:
                cs_route = Route.HOLD

            contact_result = {
                "email_valid": record.get("email_valid", False),
                "email_quality": record.get("email_quality", "unknown"),
                "email_domain_match": record.get("email_domain_match", True),
            }

            pkg = content_packages.get(i)
            final_route = route_record(record, cs, contact_result, pkg)
            record["final_route"] = final_route

            if final_route == "AUTO":
                results["auto"].append(record)
            elif final_route == "REVIEW":
                results["review"].append(record)
            else:
                results["hold"].append(record)

        logger.info(
            "Routing complete: AUTO=%d REVIEW=%d HOLD=%d",
            len(results["auto"]), len(results["review"]), len(results["hold"])
        )

    # Save results
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    verified_dir = Path(__file__).parent / "verified_output"
    verified_dir.mkdir(parents=True, exist_ok=True)
    if not dry_run:
        for route_name in ["auto", "review", "hold"]:
            route_records = results[route_name]
            if not route_records:
                continue
            if output_prefix:
                fname = verified_dir / f"{output_prefix}_{route_name}.csv"
            else:
                fname = OUTPUT_DIR / f"verified_{route_name}_{today}.csv"
            with open(fname, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=route_records[0].keys())
                writer.writeheader()
                writer.writerows(route_records)
            logger.info("Saved %s: %s", route_name.upper(), fname)

        # Save to Supabase review queue
        _save_review_queue(results["review"] + results["hold"])

    return results


def _save_review_queue(records: list[dict]) -> None:
    """Push records needing human review to Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY or not records:
        return
    batch = [
        {
            "company_name": r.get("company_name", ""),
            "domain": r.get("domain", ""),
            "sector": r.get("sector", ""),
            "state": r.get("state", ""),
            "confidence_score": r.get("confidence_score", 0),
            "final_route": r.get("final_route", "HOLD"),
            "flags": json.dumps(r.get("confidence_flags", []) + r.get("qa_flags", [])),
            "content_draft": r.get("content", ""),
            "reviewed": False,
            "reviewed_at": None,
        }
        for r in records
    ]
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/verification_review_queue?on_conflict=company_name,domain",
        headers=headers,
        json=batch,
        timeout=20,
    )
    if r.status_code not in (200, 201):
        logger.error("Failed to save review queue: %d %s", r.status_code, r.text[:200])
    else:
        logger.info("Saved %d records to review queue", len(batch))


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="ContractMotion verification pipeline")
    parser.add_argument("--input", required=True, help="CSV file of leads to verify")
    parser.add_argument("--content-type", choices=[
        "email_personalization", "physical_mail", "linkedin_post",
        "connection_request", "dm_message",
    ], help="Content type to generate (optional)")
    parser.add_argument("--stage", nargs="+",
                        choices=["entity", "signal", "contact", "content", "route"],
                        help="Stages to run (default: all)")
    parser.add_argument("--batch-size", type=int, default=50, help="Records per batch")
    parser.add_argument("--dry-run", action="store_true", help="Run all checks but don't send or save")
    parser.add_argument("--offset", type=int, default=0, help="Start from this row offset")
    parser.add_argument("--output-prefix", default="", help="Prefix for output CSV filenames (used by parallel runner)")
    args = parser.parse_args()

    # Load CSV
    with open(args.input, encoding="utf-8") as f:
        all_records = list(csv.DictReader(f))

    records = all_records[args.offset: args.offset + args.batch_size]
    logger.info("Loaded %d records from %s (offset=%d, batch=%d)",
                len(records), args.input, args.offset, args.batch_size)

    results = run_pipeline(
        records=records,
        content_type=args.content_type,
        stages=args.stage,
        dry_run=args.dry_run,
        output_prefix=args.output_prefix,
    )

    print(f"\n{'DRY RUN — ' if args.dry_run else ''}Pipeline complete.")
    print(f"  Total:  {results['total']}")
    print(f"  AUTO:   {len(results['auto'])} (ready to send)")
    print(f"  REVIEW: {len(results['review'])} (needs human check)")
    print(f"  HOLD:   {len(results['hold'])} (quarantined)")
    if results.get("stage_counts"):
        print(f"\n  Stage counts: {results['stage_counts']}")


if __name__ == "__main__":
    main()
