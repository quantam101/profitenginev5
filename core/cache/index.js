'use strict';
/**
 * core/cache/index.js — ProfitEngine v5.0
 * Three-level cache: L1 hot (Map), L2 warm (disk JSON), L3 miss.
 * Namespace support. LRU eviction. Stats collection.
 */
const fs   = require('fs');
const path = require('path');
const crypto = require('crypto');

const CACHE_DIR  = path.join(process.cwd(), 'data', 'cache');
const MAX_HOT    = 1000;
const L1         = new Map();
const stats_     = { hits: 0, misses: 0, evictions: 0 };

fs.mkdirSync(CACHE_DIR, { recursive: true });

function cacheFile(ns) { return path.join(CACHE_DIR, `${ns}.json`); }

function loadDisk(ns) {
  try {
    const f = cacheFile(ns);
    if (fs.existsSync(f)) return JSON.parse(fs.readFileSync(f, 'utf8'));
  } catch {}
  return {};
}

function saveDisk(ns, disk) {
  try {
    const now   = Date.now();
    const clean = {};
    for (const [k, v] of Object.entries(disk)) { if (v.exp > now) clean[k] = v; }
    const tmp = cacheFile(ns) + '.tmp';
    fs.writeFileSync(tmp, JSON.stringify(clean), 'utf8');
    fs.renameSync(tmp, cacheFile(ns));
  } catch {}
}

function l1Key(ns, key) { return `${ns}:${key}`; }

function evictL1() {
  if (L1.size < MAX_HOT) return;
  const oldest = [...L1.entries()].sort((a, b) => a[1].ts - b[1].ts)[0];
  L1.delete(oldest[0]);
  stats_.evictions++;
}

const _disks = {};

function get(ns, key) {
  const lk = l1Key(ns, key);
  const h  = L1.get(lk);
  if (h && h.exp > Date.now()) { stats_.hits++; h.ts = Date.now(); return h.v; }
  L1.delete(lk);
  if (!_disks[ns]) _disks[ns] = loadDisk(ns);
  const d = _disks[ns][key];
  if (d && d.exp > Date.now()) {
    evictL1(); L1.set(lk, { v: d.v, exp: d.exp, ts: Date.now() });
    stats_.hits++;
    return d.v;
  }
  stats_.misses++;
  return null;
}

function set(ns, key, value, ttlSeconds = 3600) {
  const exp = Date.now() + ttlSeconds * 1000;
  const lk  = l1Key(ns, key);
  evictL1();
  L1.set(lk, { v: value, exp, ts: Date.now() });
  if (!_disks[ns]) _disks[ns] = loadDisk(ns);
  _disks[ns][key] = { v: value, exp };
  saveDisk(ns, _disks[ns]);
}

function invalidate(ns, key) {
  L1.delete(l1Key(ns, key));
  if (_disks[ns]) { delete _disks[ns][key]; saveDisk(ns, _disks[ns]); }
}

function flush(ns) {
  for (const k of [...L1.keys()]) { if (k.startsWith(ns + ':')) L1.delete(k); }
  _disks[ns] = {};
  saveDisk(ns, {});
}

function stats() { return { ...stats_, l1Size: L1.size }; }

// Namespaced accessor factory
function ns(namespace) {
  return {
    get:        (k)       => get(namespace, k),
    set:        (k, v, t) => set(namespace, k, v, t),
    invalidate: (k)       => invalidate(namespace, k),
    flush:      ()        => flush(namespace),
  };
}

module.exports = { get, set, invalidate, flush, ns, stats };
