// src/agents/hiringAgent.ts

export interface HiringSignal {
  company_domain: string;
  bd_jobs_last_90_days: number;
  total_open_jobs: number;
}

export interface JobRecord {
  title: string;
  posted_date: string; // ISO
}

export interface HiringFetcher {
  fetchJobs(domain: string): Promise<JobRecord[]>;
}

const BD_TERMS = [
  'business development', 'sales', 'capture',
  'proposal', 'partnerships',
];

export class HiringAgent {
  private fetcher: HiringFetcher;

  constructor(fetcher?: HiringFetcher) {
    this.fetcher = fetcher ?? { fetchJobs: async () => [] };
  }

  async fetchForCompanies(domains: string[]): Promise<HiringSignal[]> {
    const results: HiringSignal[] = [];
    for (const domain of domains) {
      const signal = await this.fetchForCompany(domain);
      results.push(signal);
    }
    return results;
  }

  private async fetchForCompany(domain: string): Promise<HiringSignal> {
    const jobs = await this.fetcher.fetchJobs(domain);
    const now = Date.now();
    const ninetyDaysMs = 90 * 24 * 60 * 60 * 1000;

    let bd_jobs_last_90_days = 0;
    let total_open_jobs = jobs.length;

    for (const job of jobs) {
      const posted = new Date(job.posted_date).getTime();
      if (Number.isNaN(posted)) continue;

      const withinWindow = (now - posted) <= ninetyDaysMs;
      const isBdRole = BD_TERMS.some(t => job.title.toLowerCase().includes(t));

      if (withinWindow && isBdRole) {
        bd_jobs_last_90_days++;
      }
    }

    return { company_domain: domain, bd_jobs_last_90_days, total_open_jobs };
  }
}
