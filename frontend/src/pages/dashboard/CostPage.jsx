import React, { useEffect, useState } from "react";
import { DollarSign } from "lucide-react";
import { PageHeader, Metric } from "./_shared";
import { getCost } from "../../lib/api";

export default function CostPage() {
  const [cost, setCost] = useState(null);
  useEffect(() => { getCost().then(setCost).catch(() => {}); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, []);
  if (!cost) return <div className="px-6 py-10 md:px-10" data-testid="cost-page" />;
  return (
    <div className="px-6 py-10 md:px-10" data-testid="cost-page">
      <PageHeader eyebrow="// cost" title="$0/mo discipline." subtitle="Sovereign caps daily and monthly spend. Anything over the cap triggers the circuit breaker." />
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4 mb-6">
        <Metric label="spend today" value={`$${cost.today_usd}`} delta={`cap $${cost.daily_cap_usd}`} testId="cost-today" />
        <Metric label="spend MTD" value={`$${cost.month_usd}`} delta={`cap $${cost.monthly_cap_usd}`} testId="cost-month" />
        <Metric label="daily cap" value={`$${cost.daily_cap_usd}`} testId="cost-cap-day" />
        <Metric label="monthly cap" value={`$${cost.monthly_cap_usd}`} testId="cost-cap-mo" />
      </div>
      <div className="ent-card overflow-hidden">
        <table className="w-full text-sm">
          <thead><tr className="border-b border-line text-left text-[10px] uppercase tracking-widest text-ink-muted">
            <th className="px-5 py-3">category</th><th className="px-5 py-3 text-right">today</th>
            <th className="px-5 py-3 text-right">this month</th><th className="px-5 py-3 text-right">limit</th>
          </tr></thead>
          <tbody>
            {cost.categories.map((c) => (
              <tr key={c.category} className="border-b border-line last:border-b-0" data-testid={`cost-${c.category.replace(/[^a-z]/gi, '-').toLowerCase()}`}>
                <td className="px-5 py-4 flex items-center gap-2"><DollarSign className="h-3.5 w-3.5 text-ok" /> {c.category}</td>
                <td className="px-5 py-4 text-right font-mono">${c.today_usd.toFixed(2)}</td>
                <td className="px-5 py-4 text-right font-mono">${c.month_usd.toFixed(2)}</td>
                <td className="px-5 py-4 text-right text-ink-muted">${c.limit_usd.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
