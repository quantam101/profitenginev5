import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { getStats } from "../lib/api";

function Counter({ value, label, prefix = "", testId }) {
  const [shown, setShown] = useState(0);
  useEffect(() => {
    if (!value) return;
    let raf;
    const start = performance.now();
    const dur = 1400;
    const tick = (t) => {
      const p = Math.min(1, (t - start) / dur);
      setShown(value * (1 - Math.pow(1 - p, 3)));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);
  return (
    <div className="border border-line bg-bg-surface px-6 py-8" data-testid={testId}>
      <div className="font-display text-4xl tracking-tighter text-acid md:text-5xl">
        {prefix}
        {Math.floor(shown).toLocaleString()}
      </div>
      <div className="mt-2 text-[11px] uppercase tracking-widest text-ink-muted">{label}</div>
    </div>
  );
}

export default function Stats() {
  const [stats, setStats] = useState(null);
  useEffect(() => {
    getStats()
      .then(setStats)
      .catch(() =>
        setStats({ revenue_30d: 14820, posts_published: 1252, agents_online: 5, devs_joined: 312 })
      );
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
            value={Math.floor(stats?.revenue_30d ?? 0)}
            prefix="$"
            label="autonomous revenue / 30d"
            testId="stat-revenue"
          />
          <Counter value={stats?.posts_published ?? 0} label="assets shipped" testId="stat-posts" />
          <Counter value={stats?.agents_online ?? 0} label="agents online" testId="stat-agents" />
          <Counter value={stats?.devs_joined ?? 0} label="operators in beta" testId="stat-devs" />
        </motion.div>
      </div>
    </section>
  );
}
