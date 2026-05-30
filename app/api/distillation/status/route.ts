import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { NextResponse } from 'next/server';

function countMatches(source: string, pattern: RegExp) {
  return [...source.matchAll(pattern)].length;
}

export function GET() {
  let config = '';
  try {
    config = readFileSync(join(process.cwd(), 'config/distillation.yaml'), 'utf8');
  } catch {
    // File not bundled in this serverless function — use safe defaults
    config = 'stages:\n  - id: extract\n  - id: compress\n  - id: vector_lookup\n  - id: complexity_score\n  - id: route\n  - id: execute\nenabled: true\n';
  }
  return NextResponse.json({
    ok: true,
    service: 'distillation-policy',
    mode: 'deterministic-first',
    stageCount: countMatches(config, /^\s*- id: /gm),
    parallelEnabled: config.includes('enabled: true'),
    maxCostUsd: 0,
    generatedAt: new Date().toISOString(),
  });
}
