#!/usr/bin/env python3
"""
ContractMotion — Create Drone & Public Safety campaign in Smartlead
and upload all 6 sequences in one shot.

Run:
  doppler run --project ecas --config dev -- python3 create_dfr_campaign.py

After running, copy the printed campaign ID into config.py SECTOR_CAMPAIGN_MAP.
"""
import os
import json
import requests
import warnings
warnings.filterwarnings("ignore")

API_KEY = os.environ.get("SMARTLEAD_API_KEY", "17a34ec2-b253-45a8-9f0c-707333b745ad_3eex9gg")
BASE_URL = "https://server.smartlead.ai/api/v1"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
}


# ============================================================
# CAMPAIGN: Drone & Public Safety Technology — B2G Track
# Target: VP Sales / Dir BD / Head of Gov Sales at drone vendors
# (BRINC, Skydio, Percepto, Fotokite, Axon Air, Red Cat, etc.)
# Value prop: We tell you which municipalities are actively
# budgeting for DFR before the RFP drops.
# ============================================================

DFR_SEQUENCES = [
    {
        "seq_number": 1,
        "seq_delay_details": {"delay_in_days": 0},
        "subject": "34 agencies got COPS grants this quarter — none have issued RFPs",
        "email_body": """{{first_name}},

COPS Technology Program awards cleared for 34 agencies in Q1. Most are tagged for public safety technology — drones, sensors, aerial systems. The spend-down window is 24 months, which means procurement conversations are opening right now.

None of the 34 has issued a public solicitation yet.

That gap — between grant funded and RFP published — is where vendor evaluation actually happens. By the time a formal solicitation drops, an agency has usually already had 2–3 conversations with their shortlist. The RFP is procurement compliance, not discovery.

We built ContractMotion to map that gap for drone vendor sales teams. SAM.gov UAS notices, FEMA/COPS grant awards, FAA BVLOS applications, city council DFR resolutions — all indexed daily, all mapped to active evaluation windows.

Worth 20 minutes to show you what's active in {{company}}'s target geography right now?

Ethan
ContractMotion""",
    },
    {
        "seq_number": 2,
        "seq_delay_details": {"delay_in_days": 4},
        "subject": "the honest reason DFR deals get decided before you call",
        "email_body": """{{first_name}},

Here's how most municipal DFR evaluations actually play out.

A police chief gets a COPS grant or a city council approves a DFR resolution. The next week, a department head googles "drone as first responder" and reaches out to 2–3 vendors they've already heard of — from a conference, a peer agency recommendation, or a LinkedIn post. Those vendors get demos in the door.

By the time the agency posts an RFP or a SAM.gov notice, the evaluation is already half over. The RFP is written around the vendors who showed up during the evaluation window.

If {{company}}'s pipeline starts at the SAM.gov notice, you're entering after the evaluation framework is set.

The signal that matters isn't the RFP. It's the COPS grant award, the BVLOS waiver application, the city council agenda item. Those precede the RFP by 60–180 days.

We monitor all of them.

Happy to show you what's in the pre-evaluation window for your target states. 20 minutes?

Ethan
ContractMotion""",
    },
    {
        "seq_number": 3,
        "seq_delay_details": {"delay_in_days": 9},
        "subject": "the NDAA displacement list is bigger than most teams realize",
        "email_body": """{{first_name}},

Section 848 of the NDAA prohibits federal funds from being used to procure DJI and Autel drones. As of Q1 2026, 23 states have passed additional state-level bans or restrictions.

That means there are roughly 1,400 agencies with expiring DJI contracts or active compliance mandates who need to re-procure — and the replacement timeline is compressed because they can't renew.

USASpending shows DJI contract expirations by agency, by date. We map those expirations 90 days out, cross-reference with agencies that have active public safety technology budgets, and flag the replacement-ready pipeline.

Most of these agencies aren't issuing formal RFPs. They're calling vendors they already have a relationship with, or reaching out to peer agencies for recommendations. The vendor who reaches them first — with a credible product and a reference agency nearby — wins the evaluation.

We can pull the active NDAA displacement pipeline for {{company}}'s target geography in about 20 minutes on a call.

Ethan
ContractMotion""",
    },
    {
        "seq_number": 4,
        "seq_delay_details": {"delay_in_days": 15},
        "subject": "5 agencies in active evaluation, within 30 days — or it's free",
        "email_body": """{{first_name}},

ContractMotion guarantees 5 agencies in an active DFR evaluation window in {{company}}'s target geography within 30 days of onboarding — or we continue at no charge until we hit it.

That guarantee exists because the signals are specific and measurable. A BVLOS waiver application is a public FAA filing — it means an agency has committed to a DFR program. A COPS Technology grant award is a USASpending record — it means budget is unlocked and spend-down has started. A city council DFR resolution is a public meeting minute — it means executive buy-in exists.

These aren't intent signals. They're commitment signals. An agency that has filed a BVLOS waiver and received a COPS grant is not browsing. They're buying.

We only work with 2 vendors per category per region — so the intelligence stays exclusive and you're not competing with 5 other vendors who have the same list.

If {{company}} sells into municipal public safety, worth a call to check geography availability.

Ethan
ContractMotion""",
    },
    {
        "seq_number": 5,
        "seq_delay_details": {"delay_in_days": 22},
        "subject": "ShotSpotter renewal = DFR evaluation in 90 days (every time)",
        "email_body": """{{first_name}},

One pattern we've noticed consistently: when a municipality renews or expands their ShotSpotter contract, a DFR evaluation follows within 60–90 days.

The logic is operational — ShotSpotter detects a gunshot, dispatch sends a unit, the chief wants the drone airborne before the unit arrives. Once an agency is committed to gunshot detection, the aerial first responder conversation is inevitable. The RTCC becomes the coordination layer and the DFR fills the response gap.

SoundThinking (ShotSpotter) publishes their municipal contract awards. We monitor those awards alongside Motorola RTCC expansions and 911 center modernization grants — because every RTCC upgrade is a DFR integration conversation waiting to happen.

There are 11 ShotSpotter contract renewals in the past 60 days that haven't been followed by a DFR solicitation yet.

If {{company}} wants to know which agencies those are, happy to pull the list on a call.

Ethan
ContractMotion""",
    },
    {
        "seq_number": 6,
        "seq_delay_details": {"delay_in_days": 30},
        "subject": "closing this out",
        "email_body": """{{first_name}},

Not going to keep following up after this.

I'll leave one thing behind: the municipal DFR market is moving faster than most vendor pipeline teams realize. BVLOS waivers are getting processed in under 60 days now. COPS grants are clearing faster than any previous cycle. And NDAA compliance pressure is forcing replacement decisions that agencies were planning to defer.

The agencies buying right now are not the ones posting formal RFPs. They're the ones that got funded last quarter and are calling vendors this quarter.

Whenever the timing is right for {{company}}, the offer stands.

Ethan
ContractMotion

P.S. If someone else on your team runs government sales or BD, happy to connect with them instead.""",
    },
]


def create_campaign():
    """Create the Drone & Public Safety campaign in Smartlead."""
    url = f"{BASE_URL}/campaigns/create?api_key={API_KEY}"
    payload = {
        "name": "ContractMotion — Drone & Public Safety Technology 2026",
        "client_id": None,
        "min_time_btw_emails": 10,
        "max_leads_per_day": 40,
        "stop_lead_settings": "REPLY_TO_AN_EMAIL",
        "track_settings": ["DONT_TRACK_EMAIL_OPEN", "DONT_TRACK_LINK_CLICK"],
    }
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    campaign_id = data.get("id")
    print(f"Campaign created: {campaign_id}")
    print(f"Full response: {json.dumps(data, indent=2)}")
    return campaign_id


def upload_sequences(campaign_id):
    """Upload all 6 sequences to the campaign."""
    url = f"{BASE_URL}/campaigns/{campaign_id}/sequences?api_key={API_KEY}"
    resp = requests.post(
        url, headers=HEADERS,
        json={"sequences": DFR_SEQUENCES},
        timeout=30
    )
    resp.raise_for_status()
    result = resp.json()
    print(f"\nSequences uploaded: {json.dumps(result, indent=2)}")
    return result


def verify_sequences(campaign_id):
    """Confirm all 6 sequences are live."""
    url = f"{BASE_URL}/campaigns/{campaign_id}/sequences?api_key={API_KEY}"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    seqs = resp.json()
    print(f"\nVerification — {len(seqs)}/6 sequences live:")
    for s in sorted(seqs, key=lambda x: x["seq_number"]):
        delay = s.get("seq_delay_details", {}).get("delay_in_days", "?")
        print(f"  seq {s['seq_number']} (day {delay}): {s['subject']}")
    return len(seqs) == 6


if __name__ == "__main__":
    print("=" * 60)
    print("ContractMotion — Drone & DFR Campaign Setup")
    print("=" * 60)

    # Step 1: Create campaign
    print("\n[1/3] Creating Smartlead campaign...")
    campaign_id = create_campaign()

    if not campaign_id:
        print("ERROR: No campaign ID returned. Check API key and response above.")
        exit(1)

    # Step 2: Upload sequences
    print(f"\n[2/3] Uploading 6 sequences to campaign {campaign_id}...")
    upload_sequences(campaign_id)

    # Step 3: Verify
    print(f"\n[3/3] Verifying...")
    ok = verify_sequences(campaign_id)

    print("\n" + "=" * 60)
    if ok:
        print(f"DONE. Campaign ID: {campaign_id}")
        print(f"\nNext step: add to config.py SECTOR_CAMPAIGN_MAP:")
        print(f'    "Drone & Public Safety Technology": "{campaign_id}",')
    else:
        print("WARNING: Sequence count mismatch. Check Smartlead UI.")
    print("=" * 60)
