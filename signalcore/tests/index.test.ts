import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import { run } from '../src/index';
import { NewsFetcher } from '../src/agents/newsAgent';
import { HiringFetcher, JobRecord } from '../src/agents/hiringAgent';
import { SocialFetcher, PostRecord } from '../src/agents/socialAgent';

const TMP_DIR = path.resolve('tests/.tmp');
const INPUT_PATH = path.join(TMP_DIR, 'accounts.json');
const OUTPUT_DIR = path.join(TMP_DIR, 'output');
const EVENTS_DIR = path.join(TMP_DIR, 'events');
const CONFIG_PATH = path.join(TMP_DIR, 'config.json');

function daysAgo(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().split('T')[0];
}

const sampleAccounts = [
  {
    first_name: 'Jane',
    last_name: 'Doe',
    title: 'VP Business Development',
    linkedin_profile_url: 'https://linkedin.com/in/janedoe',
    company_name: 'Hot Corp',
    company_domain: 'hotcorp.com',
    job_change_date: daysAgo(30),
    email: 'jane@hotcorp.com',
  },
  {
    first_name: 'Bob',
    last_name: 'Smith',
    title: 'Software Engineer',
    linkedin_profile_url: 'https://linkedin.com/in/bobsmith',
    company_name: 'Cold Inc',
    company_domain: 'coldinc.com',
    email: 'bob@coldinc.com',
  },
  {
    first_name: 'Alice',
    last_name: 'Johnson',
    title: 'CEO',
    linkedin_profile_url: 'https://linkedin.com/in/alicejohnson',
    company_name: 'Warm LLC',
    company_domain: 'warmllc.com',
    job_change_date: daysAgo(60),
    email: 'alice@warmllc.com',
  },
  {
    first_name: 'Tom',
    last_name: 'Brown',
    title: 'Director of Sales',
    linkedin_profile_url: 'https://linkedin.com/in/tombrown',
    company_name: 'Hot Corp',
    company_domain: 'hotcorp.com',
    job_change_date: daysAgo(20),
    email: 'tom@hotcorp.com',
  },
  {
    first_name: 'Eve',
    last_name: 'Wilson',
    title: 'CRO',
    linkedin_profile_url: 'https://linkedin.com/in/evewilson',
    company_name: 'Warm LLC',
    company_domain: 'warmllc.com',
    email: 'eve@warmllc.com',
  },
];

const mockNewsFetcher: NewsFetcher = {
  fetchNews: async (domain) => {
    if (domain === 'hotcorp.com') {
      return [
        'Hot Corp awarded major data center contract',
        'Hot Corp breaks ground on new hyperscale campus',
      ];
    }
    if (domain === 'warmllc.com') {
      return ['Warm LLC signs MoU for SMR project'];
    }
    return [];
  },
};

const mockHiringFetcher: HiringFetcher = {
  fetchJobs: async (domain) => {
    if (domain === 'hotcorp.com') {
      return [
        { title: 'Business Development Manager', posted_date: daysAgo(10) },
        { title: 'Sales Director', posted_date: daysAgo(20) },
        { title: 'Capture Manager', posted_date: daysAgo(30) },
        { title: 'Proposal Writer', posted_date: daysAgo(40) },
        { title: 'Software Engineer', posted_date: daysAgo(5) },
      ] satisfies JobRecord[];
    }
    return [];
  },
};

const mockSocialFetcher: SocialFetcher = {
  fetchPosts: async (url) => {
    if (url === 'https://linkedin.com/in/janedoe') {
      return [
        { text: 'Excited about our data center expansion!', date: new Date(Date.now() - 5 * 86400000).toISOString() },
        { text: 'Great pipeline growth ahead', date: new Date(Date.now() - 10 * 86400000).toISOString() },
        { text: 'Weekend vibes', date: new Date(Date.now() - 15 * 86400000).toISOString() },
      ] satisfies PostRecord[];
    }
    return [];
  },
};

describe('Integration: run()', () => {
  beforeEach(() => {
    fs.mkdirSync(TMP_DIR, { recursive: true });
    fs.mkdirSync(EVENTS_DIR, { recursive: true });
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });

    fs.writeFileSync(INPUT_PATH, JSON.stringify(sampleAccounts));

    fs.writeFileSync(path.join(EVENTS_DIR, 'dcworld2026.csv'),
      `company_name,company_domain,event_name\nHot Corp,hotcorp.com,Data Center World 2026\n`);

    fs.writeFileSync(CONFIG_PATH, JSON.stringify({
      inputPath: INPUT_PATH,
      outputDir: OUTPUT_DIR,
      eventsDir: EVENTS_DIR,
      keywords: ['data center', 'SMR', 'hyperscale'],
      rateLimitMs: 0,
    }));
  });

  afterEach(() => {
    fs.rmSync(TMP_DIR, { recursive: true, force: true });
  });

  it('enriches 5 accounts and produces output files', async () => {
    const results = await run({
      inputPath: INPUT_PATH,
      outputDir: OUTPUT_DIR,
      configPath: CONFIG_PATH,
      newsFetcher: mockNewsFetcher,
      hiringFetcher: mockHiringFetcher,
      socialFetcher: mockSocialFetcher,
    });

    expect(results).toHaveLength(5);

    // Verify output files exist
    expect(fs.existsSync(path.join(OUTPUT_DIR, 'enriched_leads.json'))).toBe(true);
    expect(fs.existsSync(path.join(OUTPUT_DIR, 'enriched_leads.csv'))).toBe(true);
    expect(fs.existsSync(path.join(OUTPUT_DIR, 'smartlead_hot.csv'))).toBe(true);
  });

  it('assigns Hot tier to at least one lead', async () => {
    const results = await run({
      inputPath: INPUT_PATH,
      outputDir: OUTPUT_DIR,
      configPath: CONFIG_PATH,
      newsFetcher: mockNewsFetcher,
      hiringFetcher: mockHiringFetcher,
      socialFetcher: mockSocialFetcher,
    });

    const hot = results.filter(r => r.signal_tier === 'Hot');
    expect(hot.length).toBeGreaterThanOrEqual(1);
  });

  it('smartlead_hot.csv only contains Hot leads', async () => {
    const results = await run({
      inputPath: INPUT_PATH,
      outputDir: OUTPUT_DIR,
      configPath: CONFIG_PATH,
      newsFetcher: mockNewsFetcher,
      hiringFetcher: mockHiringFetcher,
      socialFetcher: mockSocialFetcher,
    });

    const hotCsv = fs.readFileSync(path.join(OUTPUT_DIR, 'smartlead_hot.csv'), 'utf-8');
    const hot = results.filter(r => r.signal_tier === 'Hot');

    if (hot.length === 0) {
      expect(hotCsv).toBe('');
    } else {
      // CSV should have header + hot.length data rows
      const lines = hotCsv.split('\n').filter(Boolean);
      expect(lines.length).toBe(hot.length + 1); // +1 for header
    }
  });

  it('throws on missing input file', async () => {
    await expect(run({
      inputPath: '/nonexistent/path.json',
      outputDir: OUTPUT_DIR,
      configPath: CONFIG_PATH,
    })).rejects.toThrow('Input file not found');
  });

  it('throws on malformed JSON', async () => {
    fs.writeFileSync(INPUT_PATH, '{ not valid json !!!');
    await expect(run({
      inputPath: INPUT_PATH,
      outputDir: OUTPUT_DIR,
      configPath: CONFIG_PATH,
    })).rejects.toThrow('Malformed JSON');
  });
});
