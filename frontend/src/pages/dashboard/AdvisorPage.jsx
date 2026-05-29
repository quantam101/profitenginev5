import React, { useState } from "react";
import { Send, Loader2, MessageCircle } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "./_shared";
import { askAdvisor } from "../../lib/api";

export default function AdvisorPage() {
  const [q, setQ] = useState("");
  const [log, setLog] = useState([]);
  const [loading, setLoading] = useState(false);
  const submit = async (e) => {
    e.preventDefault();
    if (!q.trim()) return;
    setLoading(true);
    const question = q.trim();
    setQ("");
    try {
      const r = await askAdvisor(question);
      setLog((l) => [...l, { question, ...r }]);
    } catch {
      toast.error("Advisor unreachable");
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className="px-6 py-10 md:px-10" data-testid="advisor-page">
      <PageHeader eyebrow="// advisor" title="Ask Sovereign." subtitle="Sovereign is your strategic advisor — wired to the same telemetry as the rest of the agents. Ask anything." />
      <form onSubmit={submit} className="ent-card p-5" data-testid="advisor-form">
        <div className="flex items-center gap-3">
          <MessageCircle className="h-5 w-5 text-ok" strokeWidth={1.5} />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="e.g. which revenue stream should we double down on this week?"
            className="flex-1 bg-transparent text-sm outline-none placeholder:text-ink-faint"
            data-testid="advisor-input"
          />
          <button type="submit" disabled={loading} data-testid="advisor-submit"
            className="inline-flex items-center gap-1 rounded-soft border border-ok bg-ok/10 px-3 py-2 text-[11px] font-bold uppercase tracking-widest text-ok hover:bg-ok hover:text-bg-deep disabled:opacity-60">
            {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />} ask
          </button>
        </div>
      </form>
      <div className="mt-6 space-y-4">
        {log.map((m) => (
          <div key={m.at} className="space-y-2" data-testid={`advisor-msg-${m.at}`}>
            <div className="ent-card p-4 text-sm"><span className="text-ink-faint text-[11px] uppercase tracking-widest">you</span><p className="mt-1">{m.question}</p></div>
            <div className="sov-card p-4 text-sm"><span className="text-sov-soft text-[11px] uppercase tracking-widest">{m.agent}</span><p className="mt-1">{m.answer}</p></div>
          </div>
        ))}
      </div>
    </div>
  );
}
