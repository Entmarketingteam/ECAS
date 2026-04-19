import { describe, it, expect } from 'vitest';
import { CRMSync, CRMClient, CRMContact, CRMDeal } from '../src/automation/crmSync';
import { EnrichedLead } from '../src/types';

function makeLead(tier: 'Hot' | 'Warm' | 'Cold', email?: string): EnrichedLead {
  return {
    first_name: 'Jane',
    last_name: 'Doe',
    title: 'VP BD',
    linkedin_profile_url: 'https://linkedin.com/in/janedoe',
    company_name: 'Test Corp',
    company_domain: 'testcorp.com',
    email,
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
    signal_score: tier === 'Hot' ? 10 : 5,
    signal_tier: tier,
    top_signals: ['Test signal'],
  };
}

function makeMockCRM(): CRMClient & { contacts: CRMContact[]; deals: CRMDeal[] } {
  const contacts: CRMContact[] = [];
  const deals: CRMDeal[] = [];
  let idCounter = 0;

  return {
    contacts,
    deals,
    upsertContact: async (contact) => {
      const existing = contacts.find(c => c.email === contact.email);
      if (existing) {
        Object.assign(existing, contact);
        return { id: existing.id!, created: false };
      }
      const id = `crm_${++idCounter}`;
      contacts.push({ ...contact, id });
      return { id, created: true };
    },
    createDeal: async (deal) => {
      const id = `deal_${++idCounter}`;
      deals.push(deal);
      return { id };
    },
    findContactByEmail: async (email) => {
      return contacts.find(c => c.email === email) ?? null;
    },
  };
}

describe('CRMSync', () => {
  it('creates contacts and deals for Hot leads', async () => {
    const crm = makeMockCRM();
    const sync = new CRMSync(crm);

    const result = await sync.syncLeads([
      makeLead('Hot', 'hot@test.com'),
      makeLead('Cold', 'cold@test.com'),
    ]);

    expect(result.contacts_created).toBe(2);
    expect(result.deals_created).toBe(1); // Only Hot gets a deal
    expect(crm.contacts).toHaveLength(2);
    expect(crm.deals).toHaveLength(1);
    expect(crm.deals[0].stage).toBe('signal_identified');
  });

  it('updates existing contacts', async () => {
    const crm = makeMockCRM();
    const sync = new CRMSync(crm);

    await sync.syncLeads([makeLead('Hot', 'jane@test.com')]);
    const result = await sync.syncLeads([makeLead('Hot', 'jane@test.com')]);

    expect(result.contacts_updated).toBe(1);
    expect(result.contacts_created).toBe(0);
  });

  it('skips leads without email', async () => {
    const crm = makeMockCRM();
    const sync = new CRMSync(crm);

    const result = await sync.syncLeads([makeLead('Hot')]);
    expect(result.contacts_skipped).toBe(1);
    expect(crm.contacts).toHaveLength(0);
  });

  it('handles API errors gracefully', async () => {
    const crm: CRMClient = {
      upsertContact: async () => { throw new Error('CRM down'); },
      createDeal: async () => ({ id: '' }),
      findContactByEmail: async () => null,
    };

    const sync = new CRMSync(crm);
    const result = await sync.syncLeads([makeLead('Hot', 'jane@test.com')]);

    expect(result.errors).toHaveLength(1);
    expect(result.errors[0]).toContain('CRM down');
  });

  it('creates deals for Hot + Warm when configured', async () => {
    const crm = makeMockCRM();
    const sync = new CRMSync(crm, ['Hot', 'Warm']);

    await sync.syncLeads([
      makeLead('Hot', 'hot@test.com'),
      makeLead('Warm', 'warm@test.com'),
      makeLead('Cold', 'cold@test.com'),
    ]);

    expect(crm.deals).toHaveLength(2);
  });
});
