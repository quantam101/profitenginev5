import React, { useEffect, useState } from "react";
import { Flame, X } from "lucide-react";
import { getCohort } from "../lib/api";

export default function CohortBar() {
  const [c, setC] = useState(null);
  const [closed, setClosed] = useState(false);
  useEffect(() => {
    if (closed) return;
    getCohort().then(setC).catch(() => {});
    const t = setInterval(() => getCohort().then(setC).catch(() => {}), 30000);
    return () => clearInterval(t);
  }, [closed]);
  if (closed || !c) return null;
  return (
    <div
      className="fixed inset-x-0 bottom-0 z-40 border-t border-ok/40 bg-bg-elev/95 backdrop-blur-md shadow-glow"
      data-testid="cohort-bar"
    >
      <div className="mx-auto flex max-w-7xl items-center gap-4 px-6 py-3 text-xs md:px-10">
        <Flame className="h-4 w-4 shrink-0 animate-pulse text-ok" strokeWidth={2} />
        <div className="flex-1 truncate">
          <span className="font-bold uppercase tracking-widest text-ok">{c.label}</span>
          <span className="ml-3 text-ink-muted">
            {c.remaining} of {c.total_seats} seats remaining
            <span className="mx-2 text-ink-faint">·</span>
            closes {new Date(c.closes_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
          </span>
        </div>
        <div className="hidden h-1.5 w-40 overflow-hidden rounded-soft bg-bg/80 md:block">
          <div
            className="h-full bg-ok transition-all duration-500"
            style={{ width: `${Math.min(100, c.pct_full)}%` }}
            data-testid="cohort-bar-progress"
          />
        </div>
        <a
          href="#pricing"
          className="border border-ok bg-ok px-4 py-1.5 text-[10px] font-bold uppercase tracking-widest text-black shadow-glow hover:bg-ok-soft"
          data-testid="cohort-bar-claim"
        >
          claim seat →
        </a>
        <button
          type="button"
          onClick={() => setClosed(true)}
          className="text-ink-faint hover:text-ink"
          aria-label="Dismiss"
          data-testid="cohort-bar-close"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}
