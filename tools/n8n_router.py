import json
import urllib.request
from config import N8N_ROUTER_WEBHOOK_URL, DISCORD_ALERTS_WEBHOOK_URL

def route_lead_to_n8n(lead_payload: dict, webhook_url: str = N8N_ROUTER_WEBHOOK_URL) -> bool:
    """POST fully verified and resolved lead to n8n router for visual campaign routing."""
    if not webhook_url:
        print("[Warning] No N8N_ROUTER_WEBHOOK_URL specified. Lead bypassed routing.")
        return False
        
    req = urllib.request.Request(
        webhook_url,
        data=json.dumps(lead_payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.getcode()
            if status in [200, 201]:
                return True
            print(f"[Warning] n8n webhook returned status code {status}")
            return False
    except Exception as e:
        print(f"[Error] Failed to POST lead to n8n: {e}")
        # Trigger real-time alert for process fail
        send_discord_alert(f"⚠️ *CRITICAL ROUTING ERROR*: Failed to POST lead {lead_payload.get('email')} to n8n. Exception: {e}")
        return False

def send_discord_alert(message: str, webhook_url: str = DISCORD_ALERTS_WEBHOOK_URL) -> bool:
    """Send real-time webhook alert to Emily & Ethan on Slack/Discord."""
    if not webhook_url:
        print(f"[Bypassed Alert]: {message}")
        return False
        
    payload = {
        "content": message,
        "username": "ECAS Pipeline Sentinel",
        "avatar_url": "https://img.icons8.com/color/96/shield.png"
    }
    
    req = urllib.request.Request(
        webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.getcode() in [200, 204]
    except Exception as e:
        print(f"[Error] Failed to send webhook alert: {e}")
        return False

def build_pending_review_fields(lead_data: dict, reason: str) -> dict:
    """Build Airtable contact fields for manual review without Smartlead enrollment."""
    notes = [
        f"Review reason: {reason}",
        f"Sector: {lead_data.get('sector') or 'Unknown'}",
    ]
    if lead_data.get("verification_status"):
        notes.append(f"Verification: {lead_data.get('verification_status')} via {lead_data.get('source') or 'unknown'}")
    if lead_data.get("domain"):
        notes.append(f"Domain: {lead_data.get('domain')}")

    return {
        "first_name": lead_data.get("first_name"),
        "last_name": lead_data.get("last_name"),
        "email": lead_data.get("email"),
        "company_name": lead_data.get("company_name"),
        "title": lead_data.get("title"),
        "linkedin_url": lead_data.get("linkedin_url"),
        "outreach_status": "pending_review",
        "analyst_notes": "\n".join(notes),
    }


def _post_contact_to_airtable(fields: dict, airtable_key: str, base_id: str) -> bool:
    url = f"https://api.airtable.com/v0/{base_id}/tblPBvTBuhwlS8AnS"
    payload = {"fields": {k: v for k, v in fields.items() if v is not None}}
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {airtable_key}",
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.getcode() == 200


def sync_pending_review_to_airtable(lead_data: dict, reason: str, airtable_key: str, base_id: str) -> bool:
    """Queue a verified lead for human approval before any Smartlead enrollment."""
    try:
        return _post_contact_to_airtable(build_pending_review_fields(lead_data, reason), airtable_key, base_id)
    except Exception as e:
        print(f"[Error] Failed to queue pending-review record in Airtable: {e}")
        return False


def sync_dead_letter_queue_to_airtable(lead_data: dict, error_msg: str, airtable_key: str, base_id: str) -> bool:
    """Log processing/verification failures into Airtable DLQ (Manual Mode)."""
    fields = build_pending_review_fields(lead_data, f"DLQ Error: {error_msg}")
    fields["title"] = lead_data.get("title") or f"[DLQ Error: {error_msg}]"
    try:
        return _post_contact_to_airtable(fields, airtable_key, base_id)
    except Exception as e:
        print(f"[Error] Failed to log DLQ record to Airtable: {e}")
        return False
