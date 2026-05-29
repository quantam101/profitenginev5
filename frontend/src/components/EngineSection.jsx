import React, { useState } from "react";
import { motion } from "framer-motion";
import { Play, Loader2, GitMerge, TrendingUp } from "lucide-react";
import { toast } from "sonner";
import { postMerge } from "../lib/api";

const SAMPLES = {
  python: {
    base: `def fetch_revenue(stream_id):
    return db.find(stream_id)
`,
    target: `import logging

def fetch_revenue(stream_id: str) -> dict:
    """Fetch revenue for one stream with retry + structured logging."""
    try:
        record = db.find(stream_id)
        if not record:
            raise ValueError(f"stream {stream_id} missing")
        return record
    except Exception as exc:
        logging.error("revenue.fetch.failed", extra={"stream_id": stream_id, "err": str(exc)})
        return {}
`,
  },
  js: {
    base: `function dispatch(event) {
  fetch('/api/bus', { method: 'POST', body: JSON.stringify(event) })
}
`,
    target: `/** Dispatch an event to the cycle bus with retry + correlation id. */
async function dispatch(event: BusEvent): Promise<void> {
  try {
    const r = await fetch('/api/bus', {
      method: 'POST',
      headers: { 'x-corr-id': crypto.randomUUID() },
      body: JSON.stringify(event),
    })
    if (!r.ok) throw new Error('bus reject')
  } catch (e) { throw e }
}
`,
  },
};

export default function EngineSection() {
  const [lang, setLang] = useState("python");
  const [base, setBase] = useState(SAMPLES.python.base);
  const [target, setTarget] = useState(SAMPLES.python.target);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const switchLang = (l) => {
    setLang(l);
    setBase(SAMPLES[l].base);
    setTarget(SAMPLES[l].target);
    setResult(null);
  };

  const runMerge = async () => {
    setLoading(true);
    setResult(null);
    try {
      const data = await postMerge({ language: lang, base, target, add_unique: false });
      setResult(data);
      if (!data.upgrades.length) toast("Base already wins — no upgrades applied.");
      else toast.success(`${data.upgrades.length} block(s) upgraded.`);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Merge failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section id="engine" className="border-b border-line py-24 md:py-32" data-testid="engine-section">
      <div className="mx-auto max-w-7xl px-6 md:px-10">
        <div className="mb-12 grid items-end gap-6 md:grid-cols-12">
          <div className="md:col-span-8">
            <div className="mb-4 text-[11px] uppercase tracking-widest text-acid">// under the hood</div>
            <h2 className="font-display text-4xl leading-tight tracking-tighter md:text-5xl">
              v5 self-upgrades<br />
              <span className="text-acid">function by function.</span>
            </h2>
            <p className="mt-5 max-w-2xl text-sm leading-relaxed text-ink-muted">
              Every release, ProfitEngine's AST merger compares the v5 codebase to the
              already-here-dashboard production code, scores each function on robustness, typing
              and complexity, and pulls in the winners. No prompts. No LLM drift.
            </p>
          </div>
          <div className="flex items-center gap-2 md:col-span-4 md:justify-end">
            {["python", "js"].map((l) => (
              <button
                key={l}
                onClick={() => switchLang(l)}
                data-testid={`engine-lang-${l}`}
                className={`border px-4 py-2 text-[11px] font-bold uppercase tracking-widest transition-colors ${
                  lang === l
                    ? "border-acid bg-acid text-black shadow-glowSm"
                    : "border-line bg-bg-surface text-ink-muted hover:border-acid hover:text-acid"
                }`}
              >
                {l === "python" ? "python" : "js / ts"}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 gap-px bg-line lg:grid-cols-2">
          <Editor label="// v5 baseline" value={base} onChange={setBase} testId="editor-base" />
          <Editor label="// already-here candidate" value={target} onChange={setTarget} testId="editor-target" />
        </div>

        <div className="mt-6 flex flex-wrap items-center justify-between gap-4">
          <p className="text-xs text-ink-muted">
            <span className="text-acid">tip:</span> v5 swaps a baseline function only when the
            candidate's quality score is strictly higher.
          </p>
          <button
            onClick={runMerge}
            disabled={loading}
            data-testid="engine-merge-btn"
            className="inline-flex items-center gap-2 border border-acid bg-acid px-6 py-3 text-xs font-bold uppercase tracking-widest text-black shadow-glow transition-colors hover:bg-acid-soft disabled:opacity-60"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            {loading ? "merging..." : "run merge"}
          </button>
        </div>

        {result && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-10 grid gap-px bg-line lg:grid-cols-3"
            data-testid="engine-result"
          >
            <div className="bg-bg-surface p-6 lg:col-span-2">
              <div className="mb-4 flex items-center justify-between text-[11px] uppercase tracking-widest text-ink-muted">
                <span>// merged output</span>
                <span className="text-acid">{result.merged.split("\n").length} lines</span>
              </div>
              <pre className="max-h-[420px] overflow-auto bg-black/40 p-4 text-xs leading-relaxed text-ink" data-testid="merged-output">
                {result.merged}
              </pre>
            </div>
            <div className="bg-bg-surface p-6">
              <div className="mb-4 flex items-center gap-2 text-[11px] uppercase tracking-widest text-ink-muted">
                <GitMerge className="h-3.5 w-3.5 text-acid" /> upgrades
              </div>
              {result.upgrades.length === 0 ? (
                <p className="text-sm text-ink-muted">No swaps — v5 baseline already wins.</p>
              ) : (
                <ul className="space-y-3">
                  {result.upgrades.map((u) => (
                    <li key={u.name} className="border border-line bg-bg p-3" data-testid={`upgrade-${u.name}`}>
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-sm text-acid">{u.name}</span>
                        <span className="inline-flex items-center gap-1 text-[11px] text-ink-muted">
                          <TrendingUp className="h-3 w-3 text-acid" />
                          {u.base} → {u.target}
                        </span>
                      </div>
                      {u.reason && (
                        <p className="mt-2 text-[11px] leading-relaxed text-ink-muted">{u.reason}</p>
                      )}
                    </li>
                  ))}
                </ul>
              )}
              {result.added_imports?.length > 0 && (
                <div className="mt-6">
                  <div className="mb-2 text-[11px] uppercase tracking-widest text-ink-muted">// imports added</div>
                  <ul className="space-y-1 font-mono text-xs text-acid">
                    {result.added_imports.map((imp) => (
                      <li key={imp}>+ {imp}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </div>
    </section>
  );
}

function Editor({ label, value, onChange, testId }) {
  return (
    <div className="flex flex-col bg-bg-surface">
      <div className="flex items-center justify-between border-b border-line px-4 py-2 text-[11px] uppercase tracking-widest text-ink-muted">
        <span>{label}</span>
        <span className="text-ink-faint">{value.split("\n").length} ln</span>
      </div>
      <textarea
        value={value}
        spellCheck={false}
        onChange={(e) => onChange(e.target.value)}
        className="min-h-[320px] w-full resize-y bg-black/40 p-4 text-xs leading-relaxed text-ink outline-none focus:bg-black/60"
        data-testid={testId}
      />
    </div>
  );
}
