/**
 * /api/tokenforge — zero-cost LLM proxy for the profit fleet.
 *
 * Cost law: every provider here is free. No keyless caller, no paid model.
 *   - POST requires the shared key in the X-TF-Key header (401/503 otherwise).
 *     Without it anyone on the internet could burn the upstream free-tier
 *     quotas this fleet depends on.
 *   - provider "auto" (default) cascades groq -> gemini -> pollinations,
 *     using whichever keys are configured. Pollinations needs no key, so a
 *     zero-configuration deployment still answers.
 *   - Caller-supplied provider/model values can only select within the free
 *     allowlist; anything else (e.g. anthropic) is rejected with 400.
 */
import { NextRequest, NextResponse } from "next/server";

const GROQ_KEY = process.env.GROQ_API_KEY ?? "";
const GEMINI_KEY = process.env.GEMINI_API_KEY ?? "";
const TF_KEY = process.env.TOKENFORGE_API_KEY ?? "";

const MAX_TOKENS_CAP = 1024;
const MAX_TOKENS_DEFAULT = 256;
// 16k is the Pollinations Classic input ceiling, the strictest provider in the chain.
const PROMPT_CHAR_CAP = 16000;

const GROQ_MODELS = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "qwen/qwen3-32b"];
const GEMINI_MODELS = ["gemini-2.5-flash"];
// Verified against https://text.pollinations.ai/models: only "openai" exists on the
// free Classic API (mistral/llama return 404). Free tier rate limit: 1 reply/45s/IP.
const POLLINATIONS_MODELS = ["openai"];

const FREE_PROVIDERS = ["auto", "groq", "gemini", "pollinations"];

function clampTokens(value: unknown): number {
  const n = typeof value === "number" && Number.isFinite(value) ? Math.floor(value) : MAX_TOKENS_DEFAULT;
  return Math.min(Math.max(n, 1), MAX_TOKENS_CAP);
}

function unauthorized() {
  return NextResponse.json({ error: "missing or invalid X-TF-Key" }, { status: 401 });
}

function pickModel(provider: string, model: unknown): string | null {
  const allow =
    provider === "groq" ? GROQ_MODELS :
    provider === "gemini" ? GEMINI_MODELS :
    provider === "pollinations" ? POLLINATIONS_MODELS : [];
  if (model == null) return allow[0] ?? null;
  return typeof model === "string" && allow.includes(model) ? model : null;
}

async function callGroq(prompt: string, system: string | undefined, model: string, maxTokens: number) {
  if (!GROQ_KEY) return { error: "groq key not configured", status: 0 };
  const messages = [];
  if (system) messages.push({ role: "system", content: system });
  messages.push({ role: "user", content: prompt });
  const res = await fetch("https://api.groq.com/openai/v1/chat/completions", {
    method: "POST",
    headers: { Authorization: `Bearer ${GROQ_KEY}`, "Content-Type": "application/json" },
    body: JSON.stringify({ model, messages, max_tokens: maxTokens, temperature: 0.7 }),
  });
  const data = await res.json() as Record<string, unknown>;
  if (!res.ok) return { error: `groq ${res.status}`, status: res.status };
  const text = (data?.choices as Array<{ message: { content: string } }>)?.[0]?.message?.content ?? "";
  if (!text) return { error: "groq empty reply", status: 0 };
  return { text, model, usage: data?.usage };
}

async function callGemini(prompt: string, system: string | undefined, model: string, maxTokens: number) {
  if (!GEMINI_KEY) return { error: "gemini key not configured", status: 0 };
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${GEMINI_KEY}`;
  const contents = [];
  if (system) contents.push({ role: "user", parts: [{ text: `[System]: ${system}` }] });
  contents.push({ role: "user", parts: [{ text: prompt }] });
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ contents, generationConfig: { maxOutputTokens: maxTokens } }),
  });
  const data = await res.json() as Record<string, unknown>;
  if (!res.ok) return { error: `gemini ${res.status}`, status: res.status };
  const text = (data?.candidates as Array<{ content: { parts: Array<{ text: string }> } }>)?.[0]?.content?.parts?.[0]?.text ?? "";
  if (!text) return { error: "gemini empty reply", status: 0 };
  return { text, model };
}

async function callPollinations(prompt: string, system: string | undefined, model: string, maxTokens: number) {
  const messages = [];
  if (system) messages.push({ role: "system", content: system });
  messages.push({ role: "user", content: prompt });
  const res = await fetch("https://text.pollinations.ai/openai", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model, messages, max_tokens: maxTokens, private: true }),
  });
  const data = await res.json() as Record<string, unknown>;
  if (!res.ok) return { error: `pollinations ${res.status}`, status: res.status };
  const text = (data?.choices as Array<{ message: { content: string } }>)?.[0]?.message?.content ?? "";
  if (!text) return { error: "pollinations empty reply", status: 0 };
  return { text, model, usage: data?.usage };
}

type CallResult =
  | { text: string; model: string; usage?: unknown }
  | { error: string; status: number };

const CALLERS: Record<string, (prompt: string, system: string | undefined, model: string, maxTokens: number) => Promise<CallResult>> = {
  groq: callGroq,
  gemini: callGemini,
  pollinations: callPollinations,
};

export async function POST(req: NextRequest) {
  if (!TF_KEY) {
    return NextResponse.json({ error: "TOKENFORGE_API_KEY not configured" }, { status: 503 });
  }
  if (req.headers.get("x-tf-key") !== TF_KEY) return unauthorized();

  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "invalid JSON body" }, { status: 400 });
  }
  const { prompt, provider = "auto", model, system } = body;
  if (!prompt || typeof prompt !== "string") {
    return NextResponse.json({ error: "prompt is required" }, { status: 400 });
  }
  if (prompt.length + String(system ?? "").length > PROMPT_CHAR_CAP) {
    return NextResponse.json({ error: `prompt too large (cap ${PROMPT_CHAR_CAP} chars)` }, { status: 413 });
  }
  if (typeof provider !== "string" || !FREE_PROVIDERS.includes(provider)) {
    return NextResponse.json(
      { error: `unsupported provider: ${String(provider)}. Free providers only: ${FREE_PROVIDERS.join(", ")}` },
      { status: 400 },
    );
  }
  const maxTokens = clampTokens(body.max_tokens);

  // "auto" stays zero-cost regardless of operator keys: Groq's free tier hard-stops
  // at quota (429, never a charge) and Pollinations is keyless. Gemini is excluded
  // because a paid-tier key in GEMINI_API_KEY would silently bill; pin it explicitly
  // only when the operator accepts that key's terms.
  const chain = provider === "auto"
    ? (["groq", "pollinations"] as const)
    : [provider as "groq" | "gemini" | "pollinations"];

  const errors: string[] = [];
  for (const p of chain) {
    const m = pickModel(p, provider === "auto" ? null : model);
    if (!m) {
      errors.push(`${p}: model not in free allowlist`);
      continue;
    }
    try {
      const out = await CALLERS[p](prompt, typeof system === "string" ? system : undefined, m, maxTokens);
      if ("text" in out) {
        return NextResponse.json({ ok: true, provider: p, model: out.model, text: out.text, usage: out.usage });
      }
      errors.push(`${p}: ${out.error}`);
    } catch (err) {
      errors.push(`${p}: ${String(err)}`);
    }
  }
  return NextResponse.json({ ok: false, error: `all free providers failed: ${errors.join("; ")}` }, { status: 502 });
}

export async function GET(req: NextRequest) {
  if (!TF_KEY || req.headers.get("x-tf-key") !== TF_KEY) {
    return NextResponse.json({ ok: false, error: "missing or invalid X-TF-Key" }, { status: 401 });
  }
  return NextResponse.json({
    ok: true,
    service: "tokenforge-integrated",
    version: "3.0.0",
    note: "Zero-cost LLM proxy: auto = groq free tier -> keyless pollinations. Gemini only when pinned explicitly (paid keys bill). Pollinations free tier: 1 reply/45s/IP.",
    providers: {
      groq: { configured: !!GROQ_KEY, models: GROQ_MODELS },
      gemini: { configured: !!GEMINI_KEY, models: GEMINI_MODELS },
      pollinations: { configured: true, keyless: true, models: POLLINATIONS_MODELS },
    },
    caps: { max_tokens: MAX_TOKENS_CAP, prompt_chars: PROMPT_CHAR_CAP },
    cost: "zero",
  });
}
