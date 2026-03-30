#!/usr/bin/env python3
"""
Add seq 6 (break-up email) to Data Center, Water, and Industrial campaigns.
These were overwritten when seqs 1-5 were uploaded.
"""
import os
import warnings
warnings.filterwarnings("ignore")
import requests

API_KEY = os.environ.get("SMARTLEAD_API_KEY", "17a34ec2-b253-45a8-9f0c-707333b745ad_3eex9gg")
BASE_URL = "https://server.smartlead.ai/api/v1"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

SEQ6_BY_CAMPAIGN = {
    3040599: {
        "seq_number": 6,
        "seq_delay_details": {"delay_in_days": 30},
        "subject": "leaving this here for {{first_name}}",
        "email_body": """{{first_name}},

Not going to keep following up after this.

But I did pull the current hyperscale and commercial data center pipeline for your market. 11 active projects in permit or interconnection stages — 7 have not issued any public procurement notice yet.

Whenever timing makes sense for {{company_name}}, the offer stands.

— Ethan, ContractMotion

P.S. If someone else on your team handles BD or project development, happy to connect with them instead.""",
    },
    3040600: {
        "seq_number": 6,
        "seq_delay_details": {"delay_in_days": 30},
        "subject": "leaving this here for {{first_name}}",
        "email_body": """{{first_name}},

Not going to keep following up after this.

IIJA water funding is still flowing through state SRF programs — more funded-but-unprocured municipal infrastructure is in queue right now than most EPCs realize. We're tracking 34 approved CWSRF loans across the mid-Atlantic and Southeast that haven't issued a solicitation yet.

Whenever timing makes sense for {{company_name}}, the offer stands.

— Ethan, ContractMotion

P.S. If someone else on your team handles BD or project development, happy to connect with them instead.""",
    },
    3040601: {
        "seq_number": 6,
        "seq_delay_details": {"delay_in_days": 30},
        "subject": "leaving this here for {{first_name}}",
        "email_body": """{{first_name}},

Not going to keep following up after this.

The CHIPS Act and IRA manufacturing buildout is creating a multi-year runway of industrial EPC work — and most procurement decisions are being made before the bid packages are written. We're currently tracking 19 IRB filings and 8-K disclosures that haven't entered formal EPC procurement yet.

Whenever timing makes sense for {{company_name}}, the offer stands.

— Ethan, ContractMotion

P.S. If someone else on your team handles BD or project development, happy to connect with them instead.""",
    },
}

for campaign_id, seq in SEQ6_BY_CAMPAIGN.items():
    url = f"{BASE_URL}/campaigns/{campaign_id}/sequences?api_key={API_KEY}"
    resp = requests.post(url, headers=HEADERS, json={"sequences": [seq]}, timeout=30)
    result = resp.json()
    print(f"Campaign {campaign_id}: {result}")

# Verify all campaigns
print("\nVERIFICATION")
names = {3005694: "Power & Grid", 3040599: "Data Center", 3040600: "Water", 3040601: "Industrial", 3095136: "Defense"}
for cid in [3005694, 3040599, 3040600, 3040601, 3095136]:
    resp = requests.get(f"{BASE_URL}/campaigns/{cid}/sequences?api_key={API_KEY}", headers=HEADERS, timeout=30)
    seqs = resp.json()
    nums = sorted([s["seq_number"] for s in seqs])
    status = "COMPLETE" if len(seqs) == 6 else f"INCOMPLETE ({len(seqs)}/6)"
    print(f"  {names[cid]} ({cid}): {status} — seqs {nums}")
