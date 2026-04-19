// src/automation/crmSync.ts
// Pushes enriched leads and deals to Close CRM via API.

import { EnrichedLead, SignalTier } from '../types.js';

export interface CRMContact {
  id?: string;
  email: string;
  first_name: string;
  last_name: string;
  title: string;
  company_name: string;
  company_domain: string;
  signal_score: number;
  signal_tier: SignalTier;
  top_signals: string[];
  linkedin_url: string;
}

export interface CRMDeal {
  contact_email: string;
  company_name: string;
  value: number;
  stage: 'signal_identified' | 'positioned' | 'in_conversation' | 'proposal_sent' | 'won' | 'lost';
  signal_tier: SignalTier;
  notes: string;
}

export interface CRMSyncResult {
  contacts_created: number;
  contacts_updated: number;
  contacts_skipped: number;
  deals_created: number;
  errors: string[];
}

export interface CRMClient {
  upsertContact(contact: CRMContact): Promise<{ id: string; created: boolean }>;
  createDeal(deal: CRMDeal): Promise<{ id: string }>;
  findContactByEmail(email: string): Promise<CRMContact | null>;
}

export class CRMSync {
  private client: CRMClient;
  private createDealsForTiers: SignalTier[];

  constructor(client: CRMClient, createDealsForTiers: SignalTier[] = ['Hot']) {
    this.client = client;
    this.createDealsForTiers = createDealsForTiers;
  }

  async syncLeads(leads: EnrichedLead[]): Promise<CRMSyncResult> {
    const result: CRMSyncResult = {
      contacts_created: 0,
      contacts_updated: 0,
      contacts_skipped: 0,
      deals_created: 0,
      errors: [],
    };

    for (const lead of leads) {
      if (!lead.email) {
        result.contacts_skipped++;
        continue;
      }

      try {
        const contact: CRMContact = {
          email: lead.email,
          first_name: lead.first_name,
          last_name: lead.last_name,
          title: lead.title,
          company_name: lead.company_name,
          company_domain: lead.company_domain,
          signal_score: lead.signal_score,
          signal_tier: lead.signal_tier,
          top_signals: lead.top_signals,
          linkedin_url: lead.linkedin_profile_url,
        };

        const upsertResult = await this.client.upsertContact(contact);
        if (upsertResult.created) {
          result.contacts_created++;
        } else {
          result.contacts_updated++;
        }

        if (this.createDealsForTiers.includes(lead.signal_tier)) {
          await this.client.createDeal({
            contact_email: lead.email,
            company_name: lead.company_name,
            value: 500000,
            stage: 'signal_identified',
            signal_tier: lead.signal_tier,
            notes: `Signal score: ${lead.signal_score}. Signals: ${lead.top_signals.join('; ')}`,
          });
          result.deals_created++;
        }
      } catch (err) {
        result.errors.push(
          `${lead.email}: ${err instanceof Error ? err.message : 'Unknown error'}`,
        );
      }
    }

    return result;
  }
}
