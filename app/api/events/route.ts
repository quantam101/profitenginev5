export const runtime = 'edge';
export const dynamic = 'force-dynamic';

const INTERVAL_MS = 5000;
const MAX_DURATION_MS = 30000;

export async function GET() {
  const encoder = new TextEncoder();
  let timer: ReturnType<typeof setInterval> | null = null;

  const stream = new ReadableStream({
    start(controller) {
      const startedAt = Date.now();
      let closed = false;

      // Send an initial event immediately
      controller.enqueue(
        encoder.encode(`event: refresh\ndata: ${JSON.stringify({ ts: new Date().toISOString() })}\n\n`),
      );

      timer = setInterval(() => {
        if (closed) return;
        if (Date.now() - startedAt > MAX_DURATION_MS) {
          closed = true;
          if (timer) clearInterval(timer);
          controller.close();
          return;
        }
        const payload = JSON.stringify({ ts: new Date().toISOString() });
        controller.enqueue(encoder.encode(`event: refresh\ndata: ${payload}\n\n`));
      }, INTERVAL_MS);
    },
    cancel() {
      if (timer) clearInterval(timer);
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache, no-transform',
      Connection: 'keep-alive',
    },
  });
}
