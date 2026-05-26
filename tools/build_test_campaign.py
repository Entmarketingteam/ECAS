#!/usr/bin/env python3
"""
Build a DRAFTED Smartlead test campaign from a niche sequence JSON.

Reads a spec produced by the cold-email QA agents (campaigns_test/{niche}.json),
creates the campaign, uploads sequences, attaches the right warmed inbox pool,
sets schedule + settings — and leaves it DRAFTED. It does NOT send. Flipping to
START is a deliberate manual step in the Smartlead UI.

Inbox pools (domain-persona matched — see feedback_smartlead_domain_persona_match):
  contractmotion = the 5 ContractMotion alias domains (energy/contract-intel persona)
  ent            = the ENT Agency domains (neutral / general-agency persona)

Usage:
  doppler run --project ecas --config dev -- python3 tools/build_test_campaign.py \
      --json campaigns_test/osha.json --name "ENT — OSHA Compliance Test 2026" --pool ent
"""
import argparse
import json
import os
import sys

import requests

API_KEY = os.environ["SMARTLEAD_API_KEY"]
BASE_URL = "https://server.smartlead.ai/api/v1"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
}

POOL_DOMAINS = {
    "contractmotion": ("contractmotion.com", "aicontractmotion.com",
                       "getcontractmotion.com", "usecontractmotion.com",
                       "contractmotionai.com"),
    "ent": ("entagency.co", "ent-agency.com", "useentagency.com", "tryentagency.com"),
}

# M–F 09:00–18:00 America/Chicago — mirrors the live ContractMotion campaigns.
SCHEDULE = {
    "timezone": "America/Chicago", "days_of_the_week": [1, 2, 3, 4, 5],
    "start_hour": "09:00", "end_hour": "18:00",
    "min_time_btw_emails": 10, "max_new_leads_per_day": 80,
    "schedule_start_time": None,
}


def _pool_inbox_ids(pool: str) -> list[int]:
    domains = POOL_DOMAINS[pool]
    ids, off = [], 0
    while True:
        r = requests.get(f"{BASE_URL}/email-accounts/?api_key={API_KEY}"
                         f"&offset={off}&limit=100", headers=HEADERS, timeout=30).json()
        if not isinstance(r, list) or not r:
            break
        ids += [a["id"] for a in r
                if (a.get("from_email") or "").split("@")[-1] in domains]
        if len(r) < 100:
            break
        off += 100
    return ids


def build(json_path: str, name: str, pool: str) -> int:
    spec = json.load(open(json_path))
    # Whitelist only the keys the sequences endpoint accepts — QA agents sometimes
    # add A/B fields (subject_b, scorecards) that 400 the upload.
    seqs = [{"seq_number": s["seq_number"],
             "seq_delay_details": {"delay_in_days": s["seq_delay_details"]["delay_in_days"]},
             "subject": s["subject"], "email_body": s["email_body"]}
            for s in spec["sequences"]]

    # 1. create (DRAFTED — create accepts only `name`)
    r = requests.post(f"{BASE_URL}/campaigns/create?api_key={API_KEY}",
                      headers=HEADERS, json={"name": name}, timeout=30)
    r.raise_for_status()
    cid = r.json()["id"]
    print(f"created {cid} (DRAFTED) — {name}")

    # 2. sequences
    requests.post(f"{BASE_URL}/campaigns/{cid}/sequences?api_key={API_KEY}",
                  headers=HEADERS, json={"sequences": seqs}, timeout=30).raise_for_status()

    # 3. inboxes (persona-matched pool)
    inbox_ids = _pool_inbox_ids(pool)
    requests.post(f"{BASE_URL}/campaigns/{cid}/email-accounts?api_key={API_KEY}",
                  headers=HEADERS, json={"email_account_ids": inbox_ids},
                  timeout=30).raise_for_status()

    # 4. schedule + 5. settings
    requests.post(f"{BASE_URL}/campaigns/{cid}/schedule?api_key={API_KEY}",
                  headers=HEADERS, json=SCHEDULE, timeout=30).raise_for_status()
    requests.post(f"{BASE_URL}/campaigns/{cid}/settings?api_key={API_KEY}",
                  headers=HEADERS, json={"track_settings": [],
                  "stop_lead_settings": "REPLY_TO_AN_EMAIL",
                  "send_as_plain_text": False}, timeout=30).raise_for_status()

    print(f"  {len(seqs)} seqs · {len(inbox_ids)} {pool} inboxes · M-F 9-18 CT · DRAFTED")
    return cid


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--json", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--pool", required=True, choices=list(POOL_DOMAINS))
    a = p.parse_args()
    cid = build(a.json, a.name, a.pool)
    print(f"\nDONE. Campaign {cid} DRAFTED — does not send. Map sector → {cid} if routing.")
