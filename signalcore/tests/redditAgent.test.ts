import { describe, it, expect } from 'vitest';
import { RedditAgent, RedditFetcher, F5BotAlert } from '../src/agents/redditAgent';

function daysAgo(n: number): string {
  return new Date(Date.now() - n * 86400000).toISOString();
}

function makeAlerts(overrides: Partial<F5BotAlert>[]): F5BotAlert[] {
  return overrides.map((o, i) => ({
    title: `Post ${i}`,
    body: '',
    url: `https://reddit.com/r/datacenter/post${i}`,
    subreddit: 'datacenter',
    date: daysAgo(5),
    keyword: 'data center',
    ...o,
  }));
}

const DC_KEYWORDS = ['data center', 'SMR', 'hyperscale', 'nuclear'];

describe('RedditAgent', () => {
  it('matches alerts to company by name and counts mentions', async () => {
    const fetcher: RedditFetcher = {
      fetchAlerts: async () => makeAlerts([
        { title: 'Hot Corp just landed a massive data center contract', body: 'Details inside', date: daysAgo(2) },
        { title: 'Hot Corp expands again', body: 'New hyperscale campus', date: daysAgo(10) },
        { title: 'Unrelated post about cooking', body: 'Nothing relevant', date: daysAgo(3) },
      ]),
    };

    const companyMap = new Map([['hotcorp.com', ['Hot Corp']]]);
    const agent = new RedditAgent(companyMap, DC_KEYWORDS, fetcher);
    const results = await agent.fetchForCompanies(['hotcorp.com', 'coldinc.com']);

    const hot = results.find(r => r.company_domain === 'hotcorp.com')!;
    expect(hot.reddit_mentions_last_30_days).toBe(2);
    expect(hot.reddit_keyword_mentions).toBe(2); // both mention DC keywords
    expect(hot.top_reddit_urls).toHaveLength(2);

    const cold = results.find(r => r.company_domain === 'coldinc.com')!;
    expect(cold.reddit_mentions_last_30_days).toBe(0);
  });

  it('filters out alerts older than 30 days', async () => {
    const fetcher: RedditFetcher = {
      fetchAlerts: async () => makeAlerts([
        { title: 'Hot Corp old news', body: 'data center', date: daysAgo(45) },
        { title: 'Hot Corp recent news', body: 'data center', date: daysAgo(5) },
      ]),
    };

    const companyMap = new Map([['hotcorp.com', ['Hot Corp']]]);
    const agent = new RedditAgent(companyMap, DC_KEYWORDS, fetcher);
    const results = await agent.fetchForCompanies(['hotcorp.com']);

    expect(results[0].reddit_mentions_last_30_days).toBe(1);
  });

  it('counts keyword mentions separately from total mentions', async () => {
    const fetcher: RedditFetcher = {
      fetchAlerts: async () => makeAlerts([
        { title: 'Hot Corp data center expansion', body: '', date: daysAgo(2) },
        { title: 'Hot Corp CEO interview on leadership', body: 'no keywords', date: daysAgo(3) },
        { title: 'Hot Corp SMR partnership announced', body: '', date: daysAgo(7) },
      ]),
    };

    const companyMap = new Map([['hotcorp.com', ['Hot Corp']]]);
    const agent = new RedditAgent(companyMap, DC_KEYWORDS, fetcher);
    const results = await agent.fetchForCompanies(['hotcorp.com']);

    expect(results[0].reddit_mentions_last_30_days).toBe(3);
    expect(results[0].reddit_keyword_mentions).toBe(2); // DC + SMR, not the leadership one
  });

  it('returns empty signals when no fetcher configured', async () => {
    const agent = new RedditAgent(new Map(), DC_KEYWORDS);
    const results = await agent.fetchForCompanies(['hotcorp.com']);

    expect(results[0].reddit_mentions_last_30_days).toBe(0);
    expect(results[0].reddit_keyword_mentions).toBe(0);
    expect(results[0].top_reddit_urls).toEqual([]);
  });

  it('handles fetch errors gracefully', async () => {
    const fetcher: RedditFetcher = {
      fetchAlerts: async () => { throw new Error('network fail'); },
    };

    const agent = new RedditAgent(new Map(), DC_KEYWORDS, fetcher);
    const results = await agent.fetchForCompanies(['hotcorp.com']);

    expect(results[0].reddit_mentions_last_30_days).toBe(0);
  });

  it('limits top_reddit_urls to 5', async () => {
    const alerts = Array.from({ length: 8 }, (_, i) =>
      ({ title: `Hot Corp post ${i}`, body: 'data center', url: `https://reddit.com/r/dc/${i}`, date: daysAgo(i + 1), keyword: 'data center', subreddit: 'datacenter' })
    );
    const fetcher: RedditFetcher = { fetchAlerts: async () => alerts };

    const companyMap = new Map([['hotcorp.com', ['Hot Corp']]]);
    const agent = new RedditAgent(companyMap, DC_KEYWORDS, fetcher);
    const results = await agent.fetchForCompanies(['hotcorp.com']);

    expect(results[0].reddit_mentions_last_30_days).toBe(8);
    expect(results[0].top_reddit_urls).toHaveLength(5);
  });

  it('buildCompanyKeywords creates map from contacts', () => {
    const contacts = [
      { company_domain: 'hotcorp.com', company_name: 'Hot Corp' },
      { company_domain: 'hotcorp.com', company_name: 'Hot Corp' }, // dupe
      { company_domain: 'coldinc.com', company_name: 'Cold Inc' },
    ];

    const map = RedditAgent.buildCompanyKeywords(contacts);
    expect(map.get('hotcorp.com')).toEqual(['Hot Corp']);
    expect(map.get('coldinc.com')).toEqual(['Cold Inc']);
  });
});
