'use strict';
const comp = require('../../agents/compliance');

describe('Compliance Agent', () => {
  test('checkDisclosures flags missing FTC for affiliate post', () => {
    const post = { body: 'Buy this product.', linksInjected: 3, affiliateProductsUsed: ['ring light'] };
    const flags = comp.checkDisclosures(post);
    expect(flags.some(f => f.type === 'missing_ftc_disclosure')).toBe(true);
  });
  test('checkDisclosures passes if disclosure present', () => {
    const post = { body: 'Disclosure: affiliate commission.', linksInjected: 1, affiliateProductsUsed: ['tripod'] };
    const flags = comp.checkDisclosures(post);
    expect(flags.filter(f => f.type === 'missing_ftc_disclosure')).toHaveLength(0);
  });
  test('injectDisclosure adds disclosure to body', () => {
    const post = { body: 'Content here.', linksInjected: 2 };
    const r = comp.injectDisclosure(post);
    expect(r.body.toLowerCase()).toContain('affiliate');
    expect(r.complianceChecked).toBe(true);
  });
  test('injectDisclosure skips if already present', () => {
    const post = { body: 'As an affiliate I earn commission.', linksInjected: 2 };
    const r = comp.injectDisclosure(post);
    expect(r.disclosureInjected).toBeUndefined();
  });
  test('processPost returns complianceChecked=true', async () => {
    const post = { title:'Test', body:'Great content with tripod and ring light.', linksInjected:2, affiliateProductsUsed:['tripod'] };
    const r = await comp.processPost(post);
    expect(r.complianceChecked).toBe(true);
    expect(Array.isArray(r.complianceFlags)).toBe(true);
  });
});
