'use strict';
const aff = require('../../agents/affiliate');

describe('Affiliate Linker', () => {
  test('buildLink returns valid Amazon URL with tag', () => {
    const url = aff.buildLink('ring light');
    expect(url).toContain('amazon.com');
    expect(url).toContain('alreadyhere-20');
  });
  test('injectLinks replaces [AMAZON_LINK]', () => {
    const { text, linksInjected } = aff.injectLinks('Buy here: [AMAZON_LINK]');
    expect(text).toContain('amazon.com');
    expect(linksInjected).toBeGreaterThan(0);
  });
  test('injectLinks max 2 per product', () => {
    const body = 'ring light ring light ring light ring light ring light';
    const { linksInjected } = aff.injectLinks(body);
    expect(linksInjected).toBeLessThanOrEqual(2);
  });
  test('buildProductSection returns table with FTC disclosure', () => {
    const section = aff.buildProductSection(['tripod','microphone']);
    expect(section).toContain('Recommended Products');
    expect(section).toContain('Disclosure');
    expect(section).toContain('amazon.com');
  });
  test('processPost injects links + FTC', () => {
    const post = { title:'Test', body:'[AMAZON_LINK]', trend: {} };
    const r = aff.processPost(post);
    expect(r.body).toContain('amazon.com');
    expect(r.ftcCompliant).toBe(true);
    expect(r.linksInjected).toBeGreaterThanOrEqual(0);
  });
});
