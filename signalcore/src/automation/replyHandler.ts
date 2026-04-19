// src/automation/replyHandler.ts
// Processes inbound replies from Smartlead webhooks.
// Updates lead status, bumps signal score, and notifies.

import { SignalTier } from '../types.js';

export interface SmartleadWebhookPayload {
  event_type: 'reply' | 'open' | 'click' | 'bounce' | 'unsubscribe';
  email: string;
  campaign_id: string;
  reply_text?: string;
  timestamp: string;
}

export interface ReplyRecord {
  email: string;
  campaign_id: string;
  event_type: string;
  reply_text?: string;
  sentiment: 'positive' | 'neutral' | 'negative' | 'unknown';
  timestamp: string;
  action: 'escalate' | 'nurture' | 'remove' | 'log';
}

export interface ReplyStore {
  saveReply(record: ReplyRecord): Promise<void>;
  getReplyCount(email: string): Promise<number>;
}

export interface ReplyNotifier {
  notify(message: string): Promise<void>;
}

export class ReplyHandler {
  private store: ReplyStore;
  private notifier?: ReplyNotifier;

  constructor(store: ReplyStore, notifier?: ReplyNotifier) {
    this.store = store;
    this.notifier = notifier;
  }

  async handleWebhook(payload: SmartleadWebhookPayload): Promise<ReplyRecord> {
    const record: ReplyRecord = {
      email: payload.email,
      campaign_id: payload.campaign_id,
      event_type: payload.event_type,
      reply_text: payload.reply_text,
      sentiment: this.classifySentiment(payload),
      timestamp: payload.timestamp,
      action: this.determineAction(payload),
    };

    await this.store.saveReply(record);

    if (record.action === 'escalate' && this.notifier) {
      await this.notifier.notify(
        `🔥 Positive reply from ${payload.email}: "${payload.reply_text?.slice(0, 100) ?? '(no text)'}"`,
      );
    }

    if (record.action === 'remove' && this.notifier) {
      await this.notifier.notify(
        `Removed ${payload.email} — ${payload.event_type}`,
      );
    }

    return record;
  }

  async handleBatch(payloads: SmartleadWebhookPayload[]): Promise<ReplyRecord[]> {
    const results: ReplyRecord[] = [];
    for (const p of payloads) {
      results.push(await this.handleWebhook(p));
    }
    return results;
  }

  private classifySentiment(payload: SmartleadWebhookPayload): ReplyRecord['sentiment'] {
    if (payload.event_type !== 'reply' || !payload.reply_text) return 'unknown';

    const text = payload.reply_text.toLowerCase();

    const negativePatterns = [
      'not interested', 'remove me', 'unsubscribe', 'stop emailing',
      'do not contact', 'no thanks', 'no thank you', 'wrong person',
      'not the right', 'please remove', 'opt out',
    ];

    const positivePatterns = [
      'interested', 'tell me more', 'let\'s talk', 'schedule',
      'calendar', 'set up a call', 'learn more', 'sounds good',
      'send me', 'share more', 'open to', 'available',
      'yes', 'sure', 'when can',
    ];

    if (negativePatterns.some(p => text.includes(p))) return 'negative';
    if (positivePatterns.some(p => text.includes(p))) return 'positive';
    return 'neutral';
  }

  private determineAction(payload: SmartleadWebhookPayload): ReplyRecord['action'] {
    if (payload.event_type === 'bounce' || payload.event_type === 'unsubscribe') {
      return 'remove';
    }

    if (payload.event_type === 'reply') {
      const sentiment = this.classifySentiment(payload);
      if (sentiment === 'positive') return 'escalate';
      if (sentiment === 'negative') return 'remove';
      return 'nurture';
    }

    return 'log';
  }
}
