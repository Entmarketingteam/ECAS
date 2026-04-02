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
6. **Export:** One-click to Instantly/Smartlead or webhook to CRM
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
4. **Tools Stacked** (Clay + Apollo + Instantly + CRM + n8n + etc.)
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
| **Sequencing** | Instantly, Smartlead, Lemlist | Cold email sending, deliverability |
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

*Last updated: 2026-04-02*
*Source: Grok research synthesis on Clay.com, GTM engineering, and signal-based outbound*
