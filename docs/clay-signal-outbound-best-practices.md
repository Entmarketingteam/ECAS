# Clay.com GTM Outbound Playbook
> Signal-based outbound best practices for GTM Engineers using Clay.com
> Source: Grok research synthesis | Saved: 2026-04-02

---

## Table of Contents
1. [What is a GTM Engineer?](#1-what-is-a-gtm-engineer)
2. [Core Skills Stack](#2-core-skills-stack)
3. [The 5 Signal Types](#3-the-5-signal-types)
4. [Signal-Based Workflows (Step-by-Step)](#4-signal-based-workflows)
5. [Claygent Prompt Library](#5-claygent-prompt-library)
6. [Scoring & Prioritization Formulas](#6-scoring--prioritization-formulas)
7. [ABM Strategy in Clay](#7-abm-strategy-in-clay)
8. [Templates & Starting Points](#8-templates--starting-points)
9. [Portfolio & Positioning](#9-portfolio--positioning)
10. [Tool Stack Reference](#10-tool-stack-reference)
11. [Sales Philosophy & Call Framework](#11-sales-philosophy--call-framework)
12. [Operational Playbook: Clay + ENT Stack Integration](#12-operational-playbook-clay--ent-stack-integration)
13. [BLUF Cold Email Framework](#13-bluf-cold-email-framework)
14. [Autonomous Email Agents & Speed-of-Thought GTM Testing](#14-autonomous-email-agents--speed-of-thought-gtm-testing)
15. [B2B List Building System (COLDIQ Framework)](#15-b2b-list-building-system-coldiq-framework)
16. [Outbound Agents Reference (janskuba/outbound-agents)](#16-outbound-agents-reference)

---

## 1. What is a GTM Engineer?

A hybrid role that collapses SDR + AE + Sales Engineer into one technical operator. Builds scalable, AI-powered revenue systems for outbound. Clay popularized the term.

**Core job:** Engineer end-to-end Go-To-Market workflows — sourcing/enriching leads, automating personalization at scale, triggering signals-based plays, integrating with CRMs/sequencing tools, and driving pipeline without massive headcount.

**Why it matters:** One GTM Engineer can replace or 10x what a team of SDRs does by automating research, enrichment, and personalization.

**Backgrounds that convert well:** Ex-SDRs/AEs who got technical, rev ops/growth operators, no-code automation freelancers, software engineers pivoting to revenue. Sales experience often edges out pure coding.

---

## 2. Core Skills Stack

### Must-Have

| Skill | What It Means in Practice |
|-------|--------------------------|
| **Clay Mastery** | Complex tables, multi-source enrichment waterfalls, AI prompting, data cleaning, lead scoring, signal detection, export to sequencers |
| **AI & Prompt Engineering** | Context-rich prompts for LLMs (Claude, GPT) — personalized messaging, company briefs, dynamic sequences. Grounding outputs in enriched data to prevent hallucinations |
| **Automation Fluency** | Zapier, Make, n8n, webhooks/APIs. CRM integrations (Salesforce, HubSpot). Scalable plays with signal-based triggers |
| **Outbound & Sales Acumen** | Domain warmup, sender rotation, deliverability, multi-touch sequencing, offer crafting, ICP understanding, pipeline metrics |

### Nice-to-Have

| Skill | Details |
|-------|---------|
| **Scripting** | Python, SQL, TypeScript — or "vibe coding" willingness |
| **Data Sources** | Apollo, RB2B, Pinecone (vector search), Firecrawl/Exa (web data) |
| **Analytics** | Tracking ROI of plays, A/B testing, CRM/dashboard reporting |

---

## 3. The 5 Signal Types

Clay University's core framework. Every outbound play should be built on one or more of these.

### 3.1 Intent Signals (Active Buying Behavior)
Shows a company is **currently evaluating** solutions in your category.

| Signal | Source | Strength |
|--------|--------|----------|
| Website visits (pricing, integrations, demo pages) | Clay Web Intent (native pixel) | Strongest for timing |
| Category/topic research surges | Third-party providers (Bombora, marketplace) | Good for early awareness |
| Competitor site engagement, G2 comparisons | Custom signals / Claygent scraping | Great for displacement |
| Content downloads, webinar attendance | Custom signals / CRM data | Engagement indicator |
| LinkedIn profile views, social mentions | Custom signals | Behavioral |

**Key insight:** Intent signals are strongest for *timing* — they show current interest vs. future-oriented signals like funding.

### 3.2 Growth Signals (Scaling & Expansion)
Company is growing fast, creating new operational needs and budgets.

| Signal | Source | Why It Matters |
|--------|--------|---------------|
| Funding announcements | Crunchbase enrichment, News signals | Fresh budget for tools |
| Aggressive hiring / headcount surges | New Hire signals, job posting monitoring | Team scaling = tool needs |
| New office openings / geo expansion | News signals, Custom signals | Operational complexity |
| Headcount growth velocity (>20% in 6mo) | Enrichment refresh comparison | Strong momentum indicator |
| Product launches, M&A, partnerships | News signals | Strategic inflection points |

### 3.3 Change Signals (Transitions & Disruptions)
New people, new priorities, new tool evaluations.

| Signal | Source | Why It Matters |
|--------|--------|---------------|
| Job changes (champion moves to new co) | Native Monitor for Job Changes | Warm reactivation play |
| New hires in buying roles | Native New Hire signals | Fresh decision-maker |
| Promotions | Native Promotion signals | Expanded scope/budget |
| Leadership transitions (new CTO, VP Sales) | News + Job Change signals | Strategy resets |

**Key insight:** Job changes are among the highest-converting signals. A champion who moves to a new company is a warm lead at the new org.

### 3.4 Distress Signals (Pain & Friction)
Visible problems creating urgency and openness to switching.

| Signal | Source | Why It Matters |
|--------|--------|---------------|
| Negative reviews (G2, Capterra, Glassdoor) | Custom signals / Claygent scraping | Specific pain = specific solution |
| Compliance violations / regulatory pressure | News signals, Custom signals | Immediate need |
| Public vendor complaints (outages, poor support) | Custom signals / social monitoring | Switch window |
| Layoffs / restructuring | Career Movement signals | Operational stress |

**Critical:** Distress plays require **empathetic messaging**. Position as helper solving the exact issue, not exploiting weakness.

### 3.5 Technographic Signals (Stack Intelligence)
Reveals fit, pain, and timing through technology usage.

| Signal | Source | Why It Matters |
|--------|--------|---------------|
| Competitor tool in stack | HG Insights, BuiltWith, Wappalyzer | Displacement opportunity |
| Stack gaps (missing complementary tool) | Enrichment waterfalls | Fit signal |
| New tech adoption / migration | Enrichment refresh + Custom signals | Expansion/evaluation window |
| Tech removal | Change detection via refresh | Active switch in progress |

---

## 4. Signal-Based Workflows

### 4.1 Foundational: Signal-Based Outbound Engine

The #1 workflow every GTM Engineer builds first.

```
Seed List → Enrich (Waterfall) → Signal Detection → Score → AI Personalization → Export to Sequencer
```

**Step-by-step:**

1. **Input:** Seed list (CSV, Apollo export, LinkedIn Sales Nav, or domains)
2. **Enrich (waterfall — cheapest first):**
   - Firmographics (size, industry, revenue, location)
   - Technographics (tech stack)
   - Contact-level (verified emails via Hunter/Snov waterfall, LinkedIn URLs, phone)
   - Signals (funding, job changes, news, hiring, website visitors)
3. **AI Research:** Claygent column for "why now" research
4. **Score:** Formula column with weighted points per signal
5. **Personalize:** AI column drafts hooks/emails grounded in enriched data
6. **Export:** One-click to Smartlead or webhook to CRM
7. **Loop:** Refresh table periodically for fresh signals

### 4.2 Job Change + Funding Combined Workflow

The highest-leverage multi-signal play. New role + fresh capital = budget, new priorities, tool evaluation window.

**Setup:**
1. Monitor for Job Changes (requires LinkedIn URL column)
2. Monitor for News/Fundraising OR Crunchbase enrichment
3. Enrich new company (firmographics, technographics, website scrape)
4. Score with combined formula (see Section 6)
5. Run Claygent only on hot rows (both signals recent)
6. Generate personalized outreach referencing both signals
7. Route: Hot → sequence + Slack alert; Medium → nurture; Low → monitor

### 4.3 Funding Signal Workflow

**Steps:**
1. Seed list of ICP companies
2. Enrich with Crunchbase (amount, stage, date, investors, total rounds)
3. Set up News/Fundraising signal monitor (daily for hot signals)
4. Score by amount threshold + stage match + recency
5. Claygent for "use of proceeds" research + value prop mapping
6. Generate hooks referencing exact amount/investors/use of funds
7. Export with routing logic

### 4.4 Investor Network / Mutual Investor Warm Intro

**Steps:**
1. Build investor network base table (your customers' investors or cap table)
2. Input target accounts, enrich with investor data
3. Detect mutual investors (formula — see Section 6)
4. Score by overlap quality (lead investor > any shared > none)
5. Claygent for warm intro angle + email draft
6. Route: hot overlaps → intro request email to mutual investor first

### 4.5 Automated Inbound Routing

**Steps:**
1. Webhook/CRM trigger pulls new leads into Clay table
2. Auto-enrich + score for potential (firmo + intent signals)
3. AI drafts follow-ups referencing similar customer use cases
4. Auto-assign to best AE or trigger nurture sequences
5. Detect activation signals → personalized activation outreach

---

## 5. Claygent Prompt Library

### Principles
- **Ground everything** in column data using `{{Column Name}}` variables
- **Specify output format** (bullets, JSON, short paragraph)
- **Add guardrails:** "Use only the following data…" / "If not found, say 'Not found'"
- **Use few-shot examples** for consistency
- **Break complex tasks** into separate columns (research → hook → email)
- **Choose model wisely:** lighter (1-credit) for simple; heavier for deep analysis

### 5.1 Combined "Why Now" Research (Job Change + Funding)

```
You are an expert GTM researcher analyzing multi-signal buying opportunities.

Contact: {{Contact Full Name}} recently moved from {{Old Title}} at {{Old Company}} to {{New Title}} at {{New Company Name}} (domain: {{New Company Domain}}).

The new company also recently raised ${{Funding Amount}} ({{Funding Stage}}) on {{Funding Date}}, with investors {{Investor Names}}.

Using the web (new company website, about/careers/news pages, relevant press), summarize:

- What the job change likely means for their responsibilities and influence (budget, tool decisions).
- What the company is probably scaling or tackling with the new funding.
- Combined urgency: How do these two signals together create a strong "why now" for our solution that [YOUR VALUE PROP]?

Output as concise, actionable bullets. If limited public info, note it. Keep under 150 words total.
```

### 5.2 Personalized Outreach Hook (Multi-Signal)

```
You are a consultative outbound writer for [Your Company/Product].

{{Contact Full Name}} just changed jobs: from {{Old Title}} at {{Old Company}} to {{New Title}} at {{New Company Name}}.

The company recently raised ${{Funding Amount}} ({{Funding Stage}}) led by {{Investor Names}}.

Ground ONLY in this data + any provided company brief/technographics:
- New company context: {{New Company Brief}}
- Our core value prop: [YOUR VALUE PROP]

Write:
- A warm, natural subject line that references the job change and/or funding timing.
- A short opening paragraph (3-5 sentences) that acknowledges the move + funding, shows understanding of the new role/company priorities, and ties in one specific way we help.

Tone: Helpful colleague — researched, non-salesy, specific. Make it feel like a peer who noticed the perfect timing.
```

### 5.3 Mutual Investor Connection Analyzer

```
You are a warm introduction strategist. We have mutual investors with {{Company Name}}:

Our network investors: {{Your_Investor_List}}
Target investors: {{Target_Investor_Names}}
Mutual/overlapping: {{Mutual_Investors_Array}}

Identify the strongest connection (lead investor, board member, recent activity). Suggest the best person at the investor firm to ask for an intro. Then, draft a short, professional warm intro angle tying in their recent ${{Funding Amount}} round and how we helped a similar portfolio company. Tone: helpful, concise, not salesy.
```

### 5.4 Technographic "Why Now"

```
You are an expert GTM researcher analyzing technographic signals.

Company: {{Company Name}} (domain: {{Domain}})
Current tech stack: {{Tech Stack}} (notably: {{Competitor Tool or Gap}})
Combined signals: Job change for {{Contact Name}} to {{New Title}}, funding ${{Funding Amount}}.

Summarize in bullets:
- What the tech stack reveals about current operations, pains, or growth stage.
- How the technographic signal + job change + funding creates urgency.
- 1-2 specific ways our solution [YOUR VALUE PROP] maps to their stack challenges.

Keep concise and grounded in data only.
```

### 5.5 Intent Signal Research

```
You are an expert GTM researcher analyzing intent signals.

Company: {{Company Name}} (domain: {{Domain}})
Intent signals: {{Pages Visited or Intent Details}}
Combined signals: {{Job Change}}, funding ${{Funding Amount}}, tech stack {{Tech Stack}}.

Summarize:
- What the intent behavior reveals about current research or pain points.
- How intent + other signals creates strong "why now" timing.
- 1-2 specific ways our solution [YOUR VALUE PROP] addresses what they're exploring.

Keep concise and grounded.
```

### 5.6 Distress Signal (Empathetic)

```
You are an expert GTM researcher analyzing distress signals empathetically.

Company: {{Company Name}} (domain: {{Domain}})
Distress signals: {{Negative Review Details}}, {{Compliance or Outage Info}}.
Combined signals: {{Job Change}}, funding ${{Funding Amount}}, tech stack {{Tech Stack}}.

Summarize:
- What the distress signals reveal about current pains.
- How distress + other signals creates timing for change.
- 1-2 helpful ways our solution [YOUR VALUE PROP] could alleviate the exact issues — without sounding opportunistic.

Tone: Empathetic and solution-oriented. Keep concise.
```

### 5.7 Signal Prioritization & Routing

```
Classify this combined signal for {{Contact Full Name}} at {{New Company Name}}.

Signals:
- Job change: {{New Title}} (from {{Old Title}} @ {{Old Company}})
- Funding: ${{Funding Amount}} on {{Funding Date}}, stage {{Funding Stage}}

Reason step-by-step considering strategic importance of role, funding urgency, ICP fit.

Output ONLY:
Priority: X/10
Reason: [one sentence]
Recommended Action: [Immediate sequence / Slack alert to AE / Nurture / Monitor only]
Suggested Hook Theme: [1-2 words]
```

### 5.8 ABM Account Brief & Stage Recommendation

```
You are an ABM strategist. For {{Company Name}} in ABM stage {{Current Stage}}:

Signals: {{Combined Signals Summary}}

Summarize:
- Key priorities and pains based on signals.
- Recommended next stage and why.
- 2-3 tailored outreach angles for our solution [YOUR VALUE PROP].

Output in structured bullets.
```

---

## 6. Scoring & Prioritization Formulas

### 6.1 Single-Signal Scoring

```javascript
// Funding recency
let score = 0;
if ({{Days_Since_Last_Funding}} < 30) score += 50;
else if ({{Days_Since_Last_Funding}} < 90) score += 35;
else if ({{Days_Since_Last_Funding}} < 180) score += 15;

// Amount threshold
if ({{Funding_Amount}} > 10000000) score += 30;

// Stage match
if (["Series A", "Series B"].includes({{Funding_Stage}})) score += 20;

score;
```

### 6.2 Multi-Signal Combined Score

```javascript
let jobScore = {{Job_Change_Detected}} ? 40 : 0;
let fundScore = ({{Days_Since_Funding}} < 90) ? 50 : 0;
let techScore = {{Competitor_In_Stack}} ? 35 : 0;
let intentScore = {{Pricing_Page_Visits}} * 30 + ({{High_Engagement}} ? 40 : 0);
let distressScore = {{Negative_Review_Detected}} ? 40 : 0;
let growthScore = ({{Headcount_Growth_Pct}} > 15) ? 40 : 0;

let roleFit = {{New_Title}}.match(/VP|Head|Director|CTO|CMO|RevOps/) ? 30 : 0;

jobScore + fundScore + techScore + intentScore + distressScore + growthScore + roleFit;
```

### 6.3 Mutual Investor Detection (Array Intersection)

```javascript
// Using Lodash (available in Clay formulas)
_.intersection(
  ({{Target_Investor_Names}} || []).map(i => i.toString().toLowerCase().trim()),
  ({{Your_Investor_List}} || []).map(i => i.toString().toLowerCase().trim())
)
```

### 6.4 Mutual Investor Weighted Scoring

```javascript
let mutual = _.intersection(
  ({{Target_Investor_Names}} || []).map(i => String(i).toLowerCase().trim()),
  ({{Your_Investor_List}} || []).map(i => String(i).toLowerCase().trim())
);

let score = mutual.length * 30;
if (mutual.includes({{Target_Lead_Investor}}.toLowerCase().trim())) score += 40;
if ({{Days_Since_Last_Funding}} < 90) score += 25;

score;
```

### 6.5 Fuzzy Investor Matching (Handles Name Variants)

```javascript
let yours = ({{Your_Investor_List}} || []).map(i => String(i).toLowerCase().trim());
let theirs = ({{Target_Investor_Names}} || []).map(i => String(i).toLowerCase().trim());

theirs.filter(t =>
  yours.some(y =>
    t.includes(y) || y.includes(t) ||
    t.split(' ').some(word => y.includes(word) && word.length > 3)
  )
);
```

### 6.6 ABM Tier Assignment

```javascript
let score = {{Combined_Score}};

if (score > 80) return "Tier 1 — Hot (Immediate Sequence)";
if (score > 50) return "Tier 2 — Warm (Nurture + Monitor)";
if (score > 25) return "Tier 3 — Aware (Light Touch)";
return "Monitor Only";
```

### 6.7 Investor Name Normalization

```javascript
{{Raw_Investor_Names}}.toLowerCase().replace(/ventures|capital|llc|lp|partners/gi, '').trim()
```

---

## 7. ABM Strategy in Clay

### ClayBM Framework (3 Stages)

| Stage | Definition | Actions | Signal Threshold |
|-------|-----------|---------|-----------------|
| **Awareness** | High-fit accounts, basic signals | Light-touch content, ads, brand awareness | ICP match + any 1 signal |
| **Interested** | Accounts showing momentum | Deeper engagement, multi-threading, warmer outreach | 2+ signals, score > 50 |
| **Engaged / Pipeline** | Strong combined signals | Orchestrated plays (sequences, direct mail, ads, sales handoff) | 3+ signals, score > 80 |

### Key ABM Plays

1. **Dynamic Tiered Account Lists** — Auto-tier accounts based on real-time signal scoring (not static lists)
2. **Multi-Signal Scoring & Progression** — Accounts auto-advance through stages as signals fire
3. **Micro-Segmentation** — Segment by challenge type, not just firmographics
4. **Anonymous Visitor → Pipeline** — Web intent capture → enrich → score → personalize → sequence
5. **Ad Intelligence** — Push high-scoring accounts to LinkedIn/Facebook custom audiences
6. **Multi-Threading** — Identify 3-5 contacts per account, generate role-specific hooks
7. **Personalized Landing Pages** — Programmatic ABM pages via Clay + Webflow

### ABM Automation Pattern

```
Signal fires → Score recalculated → Stage check →
  If stage change: Claygent research → AI hooks → Export to sequencer
  If hot: Slack alert to AE + CRM task
  If tier 1: Generate personalized landing page + multi-channel play
```

---

## 8. Templates & Starting Points

### Official Clay Templates (clay.com/templates)

| Template | Best For |
|----------|---------|
| **Build Account List + Account Score (Technographic + Firmographic)** | Core ABM foundation, tiering |
| **Auto-Generate Personalized Landing Pages** | High-touch ABM campaigns |
| **Track Job Changes for Champions** | Reactivation / warm outbound |
| **Monitor Job Changes at Target Accounts** | Change signal plays |
| **Find Company Funding Stage + Lead Investors** | Funding signal enrichment |
| **Personalize Outbound with Prospect Challenges** | AI personalization |
| **Draft Outbound Email with 5 Unique Personas** | Multi-variant testing |
| **Find Key Decision Makers from Website URL** | Multi-threading ABM |
| **Run Competitor Displacement Campaigns (Tech Stack)** | Technographic displacement |
| **Score Leads Based on Several Criteria** | Inbound qualification |

### Clay University Courses

| Course | Focus |
|--------|-------|
| **Clay 101** | FETE framework (Find, Enrich, Transform, Export) |
| **Signals & ABM** | 5 signal types, custom signals, ABM staging, ad intelligence |
| **Claygent / AI Prompting** | 11 AI prompts for prospect research, prompt engineering crash course |

Access at: university.clay.com

### Community / Third-Party

- **GTME HQ** — Plug-and-play sales automation templates
- **ZenABM** — Free signal-based ABM templates (zenabm.com/clay-templates)
- **Clay Alpha Forge** — Bootcamp with portfolio projects + certifications

---

## 9. Portfolio & Positioning

### Recommended Structure (Notion or Personal Site)

Per project (3-5 projects total):
1. **Problem & Business Context** (ICP, pain point)
2. **Solution Overview** (workflow diagram or Clay table screenshot)
3. **Key Steps/Columns** (enrichment waterfall, AI prompts, conditional logic, integrations)
4. **Tools Stacked** (Clay + Apollo + Smartlead + CRM + n8n + etc.)
5. **Results/Metrics** (reply rates, hours saved, qualified opps generated)
6. **Learnings/Challenges** (data cleaning, prompt iteration, error handling)

### High-Impact Portfolio Projects

1. **Signal-Based Outbound Engine** — "Automated signals-to-pipeline replacing manual SDR research"
2. **AI-Powered Lead Scoring + Routing** — "Turned raw leads into prioritized pipeline with $25k+ potential scoring"
3. **Hyper-Personalized Outreach with RAG** — "Context-aware sequences referencing company initiatives"
4. **Post-Sales Automations** — "Automated handoffs and QBR prep"
5. **Multi-Signal ABM Engine** — "Dynamic tiers + multi-channel orchestration driven by 5 signal types"

### Positioning for Hiring

- Many roles at ~$160k median
- Hiring signals: "built X workflows that drove Y pipeline"
- Take-home assignments or portfolio reviews are common
- Show modular, maintainable builds with error handling and scalability

---

## 10. Tool Stack Reference

### Core Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| **Intelligence** | Clay.com | Central spreadsheet — enrichment, signals, AI, scoring |
| **Data/Enrichment** | Apollo, Crunchbase, HG Insights, BuiltWith | Lead sourcing, funding, technographics |
| **AI** | Claygent (Claude/GPT inside Clay) | Research, personalization, scoring |
| **Sequencing** | Smartlead (primary), Lemlist | Cold email sending, deliverability |
| **CRM** | Salesforce, HubSpot | Pipeline management, routing |
| **Automation** | Zapier, Make, n8n | Webhooks, orchestration, complex routing |
| **Calls** | Gong | Call recording, post-call automation |
| **Intent** | RB2B, Clay Web Intent | Website visitor identification |
| **Advanced AI** | Pinecone (vector search) | RAG for case study matching |
| **Web Scraping** | Firecrawl, Exa, Claygent | Company/competitor research |

### ENT Agency Existing Stack Overlap

| ENT Tool | Clay Equivalent Use |
|----------|-------------------|
| Smartlead | Sequencer (already in use) |
| n8n | Automation/orchestration layer |
| Airtable | CRM/data storage |
| Firecrawl | Web scraping MCP |
| Claude/Anthropic | AI layer (via Claygent or direct) |
| Apollo | Data sourcing (potential Clay enrichment source) |

---

## Quick Reference: Signal Combinations (Power Rankings)

| Combo | Strength | Best Play |
|-------|----------|-----------|
| Job Change + Funding | Very High | "Congrats on the role + fresh capital = perfect timing" |
| Intent + Technographic Gap | Very High | "Saw you're evaluating — here's why we fit your stack" |
| Funding + Hiring Surge | High | "Scaling fast post-raise — we help teams like yours" |
| Champion Job Change + Mutual Investor | Very High | Warm intro via shared investor to new company |
| Distress + Competitor in Stack | High | Empathetic displacement ("We've helped teams in similar spots") |
| Intent + Job Change + Funding | Highest | Triple signal — immediate personalized sequence |
| Growth + Technographic + Intent | Highest | "Your team is scaling, your stack needs X, and you're looking" |

---

---

## 11. Sales Philosophy & Call Framework

Core principles for converting signal-driven pipeline into closed deals. These inform how Claygent writes outreach copy, how sequences are structured, and how calls are run once meetings are booked.

### The 3 Laws

1. **It's about them, not you.** Make it about them → win more than you lose. Make it about you → lose more than you win.
2. **It's them vs. them — you're the referee.** The prospect told you they want this for 20-60 minutes. The pressure is on them to be congruent with what they said. You're not begging.
3. **If you let them talk, they sell themselves.** If you talk, you bore them. 80/20 rule: they talk 80%, you 20%.

### Discovery & Call Control

| Principle | Application |
|-----------|------------|
| Discovery is for **them** to discover about themselves, not for you to interrogate | Ask expansive questions: "Tell me about that?" |
| Never engage in small talk | Ruins call flow, makes you look fake |
| Keep the call sales-focused | Always bring back to qualification or disqualification |
| If prospect asks questions mid-call, defer | "Great question — I'll cover that in a moment" → maintain flow |
| Call out red flags early | They surface again after pricing. Address disqualifiers upfront. |
| Find their "why now" or "f*** it" moment | Something that makes now the right time — this is your signal-to-close bridge |
| Get the cost of inaction | Makes your price look cheap by comparison |

### Closing & Objection Handling

| Principle | Application |
|-----------|------------|
| After dropping price → **shut up** | Silence is leverage |
| Objections are smokescreens | They mask the real concern. Your only job: get the truth. |
| Whoever justifies themselves is losing | Don't defend — redirect |
| Be prepared to walk away | Pulling away draws them into your frame |
| Use negativity to get positivity | "Given how busy you are, is this really the right time?" → they argue FOR it |
| Price drop ≠ begging | It's them vs. them. They already committed 20-60 min. |

### Offer & Positioning

| Principle | Application |
|-----------|------------|
| You can't outsell a bad offer | A bad closer on an amazing offer beats a great closer on a bad one |
| Simplest offer = easiest close | More moving parts → more confusion → longer decision cycle |
| Sell outcomes, not features | Sell the final destination, not the journey there |
| Honesty > sleaze | Honest operators make more money long-term. Harsh truth earns respect. |
| The client is often wrong | Just because they want something doesn't mean you say yes |

### Mindset

- You don't have to be an extrovert. Introverts (listeners) often make the best closers.
- Don't be a suck-up. Nobody likes or respects one.
- When you're up, don't think you're the best. When you're down, don't think you're the worst.
- Boring basics and fundamentals over slick tricks.
- Only care about the best outcome for the prospect.
- Never take it personally.

### How This Maps to Clay/Outbound Systems

| Sales Principle | System Application |
|----------------|-------------------|
| "It's about them" | Claygent prompts grounded in THEIR signals, not your features |
| "Sell outcomes" | Email hooks reference their post-funding challenges, not your product specs |
| "Cost of inaction" | AI research column calculates what doing nothing costs them |
| "Find the why now" | Multi-signal scoring IS the "why now" detector |
| "Simple offer" | One CTA per email. One clear next step. No menus. |
| "80/20 talk ratio" | Discovery calls post-booking should follow this — outbound sets the stage |
| "Call out red flags early" | Scoring formulas should DISQUALIFY as aggressively as they qualify |
| "Objections = smokescreens" | Follow-up sequences address real blockers, not surface objections |

---

## 12. Operational Playbook: Clay + ENT Stack Integration

### How Clay Tables Fit the ENT Agency Stack

```
Clay (Intelligence Layer)
  ├── Enrichment + Signals + Scoring
  ├── Claygent AI Research + Personalization
  └── Export via webhook/API
        ↓
n8n (Orchestration Layer)
  ├── Webhook receivers from Clay exports
  ├── Conditional routing (hot/warm/cold)
  ├── CRM updates + Slack alerts
  └── Sequencer triggers
        ↓
Smartlead (Delivery Layer)        Airtable (CRM Layer)
  ├── Domain rotation              ├── Contact records
  ├── Warmup management            ├── Signal history
  ├── Multi-touch sequences        ├── Campaign tracking
  └── Reply webhooks → n8n         └── Pipeline stages
```

### Clay Table Orchestration Patterns

**Pattern 1: Signal Monitor → n8n → Multi-Channel**
```
Clay signal fires (job change/funding/intent)
  → Webhook to n8n
  → n8n enriches further if needed (Firecrawl, Apollo)
  → Routes by score:
      Hot (>80): Smartlead immediate sequence + Slack alert + Airtable "Engaged"
      Warm (50-80): Smartlead nurture sequence + Airtable "Interested"
      Cold (<50): Airtable "Monitoring" only
```

**Pattern 2: Bulk List Build → Score → Segment → Deploy**
```
Clay table: ICP seed list → waterfall enrichment → multi-signal scoring
  → Export scored CSV
  → n8n imports → segments by tier
  → Tier 1: personalized Smartlead campaign (AI-written per contact)
  → Tier 2: templated Smartlead campaign (segment-level personalization)
  → Tier 3: hold for future signal triggers
```

**Pattern 3: Reply Intelligence Loop**
```
Smartlead reply → webhook → n8n (existing signal workflow)
  → Haiku classifies (positive/negative/question/ooo)
  → Positive: update Airtable → Slack → AE handoff
  → Question: Clay re-enriches contact → AI drafts informed reply
  → Negative: DNC + learn from objection patterns
```

### CRM Integration (Airtable as Hub)

Map Clay outputs to Airtable fields in the Agency CRM (`app9fVT4bBMHlCf2C`):

| Clay Output | Airtable Field | Table |
|-------------|---------------|-------|
| Signal type + details | `Signal_Type`, `Signal_Details` | Contacts / Leads |
| Combined score | `Lead_Score` | Contacts / Leads |
| ABM tier | `ABM_Tier` (Tier 1/2/3) | Brands |
| Claygent research brief | `AI_Research_Brief` | Contacts / Leads |
| Personalized hook | `Outreach_Hook` | Contacts / Leads |
| Funding amount/stage | `Last_Funding`, `Funding_Stage` | Brands |
| Tech stack | `Tech_Stack` | Brands |
| Signal timestamp | `Last_Signal_Date` | Contacts / Leads |

### Paid Ads Integration (Future)

Clay + signal scoring can power ad targeting:

| Play | How It Works |
|------|-------------|
| **Retargeting hot accounts** | Export Tier 1 ABM accounts from Clay → LinkedIn Matched Audiences or Facebook Custom Audiences → run awareness/credibility ads before or alongside email sequences |
| **Lookalike expansion** | Upload closed-won customer list from Airtable → Clay enriches with firmographics/technographics → export to ad platforms as seed for lookalikes |
| **Signal-triggered ad campaigns** | n8n watches for signal clusters → auto-adds matching companies to ad audience lists → coordinated multi-channel (email + ads + LinkedIn) |
| **Content retargeting** | Web intent visitors who don't convert → push to ad audiences for case study / social proof ads |
| **Event-based** | Funding announcements or job changes → targeted ads to the buying committee at those companies |

### List Building Accuracy Method (Proven Pattern)

> Solves the #1 outbound problem: bad lists with wrong contacts.

```
1. Source domains from Disco (or similar) → guaranteed industry match
2. Hit analyze endpoint → returns ALL titles found at those domains
3. Feed AI: offer description + ICP criteria (company size, role focus)
4. AI analyzes all returned titles against ICP context
5. AI selects decision-makers, removes irrelevant contacts
6. Output: clean, high-accuracy list of real decision-makers
```

**Why this works:**
- Industry match is pre-validated (Disco domains, not guessing)
- Title analysis uses real database records, not scraped/inferred data
- AI filtering with ICP + offer context removes false positives
- No manual list cleaning needed

**How to implement in Clay:**
- Column 1: Domain input (from Disco export)
- Column 2: API enrichment → all titles at domain
- Column 3: Claygent → "Given this offer [X] targeting [ICP], which of these titles are decision-makers? Remove irrelevant contacts."
- Column 4: Score remaining contacts
- Export clean list to Smartlead

---

---

## 13. BLUF Cold Email Framework

### What Is BLUF?

BLUF (Bottom Line Up Front) — a 3-line cold email structure. Reader self-qualifies in under 5 seconds.

### The Formula

| Line | Purpose | Pattern |
|------|---------|---------|
| **Line 1** | What you do + proof | `We [outcome] for [ICP] — [credibility signal]` |
| **Line 2** | Who you've done it for | `We've worked with [name-drop or category]` |
| **Line 3** | CTA | One specific, low-friction ask |

### Examples

**SaaS / Outbound:**
```
We book 15–30 qualified demos/month for B2B SaaS teams — without paid ads.
Past clients include Rippling, Deel, and two YC S24 companies.
Worth a 15-min call to see if it's a fit?
```

**Creator / Influencer Agency (ENT-relevant):**
```
We source vetted creators for DTC brands and deliver content that converts — average 4.2x ROAS.
We've run campaigns for LMNT, Momentous, and a handful of Series B health brands.
Open to a quick overview of how we'd approach your next launch?
```

**Backlink / PR Outreach:**
```
I place data-driven stories from B2B SaaS companies in TechCrunch, Fast Company, and niche trades.
Recent placements for Notion, Linear, and a no-code startup with 2k Twitter followers.
Got a story worth telling? Happy to assess it for free.
```

### Variations by Persona

| Persona | Line 1 Tweak | Notes |
|---------|-------------|-------|
| Cold skeptic | Lead with outcome only, no adjectives | Drop "best-in-class", "leading", etc. |
| Warm (viewed your site) | Reference the trigger | "Saw you're hiring for growth..." |
| Re-engage (ghosted) | Cut to Line 3 only | "Still relevant?" |
| Executive | Make Line 2 a peer reference | Drop client count, name the specific company |

### Clay / Claygent Output Mapping

Build one column per line in Clay.

| Clay Column | Claygent Task | Output |
|-------------|--------------|--------|
| `bluf_line1` | Outcome + proof for this prospect's vertical | 1 sentence, no filler |
| `bluf_line2` | Closest relevant client/case study match | 1 sentence, name-drop or category |
| `bluf_line3` | CTA calibrated to company stage | 1 question or soft ask |
| `bluf_full` | Concatenated final email | `{{bluf_line1}} {{bluf_line2}} {{bluf_line3}}` |

### Claygent Prompt for BLUF Output

```
You are writing a 3-line BLUF cold email targeting {{company_name}}.

Context:
- Company: {{company_name}}
- Industry: {{industry}}
- Job title: {{job_title}}
- Known trigger: {{trigger_signal}}

Our offer: [YOUR OFFER + PROOF POINTS]
Reference clients: [3-5 CLIENT NAMES OR CATEGORIES]

Output exactly 3 lines. No subject line. No greeting. No sign-off.

Line 1: What we do + credibility signal relevant to their vertical. One sentence.
Line 2: Name-drop or relevant category of client. One sentence.
Line 3: Low-friction CTA — one question, no exclamation marks.

Return only the 3 lines. Nothing else.
```

**Rules:** Max 25 words per line. CTA must be a question. Never output subject lines, greetings, or signatures — those are handled downstream in Smartlead.

---

## 14. Autonomous Email Agents & Speed-of-Thought GTM Testing

### The Core Insight

> Claude Code + `.env` with Smartlead API key + 2,000 warmed inboxes = test any GTM or PR idea at the speed of thought.

> Agents that run email on your behalf are the most underrated tool in your GTM stack.

### The Stack

| Tool | Role |
|------|------|
| **Apollo.io** | Lead sourcing + contact data |
| **MillionVerifier** | Email validation before send |
| **Smartlead.ai** | Sending infrastructure + inbox warming |
| **Hypertide.io** | Additional lead enrichment / signals |
| **Claude Code / Agent** | Orchestration, copy generation, routing logic |
| **Railway** | Persistent deployment once a motion proves out |

### Workflow: Idea → Test → Scale

```
1. Identify GTM motion to test
        ↓
2. Pull leads (Apollo / Goose scraper prompts / Clay)
        ↓
3. Validate emails (MillionVerifier)
        ↓
4. Generate BLUF copy (Claude Code + Claygent)
        ↓
5. Load into Smartlead campaign
        ↓
6. Run 5-7 days, measure reply rate
        ↓
7. Works → deploy persistent agent on Railway
   Doesn't → kill it, iterate the angle
```

### Use Cases & Success Signals

| Motion | What You're Testing | Signal That It Works |
|--------|--------------------|--------------------|
| Outbound sales | Offer, ICP, angle | >3% positive reply rate |
| Backlink building | Pitch angle, site relevance | >5% link placement rate |
| PR placements | Story hook, journalist fit | Any response from target pub |
| Creator outreach | Brief framing, comp structure | >10% response rate |
| Partnership / co-marketing | Value prop alignment | Meeting booked |

### Persistent Agent on Railway (Post-Validation)

When a test hits signal, deploy it as a persistent agent.

**Agent `.env` minimums:**
```env
SMARTLEAD_API_KEY=
ANTHROPIC_API_KEY=
APOLLO_API_KEY=
MILLIONVERIFIER_API_KEY=
AIRTABLE_API_KEY=
AIRTABLE_BASE_ID=
CAMPAIGN_ID=        # Smartlead campaign to push leads into
```

### High-Intent Lead Scraper Prompts

Use as Claude Code prompts, Goose skills, or Claygent research tasks. Each targets a specific intent signal.

| # | Source | Prompt | Best For | Signal Strength |
|---|--------|--------|----------|----------------|
| 1 | **GitHub Repo Stargazers** | `Find everyone who starred this GitHub repo: [URL]. Get names, companies, job titles, contact info. CSV.` | Dev tools, API products, open-source B2B | Technical interest |
| 2 | **LinkedIn Post Commenters** | `Find everyone who commented on this LinkedIn post: [URL]. Get names, titles, companies, LinkedIn URLs. CSV.` | Thought leadership, community products | Active opinion holder |
| 3 | **Competitor 3-Star Reviews (G2)** | `Find people who left 3-star reviews for [COMPETITOR] on G2. Get names, titles, companies, key pain points. CSV.` | Direct competitor displacement | Unhappy but still in-market |
| 4 | **New Job Starters (ICP)** | `Find people who started a new [TITLE] role in last 30-60 days at [INDUSTRY] companies. Get names, companies, LinkedIn URLs, start dates. CSV.` | Tools new hires evaluate in first 90 days | New budget + mandate |
| 5 | **Conference Speakers** | `Find people speaking at [INDUSTRY] conferences this quarter. Get names, companies, titles, LinkedIn URLs, event name. CSV.` | Enterprise, partnership, co-marketing | High visibility + networking mode |

### Intent Signal → Outreach Angle Map

| Lead Source | BLUF Line 1 Angle |
|-------------|------------------|
| GitHub stargazers | Lead with integration or dev workflow benefit |
| LinkedIn commenters | Reference the topic they engaged with |
| G2 3-star reviews | Lead with the specific pain they named |
| New job starters | "Teams like yours usually tackle X in the first 90 days..." |
| Conference speakers | Reference the event or their talk topic |

---

## 15. B2B List Building System (COLDIQ Framework)

> Source: COLDIQ B2B List Building Masterclass

### Benchmarks

| Metric | Single-Source Baseline | Multi-Source Target |
|--------|----------------------|-------------------|
| Data coverage | 50–60% TAM | 80–90% TAM |
| Email validity | 60–70% | 95%+ |
| List conversion | 1–2% | 5–15% |
| Build time | 8–10 hours | 1–2 hours |

### The 3 Pillars

| Pillar | What It Means | Why It Matters |
|--------|--------------|---------------|
| **Coverage** | Use 2+ data sources for every list | Single source misses 40% of TAM |
| **Enrichment** | Append firmographic, technographic, behavioral data before outreach | Raw lists convert at 1-2%; enriched at 5-15% |
| **Precision** | Tier and score companies; concentrate effort on A-tier | Not all leads are equal |

### 8-Phase Build Process

#### Phase 1 — Define ICP

| Dimension | Examples |
|-----------|---------|
| Firmographics | Industry, headcount, revenue, geography, company age |
| Technographics | Stack in use (CRM, MAP, ESPs, infrastructure) |
| Behavioral signals | Hiring for specific roles, funding rounds, job changes, content engagement |

#### Phase 2 — Multi-Source Company Discovery

| Source | Use Case |
|--------|---------|
| Apollo | Broad company search, industry/size filters |
| LinkedIn Sales Nav | Account-level targeting, department signals |
| Clay | Enrichment hub + scraping orchestration |
| CRM export | Existing accounts, past opps, churned customers |
| Web scraping | Niche directories, review sites, G2, Clutch |
| Ocean.io | Lookalike company discovery |

Coverage math: Apollo ~60-70%, Clay ~60-70%, LinkedIn ~70-80%, with ~40-50% overlap. Combined = 85-92%.

#### Phase 3 — Company Enrichment & Scoring

**Required enrichment fields:**

| Category | Fields |
|----------|--------|
| Firmographic | Revenue, headcount, HQ, founded year |
| Technographic | Tools in use (via BuiltWith, HG Insights, Clay) |
| Funding | Last round, amount, investors, date |
| Hiring | Open roles, department, hiring velocity |

**Tiering:**

| Tier | Criteria | Action |
|------|----------|--------|
| **A** | Exact ICP match + strong signals + decision-maker reachable | Full sequence + manual touch |
| **B** | Partial ICP match + moderate signals | Automated sequence |
| **C** | Low fit or low signal | Nurture only or skip |

#### Phase 4 — People Discovery (Waterfall)

Run in order, stop when found:
1. LinkedIn Sales Navigator
2. Apollo (people search by role + domain)
3. Clay (enrichment + people lookup)
4. Prospeo / Vayne (fallback)

**Target personas by company size:**

| Company Size | Primary | Secondary |
|-------------|---------|-----------|
| 1–50 | Founder / CEO | Head of [function] |
| 51–200 | VP / Director | Manager + C-suite cc |
| 201–1000 | Director / VP | C-suite sponsorship |
| 1000+ | VP / SVP | Champion + executive |

#### Phase 5 — Contact Enrichment & Validation

**Email waterfall:** Apollo → Hunter.io → Prospeo → Findymail → ZeroBounce / MillionVerifier

**Phone waterfall:** Apollo mobile → Lusha → Datagma → Kaspr

**Personalization data per contact:**

| Data Point | Source |
|-----------|--------|
| Recent LinkedIn post | LinkedIn scrape via Clay |
| Job title change (last 90 days) | LinkedIn / Clay |
| Company news / funding | Crunchbase / Clearbit |
| Tech they use | BuiltWith / HG Insights |
| Mutual connection or group | LinkedIn |

#### Phase 6 — Deduplication

| Level | Key Field | Tool |
|-------|----------|------|
| Company | Domain (normalized) | Clay, dedupe formula |
| Contact | Email + LinkedIn URL | Clay, CRM native dedup |

Rules: Normalize domains (strip `www.`, `http://`). Merge on email first, LinkedIn URL as fallback. Flag rather than delete.

#### Phase 7 — Personalization & Segmentation

**Segment variables:** Industry, company size, persona, trigger/signal.

**AI icebreaker rules:**
- Input: LinkedIn post, company news, recent hire, tech stack
- Output: 1-2 sentence custom first line specific to that contact
- Rule: If no real data point exists, use segment-level personalization — **never send a generic opener**

#### Phase 8 — Activation

| Step | Detail |
|------|--------|
| CRM sync | Push to HubSpot/Salesforce with dedup check on import |
| Sequencer load | Smartlead (primary) — separate campaigns by tier |
| Conditional logic | A-tier: manual + automated hybrid; B-tier: full auto; C-tier: excluded or drip only |
| Daily cap | Set sending limits per domain to protect deliverability |

### Golden Rules

1. **Multi-source everything** — 1 provider = 50-60% coverage, 2 = 80-90%
2. **Enrich before outreach** — raw 1-2%, enriched 5-15%
3. **Dedupe religiously** — company AND people level
4. **Validate emails** — 30-40% in databases are invalid
5. **Personalization at scale** — AI + real data, not generic fluff
6. **Test & iterate** — track sources, enrichments, segment performance
7. **Refresh monthly** — data decays 30% per year

### Common Failure Modes

| Mistake | Consequence | Fix |
|---------|------------|-----|
| Single data source | Miss 40% TAM | Layer 2+ sources |
| No enrichment | 1-2% conversion | Enrich all contacts before activation |
| Skip dedup | Duplicate sends, deliverability damage | Dedupe company AND contact level |
| Generic personalization | Low reply rate | Real data points or skip it entirely |
| No email validation | Bounce rate, domain blacklist | Validate with waterfall, target 95%+ |
| Treating all leads equally | Wasted effort | Tier before sequencing |
| Vague ICP | Low precision | Define with all 3 dimensions before Phase 2 |

---

## 16. Outbound Agents Reference (janskuba/outbound-agents)

> Source: github.com/janskuba/outbound-agents — A Claude Code-native B2B outbound pipeline.

### What It Is

7 Claude Code agents (`.md` files) wired by a single slash command (`/outbound-pipeline`). Drop in company names CSV → get enriched data, scored leads, profiles, personalized hooks, and 7-touch sequences ready for sequencer import. **No backend, no database, no API keys beyond Anthropic.**

### Architecture

```
input/companies.csv
  → Signal Scraper (web search enrichment + signal detection)
  → Lead Prioritizer (1-100 score, A/B/C/D tier)
  → Prospect Profiler (60-second actionable profiles)
  → Hook Writer (120-char personalized openers)
  → Sequence Builder (7-touch, 21-day multi-channel)
  → output/5-sequences.csv (ready for Smartlead/Apollo/Outreach)

Standalone agents (run anytime):
  → Reply Classifier (7-category intent classification)
  → Meeting Prep (pre-call briefs under 500 words)
```

### The 7 Agents

| # | Agent | Input | Output | Key Rules |
|---|-------|-------|--------|-----------|
| 1 | **Signal Scraper** | Company names CSV | `0-enriched.csv` + `1-signals.csv` | Only requires `company_name` column. Signal categories: HIRING, FUNDING, TECHNOLOGY, GROWTH, PAIN. Strength: HIGH/MEDIUM/LOW. Skips enrichment if data already complete. |
| 2 | **Lead Prioritizer** | `1-signals.csv` | `2-prioritized.csv` | Scores 1-100: ICP Fit (40pts) + Signal Strength (35pts) + Engagement Potential (25pts). "50% ceiling" rule: missing data caps that dimension at half max. Tiers: TIER_1 (80-100) → TIER_4 (0-39). |
| 3 | **Prospect Profiler** | `2-prioritized.csv` | `3-profiles.csv` | 100-word profile summaries. 3-5 pipe-separated talking points (must be company-specific). Communication style: formal/casual/technical. Recommended approach: `channel: X | message_type: Y | timing: Z`. |
| 4 | **Hook Writer** | `3-profiles.csv` | `4-hooks.csv` | **Max 120 characters.** Banned openers: "I saw," "I noticed," "Congrats on," "Hope you're well." Types: SIGNAL, INSIGHT, PATTERN, CHALLENGE. Confidence scored 1-10; below 6 = NEEDS_REVIEW flag. |
| 5 | **Sequence Builder** | `4-hooks.csv` | `5-sequences.csv` | 7 touches over 21 days. Email body max 80 words. Subject line 5-8 words. Single CTA. No repeated talking points across steps. Multi-channel: Email (D1, D5, D12, D17) + LinkedIn (D3, D8, D21). |
| 6 | **Reply Classifier** | Replies CSV | Classified CSV | 7 categories: INTERESTED, TIMING, OBJECTION, REFERRAL, NOT_INTERESTED, AUTO_REPLY, UNCLEAR. **Never classify ambiguous as NOT_INTERESTED.** Response SLAs: INTERESTED = 2hr, OBJECTION = 24hr, REFERRAL = 24hr. |
| 7 | **Meeting Prep** | Meeting CSV | Prep briefs | Under 500 words. **Anti-BANT:** no budget/authority/need/timeline questions. Discovery: 80% questions / 20% positioning. 30-min agenda: rapport (0-3) → questions (3-15) → positioning (15-22) → next steps (22-27) → recap (27-30). |

### Scoring Framework (Lead Prioritizer Detail)

| Dimension | Points | Components |
|-----------|--------|-----------|
| ICP Fit | 40 | Industry relevance, company size match, tech stack alignment |
| Signal Strength | 35 | Signal recency, diversity of signal types, signal quality |
| Engagement Potential | 25 | LinkedIn activity, approachability indicators |

**Tier assignment:**

| Tier | Score | Action |
|------|-------|--------|
| TIER_1 | 80-100 | Immediate outreach |
| TIER_2 | 60-79 | This week |
| TIER_3 | 40-59 | Nurture |
| TIER_4 | 0-39 | Deprioritize |

### 7-Touch Sequence Structure

| Day | Channel | Purpose |
|-----|---------|---------|
| 1 | Email | Hook-based opener + value prop bridge |
| 3 | LinkedIn | Personalized connection note |
| 5 | Email | New angle + social proof |
| 8 | LinkedIn | Content engagement or monitoring |
| 12 | Email | Pattern interrupt with different pain point |
| 17 | Email | Respectful breakup offer |
| 21 | LinkedIn | Casual voice note prompt |

### ICP Config Schema

Two-column CSV (`field`, `value`):

| Field | Controls |
|-------|---------|
| `product_name` | Sign-offs |
| `product_description` | Tech stack alignment scoring |
| `target_industries` | Industries scored higher |
| `target_company_size_min/max` | Replaces default 50-500 |
| `key_value_props` | Hook + sequence copy (pipe-separated) |
| `common_objections` | Pre-handled in later sequence steps |
| `case_studies` | Social proof in emails (pipe-separated) |
| `sender_name/title/company` | Email sign-offs |

### Cost & Performance

| Companies | With Enrichment | Without | Cost |
|-----------|----------------|---------|------|
| 5 | 3-5 min | 2-3 min | $0.15-0.50 |
| 25 | 10-15 min | 8-12 min | $0.75-2.50 |
| 50 | 20-30 min | 15-20 min | $1.50-5.00 |

### Key Architectural Patterns

1. **Agents as `.md` files** — trivially editable, no code required
2. **CSV-native I/O** — every stage reads numbered CSV, writes next one
3. **Slash command as orchestrator** — `/outbound-pipeline` sequences agents + handles pause-for-review
4. **Optional enrichment skip** — if input data complete, web search bypassed automatically
5. **Clay integration** — Clay handles structured API enrichment; this system handles interpretation + copy generation
6. **API injection** — swap web search for Apollo/Clearbit/PDL by adding `Bash` to agent tools + curl calls
7. **Standalone agents** — Reply Classifier + Meeting Prep run independently, not just in pipeline

### Sequencer Export Mapping

| Tool | Mapping |
|------|---------|
| **Smartlead** | `body` → Email Body, `subject` → Subject Line; filter `channel`=Email |
| **Apollo** | `subject` → Subject, `body` → Body, `day` → Send Day |
| **Outreach.io** | `step_number` → Step Order, `channel` → Step Type, `day` → Day |
| **LinkedIn steps** | Always manual tasks across all tools |

---

*Last updated: 2026-04-03*
*Sources: Grok research (Clay.com, GTM engineering, signal-based outbound), field-tested sales principles, COLDIQ B2B List Building Masterclass, janskuba/outbound-agents*
