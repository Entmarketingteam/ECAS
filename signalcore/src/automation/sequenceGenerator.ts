// src/automation/sequenceGenerator.ts
// Uses Claude API to generate signal-aware, personalized email + LI copy per lead.
// Inherits voice/positioning from ECAS Brand GTM docs.

import { EnrichedLead } from '../types.js';

export interface GeneratedSequence {
  email: string;
  company_name: string;
  signal_tier: string;
  emails: GeneratedEmail[];
  linkedin: GeneratedLinkedIn;
}

export interface GeneratedEmail {
  step: number;
  subject: string;
  body: string;
  delay_days: number;
}

export interface GeneratedLinkedIn {
  connection_note: string;
  first_dm: string;
  follow_up_dm: string;
}

export interface LLMClient {
  generate(prompt: string): Promise<string>;
}

export class SequenceGenerator {
  private llm: LLMClient;
  private brandContext: string;

  constructor(llm: LLMClient, brandContext?: string) {
    this.llm = llm;
    this.brandContext = brandContext ?? DEFAULT_BRAND_CONTEXT;
  }

  async generateForLead(lead: EnrichedLead): Promise<GeneratedSequence> {
    const prompt = this.buildPrompt(lead);
    const raw = await this.llm.generate(prompt);
    return this.parseResponse(lead, raw);
  }

  async generateBatch(leads: EnrichedLead[]): Promise<GeneratedSequence[]> {
    const results: GeneratedSequence[] = [];
    for (const lead of leads) {
      const seq = await this.generateForLead(lead);
      results.push(seq);
    }
    return results;
  }

  private buildPrompt(lead: EnrichedLead): string {
    return `${this.brandContext}

LEAD CONTEXT:
- Name: ${lead.first_name} ${lead.last_name}
- Title: ${lead.title}
- Company: ${lead.company_name} (${lead.company_domain})
- Signal Score: ${lead.signal_score} (${lead.signal_tier})
- Top Signals: ${lead.top_signals.join(', ')}
- BD Jobs Open: ${lead.bd_jobs_last_90_days}
- Recent Contract News: ${lead.recent_contract_news ? 'Yes' : 'No'}
- Recent DC/SMR News: ${lead.recent_dc_or_smr_news ? 'Yes' : 'No'}
- Event Exhibitor: ${lead.is_event_exhibitor ? lead.event_name : 'No'}
- Days in Role: ${lead.days_in_role ?? 'Unknown'}

TASK: Write a 2-email cold sequence + 3-touch LinkedIn sequence for this lead.

EMAIL RULES:
- Under 75 words per email
- Subject line under 4 words
- Reference specific signals from the lead context above
- No enthusiasm, no superlatives, no agency language
- Lead with the signal, not the pitch
- Email 1: signal-based opener. Email 2: follow-up 3 days later.

LINKEDIN RULES:
- Connection note: under 200 characters, no pitch, reference a signal
- First DM (day 3): value message, open-ended, no pitch
- Follow-up DM (day 7): soft pitch tied to the same angle

OUTPUT FORMAT (respond with ONLY this JSON, no other text):
{
  "emails": [
    {"step": 1, "subject": "...", "body": "...", "delay_days": 0},
    {"step": 2, "subject": "...", "body": "...", "delay_days": 3}
  ],
  "linkedin": {
    "connection_note": "...",
    "first_dm": "...",
    "follow_up_dm": "..."
  }
}`;
  }

  private parseResponse(lead: EnrichedLead, raw: string): GeneratedSequence {
    const jsonMatch = raw.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      return this.fallbackSequence(lead);
    }

    try {
      const parsed = JSON.parse(jsonMatch[0]) as {
        emails: GeneratedEmail[];
        linkedin: GeneratedLinkedIn;
      };

      return {
        email: lead.email ?? '',
        company_name: lead.company_name,
        signal_tier: lead.signal_tier,
        emails: parsed.emails,
        linkedin: parsed.linkedin,
      };
    } catch {
      return this.fallbackSequence(lead);
    }
  }

  private fallbackSequence(lead: EnrichedLead): GeneratedSequence {
    const topSignal = lead.top_signals[0] ?? 'recent activity in your market';
    return {
      email: lead.email ?? '',
      company_name: lead.company_name,
      signal_tier: lead.signal_tier,
      emails: [
        {
          step: 1,
          subject: lead.company_name,
          body: `${lead.first_name} — noticed ${topSignal}. We monitor the same data sources and position contractors before formal procurement opens. Worth a 10-minute look at what we're seeing in your market?`,
          delay_days: 0,
        },
        {
          step: 2,
          subject: 'Re: signal data',
          body: `${lead.first_name} — following up. We mapped 5 active projects in your region that haven't hit formal RFP yet. Happy to share the list if useful.`,
          delay_days: 3,
        },
      ],
      linkedin: {
        connection_note: `${lead.first_name} — saw ${topSignal}. Following your work at ${lead.company_name}.`,
        first_dm: `${lead.first_name} — we've been tracking signal activity in your market. Seeing some interesting pre-RFP movement. Thought you'd want to know.`,
        follow_up_dm: `${lead.first_name} — we mapped the procurement contacts on 5 projects in your region. Happy to share if it's useful for ${lead.company_name}.`,
      },
    };
  }
}

const DEFAULT_BRAND_CONTEXT = `BRAND VOICE: ECAS (Enterprise Contract Acquisition System)
- Flat, factual, technically grounded. Insider industry speech.
- No enthusiasm, no superlatives, no agency language.
- Use: interconnection queue, FERC docket, pre-bid window, signed contract.
- Avoid: growth, scale, leads, outreach, campaign, content, excited, innovative.
- Sentences are short. Subject. Verb. Object. Done.
- Specificity carries the sentence. Name the utility, the voltage, the filing.
- The metric is signed contracts, not meetings.
- Guarantee: 2 signed enterprise contracts ($500K+) in 180 days or we continue at no charge.`;
