import React, { useEffect, useState } from "react";
import { FileCode2, ArrowUpRight, PackageOpen } from "lucide-react";
import { getDemoReport } from "../lib/api";

export default function DemoReport() {
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getDemoReport().then(setReport).catch((e) => setError(e?.message || "unavailable"));
  }, []);

  return (
    <section id="demo" className="border-b border-line py-24 md:py-32" data-testid="demo-section">
      <div className="mx-auto max-w-7xl px-6 md:px-10">
        <div className="mb-12 grid items-end gap-6 md:grid-cols-12">
          <div className="md:col-span-8">
            <div className="mb-4 text-[11px] uppercase tracking-widest text-acid">// real-world run</div>
            <h2 className="font-display text-4xl leading-tight tracking-tighter md:text-5xl">
              We merged <span className="text-acid">profitenginev5</span><br />
              with <span className="text-acid">already-here-dashboard</span>.
            </h2>
            <p className="mt-4 max-w-2xl text-sm text-ink-muted">
              Live report from the CLI running across both repos. No fixtures — these are the actual
              upgrades the engine picked.
            </p>
          </div>
          <div className="text-xs text-ink-muted md:col-span-4 md:text-right">
            <code className="block border border-line bg-bg-surface px-3 py-2">
              <span className="text-acid">$</span> profitengine repo ./pev5 ./ahd -o ./merged
            </code>
          </div>
        </div>

        {error && (
          <div className="border border-line bg-bg-surface p-6 text-sm text-ink-muted" data-testid="demo-error">
            Couldn't load demo report ({error}). Re-run the CLI to regenerate.
          </div>
        )}

        {report && (
          <div data-testid="demo-report">
            <div className="grid grid-cols-2 gap-px bg-line md:grid-cols-4">
              <Stat label="files paired" value={report.totals.files_processed} />
              <Stat label="files upgraded" value={report.totals.files_with_upgrades} />
              <Stat label="functions swapped" value={report.totals.upgrades} />
              <Stat label="blocks added" value={report.totals.additions} />
            </div>

            <div className="mt-px grid gap-px bg-line md:grid-cols-2">
              <FileList
                title="upgraded files"
                icon={ArrowUpRight}
                items={report.files_merged.filter((f) => f.upgrades.length).slice(0, 6)}
                renderMeta={(f) => `${f.upgrades.length} upgrade(s)`}
              />
              <FileList
                title="files that added new blocks"
                icon={PackageOpen}
                items={report.files_merged.filter((f) => f.additions.length).slice(0, 6)}
                renderMeta={(f) => `+${f.additions.length} block(s)`}
              />
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

function Stat({ label, value }) {
  return (
    <div className="bg-bg-surface p-6">
      <div className="font-display text-3xl tracking-tighter text-acid md:text-4xl">{value}</div>
      <div className="mt-2 text-[11px] uppercase tracking-widest text-ink-muted">{label}</div>
    </div>
  );
}

function FileList({ title, items, renderMeta, icon: Icon }) {
  return (
    <div className="bg-bg-surface p-6">
      <div className="mb-4 flex items-center gap-2 text-[11px] uppercase tracking-widest text-ink-muted">
        <Icon className="h-3.5 w-3.5 text-acid" strokeWidth={1.5} /> {title}
      </div>
      {items.length === 0 ? (
        <p className="text-sm text-ink-muted">(none in this run)</p>
      ) : (
        <ul className="space-y-2">
          {items.map((f) => {
            const short = f.output_path.split("/").slice(-3).join("/");
            return (
              <li key={f.output_path} className="border border-line bg-bg p-3">
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-2 truncate font-mono text-xs">
                    <FileCode2 className="h-3.5 w-3.5 text-acid" strokeWidth={1.5} />
                    <span className="truncate text-ink">{short}</span>
                  </span>
                  <span className="ml-2 shrink-0 text-[11px] text-acid">{renderMeta(f)}</span>
                </div>
                {f.upgrades.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1 text-[10px] text-ink-muted">
                    {f.upgrades.slice(0, 3).map((u) => (
                      <span key={u.name} className="border border-line px-2 py-0.5">
                        {u.name} +{u.delta}
                      </span>
                    ))}
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
