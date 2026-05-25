import { readFileSync } from 'node:fs';
import { NextResponse } from 'next/server';

function agentIds() {
  const registry = readFileSync('agents/registry.yaml', 'utf8');
  return [...registry.matchAll(/^\s*- id: ([a-z0-9-]+)/gm)].map((match) => match[1]);
}

export function GET() {
  const agents = agentIds().map((id) => ({
    id,
    status: 'ready',
    mode: 'safe-local',
    parallelEligible: true,
  }));

  return NextResponse.json({
    ok: agents.length > 0,
    service: 'parallel-agent-runner',
    mode: 'safe-local',
    agentCount: agents.length,
    agents,
    generatedAt: new Date().toISOString(),
  });
}
