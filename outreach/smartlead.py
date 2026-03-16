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
from config import SMARTLEAD_API_KEY, SMARTLEAD_CAMPAIGN_ID, SECTOR_CAMPAIGN_MAP

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
            params={"api_key": SMARTLEAD_API_KEY},
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


def _resolve_campaign_id(sector: str, override: str = None) -> str:
    """
    Return the Smartlead campaign ID for a given sector.
    Priority: explicit override → SECTOR_CAMPAIGN_MAP → SMARTLEAD_CAMPAIGN_ID fallback.
    """
    if override:
        return override
    campaign = SECTOR_CAMPAIGN_MAP.get(sector)
    if campaign:
        return campaign
    # Partial match — e.g. "Power & Grid" hits "Power & Grid Infrastructure"
    sector_lower = sector.lower()
    for key, cid in SECTOR_CAMPAIGN_MAP.items():
        if sector_lower in key.lower() or key.lower() in sector_lower:
            return cid
    return SMARTLEAD_CAMPAIGN_ID  # fallback to default


def enroll_airtable_contacts(
    min_heat_score: float = 50.0,
    outreach_status: str = "pending_review",
    campaign_id: str = None,
    company_filter: str = None,
) -> dict:
    """
    Pull contacts from Airtable and enroll qualified ones in Smartlead.
    Routes each contact to the correct campaign based on their parent project's sector.
    Pass campaign_id to force a specific campaign (overrides sector routing).
    Pass company_filter to target a single company.
    """
    from storage.airtable import get_client
    at = get_client()

    # Build filter formula — optionally scope to a single company
    formula = f"{{outreach_status}}='{outreach_status}'"
    if company_filter:
        formula = f"AND({formula}, {{company_name}}='{company_filter}')"

    all_contacts = at._get("contacts", {
        "filterByFormula": formula,
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

        company = fields.get("company_name", "")
        heat = 0.0
        sector = "Power & Grid Infrastructure"  # default

        # Look up parent project for heat score + sector
        projects = at._get("projects", {
            "filterByFormula": f"{{owner_company}}='{company}'",
            "maxRecords": 1,
        })
        if projects:
            proj_fields = projects[0].get("fields", {})
            heat = float(proj_fields.get("confidence_score") or 0)
            sector = proj_fields.get("scope_summary") or sector
            if heat < min_heat_score:
                logger.debug(f"[Smartlead] {company} heat={heat} < {min_heat_score} — skipping")
                skipped += 1
                continue

        # Route to correct campaign based on sector
        target_campaign = _resolve_campaign_id(sector, override=campaign_id)
        logger.info(f"[Smartlead] {company} → sector='{sector}' → campaign {target_campaign}")

        result = enroll_lead(
            email=email,
            first_name=fields.get("first_name", ""),
            last_name=fields.get("last_name", ""),
            company=company,
            title=fields.get("title", ""),
            sector=sector,
            heat_score=heat,
            campaign_id=target_campaign,
        )

        if result["status"] == "enrolled":
            enrolled += 1
            at.update_contact_status(
                contact["id"],
                "in_sequence",
                notes=f"Enrolled in campaign {target_campaign} ({sector}) on {datetime.utcnow().date()}",
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


def create_campaign(name: str, from_name: str, from_email: str) -> str:
    """
    Create a new Smartlead campaign.
    Returns the campaign ID as a string.
    """
    if not SMARTLEAD_API_KEY:
        raise ValueError("SMARTLEAD_API_KEY not set")

    payload = {
        "name": name,
        "from_name": from_name,
        "from_email": from_email,
    }

    resp = requests.post(
        f"{SMARTLEAD_BASE_URL}/campaigns",
        params={"api_key": SMARTLEAD_API_KEY},
        headers=_headers(),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    campaign_id = data.get("id") or data.get("campaign_id")
    if not campaign_id:
        raise ValueError(f"Smartlead did not return a campaign ID: {data}")

    logger.info(f"[Smartlead] Created campaign '{name}' → ID {campaign_id}")
    return str(campaign_id)


def upload_sequence(campaign_id: str, emails: list[dict]) -> int:
    """
    Upload a list of email dicts to a Smartlead campaign sequence.

    Each email dict must have: day (int), subject (str), body (str)
    Returns the number of emails successfully uploaded.
    """
    if not SMARTLEAD_API_KEY:
        raise ValueError("SMARTLEAD_API_KEY not set")

    sequences = [
        {
            "seq_number": i + 1,
            "subject": email["subject"],
            "email_body": email["body"],
            "seq_delay_details": {
                "delay_in_days": email["day"],
                "delay_in_hours": 0,
                "delay_in_minutes": 0,
            },
        }
        for i, email in enumerate(emails)
    ]

    resp = requests.post(
        f"{SMARTLEAD_BASE_URL}/campaigns/{campaign_id}/sequences",
        params={"api_key": SMARTLEAD_API_KEY},
        headers=_headers(),
        json={"sequences": sequences},
        timeout=30,
    )
    resp.raise_for_status()

    logger.info(f"[Smartlead] Uploaded {len(sequences)} emails to campaign {campaign_id}")
    return len(sequences)
