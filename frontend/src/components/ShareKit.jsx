import React from "react";
import { Twitter, Linkedin, Link2 } from "lucide-react";
import { toast } from "sonner";

const SHARE_TEXT =
  "I just joined ProfitEngine v5 — 11 AI agents running an entire content business 24/7. Open core + token-distilled. Get in →";

export default function ShareKit() {
  const url = typeof window !== "undefined" ? window.location.origin : "https://profitengine.dev";
  const encoded = encodeURIComponent(`${SHARE_TEXT} ${url}`);
  const x = `https://twitter.com/intent/tweet?text=${encoded}`;
  const li = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`;
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(url);
      toast.success("Launch URL copied — paste it everywhere");
    } catch {
      toast.error("Couldn't copy — long-press the URL instead");
    }
  };
  return (
    <div className="mt-8 flex flex-wrap items-center gap-3 text-[11px]" data-testid="share-kit">
      <span className="uppercase tracking-widest text-ink-faint">amplify the launch →</span>
      <a
        href={x}
        target="_blank"
        rel="noreferrer"
        className="inline-flex items-center gap-1.5 border border-line bg-bg-panel px-3 py-1.5 text-ink-muted transition-colors hover:border-ok hover:text-ok"
        data-testid="share-twitter"
      >
        <Twitter className="h-3.5 w-3.5" /> share on X
      </a>
      <a
        href={li}
        target="_blank"
        rel="noreferrer"
        className="inline-flex items-center gap-1.5 border border-line bg-bg-panel px-3 py-1.5 text-ink-muted transition-colors hover:border-ok hover:text-ok"
        data-testid="share-linkedin"
      >
        <Linkedin className="h-3.5 w-3.5" /> linkedin
      </a>
      <button
        type="button"
        onClick={copy}
        className="inline-flex items-center gap-1.5 border border-line bg-bg-panel px-3 py-1.5 text-ink-muted transition-colors hover:border-ok hover:text-ok"
        data-testid="share-copy"
      >
        <Link2 className="h-3.5 w-3.5" /> copy link
      </button>
    </div>
  );
}
