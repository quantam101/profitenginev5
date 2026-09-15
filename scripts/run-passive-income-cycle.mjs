import { mkdir, writeFile } from 'node:fs/promises';
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
