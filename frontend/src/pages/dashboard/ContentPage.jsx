import React, { useEffect, useState } from "react";
import { FileText, ExternalLink } from "lucide-react";
import { PageHeader, StatusBadge } from "./_shared";
import { getContent } from "../../lib/api";

export default function ContentPage() {
  const [content, setContent] = useState([]);
  useEffect(() => {
    getContent().then(setContent).catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return (
    <div className="px-6 py-10 md:px-10" data-testid="content-page">
      <PageHeader eyebrow="// content studio" title="Recent assets shipped." subtitle="Every asset Content + Video produced and pushed through Social, with attribution to the revenue it earned." />
      <div className="ent-card overflow-hidden" data-testid="content-table">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line text-left text-[10px] uppercase tracking-widest text-ink-muted">
              <th className="px-5 py-3">title</th><th className="px-5 py-3">channel</th><th className="px-5 py-3">status</th>
              <th className="px-5 py-3 text-right">words</th><th className="px-5 py-3 text-right">revenue</th>
              <th className="px-5 py-3">created</th><th className="px-5 py-3" />
            </tr>
          </thead>
          <tbody>
            {content.map((c) => (
              <tr key={c.id} className="border-b border-line last:border-b-0 hover:bg-bg-elev/40" data-testid={`content-row-${c.id}`}>
                <td className="px-5 py-4"><span className="flex items-center gap-2"><FileText className="h-3.5 w-3.5 text-ok" strokeWidth={1.5} /><span>{c.title}</span></span></td>
                <td className="px-5 py-4 text-ink-muted">{c.channel}</td>
                <td className="px-5 py-4"><StatusBadge status={c.status} /></td>
                <td className="px-5 py-4 text-right text-ink-muted">{c.word_count.toLocaleString()}</td>
                <td className="px-5 py-4 text-right text-ok">{c.revenue ? `$${c.revenue.toFixed(2)}` : "—"}</td>
                <td className="px-5 py-4 text-ink-muted">{c.created_at}</td>
                <td className="px-5 py-4 text-right">
                  <button className="text-ink-muted hover:text-ok" data-testid={`content-open-${c.id}`}><ExternalLink className="h-4 w-4" strokeWidth={1.5} /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
