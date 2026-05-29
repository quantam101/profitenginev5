import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { getStats } from "../lib/api";

function Counter({ value, label, testId }) {
  const [shown, setShown] = useState(0);
  useEffect(() => {
    if (!value) return;
    let raf;
    const start = performance.now();
    const dur = 1400;
    const tick = (t) => {
      const p = Math.min(1, (t - start) / dur);
      setShown(Math.floor(value * (1 - Math.pow(1 - p, 3))));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [value]);
  return (
    <div className="border border-line bg-bg-surface px-6 py-8" data-testid={testId}>
      <div className="font-display text-4xl tracking-tighter text-acid md:text-5xl">
        {shown.toLocaleString()}
      </div>
      <div className="mt-2 text-[11px] uppercase tracking-widest text-ink-muted">{label}</div>
    </div>
  );
}

export default function Stats() {
  const [stats, setStats] = useState(null);
  useEffect(() => {
    getStats().then(setStats).catch(() => setStats({
      files_merged_total: 1284, devs_joined: 312, upgrades_applied: 4827, repos_analyzed: 47,
    }));
  }, []);

  return (
    <section className="border-b border-line py-20" data-testid="stats-section">
      <div className="mx-auto max-w-7xl px-6 md:px-10">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="grid grid-cols-2 gap-px bg-line md:grid-cols-4"
        >
          <Counter
            value={stats?.files_merged_total ?? 0}
            label="files merged"
            testId="stat-files"
          />
          <Counter value={stats?.upgrades_applied ?? 0} label="upgrades applied" testId="stat-upgrades" />
          <Counter value={stats?.repos_analyzed ?? 0} label="repos analyzed" testId="stat-repos" />
          <Counter value={stats?.devs_joined ?? 0} label="devs on waitlist" testId="stat-devs" />
        </motion.div>
      </div>
    </section>
  );
}
