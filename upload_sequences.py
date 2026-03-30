#!/usr/bin/env python3
"""
ContractMotion — Upload Smartlead sequences for 5 sector campaigns.
Skips campaigns that already have a full 6-email sequence.
For campaigns with partial sequences (only seq 6), uploads seqs 1-5.
Defense (3095136) already has all 6 — skipped entirely.
"""
import json
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


def get_sequences(campaign_id):
    url = f"{BASE_URL}/campaigns/{campaign_id}/sequences?api_key={API_KEY}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  Error fetching sequences: {e}")
        return []


def post_sequences(campaign_id, sequences):
    url = f"{BASE_URL}/campaigns/{campaign_id}/sequences?api_key={API_KEY}"
    try:
        resp = requests.post(url, headers=HEADERS, json={"sequences": sequences}, timeout=30)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# CAMPAIGN 3005694 — Power & Grid Infrastructure
# Status: 0 sequences — upload all 6
# Signals: FERC, PJM/MISO, IOU PUC filings, USASpending NAICS 237130
# ============================================================

POWER_GRID = [
    {
        "seq_number": 1,
        "seq_delay_details": {"delay_in_days": 0},
        "subject": "PJM queue item 3847 — transmission rebuild, no RFP yet",
        "email_body": """{{first_name}},

PJM interconnection queue item 3847 — a 345kV transmission rebuild in the AEP Ohio territory — cleared the feasibility study stage last month. Based on PJM's standard timeline, procurement conversations typically open 8–12 months after queue clearance.

We monitor FERC filings, PJM/MISO queue movement, and IOU capital expenditure filings with state PUCs to surface T&D projects before the bid package exists.

Worth a quick call to see what's in the pipeline for {{company_name}}'s territory?

— Ethan, ContractMotion""",
    },
    {
        "seq_number": 2,
        "seq_delay_details": {"delay_in_days": 4},
        "subject": "why power EPCs keep losing to the same three contractors",
        "email_body": """{{first_name}},

Most T&D and substation EPCs find out about a utility project when the RFP hits a bid portal. By then, the utility's procurement team already has 2–3 contractors on their preferred list from conversations that happened 12–18 months earlier — when the project was still a PUC rate case filing and the feasibility study wasn't done yet.

The contractors on that list didn't get there by responding faster. They got there by being present during the planning window.

Everything after that window is a price competition. The project outcome is largely set before the RFP drops.

Worth seeing what's in that pre-procurement window for {{company_name}} right now?

— Ethan, ContractMotion""",
    },
    {
        "seq_number": 3,
        "seq_delay_details": {"delay_in_days": 9},
        "subject": "what ContractMotion actually monitors for power EPCs",
        "email_body": """{{first_name}},

Here's exactly what we track for Power & Grid contractors:

- FERC eLibrary filings — interconnection applications and transmission project notices
- PJM and MISO capacity auction results — telegraph T&D spend 12–18 months out
- IOU capital expenditure filings with state PUCs — identify utility capex before it becomes public RFPs
- USASpending NAICS 237130 (power/communications line construction) contract awards — signal where federal dollars are flowing

We monitor these sources daily across 147 active EPC contractors and surface projects at the pre-procurement stage — typically 6–18 months before formal solicitation.

20 minutes to walk through what's active in {{company_name}}'s territory?

— Ethan, ContractMotion""",
    },
    {
        "seq_number": 4,
        "seq_delay_details": {"delay_in_days": 15},
        "subject": "2 contracts in 90 days or free — here's why we can guarantee it",
        "email_body": """{{first_name}},

ContractMotion guarantees 2 contracts sourced within 90 days of onboarding — or we continue at no charge until we hit it.

That guarantee exists because of the signal sources we're working from. PJM queue clearances, FERC rate case filings, and IOU capex submissions are public records — they telegraph procurement timelines with reasonable precision.

We don't generate leads. We map a pipeline that already exists and is already funded.

We only take on 3 contractors per sector per region — so the intelligence stays exclusive and the positioning is clean.

If {{company_name}} works in T&D, substation, or transmission infrastructure, worth a call to see if the territory is available.

— Ethan, ContractMotion""",
    },
    {
        "seq_number": 5,
        "seq_delay_details": {"delay_in_days": 22},
        "subject": "NextEra filed 4 transmission project notices last week",
        "email_body": """{{first_name}},

Four new FERC interconnection notices from NextEra Energy crossed our feed last week — three in the Southeast, one in MISO territory. All four are in early development. Procurement on projects like these typically opens 10–14 months after notice filing.

AES and NRG also have active FERC filings in the queue we've flagged for contractors in those regions.

We pull this data daily. Most EPC contractors don't have a system for monitoring it — which is why the preferred list on these projects tends to be the same 3–4 firms every time.

If {{company_name}}'s territory includes any of those corridors, this is worth a conversation.

— Ethan, ContractMotion""",
    },
    {
        "seq_number": 6,
        "seq_delay_details": {"delay_in_days": 30},
        "subject": "closing this out",
        "email_body": """{{first_name}},

Not going to keep following up after this.

If pre-RFP positioning in Power & Grid ever becomes relevant for {{company_name}}, my contact is below.

I'll leave you with this: the PJM interconnection queue has more pending transmission projects right now than at any point in the last decade. The procurement cycles behind that queue are already in motion. The contractors getting called first are those who showed up during the planning window — not the bid window.

Whenever the timing is right.

— Ethan, ContractMotion""",
    },
]


# ============================================================
# CAMPAIGN 3040599 — Data Center & AI Infrastructure
# Status: Only seq 6 exists — upload seqs 1-5
# Signals: County assessor land filings, 50MW+ interconnection requests,
#          AWS/Google/Meta permit filings, PPA announcements
# ============================================================

DATA_CENTER_NEW = [
    {
        "seq_number": 1,
        "seq_delay_details": {"delay_in_days": 0},
        "subject": "480MW interconnection request filed in Loudoun — no RFP yet",
        "email_body": """{{first_name}},

Dominion Energy received a 480MW interconnection capacity request in Loudoun County last month — filed alongside a county assessor land acquisition from a hyperscaler entity. Electrical procurement on projects this size typically opens 10–14 months after interconnection filing.

We track utility interconnection requests for 50MW+ loads, county assessor filings, and municipal permit applications from AWS, Google, and Meta development entities before they become public procurement.

Worth a call to see what's active in {{company_name}}'s market?

— Ethan, ContractMotion""",
    },
    {
        "seq_number": 2,
        "seq_delay_details": {"delay_in_days": 4},
        "subject": "how data center EPCs end up on the preferred list",
        "email_body": """{{first_name}},

The EPCs winning electrical and mechanical work at hyperscaler campuses are not the ones who respond best to an RFP. They're the ones the hyperscaler's construction manager already knows — from a pre-development conversation that happened before the permit was even filed.

By the time a data center bid package hits the market, the preferred list is set. The open bid process satisfies procurement policy. The winner was decided months earlier.

If {{company_name}}'s pipeline starts at the bid package stage, you're entering projects where the decision is already made.

Worth seeing what's at the permit and interconnection stage in your corridors right now?

— Ethan, ContractMotion""",
    },
    {
        "seq_number": 3,
        "seq_delay_details": {"delay_in_days": 9},
        "subject": "what ContractMotion monitors for data center contractors",
        "email_body": """{{first_name}},

Here's exactly what we track for Data Center and AI Infrastructure EPCs:

- Hyperscaler land acquisition filings with county assessors (publicly recorded, rarely watched)
- Utility interconnection requests for 50MW+ loads — filed months before construction starts
- AWS, Google, and Meta permit applications with local municipalities
- Power purchase agreement announcements — telegraph major campus development 12–18 months out

We monitor these sources daily and map the procurement contacts behind each project — so contractors like {{company_name}} are in the room before the bid package exists.

20 minutes to walk through what's active in your target corridors?

— Ethan, ContractMotion""",
    },
    {
        "seq_number": 4,
        "seq_delay_details": {"delay_in_days": 15},
        "subject": "2 contracts in 90 days or free — here's why we can guarantee it",
        "email_body": """{{first_name}},

ContractMotion guarantees 2 contracts sourced within 90 days of onboarding — or we continue at no charge until we hit it.

The guarantee is grounded in the signal sources. County assessor land filings and utility interconnection requests for 50MW+ loads are public records that telegraph hyperscaler construction timelines with real precision. We know which projects are developing and approximately when procurement opens.

We only take 3 contractors per sector per region — so the intelligence stays exclusive to {{company_name}} in your market.

If data center electrical or mechanical EPC is part of your work, worth a call to check territory availability.

— Ethan, ContractMotion""",
    },
    {
        "seq_number": 5,
        "seq_delay_details": {"delay_in_days": 22},
        "subject": "3 hyperscaler campus permits filed in the Phoenix corridor this quarter",
        "email_body": """{{first_name}},

Three separate hyperscaler conditional use permits were filed in the Phoenix-Mesa corridor this quarter — two from Meta entity LLCs, one from an Amazon subsidiary. Interconnection requests for all three have been submitted to APS and SRP.

Combined electrical load: roughly 800MW across the three sites. Procurement windows, based on the filing timeline, open between Q4 2026 and Q2 2027.

None of the three has issued any public bid notice. The contractors being considered right now are those already in conversation with the construction managers.

If {{company_name}} works in that region, this is worth a conversation.

— Ethan, ContractMotion""",
    },
]


# ============================================================
# CAMPAIGN 3040600 — Water & Wastewater Infrastructure
# Status: Only seq 6 exists — upload seqs 1-5
# Signals: CWSRF/DWSRF loan approvals, EPA WIFIA, state DEP permits
# ============================================================

WATER_NEW = [
    {
        "seq_number": 1,
        "seq_delay_details": {"delay_in_days": 0},
        "subject": "CWSRF loan approved — $38M treatment plant expansion, no RFP yet",
        "email_body": """{{first_name}},

EPA's CWSRF database shows a $38M Clean Water State Revolving Fund loan approved last month for a regional wastewater treatment plant expansion. Based on standard SRF procurement timelines, the bid package typically opens 9–12 months after loan approval.

We monitor CWSRF and DWSRF loan approvals, EPA WIFIA announcements, and state DEP permit applications to surface funded water infrastructure projects before they enter formal procurement.

Worth a call to see what's funded and pre-procurement in {{company_name}}'s target states?

— Ethan, ContractMotion""",
    },
    {
        "seq_number": 2,
        "seq_delay_details": {"delay_in_days": 4},
        "subject": "why water EPCs keep losing to the engineer-of-record's preferred list",
        "email_body": """{{first_name}},

Most water and wastewater EPCs find out about a municipal project when the invitation to bid hits a public portal. By then, the municipality's engineer of record has already had informal conversations with 2–3 contractors they trust — and those firms are getting the first call when negotiated contract awards are structured.

The window to become one of those trusted firms is the 9–15 months between SRF loan approval and formal procurement — when the project is funded but no one is watching it yet.

That's the window ContractMotion tracks.

Worth seeing what's funded and pre-procurement in {{company_name}}'s states?

— Ethan, ContractMotion""",
    },
    {
        "seq_number": 3,
        "seq_delay_details": {"delay_in_days": 9},
        "subject": "what ContractMotion monitors for water infrastructure contractors",
        "email_body": """{{first_name}},

Here's exactly what we track for Water and Wastewater EPCs:

- CWSRF (Clean Water State Revolving Fund) loan approvals — published on the EPA CWSRF database, rarely monitored by contractors
- DWSRF (Drinking Water SRF) project listings — separate fund, same pre-procurement window
- EPA WIFIA loan application announcements — large-scale projects ($20M+) with defined procurement timelines
- State DEP and DEQ permit applications for treatment plant upgrades — early signal, 12–18 months before bid

We monitor these sources daily across active water infrastructure EPCs and surface projects at the pre-procurement stage.

20 minutes to walk through what's funded in {{company_name}}'s target states?

— Ethan, ContractMotion""",
    },
    {
        "seq_number": 4,
        "seq_delay_details": {"delay_in_days": 15},
        "subject": "2 contracts in 90 days or free — here's why we can guarantee it",
        "email_body": """{{first_name}},

ContractMotion guarantees 2 contracts sourced within 90 days of onboarding — or we continue at no charge until we hit it.

The guarantee is grounded in the signals. CWSRF and DWSRF loan approvals are public records with predictable procurement timelines — once a loan is approved, the project is funded and the procurement window is measurable. We know which projects are in the pipeline and approximately when they'll go to market.

We only take 3 contractors per sector per region — keeping the intelligence exclusive to {{company_name}} in your market.

If water or wastewater EPC is part of your work, worth a call to check territory availability.

— Ethan, ContractMotion""",
    },
    {
        "seq_number": 5,
        "seq_delay_details": {"delay_in_days": 22},
        "subject": "14 WIFIA loan applications filed this quarter — none in formal procurement",
        "email_body": """{{first_name}},

EPA's WIFIA program received 14 new loan applications this quarter across 9 states — representing an estimated $2.1B in water and wastewater infrastructure. WIFIA projects at this stage typically enter formal contractor procurement 12–18 months after application acceptance.

None of the 14 has issued a public solicitation yet.

Separately, CWSRF approvals in the mid-Atlantic states have accelerated this quarter — 22 loans approved since January, 17 of which haven't entered formal bid.

The contractors being positioned on these projects right now are those who showed up during the funding window — not the bid window.

If {{company_name}}'s territory includes any of those states, worth a conversation.

— Ethan, ContractMotion""",
    },
]


# ============================================================
# CAMPAIGN 3040601 — Industrial & Manufacturing Facilities
# Status: Only seq 6 exists — upload seqs 1-5
# Signals: SEC 8-K capex, IRB filings, site selection RFIs,
#          corporate earnings calls ("new facility" / "capacity expansion")
# ============================================================

INDUSTRIAL_NEW = [
    {
        "seq_number": 1,
        "seq_delay_details": {"delay_in_days": 0},
        "subject": "8-K filed — $340M facility expansion, no EPC selected yet",
        "email_body": """{{first_name}},

A mid-cap manufacturer filed an SEC 8-K last week disclosing a $340M facility expansion in the Southeast. CHIPS Act-adjacent, not a direct recipient — corporate capex. Based on the project description, EPC procurement typically opens 10–16 months after an 8-K disclosure at this scale.

We monitor SEC 8-K capex filings, industrial revenue bond applications, and site selection consultant RFIs to surface manufacturing facility projects before they reach formal procurement.

Worth a call to see what's in the pipeline for {{company_name}}'s sector?

— Ethan, ContractMotion""",
    },
    {
        "seq_number": 2,
        "seq_delay_details": {"delay_in_days": 4},
        "subject": "why industrial EPCs keep missing the owner's engineer call list",
        "email_body": """{{first_name}},

Most industrial EPCs find out about a major facility project when the owner posts an RFQ or the owner's engineer sends a solicitation. By that point, the OE already has 2–3 contractors they're planning to recommend — firms that made contact during the permit or financing stage, before anyone else knew the project existed.

The window to get on that list is not the RFQ. It's the 12–18 months between an 8-K disclosure or industrial revenue bond filing and formal procurement — when the project is public but no one in EPC is watching it.

ContractMotion tracks that window for {{company_name}}.

Worth a look at what's in the industrial pipeline for your sector right now?

— Ethan, ContractMotion""",
    },
    {
        "seq_number": 3,
        "seq_delay_details": {"delay_in_days": 9},
        "subject": "what ContractMotion monitors for industrial contractors",
        "email_body": """{{first_name}},

Here's exactly what we track for Industrial and Manufacturing EPC contractors:

- SEC 8-K filings with capex disclosures — manufacturers announcing "new facility" or "capacity expansion" are in pre-procurement 12–18 months out
- Industrial revenue bond (IRB) filings with state finance authorities — public record, almost never monitored by contractors
- Site selection consultant RFIs filed with state economic development agencies — signals a project is actively siting
- Corporate earnings call transcripts mentioning "new facility" or "capacity expansion" — AI-extracted daily

We monitor these sources daily and cross-reference against NAICS codes relevant to your EPC work.

20 minutes to walk through what's active for {{company_name}}'s sector and region?

— Ethan, ContractMotion""",
    },
    {
        "seq_number": 4,
        "seq_delay_details": {"delay_in_days": 15},
        "subject": "2 contracts in 90 days or free — here's why we can guarantee it",
        "email_body": """{{first_name}},

ContractMotion guarantees 2 contracts sourced within 90 days of onboarding — or we continue at no charge until we hit it.

The guarantee is grounded in the signals. SEC 8-K filings and industrial revenue bond applications are public records with predictable procurement timelines — once a manufacturer discloses a capex project, the procurement window is trackable. We know which projects are developing and when the OE selection conversation typically begins.

We only take 3 contractors per sector per region — keeping the intelligence exclusive to {{company_name}} in your market.

If industrial facility construction is part of your work, worth a call to check territory availability.

— Ethan, ContractMotion""",
    },
    {
        "seq_number": 5,
        "seq_delay_details": {"delay_in_days": 22},
        "subject": "Q1 2026 — 31 IRB filings in manufacturing, 24 not yet in procurement",
        "email_body": """{{first_name}},

State finance authorities received 31 industrial revenue bond applications in the manufacturing sector in Q1 2026. Of those, 24 have not issued any EPC solicitation yet — the projects are financed and in development, but procurement hasn't opened.

Separately, our earnings call monitoring flagged 18 S&P 500 manufacturers referencing "new facility" or "capacity expansion" in Q1 transcripts. Eleven are in sectors relevant to industrial EPC work.

These filings and disclosures are public. Most EPC contractors don't have a system for watching them — which is why the OE call list tends to be the same firms every cycle.

If {{company_name}}'s sector overlaps with any of this activity, worth a conversation.

— Ethan, ContractMotion""",
    },
]


# ============================================================
# EXECUTE
# ============================================================

campaigns = [
    {
        "id": 3005694,
        "name": "Power & Grid Infrastructure",
        "sequences": POWER_GRID,
        "expected_existing_count": 0,  # Has 0 — upload all 6
        "upload_all": True,
    },
    {
        "id": 3040599,
        "name": "Data Center & AI Infrastructure",
        "sequences": DATA_CENTER_NEW,
        "expected_existing_count": 1,  # Has seq 6 only — upload 1-5
        "upload_all": False,
    },
    {
        "id": 3040600,
        "name": "Water & Wastewater",
        "sequences": WATER_NEW,
        "expected_existing_count": 1,
        "upload_all": False,
    },
    {
        "id": 3040601,
        "name": "Industrial & Manufacturing",
        "sequences": INDUSTRIAL_NEW,
        "expected_existing_count": 1,
        "upload_all": False,
    },
    # Campaign 3095136 (Defense) already has 6 sequences — skip
]

for campaign in campaigns:
    cid = campaign["id"]
    name = campaign["name"]
    print(f"\n{'='*60}")
    print(f"Campaign: {name} ({cid})")

    existing = get_sequences(cid)
    existing_seq_numbers = [s["seq_number"] for s in existing]
    print(f"  Existing sequences: {existing_seq_numbers}")

    if len(existing) >= 6:
        print(f"  SKIP — already has {len(existing)} sequences")
        continue

    sequences_to_upload = campaign["sequences"]
    print(f"  Uploading {len(sequences_to_upload)} sequences...")

    result = post_sequences(cid, sequences_to_upload)
    print(f"  Result: {result}")

# Verify
print(f"\n{'='*60}")
print("VERIFICATION")
print(f"{'='*60}")
all_campaign_ids = [3005694, 3040599, 3040600, 3040601, 3095136]
names = {
    3005694: "Power & Grid",
    3040599: "Data Center & AI",
    3040600: "Water & Wastewater",
    3040601: "Industrial & Mfg",
    3095136: "Defense & Federal",
}
for cid in all_campaign_ids:
    seqs = get_sequences(cid)
    seq_nums = sorted([s["seq_number"] for s in seqs])
    status = "COMPLETE" if len(seqs) == 6 else f"INCOMPLETE ({len(seqs)}/6)"
    print(f"  {names[cid]} ({cid}): {status} — seqs {seq_nums}")

print("\nDone.")
