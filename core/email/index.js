'use strict';
/**
 * core/email/index.js — ProfitEngine v5.0
 * Enterprise email: retry, rate limit, template support, queue.
 */
const nodemailer = require('nodemailer');
const logger     = require('../logger').child('EMAIL');

let _transport   = null;
let _lastSent    = 0;
let _queue       = [];
let _flushing    = false;
const MIN_GAP_MS = 15_000;
const MAX_QUEUE  = 50;

function getTransport() {
  if (_transport) return _transport;
  const user = process.env.GMAIL_USER;
  const pass = process.env.GMAIL_APP_PASSWORD;
  if (!user || !pass) return null;
  _transport = nodemailer.createTransport({ service: 'gmail', auth: { user, pass } });
  return _transport;
}

async function _send(opts) {
  const transport = getTransport();
  if (!transport) { logger.warn('Not configured'); return false; }
  for (let i = 1; i <= 3; i++) {
    try {
      await transport.sendMail({
        from:    `"ProfitEngine v5" <${process.env.GMAIL_USER}>`,
        to:      opts.to || process.env.ALERT_EMAIL,
        subject: opts.subject,
        text:    opts.text,
        html:    opts.html || `<pre style="font-family:monospace">${opts.text}</pre>`,
      });
      _lastSent = Date.now();
      logger.info(`Sent: ${opts.subject}`);
      return true;
    } catch (err) {
      logger.warn(`Attempt ${i} failed: ${err.message}`);
      if (i < 3) await new Promise(r => setTimeout(r, 5000 * i));
    }
  }
  return false;
}

async function drainQueue() {
  if (_flushing || !_queue.length) return;
  _flushing = true;
  while (_queue.length) {
    const gap = Date.now() - _lastSent;
    if (gap < MIN_GAP_MS) await new Promise(r => setTimeout(r, MIN_GAP_MS - gap));
    const item = _queue.shift();
    await _send(item);
  }
  _flushing = false;
}

async function send(opts) {
  if (_queue.length >= MAX_QUEUE) { logger.warn('Queue full — email dropped'); return false; }
  if (Date.now() - _lastSent > MIN_GAP_MS && !_queue.length) {
    const ok = await _send(opts);
    if (!ok) _queue.push(opts);
    return ok;
  }
  _queue.push(opts);
  drainQueue().catch(() => {});
  return true;
}

async function sendAlert(subject, text, html) {
  return send({ to: process.env.ALERT_EMAIL, subject: `[ProfitEngine] ${subject}`, text, html });
}

module.exports = { send, sendAlert };
