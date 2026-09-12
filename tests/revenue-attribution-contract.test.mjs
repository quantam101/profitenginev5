import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {
  attributionFromPayload,
  newBookingId,
  newLeadId,
  newRevenueEventId,
  safeText,
  verifySquareSignature,
} from '../lib/revenue-attribution.mjs';

const leadId = newLeadId();
const bookingId = newBookingId();
const revenueEventId = newRevenueEventId();

assert.match(leadId, /^lead_[0-9a-f-]{36}$/i);
assert.match(bookingId, /^book_[0-9a-f-]{36}$/i);
assert.match(revenueEventId, /^rev_[0-9a-f-]{36}$/i);
assert.equal(safeText('<script>`hello`</script>'), 'scripthelloscript');

const attribution = attributionFromPayload({
  source: 'google',
  medium: 'cpc',
  campaign: 'phoenix-field-service',
  landingPage: 'https://app.alreadyherellc.com/',
});
assert.equal(attribution.source, 'google');
assert.equal(attribution.medium, 'cpc');
assert.equal(attribution.campaign, 'phoenix-field-service');

const signatureKey = 'test-square-signature-key';
const notificationUrl = 'https://app.alreadyherellc.com/api/webhooks/square';
const body = JSON.stringify({ type: 'payment.updated', data: { object: { payment: { id: 'p1' } } } });
const signature = crypto
  .createHmac('sha256', signatureKey)
  .update(`${notificationUrl}${body}`)
  .digest('base64');

assert.equal(verifySquareSignature({ signatureKey, notificationUrl, body, signature }), true);
assert.equal(verifySquareSignature({ signatureKey, notificationUrl, body: `${body}x`, signature }), false);

console.log('revenue-attribution-contract.test.mjs: ok');
