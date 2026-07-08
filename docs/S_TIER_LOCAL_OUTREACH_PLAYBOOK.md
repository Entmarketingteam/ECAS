# The S-Tier Local B2B Outreach Playbook
*Integrating Growth Engine X Deliverability & ColdIQ Direct-Response Frameworks (2026 Edition)*

---

## Section 1: The Invisible 90% — Dynamic DNS & Inbox Architecture

Deliverability is not a "nice-to-have." If your domain reputation drops below 98%, your cold emails land in the promotions or spam folder, reducing your reply rate by up to 90%.

### 1. Horizontal Mailbox Scaling
*   **The Golden Rule:** Never send more than **30 cold emails per inbox per day** (including follow-ups).
*   To send 2,000 cold emails per month, do not use 1 inbox sending 100 emails/day. Use **3 secondary domains with 3 inboxes each (9 total inboxes)** sending ~22 emails/day/inbox.
*   **Domain Isolation:** Never use your primary corporate domain (e.g., `entagency.com`) for cold outreach. Always purchase auxiliary domains (e.g., `getentagency.com`, `useentagency.com`, `entagencyai.com`).

### 2. DNS Infrastructure Specifications (Non-Negotiable)
For every outreach domain, you must configure the following records exactly:

| Record Type | Host / Name | Value / Target | Purpose |
| :--- | :--- | :--- | :--- |
| **MX** | `@` | Google Workspace Mail Server | Receives replies safely |
| **SPF** | `@` | `v=spf1 include:_spf.google.com ~all` | Authenticates your sending server |
| **DKIM** | `google._domainkey` | `v=DKIM1; k=rsa; p=MIIB...` (From Google Admin) | Signs every outbound email cryptographically |
| **DMARC** | `_dmarcx` | `v=DMARC1; p=quarantine; pct=100; rua=mailto:dmarc@yourdomain.com` | Strict safety protocol preventing spoofing |
| **CNAME** | `inst` or `sl` | `custom.smartlead.sh` | Custom Tracking Domain (Bypasses global spam trackers) |

### 3. Warmup & Ramp-Up Profile
*   **Warmup Duration:** 3 to 4 weeks *before* sending a single cold email.
*   **Warmup Tool Configuration (Smartlead):**
    *   Total emails per day: 15–20 max.
    *   Ramp-up increment: 1 to 2 per day.
    *   Reply rate: 30% to 45% (simulated conversations).
    *   **Warmup Copy:** Plain text only. No HTML, no links, no trackers.

---

## Section 2: Multi-Location "Golden ICP" & Extraction Logic

Generic list filters (like "20-500 employees") waste massive ad-spend and lead to corporate gatekeeper bottlenecks. We target **local-to-regional mid-market companies with 2 to 10 physical locations**.

### 1. Why Multi-Location?
Single-location contractors are often owner-operators who are constantly in the field, struggle with cash flow, and have tiny marketing budgets. Enterprise franchises (Orkin, Terminix) have corporate red tape and require months of C-suite committee approvals. 
**Regional multi-location companies (2-10 offices) are the "Golden ICP":**
*   They have dedicated branch managers with pipeline quotas.
*   They have active commercial budgets ($5k-$20k/mo).
*   The actual Owner/CEO can make a decision in a single, 15-minute conversation.

### 2. Live Dual-Detection Implementation
Our python script (`local_outreach_pipeline.py`) identifies these premium targets using a dual-trigger algorithm:
1.  **Google Maps Search Frequency:** The pipeline pre-scrapes and counts how many times a company's web domain appears in the local territory search. If `BDpest.com` has 3 listings in nearby Louisville suburbs, it is flagged.
2.  **LLM Text Clues:** While crawling the site homepage and "About" page, OpenAI GPT-4o-mini is prompted to scan for markers of branch expansion (e.g., *"our Louisville and Lexington branches"*, list of separate offices, or geographic selectors).

---

## Section 3: The "Pattern Interrupt" 3-Touch Outreach Sequence
*Philosophy: Write for the 97% who are not buying today, not just the 3% who are. Your goal is to spark curiosity, show time/information arbitrage, and earn a soft conversation.*

### Value-Proposition Rotation:
*   **Touch 1:** Introduce the Opportunity / System (Short trigger).
*   **Touch 2:** Case Study / Peer Proof (Show them the cost of the problem).
*   **Touch 3:** Low-Friction Bribe (High-value asset for zero effort).

---

### Email 1: "The Mirror" (Short Trigger)
*   *Subject:* quick route question
*   *Preview:* Hey [First Name], noticed you're over in [Neighborhood]...
*   *Copywriter Note:* No capitalization in the subject line. Renders as a raw, personal email from a local peer.

```markdown
Hey {{Owner First Name}},

Noticed your team at {{Company Name}} has been protecting commercial properties in the {{City}} area since {{Year}} — {{Personalization Snippet}}.

Usually, local owner-operators tell us they're sick of competing with corporate national brands (like Orkin) for low-margin residential jobs, and want a predictable system to secure multi-site commercial accounts (warehouses, property managers, clinics).

We help regional pest operations in {{State}} map commercial property owners and schedule walkthroughs on performance.

According to our route tracking, we mapped out 12 warehouse portfolios in {{City}} looking for regional partners.

Worth exploring?

Best,

Ethan
ENT Agency
```

---

### Email 2: "The Peer Proof" (The Cost of the Problem)
*   *Subject:* (Threaded as reply to Email 1)
*   *Copywriter Note:* Changes the value prop to focus on *financial outcomes and peer proof*.

```markdown
Hey {{Owner First Name}},

I should have added — one regional pest operator we partner with in {{State}} recently used our commercial system to bypass residential door-knocking entirely.

By mapping local facilities with active storage compliance triggers, his estimators booked 3 commercial facility walkthroughs in under 30 days — securing a $12k/yr recurring hospital contract.

We handle the entire GTM setup, proxy scraping, and owner-matching. If we don't book you at least 3 qualified commercial walkthroughs in 45 days, you pay us zero.

Are you the right person at {{Company Name}} to look at your commercial pipeline, or should I reach out to someone else on your team?

Best,

Ethan
```

---

### Email 3: "The Low-Friction Bribe" (The Bribe)
*   *Subject:* (Threaded as reply to Email 1)
*   *Copywriter Note:* Drastically lowers the friction. They haven't responded yet, so they're either busy or unconvinced. Bribe them with high-value free work.

```markdown
Hey {{Owner First Name}},

Since we haven't connected, I went ahead and did some free research for your team.

I put together a localized competitor search audit mapping the top 3 pest companies bidding on commercial contracts in {{City}} — including their target commercial search terms and a custom pitch deck template.

Would you be open to me sending this over via a 2-minute Loom video?

No strings attached, just thought you'd find the keyword data useful.

Best,

Ethan
```

---

## Section 4: The "Lumpy Mail" Brick Campaign SOP
*When your TAM is small (<500 accounts), generic high-volume cold email fails. You must transition to hyper-targeted, high-fidelity physical direct mail to break through the noise.*

```
                       SELECT TARGET ACCOUNTS
                (Top 50 Regional Multi-Location Leads)
                                │
                                ▼
                       ACQUIRE Lumpy Mail Kits
                  (Red Clay Bricks, UPS Mailers)
                                │
                                ▼
                       WRITE Note Cards
            (Hand-written note + QR Code to Demo Page)
                                │
                                ▼
                       SHIP UPS Ground 
                     (Signature required)
                                │
                                ▼
                     EXECUTE Multi-Channel Follow-up
                (Call & Email 2 hours after delivery)
```

### Step 1: Account Selection & Validation
*   Run `local_outreach_pipeline.py` and filter down to the top **50 high-intent regional leads** marked with `Is Multi-Location: YES` and a verified physical mailing address.

### Step 2: Sourcing the "Lumpy Mail" Kit
*   **The Brick:** Purchase standard red clay building bricks from a local hardware store (Home Depot/Lowe's) for ~$0.75 each.
*   **The Packaging:** Standard UPS or USPS padded shipping mailers.
*   **The Note Card:** Heavy-stock 4x6 index cards.

### Step 3: Crafting the Deliverable
1.  On the note card, write the message **by hand** (never print a fake hand-written font; prospect owners spot this instantly and feel deceived).
    > *"Hey {{Owner First Name}} — we want to help {{Company Name}} build a rock-solid, unbreakable commercial pipeline. Scan the code to see how we did it for {{Competitor}}."*
2.  Generate a dynamic QR code leading to a customized, 2-minute video (Loom) of you explaining:
    *   Their local market opportunities.
    *   The 12 commercial properties you've already mapped in their county.
    *   Our risk-free guarantee.
3.  Paste the QR code to the back of the index card.

### Step 4: Shipping Logistics
*   Wrap the red brick in bubble wrap, place the hand-written card on top, and seal it inside the shipping mailer.
*   Ship via **UPS Ground with Signature Required**. 
*   *Why Signature?* Branch managers and owners *must* sign to receive the package. It guarantees it bypasses the front-desk trash bin and lands directly on the decision-maker's desk.

### Step 5: The Multi-Channel Follow-Up Playbook
*   **Timing:** Set an automated alert (using n8n or Slack) to trigger the moment the UPS tracking is marked as "Delivered / Signed."
*   **Within 2 Hours of Delivery:**
    1.  **The Cold Call:**
        > *"Hey {{Owner First Name}}, saw you just signed for our brick up at the office. Didn't want to break your window, just wanted to show you we're serious about building an unbreakable pipeline. Did you get a chance to scan the card?"*
    2.  **The Follow-Up Email:** Thread a quick email:
        > *"Hey {{Owner First Name}} — saw you signed for the parcel. I know it's a bit unorthodox, but I wanted to make sure you got the Louisville competitor search audit. Let me know if the QR link worked."*
