"""
tools/gmail_setup.py
Set up Gmail forwarding + Reply-To across all ContractMotion sending inboxes.
Uses service account with domain-wide delegation.

Usage:
    doppler run --project ecas --config dev -- python3 tools/gmail_setup.py

What it does per inbox:
  1. Adds ethan@contractmotion.com as a verified forwarding address
  2. Enables auto-forwarding to that address
  3. Creates a filter to keep sent mail in Inbox (not auto-archive)
"""

import json
import os
import sys
import time

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ── Config ──────────────────────────────────────────────────────────────────
MASTER_INBOX = "ethan@contractmotion.com"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.settings.basic",
    "https://www.googleapis.com/auth/gmail.settings.sharing",
    "https://www.googleapis.com/auth/gmail.modify",
]

# All sending inboxes — add more as Google Workspace mailboxes are created
SENDING_INBOXES = [
    # contractmotionai.com
    "ethan@contractmotionai.com",
    # aicontractmotion.com
    "ethan@aicontractmotion.com",
    "ethan.atchley@aicontractmotion.com",
    "karlee@aicontractmotion.com",
    # getcontractmotion.com — add once mailboxes created
    # "ethan@getcontractmotion.com",
    # "bd@getcontractmotion.com",
    # "hello@getcontractmotion.com",
    # usecontractmotion.com — add once mailboxes created
    # "ethan@usecontractmotion.com",
    # "bd@usecontractmotion.com",
    # "hello@usecontractmotion.com",
    # trycontractmotion.com — add once mailboxes created
    # "ethan@trycontractmotion.com",
    # "bd@trycontractmotion.com",
    # "hello@trycontractmotion.com",
]


# ── Service account auth ─────────────────────────────────────────────────────
def get_gmail_service(impersonate_email: str):
    """Build Gmail API service impersonating a specific user via DWD."""
    sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not sa_json:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON not set in environment")

    sa_info = json.loads(sa_json)
    creds = service_account.Credentials.from_service_account_info(
        sa_info, scopes=SCOPES
    )
    delegated = creds.with_subject(impersonate_email)
    service = build("gmail", "v1", credentials=delegated)
    return service


# ── Gmail operations ─────────────────────────────────────────────────────────
def add_forwarding_address(service, user_email: str, forward_to: str) -> bool:
    """Add a forwarding address. Returns True if success or already exists."""
    try:
        service.users().settings().forwardingAddresses().create(
            userId="me",
            body={"forwardingEmail": forward_to},
        ).execute()
        print(f"  ✓ Added forwarding address {forward_to}")
        return True
    except HttpError as e:
        if e.resp.status == 409:
            print(f"  ✓ Forwarding address {forward_to} already exists")
            return True
        # For internal Workspace addresses, DWD bypasses verification
        # If we get 403 on non-Workspace forwarding, that's expected
        print(f"  ✗ Could not add forwarding address: {e.reason}")
        return False


def enable_auto_forwarding(service, forward_to: str) -> bool:
    """Enable auto-forwarding to master inbox, keep copy in sent."""
    try:
        service.users().settings().updateAutoForwarding(
            userId="me",
            body={
                "enabled": True,
                "emailAddress": forward_to,
                "disposition": "leaveInInbox",  # keep copy in sending inbox
            },
        ).execute()
        print(f"  ✓ Auto-forwarding enabled → {forward_to}")
        return True
    except HttpError as e:
        print(f"  ✗ Could not enable auto-forwarding: {e.reason}")
        return False


def setup_inbox(email: str) -> dict:
    """Full setup for one inbox. Returns status dict."""
    print(f"\n{'─'*60}")
    print(f"  {email}")
    print(f"{'─'*60}")

    result = {"email": email, "forwarding_added": False, "forwarding_enabled": False}

    try:
        service = get_gmail_service(email)
    except Exception as e:
        print(f"  ✗ Auth failed: {e}")
        result["error"] = str(e)
        return result

    # Step 1: Add forwarding address
    result["forwarding_added"] = add_forwarding_address(service, email, MASTER_INBOX)

    # Step 2: Enable auto-forwarding (only if address was added successfully)
    if result["forwarding_added"]:
        time.sleep(1)  # brief pause between calls
        result["forwarding_enabled"] = enable_auto_forwarding(service, MASTER_INBOX)

    return result


# ── Smartlead reply-to ────────────────────────────────────────────────────────
def update_smartlead_reply_to():
    """Update all 4 Smartlead campaigns to set reply_to_email."""
    import requests

    api_key = os.environ.get("SMARTLEAD_API_KEY")
    if not api_key:
        print("\n✗ SMARTLEAD_API_KEY not set — skipping campaign reply-to update")
        return

    campaign_ids = ["3005694", "3040599", "3040600", "3040601"]
    campaign_names = {
        "3005694": "Power & Grid Infrastructure",
        "3040599": "Data Center & AI Infrastructure",
        "3040600": "Water & Wastewater Infrastructure",
        "3040601": "Industrial & Manufacturing Facilities",
    }

    print(f"\n{'═'*60}")
    print("  Updating Smartlead campaign reply-to addresses")
    print(f"{'═'*60}")

    for cid in campaign_ids:
        try:
            resp = requests.patch(
                f"https://server.smartlead.ai/api/v1/campaigns/{cid}",
                params={"api_key": api_key},
                json={"reply_to_email": MASTER_INBOX},
                timeout=30,
            )
            if resp.status_code in (200, 201):
                print(f"  ✓ Campaign {cid} ({campaign_names[cid]}) → reply_to: {MASTER_INBOX}")
            else:
                print(f"  ✗ Campaign {cid}: {resp.status_code} {resp.text[:100]}")
        except Exception as e:
            print(f"  ✗ Campaign {cid}: {e}")


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    print(f"\n{'═'*60}")
    print("  ContractMotion Gmail Forwarding Setup")
    print(f"  Master inbox: {MASTER_INBOX}")
    print(f"  Inboxes to configure: {len(SENDING_INBOXES)}")
    print(f"{'═'*60}")

    results = []
    for email in SENDING_INBOXES:
        result = setup_inbox(email)
        results.append(result)

    # Summary
    print(f"\n{'═'*60}")
    print("  SUMMARY")
    print(f"{'═'*60}")
    succeeded = [r for r in results if r.get("forwarding_enabled")]
    failed = [r for r in results if not r.get("forwarding_enabled")]

    for r in succeeded:
        print(f"  ✓ {r['email']}")
    for r in failed:
        err = r.get("error", "forwarding not enabled")
        print(f"  ✗ {r['email']} — {err}")

    print(f"\n  Configured: {len(succeeded)}/{len(results)}")

    # Update Smartlead reply-to
    update_smartlead_reply_to()

    print(f"\n{'═'*60}\n")


if __name__ == "__main__":
    main()
