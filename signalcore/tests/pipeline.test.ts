import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import { runPipeline } from '../src/automation/pipeline';
import { SmartleadAPI, SmartleadLeadPayload } from '../src/automation/smartleadClient';
import { LLMClient } from '../src/automation/sequenceGenerator';
import { CRMClient, CRMContact, CRMDeal } from '../src/automation/crmSync';
import { NewsFetcher } from '../src/agents/newsAgent';
import { HiringFetcher } from '../src/agents/hiringAgent';
import { SocialFetcher } from '../src/agents/socialAgent';
import { RedditFetcher } from '../src/agents/redditAgent';

const TMP_DIR = path.resolve('tests/.tmp-pipeline');
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
    first_name: 'Jane', last_name: 'Doe', title: 'VP Business Development',
    linkedin_profile_url: 'https://linkedin.com/in/janedoe',
    company_name: 'Hot Corp', company_domain: 'hotcorp.com',
    job_change_date: daysAgo(30), email: 'jane@hotcorp.com',
  },
  {
    first_name: 'Bob', last_name: 'Smith', title: 'Software Engineer',
    linkedin_profile_url: 'https://linkedin.com/in/bobsmith',
    company_name: 'Cold Inc', company_domain: 'coldinc.com',
    email: 'bob@coldinc.com',
  },
];

const mockNewsFetcher: NewsFetcher = {
  fetchNews: async (domain) => domain === 'hotcorp.com'
    ? ['Hot Corp awarded major data center contract']
    : [],
};

const mockHiringFetcher: HiringFetcher = {
  fetchJobs: async (domain) => domain === 'hotcorp.com'
    ? [
        { title: 'Business Development Manager', posted_date: daysAgo(10) },
        { title: 'Sales Director', posted_date: daysAgo(20) },
        { title: 'Capture Manager', posted_date: daysAgo(30) },
      ]
    : [],
};

const mockSocialFetcher: SocialFetcher = { fetchPosts: async () => [] };
const mockRedditFetcher: RedditFetcher = { fetchAlerts: async () => [] };

function makeMockSmartleadAPI(): SmartleadAPI & { enrolled: SmartleadLeadPayload[] } {
  const enrolled: SmartleadLeadPayload[] = [];
  return {
    enrolled,
    addLeadToCampaign: async (_id, lead) => { enrolled.push(lead); return { success: true }; },
    getCampaignLeads: async () => [],
  };
}

function makeMockLLM(): LLMClient {
  return {
    generate: async () => JSON.stringify({
      emails: [
        { step: 1, subject: 'Signal', body: 'Test email', delay_days: 0 },
        { step: 2, subject: 'Re: signal', body: 'Follow up', delay_days: 3 },
      ],
      linkedin: { connection_note: 'Note', first_dm: 'DM1', follow_up_dm: 'DM2' },
    }),
  };
}

function makeMockCRM(): CRMClient & { contacts: CRMContact[]; deals: CRMDeal[] } {
  const contacts: CRMContact[] = [];
  const deals: CRMDeal[] = [];
  let id = 0;
  return {
    contacts, deals,
    upsertContact: async (c) => { contacts.push({ ...c, id: `${++id}` }); return { id: `${id}`, created: true }; },
    createDeal: async (d) => { deals.push(d); return { id: `d${++id}` }; },
    findContactByEmail: async (e) => contacts.find(c => c.email === e) ?? null,
  };
}

describe('Full Pipeline (end-to-end)', () => {
  beforeEach(() => {
    fs.mkdirSync(TMP_DIR, { recursive: true });
    fs.mkdirSync(EVENTS_DIR, { recursive: true });
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
    fs.writeFileSync(INPUT_PATH, JSON.stringify(sampleAccounts));
    fs.writeFileSync(CONFIG_PATH, JSON.stringify({
      inputPath: INPUT_PATH, outputDir: OUTPUT_DIR, eventsDir: EVENTS_DIR,
      keywords: ['data center'], rateLimitMs: 0,
    }));
  });

  afterEach(() => {
    fs.rmSync(TMP_DIR, { recursive: true, force: true });
  });

  it('runs full pipeline: signals → score → sequences → enroll → CRM', async () => {
    const smartleadApi = makeMockSmartleadAPI();
    const crm = makeMockCRM();

    const result = await runPipeline({
      runOptions: {
        inputPath: INPUT_PATH,
        outputDir: OUTPUT_DIR,
        configPath: CONFIG_PATH,
        newsFetcher: mockNewsFetcher,
        hiringFetcher: mockHiringFetcher,
        socialFetcher: mockSocialFetcher,
        redditFetcher: mockRedditFetcher,
      },
      smartleadApi,
      smartleadHotCampaignId: 'camp_hot',
      llmClient: makeMockLLM(),
      crmClient: crm,
    });

    expect(result.enrichedCount).toBe(2);
    expect(result.hotCount).toBeGreaterThanOrEqual(1);
    expect(result.sequencesGenerated).toBe(result.hotCount);
    expect(result.enrollResults.length).toBeGreaterThanOrEqual(1);
    expect(result.crmResult).not.toBeNull();
    expect(result.crmResult!.contacts_created).toBe(2);
    expect(result.durationMs).toBeGreaterThan(0);

    // Verify output files
    expect(fs.existsSync(path.join(OUTPUT_DIR, 'sequences.json'))).toBe(true);
    expect(fs.existsSync(path.join(OUTPUT_DIR, 'infra_plan.json'))).toBe(true);
  });

  it('runs without optional integrations (graceful degradation)', async () => {
    const result = await runPipeline({
      runOptions: {
        inputPath: INPUT_PATH,
        outputDir: OUTPUT_DIR,
        configPath: CONFIG_PATH,
        newsFetcher: mockNewsFetcher,
        hiringFetcher: mockHiringFetcher,
        socialFetcher: mockSocialFetcher,
        redditFetcher: mockRedditFetcher,
      },
    });

    expect(result.enrichedCount).toBe(2);
    expect(result.sequencesGenerated).toBe(0);
    expect(result.enrollResults).toHaveLength(0);
    expect(result.crmResult).toBeNull();
  });
});
