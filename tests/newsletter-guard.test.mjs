import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, writeFileSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { decide, EXIT, ISSUE_SCHEMA, summaryMarkdown } from '../scripts/newsletter-guard.mjs';

const NOW = new Date('2026-10-26T13:00:00Z');
const base = (over = {}) => ({
  schema: ISSUE_SCHEMA,
  dataDate: '2026-10-26',
  fingerprint: 'abc123def4567890',
  opportunities: [],
  signals: [],
  previous: {},
  ...over,
});

test('fresh verified lead → send (exit 0)', () => {
  const r = decide(base({
    dataDate: '2026-10-25',
    opportunities: [{ section: 'Contracts and bids', title: 'Phoenix cabling RFQ', url: 'https://example.gov/rfq/1' }],
  }), { now: NOW });
  assert.equal(r.decision, 'send');
  assert.equal(r.exitCode, 0);
  assert.equal(r.ageDays, 1);
  assert.equal(r.opportunities, 1);
});

test('stale 10/19 payload evaluated on 10/26 → stale (exit 3)', () => {
  const r = decide(base({
    dataDate: '2026-10-19',
    signals: [{ title: '13 verified public videos', url: 'https://www.youtube.com/@alreadyherellc' }],
  }), { now: NOW });
  assert.equal(r.decision, 'stale');
  assert.equal(r.exitCode, 3);
  assert.equal(r.ageDays, 7);
  assert.match(r.reason, /7 days old/);
});

test('missing dataDate → invalid (exit 2), never a send', () => {
  const r = decide(base({ dataDate: null, opportunities: [{ title: 'x' }] }), { now: NOW });
  assert.equal(r.decision, 'invalid');
  assert.equal(r.exitCode, 2);
  assert.equal(decide(base({ dataDate: '10/26/2026' }), { now: NOW }).decision, 'invalid');
  assert.equal(decide(base({ dataDate: '2026-02-31' }), { now: NOW }).decision, 'invalid');
  assert.equal(decide(base({ dataDate: '2026-10-27' }), { now: NOW }).decision, 'invalid');
  assert.equal(decide(null).decision, 'invalid');
  assert.equal(decide(base({ schema: 'something-else' }), { now: NOW }).decision, 'invalid');
});

test('same fingerprint as the last sent issue → stale (exit 3)', () => {
  const r = decide(base({
    opportunities: [{ title: 'repeat lead' }],
    previous: { fingerprint: 'abc123def4567890', sentAt: '2026-10-23T13:04:00Z' },
  }), { now: NOW });
  assert.equal(r.decision, 'stale');
  assert.equal(r.exitCode, 3);
  assert.match(r.reason, /identical to the issue sent 2026-10-23/);
  const changed = decide(base({
    opportunities: [{ title: 'new lead' }],
    previous: { fingerprint: 'other' },
  }), { now: NOW });
  assert.equal(changed.decision, 'send');
});

test('signals only → brief (exit 0); nothing → empty (exit 4)', () => {
  const brief = decide(base({ signals: [{ title: '2 verified public videos', url: 'https://youtube.com' }] }), { now: NOW });
  assert.equal(brief.decision, 'brief');
  assert.equal(brief.exitCode, 0);
  const empty = decide(base(), { now: NOW });
  assert.equal(empty.decision, 'empty');
  assert.equal(empty.exitCode, EXIT.empty);
});

test('max age window is configurable and inclusive', () => {
  const twoDays = base({ dataDate: '2026-10-24', signals: [{ title: 's' }] });
  assert.equal(decide(twoDays, { now: NOW }).decision, 'brief');
  assert.equal(decide(twoDays, { now: NOW, maxAgeDays: 1 }).decision, 'stale');
  assert.equal(decide(base({ dataDate: '2026-10-23', signals: [{ title: 's' }] }), { now: NOW, maxAgeDays: 3 }).decision, 'brief');
});

test('CLI: exit code, JSON on stdout, GITHUB_OUTPUT + summary written', () => {
  const dir = mkdtempSync(join(tmpdir(), 'nl-guard-'));
  const issuePath = join(dir, 'issue.json');
  const outPath = join(dir, 'gh_output');
  const sumPath = join(dir, 'gh_summary');
  writeFileSync(outPath, '');
  writeFileSync(sumPath, '');
  const today = new Date().toISOString().slice(0, 10);
  writeFileSync(issuePath, JSON.stringify(base({
    dataDate: today,
    opportunities: [{ title: 'lead' }],
  })));
  const run = spawnSync(process.execPath, ['scripts/newsletter-guard.mjs', issuePath], {
    encoding: 'utf8',
    env: { ...process.env, GITHUB_OUTPUT: outPath, GITHUB_STEP_SUMMARY: sumPath },
  });
  assert.equal(run.status, 0, run.stderr);
  const parsed = JSON.parse(run.stdout.trim());
  assert.equal(parsed.decision, 'send');
  const ghOut = readFileSync(outPath, 'utf8');
  assert.match(ghOut, /^decision=send$/m);
  assert.match(ghOut, /^exit_code=0$/m);
  assert.match(readFileSync(sumPath, 'utf8'), /\*\*send\*\* \(exit 0\)/);

  const missing = spawnSync(process.execPath, ['scripts/newsletter-guard.mjs', join(dir, 'nope.json')], { encoding: 'utf8' });
  assert.equal(missing.status, 2);
  assert.match(JSON.parse(missing.stdout.trim()).reason, /nope\.json/);

  const stale = spawnSync(process.execPath, ['scripts/newsletter-guard.mjs', issuePath, '--max-age-days', '0'], {
    encoding: 'utf8',
    env: { ...process.env, GITHUB_OUTPUT: '', GITHUB_STEP_SUMMARY: '' },
  });
  assert.equal(stale.status, 0, 'today\'s data is 0 days old and allowed at max 0');
});

test('summary markdown escapes pipes and lists every field', () => {
  const md = summaryMarkdown({ decision: 'stale', exitCode: 3, reason: 'a | b', dataDate: '2026-10-19', ageDays: 7, opportunities: 0, signals: 1, fingerprint: 'f' });
  assert.match(md, /a \\\| b/);
  assert.match(md, /\| Data age \(days\) \| 7 \|/);
});
