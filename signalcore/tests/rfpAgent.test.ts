import { describe, it, expect } from 'vitest';
import { RFPAgent, RFPFetcher, RawRFP } from '../src/agents/rfpAgent';

function makeFetcher(rfps: RawRFP[]): RFPFetcher {
  return { fetchRFPs: async () => rfps };
}

describe('RFPAgent', () => {
  const keywords = ['data center', 'hyperscale', 'SMR', 'critical power'];

  it('parses and returns matching RFPs', async () => {
    const agent = new RFPAgent(keywords, makeFetcher([
      { buyer: 'DOE', title: 'Data Center Expansion RFI', url: 'https://sam.gov/1', text_snippet: 'Build a hyperscale data center facility' },
      { buyer: 'GSA', title: 'Solar Panel Install', url: 'https://sam.gov/2', text_snippet: 'Solar panel installation for office building' },
      { buyer: 'DoD', title: 'SMR Feasibility Study', url: 'https://sam.gov/3', text_snippet: 'Evaluate small modular reactor for base power' },
    ]));

    const results = await agent.fetch();
    expect(results).toHaveLength(2);
    expect(results[0].title).toBe('Data Center Expansion RFI');
    expect(results[1].title).toBe('SMR Feasibility Study');
  });

  it('filters by keyword list', async () => {
    const agent = new RFPAgent(['office cleaning'], makeFetcher([
      { buyer: 'DOE', title: 'Data Center Expansion', url: 'https://sam.gov/1', text_snippet: 'Build a new data center' },
      { buyer: 'GSA', title: 'Office Cleaning Services', url: 'https://sam.gov/2', text_snippet: 'Office cleaning for federal building' },
    ]));

    const results = await agent.fetch();
    expect(results).toHaveLength(1);
    expect(results[0].title).toBe('Office Cleaning Services');
  });

  it('returns empty array when fetcher fails', async () => {
    const failFetcher: RFPFetcher = {
      fetchRFPs: async () => { throw new Error('Network error'); },
    };

    const agent = new RFPAgent(keywords, failFetcher);
    await expect(agent.fetch()).rejects.toThrow('Network error');
  });

  it('returns empty when no RFPs match', async () => {
    const agent = new RFPAgent(keywords, makeFetcher([
      { buyer: 'GSA', title: 'Carpet Replacement', url: 'https://sam.gov/1', text_snippet: 'Replace carpets in office' },
    ]));

    const results = await agent.fetch();
    expect(results).toHaveLength(0);
  });
});
