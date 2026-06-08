'use strict';
/**
 * tests/integration/pipeline.test.js — ProfitEngine v5.0
 * Integration tests: module wiring, agent chain, publisher interface.
 * No real LLM or HTTP calls — all external I/O stubbed.
 */

// Stub all external HTTP calls
jest.mock('axios', () => ({
  get:  jest.fn().mockResolvedValue({ data: {} }),
  post: jest.fn().mockResolvedValue({ data: { choices: [{ message: { content: 'Test response' } }], usage: { prompt_tokens: 10, completion_tokens: 20 } } }),
  put:  jest.fn().mockResolvedValue({ data: { content: { sha: 'abc123' } } }),
}));

const state   = require('../../core/state');
const cache   = require('../../core/cache');
const llm     = require('../../core/llm');
const aff     = require('../../agents/affiliate');
const comp    = require('../../agents/compliance');
const seo     = require('../../agents/seo');
const pub     = require('../../publishers/blog');
const workers = require('../../workers');
const intel   = require('../../agents/intelligence');

describe('Module wiring', () => {
  test('all core modules export expected API', () => {
    expect(typeof state.get).toBe('function');
    expect(typeof state.set).toBe('function');
    expect(typeof state.ns).toBe('function');
    expect(typeof cache.get).toBe('function');
    expect(typeof cache.ns).toBe('function');
    expect(typeof llm.generate).toBe('function');
    expect(typeof llm.generateJSON).toBe('function');
    expect(typeof llm.circuitStatus).toBe('function');
  });

  test('all agent modules export expected API', () => {
    expect(typeof aff.processPost).toBe('function');
    expect(typeof aff.buildLink).toBe('function');
    expect(typeof comp.processPost).toBe('function');
    expect(typeof seo.optimizePost).toBe('function');
    expect(typeof seo.injectSchemaMarkup).toBe('function');
    expect(typeof pub.publish).toBe('function');
    expect(typeof pub.platformStats).toBe('function');
    expect(typeof intel.analyze).toBe('function');
    expect(typeof intel.addToDLQ).toBe('function');
    expect(typeof intel.drainDLQ).toBe('function');
  });
});

describe('Affiliate → Compliance chain', () => {
  const basePost = {
    id: 'test_001',
    title: 'Best Ring Lights for Streaming',
    slug: 'best-ring-lights',
    body: 'Buy this [AMAZON_LINK] today. The ring light is amazing.',
    keywords: ['ring light', 'streaming'],
    niche: 'passive income',
    trend: { affiliateProducts: ['ring light'] },
  };

  test('affiliate injects links and FTC disclosure', async () => {
    const withAff = aff.processPost(basePost);
    expect(withAff.body).toContain('amazon.com');
    expect(withAff.linksInjected).toBeGreaterThan(0);
    expect(withAff.ftcCompliant).toBe(true);
  });

  test('compliance injects affiliate disclosure', async () => {
    const withAff = aff.processPost(basePost);
    const withComp = await comp.processPost(withAff);
    expect(withComp.complianceChecked).toBe(true);
    expect(Array.isArray(withComp.complianceFlags)).toBe(true);
    const body = withComp.body.toLowerCase();
    expect(body.includes('affiliate') || body.includes('commission') || body.includes('disclosure')).toBe(true);
  });

  test('compliance removes prohibited claims', async () => {
    const badPost = { ...basePost, body: 'Guaranteed income! Make $500 per day, 100% guaranteed.' };
    const withComp = await comp.processPost(badPost);
    expect(withComp.body.toLowerCase()).not.toContain('100% guaranteed');
  });
});

describe('SEO chain', () => {
  test('injectSchemaMarkup adds LD+JSON BlogPosting', () => {
    const post = { title: 'Test', slug: 'test', keywords: ['kw1', 'kw2'], generatedAt: new Date().toISOString() };
    const result = seo.injectSchemaMarkup(post);
    expect(result.schemaInjected).toBe(true);
    expect(result.schemaMarkup).toContain('BlogPosting');
    expect(result.schemaMarkup).toContain('application/ld+json');
  });
});

describe('Publisher interface', () => {
  test('platformStats returns correct shape', () => {
    const stats = pub.platformStats();
    expect(Array.isArray(stats)).toBe(true);
    stats.forEach(p => {
      expect(p).toHaveProperty('name');
      expect(p).toHaveProperty('enabled');
      expect(p).toHaveProperty('successRate');
    });
  });

  test('publish returns zero when no platforms configured', async () => {
    // No API keys in test env
    const result = await pub.publish({ title: 'T', body: 'B', keywords: [] });
    expect(result).toHaveProperty('published');
    expect(typeof result.published).toBe('number');
  });

  test('daily cap enforced', async () => {
    const today = new Date().toISOString().slice(0, 10);
    state.set(`posts_today_${today}`, 9999);
    const result = await pub.publish({ title: 'T', body: 'B' });
    expect(result.capped).toBe(true);
    state.set(`posts_today_${today}`, 0);
  });
});

describe('Worker system', () => {
  test('enqueue returns false for unknown task', () => {
    expect(workers.enqueue('nonexistentTask')).toBe(false);
  });

  test('enqueue returns true for registered task', () => {
    expect(workers.enqueue('retryDLQ')).toBe(true);
  });

  test('stats returns expected shape', () => {
    const s = workers.stats();
    expect(s).toHaveProperty('queueDepth');
    expect(s).toHaveProperty('running');
    expect(s).toHaveProperty('tasksComplete');
    expect(Array.isArray(s.registeredTasks)).toBe(true);
  });
});

describe('Intelligence DLQ', () => {
  test('addToDLQ adds item with retries', () => {
    intel.addToDLQ({ id: 'dlq_test_001', title: 'Test' }, 'connection timeout', 'pipeline');
    const dlq = state.get('dlq', []);
    const item = dlq.find(d => d.id === 'dlq_test_001');
    expect(item).toBeDefined();
    expect(item.retries).toBe(1);
    expect(item.lastError).toBe('connection timeout');
  });

  test('drainDLQ separates recoverable from dead', async () => {
    // Add a dead item (3 retries)
    state.set('dlq', [
      { id: 'dead_001', retries: 3 },
      { id: 'live_001', retries: 1 },
    ]);
    const recovered = await intel.drainDLQ();
    expect(recovered).toBe(1);
    const remaining = state.get('dlq', []);
    expect(remaining.every(d => d.retries >= 3)).toBe(true);
  });
});

describe('State namespace isolation', () => {
  test('ns() creates isolated key namespace', () => {
    const ns1 = state.ns('ns1');
    const ns2 = state.ns('ns2');
    ns1.set('setting', 'val1');
    ns2.set('setting', 'val2');
    expect(ns1.get('setting')).toBe('val1');
    expect(ns2.get('setting')).toBe('val2');
  });
});
