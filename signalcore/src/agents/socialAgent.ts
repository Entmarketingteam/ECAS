// src/agents/socialAgent.ts

export interface SocialSignal {
  linkedin_profile_url: string;
  posts_last_30_days: number;
  growth_posts_last_30_days: number;
}

export interface PostRecord {
  text: string;
  date: string; // ISO
}

export interface SocialFetcher {
  fetchPosts(profileUrl: string): Promise<PostRecord[]>;
}

const GROWTH_KEYWORDS = [
  'growth', 'expansion', 'contract', 'pipeline',
  'rfp', 'data center', 'data centre', 'smr',
  'hyperscale', 'utility',
];

export class SocialAgent {
  private fetcher: SocialFetcher;

  constructor(fetcher?: SocialFetcher) {
    this.fetcher = fetcher ?? { fetchPosts: async () => [] };
  }

  async fetchForProfiles(profileUrls: string[]): Promise<SocialSignal[]> {
    const results: SocialSignal[] = [];
    for (const url of profileUrls) {
      const signal = await this.fetchForProfile(url);
      results.push(signal);
    }
    return results;
  }

  private async fetchForProfile(url: string): Promise<SocialSignal> {
    const posts = await this.fetcher.fetchPosts(url);
    const now = Date.now();
    const thirtyDaysMs = 30 * 24 * 60 * 60 * 1000;

    let posts_last_30_days = 0;
    let growth_posts_last_30_days = 0;

    for (const post of posts) {
      const posted = new Date(post.date).getTime();
      if (Number.isNaN(posted)) continue;
      if ((now - posted) > thirtyDaysMs) continue;

      posts_last_30_days++;
      const lower = post.text.toLowerCase();
      if (GROWTH_KEYWORDS.some(kw => lower.includes(kw))) {
        growth_posts_last_30_days++;
      }
    }

    return { linkedin_profile_url: url, posts_last_30_days, growth_posts_last_30_days };
  }
}
