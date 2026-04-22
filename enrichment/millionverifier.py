"""
enrichment/millionverifier.py
Email validation via MillionVerifier API.

Returns True for "good" emails, False for "bad".
"risky" emails (catch-all, unknown) are accepted by default — set
REJECT_RISKY=True via env var to tighten quality gates.
"""

import logging
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import MILLIONVERIFIER_API_KEY

logger = logging.getLogger(__name__)

REJECT_RISKY = os.environ.get("REJECT_RISKY", "false").lower() == "true"


def verify_email(email: str) -> tuple[bool, str]:
    """
    Validate an email address.

    Returns:
        (is_valid, quality) where quality is 'good', 'risky', or 'bad'
    """
    if not MILLIONVERIFIER_API_KEY:
        logger.debug("[MillionVerifier] No API key — passing email through as risky")
        return True, "risky"

    try:
        r = requests.get(
            "https://api.millionverifier.com/api/v3/",
            params={"api": MILLIONVERIFIER_API_KEY, "email": email},
            timeout=10,
        )
        if r.status_code != 200:
            logger.warning(f"[MillionVerifier] {r.status_code} for {email} — treating as risky")
            return True, "risky"

        data = r.json()
        quality = data.get("quality", "risky").lower()
        result_code = data.get("result", "")

        if quality == "good":
            return True, "good"
        if quality == "bad" or result_code in ("invalid", "disposable", "spamtrap"):
            return False, "bad"
        # risky / catch-all / unknown
        return not REJECT_RISKY, "risky"

    except Exception as e:
        logger.debug(f"[MillionVerifier] error for {email}: {e} — treating as risky")
        return True, "risky"


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    test_email = sys.argv[1] if len(sys.argv) > 1 else "test@example.com"
    valid, quality = verify_email(test_email)
    print(f"{test_email} → valid={valid}, quality={quality}")
