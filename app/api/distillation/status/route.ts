import { readFileSync } from 'node:fs';
import { NextResponse } from 'next/server';

function countMatches(source: string, pattern: RegExp) {
  return [...source.matchAll(pattern)].length;
}

export function GET() {
  const config = readFileSync('config/distillation.yaml', 'utf8');
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
