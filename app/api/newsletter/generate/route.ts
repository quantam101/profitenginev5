import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { z } from 'zod';
import { routeAI } from '@/lib/ai-gateway.mjs';
import { editorialPrompt } from '@/lib/newsletter-business/editorial.mjs';

export const runtime = 'nodejs';

const schema = z.object({
  mode: z.enum(['ideas', 'draft', 'subject_lines']).default('ideas'),
  brief: z.string().max(12000).default(''),
  audience: z.string().max(500).optional(),
});

export async function POST(request: Request) {
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ ok: false, error: 'Unauthorized' }, { status: 401 });
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ ok: false, error: 'Invalid JSON' }, { status: 400 });
  }

  const parsed = schema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ ok: false, error: parsed.error.issues.map((i) => i.message).join(', ') }, { status: 400 });
  }

  const prompt = editorialPrompt(parsed.data);
  const result = await routeAI({
    task: parsed.data.mode === 'draft' ? 'internal_planning' : 'offer_optimization',
    prompt,
    system: 'You are the ProfitEngine AI newsletter editor. Produce factual, auditable drafts for human review. Never send, publish, fabricate results, or claim unverified revenue.',
    maxTokens: parsed.data.mode === 'draft' ? 1800 : 1200,
    temperature: 0.35,
    metadata: {
      source: 'newsletter_editorial_api',
      mode: parsed.data.mode,
      requestedBy: session.user.email || session.user.name || 'operator',
    },
  });

  return NextResponse.json({
    ok: result.ok,
    mode: parsed.data.mode,
    text: result.text,
    provider: result.provider,
    fallbackUsed: result.fallbackUsed,
    requestId: result.requestId,
    latencyMs: result.latencyMs,
    costUsd: result.costUsd,
    blocked: result.blocked || false,
  }, { status: result.ok ? 200 : result.blocked ? 403 : 500 });
}
