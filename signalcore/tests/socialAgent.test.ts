import { describe, it, expect } from 'vitest';
import { SocialAgent, SocialFetcher, PostRecord } from '../src/agents/socialAgent';

function makeFetcher(map: Record<string, PostRecord[]>): SocialFetcher {
  return { fetchPosts: async (url) => map[url] ?? [] };
}

function daysAgo(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString();
}

describe('SocialAgent', () => {
  it('counts posts and growth posts within 30 days', async () => {
    const agent = new SocialAgent(makeFetcher({
      'https://linkedin.com/in/janedoe': [
        { text: 'Excited about our data center expansion!', date: daysAgo(5) },
        { text: 'Great team dinner last night', date: daysAgo(10) },
        { text: 'Thrilled to land a new contract for hyperscale build', date: daysAgo(15) },
        { text: 'Weekend hiking trip', date: daysAgo(20) },
        { text: 'Big pipeline growth ahead for our team', date: daysAgo(25) },
      ],
    }));

    const results = await agent.fetchForProfiles(['https://linkedin.com/in/janedoe']);
    expect(results[0].posts_last_30_days).toBe(5);
    expect(results[0].growth_posts_last_30_days).toBe(3); // data center, contract, pipeline/growth
  });

  it('returns 0 for no posts', async () => {
    const agent = new SocialAgent(makeFetcher({}));
    const results = await agent.fetchForProfiles(['https://linkedin.com/in/nobody']);
    expect(results[0].posts_last_30_days).toBe(0);
    expect(results[0].growth_posts_last_30_days).toBe(0);
  });

  it('excludes posts older than 30 days', async () => {
    const agent = new SocialAgent(makeFetcher({
      'https://linkedin.com/in/oldposter': [
        { text: 'Major expansion announcement', date: daysAgo(35) },
        { text: 'Growth is incredible this quarter', date: daysAgo(60) },
      ],
    }));

    const results = await agent.fetchForProfiles(['https://linkedin.com/in/oldposter']);
    expect(results[0].posts_last_30_days).toBe(0);
    expect(results[0].growth_posts_last_30_days).toBe(0);
  });
});
