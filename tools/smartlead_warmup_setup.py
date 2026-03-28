#!/usr/bin/env python3
"""
tools/smartlead_warmup_setup.py

Adds all ContractMotion sending inboxes to Smartlead and enables warmup.

Prerequisites:
  1. Generate app passwords for each inbox (Google Account → Security → App passwords)
  2. Store in Doppler (ecas project):
       doppler secrets set INBOX_ETHAN_CONTRACTMOTIONAI_PASS="xxxx xxxx xxxx xxxx"
       doppler secrets set INBOX_ETHAN_AICONTRACTMOTION_PASS="xxxx xxxx xxxx xxxx"
       doppler secrets set INBOX_ETHAN_ATCHLEY_AICONTRACTMOTION_PASS="xxxx xxxx xxxx xxxx"
       doppler secrets set INBOX_KARLEE_AICONTRACTMOTION_PASS="xxxx xxxx xxxx xxxx"
  3. Run:
       doppler run --project ecas --config dev -- python3 tools/smartlead_warmup_setup.py

DNS status:
  aicontractmotion.com     → MX ✅ SPF ✅ DKIM ✅ DMARC ✅  (fully ready)
  contractmotionai.com     → MX ✅ SPF ❌ DKIM ✅ DMARC ✅  (add SPF before sending)
  getcontractmotion.com    → ❌ not set up yet
  trycontractmotion.com    → ❌ not set up yet
  usecontractmotion.com    → ❌ not set up yet
"""

import os
import sys
import time
import requests

SMARTLEAD_API_KEY = os.environ.get("SMARTLEAD_API_KEY", "")
if not SMARTLEAD_API_KEY:
    print("ERROR: SMARTLEAD_API_KEY not set")
    sys.exit(1)

BASE_URL = "https://server.smartlead.ai/api/v1"

# Each entry: (from_email, from_name, doppler_env_var)
INBOXES = [
    # aicontractmotion.com — DNS fully ready ✅
    ("ethan@aicontractmotion.com",          "Ethan Atchley",    "INBOX_ETHAN_AICONTRACTMOTION_PASS"),
    ("ethan.atchley@aicontractmotion.com",  "Ethan Atchley",    "INBOX_ETHAN_ATCHLEY_AICONTRACTMOTION_PASS"),
    ("karlee@aicontractmotion.com",         "Karlee",           "INBOX_KARLEE_AICONTRACTMOTION_PASS"),
    # contractmotionai.com — SPF missing, add before sending (warmup ok without it)
    ("ethan@contractmotionai.com",          "Ethan Atchley",    "INBOX_ETHAN_CONTRACTMOTIONAI_PASS"),
]

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993

# Week 1 warmup: 2 emails/day per inbox (scale up weekly)
WARMUP_EMAILS_PER_DAY = 2
WARMUP_REPLY_RATE = 20  # % of warmup emails to reply to


def add_email_account(from_email: str, from_name: str, password: str):
    """Add an SMTP email account to Smartlead."""
    payload = {
        "from_name": from_name,
        "from_email": from_email,
        "user_name": from_email,
        "password": password,
        "smtp_host": SMTP_HOST,
        "smtp_port": SMTP_PORT,
        "smtp_port_type": "TLS",
        "imap_username": from_email,
        "imap_password": password,
        "imap_host": IMAP_HOST,
        "imap_port": IMAP_PORT,
        "imap_port_type": "SSL",
        "message_per_day": WARMUP_EMAILS_PER_DAY,
    }
    resp = requests.post(
        f"{BASE_URL}/email-accounts/save",
        params={"api_key": SMARTLEAD_API_KEY},
        json=payload,
        timeout=30,
    )
    if resp.status_code in (200, 201):
        data = resp.json()
        return data
    else:
        print(f"    ✗ Add failed: {resp.status_code} {resp.text[:200]}")
        return None


def enable_warmup(account_id):
    """Enable Smartlead warmup for an email account."""
    payload = {
        "warmup_enabled": True,
        "total_warmup_per_day": WARMUP_EMAILS_PER_DAY,
        "daily_rampup": 1,  # add 1 email/day each day
        "reply_rate_percent": WARMUP_REPLY_RATE,
    }
    resp = requests.post(
        f"{BASE_URL}/email-accounts/{account_id}/warmup",
        params={"api_key": SMARTLEAD_API_KEY},
        json=payload,
        timeout=30,
    )
    if resp.status_code in (200, 201):
        return True
    else:
        print(f"    ✗ Warmup enable failed: {resp.status_code} {resp.text[:200]}")
        return False


def get_existing_accounts() -> set:
    """Return set of emails already in Smartlead."""
    resp = requests.get(
        f"{BASE_URL}/email-accounts",
        params={"api_key": SMARTLEAD_API_KEY, "limit": 100, "offset": 0},
        timeout=30,
    )
    if resp.status_code == 200:
        data = resp.json()
        accs = data if isinstance(data, list) else data.get("email_accounts", [])
        return {a["from_email"] for a in accs}
    return set()


def main():
    print("\n" + "═" * 60)
    print("  ContractMotion Smartlead Warmup Setup")
    print("  Week 1: 2 emails/day, ramp +1/day, 20% reply rate")
    print("═" * 60)

    existing = get_existing_accounts()
    print(f"\n  {len(existing)} accounts already in Smartlead\n")

    results = []
    for from_email, from_name, env_var in INBOXES:
        print(f"{'─'*60}")
        print(f"  {from_email}")

        if from_email in existing:
            print(f"  ✓ Already in Smartlead — skipping add")
            results.append((from_email, True, "already exists"))
            continue

        password = os.environ.get(env_var, "").strip()
        if not password:
            print(f"  ✗ Missing: {env_var} not set in Doppler — skipping")
            results.append((from_email, False, f"missing {env_var}"))
            continue

        # Add account
        account = add_email_account(from_email, from_name, password)
        if not account:
            results.append((from_email, False, "add failed"))
            continue

        account_id = account.get("id") or account.get("email_account_id")
        if not account_id:
            print(f"    ✗ Could not find account ID in response: {account}")
            results.append((from_email, False, "no account ID"))
            continue

        print(f"  ✓ Added (id: {account_id})")
        time.sleep(1)

        # Enable warmup
        ok = enable_warmup(account_id)
        if ok:
            print(f"  ✓ Warmup enabled ({WARMUP_EMAILS_PER_DAY}/day, ramp +1/day)")
            results.append((from_email, True, f"added + warmup enabled"))
        else:
            results.append((from_email, False, "added but warmup failed"))

        time.sleep(1)

    # Summary
    print(f"\n{'═'*60}")
    print("  SUMMARY")
    print(f"{'═'*60}")
    for email, ok, note in results:
        icon = "✓" if ok else "✗"
        print(f"  {icon} {email} — {note}")

    ready = sum(1 for _, ok, _ in results if ok)
    print(f"\n  Warmup active: {ready}/{len(INBOXES)} inboxes")
    if ready > 0:
        print(f"\n  Warmup timeline:")
        print(f"    Week 1-2:  2–5 emails/day/inbox (auto-warmup only)")
        print(f"    Week 3:    10/day — begin soft launch")
        print(f"    Day 21 (~2026-04-06): full campaign launch at 20–30/day")
        print(f"\n  Monitor: app.smartlead.ai → Email Accounts → Warmup tab")
    print(f"{'═'*60}\n")


if __name__ == "__main__":
    main()
