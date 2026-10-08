import { mkdir, readdir, writeFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';
import { routePassiveIncomeAI } from '../lib/revenue-os/passive-income-ai.mjs';
import {
  collectRssSources,
  runPassiveIncomeCycle,
} from '../lib/revenue-os/passive-income-engine.mjs';
import { materializeCycleArtifacts } from '../lib/revenue-os/artifact-factory.mjs';
import { buildProcessAgentStatus } from '../lib/revenue-os/process-agents.mjs';

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
  publish: false,
  agents,
  sources: rss.sources,
  newsletterNiche: process.env.PASSIVE_INCOME_NEWSLETTER_NICHE || 'AI operations and infrastructure for small technology businesses',
}, {
  routeAI: routePassiveIncomeAI,
  env: process.env,
});

const outputDir = resolve('.runtime/passive-income');
await mkdir(outputDir, { recursive: true });
const stamp = now.toISOString().replace(/[:.]/g, '-');
const cycleDir = resolve(outputDir, result.cycleId || `cycle-${stamp}`);
await mkdir(cycleDir, { recursive: true });
const artifacts = await materializeCycleArtifacts(result, cycleDir);

// Optional live listing: when external writes are enabled and a Gumroad
// token exists, list each newly materialized technical product and write
// its listing_url back into checkout.json (newsletter then features it).
let listedProducts = 0;
const externalWrites = String(process.env.PASSIVE_INCOME_EXTERNAL_WRITES || 'false') === 'true';
if (externalWrites && process.env.GUMROAD_ACCESS_TOKEN) {
  const productRoot = resolve(cycleDir, 'technical-products');
  try {
    for (const slug of await readdir(productRoot)) {
      try {
        execFileSync('python3', ['scripts/list_product_on_gumroad.py', resolve(productRoot, slug)],
          { stdio: 'inherit' });
        listedProducts += 1;
      } catch (err) {
        console.warn(`gumroad listing failed for ${slug}:`, String(err).slice(0, 200));
      }
    }
  } catch {
    // no technical-products dir this cycle — nothing to list
  }
} else if (externalWrites) {
  console.warn('PASSIVE_INCOME_EXTERNAL_WRITES=true but GUMROAD_ACCESS_TOKEN unset — skipping listings');
}
const processAgents = buildProcessAgentStatus(result, artifacts);
const outputPath = resolve(cycleDir, `cycle-${stamp}.json`);
await writeFile(outputPath, `${JSON.stringify({ ...result, rss, artifacts, processAgents }, null, 2)}\n`, 'utf8');

const artifactFailures = artifacts.artifacts.filter((artifact) => !artifact.ok);
const cycleComplete = result.ok && artifactFailures.length === 0;
console.log(JSON.stringify({
  ok: cycleComplete,
  cycleId: result.cycleId,
  laneAgents: agents,
  processAgents: processAgents.length,
  processAgentAttention: processAgents.filter((agent) => agent.state === 'attention').map((agent) => agent.id),
  metrics: result.metrics,
  reviewQueueItems: result.reviewQueue?.length || 0,
  listedProducts,
  artifacts: artifacts.artifacts.map((artifact) => ({
    agentId: artifact.agentId,
    ok: artifact.ok,
    kind: artifact.kind || null,
    zipPath: artifact.zipPath || null,
    sha256: artifact.sha256 || null,
    reason: artifact.reason || null,
  })),
  outputPath,
}, null, 2));

if (!cycleComplete) process.exitCode = 1;
