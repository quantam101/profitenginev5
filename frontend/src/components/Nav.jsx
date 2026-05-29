import React, { useState, useEffect } from "react";
import { Github, Terminal } from "lucide-react";

const links = [
  { id: "features", label: "// features" },
  { id: "playground", label: "// playground" },
  { id: "demo", label: "// demo" },
  { id: "pricing", label: "// pricing" },
];

export default function Nav() {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const on = () => setScrolled(window.scrollY > 8);
    window.addEventListener("scroll", on);
    return () => window.removeEventListener("scroll", on);
  }, []);
  return (
    <header
      data-testid="site-nav"
      className={`fixed top-0 left-0 right-0 z-50 border-b transition-colors ${
        scrolled ? "bg-bg/90 backdrop-blur border-line" : "bg-transparent border-transparent"
      }`}
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 md:px-10">
        <a href="#top" className="flex items-center gap-2 font-display text-lg tracking-tight">
          <Terminal className="h-5 w-5 text-acid" strokeWidth={1.5} />
          <span>PROFIT<span className="text-acid">ENGINE</span></span>
          <span className="ml-1 text-xs text-ink-faint">v0.1</span>
        </a>
        <nav className="hidden gap-6 text-xs text-ink-muted md:flex">
          {links.map((l) => (
            <a
              key={l.id}
              href={`#${l.id}`}
              className="transition-colors hover:text-acid"
              data-testid={`nav-link-${l.id}`}
            >
              {l.label}
            </a>
          ))}
        </nav>
        <div className="flex items-center gap-3">
          <a
            href="https://github.com/quantam101"
            target="_blank"
            rel="noreferrer"
            className="text-ink-muted transition-colors hover:text-acid"
            data-testid="nav-github"
          >
            <Github className="h-5 w-5" strokeWidth={1.5} />
          </a>
          <a
            href="#waitlist"
            className="border border-acid bg-acid px-4 py-2 text-[11px] font-bold uppercase tracking-widest text-black shadow-glowSm transition-colors hover:bg-acid-soft"
            data-testid="nav-cta-waitlist"
          >
            Join waitlist
          </a>
        </div>
      </div>
    </header>
  );
}
