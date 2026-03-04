// src/agents/eventAgent.ts

export interface EventSignal {
  company_domain: string;
  is_event_exhibitor: 0 | 1;
  event_name?: string;
}

export interface EventRecord {
  company_name: string;
  company_domain?: string;
  event_name: string;
}

export class EventAgent {
  private events: EventRecord[];

  constructor(events: EventRecord[] = []) {
    this.events = events;
  }

  static fromCSV(csvContent: string, fallbackEventName?: string): EventRecord[] {
    const lines = csvContent.split('\n').filter(Boolean);
    if (lines.length < 2) return [];

    const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
    const nameIdx = headers.indexOf('company_name');
    const domainIdx = headers.indexOf('company_domain');
    const eventIdx = headers.indexOf('event_name');

    if (nameIdx < 0) return [];

    const records: EventRecord[] = [];
    for (let i = 1; i < lines.length; i++) {
      const cols = lines[i].split(',').map(c => c.trim());
      records.push({
        company_name: cols[nameIdx] ?? '',
        company_domain: domainIdx >= 0 ? cols[domainIdx] : undefined,
        event_name: eventIdx >= 0 ? (cols[eventIdx] ?? fallbackEventName ?? '') : (fallbackEventName ?? ''),
      });
    }
    return records;
  }

  async fetchForCompanies(domains: string[]): Promise<EventSignal[]> {
    return domains.map(domain => this.matchCompany(domain));
  }

  private matchCompany(domain: string): EventSignal {
    const match = this.events.find(
      e => e.company_domain === domain
    );

    if (!match) {
      return { company_domain: domain, is_event_exhibitor: 0 };
    }

    return {
      company_domain: domain,
      is_event_exhibitor: 1,
      event_name: match.event_name,
    };
  }
}
