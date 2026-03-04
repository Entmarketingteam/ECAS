// src/agents/rfpAgent.ts

export interface RFP {
  buyer: string;
  title: string;
  url: string;
  due_date?: string;
  est_value?: number;
  text_snippet: string;
}

export interface RFPFetcher {
  fetchRFPs(): Promise<RawRFP[]>;
}

export interface RawRFP {
  buyer: string;
  title: string;
  url: string;
  due_date?: string;
  est_value?: number;
  text_snippet: string;
}

export class RFPAgent {
  private keywords: string[];
  private fetcher: RFPFetcher;

  constructor(keywords: string[], fetcher?: RFPFetcher) {
    this.keywords = keywords.map(k => k.toLowerCase());
    this.fetcher = fetcher ?? { fetchRFPs: async () => [] };
  }

  async fetch(): Promise<RFP[]> {
    const raw = await this.fetcher.fetchRFPs();
    return raw.filter(rfp => this.matchesKeywords(rfp));
  }

  private matchesKeywords(rfp: RawRFP): boolean {
    const text = `${rfp.title} ${rfp.text_snippet}`.toLowerCase();
    return this.keywords.some(kw => text.includes(kw));
  }
}
