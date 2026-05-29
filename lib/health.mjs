import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';

// Only match actual key VALUE prefixes — not env-var names (ANTHROPIC_API_KEY,
// OPENAI_API_KEY) or assignment patterns (API_KEY=) that appear legitimately in
// every gateway file.  Ruff (select=S) and ESLint handle code-quality /
// hardcoded-credential checks; this scanner exists only to catch accidentally
// committed key values.
const secretMarkers = [
  'sk-ant-',                // Anthropic live key
  'sk-proj-',               // OpenAI live key
  'BEGIN PRIVATE KEY',      // PEM private key block
  'BEGIN RSA PRIVATE KEY',  // RSA PEM block
  'AWS_SECRET_ACCESS_KEY=', // AWS secret with a value assigned
];
const ignoredDirs = new Set(['.git', '.next', 'node_modules', '__pycache__', '.pytest_cache', '.v8-cache', '.claude']);
// Only self-referential files that list the marker strings themselves.
// Keep this list short — if a file keeps appearing here, the marker is too broad.
const ignoredFiles = new Set(['package-lock.json', 'security_scanner.py', 'verifier.py', 'health.mjs', 'security_check.py']);
const ignoredPaths = new Set([
  '.env.example',
  'scripts/secrets.env.example',
  'CONTINUATION.md',
  'DEPLOYMENT.md',
  'DEPLOY.md',
  'docs/LAUNCH_CHECKLIST.md',
  'docs/AFFILIATE_SETUP.md',
]);
let cachedPayload = null;
let cachedAt = 0;
const defaultCacheTtlMs = 30_000;

function readText(root, path) {
  try {
    return readFileSync(join(root, path), 'utf8').replace(/\r\n/g, '\n');
  } catch {
    return '';
  }
}

function exists(root, path) {
  try {
    statSync(join(root, path));
    return true;
  } catch {
    return false;
  }
}

function yamlBoolean(source, section, key) {
  const pattern = new RegExp(`\\n${section}:\\n(?:  [^\\n]+\\n)*?  ${key}:\\s*(true|false)\\b`, 'm');
  const match = `\n${source}`.match(pattern);
  return match ? match[1] === 'true' : null;
}

function yamlNumber(source, section, key) {
  const pattern = new RegExp(`\\n${section}:\\n(?:  [^\\n]+\\n)*?  ${key}:\\s*(-?\\d+(?:\\.\\d+)?)\\b`, 'm');
  const match = `\n${source}`.match(pattern);
  return match ? Number(match[1]) : null;
}

function yamlString(source, section, key) {
  const pattern = new RegExp(`\\n${section}:\\n(?:  [^\\n]+\\n)*?  ${key}:\\s*([^\\n#]+)`, 'm');
  const match = `\n${source}`.match(pattern);
  return match ? match[1].trim() : null;
}

function yamlSectionBooleans(source, section) {
  const lines = source.split('\n');
  const start = lines.findIndex((line) => line.trim() === `${section}:`);
  if (start === -1) return {};
  const values = {};
  for (const line of lines.slice(start + 1)) {
    if (line.trim() && !line.startsWith(' ')) break;
    const match = line.match(/^\s{2}([A-Za-z0-9_]+):\s*(true|false)\s*$/);
    if (match) values[match[1]] = match[2] === 'true';
  }
  return values;
}

function walkFiles(root, dir = '.') {
  const base = join(root, dir);
  let entries = [];
  try {
    entries = readdirSync(base, { withFileTypes: true });
  } catch {
    return [];
  }

  return entries.flatMap((entry) => {
    if (ignoredDirs.has(entry.name)) return [];
    const path = dir === '.' ? entry.name : `${dir}/${entry.name}`;
    if (entry.isDirectory()) return walkFiles(root, path);
    return entry.isFile() ? [path] : [];
  });
}

function scanSecrets(root) {
  const findings = [];
  for (const path of walkFiles(root)) {
    if (ignoredFiles.has(path.split('/').pop()) || ignoredPaths.has(path)) continue;
    const text = readText(root, path).toLowerCase();
    const markers = secretMarkers.filter((marker) => text.includes(marker.toLowerCase()));
    if (markers.length) findings.push(`${path}: ${markers.join(',')}`);
  }
  return findings;
}

function status(ok) {
  return ok ? 'pass' : 'fail';
}

export function buildHealthPayload(options = {}) {
  const root = options.root ?? process.cwd();
  const cacheTtlMs = options.cacheTtlMs ?? defaultCacheTtlMs;
  if (!options.root && cachedPayload && Date.now() - cachedAt < cacheTtlMs) {
    return { ...cachedPayload, timestamp: new Date().toISOString(), cached: true };
  }
  const blockers = [];
  const config = readText(root, 'eaos.config.yaml');
  const packageJson = JSON.parse(readText(root, 'package.json') || '{}');
  const packageLock = JSON.parse(readText(root, 'package-lock.json') || '{}');
  const workflow = readText(root, '.github/workflows/ci.yml');
  const agentsRegistry = readText(root, 'agents/registry.yaml');
  const connectorsRegistry = readText(root, 'connectors/registry.yaml');
  const sloConfig = readText(root, 'observability/slo.yaml');
  const dockerfile = readText(root, 'Dockerfile.web');
  const compose = readText(root, 'docker-compose.yml');
  const envExample = readText(root, '.env.example');

  const paidAdaptersEnabled = yamlBoolean(config, 'runtime', 'paid_adapters_enabled') !== false;
  const externalExecutionEnabled = yamlBoolean(config, 'runtime', 'external_execution_enabled') !== false;
  const staleSourcePresent = exists(root, 'modules');
  const secretFindings = scanSecrets(root);
  const productionGateTargets = yamlSectionBooleans(config, 'production_gate_targets');
  const failedGates = Object.entries(productionGateTargets)
    .filter(([, value]) => value !== true)
    .map(([key]) => key);

  const checks = {
    source: status(!staleSourcePresent),
    config: status(
      yamlString(config, 'system', 'mode') === 'strict_zero_spend' &&
        yamlNumber(config, 'runtime', 'max_cost_usd') === 0 &&
        !paidAdaptersEnabled &&
        !externalExecutionEnabled
    ),
    dependencies: status(packageJson.name === 'profitenginev5' && packageLock.name === packageJson.name),
    ci: status(
      workflow.includes('pip install -r requirements.txt') &&
        workflow.includes('npm run ci:all') &&
        packageJson.scripts?.['ci:all']?.includes('npm run validate:yaml') &&
        packageJson.scripts?.['ci:all']?.includes('npm run test:unit')
    ),
    registry: status(
      agentsRegistry.includes('id: local-research') &&
        agentsRegistry.includes('playwright_local') &&
        agentsRegistry.includes('local_files') &&
        connectorsRegistry.includes('playwright_local:') &&
        sloConfig.includes('deterministic_route_p95_ms')
    ),
    docker: status(dockerfile.includes('node:20-alpine') && !dockerfile.includes('node:22') && !compose.includes('n8nio/n8n:latest')),
    environment: status(!envExample.includes('change-me-server-side') && !envExample.includes('API_KEY=')),
    productionGateTargets: status(Object.keys(productionGateTargets).length > 0 && failedGates.length === 0),
    security: status(secretFindings.length === 0),
    routing: status(exists(root, 'app/api/health/route.ts') && exists(root, 'vercel.json')),
    runtime: status(!paidAdaptersEnabled && !externalExecutionEnabled)
  };

  if (staleSourcePresent) blockers.push('stale modules/ source directory is present');
  if (paidAdaptersEnabled) blockers.push('paid adapters are enabled');
  if (externalExecutionEnabled) blockers.push('external execution is enabled');
  if (failedGates.length) blockers.push(`production gate targets failing: ${failedGates.join(', ')}`);
  if (secretFindings.length) blockers.push(`secret scan findings: ${secretFindings.map((item) => relative(root, join(root, item))).join('; ')}`);
  for (const [name, value] of Object.entries(checks)) {
    if (value !== 'pass') blockers.push(`${name} check failed`);
  }

  const passed = Object.values(checks).filter((value) => value === 'pass').length;
  const healthScore = Math.round((passed / Object.keys(checks).length) * 100);

  const payload = {
    ok: blockers.length === 0,
    service: 'profitengine-command-center',
    version: packageJson.version ?? 'unknown',
    mode: yamlString(config, 'system', 'mode') ?? 'unknown',
    healthScore,
    paidAdaptersEnabled,
    externalExecutionEnabled,
    staleSourcePresent,
    deploymentBlockers: blockers,
    checks,
    timestamp: new Date().toISOString(),
    cached: false
  };
  if (!options.root) {
    cachedPayload = payload;
    cachedAt = Date.now();
  }
  return payload;
}
