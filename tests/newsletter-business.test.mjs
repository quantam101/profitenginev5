import assert from 'node:assert/strict';
import {
  normalizeEmail,
  sha256,
  slugify,
  renderConfirmationHtml,
  renderIssueHtml,
} from '../lib/newsletter-business/core.mjs';

assert.equal(normalizeEmail('  User@Example.COM '), 'user@example.com');
assert.equal(slugify('How to Build a Newsletter Business with AI!'), 'how-to-build-a-newsletter-business-with-ai');
assert.equal(sha256('abc').length, 64);

const confirm = renderConfirmationHtml({ confirmUrl: 'https://example.com/confirm?token=abc' });
assert.match(confirm, /Confirm your ProfitEngine AI subscription/);
assert.match(confirm, /confirm\?token=abc/);

const html = renderIssueHtml({
  title: 'Issue One',
  bodyHtml: '<p>Body</p>',
  ctaLabel: 'Open',
  ctaUrl: 'https://example.com/offer',
}, 'https://example.com/unsubscribe?token=xyz');
assert.match(html, /Issue One/);
assert.match(html, /https:\/\/example.com\/offer/);
assert.match(html, /unsubscribe\?token=xyz/);

console.log('newsletter-business.test.mjs: ok');
