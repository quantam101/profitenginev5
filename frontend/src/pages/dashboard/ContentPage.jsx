import React, { useEffect, useState } from "react";
import { FileText, ExternalLink } from "lucide-react";
import { getContent } from "../../lib/api";

const STATUS_TONE = {
  published: "border-acid text-acid",
  queued: "border-yellow-400 text-yellow-400",
  draft: "border-line text-ink-muted",
};

export default function ContentPage() {
  const [content, setContent] = useState([]);
  useEffect(() => {
    getContent().then(setContent).catch(() => {});
  }, []);
  return (
    <div className="px-6 py-10 md:px-10" data-testid="content-page">
      <header className="mb-10">
        <div className="mb-2 text-[11px] uppercase tracking-widest text-acid">// content studio</div>
        <h1 className="font-display text-3xl tracking-tighter md:text-4xl">Recent assets shipped.</h1>
        <p className="mt-2 text-sm text-ink-muted">
          Every asset Content + Video produced and pushed through Social, with attribution to the
          revenue it earned.
        </p>
      </header>

      <div className="border border-line bg-bg-surface" data-testid="content-table">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line text-left text-[10px] uppercase tracking-widest text-ink-muted">
              <th className="px-5 py-3">title</th>
              <th className="px-5 py-3">channel</th>
              <th className="px-5 py-3">status</th>
              <th className="px-5 py-3 text-right">revenue</th>
              <th className="px-5 py-3">created</th>
              <th className="px-5 py-3" />
            </tr>
          </thead>
          <tbody>
            {content.map((c) => (
              <tr key={c.id} className="border-b border-line last:border-b-0 hover:bg-bg-elev" data-testid={`content-row-${c.id}`}>
                <td className="px-5 py-4">
                  <span className="flex items-center gap-2">
                    <FileText className="h-3.5 w-3.5 text-acid" strokeWidth={1.5} />
                    <span className="text-ink">{c.title}</span>
                  </span>
                </td>
                <td className="px-5 py-4 text-ink-muted">{c.channel}</td>
                <td className="px-5 py-4">
                  <span className={`border px-2 py-0.5 text-[10px] uppercase tracking-widest ${STATUS_TONE[c.status]}`}>
                    {c.status}
                  </span>
                </td>
                <td className="px-5 py-4 text-right text-acid">
                  {c.revenue ? `$${c.revenue.toFixed(2)}` : "—"}
                </td>
                <td className="px-5 py-4 text-ink-muted">{c.created_at}</td>
                <td className="px-5 py-4 text-right">
                  <button className="text-ink-muted transition-colors hover:text-acid" data-testid={`content-open-${c.id}`}>
                    <ExternalLink className="h-4 w-4" strokeWidth={1.5} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
