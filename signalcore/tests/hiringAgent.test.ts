import { describe, it, expect } from 'vitest';
import { HiringAgent, HiringFetcher, JobRecord } from '../src/agents/hiringAgent';

function makeFetcher(map: Record<string, JobRecord[]>): HiringFetcher {
  return { fetchJobs: async (domain) => map[domain] ?? [] };
}

function daysAgo(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().split('T')[0];
}

describe('HiringAgent', () => {
  it('counts BD jobs within 90-day window', async () => {
    const agent = new HiringAgent(makeFetcher({
      'techco.com': [
        { title: 'Sr. Business Development Manager', posted_date: daysAgo(10) },
        { title: 'Sales Director', posted_date: daysAgo(30) },
        { title: 'Capture Manager', posted_date: daysAgo(50) },
        { title: 'Software Engineer', posted_date: daysAgo(5) },
        { title: 'Data Analyst', posted_date: daysAgo(20) },
      ],
    }));

    const results = await agent.fetchForCompanies(['techco.com']);
    expect(results[0].bd_jobs_last_90_days).toBe(3);
    expect(results[0].total_open_jobs).toBe(5);
  });

  it('returns 0 for no jobs', async () => {
    const agent = new HiringAgent(makeFetcher({}));
    const results = await agent.fetchForCompanies(['empty.com']);
    expect(results[0].bd_jobs_last_90_days).toBe(0);
    expect(results[0].total_open_jobs).toBe(0);
  });

  it('ignores BD jobs older than 90 days', async () => {
    const agent = new HiringAgent(makeFetcher({
      'old.com': [
        { title: 'Business Development Rep', posted_date: daysAgo(100) },
        { title: 'Partnerships Lead', posted_date: daysAgo(120) },
        { title: 'Software Engineer', posted_date: daysAgo(5) },
      ],
    }));

    const results = await agent.fetchForCompanies(['old.com']);
    expect(results[0].bd_jobs_last_90_days).toBe(0);
    expect(results[0].total_open_jobs).toBe(3);
  });
});
