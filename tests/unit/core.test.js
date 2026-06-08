'use strict';
const state = require('../../core/state');
const cache = require('../../core/cache');

describe('State', () => {
  test('get returns default for missing key', () => {
    expect(state.get('__missing_xyz__', 'default')).toBe('default');
  });
  test('set/get round-trip', () => {
    state.set('__test_rtrip__', { v: 42 });
    expect(state.get('__test_rtrip__').v).toBe(42);
  });
  test('increment works', () => {
    state.set('__test_inc__', 10);
    expect(state.increment('__test_inc__', 5)).toBe(15);
  });
  test('push respects maxLen', () => {
    state.set('__test_push__', []);
    for (let i = 0; i < 10; i++) state.push('__test_push__', i, 5);
    expect(state.get('__test_push__').length).toBe(5);
  });
  test('refuses to persist sensitive keys', () => {
    expect(() => state.set('my_api_key', 'x')).toThrow();       // ends with _api_key
    expect(() => state.set('GROQ_API_KEY', 'x')).toThrow();     // ALL_CAPS_KEY pattern
    expect(() => state.set('oauth_access_token', 'x')).toThrow(); // ends with _token
  });
  test('allows non-sensitive keys with date segments', () => {
    expect(() => state.set('tokens_2026-05-13', {})).not.toThrow();
    expect(() => state.set('platform_stats_devto', {})).not.toThrow();
    expect(() => state.set('posts_today_2026-05-13', 0)).not.toThrow();
    expect(() => state.set('pstats_medium', {})).not.toThrow();
  });
  test('TTL expiry returns default', async () => {
    state.set('__test_ttl__', 'alive', 0.001); // 1ms TTL
    await new Promise(r => setTimeout(r, 10));
    expect(state.get('__test_ttl__', 'expired')).toBe('expired');
  });
  test('namespace accessor works', () => {
    const ns = state.ns('mymodule');
    ns.set('setting', 'val');
    expect(ns.get('setting')).toBe('val');
  });
});

describe('Cache', () => {
  test('miss returns null', () => {
    expect(cache.get('ns_test', '__nocache__')).toBeNull();
  });
  test('set/get round-trip', () => {
    cache.set('ns_test', '__cache_key__', { x: 1 }, 60);
    expect(cache.get('ns_test', '__cache_key__').x).toBe(1);
  });
  test('stats returns counts', () => {
    const s = cache.stats();
    expect(s).toHaveProperty('hits');
    expect(s).toHaveProperty('misses');
    expect(s).toHaveProperty('l1Size');
  });
  test('ns factory works', () => {
    const c = cache.ns('unit_test');
    c.set('k', 99, 60);
    expect(c.get('k')).toBe(99);
  });
});
