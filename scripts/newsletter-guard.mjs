#!/usr/bin/env node
// Newsletter send gate. Reads the issue payload written by
// `python scripts/make_newsletter.py compose` and decides whether it may go
// out. The sender refuses anything that is not `send` or `brief`, and the
// workflow only runs the sender when this process exits 0.
//
//   exit 0  send   — fresh data with at least one verified opportunity
//   exit 0  brief  — fresh data, no opportunities, but new production/market signals
//   exit 2  invalid — payload unusable (missing/malformed dataDate, wrong schema)
//   exit 3  stale  — data older than the allowed window, or identical to the last sent issue
//   exit 4  empty  — fresh but nothing to say (no opportunities, no signals)
//
// Usage: node scripts/newsletter-guard.mjs [issue.json] [--max-age-days N]
// Env:   NEWSLETTER_MAX_DATA_AGE_DAYS (default 2), GITHUB_OUTPUT, GITHUB_STEP_SUMMARY
import { readFileSync, appendFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

export const ISSUE_SCHEMA = 'already-here-issue/1';
export const EXIT = Object.freeze({ send: 0, brief: 0, invalid: 2, stale: 3, empty: 4 });
export const DEFAULT_MAX_AGE_DAYS = 2;

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const DAY_MS = 86_400_000;

function utcDay(date) {
  return Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate());
}

function parseDataDate(value) {
  if (typeof value !== 'string' || !DATE_RE.test(value)) return null;
  const ms = Date.parse(`${value}T00:00:00Z`);
  if (Number.isNaN(ms)) return null;
  // reject 2026-02-31 style dates that Date.parse silently rolls over
  if (new Date(ms).toISOString().slice(0, 10) !== value) return null;
  return ms;
}

function countList(value) {
  return Array.isArray(value) ? value.filter((x) => x && typeof x === 'object').length : 0;
}

/**
 * Pure decision function. Never throws on bad input — bad input is a decision.
 * @returns {{decision:'send'|'brief'|'invalid'|'stale'|'empty', exitCode:number, reason:string,
 *            dataDate:string|null, ageDays:number|null, opportunities:number, signals:number,
 *            fingerprint:string|null}}
 */
export function decide(issue, { now = new Date(), maxAgeDays = DEFAULT_MAX_AGE_DAYS } = {}) {
  const base = {
    dataDate: null, ageDays: null, opportunities: 0, signals: 0, fingerprint: null,
  };
  const verdict = (decision, reason, extra = {}) => ({
    decision, exitCode: EXIT[decision], reason, ...base, ...extra,
  });

  if (!issue || typeof issue !== 'object' || Array.isArray(issue)) {
    return verdict('invalid', 'issue payload is not a JSON object');
  }
  if (issue.schema !== ISSUE_SCHEMA) {
    return verdict('invalid', `schema is ${JSON.stringify(issue.schema ?? null)}, expected ${ISSUE_SCHEMA}`);
  }
  const opportunities = countList(issue.opportunities);
  const signals = countList(issue.signals);
  const fingerprint = typeof issue.fingerprint === 'string' && issue.fingerprint ? issue.fingerprint : null;
  const dataMs = parseDataDate(issue.dataDate);
  if (dataMs === null) {
    return verdict('invalid', 'dataDate missing or not YYYY-MM-DD — sourcing step did not record a run date',
      { opportunities, signals, fingerprint });
  }
  const dataDate = issue.dataDate;
  const ageDays = Math.round((utcDay(now) - dataMs) / DAY_MS);
  const ctx = { dataDate, ageDays, opportunities, signals, fingerprint };
  if (ageDays < 0) {
    return verdict('invalid', `dataDate ${dataDate} is in the future`, ctx);
  }
  if (!fingerprint) {
    return verdict('invalid', 'fingerprint missing — cannot de-duplicate against the last sent issue', ctx);
  }
  if (ageDays > maxAgeDays) {
    return verdict('stale', `data is ${ageDays} days old (dataDate ${dataDate}, max ${maxAgeDays})`, ctx);
  }
  const previous = issue.previous && typeof issue.previous === 'object' ? issue.previous : {};
  if (previous.fingerprint && previous.fingerprint === fingerprint) {
    const when = previous.sentAt || previous.dataDate || 'a prior run';
    return verdict('stale', `content fingerprint ${fingerprint} is identical to the issue sent ${when}`, ctx);
  }
  if (opportunities > 0) {
    return verdict('send', `${opportunities} verified opportunit${opportunities === 1 ? 'y' : 'ies'}, data ${ageDays} day(s) old`, ctx);
  }
  if (signals > 0) {
    return verdict('brief', `no opportunities; ${signals} new signal(s), data ${ageDays} day(s) old`, ctx);
  }
  return verdict('empty', 'fresh data but no opportunities and no signals — nothing worth sending', ctx);
}

export function loadIssue(path) {
  try {
    return JSON.parse(readFileSync(path, 'utf8'));
  } catch (err) {
    return { __loadError: `${path}: ${err.message}` };
  }
}

export function summaryMarkdown(result) {
  const rows = [
    ['Decision', `**${result.decision}** (exit ${result.exitCode})`],
    ['Reason', result.reason],
    ['Data date', result.dataDate ?? '—'],
    ['Data age (days)', result.ageDays ?? '—'],
    ['Opportunities', String(result.opportunities)],
    ['Signals', String(result.signals)],
    ['Fingerprint', result.fingerprint ?? '—'],
  ];
  return ['### Newsletter guard', '', '| Field | Value |', '|---|---|',
    ...rows.map(([k, v]) => `| ${k} | ${String(v).replace(/\|/g, '\\|')} |`), ''].join('\n');
}

function parseArgs(argv) {
  let path = 'issue.json';
  let maxAgeDays = Number(process.env.NEWSLETTER_MAX_DATA_AGE_DAYS || DEFAULT_MAX_AGE_DAYS);
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === '--max-age-days') { maxAgeDays = Number(argv[i + 1]); i += 1; }
    else path = argv[i];
  }
  if (!Number.isFinite(maxAgeDays) || maxAgeDays < 0) maxAgeDays = DEFAULT_MAX_AGE_DAYS;
  return { path, maxAgeDays };
}

export function main(argv = process.argv.slice(2), env = process.env) {
  const { path, maxAgeDays } = parseArgs(argv);
  const issue = loadIssue(path);
  const result = issue.__loadError
    ? { ...decide(null), reason: issue.__loadError }
    : decide(issue, { maxAgeDays });
  process.stdout.write(`${JSON.stringify(result)}\n`);
  if (env.GITHUB_OUTPUT) {
    appendFileSync(env.GITHUB_OUTPUT,
      `decision=${result.decision}\nexit_code=${result.exitCode}\nreason=${result.reason.replace(/\r?\n/g, ' ')}\n`);
  }
  if (env.GITHUB_STEP_SUMMARY) {
    appendFileSync(env.GITHUB_STEP_SUMMARY, `${summaryMarkdown(result)}\n`);
  }
  return result.exitCode;
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  process.exit(main());
}
