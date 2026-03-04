// src/agents/newsAgent.ts

export interface NewsSignal {
  company_domain: string;
  recent_contract_news: 0 | 1;
  recent_dc_or_smr_news: 0 | 1;
  example_headlines: string[];
}

export interface NewsFetcher {
  fetchNews(domain: string): Promise<string[]>;
}

const CONTRACT_PATTERNS = [
  'contract', 'award', 'selected by', 'framework agreement',
  'ppa', 'mou', 'breaks ground',
];

const DC_SMR_PATTERNS = [
  'data center', 'data centre', 'hyperscale', 'smr',
  'small modular reactor', 'nuclear', 'substation',
  'critical power', 'expansion', 'campus',
];

export class NewsAgent {
  private keywords: string[];
  private fetcher: NewsFetcher;

  constructor(keywords: string[], fetcher?: NewsFetcher) {
    this.keywords = keywords;
    this.fetcher = fetcher ?? { fetchNews: async () => [] };
  }

  async fetchForCompanies(domains: string[]): Promise<NewsSignal[]> {
    const results: NewsSignal[] = [];
    for (const domain of domains) {
      const signal = await this.fetchForCompany(domain);
      results.push(signal);
    }
    return results;
  }

  private async fetchForCompany(domain: string): Promise<NewsSignal> {
    const headlines = await this.fetcher.fetchNews(domain);

    let recent_contract_news: 0 | 1 = 0;
    let recent_dc_or_smr_news: 0 | 1 = 0;
    const example_headlines: string[] = [];

    for (const headline of headlines) {
      const lower = headline.toLowerCase();

      const isContract = CONTRACT_PATTERNS.some(p => lower.includes(p));
      const isDcSmr = DC_SMR_PATTERNS.some(p => lower.includes(p));

      if (isContract) {
        recent_contract_news = 1;
        example_headlines.push(headline);
      }
      if (isDcSmr) {
        recent_dc_or_smr_news = 1;
        if (!example_headlines.includes(headline)) {
          example_headlines.push(headline);
        }
      }
    }

    return {
      company_domain: domain,
      recent_contract_news,
      recent_dc_or_smr_news,
      example_headlines,
    };
  }
}
