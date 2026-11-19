#!/usr/bin/env node
/**
 * Vercel Ignored Build Step.
 *
 * Exit 0 skips the deployment; exit 1 continues the build. We only skip when
 * every changed path is automation data consumed by GitHub Actions/runtime
 * workflows, never by the Next.js app. `data/revenue-os/` is deliberately not
 * allowlisted because lib/revenue-os imports its seed file.
 */
import { execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';

const AUTOMATION_DATA_PATTERNS = [
  /^DAILY_REVENUE_REPORT\.md$/,
  /^daily_revenue_\d{4}-\d{2}-\d{2}\.json$/,
  /^data\/strategy\/signals\.json$/,
  /^data\/field_income\.csv$/,
  /^data\/newsletter_ledger\.json$/,
];

export function isAutomationDataPath(path) {
  return AUTOMATION_DATA_PATTERNS.some((pattern) => pattern.test(path));
}

export function isAutomationDataOnly(paths) {
  return paths.length > 0 && paths.every(isAutomationDataPath);
}

function defaultGit(args, cwd) {
  return execFileSync('git', args, { cwd, encoding: 'utf8' });
}

export function main({
  env = process.env,
  cwd = process.cwd(),
  runGit = defaultGit,
  log = console.log,
} = {}) {
  const current = env.VERCEL_GIT_COMMIT_SHA || 'HEAD';
  let previous = env.VERCEL_GIT_PREVIOUS_SHA || '';

  if (!previous) {
    try {
      previous = runGit(['rev-parse', '--verify', 'HEAD^'], cwd).trim();
    } catch {
      log('[vercel-ignore] build: no previous deployment SHA and HEAD^ is unavailable');
      return 1;
    }
  }

  let diff;
  try {
    diff = runGit(['diff', '--name-only', '-z', '--no-renames', previous, current, '--'], cwd);
  } catch (error) {
    log(`[vercel-ignore] build: git diff failed (${error instanceof Error ? error.message : String(error)})`);
    return 1;
  }

  const paths = diff.split('\0').map((path) => path.trim()).filter(Boolean);
  if (!paths.length) {
    log('[vercel-ignore] build: no changed paths resolved; refusing to skip');
    return 1;
  }

  const nonDataPaths = paths.filter((path) => !isAutomationDataPath(path));
  if (nonDataPaths.length) {
    const preview = nonDataPaths.slice(0, 5).join(', ');
    log(`[vercel-ignore] build: non-automation paths changed (${preview}${nonDataPaths.length > 5 ? ', …' : ''})`);
    return 1;
  }

  log(`[vercel-ignore] skip: only automation data changed (${paths.length} file${paths.length === 1 ? '' : 's'})`);
  return 0;
}

const isMain = process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href;
if (isMain) {
  process.exitCode = main();
}
