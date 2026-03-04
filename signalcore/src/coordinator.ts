// src/coordinator.ts
import { Contact, CompanySignals, EnrichedLead, SignalTier } from './types.js';

export interface CoordinatorInput {
  contacts: Contact[];
  signalsByCompany: Record<string, CompanySignals>;
}

export class Coordinator {
  enrich({ contacts, signalsByCompany }: CoordinatorInput): EnrichedLead[] {
    return contacts.map(contact => {
      const baseSignals =
        signalsByCompany[contact.company_domain] ??
        this.emptySignals(contact.company_domain);
      const days_in_role = this.computeDaysInRole(contact.job_change_date);
      const { signal_score, signal_tier, top_signals } = this.score(
        contact, baseSignals, days_in_role,
      );

      return {
        ...contact,
        ...baseSignals,
        days_in_role,
        signal_score,
        signal_tier,
        top_signals,
      };
    });
  }

  private emptySignals(domain: string): CompanySignals {
    return {
      company_domain: domain,
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
    };
  }

  computeDaysInRole(job_change_date?: string, now?: Date): number | undefined {
    if (!job_change_date) return undefined;
    const start = new Date(job_change_date).getTime();
    if (Number.isNaN(start)) return undefined;
    const ref = now ? now.getTime() : Date.now();
    const diffMs = ref - start;
    return Math.floor(diffMs / (1000 * 60 * 60 * 24));
  }

  private score(
    contact: Contact,
    signals: CompanySignals,
    days_in_role?: number,
  ): { signal_score: number; signal_tier: SignalTier; top_signals: string[] } {
    let score = 0;
    const top_signals: string[] = [];

    const titleLower = contact.title.toLowerCase();
    const isGrowthLeader =
      titleLower.includes('vp') ||
      titleLower.includes('vice president') ||
      titleLower.includes('chief') ||
      titleLower.includes('cro') ||
      titleLower.includes('ceo') ||
      titleLower.includes('head') ||
      titleLower.includes('director');

    if (days_in_role !== undefined && days_in_role <= 90 && isGrowthLeader) {
      score += 3;
      top_signals.push(`New ${contact.title} < 90 days`);
    }

    if (signals.bd_jobs_last_90_days >= 3) {
      score += 3;
      top_signals.push(`${signals.bd_jobs_last_90_days} BD roles open`);
    }

    if (signals.recent_contract_news === 1) {
      score += 2;
      top_signals.push('Recent contract/award PR');
    }

    if (signals.recent_dc_or_smr_news === 1) {
      score += 2;
      top_signals.push('Recent data center / SMR PR');
    }

    if (signals.growth_posts_last_30_days >= 1) {
      score += 2;
      top_signals.push('Exec posting about growth/contracts');
    }

    if (signals.posts_last_30_days >= 2) {
      score += 1;
      top_signals.push('Exec active on LinkedIn');
    }

    if (signals.is_event_exhibitor === 1) {
      score += 2;
      top_signals.push(`Exhibiting at ${signals.event_name ?? 'industry event'}`);
    }

    // Reddit / F5Bot signals
    if (signals.reddit_keyword_mentions >= 3) {
      score += 2;
      top_signals.push(`${signals.reddit_keyword_mentions} Reddit keyword mentions (DC/SMR)`);
    } else if (signals.reddit_keyword_mentions >= 1) {
      score += 1;
      top_signals.push(`${signals.reddit_keyword_mentions} Reddit keyword mention(s)`);
    }

    if (signals.reddit_mentions_last_30_days >= 5) {
      score += 1;
      top_signals.push(`${signals.reddit_mentions_last_30_days} Reddit mentions in 30 days`);
    }

    const tier: SignalTier =
      score >= 7 ? 'Hot' :
      score >= 4 ? 'Warm' :
      'Cold';

    return { signal_score: score, signal_tier: tier, top_signals };
  }
}
