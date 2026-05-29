import React, { useEffect, useState } from "react";
import { Radar, Flame } from "lucide-react";
import { PageHeader } from "./_shared";
import { getScoutOpps } from "../../lib/api";

export default function ScoutPage() {
  const [opps, setOpps] = useState([]);
  useEffect(() => {
    getScoutOpps().then(setOpps).catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return (
    <div className="px-6 py-10 md:px-10" data-testid="scout-page">
      <PageHeader eyebrow="// scout" title="Trending opportunities." subtitle="Trend Scout surfaces monetizable signals from free public sources every 60 minutes." />
      <ul className="grid gap-4 md:grid-cols-2">
        {opps.map((o) => (
          <li key={o.id} className="ent-card p-5" data-testid={`opp-${o.id}`}>
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2 text-[11px] uppercase tracking-widest text-ink-muted">
                <Radar className="h-3.5 w-3.5 text-ok" /> {o.source}
              </div>
              <span className="badge badge-ok">score {(o.score * 100).toFixed(0)}</span>
            </div>
            <h3 className="mt-2 font-display text-lg">{o.title}</h3>
            <div className="mt-3 flex items-center justify-between text-[11px] text-ink-muted">
              <span className="inline-flex items-center gap-1"><Flame className="h-3 w-3 text-warn" /> velocity {o.velocity}x</span>
              <span>est. yield <span className="text-ok">${o.estimated_yield_usd}</span></span>
              <span>{o.captured_at}</span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
