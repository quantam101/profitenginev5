import { NextRequest, NextResponse } from 'next/server';
const SYSTEM = 'You are the ProfitEngine v5.0 AI Operations Advisor. You have full telemetry access to 10 agents, 6 revenue streams, the VHLL/XAF pipeline, LC&C 4-loop system, and live revenue data. Be concise, data-driven, and action-oriented.';
export async function POST(req: NextRequest) {
  const { message } = await req.json();
  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'x-api-key': process.env.ANTHROPIC_API_KEY ?? '', 'anthropic-version': '2023-06-01' },
    body: JSON.stringify({ model: 'claude-sonnet-4-20250514', max_tokens: 512, system: SYSTEM, messages: [{ role: 'user', content: message }] }),
  });
  if (!res.ok) return NextResponse.json({ reply: 'API error. Check ANTHROPIC_API_KEY.' });
  const data = await res.json();
  return NextResponse.json({ reply: data.content?.[0]?.text ?? 'No response.' });
}
