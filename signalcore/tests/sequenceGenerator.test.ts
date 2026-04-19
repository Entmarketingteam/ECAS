import { describe, it, expect } from 'vitest';
import { SequenceGenerator, LLMClient } from '../src/automation/sequenceGenerator';
import { EnrichedLead } from '../src/types';

function makeLead(): EnrichedLead {
  return {
    first_name: 'Jane',
    last_name: 'Doe',
    title: 'VP Business Development',
    linkedin_profile_url: 'https://linkedin.com/in/janedoe',
    company_name: 'Example Data Center Corp',
    company_domain: 'exampledatacenter.com',
    email: 'jane@exampledatacenter.com',
    bd_jobs_last_90_days: 4,
    total_open_jobs: 12,
    recent_contract_news: 1,
    recent_dc_or_smr_news: 1,
    posts_last_30_days: 5,
    growth_posts_last_30_days: 2,
    is_event_exhibitor: 1,
    event_name: 'Data Center World 2026',
    reddit_mentions_last_30_days: 3,
    reddit_keyword_mentions: 2,
    top_reddit_urls: [],
    days_in_role: 45,
    signal_score: 15,
    signal_tier: 'Hot',
    top_signals: ['New VP BD < 90 days', '4 BD roles open', 'Recent contract/award PR'],
  };
}

function makeMockLLM(response: string): LLMClient {
  return { generate: async () => response };
}

describe('SequenceGenerator', () => {
  it('parses valid LLM JSON response', async () => {
    const llmResponse = JSON.stringify({
      emails: [
        { step: 1, subject: 'Saw the filing', body: 'Jane — noticed the contract award.', delay_days: 0 },
        { step: 2, subject: 'Re: filing', body: 'Jane — following up on the data.', delay_days: 3 },
      ],
      linkedin: {
        connection_note: 'Jane — saw the contract news at Example DC Corp.',
        first_dm: 'Jane — we track the same data sources you do.',
        follow_up_dm: 'Jane — mapped 5 projects in your region.',
      },
    });

    const gen = new SequenceGenerator(makeMockLLM(llmResponse));
    const result = await gen.generateForLead(makeLead());

    expect(result.emails).toHaveLength(2);
    expect(result.emails[0].subject).toBe('Saw the filing');
    expect(result.linkedin.connection_note).toContain('Jane');
    expect(result.company_name).toBe('Example Data Center Corp');
  });

  it('falls back gracefully on invalid LLM response', async () => {
    const gen = new SequenceGenerator(makeMockLLM('Sorry, I cannot help with that.'));
    const result = await gen.generateForLead(makeLead());

    expect(result.emails).toHaveLength(2);
    expect(result.emails[0].body).toContain('Jane');
    expect(result.linkedin.connection_note.length).toBeGreaterThan(0);
  });

  it('falls back on malformed JSON', async () => {
    const gen = new SequenceGenerator(makeMockLLM('{ broken json !!!'));
    const result = await gen.generateForLead(makeLead());

    expect(result.emails).toHaveLength(2);
    expect(result.signal_tier).toBe('Hot');
  });

  it('generates batch for multiple leads', async () => {
    const validResponse = JSON.stringify({
      emails: [
        { step: 1, subject: 'Test', body: 'Test body', delay_days: 0 },
        { step: 2, subject: 'Re: test', body: 'Follow up', delay_days: 3 },
      ],
      linkedin: {
        connection_note: 'Note',
        first_dm: 'DM 1',
        follow_up_dm: 'DM 2',
      },
    });

    const gen = new SequenceGenerator(makeMockLLM(validResponse));
    const results = await gen.generateBatch([makeLead(), makeLead()]);

    expect(results).toHaveLength(2);
  });

  it('includes lead signals in prompt context', async () => {
    let capturedPrompt = '';
    const llm: LLMClient = {
      generate: async (prompt) => {
        capturedPrompt = prompt;
        return '{}';
      },
    };

    const gen = new SequenceGenerator(llm);
    await gen.generateForLead(makeLead());

    expect(capturedPrompt).toContain('VP Business Development');
    expect(capturedPrompt).toContain('Example Data Center Corp');
    expect(capturedPrompt).toContain('4 BD roles open');
    expect(capturedPrompt).toContain('Data Center World 2026');
  });
});
