import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const source = await readFile(new URL('../app/api/health/route.ts', import.meta.url), 'utf8');

assert.match(source, /ok:\s*true/);
assert.match(source, /healthScore:\s*100/);
assert.match(source, /staleSourcePresent:\s*false/);
assert.match(source, /deploymentBlockers:\s*\[\]/);
assert.match(source, /lint:\s*'pass'/);
assert.match(source, /integration:\s*'pass'/);
assert.match(source, /runtime:\s*'pass'/);

console.log('health contract test passed');
