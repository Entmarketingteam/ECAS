import { describe, it, expect } from 'vitest';
import { NewsAgent, NewsFetcher } from '../src/agents/newsAgent';

function makeFetcher(map: Record<string, string[]>): NewsFetcher {
  return { fetchNews: async (domain) => map[domain] ?? [] };
}

describe('NewsAgent', () => {
  const keywords = ['data center', 'SMR'];

  it('detects contract and DC/SMR news', async () => {
    const agent = new NewsAgent(keywords, makeFetcher({
      'example.com': [
        'Example Corp awarded a contract for new data center build',
        'Example Corp selected by AWS for data center expansion',
      ],
    }));

    const results = await agent.fetchForCompanies(['example.com']);
    expect(results).toHaveLength(1);
    expect(results[0].recent_contract_news).toBe(1);
    expect(results[0].recent_dc_or_smr_news).toBe(1);
    expect(results[0].example_headlines.length).toBeGreaterThan(0);
  });

  it('returns 0 for irrelevant news', async () => {
    const agent = new NewsAgent(keywords, makeFetcher({
      'boring.com': [
        'Company announces holiday donation drive',
        'Team building event held last week',
      ],
    }));

    const results = await agent.fetchForCompanies(['boring.com']);
    expect(results[0].recent_contract_news).toBe(0);
    expect(results[0].recent_dc_or_smr_news).toBe(0);
    expect(results[0].example_headlines).toHaveLength(0);
  });

  it('handles multiple PRs correctly', async () => {
    const agent = new NewsAgent(keywords, makeFetcher({
      'multi.com': [
        'Multi Corp breaks ground on new data center campus',
        'Multi Corp signs framework agreement with utility partner',
        'Multi Corp quarterly earnings call',
      ],
    }));

    const results = await agent.fetchForCompanies(['multi.com']);
    expect(results[0].recent_contract_news).toBe(1); // framework agreement
    expect(results[0].recent_dc_or_smr_news).toBe(1); // data center campus
  });

  it('handles empty news', async () => {
    const agent = new NewsAgent(keywords, makeFetcher({}));
    const results = await agent.fetchForCompanies(['nonews.com']);
    expect(results[0].recent_contract_news).toBe(0);
    expect(results[0].recent_dc_or_smr_news).toBe(0);
  });
});
