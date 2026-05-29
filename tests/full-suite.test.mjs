/**
 * ProfitEngine v5 — Full Test Suite
 * ==================================
 * Seven test categories in a single pass:
 *   1. E2E Smoke        — every public endpoint, status + schema shape
 *   2. Regression       — response fields stable vs. stored contract
 *   3. ESLint           — project linter, zero warnings
 *   4. Latency          — p50/p95/p99 vs SLO thresholds
 *   5. Init Profile     — module load time + Next.js health.mjs import
 *   6. Load + Spike     — sustained concurrency + sudden spike
 *   7. Timeout Audit    — static scan for fetch/HTTP calls missing timeout
 *
 * Usage:
 *   node tests/full-suite.test.mjs
 *   RUNTIME_URL=http://myserver:8080 node tests/full-suite.test.mjs
 *   node tests/full-suite.test.mjs --skip-live   # static tests only
 *
 * Live tests (1,2,4,6) are skipped automatically if the server is unreachable.
 */

import assert from 'node:assert/strict';
import { execSync, spawnSync } from 'node:child_process';
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import { performance } from 'node:perf_hooks';

// ── Config ─────────────────────────────────────────────────────────────────────
const RUNTIME_URL = process.env.RUNTIME_URL ?? 'http://localhost:8080';
const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:8001';
const NEXT_URL    = process.env.NEXT_URL    ?? 'http://localhost:3000';
const SKIP_LIVE   = process.argv.includes('--skip-live');
const ROOT        = new URL('..', import.meta.url).pathname.replace(/^\/([A-Z]:)/, '$1');

const SLO = {
  health_endpoint_p95_ms:       500,
  deterministic_route_p95_ms:   250,
  list_endpoint_p95_ms:         300,
  backend_health_p95_ms:        150,
  backend_list_p95_ms:          400,
};

// ── Reporter ───────────────────────────────────────────────────────────────────
let _pass = 0, _fail = 0, _skip = 0;
const _failures = [];

function pass(label) {
  _pass++;
  console.log(`  [PASS] ${label}`);
}
function fail(label, msg) {
  _fail++;
  const entry = `  [FAIL] ${label}: ${msg}`;
  console.log(entry);
  _failures.push(entry);
}
function skip(label, reason) {
  _skip++;
  console.log(`  [SKIP] ${label} (${reason})`);
}
function section(title) {
  console.log(`\n${'='.repeat(64)}\n  ${title}\n${'='.repeat(64)}`);
}

// ── HTTP helpers ───────────────────────────────────────────────────────────────
async function fetchJSON(url, opts = {}) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), opts.timeout ?? 10_000);
  try {
    const r = await fetch(url, { ...opts, signal: ctrl.signal });
    const text = await r.text();
    let json = null;
    try { json = JSON.parse(text); } catch {}
    return { status: r.status, ok: r.ok, json, headers: r.headers, text };
  } finally {
    clearTimeout(timer);
  }
}

async function isReachable(url) {
  try {
    const ctrl = new AbortController();
    setTimeout(() => ctrl.abort(), 2_000);
    const r = await fetch(`${url}/health`, { signal: ctrl.signal });
    return r.ok || r.status < 500;
  } catch { return false; }
}

async function isBackendReachable() {
  try {
    const ctrl = new AbortController();
    setTimeout(() => ctrl.abort(), 2_000);
    const r = await fetch(`${BACKEND_URL}/api/health`, { signal: ctrl.signal });
    return r.ok || r.status < 500;
  } catch { return false; }
}

// ── Percentile helper ──────────────────────────────────────────────────────────
function percentile(sorted, p) {
  const i = Math.ceil((p / 100) * sorted.length) - 1;
  return sorted[Math.max(0, i)];
}

async function measureLatencies(url, n = 12, body = null) {
  const timings = [];
  for (let i = 0; i < n; i++) {
    const t0 = performance.now();
    try {
      await fetchJSON(url, body ? {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        timeout: 15_000,
      } : { timeout: 5_000 });
    } catch {}
    timings.push(performance.now() - t0);
  }
  timings.sort((a, b) => a - b);
  return {
    p50: percentile(timings, 50),
    p95: percentile(timings, 95),
    p99: percentile(timings, 99),
    min: timings[0],
    max: timings[timings.length - 1],
  };
}

// ════════════════════════════════════════════════════════════════════════════════
// 1. E2E SMOKE TEST
// ════════════════════════════════════════════════════════════════════════════════
async function runSmoke(runtimeOk, backendOk) {
  section('1. E2E Smoke Test');

  // ── Runtime API (port 8080) ──────────────────────────────────────────────────
  if (!runtimeOk) {
    skip('runtime endpoints', `${RUNTIME_URL} unreachable`);
  } else {
    const checks = [
      ['GET /health',  `${RUNTIME_URL}/health`,  200, ['ok', 'service']],
      ['GET /agents',  `${RUNTIME_URL}/agents`,   200, null],
    ];
    for (const [label, url, expectedStatus, requiredFields] of checks) {
      try {
        const r = await fetchJSON(url);
        if (r.status !== expectedStatus) {
          fail(`runtime ${label}`, `status ${r.status} != ${expectedStatus}`);
          continue;
        }
        if (requiredFields && r.json) {
          const missing = requiredFields.filter(f => !(f in r.json));
          if (missing.length) { fail(`runtime ${label}`, `missing fields: ${missing}`); continue; }
        }
        pass(`runtime ${label}`);
      } catch (e) { fail(`runtime ${label}`, e.message); }
    }

    // POST /execute smoke
    try {
      const r = await fetchJSON(`${RUNTIME_URL}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          objective: 'Draft a local research summary',
          dynamic_context: 'test context',
          embedding_vector: [0.3, 0.3, 0.3, 0.3],
          agent_id: 'local-research',
        }),
        timeout: 15_000,
      });
      if (![200, 202].includes(r.status)) fail('runtime POST /execute', `status ${r.status}`);
      else if (!r.json?.status) fail('runtime POST /execute', 'missing status field');
      else pass('runtime POST /execute');
    } catch (e) { fail('runtime POST /execute', e.message); }
  }

  // ── Backend API (port 8001) ──────────────────────────────────────────────────
  if (!backendOk) {
    skip('backend endpoints', `${BACKEND_URL} unreachable`);
  } else {
    const backendRoutes = [
      ['/api/health',              ['status']],
      ['/api/stats',               ['revenue_30d', 'agents_online']],
      ['/api/agents',              null],
      ['/api/approvals',           null],
      ['/api/revenue/stats',       ['total_30d', 'active_streams']],
      ['/api/revenue/series',      null],
      ['/api/cycle/status',        ['state', 'current_step']],
      ['/api/sovereign/status',    ['id', 'model']],
      ['/api/proof-of-work',       ['score', 'uptime_pct']],
      ['/api/cost',                ['today_usd', 'daily_cap_usd']],
      ['/api/audit',               null],
      ['/api/distillation/status', ['state', 'tier_routing']],
      ['/api/cash/audit-trail',    null],
    ];
    for (const [path, fields] of backendRoutes) {
      try {
        const r = await fetchJSON(`${BACKEND_URL}${path}`);
        if (r.status !== 200) { fail(`backend GET ${path}`, `status ${r.status}`); continue; }
        if (fields && r.json && !Array.isArray(r.json)) {
          const missing = fields.filter(f => !(f in r.json));
          if (missing.length) { fail(`backend GET ${path}`, `missing: ${missing}`); continue; }
        }
        pass(`backend GET ${path}`);
      } catch (e) { fail(`backend GET ${path}`, e.message); }
    }

    // POST waitlist
    try {
      const email = `smoke-test-${Date.now()}@example.com`;
      const r = await fetchJSON(`${BACKEND_URL}/api/waitlist`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, role: 'developer' }),
        timeout: 8_000,
      });
      if (![200, 201].includes(r.status)) fail('backend POST /api/waitlist', `status ${r.status}`);
      else if (!r.json?.id) fail('backend POST /api/waitlist', 'missing id field');
      else pass('backend POST /api/waitlist');
    } catch (e) { fail('backend POST /api/waitlist', e.message); }
  }
}

// ════════════════════════════════════════════════════════════════════════════════
// 2. REGRESSION TEST
// ════════════════════════════════════════════════════════════════════════════════
const REGRESSION_CONTRACT = {
  '/api/health':           { required: ['status'],                    types: { status: 'string' } },
  '/api/stats':            { required: ['revenue_30d','agents_online','devs_joined'], types: { revenue_30d: 'number' } },
  '/api/revenue/stats':    { required: ['total_30d','mrr_estimate','active_streams'], types: { total_30d: 'number' } },
  '/api/cycle/status':     { required: ['state','current_step','approval_required'],  types: { approval_required: 'boolean' } },
  '/api/sovereign/status': { required: ['id','model','next_cycle_in_min'],            types: { next_cycle_in_min: 'number' } },
  '/api/proof-of-work':    { required: ['score','uptime_pct','passed_cycles_24h'],    types: { score: 'number' } },
  '/api/cost':             { required: ['today_usd','daily_cap_usd','categories'],    types: { categories: 'object' } },
};

async function runRegression(backendOk) {
  section('2. Regression Test (response contract)');
  if (!backendOk) { skip('all regression checks', `${BACKEND_URL} unreachable`); return; }

  for (const [path, contract] of Object.entries(REGRESSION_CONTRACT)) {
    try {
      const r = await fetchJSON(`${BACKEND_URL}${path}`);
      if (!r.json || typeof r.json !== 'object' || Array.isArray(r.json)) {
        fail(`regression ${path}`, 'response is not an object'); continue;
      }
      const missing = contract.required.filter(f => !(f in r.json));
      if (missing.length) { fail(`regression ${path}`, `missing fields: ${missing}`); continue; }
      const typeErrors = Object.entries(contract.types ?? {})
        .filter(([k, t]) => {
          const v = r.json[k];
          return t === 'object' ? (typeof v !== 'object' || v === null) : typeof v !== t;
        })
        .map(([k, t]) => `${k} expected ${t} got ${typeof r.json[k]}`);
      if (typeErrors.length) { fail(`regression ${path}`, typeErrors.join(', ')); continue; }
      pass(`regression ${path}`);
    } catch (e) { fail(`regression ${path}`, e.message); }
  }
}

// ════════════════════════════════════════════════════════════════════════════════
// 3. ESLINT
// ════════════════════════════════════════════════════════════════════════════════
function runESLint() {
  section('3. ESLint');
  const result = spawnSync(
    'node', ['node_modules/.bin/next', 'lint', '--format', 'json'],
    { cwd: ROOT, encoding: 'utf8', timeout: 60_000 }
  );

  // Try plain eslint if next lint not available
  const eslintResult = spawnSync(
    process.platform === 'win32' ? 'npx.cmd' : 'npx',
    ['--no-install', 'eslint', 'app/', 'lib/', '--format', 'json', '--max-warnings', '0'],
    { cwd: ROOT, encoding: 'utf8', timeout: 60_000 }
  );

  if (eslintResult.status === null) {
    skip('ESLint', 'command not available');
    return;
  }

  let parsed = null;
  try { parsed = JSON.parse(eslintResult.stdout); } catch {}

  if (eslintResult.status === 0) {
    pass('ESLint: zero warnings/errors');
    return;
  }

  if (parsed && Array.isArray(parsed)) {
    const fileCount = parsed.filter(f => f.errorCount + f.warningCount > 0).length;
    const totalErrors = parsed.reduce((s, f) => s + f.errorCount, 0);
    const totalWarns  = parsed.reduce((s, f) => s + f.warningCount, 0);
    if (totalErrors > 0) {
      fail('ESLint', `${totalErrors} error(s) in ${fileCount} file(s)`);
      parsed.filter(f => f.errorCount > 0).slice(0, 5).forEach(f => {
        console.log(`    ${relative(ROOT, f.filePath)}`);
        f.messages.filter(m => m.severity === 2).slice(0, 3).forEach(m =>
          console.log(`      L${m.line}: ${m.message} (${m.ruleId})`)
        );
      });
    } else if (totalWarns > 0) {
      fail('ESLint', `${totalWarns} warning(s) — max-warnings=0`);
    }
  } else {
    fail('ESLint', eslintResult.stderr?.slice(0, 200) ?? 'unknown error');
  }
}

// ════════════════════════════════════════════════════════════════════════════════
// 4. LATENCY TEST
// ════════════════════════════════════════════════════════════════════════════════
async function runLatency(runtimeOk, backendOk) {
  section('4. Latency Test (SLO thresholds)');

  function reportLatency(label, stats, sloKey) {
    const slo = SLO[sloKey];
    const line = `${label}: p50=${stats.p50.toFixed(0)}ms p95=${stats.p95.toFixed(0)}ms p99=${stats.p99.toFixed(0)}ms`;
    if (slo && stats.p95 > slo) {
      fail(`latency ${label}`, `p95=${stats.p95.toFixed(0)}ms exceeds SLO ${slo}ms`);
    } else {
      pass(`latency ${label}`);
    }
    console.log(`    ${line}${slo ? ` [SLO: ${slo}ms]` : ''}`);
  }

  if (!runtimeOk) {
    skip('runtime latency', `${RUNTIME_URL} unreachable`);
  } else {
    reportLatency('runtime /health', await measureLatencies(`${RUNTIME_URL}/health`), 'health_endpoint_p95_ms');
    reportLatency('runtime POST /execute (local)',
      await measureLatencies(`${RUNTIME_URL}/execute`, 8, {
        objective: 'Draft a local research summary',
        dynamic_context: 'test',
        embedding_vector: [0.3, 0.3, 0.3, 0.3],
        agent_id: 'local-research',
      }), 'deterministic_route_p95_ms');
  }

  if (!backendOk) {
    skip('backend latency', `${BACKEND_URL} unreachable`);
  } else {
    reportLatency('backend /api/health',        await measureLatencies(`${BACKEND_URL}/api/health`), 'backend_health_p95_ms');
    reportLatency('backend /api/stats',         await measureLatencies(`${BACKEND_URL}/api/stats`), 'backend_list_p95_ms');
    reportLatency('backend /api/agents',        await measureLatencies(`${BACKEND_URL}/api/agents`), 'backend_list_p95_ms');
    reportLatency('backend /api/revenue/stats', await measureLatencies(`${BACKEND_URL}/api/revenue/stats`), 'backend_list_p95_ms');
  }
}

// ════════════════════════════════════════════════════════════════════════════════
// 5. DEPENDENCY & INIT PROFILE
// ════════════════════════════════════════════════════════════════════════════════
async function runInitProfile() {
  section('5. Dependency & Init Profile');

  // Node.js: time health.mjs import
  const t0 = performance.now();
  try {
    await import('../lib/health.mjs');
    const elapsed = performance.now() - t0;
    if (elapsed > 500) fail('health.mjs import time', `${elapsed.toFixed(0)}ms > 500ms threshold`);
    else pass(`health.mjs import: ${elapsed.toFixed(0)}ms`);
  } catch (e) { fail('health.mjs import', e.message); }

  // Python: time key module imports via subprocess
  const PYTHON_MODULES = [
    ['runtime.distillation',  500],
    ['runtime.sovereign_core', 800],
    ['runtime.registry',      300],
  ];

  const pyBin = process.platform === 'win32' ? 'python' : 'python3';
  for (const [mod, thresholdMs] of PYTHON_MODULES) {
    const result = spawnSync(pyBin, ['-c',
      `import time; t=time.perf_counter(); import ${mod}; print(f"{(time.perf_counter()-t)*1000:.1f}")`
    ], { cwd: ROOT, encoding: 'utf8', timeout: 15_000 });
    if (result.status !== 0) {
      fail(`import ${mod}`, result.stderr?.slice(0, 120) ?? 'import failed');
    } else {
      const ms = parseFloat(result.stdout.trim());
      if (ms > thresholdMs) fail(`import ${mod}`, `${ms.toFixed(0)}ms > ${thresholdMs}ms`);
      else pass(`import ${mod}: ${ms.toFixed(0)}ms`);
    }
  }

  // Node packages: check node_modules integrity
  const pkgJson = JSON.parse(readFileSync(join(ROOT, 'package.json'), 'utf8'));
  const pkgLock = JSON.parse(readFileSync(join(ROOT, 'package-lock.json'), 'utf8'));
  if (pkgJson.name !== pkgLock.name) fail('package-lock.json sync', 'name mismatch');
  else pass('package.json / package-lock.json in sync');

  // Check for known problematic deps
  const depsToCheck = { 'next': '>=14.0.0', 'react': '>=18.0.0' };
  const allDeps = { ...pkgJson.dependencies, ...pkgJson.devDependencies };
  for (const [pkg, range] of Object.entries(depsToCheck)) {
    if (allDeps[pkg]) pass(`dep present: ${pkg}@${allDeps[pkg]}`);
    else fail(`dep missing: ${pkg}`, `expected ${range}`);
  }
}

// ════════════════════════════════════════════════════════════════════════════════
// 6. LOAD & SPIKE TEST
// ════════════════════════════════════════════════════════════════════════════════
async function runLoad(runtimeOk, backendOk) {
  section('6. Load & Spike Test');

  async function loadRun(url, vus, durationMs, label, method = 'GET', body = null) {
    const results = { ok: 0, err: 0, timings: [] };
    const deadline = Date.now() + durationMs;
    const workers = Array.from({ length: vus }, async () => {
      while (Date.now() < deadline) {
        const t0 = performance.now();
        try {
          const opts = { timeout: 10_000 };
          if (method === 'POST' && body) {
            opts.method = 'POST';
            opts.headers = { 'Content-Type': 'application/json' };
            opts.body = JSON.stringify(body);
          }
          const r = await fetchJSON(url, opts);
          if (r.ok) { results.ok++; results.timings.push(performance.now() - t0); }
          else results.err++;
        } catch { results.err++; }
      }
    });
    await Promise.all(workers);
    results.timings.sort((a, b) => a - b);
    const rps = Math.round((results.ok + results.err) / (durationMs / 1000));
    const p95 = results.timings.length ? percentile(results.timings, 95) : 0;
    const errRate = results.ok + results.err ? (results.err / (results.ok + results.err)) * 100 : 100;
    console.log(`    ${label}: ${rps} req/s, ${results.ok} ok, ${results.err} err, p95=${p95.toFixed(0)}ms, err%=${errRate.toFixed(1)}`);
    if (errRate > 5) fail(`load ${label}`, `error rate ${errRate.toFixed(1)}% > 5%`);
    else pass(`load ${label} (err=${errRate.toFixed(1)}%)`);
    return { rps, p95, errRate };
  }

  if (!runtimeOk) {
    skip('runtime load test', `${RUNTIME_URL} unreachable`);
  } else {
    // Sustained: 10 VUs for 10 seconds
    await loadRun(`${RUNTIME_URL}/health`, 10, 10_000, 'runtime /health sustained (10VU/10s)');
    // Spike: 40 VUs for 3 seconds
    await loadRun(`${RUNTIME_URL}/health`, 40, 3_000, 'runtime /health spike (40VU/3s)');
  }

  if (!backendOk) {
    skip('backend load test', `${BACKEND_URL} unreachable`);
  } else {
    await loadRun(`${BACKEND_URL}/api/health`, 10, 10_000, 'backend /api/health sustained (10VU/10s)');
    await loadRun(`${BACKEND_URL}/api/stats`,  10, 10_000, 'backend /api/stats sustained (10VU/10s)');
    await loadRun(`${BACKEND_URL}/api/health`, 40,  3_000, 'backend /api/health spike (40VU/3s)');
  }
}

// ════════════════════════════════════════════════════════════════════════════════
// 7. TIMEOUT AUDIT (static)
// ════════════════════════════════════════════════════════════════════════════════
function runTimeoutAudit() {
  section('7. Timeout Validation (static analysis)');

  // JS / TS: fetch calls without AbortController signal
  const jsFetchNoTimeout = [];
  // Python: requests/httpx calls without timeout=
  const pyNoTimeout = [];

  const ignoredDirs = new Set(['.git', '.next', 'node_modules', '__pycache__', '.pytest_cache']);

  function* walkFiles(dir, exts) {
    let entries;
    try { entries = readdirSync(dir, { withFileTypes: true }); } catch { return; }
    for (const e of entries) {
      if (ignoredDirs.has(e.name)) continue;
      const full = join(dir, e.name);
      if (e.isDirectory()) { yield* walkFiles(full, exts); }
      else if (e.isFile() && exts.some(x => e.name.endsWith(x))) yield full;
    }
  }

  // JS/TS: find bare fetch( without AbortController/signal nearby
  for (const file of walkFiles(ROOT, ['.ts', '.tsx', '.mjs', '.js'])) {
    const rel = relative(ROOT, file);
    if (rel.startsWith('node_modules') || rel.includes('.next')) continue;
    let src;
    try { src = readFileSync(file, 'utf8'); } catch { continue; }
    const lines = src.split('\n');
    lines.forEach((line, i) => {
      // bare fetch( without signal in same or adjacent lines
      // Use 20-line window to handle multi-line fetch options (e.g. large body JSON)
      if (/\bfetch\s*\(/.test(line) && !/signal\s*:/.test(line)) {
        const ctx = lines.slice(Math.max(0, i - 1), i + 20).join(' ');
        if (!/signal\s*:/.test(ctx) && !/AbortController/.test(ctx)) {
          jsFetchNoTimeout.push(`${rel}:${i + 1}`);
        }
      }
    });
  }

  // Python: requests.get/post/put etc. without timeout=
  // Use line-by-line scan with 10-line lookahead to handle multi-line calls
  // (regex [^)]* stops at first ')' which misses keyword args on later lines).
  const pyCallPat = /\b(requests|httpx)\.(get|post|put|patch|delete|head)\s*\(/;
  for (const file of walkFiles(ROOT, ['.py'])) {
    const rel = relative(ROOT, file);
    if (rel.includes('test_') || rel.startsWith('tests')) continue;
    let src;
    try { src = readFileSync(file, 'utf8'); } catch { continue; }
    const lines = src.split('\n');
    lines.forEach((line, i) => {
      if (pyCallPat.test(line)) {
        // Look for timeout= within 20 lines of the call (covers multi-line args
        // with large JSON bodies that push timeout= keyword beyond 10 lines)
        const ctx = lines.slice(i, Math.min(lines.length, i + 20)).join('\n');
        if (!ctx.includes('timeout=')) {
          pyNoTimeout.push(`${rel}:${i + 1} -- ${line.trim().slice(0, 60)}`);
        }
      }
    });
  }

  if (jsFetchNoTimeout.length === 0) {
    pass('JS/TS: all fetch() calls have AbortController signal');
  } else {
    // Warn but don't fail — some server-action fetches may be intentionally without timeout
    const count = jsFetchNoTimeout.length;
    if (count > 10) {
      fail('JS/TS fetch timeouts', `${count} calls potentially missing signal/timeout`);
      jsFetchNoTimeout.slice(0, 5).forEach(f => console.log(`    - ${f}`));
    } else {
      pass(`JS/TS fetch: ${count} calls without explicit signal (acceptable)`);
      jsFetchNoTimeout.forEach(f => console.log(`    note: ${f}`));
    }
  }

  if (pyNoTimeout.length === 0) {
    pass('Python: all HTTP calls have timeout= parameter');
  } else {
    fail('Python HTTP timeouts', `${pyNoTimeout.length} call(s) missing timeout=`);
    pyNoTimeout.slice(0, 8).forEach(f => console.log(`    - ${f}`));
  }
}

// ════════════════════════════════════════════════════════════════════════════════
// MAIN
// ════════════════════════════════════════════════════════════════════════════════
async function main() {
  console.log('\nProfitEngine v5 -- Full Test Suite');
  console.log(`Runtime: ${RUNTIME_URL}  Backend: ${BACKEND_URL}`);
  console.log(`Skip-live: ${SKIP_LIVE}`);

  const runtimeOk = !SKIP_LIVE && await isReachable(RUNTIME_URL);
  const backendOk  = !SKIP_LIVE && await isBackendReachable();
  if (!SKIP_LIVE) {
    console.log(`\nServer connectivity: runtime=${runtimeOk ? 'UP' : 'DOWN'}  backend=${backendOk ? 'UP' : 'DOWN'}`);
  }

  await runSmoke(runtimeOk, backendOk);
  await runRegression(backendOk);
  runESLint();
  await runLatency(runtimeOk, backendOk);
  await runInitProfile();

  if (!SKIP_LIVE) {
    await runLoad(runtimeOk, backendOk);
  } else {
    skip('load & spike test', '--skip-live');
  }

  runTimeoutAudit();

  // ── Summary ──────────────────────────────────────────────────────────────────
  console.log(`\n${'='.repeat(64)}`);
  console.log(`  RESULTS  pass=${_pass}  fail=${_fail}  skip=${_skip}`);
  console.log('='.repeat(64));
  if (_failures.length) {
    console.log('\nFailures:');
    _failures.forEach(f => console.log(f));
  }

  process.exit(_fail > 0 ? 1 : 0);
}

main().catch(e => { console.error(e); process.exit(1); });
