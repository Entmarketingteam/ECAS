// src/infraSizing.ts
// TAM Coverage Infrastructure Calculator
// Maps enriched leads → send volume → domains/inboxes/LinkedIn accounts → monthly cost

import { EnrichedLead, SignalTier } from './types.js';

export interface InfraConfig {
  emailTouchesPerContact: number;     // email touches per contact over the window
  linkedinTouchesPerProspect: number; // LI touches per Hot prospect over the window
  windowDays: number;                 // campaign window in days (default 90)
  warmupDays: number;                 // inbox warmup period before full volume
  emailsPerInboxPerDay: number;       // max sends per warmed inbox per day
  inboxesPerDomain: number;           // inboxes per sending domain
  linkedinActionsPerAccountPerDay: number; // LI actions per account per day
  linkedinTierThreshold: SignalTier;  // which tier goes to LinkedIn (default 'Hot')
  domainCostPerMonth: number;         // $/mo per sending domain
  inboxCostPerMonth: number;          // $/mo per inbox (Google Workspace, etc.)
  salesNavCostPerMonth: number;       // $/mo per LinkedIn Sales Nav seat
  sendingPlatformCostPerMonth: number; // Smartlead/Instantly base cost
}

export interface InfraPlan {
  // TAM breakdown
  totalContacts: number;
  emailContacts: number;
  linkedinContacts: number;
  hotCount: number;
  warmCount: number;
  coldCount: number;

  // Email infrastructure
  totalEmailTouches: number;
  emailsPerDay: number;
  domainsNeeded: number;
  inboxesNeeded: number;
  emailDeliverabilityTarget: string;

  // LinkedIn infrastructure
  totalLinkedinTouches: number;
  linkedinActionsPerDay: number;
  linkedinAccountsNeeded: number;

  // Cost breakdown
  domainCostMonthly: number;
  inboxCostMonthly: number;
  salesNavCostMonthly: number;
  sendingPlatformCostMonthly: number;
  totalMonthlyCost: number;

  // Efficiency metrics
  costPerTouch: number;
  costPerContact: number;
  emailToLinkedinRatio: string;

  // Timeline
  windowDays: number;
  warmupDays: number;
  effectiveSendDays: number;
}

const DEFAULT_CONFIG: InfraConfig = {
  emailTouchesPerContact: 2,
  linkedinTouchesPerProspect: 3,
  windowDays: 90,
  warmupDays: 14,
  emailsPerInboxPerDay: 20,
  inboxesPerDomain: 3,
  linkedinActionsPerAccountPerDay: 50,
  linkedinTierThreshold: 'Hot',
  domainCostPerMonth: 3,
  inboxCostPerMonth: 3,
  salesNavCostPerMonth: 80,
  sendingPlatformCostPerMonth: 97,
};

export function computeInfraPlan(
  leads: EnrichedLead[],
  overrides: Partial<InfraConfig> = {},
): InfraPlan {
  const cfg = { ...DEFAULT_CONFIG, ...overrides };

  const hotCount = leads.filter(l => l.signal_tier === 'Hot').length;
  const warmCount = leads.filter(l => l.signal_tier === 'Warm').length;
  const coldCount = leads.filter(l => l.signal_tier === 'Cold').length;
  const totalContacts = leads.length;

  // Email covers everyone; LinkedIn covers Hot only (or whatever threshold is set)
  const emailContacts = totalContacts;
  const linkedinContacts = cfg.linkedinTierThreshold === 'Hot'
    ? hotCount
    : cfg.linkedinTierThreshold === 'Warm'
      ? hotCount + warmCount
      : totalContacts;

  // Total touches
  const totalEmailTouches = emailContacts * cfg.emailTouchesPerContact;
  const totalLinkedinTouches = linkedinContacts * cfg.linkedinTouchesPerProspect;

  // Effective send days (subtract warmup)
  const effectiveSendDays = Math.max(cfg.windowDays - cfg.warmupDays, 1);

  // Email: daily volume and infrastructure
  const emailsPerDay = Math.ceil(totalEmailTouches / effectiveSendDays);
  const inboxesNeeded = Math.max(Math.ceil(emailsPerDay / cfg.emailsPerInboxPerDay), 1);
  const domainsNeeded = Math.max(Math.ceil(inboxesNeeded / cfg.inboxesPerDomain), 1);

  // LinkedIn: daily volume and accounts
  const linkedinActionsPerDay = totalLinkedinTouches > 0
    ? Math.ceil(totalLinkedinTouches / effectiveSendDays)
    : 0;
  const linkedinAccountsNeeded = linkedinActionsPerDay > 0
    ? Math.max(Math.ceil(linkedinActionsPerDay / cfg.linkedinActionsPerAccountPerDay), 1)
    : 0;

  // Costs
  const domainCostMonthly = domainsNeeded * cfg.domainCostPerMonth;
  const inboxCostMonthly = inboxesNeeded * cfg.inboxCostPerMonth;
  const salesNavCostMonthly = linkedinAccountsNeeded * cfg.salesNavCostPerMonth;
  const sendingPlatformCostMonthly = cfg.sendingPlatformCostPerMonth;
  const totalMonthlyCost = domainCostMonthly + inboxCostMonthly + salesNavCostMonthly + sendingPlatformCostMonthly;

  // Efficiency
  const totalTouches = totalEmailTouches + totalLinkedinTouches;
  const monthsInWindow = cfg.windowDays / 30;
  const totalCostOverWindow = totalMonthlyCost * monthsInWindow;
  const costPerTouch = totalTouches > 0 ? round(totalCostOverWindow / totalTouches, 4) : 0;
  const costPerContact = totalContacts > 0 ? round(totalCostOverWindow / totalContacts, 2) : 0;

  const ratio = linkedinContacts > 0
    ? `${Math.round(emailContacts / linkedinContacts)}:1`
    : 'email only';

  return {
    totalContacts,
    emailContacts,
    linkedinContacts,
    hotCount,
    warmCount,
    coldCount,
    totalEmailTouches,
    emailsPerDay,
    domainsNeeded,
    inboxesNeeded,
    emailDeliverabilityTarget: '90%+',
    totalLinkedinTouches,
    linkedinActionsPerDay,
    linkedinAccountsNeeded,
    domainCostMonthly,
    inboxCostMonthly,
    salesNavCostMonthly,
    sendingPlatformCostMonthly,
    totalMonthlyCost,
    costPerTouch,
    costPerContact,
    emailToLinkedinRatio: ratio,
    windowDays: cfg.windowDays,
    warmupDays: cfg.warmupDays,
    effectiveSendDays,
  };
}

export function formatInfraPlan(plan: InfraPlan): string {
  return `
TAM COVERAGE INFRASTRUCTURE
────────────────────────────────────────

TAM Breakdown
  Total contacts:     ${plan.totalContacts.toLocaleString()}
  Hot:                ${plan.hotCount.toLocaleString()}
  Warm:               ${plan.warmCount.toLocaleString()}
  Cold:               ${plan.coldCount.toLocaleString()}

Email Layer (100% TAM coverage)
  Contacts:           ${plan.emailContacts.toLocaleString()}
  Total touches:      ${plan.totalEmailTouches.toLocaleString()}
  Emails/day:         ${plan.emailsPerDay.toLocaleString()}
  Domains needed:     ${plan.domainsNeeded}
  Inboxes needed:     ${plan.inboxesNeeded}
  Deliverability:     ${plan.emailDeliverabilityTarget}

LinkedIn Layer (Hot leads only)
  Contacts:           ${plan.linkedinContacts.toLocaleString()}
  Total touches:      ${plan.totalLinkedinTouches.toLocaleString()}
  Actions/day:        ${plan.linkedinActionsPerDay}
  Accounts needed:    ${plan.linkedinAccountsNeeded}

Email-to-LinkedIn:    ${plan.emailToLinkedinRatio}

Monthly Cost
  Domains:            $${plan.domainCostMonthly}/mo
  Inboxes:            $${plan.inboxCostMonthly}/mo
  Sales Navigator:    $${plan.salesNavCostMonthly}/mo
  Sending platform:   $${plan.sendingPlatformCostMonthly}/mo
  ─────────────────
  Total:              $${plan.totalMonthlyCost}/mo

Efficiency
  Cost per touch:     $${plan.costPerTouch}
  Cost per contact:   $${plan.costPerContact}

Timeline
  Campaign window:    ${plan.windowDays} days
  Warmup period:      ${plan.warmupDays} days
  Effective send:     ${plan.effectiveSendDays} days
`.trim();
}

function round(n: number, decimals: number): number {
  const factor = Math.pow(10, decimals);
  return Math.round(n * factor) / factor;
}
