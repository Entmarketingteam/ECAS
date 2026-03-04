// src/agents/redditAgent.ts
// Integrates with F5Bot JSON feeds for Reddit/HN/Lobsters keyword monitoring.
// F5Bot Power Users get a JSON feed URL from their account page.
// This agent fetches that feed, matches mentions to target companies,
// and produces per-company Reddit signal data.

export interface F5BotAlert {
  title: string;
  body: string;
  url: string;
  subreddit?: string;
  date: string; // ISO or unix
  keyword: string;
}

export interface RedditSignal {
  company_domain: string;
  reddit_mentions_last_30_days: number;
  reddit_keyword_mentions: number; // mentions matching DC/SMR keywords
  top_reddit_urls: string[];
}

export interface RedditFetcher {
  fetchAlerts: () => Promise<F5BotAlert[]>;
}

/** Default fetcher that hits the F5Bot JSON feed URL */
export class HttpRedditFetcher implements RedditFetcher {
  constructor(private feedUrl: string) {}

  async fetchAlerts(): Promise<F5BotAlert[]> {
    const res = await fetch(this.feedUrl);
    if (!res.ok) {
      console.error(`F5Bot feed fetch failed: ${res.status}`);
      return [];
    }
    const data = await res.json() as F5BotAlertRaw[];
    return data.map(item => ({
      title: item.title ?? '',
      body: item.body ?? item.content ?? item.summary ?? '',
      url: item.url ?? item.link ?? '',
      subreddit: item.subreddit ?? extractSubreddit(item.url ?? item.link ?? ''),
      date: item.date ?? item.published ?? item.created ?? '',
      keyword: item.keyword ?? item.matched_keyword ?? '',
    }));
  }
}

interface F5BotAlertRaw {
  title?: string;
  body?: string;
  content?: string;
  summary?: string;
  url?: string;
  link?: string;
  subreddit?: string;
  date?: string;
  published?: string;
  created?: string;
  keyword?: string;
  matched_keyword?: string;
}

function extractSubreddit(url: string): string | undefined {
  const match = url.match(/reddit\.com\/r\/([^/]+)/);
  return match ? match[1] : undefined;
}

export class RedditAgent {
  constructor(
    private companyKeywords: Map<string, string[]>, // domain -> [company name variants]
    private dcKeywords: string[],
    private fetcher?: RedditFetcher,
  ) {}

  /**
   * Fetch F5Bot alerts and match them to target company domains.
   * Matching logic: check if alert title/body mentions any company name variant.
   */
  async fetchForCompanies(companyDomains: string[]): Promise<RedditSignal[]> {
    if (!this.fetcher) {
      // No F5Bot feed configured – return empty signals
      return companyDomains.map(domain => ({
        company_domain: domain,
        reddit_mentions_last_30_days: 0,
        reddit_keyword_mentions: 0,
        top_reddit_urls: [],
      }));
    }

    let alerts: F5BotAlert[];
    try {
      alerts = await this.fetcher.fetchAlerts();
    } catch (err) {
      console.error('RedditAgent: failed to fetch F5Bot alerts', err);
      return companyDomains.map(domain => ({
        company_domain: domain,
        reddit_mentions_last_30_days: 0,
        reddit_keyword_mentions: 0,
        top_reddit_urls: [],
      }));
    }

    // Filter to last 30 days
    const cutoff = Date.now() - 30 * 24 * 60 * 60 * 1000;
    const recentAlerts = alerts.filter(a => {
      const ts = new Date(a.date).getTime();
      return !Number.isNaN(ts) && ts >= cutoff;
    });

    // Build result per domain
    const results: RedditSignal[] = [];

    for (const domain of companyDomains) {
      const nameVariants = this.companyKeywords.get(domain) ?? [domain.replace(/\.\w+$/, '')];
      const matched: F5BotAlert[] = [];

      for (const alert of recentAlerts) {
        const text = `${alert.title} ${alert.body}`.toLowerCase();
        const matchesCompany = nameVariants.some(v => text.includes(v.toLowerCase()));
        if (matchesCompany) {
          matched.push(alert);
        }
      }

      const dcLower = this.dcKeywords.map(k => k.toLowerCase());
      let keywordHits = 0;
      for (const alert of matched) {
        const text = `${alert.title} ${alert.body}`.toLowerCase();
        if (dcLower.some(k => text.includes(k))) {
          keywordHits++;
        }
      }

      results.push({
        company_domain: domain,
        reddit_mentions_last_30_days: matched.length,
        reddit_keyword_mentions: keywordHits,
        top_reddit_urls: matched.slice(0, 5).map(a => a.url),
      });
    }

    return results;
  }

  /**
   * Build a company keyword map from contacts for matching.
   */
  static buildCompanyKeywords(
    contacts: { company_domain: string; company_name: string }[],
  ): Map<string, string[]> {
    const map = new Map<string, string[]>();
    for (const c of contacts) {
      const existing = map.get(c.company_domain) ?? [];
      if (!existing.includes(c.company_name)) {
        existing.push(c.company_name);
      }
      map.set(c.company_domain, existing);
    }
    return map;
  }
}
