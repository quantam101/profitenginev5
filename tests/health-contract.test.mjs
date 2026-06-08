import assert from 'node:assert/strict';
import { mkdir, rm, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { buildHealthPayload } from '../lib/health.mjs';

async function writeBaseFixture(root) {
  await mkdir(join(root, 'agents'), { recursive: true });
  await mkdir(join(root, 'connectors'), { recursive: true });
  await mkdir(join(root, 'observability'), { recursive: true });
  await mkdir(join(root, 'app/api/health'), { recursive: true });
  await mkdir(join(root, '.github/workflows'), { recursive: true });

  await writeFile(
    join(root, 'eaos.config.yaml'),
    `system:
  mode: strict_zero_spend
runtime:
  max_cost_usd: 0
  paid_adapters_enabled: false
  external_execution_enabled: false
production_gate_targets:
  ci_passes: true
  lint_passes: true
  typecheck_passes: true
  tests_pass: true
`
  );

  await writeFile(
    join(root, 'package.json'),
    JSON.stringify({
      name: 'profitenginev5',
      version: '0.1.0',
      scripts: {
        'ci:all': 'npm run lint && npm run typecheck && npm run validate:yaml && npm run test:unit && npm run build'
      }
    })
  );
  await writeFile(join(root, 'package-lock.json'), JSON.stringify({ name: 'profitenginev5' }));
  await writeFile(
    join(root, '.github/workflows/ci.yml'),
    `run: |
  pip install -r requirements.txt
  npm ci
  npm run typecheck
  npm run validate:yaml
  npm run test:unit
  npm run test:ai-gateway
  npm run test:skill-gateway
  npm run build
`
  );
  await writeFile(join(root, 'agents/registry.yaml'), 'agents:\n  - id: local-research\n    allowed_connectors: [playwright_local, local_files]\n');
  await writeFile(join(root, 'connectors/registry.yaml'), 'connectors:\n  playwright_local:\n    enabled: true\n');
  await writeFile(join(root, 'observability/slo.yaml'), 'slos:\n  deterministic_route_p95_ms:\n    target: 250\n');
  await writeFile(join(root, 'Dockerfile.web'), 'FROM node:20-alpine\n');
  await writeFile(join(root, 'docker-compose.yml'), 'image: n8nio/n8n:2.19.5\n');
  await writeFile(join(root, '.env.example'), 'POSTGRES_PASSWORD=\nN8N_BASIC_AUTH_PASSWORD=\n');
  await writeFile(join(root, 'app/api/health/route.ts'), 'export const dynamic = "force-dynamic";\n');
  await writeFile(join(root, 'vercel.json'), '{}\n');
}

const passingFixture = join(process.cwd(), `.health-pass-fixture-${Date.now()}`);
const failingFixture = join(process.cwd(), `.health-fail-fixture-${Date.now()}`);

try {
  await writeBaseFixture(passingFixture);
  const payload = buildHealthPayload({ root: passingFixture });
  const cachedPayload = buildHealthPayload({ root: passingFixture });

  assert.equal(payload.ok, true, JSON.stringify(payload, null, 2));
  assert.equal(cachedPayload.cached, false);
  assert.equal(payload.healthScore, 100, JSON.stringify(payload, null, 2));
  assert.equal(payload.staleSourcePresent, false);
  assert.deepEqual(payload.deploymentBlockers, []);
  assert.equal(payload.checks.source, 'pass');
  assert.equal(payload.checks.ci, 'pass');
  assert.equal(payload.checks.docker, 'pass');
  assert.equal(payload.checks.registry, 'pass');
  assert.equal(payload.checks.security, 'pass');
  assert.equal(payload.checks.runtime, 'pass');

  await writeBaseFixture(failingFixture);
  await mkdir(join(failingFixture, 'modules'), { recursive: true });
  await writeFile(
    join(failingFixture, 'eaos.config.yaml'),
    `system:
  mode: strict_zero_spend
runtime:
  max_cost_usd: 0
  paid_adapters_enabled: true
  external_execution_enabled: false
production_gate_targets:
  ci_passes: false
`
  );
  await writeFile(join(failingFixture, '.github/workflows/ci.yml'), 'run: npm run test:unit\n');
  await writeFile(join(failingFixture, 'Dockerfile.web'), 'FROM node:22-alpine\n');
  await writeFile(join(failingFixture, 'docker-compose.yml'), 'image: n8nio/n8n:latest\n');
  await writeFile(join(failingFixture, '.env.example'), `POSTGRES_PASSWORD=${['change', '-me-server-side'].join('')}\n${['API', '_KEY='].join('')}\n`);

  const failingPayload = buildHealthPayload({ root: failingFixture });
  assert.equal(failingPayload.ok, false);
  assert.equal(failingPayload.staleSourcePresent, true);
  assert.equal(failingPayload.paidAdaptersEnabled, true);
  assert.ok(failingPayload.healthScore < 100);
  assert.ok(failingPayload.deploymentBlockers.length > 0);

  console.log('health contract test passed');
} finally {
  await rm(passingFixture, { recursive: true, force: true });
  await rm(failingFixture, { recursive: true, force: true });
}
