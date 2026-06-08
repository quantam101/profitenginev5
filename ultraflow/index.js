'use strict';
/**
 * ultraflow/index.js — ProfitEngine v5.0
 * VHLL telemetry bridge. Batch + circuit-break + queue persistence.
 * Fire-and-forget — never blocks the pipeline.
 */
const axios  = require('axios');
const logger = require('../core/logger').child('ULTRAFLOW');
const state  = require('../core/state');

let _queue    = [];
let _failures = 0;
let _openUntil = 0;
let _timer    = null;
const BATCH   = 25;
const FLUSH_MS= 20_000;

function isOpen() { return _openUntil > Date.now(); }
function trip()   { _failures++; if (_failures >= 5) { _openUntil = Date.now() + Math.min(300_000, 30_000 * _failures); logger.warn(`Circuit open until ${new Date(_openUntil).toISOString()}`); } }
function reset()  { _failures = 0; _openUntil = 0; }

async function flush() {
  if (_timer) { clearTimeout(_timer); _timer = null; }
  if (!_queue.length || isOpen()) return;
  const url = process.env.ULTRAFLOW_URL;
  const key = process.env.ULTRAFLOW_API_KEY;
  if (!url || !key) return;
  const batch = _queue.splice(0, BATCH);
  try {
    await axios.post(`${url}/api/v1/events/batch`, { events: batch },
      { headers: { 'X-TG-Token': key, 'Content-Type': 'application/json', 'X-Source': 'ProfitEngine/5.0' }, timeout: 10_000 });
    reset();
  } catch (err) {
    _queue.unshift(...batch); trip();
    logger.warn(`Flush failed: ${err.message}`);
  }
}

function schedule() { if (!_timer) _timer = setTimeout(flush, FLUSH_MS); }

function emit(type, data = {}) {
  _queue.push({ type, source: 'profitengine', version: '5.0', sessionId: state.get('sessionId','unknown'), timestamp: new Date().toISOString(), data });
  if (_queue.length >= BATCH) flush();
  else schedule();
}

process.on('SIGTERM', async () => { await flush(); });
process.on('SIGINT',  async () => { await flush(); });

module.exports = { emit, flush };
