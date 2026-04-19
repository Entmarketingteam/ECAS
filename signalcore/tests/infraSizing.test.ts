import { describe, it, expect } from 'vitest';
import { computeInfraPlan, formatInfraPlan } from '../src/infraSizing';
import { EnrichedLead } from '../src/types';

function makeLead(tier: 'Hot' | 'Warm' | 'Cold', i: number): EnrichedLead {
  return {
    first_name: `First${i}`,
    last_name: `Last${i}`,
    title: 'VP Sales',
    linkedin_profile_url: `https://linkedin.com/in/person${i}`,
    company_name: `Company ${i}`,
    company_domain: `company${i}.com`,
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
    top_signals: [],
  };
}

function makeLeadSet(hot: number, warm: number, cold: number): EnrichedLead[] {
  const leads: EnrichedLead[] = [];
  let idx = 0;
  for (let i = 0; i < hot; i++) leads.push(makeLead('Hot', idx++));
  for (let i = 0; i < warm; i++) leads.push(makeLead('Warm', idx++));
  for (let i = 0; i < cold; i++) leads.push(makeLead('Cold', idx++));
  return leads;
}

describe('Infrastructure Sizing', () => {
  it('computes correct TAM breakdown', () => {
    const leads = makeLeadSet(50, 150, 300);
    const plan = computeInfraPlan(leads);

    expect(plan.totalContacts).toBe(500);
    expect(plan.hotCount).toBe(50);
    expect(plan.warmCount).toBe(150);
    expect(plan.coldCount).toBe(300);
    expect(plan.emailContacts).toBe(500); // email covers all
    expect(plan.linkedinContacts).toBe(50); // LI covers Hot only
  });

  it('computes email infrastructure for 30K TAM (matches the framework example)', () => {
    const leads = makeLeadSet(3000, 9000, 18000); // 30K total, 10% hot
    const plan = computeInfraPlan(leads, {
      emailTouchesPerContact: 2,
      linkedinTouchesPerProspect: 3,
      windowDays: 90,
      warmupDays: 14,
      emailsPerInboxPerDay: 20,
      inboxesPerDomain: 3,
    });

    expect(plan.totalContacts).toBe(30000);
    expect(plan.totalEmailTouches).toBe(60000);
    expect(plan.totalLinkedinTouches).toBe(9000);
    expect(plan.effectiveSendDays).toBe(76);

    // 60000 / 76 = 790 emails/day → 790/20 = 40 inboxes → 40/3 = 14 domains
    expect(plan.emailsPerDay).toBe(790);
    expect(plan.inboxesNeeded).toBe(40);
    expect(plan.domainsNeeded).toBe(14);

    // 9000 / 76 = 119 actions/day → 119/50 = 3 accounts
    expect(plan.linkedinActionsPerDay).toBe(119);
    expect(plan.linkedinAccountsNeeded).toBe(3);

    // Ratio: 30000 / 3000 = 10:1
    expect(plan.emailToLinkedinRatio).toBe('10:1');
  });

  it('computes monthly cost correctly', () => {
    const leads = makeLeadSet(10, 30, 60);
    const plan = computeInfraPlan(leads, {
      domainCostPerMonth: 3,
      inboxCostPerMonth: 3,
      salesNavCostPerMonth: 80,
      sendingPlatformCostPerMonth: 97,
    });

    const expectedDomainCost = plan.domainsNeeded * 3;
    const expectedInboxCost = plan.inboxesNeeded * 3;
    const expectedSalesNavCost = plan.linkedinAccountsNeeded * 80;
    const expectedTotal = expectedDomainCost + expectedInboxCost + expectedSalesNavCost + 97;

    expect(plan.domainCostMonthly).toBe(expectedDomainCost);
    expect(plan.inboxCostMonthly).toBe(expectedInboxCost);
    expect(plan.salesNavCostMonthly).toBe(expectedSalesNavCost);
    expect(plan.totalMonthlyCost).toBe(expectedTotal);
  });

  it('handles zero leads gracefully', () => {
    const plan = computeInfraPlan([]);
    expect(plan.totalContacts).toBe(0);
    expect(plan.emailsPerDay).toBe(0);
    expect(plan.domainsNeeded).toBe(1); // minimum 1
    expect(plan.linkedinAccountsNeeded).toBe(0);
    expect(plan.costPerTouch).toBe(0);
  });

  it('handles all-Cold list (no LinkedIn needed)', () => {
    const leads = makeLeadSet(0, 0, 100);
    const plan = computeInfraPlan(leads);

    expect(plan.linkedinContacts).toBe(0);
    expect(plan.totalLinkedinTouches).toBe(0);
    expect(plan.linkedinAccountsNeeded).toBe(0);
    expect(plan.salesNavCostMonthly).toBe(0);
    expect(plan.emailToLinkedinRatio).toBe('email only');
  });

  it('supports Warm+Hot LinkedIn threshold', () => {
    const leads = makeLeadSet(10, 40, 50);
    const plan = computeInfraPlan(leads, {
      linkedinTierThreshold: 'Warm',
    });

    expect(plan.linkedinContacts).toBe(50); // Hot + Warm
  });

  it('computes cost per touch and cost per contact', () => {
    const leads = makeLeadSet(50, 150, 300);
    const plan = computeInfraPlan(leads);

    expect(plan.costPerTouch).toBeGreaterThan(0);
    expect(plan.costPerContact).toBeGreaterThan(0);
    expect(plan.costPerContact).toBeGreaterThan(plan.costPerTouch);
  });

  it('formats plan as readable string', () => {
    const leads = makeLeadSet(50, 150, 300);
    const plan = computeInfraPlan(leads);
    const formatted = formatInfraPlan(plan);

    expect(formatted).toContain('TAM COVERAGE INFRASTRUCTURE');
    expect(formatted).toContain('Email Layer');
    expect(formatted).toContain('LinkedIn Layer');
    expect(formatted).toContain('Monthly Cost');
    expect(formatted).toContain('500'); // total contacts
    expect(formatted).toContain('$');
  });

  it('effective send days respects warmup period', () => {
    const leads = makeLeadSet(10, 10, 10);

    const plan90 = computeInfraPlan(leads, { windowDays: 90, warmupDays: 14 });
    expect(plan90.effectiveSendDays).toBe(76);

    const plan60 = computeInfraPlan(leads, { windowDays: 60, warmupDays: 21 });
    expect(plan60.effectiveSendDays).toBe(39);
  });
});
