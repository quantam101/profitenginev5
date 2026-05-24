import { NextRequest, NextResponse } from 'next/server';

const RUNTIME = process.env.RUNTIME_API_URL ?? 'http://runtime:8080';

interface BlogPayload {
  title: string;
  slug: string;
  content: string;
  excerpt: string;
  date: string;
  category: string;
  url: string;
  source: string;
}

export async function POST(req: NextRequest) {
  try {
    const body = (await req.json()) as Partial<BlogPayload>;

    if (!body.title || !body.slug) {
      return NextResponse.json(
        { ok: false, error: 'title and slug are required' },
        { status: 400 },
      );
    }

    const record = {
      type: 'blog_crosspost',
      receivedAt: new Date().toISOString(),
      title: body.title,
      slug: body.slug,
      excerpt: (body.excerpt ?? '').slice(0, 300),
      category: body.category ?? '',
      date: body.date ?? new Date().toISOString(),
      url: body.url ?? '',
      source: body.source ?? 'alreadyherellc.com',
    };

    try {
      await fetch(`${RUNTIME}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          objective: `Cross-post blog: ${body.title}`,
          dynamic_context: `ARTICLE_JSON:${JSON.stringify({
            title: body.title,
            slug: body.slug,
            body: body.content ?? body.excerpt ?? '',
            meta_description: body.excerpt ?? '',
            tags: [body.category ?? 'field-service'],
          })}`,
          agent_id: 'blog-publisher',
          namespace: 'webhook',
          actor: 'webhook-blog',
        }),
        signal: AbortSignal.timeout(15000),
      });
    } catch {
      // Runtime may be offline; record is still logged below
    }

    return NextResponse.json({ ok: true, record }, { status: 201 });
  } catch {
    return NextResponse.json(
      { ok: false, error: 'invalid_payload' },
      { status: 400 },
    );
  }
}
