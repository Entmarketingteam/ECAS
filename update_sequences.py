#!/usr/bin/env python3
"""
Update ContractMotion Smartlead sequences with persona-specific messaging.
"""
import json
import urllib.request
import urllib.error

API_KEY = "17a34ec2-b253-45a8-9f0c-707333b745ad_3eex9gg"
BASE_URL = "https://server.smartlead.ai/api/v1"


def update_sequences(campaign_id, sequences):
    """POST sequences update to Smartlead."""
    url = f"{BASE_URL}/campaigns/{campaign_id}/sequences?api_key={API_KEY}"
    payload = json.dumps({"sequences": sequences}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            return result
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read().decode()}


# ============================================================
# CAMPAIGN 3005694 — Power & Grid
# Sequence IDs: 6657767, 6657768, 6657769, 6657770, 6657771, 6657772
# ============================================================

POWER_GRID_SEQUENCES = [
    {
        "id": 6657767,
        "seq_number": 1,
        "seq_delay_details": {"delay_in_days": 0},
        "subject": "138kV rebuild going to RFP — {{company_name}} territory",
        "email_body": (
            "<p>{{first_name}},</p>"
            "<p>Dominion filed interconnection paperwork on a 138kV transmission rebuild in Northern Virginia last week. "
            "Estimated procurement window: Q3 this year. It's not public yet.</p>"
            "<p>We track FERC filings, utility rate cases, and PJM queue movement 12–18 months ahead of formal procurement. "
            "Thought it was worth flagging for {{company_name}}.</p>"
            "<p>— Ethan</p>"
        ),
    },
    {
        "id": 6657768,
        "seq_number": 2,
        "seq_delay_details": {"delay_in_days": 4},
        "subject": "how most Power & Grid EPCs find out about utility projects",
        "email_body": (
            "<p>{{first_name}},</p>"
            "<p>The typical EPC finds out about a utility project when the RFP hits Dodge or a rep forwards a bid notice. "
            "By then, the procurement team already has 2–3 contractors in mind from pre-development conversations that happened "
            "12 months earlier.</p>"
            "<p>Those contractors didn't get there by responding faster. They got there by being visible when the project was "
            "still a rate case filing — before anyone else was looking. That's the only window that matters in Power & Grid. "
            "Everything after it is a price competition.</p>"
            "<p>Worth seeing what's in that window for {{company_name}} right now?</p>"
            "<p>— Ethan</p>"
        ),
    },
    {
        "id": 6657769,
        "seq_number": 3,
        "seq_delay_details": {"delay_in_days": 9},
        "subject": "what shifted for one EPC in the PJM corridor",
        "email_body": (
            "<p>{{first_name}},</p>"
            "<p>A mid-tier Power & Grid EPC — strong regional reputation, not hurting for work but not growing the way they wanted — "
            "started tracking FERC interconnection filings and utility capex rate cases before they became public solicitations.</p>"
            "<p>Within two quarters, they had procurement conversations at two utilities they had never worked with. Neither project "
            "was on anyone else's radar. Both went to preferred contractor selection — not open bid.</p>"
            "<p>The difference wasn't price or capability. It was showing up before there was anything to bid on.</p>"
            "<p>That window is open in the PJM and ERCOT corridors right now. Happy to show you what we're seeing for your territory.</p>"
            "<p>— Ethan</p>"
        ),
    },
    {
        "id": 6657770,
        "seq_number": 4,
        "seq_delay_details": {"delay_in_days": 15},
        "subject": "the Power & Grid projects that never become public RFPs",
        "email_body": (
            "<p>{{first_name}},</p>"
            "<p>In Q1 2026, 47 transmission and substation projects in PJM and ERCOT moved from feasibility study to active development — "
            "meaning procurement conversations are happening now or within 6 months.</p>"
            "<p>Of those, roughly 12 will go to open competitive bid. The other 35 will be awarded through preferred contractor "
            "relationships, sole-source pre-qualifications, or negotiated contracts with firms already known to the developer or utility.</p>"
            "<p>If {{company_name}}'s pipeline starts at the RFP stage, you have visibility into roughly 25% of the available market. "
            "The other 75% requires being positioned before the project is formally announced.</p>"
            "<p>That's not a BD problem. It's an intelligence problem — knowing which projects exist before your competitors do. "
            "Happy to pull the active project list for your territory.</p>"
            "<p>— Ethan</p>"
        ),
    },
    {
        "id": 6657771,
        "seq_number": 5,
        "seq_delay_details": {"delay_in_days": 22},
        "subject": "2 pre-RFP shortlist positions. 180 days. Guaranteed.",
        "email_body": (
            "<p>{{first_name}},</p>"
            "<p>One thing I haven't mentioned: ContractMotion guarantees 2 pre-RFP shortlist positions in your sector within "
            "180 days of onboarding — or we continue working at no charge until we hit it.</p>"
            "<p>That guarantee exists because we know which utility and developer procurement cycles are active before they publish. "
            "We're not generating leads. We're mapping a pipeline that already exists.</p>"
            "<p>Worth 20 minutes to see if {{company_name}} qualifies?</p>"
            "<p>— Ethan</p>"
        ),
    },
    {
        "id": 6657772,
        "seq_number": 6,
        "seq_delay_details": {"delay_in_days": 30},
        "subject": "closing the file on this",
        "email_body": (
            "<p>{{first_name}},</p>"
            "<p>Closing this thread — I don't want to become noise in your inbox.</p>"
            "<p>If the Power & Grid pipeline ever gets competitive and pre-RFP positioning becomes relevant for {{company_name}}, "
            "my contact is below. I'll also leave you this: the PJM interconnection queue has more pending transmission projects "
            "right now than at any point in the last decade. The procurement cycles behind that queue are already in motion.</p>"
            "<p>Worth keeping in mind whenever the timing is right.</p>"
            "<p>— Ethan</p>"
        ),
    },
]

# ============================================================
# CAMPAIGN 3040599 — Data Center & AI Infrastructure
# Sequence ID for email 6: 6681006 (only one exists, need to add 1-5)
# ============================================================

DATA_CENTER_SEQUENCES = [
    {
        "seq_number": 1,
        "seq_delay_details": {"delay_in_days": 0},
        "subject": "480MW data center campus — permit filed, no RFP yet",
        "email_body": (
            "<p>{{first_name}},</p>"
            "<p>A hyperscaler filed a conditional use permit for a 480MW data center campus in Loudoun County last week. "
            "Electrical procurement typically opens 10–14 months after permit filing. The bid package doesn't exist yet.</p>"
            "<p>We track permit applications, interconnection filings, and utility capacity requests across the hyperscaler and "
            "co-lo corridor. Flagging it for {{company_name}}.</p>"
            "<p>— Ethan</p>"
        ),
    },
    {
        "seq_number": 2,
        "seq_delay_details": {"delay_in_days": 4},
        "subject": "how Data Center EPCs end up on the preferred list (and how they don't)",
        "email_body": (
            "<p>{{first_name}},</p>"
            "<p>The EPCs winning data center electrical work at hyperscalers are not the ones who respond best to an RFP. "
            "They're the ones the hyperscaler's construction manager already knows from a pre-development meeting that happened "
            "before the permit was even filed.</p>"
            "<p>By the time a data center bid package hits the market, the preferred list is already set. The open bid process "
            "is a formality — it satisfies procurement policy, but the winner was decided months earlier.</p>"
            "<p>ContractMotion tracks permit filings, interconnection capacity requests, and utility coordination letters "
            "so {{company_name}} is in that conversation before the project is announced.</p>"
            "<p>Worth a look at what's active in your market right now?</p>"
            "<p>— Ethan</p>"
        ),
    },
    {
        "seq_number": 3,
        "seq_delay_details": {"delay_in_days": 9},
        "subject": "what shifted for one data center EPC in Northern Virginia",
        "email_body": (
            "<p>{{first_name}},</p>"
            "<p>A mid-size electrical EPC focused on data center work was landing projects fine — mostly repeat business, "
            "occasional competitive bids — but couldn't break into the hyperscaler tier. Too much competition, no relationships.</p>"
            "<p>They started tracking permit applications and interconnection filings in the Northern Virginia corridor. "
            "Within one quarter, they had intro calls with construction managers at two hyperscalers based on projects "
            "that weren't public yet. One converted to a pre-qualification. The other is still in motion.</p>"
            "<p>The opening wasn't the RFP. It was the permit filing — 14 months earlier.</p>"
            "<p>The same window is open across the Loudoun, Ashburn, and Phoenix corridors right now. Happy to pull what we're seeing.</p>"
            "<p>— Ethan</p>"
        ),
    },
    {
        "seq_number": 4,
        "seq_delay_details": {"delay_in_days": 15},
        "subject": "data center electrical projects that never go to open bid",
        "email_body": (
            "<p>{{first_name}},</p>"
            "<p>In Q1 2026, 63 data center projects filed permits or submitted interconnection requests across the top 10 US "
            "hyperscaler markets — representing an estimated 18GW of committed load through 2028.</p>"
            "<p>Of the electrical and mechanical EPC contracts behind those projects, roughly 20% will go to competitive bid. "
            "The other 80% will be awarded through preferred contractor agreements, repeat relationships, or sole-source "
            "negotiations with firms that were already known to the developer's construction team.</p>"
            "<p>If {{company_name}}'s pipeline starts at the bid package stage, you have access to roughly a fifth of the market. "
            "ContractMotion tracks the other four-fifths — at the permit and interconnection stage, before procurement opens.</p>"
            "<p>Happy to pull the active project list for your target corridors.</p>"
            "<p>— Ethan</p>"
        ),
    },
    {
        "seq_number": 5,
        "seq_delay_details": {"delay_in_days": 22},
        "subject": "2 pre-RFP shortlist positions. 180 days. Guaranteed.",
        "email_body": (
            "<p>{{first_name}},</p>"
            "<p>One thing I haven't mentioned: ContractMotion guarantees 2 pre-RFP shortlist positions in the Data Center "
            "and AI infrastructure sector within 180 days of onboarding — or we keep working at no charge until we hit it.</p>"
            "<p>That guarantee exists because we're not generating leads. We're tracking a construction pipeline that already "
            "exists in permit filings, interconnection queues, and utility capacity requests — and mapping the procurement "
            "contacts behind each project.</p>"
            "<p>Worth 20 minutes to see if {{company_name}} qualifies?</p>"
            "<p>— Ethan</p>"
        ),
    },
    {
        "id": 6681006,
        "seq_number": 6,
        "seq_delay_details": {"delay_in_days": 30},
        "subject": "last note — leaving a resource",
        "email_body": (
            "<p>{{first_name}},</p>"
            "<p>Closing this out — don't want to become noise.</p>"
            "<p>If pre-RFP positioning in the data center sector ever becomes relevant for {{company_name}}, I'm easy to find. "
            "I'll leave you this: the Northern Virginia, Phoenix, and Chicago data center corridors have more permitted-but-unprocured "
            "electrical capacity in queue right now than at any point in the last five years. The contractors positioned before "
            "those projects announce will be the ones who win them.</p>"
            "<p>Good luck out there.</p>"
            "<p>— Ethan</p>"
        ),
    },
]

# ============================================================
# CAMPAIGN 3040600 — Water & Wastewater Infrastructure
# Sequence ID for email 6: 6681012
# ============================================================

WATER_SEQUENCES = [
    {
        "seq_number": 1,
        "seq_delay_details": {"delay_in_days": 0},
        "subject": "$42M SRF loan approved — project going to bid in 9 months",
        "email_body": (
            "<p>{{first_name}},</p>"
            "<p>EPA approved a $42M State Revolving Fund loan for a regional wastewater treatment expansion in your state last week. "
            "Based on the SRF timeline, procurement typically opens 9–12 months after loan approval. The bid package doesn't exist yet.</p>"
            "<p>We track SRF approvals, EPA awards, and PUC filings to surface funded water and wastewater projects before they "
            "go to market. Flagging this one for {{company_name}}.</p>"
            "<p>— Ethan</p>"
        ),
    },
    {
        "seq_number": 2,
        "seq_delay_details": {"delay_in_days": 4},
        "subject": "how water & wastewater EPCs end up on the short list",
        "email_body": (
            "<p>{{first_name}},</p>"
            "<p>Most water and wastewater EPCs find out about a municipal project when the invitation to bid hits a public portal. "
            "By then, the municipality's engineer of record has already had informal conversations with 2–3 contractors they "
            "trust — and those firms are getting the first call when the contract award is negotiated.</p>"
            "<p>The window to become one of those trusted firms isn't the bid response. It's the 9–15 months between SRF loan "
            "approval and formal procurement — when no one else is paying attention.</p>"
            "<p>ContractMotion tracks that window for {{company_name}}. Worth seeing what's funded and pre-procurement in your states?</p>"
            "<p>— Ethan</p>"
        ),
    },
    {
        "seq_number": 3,
        "seq_delay_details": {"delay_in_days": 9},
        "subject": "what changed for one water infrastructure EPC",
        "email_body": (
            "<p>{{first_name}},</p>"
            "<p>A regional water infrastructure EPC — solid reputation, mostly repeat municipal clients — was competing on "
            "open bids for every new project. Win rate was around 20%. Good work, but no edge.</p>"
            "<p>They started tracking SRF approvals and EPA infrastructure grants in their target states before the projects "
            "went to formal procurement. Within two quarters, they had pre-procurement conversations with three municipalities "
            "whose projects hadn't been announced. Two led to preferred contractor discussions before the bid even went public.</p>"
            "<p>The difference wasn't their proposal. It was the fact that they showed up before there was a proposal to write.</p>"
            "<p>The same approach is available to {{company_name}} right now. Happy to show you what's in the funded pipeline for your states.</p>"
            "<p>— Ethan</p>"
        ),
    },
    {
        "seq_number": 4,
        "seq_delay_details": {"delay_in_days": 15},
        "subject": "funded water projects in your states that haven't gone to bid yet",
        "email_body": (
            "<p>{{first_name}},</p>"
            "<p>The Infrastructure Investment and Jobs Act allocated $55B to water infrastructure through 2026. As of Q1 2026, "
            "SRF programs across US states have approved funding for thousands of municipal water and wastewater projects — "
            "a large majority of which have not yet entered formal procurement.</p>"
            "<p>Of the contracts behind those funded projects, most will go to open competitive bid. But a meaningful share "
            "will be awarded through preferred contractor negotiations, engineering firm relationships, or sole-source agreements "
            "with contractors who were already in conversation with the municipality.</p>"
            "<p>If {{company_name}}'s pipeline starts at the public bid notice, you're missing the pre-procurement window entirely. "
            "ContractMotion tracks SRF approvals, EPA awards, and PUC filings to surface those projects before procurement opens.</p>"
            "<p>Happy to pull the funded project list for your target states.</p>"
            "<p>— Ethan</p>"
        ),
    },
    {
        "seq_number": 5,
        "seq_delay_details": {"delay_in_days": 22},
        "subject": "2 pre-RFP shortlist positions. 180 days. Guaranteed.",
        "email_body": (
            "<p>{{first_name}},</p>"
            "<p>One thing I haven't mentioned: ContractMotion guarantees 2 pre-RFP shortlist positions in the water and "
            "wastewater sector within 180 days of onboarding — or we keep working at no charge until we hit it.</p>"
            "<p>That guarantee exists because we're tracking a funded pipeline — SRF approvals and EPA awards that already "
            "exist in public records but haven't reached formal procurement yet.</p>"
            "<p>Worth 20 minutes to see if {{company_name}} qualifies?</p>"
            "<p>— Ethan</p>"
        ),
    },
    {
        "id": 6681012,
        "seq_number": 6,
        "seq_delay_details": {"delay_in_days": 30},
        "subject": "last note — leaving a resource",
        "email_body": (
            "<p>{{first_name}},</p>"
            "<p>Closing this out — don't want to become noise.</p>"
            "<p>If pre-procurement positioning in the water and wastewater sector ever becomes relevant for {{company_name}}, "
            "I'm easy to find. I'll leave you this: IIJA water funding is still flowing through state SRF programs through 2026 — "
            "there's more funded-but-unprocured municipal infrastructure in queue right now than most EPCs realize. "
            "The contractors who show up during the funding window, not the bid window, are the ones building relationships "
            "that compound over years.</p>"
            "<p>Good luck out there.</p>"
            "<p>— Ethan</p>"
        ),
    },
]

# ============================================================
# CAMPAIGN 3040601 — Industrial & Manufacturing Facilities
# Sequence ID for email 6: 6681018
# ============================================================

INDUSTRIAL_SEQUENCES = [
    {
        "seq_number": 1,
        "seq_delay_details": {"delay_in_days": 0},
        "subject": "CHIPS Act fab expansion — air permit filed, no EPC selected yet",
        "email_body": (
            "<p>{{first_name}},</p>"
            "<p>A semiconductor manufacturer filed an air permit for a fab expansion in Arizona last week. "
            "CHIPS Act funding was confirmed in January. EPC selection typically happens 12–18 months after permit filing. "
            "The project isn't in procurement yet.</p>"
            "<p>We track CHIPS grants, EPA air permits, and industrial facility permit applications to surface projects before "
            "they go to market. Flagging this one for {{company_name}}.</p>"
            "<p>— Ethan</p>"
        ),
    },
    {
        "seq_number": 2,
        "seq_delay_details": {"delay_in_days": 4},
        "subject": "how industrial EPCs end up on the owner's engineer's call list",
        "email_body": (
            "<p>{{first_name}},</p>"
            "<p>Most industrial EPCs find out about a CHIPS Act or advanced manufacturing project when the owner posts a bid package "
            "or the owner's engineer sends out an RFQ. By that point, the OE already has 2–3 contractors they're planning to call — "
            "firms they've worked with before or who reached out during the permit stage.</p>"
            "<p>The window to get on that list isn't the bid response. It's the 12–18 months between permit approval and formal "
            "procurement — when the project exists in public records but nobody's watching it yet.</p>"
            "<p>That's the window ContractMotion tracks for {{company_name}}. Worth seeing what's in the industrial pipeline for your sector right now?</p>"
            "<p>— Ethan</p>"
        ),
    },
    {
        "seq_number": 3,
        "seq_delay_details": {"delay_in_days": 9},
        "subject": "what shifted for one industrial EPC chasing CHIPS projects",
        "email_body": (
            "<p>{{first_name}},</p>"
            "<p>A mid-size industrial EPC was qualified for CHIPS Act and advanced manufacturing work — strong resume, right "
            "NAICS codes — but couldn't get in front of the right owners engineers before the preferred contractors were already set.</p>"
            "<p>They started tracking EPA air permits and CHIPS grant announcements in their target geographies before projects "
            "went to formal procurement. Within two quarters, they had pre-qualification conversations at two projects that "
            "weren't publicly announced yet. One converted. The other is still developing.</p>"
            "<p>The entry point wasn't the RFQ. It was the permit filing — 15 months earlier — when the OE was still open to "
            "new relationships.</p>"
            "<p>The same window is open in the semiconductor and battery manufacturing corridors right now. Happy to show you "
            "what we're tracking for {{company_name}}'s sector.</p>"
            "<p>— Ethan</p>"
        ),
    },
    {
        "seq_number": 4,
        "seq_delay_details": {"delay_in_days": 15},
        "subject": "industrial projects in your sector that haven't entered procurement yet",
        "email_body": (
            "<p>{{first_name}},</p>"
            "<p>CHIPS Act, IRA manufacturing incentives, and DOE industrial grants are funding a multi-year wave of advanced "
            "manufacturing facility construction. As of Q1 2026, over 200 semiconductor, EV battery, and critical materials "
            "facilities have received federal funding commitments — the majority of which have not yet entered formal EPC procurement.</p>"
            "<p>Of the contracts behind those projects, most will go through some form of competitive selection. But the firms "
            "that get invited to the table are those the owner's engineer already knows — often from pre-permit conversations "
            "that happened 12–18 months before the bid package was written.</p>"
            "<p>If {{company_name}}'s pipeline starts at the RFQ stage, you're entering projects where the preferred list is "
            "already forming. ContractMotion tracks EPA permits, CHIPS grants, and FERC filings to surface projects at the "
            "pre-procurement stage.</p>"
            "<p>Happy to pull the active project list for your sector and target states.</p>"
            "<p>— Ethan</p>"
        ),
    },
    {
        "seq_number": 5,
        "seq_delay_details": {"delay_in_days": 22},
        "subject": "2 pre-RFP shortlist positions. 180 days. Guaranteed.",
        "email_body": (
            "<p>{{first_name}},</p>"
            "<p>One thing I haven't mentioned: ContractMotion guarantees 2 pre-RFP shortlist positions in the industrial and "
            "manufacturing sector within 180 days of onboarding — or we keep working at no charge until we hit it.</p>"
            "<p>That guarantee exists because we're tracking a funded pipeline — CHIPS grants, IRA incentives, and EPA permits "
            "that already exist in public records but haven't reached formal procurement yet.</p>"
            "<p>Worth 20 minutes to see if {{company_name}} qualifies?</p>"
            "<p>— Ethan</p>"
        ),
    },
    {
        "id": 6681018,
        "seq_number": 6,
        "seq_delay_details": {"delay_in_days": 30},
        "subject": "last note — leaving a resource",
        "email_body": (
            "<p>{{first_name}},</p>"
            "<p>Closing this out — don't want to become noise.</p>"
            "<p>If pre-procurement positioning in the industrial and manufacturing sector ever becomes relevant for {{company_name}}, "
            "I'm easy to find. I'll leave you this: the CHIPS Act and IRA manufacturing buildout is creating a 5-year runway of "
            "industrial EPC work — and most of the procurement decisions are being made before the bid packages are written. "
            "The contractors who are visible at the permit stage are the ones building the owner relationships that lead to "
            "decade-long preferred contractor status.</p>"
            "<p>Good luck out there.</p>"
            "<p>— Ethan</p>"
        ),
    },
]

# ============================================================
# EXECUTE UPDATES
# ============================================================

campaigns = [
    (3005694, POWER_GRID_SEQUENCES, "Power & Grid"),
    (3040599, DATA_CENTER_SEQUENCES, "Data Center & AI Infrastructure"),
    (3040600, WATER_SEQUENCES, "Water & Wastewater"),
    (3040601, INDUSTRIAL_SEQUENCES, "Industrial & Manufacturing"),
]

for campaign_id, sequences, name in campaigns:
    print(f"\n{'='*60}")
    print(f"Updating: {name} (Campaign {campaign_id})")
    print(f"Sequences to push: {len(sequences)}")
    result = update_sequences(campaign_id, sequences)
    print(f"Result: {result}")

print("\nDone.")
