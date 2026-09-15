import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { routeAI } from '../lib/ai-gateway.mjs';
import {
  collectRssSources,
  runPassiveIncomeCycle,
} from '../lib/revenue-os/passive-income-engine.mjs';

const now = new Date();
const agents = ['technical_product', 'stock_asset'];
if (now.getUTCDay() === 0) agents.push('newsletter');

const feedUrls = String(process.env.PASSIVE_INCOME_RSS_FEEDS || '')
  .split(',')
  .map((value) => value.trim())
  .filter(Boolean);

const rss = agents.includes('newsletter') && feedUrls.length
  ? await collectRssSources(feedUrls)
  : { ok: false, sources: [], errors: [] };

const result = await runPassiveIncomeCycle({
  publish: true,
  agents,
  sources: rss.sources,
  newsletterNiche: process.env.PASSIVE_INCOME_NEWSLETTER_NICHE || 'AI operations and infrastructure for small technology businesses',
}, {
  routeAI,
  env: process.env,
});

const outputDir = resolve('.runtime/passive-income');
await mkdir(outputDir, { recursive: true });
const stamp = now.toISOString().replace(/[:.]/g, '-');
const outputPath = resolve(outputDir, `cycle-${stamp}.json`);
await writeFile(outputPath, `${JSON.stringify({ ...result, rss }, null, 2)}\n`, 'utf8');

console.log(JSON.stringify({
  ok: result.ok,
  cycleId: result.cycleId,
  agents,
  metrics: result.metrics,
  reviewQueueItems: result.reviewQueue?.length || 0,
  outputPath,
}, null, 2));

if (!result.ok) process.exitCode = 1;
