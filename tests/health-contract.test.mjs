import assert from 'node:assert/strict';
import { GET } from '../app/api/health/route.ts';

const response = await GET();
assert.equal(response.status, 200);

const health = await response.json();
assert.equal(health.ok, true);
assert.equal(health.healthScore, 100);
assert.equal(health.staleSourcePresent, false);
assert.deepEqual(health.deploymentBlockers, []);
assert.equal(health.checks.lint, 'pass');
assert.equal(health.checks.integration, 'pass');

console.log('health contract test passed');
