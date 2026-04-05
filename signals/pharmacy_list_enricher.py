#!/usr/bin/env python3
"""
pharmacy_list_enricher.py

Enriches a raw contact list (Apollo export or state board CSV) with verified
email addresses via Findymail, with a Hunter.io fallback for contacts that
lack a company domain.

Pipeline:
  1. Load input CSV (stdin or --input flag)
  2. Normalize + deduplicate on email, phone, and company+name
  3. Filter out chain pharmacies
  4. Resolve company domain (extract from Apollo email or Hunter domain search)
  5. Call Findymail email enrichment (5 concurrent workers)
  6. Write enriched CSV with standardized columns
  7. Print stats summary

Usage:
  python pharmacy_list_enricher.py --input apollo-TX-2026-04-05.csv
  cat merged-pharmacy-list.csv | python pharmacy_list_enricher.py

Output:
  enriched_<input_filename>.csv  (or enriched_output.csv for stdin)

Required env vars (pull via Doppler before running):
  FINDYMAIL_API_KEY
  HUNTER_API_KEY  (fallback only — used when no domain available)
"""

import argparse
import csv
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

import requests
from rapidfuzz import fuzz

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

FINDYMAIL_URL = "https://app.findymail.com/api/search/name"
HUNTER_DOMAIN_URL = "https://api.hunter.io/v2/domain-search"

CONCURRENCY = 5          # Findymail concurrent workers
RATE_LIMIT_DELAY = 0.2   # seconds between batches (conservative)
FUZZY_DEDUP_THRESHOLD = 85  # company+name match score to call a duplicate

# Chain pharmacies to exclude — applied to company name (case-insensitive)
CHAIN_EXCLUDE = [
    "walgreens", "cvs", "walmart", "rite aid", "kroger", "costco",
    "target", "albertsons", "safeway", "publix", "heb", "meijer",
    "winn-dixie", "giant", "harris teeter", "fred meyer", "duane reade",
    "express scripts", "optumrx", "caremark", "humana pharmacy",
    "kaiser", "va pharmacy", "veterans affairs", "hospital pharmacy",
    "health system", "medical center", "medical group",
]

# Output column order
OUTPUT_COLUMNS = [
    "first_name", "last_name", "email", "email_confidence",
    "phone", "company", "title", "address", "city", "state", "zip",
    "source",
]

# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def get_api_keys() -> tuple[str, str]:
    """Pull API keys from environment (set by Doppler or export)."""
    findymail_key = os.environ.get("FINDYMAIL_API_KEY", "")
    hunter_key = os.environ.get("HUNTER_API_KEY", "")
    if not findymail_key:
        print("ERROR: FINDYMAIL_API_KEY not set. Run with doppler run -- python pharmacy_list_enricher.py", file=sys.stderr)
        sys.exit(1)
    return findymail_key, hunter_key


def extract_domain_from_email(email: str) -> Optional[str]:
    """Pull the domain from an existing email address."""
    if email and "@" in email:
        return email.split("@", 1)[1].strip().lower()
    return None


def hunter_domain_search(company_name: str, api_key: str) -> Optional[str]:
    """
    Use Hunter.io to find the company's domain from its name.
    Returns domain string or None if not found.
    """
    if not api_key:
        return None
    try:
        resp = requests.get(
            HUNTER_DOMAIN_URL,
            params={"company": company_name, "api_key": api_key},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        domain = data.get("data", {}).get("domain")
        return domain if domain else None
    except Exception:
        return None


def findymail_enrich(
    first_name: str,
    last_name: str,
    domain: str,
    api_key: str,
) -> tuple[Optional[str], Optional[float]]:
    """
    Call Findymail to find a verified email for a person at a domain.

    Returns:
        (email, confidence_score) or (None, None) if not found
    """
    name = f"{first_name} {last_name}".strip()
    if not name or not domain:
        return None, None

    try:
        resp = requests.post(
            FINDYMAIL_URL,
            json={"name": name, "domain": domain},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15,
        )
        if resp.status_code == 404:
            return None, None
        resp.raise_for_status()
        data = resp.json()
        email = data.get("email") or data.get("data", {}).get("email")
        confidence = data.get("confidence") or data.get("data", {}).get("confidence")
        return email, float(confidence) if confidence is not None else None
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code in (429, 503):
            # Rate limited — back off and retry once
            time.sleep(2)
            return findymail_enrich(first_name, last_name, domain, api_key)
        return None, None
    except Exception:
        return None, None


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

def normalize_phone(phone: str) -> str:
    """Strip all non-digits and return 10-digit US phone number."""
    digits = re.sub(r"\D", "", str(phone or ""))
    if digits.startswith("1") and len(digits) == 11:
        digits = digits[1:]
    return digits if len(digits) == 10 else ""


def normalize_company(name: str) -> str:
    """
    Strip common suffixes and noise words for fuzzy matching.
    Returns lowercase normalized string.
    """
    name = str(name or "").lower()
    # Remove punctuation
    name = re.sub(r"[^\w\s]", " ", name)
    # Remove common pharmacy suffixes
    noise = [
        "pharmacy", "pharmacies", "rx", "compounding", "llc", "inc",
        "corp", "ltd", "co", "the", "and", "&", "sterile", "solutions",
        "services", "group", "partners",
    ]
    words = name.split()
    words = [w for w in words if w not in noise]
    return " ".join(words).strip()


def normalize_name(first: str, last: str) -> str:
    """Return normalized full name for dedup key."""
    return f"{str(first or '').strip().lower()} {str(last or '').strip().lower()}".strip()


def is_chain_pharmacy(company: str) -> bool:
    """Return True if company name matches any chain pharmacy pattern."""
    company_lower = str(company or "").lower()
    return any(chain in company_lower for chain in CHAIN_EXCLUDE)


# ---------------------------------------------------------------------------
# Column mapping — Apollo + state board field name variants
# ---------------------------------------------------------------------------

# Maps our canonical field names → list of possible CSV header names (in priority order)
FIELD_MAP = {
    "first_name":   ["first_name", "first name", "firstname", "pic_first", "contact_first"],
    "last_name":    ["last_name", "last name", "lastname", "pic_last", "contact_last"],
    "email":        ["email", "email_address", "work_email", "contact_email"],
    "phone":        ["phone", "phone_number", "direct_phone", "work_phone", "company_phone"],
    "company":      ["company", "company_name", "organization", "business_name", "pharmacy_name"],
    "title":        ["title", "job_title", "position", "role"],
    "address":      ["address", "street_address", "address_1", "company_address"],
    "city":         ["city", "company_city"],
    "state":        ["state", "company_state", "province"],
    "zip":          ["zip", "postal_code", "zip_code", "company_zip"],
    "source":       ["source", "list_source", "data_source"],
    # Extra fields present in Apollo exports (not in output but used for domain extraction)
    "linkedin_url": ["linkedin_url", "linkedin", "person_linkedin_url"],
}


def resolve_field(row: dict, canonical: str, headers_lower: dict) -> str:
    """
    Resolve a canonical field name to the actual value in the row,
    trying each variant in FIELD_MAP until one is found.

    headers_lower: {lowercase_header: original_header}
    """
    for variant in FIELD_MAP.get(canonical, [canonical]):
        if variant in headers_lower:
            return str(row.get(headers_lower[variant], "") or "").strip()
    return ""


def build_headers_lower(fieldnames: list) -> dict:
    """Build a {lowercase: original} map for CSV header lookup."""
    return {h.lower().strip(): h for h in fieldnames}


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

class Deduplicator:
    """
    Tracks seen contacts and identifies duplicates based on:
      1. Exact email match
      2. Exact normalized phone match
      3. Fuzzy company + exact name match (85% threshold)
    """

    def __init__(self):
        self.seen_emails: set[str] = set()
        self.seen_phones: set[str] = set()
        # (normalized_company, normalized_name) -> True
        self.seen_company_names: list[tuple[str, str]] = []

    def is_duplicate(self, email: str, phone: str, company: str, first: str, last: str) -> bool:
        # 1. Email exact match
        clean_email = (email or "").strip().lower()
        if clean_email and clean_email in self.seen_emails:
            return True

        # 2. Phone exact match
        clean_phone = normalize_phone(phone)
        if clean_phone and clean_phone in self.seen_phones:
            return True

        # 3. Fuzzy company + name match
        norm_company = normalize_company(company)
        norm_name = normalize_name(first, last)
        if norm_company and norm_name:
            for seen_company, seen_name in self.seen_company_names:
                company_score = fuzz.token_sort_ratio(norm_company, seen_company)
                if company_score >= FUZZY_DEDUP_THRESHOLD and norm_name == seen_name:
                    return True

        return False

    def mark_seen(self, email: str, phone: str, company: str, first: str, last: str):
        clean_email = (email or "").strip().lower()
        if clean_email:
            self.seen_emails.add(clean_email)

        clean_phone = normalize_phone(phone)
        if clean_phone:
            self.seen_phones.add(clean_phone)

        norm_company = normalize_company(company)
        norm_name = normalize_name(first, last)
        if norm_company and norm_name:
            self.seen_company_names.append((norm_company, norm_name))


# ---------------------------------------------------------------------------
# Enrichment worker
# ---------------------------------------------------------------------------

def enrich_contact(
    contact: dict,
    findymail_key: str,
    hunter_key: str,
) -> dict:
    """
    Resolve domain and call Findymail for a single contact.
    Mutates and returns the contact dict with email + email_confidence populated.
    """
    # Skip enrichment if already has a high-confidence email
    existing_email = contact.get("email", "")
    if existing_email and "@" in existing_email:
        contact.setdefault("email_confidence", "pre-existing")
        return contact

    first = contact.get("first_name", "")
    last = contact.get("last_name", "")
    company = contact.get("company", "")

    # Step 1: Try to get domain from existing email field (Apollo guessed emails)
    domain = extract_domain_from_email(existing_email)

    # Step 2: Hunter.io fallback to find domain by company name
    if not domain and company:
        domain = hunter_domain_search(company, hunter_key)

    # Step 3: Call Findymail if we have a domain
    if domain and first:
        email, confidence = findymail_enrich(first, last, domain, findymail_key)
        if email:
            contact["email"] = email
            contact["email_confidence"] = str(confidence) if confidence is not None else "found"
        else:
            contact["email_confidence"] = "not_found"
    else:
        contact["email_confidence"] = "no_domain"

    return contact


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def load_csv(source) -> tuple[list[dict], list[str]]:
    """Load CSV from file object. Returns (rows, fieldnames)."""
    reader = csv.DictReader(source)
    fieldnames = reader.fieldnames or []
    rows = list(reader)
    return rows, fieldnames


def normalize_row(row: dict, headers_lower: dict) -> dict:
    """Map raw CSV row to canonical output fields."""
    return {
        "first_name":        resolve_field(row, "first_name", headers_lower),
        "last_name":         resolve_field(row, "last_name", headers_lower),
        "email":             resolve_field(row, "email", headers_lower),
        "email_confidence":  "",
        "phone":             normalize_phone(resolve_field(row, "phone", headers_lower)),
        "company":           resolve_field(row, "company", headers_lower),
        "title":             resolve_field(row, "title", headers_lower),
        "address":           resolve_field(row, "address", headers_lower),
        "city":              resolve_field(row, "city", headers_lower),
        "state":             resolve_field(row, "state", headers_lower),
        "zip":               resolve_field(row, "zip", headers_lower),
        "source":            resolve_field(row, "source", headers_lower) or "unknown",
    }


def run_enrichment_pipeline(contacts: list[dict], findymail_key: str, hunter_key: str) -> list[dict]:
    """Run Findymail enrichment concurrently across all contacts."""
    enriched = []
    total = len(contacts)

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        futures = {
            executor.submit(enrich_contact, contact, findymail_key, hunter_key): i
            for i, contact in enumerate(contacts)
        }

        completed = 0
        for future in as_completed(futures):
            result = future.result()
            enriched.append(result)
            completed += 1

            if completed % 25 == 0:
                pct = (completed / total) * 100
                print(f"  Enrichment progress: {completed}/{total} ({pct:.0f}%)", file=sys.stderr)

            # Light rate limiting
            if completed % CONCURRENCY == 0:
                time.sleep(RATE_LIMIT_DELAY)

    return enriched


def write_output(contacts: list[dict], output_path: str):
    """Write enriched contacts to CSV."""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(contacts)


def print_stats(total_input: int, after_chain_filter: int, after_dedup: int, emails_found: int, ready: int):
    print("\n" + "=" * 50)
    print("ENRICHMENT STATS")
    print("=" * 50)
    print(f"  Total input records:        {total_input}")
    print(f"  After chain filter:         {after_chain_filter}  (-{total_input - after_chain_filter} removed)")
    print(f"  After dedup:                {after_dedup}  (-{after_chain_filter - after_dedup} dupes removed)")
    print(f"  Emails found (new):         {emails_found}")
    print(f"  Ready-to-load count:        {ready}  (has first name + company + email)")
    print("=" * 50 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Enrich pharmacy contact list with email via Findymail + Hunter fallback."
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        default=None,
        help="Path to input CSV file. Reads from stdin if not provided.",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Path to output CSV. Defaults to enriched_<input>.csv or enriched_output.csv for stdin.",
    )
    args = parser.parse_args()

    # Resolve output path
    if args.output:
        output_path = args.output
    elif args.input:
        base = os.path.basename(args.input).replace(".csv", "")
        output_path = os.path.join(os.path.dirname(args.input) or ".", f"enriched_{base}.csv")
    else:
        output_path = "enriched_output.csv"

    # Load API keys
    findymail_key, hunter_key = get_api_keys()
    if not hunter_key:
        print("WARNING: HUNTER_API_KEY not set — domain fallback disabled", file=sys.stderr)

    # Load input
    print("Loading input...", file=sys.stderr)
    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            raw_rows, fieldnames = load_csv(f)
    else:
        raw_rows, fieldnames = load_csv(sys.stdin)

    total_input = len(raw_rows)
    print(f"  Loaded {total_input} records", file=sys.stderr)

    # Build header lookup map
    headers_lower = build_headers_lower(fieldnames)

    # Normalize all rows to canonical fields
    contacts = [normalize_row(row, headers_lower) for row in raw_rows]

    # Filter out chain pharmacies
    contacts = [c for c in contacts if not is_chain_pharmacy(c["company"])]
    after_chain_filter = len(contacts)
    print(f"  After chain filter: {after_chain_filter}", file=sys.stderr)

    # Deduplicate
    deduplicator = Deduplicator()
    deduped = []
    for contact in contacts:
        if not deduplicator.is_duplicate(
            contact["email"], contact["phone"],
            contact["company"], contact["first_name"], contact["last_name"]
        ):
            deduplicator.mark_seen(
                contact["email"], contact["phone"],
                contact["company"], contact["first_name"], contact["last_name"]
            )
            deduped.append(contact)

    after_dedup = len(deduped)
    print(f"  After dedup: {after_dedup}", file=sys.stderr)

    # Enrichment
    print(f"\nRunning Findymail enrichment ({CONCURRENCY} workers)...", file=sys.stderr)
    enriched = run_enrichment_pipeline(deduped, findymail_key, hunter_key)

    # Count new emails found
    emails_found = sum(
        1 for c in enriched
        if c.get("email_confidence") not in ("pre-existing", "not_found", "no_domain", "")
        and c.get("email")
    )

    # Ready-to-load: must have first_name + company + email
    ready = sum(
        1 for c in enriched
        if c.get("first_name") and c.get("company") and c.get("email")
    )

    # Write output
    write_output(enriched, output_path)
    print(f"\nOutput written to: {output_path}", file=sys.stderr)

    # Stats summary
    print_stats(total_input, after_chain_filter, after_dedup, emails_found, ready)


if __name__ == "__main__":
    main()
