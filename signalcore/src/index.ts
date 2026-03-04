// src/index.ts
import fs from 'fs';
import path from 'path';
import { program } from 'commander';
import { loadConfig } from './config.js';
import { Contact, CompanySignals, EnrichedLead } from './types.js';
import { NewsAgent, NewsFetcher } from './agents/newsAgent.js';
import { HiringAgent, HiringFetcher } from './agents/hiringAgent.js';
import { SocialAgent, SocialFetcher } from './agents/socialAgent.js';
import { EventAgent } from './agents/eventAgent.js';
import { RFPAgent, RFPFetcher } from './agents/rfpAgent.js';
import { RedditAgent, RedditFetcher, HttpRedditFetcher } from './agents/redditAgent.js';
import { Coordinator } from './coordinator.js';

export interface RunOptions {
  inputPath?: string;
  outputDir?: string;
  configPath?: string;
  newsFetcher?: NewsFetcher;
  hiringFetcher?: HiringFetcher;
  socialFetcher?: SocialFetcher;
  rfpFetcher?: RFPFetcher;
  redditFetcher?: RedditFetcher;
}

export async function run(opts: RunOptions = {}): Promise<EnrichedLead[]> {
  const cfg = loadConfig(opts.configPath);
  const inputPath = opts.inputPath ?? cfg.inputPath;
  const outputDir = opts.outputDir ?? cfg.outputDir;

  if (!fs.existsSync(inputPath)) {
    throw new Error(`Input file not found: ${inputPath}`);
  }

  const raw = fs.readFileSync(inputPath, 'utf-8');
  let contacts: Contact[];
  try {
    contacts = JSON.parse(raw) as Contact[];
  } catch {
    throw new Error(`Malformed JSON in input file: ${inputPath}`);
  }

  if (!Array.isArray(contacts)) {
    throw new Error(`Input must be a JSON array of contacts`);
  }

  const companyDomains = [...new Set(contacts.map(c => c.company_domain).filter(Boolean))];
  const profileUrls = [...new Set(contacts.map(c => c.linkedin_profile_url).filter(Boolean))];

  // Load event records from CSV files in events dir
  let eventRecords: import('./agents/eventAgent.js').EventRecord[] = [];
  if (fs.existsSync(cfg.eventsDir)) {
    const eventFiles = fs.readdirSync(cfg.eventsDir).filter(f => f.endsWith('.csv'));
    for (const file of eventFiles) {
      const content = fs.readFileSync(path.join(cfg.eventsDir, file), 'utf-8');
      eventRecords = eventRecords.concat(EventAgent.fromCSV(content, file.replace('.csv', '')));
    }
  }

  const newsAgent = new NewsAgent(cfg.keywords, opts.newsFetcher);
  const hiringAgent = new HiringAgent(opts.hiringFetcher);
  const socialAgent = new SocialAgent(opts.socialFetcher);
  const eventAgent = new EventAgent(eventRecords);
  const rfpAgent = new RFPAgent(cfg.keywords, opts.rfpFetcher);

  // Reddit/F5Bot: use injected fetcher, or build from config, or skip
  const redditFetcher = opts.redditFetcher ??
    (cfg.f5botFeedUrl ? new HttpRedditFetcher(cfg.f5botFeedUrl) : undefined);
  const companyKeywords = RedditAgent.buildCompanyKeywords(contacts);
  const redditAgent = new RedditAgent(companyKeywords, cfg.keywords, redditFetcher);

  const [newsSignals, hiringSignals, socialSignals, eventSignals, rfps, redditSignals] = await Promise.all([
    newsAgent.fetchForCompanies(companyDomains),
    hiringAgent.fetchForCompanies(companyDomains),
    socialAgent.fetchForProfiles(profileUrls),
    eventAgent.fetchForCompanies(companyDomains),
    rfpAgent.fetch(),
    redditAgent.fetchForCompanies(companyDomains),
  ]);

  // Build per-company signal map
  const signalsByCompany: Record<string, CompanySignals> = {};

  for (const domain of companyDomains) {
    signalsByCompany[domain] = {
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

  for (const n of newsSignals) {
    const s = signalsByCompany[n.company_domain];
    if (!s) continue;
    s.recent_contract_news = n.recent_contract_news;
    s.recent_dc_or_smr_news = n.recent_dc_or_smr_news;
  }

  for (const h of hiringSignals) {
    const s = signalsByCompany[h.company_domain];
    if (!s) continue;
    s.bd_jobs_last_90_days = h.bd_jobs_last_90_days;
    s.total_open_jobs = h.total_open_jobs;
  }

  // Map social signals by profile URL
  const postsMap: Record<string, { posts: number; growthPosts: number }> = {};
  for (const ss of socialSignals) {
    postsMap[ss.linkedin_profile_url] = {
      posts: ss.posts_last_30_days,
      growthPosts: ss.growth_posts_last_30_days,
    };
  }

  for (const c of contacts) {
    const p = postsMap[c.linkedin_profile_url];
    if (!p) continue;
    const s = signalsByCompany[c.company_domain];
    if (!s) continue;
    s.posts_last_30_days = Math.max(s.posts_last_30_days, p.posts);
    s.growth_posts_last_30_days = Math.max(s.growth_posts_last_30_days, p.growthPosts);
  }

  for (const e of eventSignals) {
    const s = signalsByCompany[e.company_domain];
    if (!s) continue;
    s.is_event_exhibitor = e.is_event_exhibitor;
    if (e.event_name) s.event_name = e.event_name;
  }

  for (const r of redditSignals) {
    const s = signalsByCompany[r.company_domain];
    if (!s) continue;
    s.reddit_mentions_last_30_days = r.reddit_mentions_last_30_days;
    s.reddit_keyword_mentions = r.reddit_keyword_mentions;
    s.top_reddit_urls = r.top_reddit_urls;
  }

  const coordinator = new Coordinator();
  const enriched = coordinator.enrich({ contacts, signalsByCompany });

  // Write outputs
  ensureDir(outputDir);
  writeJson(path.join(outputDir, 'enriched_leads.json'), enriched);
  writeCsv(path.join(outputDir, 'enriched_leads.csv'), enriched);

  const hot = enriched.filter(e => e.signal_tier === 'Hot');
  writeCsv(path.join(outputDir, 'smartlead_hot.csv'), hot);

  console.log(`SignalCore: Enriched ${enriched.length} leads | Hot: ${hot.length} | Warm: ${enriched.filter(e => e.signal_tier === 'Warm').length} | Cold: ${enriched.filter(e => e.signal_tier === 'Cold').length}`);
  if (rfps.length > 0) {
    console.log(`SignalCore: Found ${rfps.length} matching RFPs`);
    writeJson(path.join(outputDir, 'rfps.json'), rfps);
  }

  return enriched;
}

function ensureDir(dir: string) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

function writeJson(p: string, data: unknown) {
  fs.writeFileSync(p, JSON.stringify(data, null, 2), 'utf-8');
}

function writeCsv(p: string, rows: EnrichedLead[]) {
  if (!rows.length) {
    fs.writeFileSync(p, '', 'utf-8');
    return;
  }
  const headers = Object.keys(rows[0]) as (keyof EnrichedLead)[];
  const lines = [
    headers.join(','),
    ...rows.map(r =>
      headers.map(h => JSON.stringify((r as Record<string, unknown>)[h] ?? '')).join(','),
    ),
  ];
  fs.writeFileSync(p, lines.join('\n'), 'utf-8');
}

// CLI entrypoint
function cli() {
  program
    .name('signalcore')
    .description('SignalCore DC/SMR – Data center signal engine')
    .option('--input <path>', 'Input accounts JSON file')
    .option('--output <dir>', 'Output directory')
    .option('--config <path>', 'Config JSON file')
    .action(async (opts) => {
      await run({
        inputPath: opts.input,
        outputDir: opts.output,
        configPath: opts.config,
      });
    });

  program.parse();
}

// Only run CLI if this file is executed directly
const isMain = process.argv[1] && (
  process.argv[1].endsWith('index.ts') ||
  process.argv[1].endsWith('index.js')
);

if (isMain) {
  cli();
}
