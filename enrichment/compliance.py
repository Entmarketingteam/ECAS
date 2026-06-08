"""Drop EU/CA contacts before Smartlead enrollment unless explicit opt-in."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

RESTRICTED_COUNTRIES = {
    "germany", "france", "netherlands", "belgium", "italy", "spain",
    "portugal", "austria", "sweden", "denmark", "finland", "norway",
    "ireland", "poland", "czech republic", "greece", "hungary",
    "united kingdom", "uk", "gb",
    "canada", "ca",
}


def filter_contacts_for_compliance(
    contacts: list[dict],
) -> tuple[list[dict], list[dict]]:
    """Split contacts into (ok_to_enroll, dropped_for_compliance)."""
    ok: list[dict] = []
    dropped: list[dict] = []
    for c in contacts:
        country = (c.get("country") or "").strip().lower()
        if country in RESTRICTED_COUNTRIES and not c.get("optin_verified"):
            dropped.append({**c, "compliance_reason": f"Restricted country: {country}"})
            continue
        ok.append(c)
    if dropped:
        logger.info("[Compliance] Dropped %d/%d contacts for region rules",
                    len(dropped), len(contacts))
    return ok, dropped
