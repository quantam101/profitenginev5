import React from "react";
import { Link } from "react-router-dom";
import { Github, Terminal } from "lucide-react";

export default function Footer() {
  return (
    <footer className="relative z-10 border-t border-line bg-bg-panel py-12" data-testid="site-footer">
      <div className="mx-auto grid max-w-7xl gap-10 px-6 md:grid-cols-4 md:px-10">
        <div className="md:col-span-2">
          <div className="flex items-center gap-2 font-display text-lg">
            <Terminal className="h-5 w-5 text-ok" strokeWidth={1.5} />
            <span>PROFIT<span className="text-ok">ENGINE</span> <span className="text-ink-muted">v5</span></span>
          </div>
          <p className="mt-3 max-w-sm text-xs leading-relaxed text-ink-muted">
            Six-agent autonomous content engine, open core. Built by the team behind
            already-here-llc-dashboard. The same cockpit, now self-upgrading.
          </p>
          <code className="mt-5 inline-block border border-line bg-bg px-3 py-2 text-xs">
            <span className="text-ok">$</span> git clone github.com/quantam101/profitenginev5
          </code>
        </div>

        <div>
          <div className="mb-3 text-[11px] uppercase tracking-widest text-ink-muted">// product</div>
          <ul className="space-y-2 text-xs text-ink">
            <li><a href="#agents" className="transition-colors hover:text-ok">Agents</a></li>
            <li><Link to="/dashboard" className="transition-colors hover:text-ok">Dashboard</Link></li>
            <li><a href="#engine" className="transition-colors hover:text-ok">Self-merge engine</a></li>
            <li><a href="#pricing" className="transition-colors hover:text-ok">Pricing</a></li>
            <li><a href="#roadmap" className="transition-colors hover:text-ok">Roadmap</a></li>
          </ul>
        </div>

        <div>
          <div className="mb-3 text-[11px] uppercase tracking-widest text-ink-muted">// resources</div>
          <ul className="space-y-2 text-xs text-ink">
            <li>
              <a
                href="https://github.com/quantam101/profitenginev5"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 transition-colors hover:text-ok"
              >
                <Github className="h-3.5 w-3.5" /> profitenginev5
              </a>
            </li>
            <li>
              <a
                href="https://github.com/quantam101/already-here-dashboard"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 transition-colors hover:text-ok"
              >
                <Github className="h-3.5 w-3.5" /> already-here-dashboard
              </a>
            </li>
            <li><a href="#waitlist" className="transition-colors hover:text-ok">Beta waitlist</a></li>
            <li><a href="#faq" className="transition-colors hover:text-ok">FAQ</a></li>
          </ul>
        </div>
      </div>

      <div className="mx-auto mt-12 flex max-w-7xl items-center justify-between border-t border-line px-6 pt-6 text-[11px] text-ink-faint md:px-10">
        <span>© 2026 ProfitEngine · Open core, MIT.</span>
        <span className="text-ok">v5.0 — closed beta</span>
      </div>
    </footer>
  );
}
