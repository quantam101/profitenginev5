import React, { useEffect, useState } from "react";
import { ShieldCheck, AlertTriangle, AlertCircle, Loader2, CheckCircle2, Clock } from "lucide-react";
import { PageHeader, Metric } from "./_shared";
import { getLifelongIssues } from "../../lib/api";

const RISK_TONE = {
  low: { border: "border-ok/40", bg: "bg-ok/5", text: "text-ok", icon: ShieldCheck },
  medium: { border: "border-warn/40", bg: "bg-warn/5", text: "text-warn", icon: AlertTriangle },
  high: { border: "border-danger/40", bg: "bg-danger/5", text: "text-danger", icon: AlertCircle },
};

const STATUS_BADGE = {
  queued: { class: "badge", label: "queued", icon: Clock },
  in_progress: { class: "badge badge-warn", label: "in progress", icon: Loader2 },
  corrected: { class: "badge badge-ok", label: "corrected", icon: CheckCircle2 },
};

function Row({ label, value }) {
  if (!value) return null;
  return (
    <div className="grid grid-cols-[140px_1fr] items-start gap-4 text-sm">
      <div className="text-[10px] uppercase tracking-widest text-ink-faint">{label}</div>
      <div className="text-ink-muted leading-relaxed">{value}</div>
    </div>
  );
}

function IssueCard({ issue }) {
  const tone = RISK_TONE[issue.risk_level] || RISK_TONE.low;
  const status = STATUS_BADGE[issue.status] || STATUS_BADGE.queued;
  const Icon = tone.icon;
  const StatusIcon = status.icon;
  return (
    <li
      className={`ent-card border-2 p-6 ${tone.border} ${tone.bg}`}
      data-testid={`lifelong-issue-${issue.id}`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <Icon className={`mt-1 h-5 w-5 ${tone.text}`} strokeWidth={1.75} />
          <div>
            <div className="text-[10px] uppercase tracking-widest text-ink-faint">
              detected · {issue.detected_at}
            </div>
            <h3 className="mt-1 font-display text-lg leading-tight">{issue.detected_issue}</h3>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`inline-flex items-center gap-1 border px-2 py-0.5 text-[10px] font-bold uppercase tracking-widest ${tone.border} ${tone.text}`}>
            {issue.risk_level} risk
          </span>
          <span className={status.class}>
            <StatusIcon className={`mr-1 inline h-3 w-3 ${issue.status === "in_progress" ? "animate-spin" : ""}`} />
            {status.label}
          </span>
        </div>
      </div>
      <div className="mt-5 space-y-3">
        <Row label="root cause" value={issue.root_cause} />
        <Row label="business impact" value={issue.business_impact} />
        <Row label="correction" value={issue.recommended_correction} />
        <Row label="assigned agent" value={issue.assigned_agent} />
        <Row label="expected improvement" value={issue.expected_improvement} />
        <Row label="result" value={issue.result_after_correction} />
      </div>
    </li>
  );
}

export default function LifelongPage() {
  const [issues, setIssues] = useState([]);
  useEffect(() => {
    getLifelongIssues(50).then(setIssues).catch(() => {});
  }, []);

  const open = issues.filter((i) => i.status !== "corrected").length;
  const high = issues.filter((i) => i.risk_level === "high").length;
  const corrected = issues.filter((i) => i.status === "corrected").length;

  return (
    <div className="px-6 py-10 md:px-10" data-testid="lifelong-page">
      <PageHeader
        eyebrow="// lifelong catch & correct"
        title="Catch problems before they compound."
        subtitle="Every cycle scans for failed targets, weak offers, broken automations, bad pricing, slow fulfillment, security risks and repeated mistakes. The fleet diagnoses, assigns, corrects and verifies — and logs every loop for replay."
      />
      <div className="mb-8 grid grid-cols-2 gap-4 md:grid-cols-4">
        <Metric label="open issues" value={open} testId="lcc-open" />
        <Metric label="high risk" value={high} tone={high ? "danger" : "ok"} testId="lcc-high" />
        <Metric label="corrected · all-time" value={corrected} tone="ok" testId="lcc-corrected" />
        <Metric label="cycle scan" value="every 60s" testId="lcc-cadence" />
      </div>
      <ul className="space-y-4" data-testid="lifelong-list">
        {issues.map((i) => <IssueCard key={i.id} issue={i} />)}
      </ul>
    </div>
  );
}
