import { describe, it, expect } from 'vitest';
import { ReplyHandler, ReplyStore, ReplyRecord, SmartleadWebhookPayload, ReplyNotifier } from '../src/automation/replyHandler';

function makeMockStore(): ReplyStore & { records: ReplyRecord[] } {
  const records: ReplyRecord[] = [];
  return {
    records,
    saveReply: async (record) => { records.push(record); },
    getReplyCount: async (email) => records.filter(r => r.email === email).length,
  };
}

function makeMockNotifier(): ReplyNotifier & { messages: string[] } {
  const messages: string[] = [];
  return {
    messages,
    notify: async (msg) => { messages.push(msg); },
  };
}

function makePayload(overrides: Partial<SmartleadWebhookPayload> = {}): SmartleadWebhookPayload {
  return {
    event_type: 'reply',
    email: 'jane@test.com',
    campaign_id: 'camp_123',
    reply_text: '',
    timestamp: new Date().toISOString(),
    ...overrides,
  };
}

describe('ReplyHandler', () => {
  it('classifies positive reply and escalates', async () => {
    const store = makeMockStore();
    const notifier = makeMockNotifier();
    const handler = new ReplyHandler(store, notifier);

    const result = await handler.handleWebhook(makePayload({
      reply_text: 'Sounds good, let\'s schedule a call next week',
    }));

    expect(result.sentiment).toBe('positive');
    expect(result.action).toBe('escalate');
    expect(notifier.messages).toHaveLength(1);
    expect(notifier.messages[0]).toContain('Positive reply');
  });

  it('classifies negative reply and removes', async () => {
    const store = makeMockStore();
    const handler = new ReplyHandler(store);

    const result = await handler.handleWebhook(makePayload({
      reply_text: 'Not interested, please remove me from your list',
    }));

    expect(result.sentiment).toBe('negative');
    expect(result.action).toBe('remove');
  });

  it('classifies neutral reply and nurtures', async () => {
    const store = makeMockStore();
    const handler = new ReplyHandler(store);

    const result = await handler.handleWebhook(makePayload({
      reply_text: 'What exactly does this cover? Forwarding to my colleague.',
    }));

    expect(result.sentiment).toBe('neutral');
    expect(result.action).toBe('nurture');
  });

  it('handles bounce events as remove', async () => {
    const store = makeMockStore();
    const notifier = makeMockNotifier();
    const handler = new ReplyHandler(store, notifier);

    const result = await handler.handleWebhook(makePayload({
      event_type: 'bounce',
    }));

    expect(result.action).toBe('remove');
    expect(notifier.messages).toHaveLength(1);
  });

  it('handles unsubscribe as remove', async () => {
    const store = makeMockStore();
    const handler = new ReplyHandler(store);

    const result = await handler.handleWebhook(makePayload({
      event_type: 'unsubscribe',
    }));

    expect(result.action).toBe('remove');
  });

  it('logs open/click events', async () => {
    const store = makeMockStore();
    const handler = new ReplyHandler(store);

    const result = await handler.handleWebhook(makePayload({
      event_type: 'open',
    }));

    expect(result.action).toBe('log');
  });

  it('saves all events to store', async () => {
    const store = makeMockStore();
    const handler = new ReplyHandler(store);

    await handler.handleWebhook(makePayload({ event_type: 'open' }));
    await handler.handleWebhook(makePayload({ event_type: 'reply', reply_text: 'interested' }));
    await handler.handleWebhook(makePayload({ event_type: 'bounce' }));

    expect(store.records).toHaveLength(3);
  });

  it('handles batch of webhooks', async () => {
    const store = makeMockStore();
    const handler = new ReplyHandler(store);

    const results = await handler.handleBatch([
      makePayload({ reply_text: 'Yes, let\'s talk', email: 'a@test.com' }),
      makePayload({ reply_text: 'Not interested', email: 'b@test.com' }),
      makePayload({ event_type: 'open', email: 'c@test.com' }),
    ]);

    expect(results).toHaveLength(3);
    expect(results[0].action).toBe('escalate');
    expect(results[1].action).toBe('remove');
    expect(results[2].action).toBe('log');
  });
});
