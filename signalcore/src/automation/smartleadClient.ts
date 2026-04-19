// src/automation/smartleadClient.ts
// Auto-enrolls scored leads into Smartlead campaigns.
// Hot → high-touch campaign. Warm → nurture campaign. Cold → skip.

import { EnrichedLead, SignalTier } from '../types.js';

export interface SmartleadEnrollResult {
  email: string;
  campaign_id: string;
  status: 'enrolled' | 'skipped' | 'duplicate' | 'error';
  error?: string;
}

export interface SmartleadAPI {
  addLeadToCampaign(campaignId: string, lead: SmartleadLeadPayload): Promise<{ success: boolean; error?: string }>;
  getCampaignLeads(campaignId: string): Promise<string[]>; // returns list of emails already in campaign
}

export interface SmartleadLeadPayload {
  email: string;
  first_name: string;
  last_name: string;
  company_name: string;
  custom_fields: Record<string, string>;
}

export interface SmartleadConfig {
  hotCampaignId: string;
  warmCampaignId?: string;
  enrollTiers: SignalTier[];
  skipWithoutEmail: boolean;
}

const DEFAULT_SMARTLEAD_CONFIG: SmartleadConfig = {
  hotCampaignId: '',
  enrollTiers: ['Hot'],
  skipWithoutEmail: true,
};

export class SmartleadClient {
  private api: SmartleadAPI;
  private config: SmartleadConfig;

  constructor(api: SmartleadAPI, config?: Partial<SmartleadConfig>) {
    this.api = api;
    this.config = { ...DEFAULT_SMARTLEAD_CONFIG, ...config };
  }

  async enrollLeads(leads: EnrichedLead[]): Promise<SmartleadEnrollResult[]> {
    const eligible = leads.filter(l => this.config.enrollTiers.includes(l.signal_tier));

    if (!this.config.hotCampaignId) {
      return eligible.map(l => ({
        email: l.email ?? '',
        campaign_id: '',
        status: 'error' as const,
        error: 'No campaign ID configured',
      }));
    }

    // Get existing leads to deduplicate
    const existingEmails = new Set<string>();
    try {
      const hotExisting = await this.api.getCampaignLeads(this.config.hotCampaignId);
      hotExisting.forEach(e => existingEmails.add(e.toLowerCase()));
      if (this.config.warmCampaignId) {
        const warmExisting = await this.api.getCampaignLeads(this.config.warmCampaignId);
        warmExisting.forEach(e => existingEmails.add(e.toLowerCase()));
      }
    } catch {
      // Continue without dedup if fetch fails
    }

    const results: SmartleadEnrollResult[] = [];

    for (const lead of eligible) {
      if (!lead.email && this.config.skipWithoutEmail) {
        results.push({ email: '', campaign_id: '', status: 'skipped', error: 'No email' });
        continue;
      }

      if (existingEmails.has((lead.email ?? '').toLowerCase())) {
        results.push({
          email: lead.email!,
          campaign_id: this.getCampaignForTier(lead.signal_tier),
          status: 'duplicate',
        });
        continue;
      }

      const campaignId = this.getCampaignForTier(lead.signal_tier);
      const payload = this.buildPayload(lead);

      try {
        const res = await this.api.addLeadToCampaign(campaignId, payload);
        results.push({
          email: lead.email!,
          campaign_id: campaignId,
          status: res.success ? 'enrolled' : 'error',
          error: res.error,
        });
      } catch (err) {
        results.push({
          email: lead.email ?? '',
          campaign_id: campaignId,
          status: 'error',
          error: err instanceof Error ? err.message : 'Unknown error',
        });
      }
    }

    return results;
  }

  private getCampaignForTier(tier: SignalTier): string {
    if (tier === 'Warm' && this.config.warmCampaignId) {
      return this.config.warmCampaignId;
    }
    return this.config.hotCampaignId;
  }

  private buildPayload(lead: EnrichedLead): SmartleadLeadPayload {
    return {
      email: lead.email!,
      first_name: lead.first_name,
      last_name: lead.last_name,
      company_name: lead.company_name,
      custom_fields: {
        title: lead.title,
        signal_score: String(lead.signal_score),
        signal_tier: lead.signal_tier,
        top_signals: lead.top_signals.join('; '),
        company_domain: lead.company_domain,
        linkedin_url: lead.linkedin_profile_url,
      },
    };
  }
}
