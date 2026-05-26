#!/usr/bin/env python3
"""
ContractMotion — Create General EPC / Commercial Construction campaign in
Smartlead and upload the sequence in one shot.

These are broad commercial + federal general contractors (DPR, Haskell, Kiewit,
Primoris, BNBuilders) that surface in USASpending award data — i.e. they win
construction contracts but don't fit one of the 5 infra sectors. Copy is the
horizontal "win your next contract" thesis (matches the /commercial-trades morph),
generic enough to land across the General EPC bucket.

Created DRAFTED (per repo convention — never /start without human approval).

Run:
  doppler run --project ecas --config dev -- python3 create_commercial_epc_campaign.py

After running, copy the printed campaign ID into:
  - config.py                       → SECTOR_CAMPAIGN_MAP["General EPC"]
  - enroll_contacts_to_campaigns.py → SECTOR_TO_CAMPAIGN["General EPC"]
"""
import os
import json
import requests
import warnings

warnings.filterwarnings("ignore")

API_KEY = os.environ["SMARTLEAD_API_KEY"]
BASE_URL = "https://server.smartlead.ai/api/v1"
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
}

# Mirror inboxes + schedule from this live sibling campaign so the new one shares
# the same ContractMotion sending pool and cadence (Industrial & Manufacturing).
REFERENCE_CAMPAIGN_ID = 3040601


# ============================================================
# CAMPAIGN: General EPC / Commercial Construction
# Target: BD / preconstruction / owner at commercial + federal GCs
# Value prop: see the next project form before it hits the bid board.
# ============================================================

EPC_SEQUENCES = [
    {
        "seq_number": 1,
        "seq_delay_details": {"delay_in_days": 0},
        "subject": "{{company}} won the work — who's tracking the next one?",
        "email_body": """{{first_name}},

{{company}} shows up in federal and commercial award data, which means you're winning projects. The question that decides next year's backlog is what's forming behind the ones you already booked.

The GCs that stay booked aren't bidding harder. They're seeing the project take shape before it hits the bid board — when the owner is still picking a shortlist, not collecting three quotes for procurement compliance.

ContractMotion indexes USASpending awards, SAM.gov notices, and large commercial permit filings daily, and maps them to projects entering procurement in your lane.

Worth 20 minutes to show what's forming in {{company}}'s market right now?

Ethan
ContractMotion""",
    },
    {
        "seq_number": 2,
        "seq_delay_details": {"delay_in_days": 4},
        "subject": "the bid board is where you're already #4",
        "email_body": """{{first_name}},

Here's the uncomfortable part of how commercial and federal construction actually gets awarded.

By the time a project hits a public bid board or a SAM.gov solicitation, the owner has usually already had conversations with the GCs they're seriously considering. The formal bid is procurement requiring three quotes — not the moment the decision gets made.

If {{company}}'s pipeline starts at the solicitation, you're entering after the shortlist is set.

The signals that matter come earlier: the permit pulled on the facility, the capex disclosed in a 10-Q, the federal award that funds the next phase. Those precede the RFP by 60–180 days.

We monitor all of them and run the outreach that puts you in the conversation before procurement opens.

Happy to show you what's in the pre-RFP window for your markets. 20 minutes?

Ethan
ContractMotion""",
    },
    {
        "seq_number": 3,
        "seq_delay_details": {"delay_in_days": 9},
        "subject": "5 projects forming in your market in 30 days — or it's free",
        "email_body": """{{first_name}},

ContractMotion guarantees 5 commercial or federal projects in active formation in {{company}}'s service area within 30 days of onboarding — or we keep working at no charge until we hit it.

The guarantee holds because the signals are public and measurable. A large commercial building permit is a county filing. A USASpending award is a federal record. A REIT or hospital-system capex disclosure is in the 10-Q. None of these are intent guesses — they're commitment signals from owners who are funded and moving.

We work with a limited number of GCs per market so the intelligence stays exclusive and you're not chasing the same projects as five other firms with the same list.

If {{company}} wants to see what's available in your geography, worth a call to check.

Ethan
ContractMotion""",
    },
    {
        "seq_number": 4,
        "seq_delay_details": {"delay_in_days": 15},
        "subject": "closing this out",
        "email_body": """{{first_name}},

Not going to keep following up after this.

One thing to leave behind: the GCs winning consistently right now aren't the ones working the bid boards harder. They're the ones who saw the project forming a quarter earlier and were already in the owner's conversation when the shortlist got drawn.

That window is the whole game, and it's measurable if you're watching the right signals.

Whenever the timing is right for {{company}}, the offer stands.

Ethan
ContractMotion

P.S. If someone else runs preconstruction or business development, happy to connect with them instead.""",
    },
]


def create_campaign():
    """Create the General EPC / Commercial Construction campaign (DRAFTED).

    Create only accepts `name`; throttle/tracking settings are set at activation
    time (UI), alongside attaching inboxes + schedule.
    """
    url = f"{BASE_URL}/campaigns/create?api_key={API_KEY}"
    payload = {"name": "ContractMotion — General EPC / Commercial Construction 2026"}
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    campaign_id = data.get("id")
    print(f"Campaign created (DRAFTED): {campaign_id}")
    return campaign_id


def upload_sequences(campaign_id):
    """Upload the sequence to the campaign."""
    url = f"{BASE_URL}/campaigns/{campaign_id}/sequences?api_key={API_KEY}"
    resp = requests.post(
        url, headers=HEADERS, json={"sequences": EPC_SEQUENCES}, timeout=30
    )
    resp.raise_for_status()
    print(f"Sequences uploaded: {json.dumps(resp.json(), indent=2)}")


def verify_sequences(campaign_id):
    """Confirm all 4 sequences are live."""
    url = f"{BASE_URL}/campaigns/{campaign_id}/sequences?api_key={API_KEY}"
    seqs = requests.get(url, headers=HEADERS, timeout=30).json()
    print(f"\nVerification — {len(seqs)}/4 sequences live:")
    for s in sorted(seqs, key=lambda x: x["seq_number"]):
        delay = s.get("seq_delay_details", {}).get("delayInDays", "?")
        print(f"  seq {s['seq_number']} (day {delay}): {s['subject']}")
    return len(seqs) == len(EPC_SEQUENCES)


def provision_campaign(campaign_id):
    """Attach inboxes + schedule + settings mirrored from the reference campaign.

    Leaves the campaign DRAFTED — it does NOT send. Flipping to START is a
    deliberate manual step in the Smartlead UI.
    """
    ref = f"{BASE_URL}/campaigns/{REFERENCE_CAMPAIGN_ID}"
    inbox_ids = [a["id"] for a in
                 requests.get(f"{ref}/email-accounts?api_key={API_KEY}",
                              headers=HEADERS, timeout=30).json()]
    cron = requests.get(f"{ref}?api_key={API_KEY}", headers=HEADERS,
                        timeout=30).json()["scheduler_cron_value"]

    base = f"{BASE_URL}/campaigns/{campaign_id}"
    requests.post(f"{base}/email-accounts?api_key={API_KEY}", headers=HEADERS,
                  json={"email_account_ids": inbox_ids}, timeout=30).raise_for_status()
    requests.post(f"{base}/schedule?api_key={API_KEY}", headers=HEADERS, json={
        "timezone": cron["tz"], "days_of_the_week": cron["days"],
        "start_hour": cron["startHour"], "end_hour": cron["endHour"],
        "min_time_btw_emails": 10, "max_new_leads_per_day": 80,
        "schedule_start_time": None,
    }, timeout=30).raise_for_status()
    requests.post(f"{base}/settings?api_key={API_KEY}", headers=HEADERS, json={
        "track_settings": [], "stop_lead_settings": "REPLY_TO_AN_EMAIL",
        "send_as_plain_text": False,
    }, timeout=30).raise_for_status()
    print(f"Provisioned: {len(inbox_ids)} inboxes, schedule "
          f"{cron['days']} {cron['startHour']}–{cron['endHour']} {cron['tz']}")


if __name__ == "__main__":
    print("=" * 60)
    print("ContractMotion — General EPC / Commercial Construction Setup")
    print("=" * 60)

    print("\n[1/4] Creating Smartlead campaign (DRAFTED)...")
    campaign_id = create_campaign()
    if not campaign_id:
        print("ERROR: No campaign ID returned. Check API key and response above.")
        exit(1)

    print(f"\n[2/4] Uploading {len(EPC_SEQUENCES)} sequences to campaign {campaign_id}...")
    upload_sequences(campaign_id)

    print(f"\n[3/4] Provisioning inboxes + schedule + settings...")
    provision_campaign(campaign_id)

    print(f"\n[4/4] Verifying...")
    ok = verify_sequences(campaign_id)

    print("\n" + "=" * 60)
    if ok:
        print(f"DONE. Campaign ID: {campaign_id}  (status: DRAFTED — does not send)")
        print("\nWired and ready. Final manual step to go live:")
        print("  Smartlead UI → campaign → flip status to START")
        print("\nAlready mapped in config.py SECTOR_CAMPAIGN_MAP +")
        print("enroll_contacts_to_campaigns.py for 'General EPC'.")
    else:
        print("WARNING: Sequence count mismatch. Check Smartlead UI.")
    print("=" * 60)
