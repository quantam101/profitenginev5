import assert from 'node:assert/strict';
import { isAutomationDataOnly, main } from '../scripts/vercel-ignore-build.mjs';

assert.equal(isAutomationDataOnly([
  'DAILY_REVENUE_REPORT.md',
  'daily_revenue_2026-11-07.json',
  'data/strategy/signals.json',
  'data/field_income.csv',
  'data/newsletter_ledger.json',
]), true);

assert.equal(isAutomationDataOnly([]), false);
assert.equal(isAutomationDataOnly(['data/revenue-os/revenue-plays.seed.json']), false);
assert.equal(isAutomationDataOnly(['data/strategy/signals.json', 'app/page.tsx']), false);

function fakeGit(diff) {
  return (args) => {
    if (args[0] === 'rev-parse') return 'base-sha\n';
    if (args[0] === 'diff') return diff;
    throw new Error(`unexpected git args: ${args.join(' ')}`);
  };
}

const logs = [];
const log = (message) => logs.push(message);

let code = main({
  env: {},
  runGit: fakeGit('DAILY_REVENUE_REPORT.md\0daily_revenue_2026-11-07.json\0data/strategy/signals.json\0'),
  log,
});
assert.equal(code, 0);
assert.match(logs.at(-1), /skip: only automation data changed/);

code = main({
  env: {},
  runGit: fakeGit('data/strategy/signals.json\0app/page.tsx\0'),
  log,
});
assert.equal(code, 1);
assert.match(logs.at(-1), /build: non-automation paths changed/);

code = main({
  env: {},
  runGit: () => { throw new Error('git unavailable'); },
  log,
});
assert.equal(code, 1);
assert.match(logs.at(-1), /build: no previous deployment SHA/);

console.log('vercel ignore build test passed');
