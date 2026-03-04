import { describe, it, expect } from 'vitest';
import { EventAgent } from '../src/agents/eventAgent';

describe('EventAgent', () => {
  it('matches exhibitors by domain', async () => {
    const events = [
      { company_name: 'Example DC Corp', company_domain: 'exampledatacenter.com', event_name: 'Data Center World 2026' },
      { company_name: 'NuScale Power', company_domain: 'nuscalepower.com', event_name: 'Data Center World 2026' },
    ];

    const agent = new EventAgent(events);
    const results = await agent.fetchForCompanies(['exampledatacenter.com', 'other.com']);

    expect(results[0].is_event_exhibitor).toBe(1);
    expect(results[0].event_name).toBe('Data Center World 2026');
    expect(results[1].is_event_exhibitor).toBe(0);
    expect(results[1].event_name).toBeUndefined();
  });

  it('returns 0 for no match', async () => {
    const agent = new EventAgent([]);
    const results = await agent.fetchForCompanies(['unknown.com']);
    expect(results[0].is_event_exhibitor).toBe(0);
  });

  it('parses CSV correctly', () => {
    const csv = `company_name,company_domain,event_name
Example DC Corp,exampledatacenter.com,Data Center World 2026
NuScale Power,nuscalepower.com,Data Center World 2026`;

    const records = EventAgent.fromCSV(csv);
    expect(records).toHaveLength(2);
    expect(records[0].company_domain).toBe('exampledatacenter.com');
    expect(records[0].event_name).toBe('Data Center World 2026');
  });

  it('handles CSV without event_name column', () => {
    const csv = `company_name,company_domain
Example DC Corp,exampledatacenter.com`;

    const records = EventAgent.fromCSV(csv, 'Fallback Event');
    expect(records[0].event_name).toBe('Fallback Event');
  });
});
