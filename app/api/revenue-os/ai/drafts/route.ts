import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { z } from 'zod';
import { createDraftAction, generateDraft } from '@/lib/revenue-os/services/ai-advisor.mjs';

const draftSchema = z.object({
  type: z.enum([
    'intro_email',
    'follow_up_email',
    'capability_statement',
    'call_script',
    'proposal_summary',
    'sow_draft',
  ] as const),
  opportunityId: z.string().min(1),
  save: z.boolean().optional().default(false),
  overrides: z.record(z.string(), z.unknown()).optional(),
});

export async function POST(request: Request) {
  if (process.env.REVENUE_OS_ENABLED !== 'true' || process.env.REVENUE_OS_AI_ENABLED !== 'true') {
    return NextResponse.json({ ok: false, error: 'Revenue OS AI is not enabled' }, { status: 404 });
  }
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ ok: false, error: 'Unauthorized' }, { status: 401 });
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ ok: false, error: 'Invalid JSON' }, { status: 400 });
  }

  const parse = draftSchema.safeParse(body);
  if (!parse.success) {
    return NextResponse.json({ ok: false, error: parse.error.issues.map((i) => i.message).join(', ') }, { status: 400 });
  }

  const actor = session.user.email || session.user.name || 'unknown';

  try {
    if (parse.data.save) {
      const result = await createDraftAction({
        type: parse.data.type,
        opportunityId: parse.data.opportunityId,
        actor,
        overrides: parse.data.overrides,
      });
      if (!result.ok) {
        return NextResponse.json({ ok: false, error: result.error }, { status: 400 });
      }
      return NextResponse.json({
        ok: true,
        content: result.action?.content,
        action: { ...result.action, _id: String(result.action?._id) },
      }, { status: 201 });
    }

    const result = await generateDraft({
      type: parse.data.type,
      opportunityId: parse.data.opportunityId,
      overrides: parse.data.overrides,
    });
    if (!result.ok) {
      return NextResponse.json({ ok: false, error: result.error }, { status: 400 });
    }
    return NextResponse.json({ ok: true, content: result.content, context: result.context });
  } catch (err) {
    console.error('[revenue-os] ai drafts error:', err);
    return NextResponse.json({ ok: false, error: 'Internal server error' }, { status: 500 });
  }
}
