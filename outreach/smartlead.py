"""
outreach/smartlead.py
Enrolls qualified contacts into Smartlead email campaigns.
Checks for existing enrollment before adding to avoid duplicates.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import SMARTLEAD_API_KEY, SMARTLEAD_CAMPAIGN_ID

logger = logging.getLogger(__name__)

SMARTLEAD_BASE_URL = "https://server.smartlead.ai/api/v1"


def _headers() -> dict:
    return {
        "Content-Type": "application/json",
    }


def get_campaign_leads(campaign_id: str = None) -> list[dict]:
    """Fetch all leads in a campaign to check for existing enrollment."""
    cid = campaign_id or SMARTLEAD_CAMPAIGN_ID
    if not SMARTLEAD_API_KEY or not cid:
        return []

    try:
        resp = requests.get(
            f"{SMARTLEAD_BASE_URL}/campaigns/{cid}/leads",
            params={"api_key": SMARTLEAD_API_KEY, "limit": 1000, "offset": 0},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", data if isinstance(data, list) else [])
    except Exception as e:
        logger.error(f"[Smartlead] Error fetching campaign leads: {e}")
        return []


def is_enrolled(email: str, campaign_id: str = None) -> bool:
    """Check if an email is already enrolled in the campaign."""
    leads = get_campaign_leads(campaign_id)
    email_lower = email.lower().strip()
    return any(
        lead.get("email", "").lower().strip() == email_lower
        for lead in leads
    )


def enroll_lead(
    email: str,
    first_name: str,
    last_name: str,
    company: str,
    title: str,
    sector: str = "Power & Grid Infrastructure",
    heat_score: float = 0.0,
    campaign_id: str = None,
) -> dict:
    """
    Add a single lead to Smartlead campaign.
    Returns result dict with status.
    """
    cid = campaign_id or SMARTLEAD_CAMPAIGN_ID
    if not SMARTLEAD_API_KEY:
        return {"status": "error", "reason": "SMARTLEAD_API_KEY not set"}
    if not cid:
        return {"status": "error", "reason": "SMARTLEAD_CAMPAIGN_ID not set"}

    # Check for existing enrollment
    if is_enrolled(email, cid):
        logger.info(f"[Smartlead] {email} already enrolled — skipping")
        return {"status": "skipped", "reason": "already_enrolled", "email": email}

    payload = {
        "lead_list": [
            {
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "company_name": company,
                "phone_number": "",
                "custom_fields": {
                    "title": title,
                    "sector": sector,
                    "heat_score": str(round(heat_score, 1)),
                    "enrolled_at": datetime.utcnow().strftime("%Y-%m-%d"),
                },
            }
        ]
    }

    try:
        resp = requests.post(
            f"{SMARTLEAD_BASE_URL}/campaigns/{cid}/leads",
            params={"api_key": SMARTLEAD_API_KEY},
            headers=_headers(),
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        logger.info(f"[Smartlead] Enrolled {email} at {company}")
        return {"status": "enrolled", "email": email, "response": data}

    except requests.HTTPError as e:
        logger.error(f"[Smartlead] HTTP error enrolling {email}: {e.response.text}")
        return {"status": "error", "reason": str(e), "email": email}
    except Exception as e:
        logger.error(f"[Smartlead] Error enrolling {email}: {e}")
        return {"status": "error", "reason": str(e), "email": email}


def enroll_airtable_contacts(
    min_heat_score: float = 50.0,
    outreach_status: str = "not_contacted",
    campaign_id: str = None,
) -> dict:
    """
    Pull contacts from Airtable and enroll qualified ones in Smartlead.
    Only enrolls contacts whose company has heat_score >= min_heat_score.
    """
    from storage.airtable import get_client
    at = get_client()

    # Get contacts not yet in outreach
    all_contacts = at._get("contacts", {
        "filterByFormula": f"{{outreach_status}}='{outreach_status}'",
        "maxRecords": 100,
    })

    enrolled = 0
    skipped = 0
    errors = 0

    for contact in all_contacts:
        fields = contact.get("fields", {})
        email = fields.get("email", "")
        if not email:
            continue

        # Get parent company heat score
        company = fields.get("company", "")
        projects = at._get("projects", {
            "filterByFormula": f"{{company_name}}='{company}'",
            "maxRecords": 1,
        })
        if projects:
            heat = projects[0].get("fields", {}).get("heat_score", 0)
            if heat < min_heat_score:
                logger.debug(f"[Smartlead] {company} heat={heat} < {min_heat_score} — skipping")
                skipped += 1
                continue

        result = enroll_lead(
            email=email,
            first_name=fields.get("first_name", ""),
            last_name=fields.get("last_name", ""),
            company=company,
            title=fields.get("title", ""),
            heat_score=heat if projects else 0.0,
            campaign_id=campaign_id,
        )

        if result["status"] == "enrolled":
            enrolled += 1
            # Update Airtable contact status
            at.update_contact_status(
                contact["id"],
                "enrolled",
                notes=f"Enrolled in Smartlead {datetime.utcnow().date()}",
            )
        elif result["status"] == "skipped":
            skipped += 1
        else:
            errors += 1

    logger.info(
        f"[Smartlead] Enrolled: {enrolled} | Skipped: {skipped} | Errors: {errors}"
    )
    return {
        "enrolled": enrolled,
        "skipped": skipped,
        "errors": errors,
        "total_processed": len(all_contacts),
    }


def get_campaign_stats(campaign_id: str = None) -> dict:
    """Fetch campaign performance stats from Smartlead."""
    cid = campaign_id or SMARTLEAD_CAMPAIGN_ID
    if not SMARTLEAD_API_KEY or not cid:
        return {}

    try:
        resp = requests.get(
            f"{SMARTLEAD_BASE_URL}/campaigns/{cid}/analytics",
            params={"api_key": SMARTLEAD_API_KEY},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"[Smartlead] Error fetching stats: {e}")
        return {}


if __name__ == "__main__":
    import json
    import logging
    logging.basicConfig(level=logging.INFO)
    stats = get_campaign_stats()
    print(json.dumps(stats, indent=2))
