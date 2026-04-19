// src/automation/pipeline.ts
// Full end-to-end pipeline: signals → score → generate copy → enroll → CRM sync.
// Single entry point for cron. Zero human-in-the-loop after initial config.

import fs from 'fs';
import path from 'path';
import { EnrichedLead } from '../types.js';
import { run, RunOptions } from '../index.js';
import { SmartleadClient, SmartleadAPI, SmartleadEnrollResult } from './smartleadClient.js';
import { SequenceGenerator, LLMClient, GeneratedSequence } from './sequenceGenerator.js';
import { CRMSync, CRMClient, CRMSyncResult } from './crmSync.js';

export interface PipelineConfig {
  runOptions: RunOptions;
  smartleadApi?: SmartleadAPI;
  smartleadHotCampaignId?: string;
  smartleadWarmCampaignId?: string;
  llmClient?: LLMClient;
  crmClient?: CRMClient;
  brandContext?: string;
  outputDir?: string;
}

export interface PipelineResult {
  enrichedCount: number;
  hotCount: number;
  warmCount: number;
  coldCount: number;
  sequencesGenerated: number;
  enrollResults: SmartleadEnrollResult[];
  crmResult: CRMSyncResult | null;
  durationMs: number;
}

export async function runPipeline(config: PipelineConfig): Promise<PipelineResult> {
  const start = Date.now();
  const outputDir = config.outputDir ?? config.runOptions.outputDir ?? 'data/output';

  // Step 1: Signal collection + scoring
  const enriched = await run(config.runOptions);

  const hot = enriched.filter(l => l.signal_tier === 'Hot');
  const warm = enriched.filter(l => l.signal_tier === 'Warm');
  const cold = enriched.filter(l => l.signal_tier === 'Cold');

  // Step 2: Generate sequences for Hot leads
  let sequences: GeneratedSequence[] = [];
  if (config.llmClient && hot.length > 0) {
    const generator = new SequenceGenerator(config.llmClient, config.brandContext);
    sequences = await generator.generateBatch(hot);

    ensureDir(outputDir);
    fs.writeFileSync(
      path.join(outputDir, 'sequences.json'),
      JSON.stringify(sequences, null, 2),
      'utf-8',
    );
    console.log(`Pipeline: Generated ${sequences.length} outreach sequences`);
  }

  // Step 3: Auto-enroll in Smartlead
  let enrollResults: SmartleadEnrollResult[] = [];
  if (config.smartleadApi && config.smartleadHotCampaignId) {
    const smartlead = new SmartleadClient(config.smartleadApi, {
      hotCampaignId: config.smartleadHotCampaignId,
      warmCampaignId: config.smartleadWarmCampaignId,
      enrollTiers: config.smartleadWarmCampaignId ? ['Hot', 'Warm'] : ['Hot'],
    });

    enrollResults = await smartlead.enrollLeads(enriched);

    const enrolled = enrollResults.filter(r => r.status === 'enrolled').length;
    const dupes = enrollResults.filter(r => r.status === 'duplicate').length;
    const errors = enrollResults.filter(r => r.status === 'error').length;
    console.log(`Pipeline: Smartlead enrollment — ${enrolled} new, ${dupes} dupes, ${errors} errors`);
  }

  // Step 4: CRM sync
  let crmResult: CRMSyncResult | null = null;
  if (config.crmClient) {
    const crm = new CRMSync(config.crmClient, ['Hot']);
    crmResult = await crm.syncLeads(enriched);
    console.log(`Pipeline: CRM sync — ${crmResult.contacts_created} created, ${crmResult.contacts_updated} updated, ${crmResult.deals_created} deals`);
  }

  const durationMs = Date.now() - start;
  console.log(`Pipeline: Complete in ${(durationMs / 1000).toFixed(1)}s`);

  return {
    enrichedCount: enriched.length,
    hotCount: hot.length,
    warmCount: warm.length,
    coldCount: cold.length,
    sequencesGenerated: sequences.length,
    enrollResults,
    crmResult,
    durationMs,
  };
}

function ensureDir(dir: string) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}
