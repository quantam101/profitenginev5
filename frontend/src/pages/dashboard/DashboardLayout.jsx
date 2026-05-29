import React, { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import {
  Terminal,
  LayoutDashboard,
  Cpu,
  ShieldAlert,
  BarChart3,
  FileText,
  ArrowLeft,
  Activity,
} from "lucide-react";
import { getCycleStatus } from "../../lib/api";

const NAV = [
  { to: "/dashboard", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/dashboard/agents", label: "Agents", icon: Cpu },
  { to: "/dashboard/approvals", label: "Approvals", icon: ShieldAlert },
  { to: "/dashboard/revenue", label: "Revenue", icon: BarChart3 },
  { to: "/dashboard/content", label: "Content", icon: FileText },
];

export default function DashboardLayout() {
  const [cycle, setCycle] = useState(null);
  const { pathname } = useLocation();
  useEffect(() => {
    getCycleStatus().then(setCycle).catch(() => setCycle(null));
  }, [pathname]);

  return (
    <div className="relative z-10 flex min-h-screen bg-bg" data-testid="dashboard-layout">
      <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-line bg-bg-surface md:flex">
        <div className="border-b border-line px-6 py-5">
          <Link to="/" className="flex items-center gap-2 font-display text-base" data-testid="dashboard-home-link">
            <Terminal className="h-4 w-4 text-acid" strokeWidth={1.5} />
            <span>PROFIT<span className="text-acid">ENGINE</span></span>
            <span className="ml-1 text-[10px] text-ink-faint">v5</span>
          </Link>
        </div>
        <nav className="flex-1 px-3 py-4">
          {NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.end}
              data-testid={`sidebar-${n.label.toLowerCase()}`}
              className={({ isActive }) =>
                `mb-1 flex items-center gap-3 border px-4 py-2.5 text-xs uppercase tracking-widest transition-colors ${
                  isActive
                    ? "border-acid bg-bg text-acid shadow-glowSm"
                    : "border-transparent text-ink-muted hover:border-line hover:text-ink"
                }`
              }
            >
              <n.icon className="h-4 w-4" strokeWidth={1.5} />
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-line px-5 py-4">
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-[11px] text-ink-muted transition-colors hover:text-acid"
            data-testid="dashboard-back-landing"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> back to launch
          </Link>
        </div>
      </aside>

      <main className="flex-1">
        <div className="sticky top-0 z-20 flex items-center justify-between border-b border-line bg-bg/95 px-6 py-3 backdrop-blur md:px-10">
          <div className="text-[11px] uppercase tracking-widest text-ink-muted">// command center</div>
          {cycle && (
            <div
              className="flex items-center gap-3 border border-line bg-bg-surface px-3 py-1.5 text-[11px] text-ink-muted"
              data-testid="cycle-pill"
            >
              <Activity className="h-3.5 w-3.5 text-acid" strokeWidth={1.75} />
              <span className="hidden sm:inline">cycle {cycle.state} ·</span>
              <span className="text-acid">{cycle.current_step}</span>
              <span className="text-ink-faint">
                step {cycle.step_index}/{cycle.step_total}
              </span>
              {cycle.approval_required && (
                <span className="border border-yellow-400 px-1.5 py-0.5 text-[10px] uppercase text-yellow-400">
                  approval
                </span>
              )}
            </div>
          )}
        </div>
        <Outlet />
      </main>
    </div>
  );
}
