import { describe, it, expect } from 'vitest';
import { SmartleadClient, SmartleadAPI, SmartleadLeadPayload } from '../src/automation/smartleadClient';
import { EnrichedLead } from '../src/types';

function makeLead(tier: 'Hot' | 'Warm' | 'Cold', email?: string): EnrichedLead {
  return {
    first_name: 'Jane',
    last_name: 'Doe',
    title: 'VP BD',
    linkedin_profile_url: 'https://linkedin.com/in/janedoe',
    company_name: 'Test Corp',
    company_domain: 'testcorp.com',
    email: email ?? 'jane@testcorp.com',
    bd_jobs_last_90_days: 0,
    total_open_jobs: 0,
    recent_contract_news: 0,
    recent_dc_or_smr_news: 0,
    posts_last_30_days: 0,
    growth_posts_last_30_days: 0,
    is_event_exhibitor: 0,
    reddit_mentions_last_30_days: 0,
    reddit_keyword_mentions: 0,
    top_reddit_urls: [],
    signal_score: tier === 'Hot' ? 10 : tier === 'Warm' ? 5 : 1,
    signal_tier: tier,
    top_signals: ['Test signal'],
  };
}

function makeMockAPI(existingEmails: string[] = []): SmartleadAPI & { enrolled: SmartleadLeadPayload[] } {
  const enrolled: SmartleadLeadPayload[] = [];
  return {
    enrolled,
    addLeadToCampaign: async (_id, lead) => {
      enrolled.push(lead);
      return { success: true };
    },
    getCampaignLeads: async () => existingEmails,
  };
}

describe('SmartleadClient', () => {
  it('enrolls Hot leads into campaign', async () => {
    const api = makeMockAPI();
    const client = new SmartleadClient(api, { hotCampaignId: 'camp_123' });

    const results = await client.enrollLeads([
      makeLead('Hot'),
      makeLead('Cold'),
    ]);

    expect(results).toHaveLength(1); // Only Hot is eligible
    expect(results[0].status).toBe('enrolled');
    expect(api.enrolled).toHaveLength(1);
    expect(api.enrolled[0].email).toBe('jane@testcorp.com');
  });

  it('skips duplicates already in campaign', async () => {
    const api = makeMockAPI(['jane@testcorp.com']);
    const client = new SmartleadClient(api, { hotCampaignId: 'camp_123' });

    const results = await client.enrollLeads([makeLead('Hot')]);
    expect(results[0].status).toBe('duplicate');
    expect(api.enrolled).toHaveLength(0);
  });

  it('skips leads without email', async () => {
    const api = makeMockAPI();
    const lead = makeLead('Hot');
    delete (lead as Record<string, unknown>).email;
    const client = new SmartleadClient(api, { hotCampaignId: 'camp_123' });

    const results = await client.enrollLeads([lead]);
    expect(results[0].status).toBe('skipped');
  });

  it('returns error when no campaign ID configured', async () => {
    const api = makeMockAPI();
    const client = new SmartleadClient(api);

    const results = await client.enrollLeads([makeLead('Hot')]);
    expect(results[0].status).toBe('error');
    expect(results[0].error).toContain('No campaign ID');
  });

  it('includes signal data in custom fields', async () => {
    const api = makeMockAPI();
    const client = new SmartleadClient(api, { hotCampaignId: 'camp_123' });

    await client.enrollLeads([makeLead('Hot')]);
    expect(api.enrolled[0].custom_fields.signal_tier).toBe('Hot');
    expect(api.enrolled[0].custom_fields.signal_score).toBe('10');
  });

  it('enrolls both Hot and Warm when configured', async () => {
    const api = makeMockAPI();
    const client = new SmartleadClient(api, {
      hotCampaignId: 'camp_hot',
      warmCampaignId: 'camp_warm',
      enrollTiers: ['Hot', 'Warm'],
    });

    const results = await client.enrollLeads([
      makeLead('Hot', 'hot@test.com'),
      makeLead('Warm', 'warm@test.com'),
      makeLead('Cold', 'cold@test.com'),
    ]);

    expect(results).toHaveLength(2);
    expect(results.every(r => r.status === 'enrolled')).toBe(true);
  });
});
