import React, { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import {
  Crown, LayoutDashboard, Cpu, ShieldAlert, MessageCircleQuestion, Radar,
  FileText, BarChart3, BookOpen, Server, GitBranch, ScrollText, Vote,
  Award, LineChart, Sparkles, DollarSign, KeyRound, ArrowLeft, Activity, Terminal,
} from "lucide-react";
import { getCycleStatus, getSovereignStatus } from "../../lib/api";

const NAV_GROUPS = [
  {
    label: "Command",
    links: [
      { to: "/dashboard", label: "Overview", icon: LayoutDashboard, end: true, testId: "sidebar-overview" },
      { to: "/dashboard/sovereign", label: "Sovereign", icon: Crown, sov: true, testId: "sidebar-sovereign" },
      { to: "/dashboard/agents", label: "Agents", icon: Cpu, testId: "sidebar-agents" },
      { to: "/dashboard/approvals", label: "Approvals", icon: ShieldAlert, testId: "sidebar-approvals" },
      { to: "/dashboard/advisor", label: "Advisor", icon: MessageCircleQuestion, testId: "sidebar-advisor" },
    ],
  },
  {
    label: "Operations",
    links: [
      { to: "/dashboard/scout", label: "Scout", icon: Radar, testId: "sidebar-scout" },
      { to: "/dashboard/content", label: "Content", icon: FileText, testId: "sidebar-content" },
      { to: "/dashboard/revenue", label: "Revenue", icon: BarChart3, testId: "sidebar-revenue" },
      { to: "/dashboard/books", label: "Books", icon: BookOpen, testId: "sidebar-books" },
    ],
  },
  {
    label: "Infrastructure",
    links: [
      { to: "/dashboard/deployments", label: "Deployments", icon: Server, testId: "sidebar-deployments" },
      { to: "/dashboard/builds", label: "Builds", icon: GitBranch, testId: "sidebar-builds" },
      { to: "/dashboard/audit", label: "Audit Log", icon: ScrollText, testId: "sidebar-audit" },
      { to: "/dashboard/proposals", label: "Proposals", icon: Vote, testId: "sidebar-proposals" },
    ],
  },
  {
    label: "Governance",
    links: [
      { to: "/dashboard/proof-of-work", label: "Proof of Work", icon: Award, testId: "sidebar-pow" },
      { to: "/dashboard/analytics", label: "Analytics", icon: LineChart, testId: "sidebar-analytics" },
      { to: "/dashboard/distillation", label: "Distillation", icon: Sparkles, testId: "sidebar-distillation" },
      { to: "/dashboard/cost", label: "Cost", icon: DollarSign, testId: "sidebar-cost" },
      { to: "/dashboard/secrets", label: "Secrets", icon: KeyRound, testId: "sidebar-secrets" },
    ],
  },
];

export default function DashboardLayout() {
  const [cycle, setCycle] = useState(null);
  const [sov, setSov] = useState(null);
  const { pathname } = useLocation();
  useEffect(() => {
    getCycleStatus().then(setCycle).catch(() => setCycle(null));
    getSovereignStatus().then(setSov).catch(() => setSov(null));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname]);

  return (
    <div className="flex min-h-screen" data-testid="dashboard-layout">
      <aside className="sticky top-0 hidden h-screen w-[252px] shrink-0 flex-col border-r border-line bg-bg-panel/60 backdrop-blur-md md:flex">
        <div className="border-b border-line px-5 py-5">
          <Link to="/" className="flex items-center gap-2 font-display text-base font-semibold" data-testid="dashboard-home-link">
            <Terminal className="h-5 w-5 text-ok" strokeWidth={2} />
            <span>PROFIT<span className="text-ok">ENGINE</span></span>
            <span className="ml-1 text-[10px] text-ink-faint">v5</span>
          </Link>
          <div className="mt-4 flex items-center gap-2 text-[10px] uppercase tracking-widest text-ink-muted">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-ok" />
            Command OS · online
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-5">
          {NAV_GROUPS.map((group) => (
            <div key={group.label}>
              <div className="px-3 mb-2 text-[10px] uppercase tracking-widest text-ink-faint">{group.label}</div>
              {group.links.map((n) => {
                const Icon = n.icon;
                return (
                  <NavLink
                    key={n.to}
                    to={n.to}
                    end={n.end}
                    data-testid={n.testId}
                    className={({ isActive }) =>
                      `side-link mb-1 ${isActive ? "active" : ""} ${n.sov ? "sov-link" : ""}`
                    }
                  >
                    <Icon className="h-4 w-4" strokeWidth={1.75} />
                    {n.label}
                  </NavLink>
                );
              })}
            </div>
          ))}
        </nav>

        <div className="border-t border-line p-4 space-y-2">
          {sov && (
            <div className="rounded-soft border border-sov/30 bg-sov/5 px-3 py-2 text-[11px]" data-testid="sov-status-pill">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-sov-soft">Sovereign</span>
                <span className="text-ink-muted">next in {sov.next_cycle_in_min}m</span>
              </div>
              <div className="mt-1 truncate text-ink-muted">{sov.current_objective}</div>
            </div>
          )}
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-[11px] text-ink-muted hover:text-ok"
            data-testid="dashboard-back-landing"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> back to launch
          </Link>
        </div>
      </aside>

      <main className="flex-1">
        <div className="sticky top-0 z-20 flex items-center justify-between border-b border-line bg-bg/85 px-6 py-3 backdrop-blur md:px-10">
          <div className="text-[11px] uppercase tracking-widest text-ink-muted">// command center</div>
          {cycle && (
            <div className="flex items-center gap-3 rounded-soft border border-line bg-bg-panel/50 px-3 py-1.5 text-[11px] text-ink-muted" data-testid="cycle-pill">
              <Activity className="h-3.5 w-3.5 text-ok" strokeWidth={1.75} />
              <span className="hidden sm:inline">cycle {cycle.state} ·</span>
              <span className="text-ok">{cycle.current_step}</span>
              <span className="text-ink-faint">step {cycle.step_index}/{cycle.step_total}</span>
              {cycle.approval_required && <span className="badge badge-warn">approval</span>}
            </div>
          )}
        </div>
        <Outlet />
      </main>
    </div>
  );
}
