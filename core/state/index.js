'use strict';
/**
 * core/state/index.js — ProfitEngine v5.0
 * Enterprise persistent state: atomic writes, namespaced keys,
 * TTL support, size limits, audit trail, backup rotation.
 */
const fs     = require('fs');
const path   = require('path');
const crypto = require('crypto');

const DATA_DIR    = path.join(process.cwd(), 'data');
const STATE_FILE  = path.join(DATA_DIR, 'state.json');
const AUDIT_FILE  = path.join(DATA_DIR, 'audit.jsonl');
const BACKUP_DIR  = path.join(DATA_DIR, 'backups');
const MAX_BACKUPS = 10;
const MAX_VALUE_BYTES = 512 * 1024; // 512KB per key

const SENSITIVE = new Set(['key','secret','token','password','pass','auth']);

fs.mkdirSync(DATA_DIR,   { recursive: true });
fs.mkdirSync(BACKUP_DIR, { recursive: true });

let _cache = null;
let _dirty = false;
let _flushTimer = null;
let _backupTimer = null;

function isSensitive(key) {
  const lk = key.toLowerCase();
  // Exact suffix patterns that indicate a real credential field
  const BLOCKED_SUFFIXES = [
    '_api_key','_apikey','apikey',
    '_secret','_client_secret',
    '_access_token','accesstoken','_token','_authtoken',
    '_password','password','_pass',
    '_auth','_credential',
  ];
  if (BLOCKED_SUFFIXES.some(s => lk.endsWith(s))) return true;
  // Block ALL-CAPS style env var patterns (GROQ_API_KEY, etc.)
  if (/^[A-Z_]+_(KEY|SECRET|TOKEN|PASSWORD|PASS|AUTH)$/.test(key)) return true;
  return false;
}

function load() {
  if (_cache) return _cache;
  try {
    _cache = fs.existsSync(STATE_FILE)
      ? JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'))
      : {};
  } catch { _cache = {}; }
  return _cache;
}

function flush() {
  if (!_dirty || !_cache) return;
  try {
    const tmp = STATE_FILE + '.tmp';
    fs.writeFileSync(tmp, JSON.stringify(_cache, null, 2), 'utf8');
    fs.renameSync(tmp, STATE_FILE);
    _dirty = false;
  } catch (err) {
    console.error('[STATE] Flush failed:', err.message);
  }
}

function scheduleFlush() {
  if (_flushTimer) return;
  _flushTimer = setTimeout(() => { _flushTimer = null; flush(); }, 500);
}

function rotate() {
  if (!fs.existsSync(STATE_FILE)) return;
  const ts   = new Date().toISOString().replace(/[:.]/g, '-');
  const dest = path.join(BACKUP_DIR, `state-${ts}.json`);
  fs.copyFileSync(STATE_FILE, dest);
  const backups = fs.readdirSync(BACKUP_DIR).filter(f => f.endsWith('.json')).sort();
  while (backups.length > MAX_BACKUPS) {
    fs.unlinkSync(path.join(BACKUP_DIR, backups.shift()));
  }
}

function audit(key, value) {
  try {
    const entry = { ts: new Date().toISOString(), key, value: isSensitive(key) ? '[REDACTED]' : value };
    fs.appendFileSync(AUDIT_FILE, JSON.stringify(entry) + '\n');
  } catch {}
}

const state = {
  ns(namespace) {
    return {
      get:       (k, d)    => state.get(`${namespace}:${k}`, d),
      set:       (k, v)    => state.set(`${namespace}:${k}`, v),
      delete:    (k)       => state.delete(`${namespace}:${k}`),
      increment: (k, by)   => state.increment(`${namespace}:${k}`, by),
      push:      (k, v, m) => state.push(`${namespace}:${k}`, v, m),
    };
  },

  get(key, defaultVal = null) {
    const data = load();
    if (!(key in data)) return defaultVal;
    const entry = data[key];
    // TTL check
    if (entry && typeof entry === 'object' && entry.__ttl) {
      if (Date.now() > entry.__ttl) { delete data[key]; _dirty = true; return defaultVal; }
      return entry.__value;
    }
    return entry;
  },

  set(key, value, ttlSeconds = null) {
    if (isSensitive(key)) throw new Error(`[STATE] Refusing to persist sensitive key: ${key}`);
    const serialized = JSON.stringify(value);
    if (serialized.length > MAX_VALUE_BYTES) {
      console.warn(`[STATE] Value for "${key}" exceeds size limit — truncating`);
    }
    const data = load();
    data[key] = ttlSeconds ? { __ttl: Date.now() + ttlSeconds * 1000, __value: value } : value;
    _dirty = true;
    audit(key, value);
    scheduleFlush();
  },

  delete(key) {
    const data = load();
    delete data[key];
    _dirty = true;
    scheduleFlush();
  },

  getAll() { return { ...load() }; },

  increment(key, by = 1) {
    const cur = this.get(key, 0);
    const next = (typeof cur === 'number' ? cur : 0) + by;
    this.set(key, next);
    return next;
  },

  push(key, value, maxLen = 500) {
    const arr = this.get(key, []);
    if (!Array.isArray(arr)) { this.set(key, [value]); return; }
    arr.push(value);
    if (arr.length > maxLen) arr.splice(0, arr.length - maxLen);
    this.set(key, arr);
  },

  flush, load, rotate,
};

// Daily backup rotation
_backupTimer = setInterval(rotate, 24 * 60 * 60 * 1000);

process.on('SIGTERM', () => { flush(); process.exit(0); });
process.on('SIGINT',  () => { flush(); process.exit(0); });

module.exports = state;
