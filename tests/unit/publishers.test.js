'use strict';
const blog = require('../../publishers/blog');
const state = require('../../core/state');

describe('Blog Publisher', () => {
  test('returns empty if no post', async () => {
    const r = await blog.publish(null);
    expect(r.published).toBe(0);
  });
  test('platformStats returns array', () => {
    const s = blog.platformStats();
    expect(Array.isArray(s)).toBe(true);
    s.forEach(p => {
      expect(p).toHaveProperty('name');
      expect(p).toHaveProperty('enabled');
      expect(p).toHaveProperty('successRate');
    });
  });
  test('daily cap enforced', async () => {
    const today = new Date().toISOString().slice(0,10);
    state.set(`posts_today_${today}`, 9999);
    const r = await blog.publish({ title:'Test', body:'Body' });
    expect(r.capped).toBe(true);
    state.set(`posts_today_${today}`, 0);
  });
});
