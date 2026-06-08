"""Refresh Gmail + Google Workspace OAuth tokens before expiration."""
from __future__ import annotations

import logging
import subprocess

logger = logging.getLogger(__name__)


def refresh_google_oauth_tokens() -> dict:
    """Best-effort token refresh across Google integrations."""
    results: dict = {"refreshed": [], "errors": []}

    try:
        r = subprocess.run(
            ["gws", "auth", "refresh"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if r.returncode == 0:
            results["refreshed"].append("gws")
        else:
            results["errors"].append(f"gws: {r.stderr.strip()[:200]}")
    except FileNotFoundError:
        results["errors"].append("gws CLI not installed")
    except Exception as e:
        results["errors"].append(f"gws: {e}")

    logger.info("[OAuthRefresh] %s", results)
    return results
