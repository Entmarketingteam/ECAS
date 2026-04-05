"""
enrichment/retry.py
Universal retry engine with error classification, exponential backoff, and circuit breaker.
All API calls in the pipeline go through retry_with_fallback().

Design decisions (from architecture review 2026-04-05):
- Classifies errors by HTTP status code, NOT custom exception types
  (existing code raises raw requests exceptions — wrapping would require refactoring every caller)
- No Doppler CLI calls (not installed on Railway container)
- Credential refresh = alert-only (key rotation requires redeploy)
"""

import logging
import time
from functools import wraps

import requests

logger = logging.getLogger(__name__)


# ── Error Classification ─────────────────────────────────────────────────────

def classify_error(error: Exception) -> str:
    """
    Classify any exception into a retry strategy.
    Inspects HTTP status codes directly — no custom exception types needed.
    """
    # Extract status code from requests exceptions
    status = None
    if isinstance(error, requests.HTTPError) and error.response is not None:
        status = error.response.status_code
    elif hasattr(error, "response") and hasattr(error.response, "status_code"):
        status = error.response.status_code

    error_str = str(error).lower()

    # Rate limiting
    if status == 429 or "rate limit" in error_str or "too many requests" in error_str:
        return "rate_limit"

    # Auth / credentials
    if status in (401, 403) or "unauthorized" in error_str or "forbidden" in error_str:
        return "auth"

    # Payment / credits exhausted
    if status == 402 or "payment required" in error_str:
        return "credits_exhausted"

    # Server errors (transient)
    if status in (500, 502, 503, 504):
        return "transient"

    # Timeout
    if isinstance(error, (requests.Timeout, TimeoutError)):
        return "timeout"

    # Connection errors
    if isinstance(error, (requests.ConnectionError, ConnectionError)):
        return "connection"

    # Client errors (permanent — don't retry)
    if status and 400 <= status < 500:
        return "permanent"

    return "unknown"


def _get_retry_after(error: Exception) -> int | None:
    """Extract Retry-After header from rate limit responses."""
    if isinstance(error, requests.HTTPError) and error.response is not None:
        retry_after = error.response.headers.get("Retry-After")
        if retry_after:
            try:
                return int(retry_after)
            except ValueError:
                pass
    return None


# ── Circuit Breaker ──────────────────────────────────────────────────────────

class CircuitBreaker:
    """
    Tracks consecutive failures per service.
    Opens circuit (blocks calls) after threshold failures.
    Auto-resets after cooldown period (half-open → allow one attempt).
    """

    def __init__(self, threshold: int = 5, cooldown_seconds: int = 300):
        self.threshold = threshold
        self.cooldown = cooldown_seconds
        self._failures: dict[str, int] = {}
        self._opened_at: dict[str, float] = {}

    def is_open(self, category: str) -> bool:
        if category not in self._opened_at:
            return False
        elapsed = time.time() - self._opened_at[category]
        if elapsed > self.cooldown:
            # Half-open: allow one attempt
            del self._opened_at[category]
            self._failures[category] = 0
            logger.info(f"[CircuitBreaker] {category} half-open — allowing retry")
            return False
        return True

    def record_success(self, category: str) -> None:
        self._failures[category] = 0
        if category in self._opened_at:
            del self._opened_at[category]
            logger.info(f"[CircuitBreaker] {category} closed — recovered")

    def record_failure(self, category: str) -> None:
        self._failures[category] = self._failures.get(category, 0) + 1
        if self._failures[category] >= self.threshold:
            self._opened_at[category] = time.time()
            logger.error(
                f"[CircuitBreaker] {category} OPEN after {self.threshold} consecutive failures. "
                f"Cooldown: {self.cooldown}s"
            )

    def status(self) -> dict:
        """Return current state for health checks / diagnostics."""
        return {
            cat: {
                "failures": self._failures.get(cat, 0),
                "open": cat in self._opened_at,
                "cooldown_remaining": max(0, self.cooldown - (time.time() - self._opened_at.get(cat, 0)))
                if cat in self._opened_at else 0,
            }
            for cat in set(list(self._failures.keys()) + list(self._opened_at.keys()))
        }


# ── Retry Engine ─────────────────────────────────────────────────────────────

class CircuitBreakerOpen(Exception):
    """Raised when a circuit breaker is open and blocking calls."""
    pass


def retry_with_fallback(
    primary: callable,
    fallback: callable = None,
    retries: int = 3,
    backoff: int = 2,
    max_backoff: int = 60,
    category: str = "unknown",
    circuit_breaker: CircuitBreaker = None,
) -> any:
    """
    Universal retry wrapper for all API calls in the pipeline.

    Strategy per error type:
      rate_limit  → wait Retry-After (or exponential), retry
      auth        → log + alert (can't auto-fix on Railway), don't retry
      credits     → log + alert, don't retry
      transient   → exponential backoff, retry
      timeout     → retry with same backoff
      connection  → retry with backoff
      permanent   → don't retry
      unknown     → retry once, then give up
    """
    if circuit_breaker and circuit_breaker.is_open(category):
        raise CircuitBreakerOpen(f"{category} circuit breaker is open — skipping")

    last_error = None
    auto_fix_log = []

    for attempt in range(retries + 1):
        try:
            result = primary()
            if circuit_breaker:
                circuit_breaker.record_success(category)
            return result

        except Exception as e:
            last_error = e
            error_type = classify_error(e)

            if error_type == "rate_limit":
                retry_after = _get_retry_after(e)
                wait = retry_after or min(backoff ** (attempt + 1), max_backoff)
                auto_fix_log.append(f"Rate limited. Waiting {wait}s (attempt {attempt + 1})")
                logger.warning(f"[{category}] Rate limited. Waiting {wait}s (attempt {attempt + 1}/{retries + 1})")
                time.sleep(wait)
                continue

            elif error_type == "auth":
                auto_fix_log.append(f"Auth failed (401/403). Cannot auto-fix on Railway — requires redeploy with new key.")
                logger.error(f"[{category}] Auth failed: {e}. Key rotation requires redeploy.")
                break  # Don't retry auth failures

            elif error_type == "credits_exhausted":
                auto_fix_log.append(f"Credits exhausted (402). Cannot auto-fix — needs account top-up.")
                logger.error(f"[{category}] Credits exhausted: {e}")
                break

            elif error_type in ("transient", "timeout", "connection"):
                wait = min(backoff ** (attempt + 1), max_backoff)
                auto_fix_log.append(f"{error_type} error. Backoff {wait}s (attempt {attempt + 1})")
                logger.warning(f"[{category}] {error_type}: {e}. Backoff {wait}s (attempt {attempt + 1}/{retries + 1})")
                time.sleep(wait)
                continue

            elif error_type == "permanent":
                auto_fix_log.append(f"Permanent error ({e}). Not retrying.")
                logger.error(f"[{category}] Permanent error: {e}")
                break

            else:  # unknown
                if attempt == 0:
                    auto_fix_log.append(f"Unknown error. Retrying once.")
                    logger.warning(f"[{category}] Unknown error: {e}. Retrying once.")
                    time.sleep(backoff)
                    continue
                else:
                    auto_fix_log.append(f"Unknown error persists after retry.")
                    break

    # All retries exhausted — try fallback
    if fallback:
        try:
            auto_fix_log.append("Primary exhausted. Trying fallback.")
            logger.info(f"[{category}] Primary exhausted. Trying fallback.")
            result = fallback()
            if circuit_breaker:
                circuit_breaker.record_success(category)
            return result
        except Exception as fb_error:
            auto_fix_log.append(f"Fallback also failed: {fb_error}")
            last_error = fb_error

    # Record failure for circuit breaker
    if circuit_breaker:
        circuit_breaker.record_failure(category)

    # Attach auto-fix log to the error for diagnosis
    if last_error:
        last_error.auto_fix_log = auto_fix_log
    raise last_error
