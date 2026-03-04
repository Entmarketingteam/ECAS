import { describe, it, expect } from 'vitest';
import { Coordinator } from '../src/coordinator';
import { Contact, CompanySignals } from '../src/types';

function makeContact(overrides: Partial<Contact> = {}): Contact {
  return {
    first_name: 'Jane',
    last_name: 'Doe',
    title: 'VP Business Development',
    linkedin_profile_url: 'https://linkedin.com/in/janedoe',
    company_name: 'Example Data Center Corp',
    company_domain: 'exampledatacenter.com',
    ...overrides,
  };
}

function makeSignals(overrides: Partial<CompanySignals> = {}): CompanySignals {
  return {
    company_domain: 'exampledatacenter.com',
    bd_jobs_last_90_days: 0,
    total_open_jobs: 0,
    recent_contract_news: 0,
    recent_dc_or_smr_news: 0,
    posts_last_30_days: 0,
    growth_posts_last_30_days: 0,
    is_event_exhibitor: 0,
    ...overrides,
  };
}

describe('Coordinator', () => {
  const coordinator = new Coordinator();

  it('computes max score for fully-loaded lead', () => {
    // days_in_role ~60 days
    const jobChangeDate = new Date();
    jobChangeDate.setDate(jobChangeDate.getDate() - 60);

    const contact = makeContact({
      title: 'VP Business Development',
      job_change_date: jobChangeDate.toISOString().split('T')[0],
    });

    const signals = makeSignals({
      bd_jobs_last_90_days: 4,
      total_open_jobs: 12,
      recent_contract_news: 1,
      recent_dc_or_smr_news: 1,
      growth_posts_last_30_days: 2,
      posts_last_30_days: 3,
      is_event_exhibitor: 1,
      event_name: 'Data Center World 2026',
    });

    const result = coordinator.enrich({
      contacts: [contact],
      signalsByCompany: { 'exampledatacenter.com': signals },
    });

    expect(result[0].signal_score).toBe(15);
    expect(result[0].signal_tier).toBe('Hot');
    expect(result[0].top_signals).toContain('4 BD roles open');
    expect(result[0].top_signals).toContain('Recent contract/award PR');
    expect(result[0].top_signals).toContain('Recent data center / SMR PR');
    expect(result[0].top_signals).toContain('Exec posting about growth/contracts');
    expect(result[0].top_signals).toContain('Exec active on LinkedIn');
    expect(result[0].top_signals).toContain('Exhibiting at Data Center World 2026');
  });

  it('tier boundaries: Hot at 7', () => {
    const contact = makeContact({ title: 'Software Engineer', job_change_date: undefined });
    const signals = makeSignals({
      bd_jobs_last_90_days: 3,   // +3
      recent_contract_news: 1,   // +2
      recent_dc_or_smr_news: 1,  // +2
    });

    const result = coordinator.enrich({
      contacts: [contact],
      signalsByCompany: { 'exampledatacenter.com': signals },
    });

    expect(result[0].signal_score).toBe(7);
    expect(result[0].signal_tier).toBe('Hot');
  });

  it('tier boundaries: Warm at 4-6', () => {
    const contact = makeContact({ title: 'Account Manager', job_change_date: undefined });
    const signals = makeSignals({
      recent_contract_news: 1,        // +2
      growth_posts_last_30_days: 1,   // +2
    });

    const result = coordinator.enrich({
      contacts: [contact],
      signalsByCompany: { 'exampledatacenter.com': signals },
    });

    expect(result[0].signal_score).toBe(4);
    expect(result[0].signal_tier).toBe('Warm');
  });

  it('tier boundaries: Cold at <=3', () => {
    const contact = makeContact({ title: 'Junior Analyst', job_change_date: undefined });
    const signals = makeSignals({
      recent_contract_news: 1,  // +2
    });

    const result = coordinator.enrich({
      contacts: [contact],
      signalsByCompany: { 'exampledatacenter.com': signals },
    });

    expect(result[0].signal_score).toBe(2);
    expect(result[0].signal_tier).toBe('Cold');
  });

  it('top_signals contains human-readable summaries', () => {
    const jobChangeDate = new Date();
    jobChangeDate.setDate(jobChangeDate.getDate() - 30);

    const contact = makeContact({
      title: 'VP Sales',
      job_change_date: jobChangeDate.toISOString().split('T')[0],
    });
    const signals = makeSignals({
      bd_jobs_last_90_days: 5,
      is_event_exhibitor: 1,
      event_name: 'Data Center World 2026',
    });

    const result = coordinator.enrich({
      contacts: [contact],
      signalsByCompany: { 'exampledatacenter.com': signals },
    });

    expect(result[0].top_signals).toEqual(expect.arrayContaining([
      expect.stringContaining('VP Sales'),
      expect.stringContaining('5 BD roles open'),
      expect.stringContaining('Data Center World 2026'),
    ]));
  });

  it('handles missing company signals gracefully', () => {
    const contact = makeContact({ company_domain: 'unknown.com' });
    const result = coordinator.enrich({
      contacts: [contact],
      signalsByCompany: {},
    });

    expect(result[0].signal_score).toBe(0);
    expect(result[0].signal_tier).toBe('Cold');
  });

  it('computes days_in_role correctly', () => {
    const daysAgo = 45;
    const date = new Date();
    date.setDate(date.getDate() - daysAgo);

    const result = coordinator.computeDaysInRole(date.toISOString().split('T')[0], new Date());
    expect(result).toBe(daysAgo);
  });

  it('returns undefined for missing job_change_date', () => {
    const result = coordinator.computeDaysInRole(undefined);
    expect(result).toBeUndefined();
  });
});
