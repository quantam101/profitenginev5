import { NextRequest, NextResponse } from 'next/server';

const SYSTEM = 'You are the ProfitEngine v5.0 AI Operations Advisor. You have full telemetry access to 10 agents, 6 revenue streams, the VHLL/XAF pipeline, LC&C 4-loop system, and live revenue data. Be concise, data-driven, and action-oriented.';

/** Groq — free tier, 100k tokens/day, ~500 tok/s (llama-3.3-70b-versatile) */
async function tryGroq(messages: object[]): Promise<string | null> {
  const key = process.env.GROQ_API_KEY;
  if (!key) return null;
  try {
    const res = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${key}` },
      body: JSON.stringify({ model: 'llama-3.3-70b-versatile', messages, max_tokens: 512, temperature: 0.7 }),
      signal: AbortSignal.timeout(30000),
    });
    if (!res.ok) return null;
    const d = await res.json();
    return d.choices?.[0]?.message?.content?.trim() ?? null;
  } catch {
    return null;
  }
}

/** Gemini Flash — free tier, 1 500 req/day, 1 M context */
async function tryGemini(userMessage: string): Promise<string | null> {
  const key = process.env.GEMINI_API_KEY;
  if (!key) return null;
  try {
    const res = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${key}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [
            { role: 'user', parts: [{ text: `[System]: ${SYSTEM}` }] },
            { role: 'model', parts: [{ text: 'Understood. I am ready to assist.' }] },
            { role: 'user', parts: [{ text: userMessage }] },
          ],
          generationConfig: { maxOutputTokens: 512, temperature: 0.7 },
        }),
        signal: AbortSignal.timeout(30000),
      },
    );
    if (!res.ok) return null;
    const d = await res.json();
    const parts = d.candidates?.[0]?.content?.parts ?? [];
    const text = parts.map((p: { text?: string }) => p.text ?? '').join('').trim();
    return text || null;
  } catch {
    return null;
  }
}

export async function POST(req: NextRequest) {
  const { message } = await req.json();
  if (!message?.trim()) {
    return NextResponse.json({ reply: 'Please enter a message.' });
  }

  const messages = [
    { role: 'system', content: SYSTEM },
    { role: 'user', content: message },
  ];

  // Groq first (fastest, free)
  const groqReply = await tryGroq(messages);
  if (groqReply) return NextResponse.json({ reply: groqReply });

  // Gemini fallback (also free)
  const geminiReply = await tryGemini(message);
  if (geminiReply) return NextResponse.json({ reply: geminiReply });

  return NextResponse.json({
    reply: 'All AI providers are currently unavailable. Check GROQ_API_KEY and GEMINI_API_KEY on the server.',
  });
}
