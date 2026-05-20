import assert from 'node:assert/strict';
import { mkdir, rm, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { buildHealthPayload } from '../lib/health.mjs';

const payload = buildHealthPayload();

assert.equal(payload.ok, true);
assert.equal(payload.healthScore, 100);
assert.equal(payload.staleSourcePresent, false);
assert.deepEqual(payload.deploymentBlockers, []);
assert.equal(payload.checks.source, 'pass');
assert.equal(payload.checks.ci, 'pass');
assert.equal(payload.checks.docker, 'pass');
assert.equal(payload.checks.registry, 'pass');
assert.equal(payload.checks.security, 'pass');
assert.equal(payload.checks.runtime, 'pass');

const fixture = join(process.cwd(), `.health-test-fixture-${Date.now()}`);
await mkdir(join(fixture, 'modules'), { recursive: true });
await mkdir(join(fixture, 'app/api/health'), { recursive: true });
await mkdir(join(fixture, '.github/workflows'), { recursive: true });
await writeFile(join(fixture, 'package.json'), '{"name":"profitenginev5","version":"0.1.0"}');
await writeFile(join(fixture, 'package-lock.json'), '{"name":"profitenginev5"}');
await writeFile(join(fixture, 'eaos.config.yaml'), `system:
  mode: strict_zero_spend
runtime:
  max_cost_usd: 0
  paid_adapters_enabled: true
  external_execution_enabled: false
production_gate:
  ci_passes: true
`);
await writeFile(join(fixture, '.github/workflows/ci.yml'), 'run: npm run test:unit\n');
await mkdir(join(fixture, 'agents'), { recursive: true });
await mkdir(join(fixture, 'connectors'), { recursive: true });
await mkdir(join(fixture, 'observability'), { recursive: true });
await writeFile(join(fixture, 'agents/registry.yaml'), 'agents: []\n');
await writeFile(join(fixture, 'connectors/registry.yaml'), 'connectors: {}\n');
await writeFile(join(fixture, 'observability/slo.yaml'), 'slos: {}\n');
await writeFile(join(fixture, 'Dockerfile.web'), 'FROM node:22-alpine\n');
await writeFile(join(fixture, 'docker-compose.yml'), 'image: n8nio/n8n:latest\n');
await writeFile(join(fixture, '.env.example'), 'POSTGRES_PASSWORD=change-me-server-side\n');
await writeFile(join(fixture, 'app/api/health/route.ts'), '');
await writeFile(join(fixture, 'vercel.json'), '{}');

const failingPayload = buildHealthPayload({ root: fixture });
assert.equal(failingPayload.ok, false);
assert.equal(failingPayload.staleSourcePresent, true);
assert.equal(failingPayload.paidAdaptersEnabled, true);
assert.ok(failingPayload.healthScore < 100);
assert.ok(failingPayload.deploymentBlockers.length > 0);
await rm(fixture, { recursive: true, force: true });

console.log('health contract test passed');
