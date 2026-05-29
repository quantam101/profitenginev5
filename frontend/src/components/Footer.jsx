import React from "react";
import { Github, Terminal } from "lucide-react";

export default function Footer() {
  return (
    <footer className="relative z-10 border-t border-line bg-bg-surface py-12" data-testid="site-footer">
      <div className="mx-auto grid max-w-7xl gap-10 px-6 md:grid-cols-4 md:px-10">
        <div className="md:col-span-2">
          <div className="flex items-center gap-2 font-display text-lg">
            <Terminal className="h-5 w-5 text-acid" strokeWidth={1.5} />
            <span>PROFIT<span className="text-acid">ENGINE</span></span>
          </div>
          <p className="mt-3 max-w-sm text-xs leading-relaxed text-ink-muted">
            AST-native code merger for senior engineers. Built by the team behind
            already-here-dashboard &amp; profitenginev5.
          </p>
          <code className="mt-5 inline-block border border-line bg-bg px-3 py-2 text-xs">
            <span className="text-acid">$</span> pip install profitengine
          </code>
        </div>

        <div>
          <div className="mb-3 text-[11px] uppercase tracking-widest text-ink-muted">// product</div>
          <ul className="space-y-2 text-xs text-ink">
            <li><a href="#features" className="transition-colors hover:text-acid">Features</a></li>
            <li><a href="#playground" className="transition-colors hover:text-acid">Playground</a></li>
            <li><a href="#demo" className="transition-colors hover:text-acid">Demo report</a></li>
            <li><a href="#pricing" className="transition-colors hover:text-acid">Pricing</a></li>
          </ul>
        </div>

        <div>
          <div className="mb-3 text-[11px] uppercase tracking-widest text-ink-muted">// resources</div>
          <ul className="space-y-2 text-xs text-ink">
            <li>
              <a
                href="https://github.com/quantam101"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 transition-colors hover:text-acid"
              >
                <Github className="h-3.5 w-3.5" /> GitHub
              </a>
            </li>
            <li><a href="#waitlist" className="transition-colors hover:text-acid">Waitlist</a></li>
            <li><a href="#" className="transition-colors hover:text-acid">Docs (soon)</a></li>
            <li><a href="#" className="transition-colors hover:text-acid">Changelog (soon)</a></li>
          </ul>
        </div>
      </div>

      <div className="mx-auto mt-12 flex max-w-7xl items-center justify-between border-t border-line px-6 pt-6 text-[11px] text-ink-faint md:px-10">
        <span>© 2026 ProfitEngine · Built in Tahoe, deployed everywhere.</span>
        <span className="text-acid">v0.1.0 — alpha</span>
      </div>
    </footer>
  );
}
