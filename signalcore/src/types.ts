// src/types.ts
export interface Contact {
  first_name: string;
  last_name: string;
  title: string;
  linkedin_profile_url: string;
  company_name: string;
  company_domain: string;
  company_size?: string;
  industry?: string;
  country?: string;
  email?: string;
  job_change_date?: string; // ISO
}

export interface CompanySignals {
  company_domain: string;
  bd_jobs_last_90_days: number;
  total_open_jobs: number;
  recent_contract_news: 0 | 1;
  recent_dc_or_smr_news: 0 | 1;
  posts_last_30_days: number;
  growth_posts_last_30_days: number;
  is_event_exhibitor: 0 | 1;
  event_name?: string;
  reddit_mentions_last_30_days: number;
  reddit_keyword_mentions: number;
  top_reddit_urls: string[];
}

export type SignalTier = 'Hot' | 'Warm' | 'Cold';

export interface EnrichedLead extends Contact, CompanySignals {
  days_in_role?: number;
  signal_score: number;
  signal_tier: SignalTier;
  top_signals: string[];
}
