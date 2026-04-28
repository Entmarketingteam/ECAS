"""
verification/confidence.py — Confidence scoring and routing decisions.

Every company record and every piece of content gets a score before anything
goes out. Below threshold = quarantine. Uncertain = human review queue.

Score components:
  Company identity (max 55 pts)
    +25  Domain verified via primary source (official website matches company name)
    +15  Found in SAM.gov active registrations (federal contractor, vetted)
    +15  Found in USASpending as contract recipient (actually won work)

  Contact quality (max 30 pts)
    +15  Email verified valid by Findymail/MillionVerifier
    +10  LinkedIn profile confirmed (title + company match)
    +5   Direct dial or mobile found

  Signal data (max 15 pts)
    +10  Signal source URL still live and returns expected data
    +5   Signal age < 90 days

  Deductions
    -20  Similar company name found in list (possible identity confusion)
    -15  Domain mismatch (website doesn't match company name we scraped)
    -10  Email address domain doesn't match company domain
    -10  Signal source returns 404 or changed content
    -5   Company has generic name (Inc, LLC, Services — high collision risk)

Routing thresholds:
  AUTO   >= 70  — ready to send, no human review needed
  REVIEW 40-69  — send to human review queue with flags
  HOLD   < 40   — quarantine, do not use until resolved
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Route(str, Enum):
    AUTO = "AUTO"
    REVIEW = "REVIEW"
    HOLD = "HOLD"


@dataclass
class ConfidenceScore:
    company_name: str
    domain: str = ""
    score: int = 0
    flags: list[str] = field(default_factory=list)
    checks_passed: list[str] = field(default_factory=list)
    checks_failed: list[str] = field(default_factory=list)

    # Component scores
    domain_verified: bool = False
    sam_gov_confirmed: bool = False
    usaspending_confirmed: bool = False
    email_valid: bool = False
    linkedin_confirmed: bool = False
    signal_live: bool = False

    # Deduction triggers
    similar_name_found: bool = False
    domain_mismatch: bool = False
    email_domain_mismatch: bool = False
    signal_dead: bool = False
    generic_name: bool = False

    def compute(self) -> int:
        s = 0

        if self.domain_verified:
            s += 25
            self.checks_passed.append("domain_verified")
        if self.sam_gov_confirmed:
            s += 15
            self.checks_passed.append("sam_gov_confirmed")
        if self.usaspending_confirmed:
            s += 15
            self.checks_passed.append("usaspending_confirmed")
        if self.email_valid:
            s += 15
            self.checks_passed.append("email_valid")
        if self.linkedin_confirmed:
            s += 10
            self.checks_passed.append("linkedin_confirmed")
        if self.signal_live:
            s += 10
            self.checks_passed.append("signal_live")

        if self.similar_name_found:
            s -= 20
            self.flags.append("SIMILAR_NAME: possible identity confusion with another company in list")
        if self.domain_mismatch:
            s -= 15
            self.flags.append("DOMAIN_MISMATCH: website homepage doesn't match expected company name")
        if self.email_domain_mismatch:
            s -= 10
            self.flags.append("EMAIL_DOMAIN_MISMATCH: contact email domain differs from company domain")
        if self.signal_dead:
            s -= 10
            self.flags.append("SIGNAL_DEAD: source URL no longer returns expected data")
        if self.generic_name:
            s -= 5
            self.flags.append("GENERIC_NAME: company name is common, collision risk")

        self.score = max(0, s)
        return self.score

    @property
    def route(self) -> Route:
        if self.score >= 70:
            return Route.AUTO
        if self.score >= 40:
            return Route.REVIEW
        return Route.HOLD

    def to_dict(self) -> dict:
        return {
            "company_name": self.company_name,
            "domain": self.domain,
            "score": self.score,
            "route": self.route.value,
            "flags": self.flags,
            "checks_passed": self.checks_passed,
        }


GENERIC_NAME_FRAGMENTS = {
    "solutions", "services", "group", "partners", "associates", "technologies",
    "systems", "international", "management", "consulting", "enterprises",
    "holdings", "resources", "industries",
}


def has_generic_name(company_name: str) -> bool:
    words = set(company_name.lower().split())
    return bool(words & GENERIC_NAME_FRAGMENTS) and len(company_name.split()) <= 2


def levenshtein(a: str, b: str) -> int:
    a, b = a.lower(), b.lower()
    if len(a) < len(b):
        a, b = b, a
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (ca != cb)))
        prev = curr
    return prev[-1]


def find_similar_names(target: str, all_names: list[str], threshold: int = 4) -> list[str]:
    """Return company names within edit distance `threshold` of target."""
    return [
        n for n in all_names
        if n != target and levenshtein(target, n) <= threshold
    ]
