/**
 * /api/tokenforge — LLM proxy using ProfitEngine's own zero-cost inference chain.
 * TokenForge standalone backend has been paused; all routing now runs internally.
 * Supports: groq, gemini, openrouter (free tier only)
 */
import { NextRequest, NextResponse } from "next/server";

const GROQ_KEY = process.env.GROQ_API_KEY ?? "";
const GEMINI_KEY = process.env.GEMINI_API_KEY ?? "";

const PROVIDER_MODELS: Record<string, { url: string; defaultModel: string }> = {
  groq: {
    url: "https://api.groq.com/openai/v1/chat/completions",
    defaultModel: "llama-3.3-70b-versatile",
  },
  gemini: {
    url: "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
    defaultModel: "gemini-2.5-flash",
  },
};

export async function POST(req: NextRequest) {
  const body = await req.json();
  const { prompt, provider = "groq", model, max_tokens = 512, system } = body;

  if (!prompt) {
    return NextResponse.json({ error: "prompt is required" }, { status: 400 });
  }

  try {
    if (provider === "groq" || provider === "openai") {
      if (!GROQ_KEY) return NextResponse.json({ error: "GROQ_API_KEY not configured" }, { status: 503 });
      const messages = [];
      if (system) messages.push({ role: "system", content: system });
      messages.push({ role: "user", content: prompt });
      const res = await fetch(PROVIDER_MODELS.groq.url, {
        method: "POST",
        headers: { Authorization: `Bearer ${GROQ_KEY}`, "Content-Type": "application/json" },
        body: JSON.stringify({
          model: model ?? PROVIDER_MODELS.groq.defaultModel,
          messages,
          max_tokens,
          temperature: 0.7,
        }),
      });
      const data = await res.json() as Record<string, unknown>;
      const text = (data?.choices as Array<{message:{content:string}}>)?.[0]?.message?.content ?? "";
      return NextResponse.json({ ok: true, provider: "groq", model: model ?? PROVIDER_MODELS.groq.defaultModel, text, usage: data?.usage });
    }

    if (provider === "gemini" || provider === "google") {
      if (!GEMINI_KEY) return NextResponse.json({ error: "GEMINI_API_KEY not configured" }, { status: 503 });
      const url = `${PROVIDER_MODELS.gemini.url}?key=${GEMINI_KEY}`;
      const contents = [];
      if (system) contents.push({ role: "user", parts: [{ text: `[System]: ${system}` }] });
      contents.push({ role: "user", parts: [{ text: prompt }] });
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ contents, generationConfig: { maxOutputTokens: max_tokens } }),
      });
      const data = await res.json() as Record<string, unknown>;
      const text = (data?.candidates as Array<{content:{parts:Array<{text:string}>}}>)?.[0]?.content?.parts?.[0]?.text ?? "";
      return NextResponse.json({ ok: true, provider: "gemini", model: "gemini-2.5-flash", text });
    }

    return NextResponse.json({ error: `unsupported provider: ${provider}. Use groq or gemini.` }, { status: 400 });
  } catch (err) {
    return NextResponse.json({ ok: false, error: String(err) }, { status: 502 });
  }
}

export async function GET() {
  return NextResponse.json({
    ok: true,
    service: "tokenforge-integrated",
    version: "2.0.0",
    note: "TokenForge standalone backend paused. LLM routing runs inside ProfitEngine.",
    providers: {
      groq: { configured: !!GROQ_KEY, models: ["llama-3.3-70b-versatile", "qwen-qwq-32b", "llama-3.1-8b-instant"] },
      gemini: { configured: !!GEMINI_KEY, models: ["gemini-2.5-flash"] },
    },
    cost: "zero",
  });
}
