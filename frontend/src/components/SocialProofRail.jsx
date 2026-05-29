import React, { useEffect, useState } from "react";
import { Activity, Users, Coins, Repeat } from "lucide-react";
import { getSocialProof } from "../lib/api";

function Counter({ label, value, icon: Icon, testId }) {
  return (
    <div className="flex items-center gap-3 border-r border-line/60 px-6 py-4 last:border-r-0" data-testid={testId}>
      <Icon className="h-4 w-4 text-ok" strokeWidth={1.75} />
      <div>
        <div className="font-display text-xl tracking-tighter">{value}</div>
        <div className="mt-0.5 text-[10px] uppercase tracking-widest text-ink-faint">{label}</div>
      </div>
    </div>
  );
}

export default function SocialProofRail() {
  const [d, setD] = useState(null);
  useEffect(() => {
    let mounted = true;
    const load = () => getSocialProof().then((r) => mounted && setD(r)).catch(() => {});
    load();
    const t = setInterval(load, 12000);
    return () => { mounted = false; clearInterval(t); };
  }, []);
  return (
    <div
      className="mx-auto mt-12 grid max-w-5xl grid-cols-2 overflow-hidden border border-line bg-bg-panel/60 backdrop-blur md:grid-cols-4"
      data-testid="social-proof-rail"
    >
      <Counter
        label="operators joined"
        value={d?.operators_joined?.toLocaleString?.() || "—"}
        icon={Users}
        testId="sp-operators"
      />
      <Counter
        label="agent runs · all-time"
        value={d?.agent_runs_total?.toLocaleString?.() || "—"}
        icon={Activity}
        testId="sp-runs"
      />
      <Counter
        label="cycles completed"
        value={d?.cycles_ran_total?.toLocaleString?.() || "—"}
        icon={Repeat}
        testId="sp-cycles"
      />
      <Counter
        label="paid · cohort 1"
        value={d?.paid_subscribers?.toLocaleString?.() || "0"}
        icon={Coins}
        testId="sp-paid"
      />
    </div>
  );
}
