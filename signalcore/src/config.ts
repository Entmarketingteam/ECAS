// src/config.ts
import fs from 'fs';
import path from 'path';

export interface Config {
  inputPath: string;
  outputDir: string;
  keywords: string[];
  eventsDir: string;
  rateLimitMs: number;
}

const defaults: Config = {
  inputPath: 'data/input/accounts.json',
  outputDir: 'data/output',
  eventsDir: 'data/events',
  keywords: [
    'data center',
    'data centre',
    'hyperscale',
    'hyperscaler',
    'SMR',
    'small modular reactor',
    'nuclear',
    'substation',
    'critical power',
    'grid upgrade',
  ],
  rateLimitMs: 500,
};

export function loadConfig(overridePath?: string): Config {
  if (overridePath && fs.existsSync(overridePath)) {
    const raw = fs.readFileSync(overridePath, 'utf-8');
    const overrides = JSON.parse(raw) as Partial<Config>;
    return { ...defaults, ...overrides };
  }
  const defaultConfigPath = path.resolve('config.json');
  if (fs.existsSync(defaultConfigPath)) {
    const raw = fs.readFileSync(defaultConfigPath, 'utf-8');
    const overrides = JSON.parse(raw) as Partial<Config>;
    return { ...defaults, ...overrides };
  }
  return { ...defaults };
}

export const config: Config = defaults;
