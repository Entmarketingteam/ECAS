"""
enrichment/millionverifier.py
Email validation — Findymail first (key already in Doppler), MillionVerifier fallback.
Returns (is_valid: bool, quality: str) where quality is 'good', 'risky', or 'bad'.
"""

import logging
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import FINDYMAIL_API_KEY, MILLIONVERIFIER_API_KEY

logger = logging.getLogger(__name__)

FINDYMAIL_BASE = "https://app.findymail.com/api"
REJECT_RISKY = os.environ.get("REJECT_RISKY", "false").lower() == "true"


def _verify_findymail(email: str) -> tuple[bool, str] | None:
    if not FINDYMAIL_API_KEY:
        return None
    try:
        r = requests.post(
            f"{FINDYMAIL_BASE}/verify",
            headers={"Authorization": f"Bearer {FINDYMAIL_API_KEY}", "Content-Type": "application/json"},
            json={"email": email},
            timeout=15,
        )
        if r.status_code != 200:
            return None
        status = r.json().get("status", "unknown").lower()
        if status == "valid":
            return True, "good"
        if status in ("invalid", "disposable", "spamtrap"):
            return False, "bad"
        return not REJECT_RISKY, "risky"
    except Exception:
        return None


def _verify_millionverifier(email: str) -> tuple[bool, str] | None:
    if not MILLIONVERIFIER_API_KEY:
        return None
    try:
        r = requests.get(
            "https://api.millionverifier.com/api/v3/",
            params={"api": MILLIONVERIFIER_API_KEY, "email": email},
            timeout=10,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        quality = data.get("quality", "risky").lower()
        result_code = data.get("result", "")
        if quality == "good":
            return True, "good"
        if quality == "bad" or result_code in ("invalid", "disposable", "spamtrap"):
            return False, "bad"
        return not REJECT_RISKY, "risky"
    except Exception:
        return None


def verify_email(email: str) -> tuple[bool, str]:
    """
    Validate an email. Tries Findymail first (already in Doppler), then MillionVerifier.
    Returns (is_valid, quality) — quality is 'good', 'risky', or 'bad'.
    """
    result = _verify_findymail(email) or _verify_millionverifier(email)
    if result:
        return result
    logger.debug(f"[EmailVerify] No validator key set — passing {email} as risky")
    return True, "risky"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_email = sys.argv[1] if len(sys.argv) > 1 else "test@example.com"
    valid, quality = verify_email(test_email)
    print(f"{test_email} -> valid={valid}, quality={quality}")
