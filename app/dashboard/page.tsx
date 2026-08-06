'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import ThemeToggle from '../components/ThemeToggle';
import styles from './dashboard.module.css';

interface Stream {
  name: string;
  status: string;
  health: number;
  revenue30d: number;
  today: number;
  trend: string;
}

interface Agent {
  id: string;
  label: string;
  status: string;
}

interface Activity {
  type: string;
  message: string;
  ago: string;
}

interface Data {
  todayProfit: number;
  ratePerHour: number;
  activeStreams: number;
  totalStreams: number;
  revenue30d: number;
  revenueMoM: number;
  content24h: number;
  aiOpsPerCycle: number;
  uptime: string;
  healthScore: number;
  tokensToday: number;
  dlqItems: number;
  engineRunning: boolean;
  publishedPosts?: number;
  lastPublished?: string;
  lastPublishedDate?: string;
  contentSite?: string;
  totalCycles?: number;
  successfulCycles?: number;
  avgDurationMs?: number;
  lastCycleIso?: string;
  memUsedPct?: number;
  tierDistribution?: Record<string, number>;
  streams: Stream[];
  agents: Agent[];
  activity: Activity[];
  pipeline: {
    trends: number;
    generate: number;
    seo: number;
    affiliate: number;
    publish: number;
    lcc: number;
  };
}

const DEFAULT_DATA: Data = {
  todayProfit: 33.09,
  ratePerHour: 120.95,
  activeStreams: 6,
  totalStreams: 6,
  revenue30d: 1451.16,
  revenueMoM: 23,
  content24h: 15,
  aiOpsPerCycle: 2196,
  uptime: '0h 39m',
  healthScore: 94,
  tokensToday: 284,
  dlqItems: 0,
  engineRunning: true,
  pipeline: { trends: 100, generate: 87, seo: 92, affiliate: 100, publish: 94, lcc: 100 },
  streams: [
    { name: 'AI Blog Network', status: 'running', health: 94, revenue30d: 260.1, today: 122.3, trend: 'up' },
    { name: 'Faceless Videos', status: 'running', health: 88, revenue30d: 204.78, today: 118.88, trend: 'up' },
    { name: 'Print-on-Demand A', status: 'running', health: 79, revenue30d: 185.69, today: 120.49, trend: 'up' },
    { name: 'Print-on-Demand B', status: 'running', health: 82, revenue30d: 185.8, today: 120.6, trend: 'down' },
    { name: 'Affiliate Links', status: 'running', health: 97, revenue30d: 332.97, today: 121.37, trend: 'up' },
    { name: 'Social Automation', status: 'running', health: 85, revenue30d: 168.63, today: 115.83, trend: 'up' },
    { name: 'SEO Content Farm', status: 'running', health: 91, revenue30d: 312.43, today: 123.13, trend: 'up' },
  ],
  agents: [
    { id: 'trendScanner', label: 'trendScanner', status: 'busy' },
    { id: 'contentGen', label: 'contentGen', status: 'idle' },
    { id: 'seoAgent', label: 'seoAgent', status: 'idle' },
    { id: 'affiliateLinker', label: 'affiliateLinker', status: 'busy' },
    { id: 'socialAgent', label: 'socialAgent', status: 'busy' },
    { id: 'earningsAgent', label: 'earningsAgent', status: 'busy' },
    { id: 'healthAgent', label: 'healthAgent', status: 'idle' },
    { id: 'podAgent', label: 'podAgent', status: 'busy' },
    { id: 'revenueAgent', label: 'revenueAgent', status: 'busy' },
    { id: 'websiteAgent', label: 'websiteAgent', status: 'idle' },
  ],
  activity: [
    { type: 'trends', message: 'Trend scan: 12 new niches found', ago: '48m ago' },
    { type: 'social', message: 'Reddit scheduled: r/passive_income', ago: '35m ago' },
    { type: 'merch', message: 'Printify order fulfilled: $18.40 margin', ago: '29m ago' },
    { type: 'lcc', message: 'LC&C: prompt seo_title rewritten (+8% CTR)', ago: '18m ago' },
    { type: 'blog', message: 'SEO article published: Dev.to + Hashnode', ago: '11m ago' },
  ],
};

const NAV = [
  { id: 'overview', label: 'Operations', abbr: 'OPS', group: 'Command' },
  { id: 'revenue', label: 'Revenue', abbr: 'REV', group: 'Command' },
  { id: 'streams', label: 'Streams', abbr: 'STR', group: 'Command' },
  { id: 'agents', label: 'Agent Fleet', abbr: 'FLT', group: 'Engine' },
  { id: 'pipeline', label: 'Pipeline', abbr: 'PLN', group: 'Engine' },
  { id: 'activity', label: 'Live Activity', abbr: 'LOG', group: 'Engine' },
  { id: 'advisor', label: 'AI Advisor', abbr: 'AI', group: 'Tools' },
  { id: 'system', label: 'System', abbr: 'SYS', group: 'Tools' },
] as const;

type SID = (typeof NAV)[number]['id'];

const TYPE_COLORS: Record<string, string> = {
  trends: '#00aaff',
  social: '#aa00ff',
  merch: '#ff6600',
  lcc: '#00ff88',
  blog: '#ffcc00',
  system: '#6f8299',
};

function useData() {
  const [data, setData] = useState<Data>(DEFAULT_DATA);
  const [connected, setConnected] = useState(false);
  const [ts, setTs] = useState<Date | null>(null);

  const go = useCallback(async () => {
    try {
      const r = await fetch('/api/data', { cache: 'no-store' });
      if (!r.ok) throw new Error(`status ${r.status}`);
      const j = (await r.json()) as Partial<Data>;
      if (j && !('error' in j)) {
        setData((prev) => ({
          ...prev,
          ...Object.fromEntries(Object.entries(j).filter(([, v]) => v != null)),
        }));
        setConnected(true);
      } else {
        setConnected(false);
      }
    } catch {
      setConnected(false);
    }
    setTs(new Date());
  }, []);

  useEffect(() => {
    go();

    if (typeof window === 'undefined' || !('EventSource' in window)) {
      const t = setInterval(() => {
        if (document.hidden) return;
        go();
      }, 8000);
      return () => clearInterval(t);
    }

    let es: EventSource | null = null;
    const connect = () => {
      if (es) return;
      es = new EventSource('/api/events');
      es.addEventListener('refresh', go);
    };
    const onVisibility = () => {
      if (document.hidden) {
        if (es) { es.close(); es = null; }
      } else {
        connect();
      }
    };
    connect();
    document.addEventListener('visibilitychange', onVisibility);
    return () => {
      if (es) es.close();
      document.removeEventListener('visibilitychange', onVisibility);
    };
  }, [go]);

  return { data, connected, ts };
}

interface CommandLogEntry {
  id: string;
  command: string;
  status: 'pending' | 'success' | 'error';
  message?: string;
  at: number;
}

const LOG_KEY = 'pe-command-log';

function useCommandLog() {
  const [log, setLog] = useState<CommandLogEntry[]>(() => {
    if (typeof window === 'undefined') return [];
    try {
      const raw = localStorage.getItem(LOG_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as CommandLogEntry[];
        if (Array.isArray(parsed)) return parsed.slice(-50);
      }
    } catch {}
    return [];
  });

  // Persist every change to localStorage without blocking render.
  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      localStorage.setItem(LOG_KEY, JSON.stringify(log.slice(-50)));
    } catch {}
  }, [log]);

  const add = useCallback((command: string) => {
    const entry: CommandLogEntry = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      command,
      status: 'pending',
      at: Date.now(),
    };
    setLog((prev) => [...prev, entry].slice(-50));
    return entry.id;
  }, []);

  const update = useCallback((id: string, status: CommandLogEntry['status'], message?: string) => {
    setLog((prev) => prev.map((e) => (e.id === id ? { ...e, status, message } : e)));
  }, []);

  const undo = useCallback((send: (cmd: string) => void) => {
    setLog((prev) => {
      const entry = [...prev].reverse().find((e) => e.status === 'success' || e.status === 'pending');
      if (!entry) return prev;
      const inverse: Record<string, string> = { 'Pause All': 'Resume All', 'Resume All': 'Pause All' };
      const cmd = inverse[entry.command];
      if (cmd) send(cmd);
      return prev;
    });
  }, []);

  const clear = useCallback(() => setLog([]), []);

  return { log, add, update, undo, clear };
}

function useCommand() {
  const [pending, setPending] = useState<string | null>(null);
  const [toast, setToast] = useState<{ message: string; tone: 'good' | 'bad' | 'neutral' } | null>(null);
  const { log, add, update, undo, clear } = useCommandLog();

  const send = useCallback(async (command: string) => {
    if (pending) return;
    setPending(command);
    const id = add(command);
    try {
      const r = await fetch('/api/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command }),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      update(id, 'success');
      setToast({ message: `${command}: acknowledged`, tone: 'good' });
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'network';
      update(id, 'error', msg);
      setToast({ message: `${command}: failed — ${msg}`, tone: 'bad' });
    } finally {
      setPending(null);
      setTimeout(() => setToast(null), 3000);
    }
  }, [pending, add, update]);

  const undoLast = useCallback(() => undo(send), [undo, send]);

  return { pending, send, toast, log, undo: undoLast, clearLog: clear };
}

function scoreColor(value: number): string {
  if (value >= 90) return '#00d084';
  if (value >= 75) return '#ffb020';
  return '#ff4d4d';
}

function stageState(value: number): string {
  if (value >= 95) return 'ARMED';
  if (value >= 80) return 'READY';
  return 'DEGRADED';
}

function cn(...parts: (string | false | undefined)[]) {
  return parts.filter(Boolean).join(' ');
}

function Kpi({ label, value, sub, accent = '#00d084' }: { label: string; value: string; sub?: string; accent?: string }) {
  return (
    <div className={styles.kpi} style={{ ['--accent' as string]: accent }}>
      <p className={styles.kpiLabel}>{label}</p>
      <p className={styles.kpiValue}>{value}</p>
      {sub && <p className={styles.kpiSub}>{sub}</p>}
    </div>
  );
}

function Progress({ label, value }: { label: string; value: number }) {
  const color = scoreColor(value);
  return (
    <div className={styles.barRow}>
      <span className={styles.barLabel}>{label}</span>
      <div className={styles.barTrack}>
        <div className={styles.barFill} style={{ width: `${value}%`, ['--c' as string]: color }} />
      </div>
      <span className={styles.barValue} style={{ ['--c' as string]: color }}>{value}%</span>
    </div>
  );
}

function HBar({ value }: { value: number }) {
  const color = scoreColor(value);
  return (
    <div className={styles.barRow}>
      <div className={styles.barTrack}>
        <div className={styles.barFill} style={{ width: `${value}%`, ['--c' as string]: color }} />
      </div>
      <span className={styles.barValue} style={{ ['--c' as string]: color }}>{value}%</span>
    </div>
  );
}

function StageCard({ label, value }: { label: string; value: number }) {
  const color = scoreColor(value);
  const state = stageState(value);
  return (
    <div className={styles.stageCard} style={{ ['--accent' as string]: color }}>
      <p className={styles.stageName}>{label}</p>
      <p className={styles.stageState}>{state}</p>
      <p className={styles.stageSub}>{value}%</p>
    </div>
  );
}

function Feed({ items }: { items: Activity[] }) {
  return (
    <div className={styles.feed}>
      {items.map((item, i) => {
        const color = TYPE_COLORS[item.type] ?? '#6f8299';
        return (
          <div key={i} className={styles.feedItem}>
            <span className={styles.badge} style={{ color, borderColor: `${color}55`, background: `${color}10` }}>
              {item.type}
            </span>
            <span className={styles.feedMsg}>{item.message}</span>
            <span className={styles.feedTime}>{item.ago}</span>
          </div>
        );
      })}
    </div>
  );
}

function Overview({ data, pending, send }: { data: Data; pending: string | null; send: (c: string) => void }) {
  const intent = data.engineRunning ? 'RUN AUTONOMOUS PROFIT CYCLE' : 'ALL OPERATIONS PAUSED';
  return (
    <div>
      <div className={styles.sectionHeader}>
        <h2 className={styles.sectionTitle}>Operations</h2>
        <span className={cn(styles.engineBadge, data.engineRunning ? styles.engineRunning : styles.enginePaused)}>
          {data.engineRunning ? '● ENGINE RUNNING' : '○ PAUSED'}
        </span>
      </div>

      <div className={styles.intentPanel}>
        <div>
          <p className={styles.intentLabel}>Declared Intent (VHLL)</p>
          <p className={styles.intentValue}>{intent}</p>
        </div>
        <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
          <p className={styles.intentLabel}>Health</p>
          <p className={styles.intentValue} style={{ color: scoreColor(data.healthScore) }}>{data.healthScore}/100</p>
        </div>
      </div>

      <div className={styles.grid3}>
        <Kpi label="Today Profit" value={`$${data.todayProfit.toFixed(2)}`} sub={`+$${data.ratePerHour}/hr`} accent="#00d084" />
        <Kpi label="Revenue 30D" value={`$${data.revenue30d.toFixed(2)}`} sub={`+${data.revenueMoM}% MoM`} accent="#5aa2ff" />
        <Kpi label="Streams" value={`${data.activeStreams}/${data.totalStreams}`} sub="all running" accent="#aa00ff" />
        <Kpi label="Content/24H" value={String(data.content24h)} sub="6 platforms" accent="#ff6600" />
        <Kpi label="AI Ops/Cycle" value={data.aiOpsPerCycle.toLocaleString()} sub="self-improving" accent="#ff0088" />
        <Kpi label="Uptime" value={data.uptime} sub={`health ${data.healthScore}/100`} accent="#00d0ff" />
      </div>

      <div className={styles.cmdBar}>
        {[
          { label: 'Run Cycle', tone: styles.cmdGreen },
          { label: 'Self-Improve', tone: styles.cmdBlue },
          { label: 'Pause All', tone: styles.cmdRed },
          { label: 'Resume All', tone: styles.cmdAmber },
        ].map((c) => (
          <button
            key={c.label}
            disabled={Boolean(pending)}
            className={cn(styles.cmdBtn, c.tone, pending === c.label ? styles.cmdPending : undefined)}
            onClick={() => send(c.label)}
          >
            {pending === c.label ? 'EXECUTING...' : c.label.toUpperCase()}
          </button>
        ))}
      </div>

      <div className={styles.panel}>
        <p className={styles.panelTitle}>Pipeline Readiness</p>
        <div className={styles.stageGrid}>
          <StageCard label="Trends" value={data.pipeline.trends} />
          <StageCard label="Generate" value={data.pipeline.generate} />
          <StageCard label="SEO/A-B" value={data.pipeline.seo} />
          <StageCard label="Affiliate" value={data.pipeline.affiliate} />
          <StageCard label="Publish" value={data.pipeline.publish} />
          <StageCard label="LC&C" value={data.pipeline.lcc} />
        </div>
      </div>

      <div className={styles.panel}>
        <p className={styles.panelTitle}>Live Activity</p>
        <Feed items={data.activity.slice(0, 8)} />
      </div>
    </div>
  );
}

function Revenue({ data }: { data: Data }) {
  const max = useMemo(() => Math.max(...data.streams.map((s) => s.revenue30d)), [data.streams]);
  return (
    <div>
      <div className={styles.sectionHeader}>
        <h2 className={styles.sectionTitle}>Revenue</h2>
      </div>
      <div className={styles.grid3}>
        <Kpi label="Total 30D" value={`$${data.revenue30d.toFixed(2)}`} sub={`+${data.revenueMoM}% MoM`} accent="#00d084" />
        <Kpi label="Today" value={`$${data.todayProfit.toFixed(2)}`} sub={`$${data.ratePerHour}/hr`} accent="#5aa2ff" />
        <Kpi label="Streams Active" value={`${data.activeStreams}/${data.totalStreams}`} sub="revenue-generating" accent="#aa00ff" />
      </div>
      <div className={styles.panel}>
        <p className={styles.panelTitle}>Revenue by Stream — 30 days</p>
        {data.streams.map((s) => (
          <div key={s.name} className={styles.barRow}>
            <span className={styles.barLabel} style={{ width: 150, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{s.name}</span>
            <div className={styles.barTrack}>
              <div className={styles.barFill} style={{ width: `${(s.revenue30d / max) * 100}%` }} />
            </div>
            <span className={cn(styles.barValue, s.trend === 'up' ? styles.trendUp : styles.trendDown)} style={{ width: 70 }}>
              ${s.revenue30d.toFixed(0)} {s.trend === 'up' ? '▲' : '▼'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function Streams({ data }: { data: Data }) {
  return (
    <div>
      <div className={styles.sectionHeader}>
        <h2 className={styles.sectionTitle}>Stream Health</h2>
      </div>
      <div className={styles.panel}>
        <table className={styles.dataTable}>
          <thead>
            <tr>
              {['Stream', 'Status', 'Health', '30d Rev', 'Today', 'Trend'].map((h) => (
                <th key={h}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.streams.map((s) => (
              <tr key={s.name}>
                <td>{s.name}</td>
                <td>
                  <span className={styles.badge} style={{ color: '#00d084', borderColor: '#00d08455', background: '#00d08410' }}>
                    {s.status}
                  </span>
                </td>
                <td style={{ minWidth: 140 }}><HBar value={s.health} /></td>
                <td className={styles.mono}>${s.revenue30d.toFixed(2)}</td>
                <td className={styles.mono} style={{ color: '#00d084' }}>+${s.today.toFixed(2)}</td>
                <td className={cn(s.trend === 'up' ? styles.trendUp : styles.trendDown)}>{s.trend === 'up' ? '▲' : '▼'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Agents({ data }: { data: Data }) {
  return (
    <div>
      <div className={styles.sectionHeader}>
        <h2 className={styles.sectionTitle}>Agent Fleet</h2>
      </div>
      <div className={styles.agentGrid}>
        {data.agents.map((a) => (
          <div key={a.id} className={cn(styles.agentCard, a.status === 'busy' ? styles.agentCardBusy : styles.agentCardIdle)}>
            <span className={cn(styles.led, a.status === 'busy' ? styles.ledBusy : styles.ledIdle)} aria-hidden="true" />
            <div>
              <p className={styles.agentName}>{a.label}</p>
              <p className={styles.agentStatus}>{a.status}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Pipeline({ data }: { data: Data }) {
  const tiers = data.tierDistribution ? Object.entries(data.tierDistribution) : [];
  return (
    <div>
      <div className={styles.sectionHeader}>
        <h2 className={styles.sectionTitle}>Pipeline</h2>
      </div>
      <div className={styles.stageGrid}>
        <StageCard label="Trends" value={data.pipeline.trends} />
        <StageCard label="Generate" value={data.pipeline.generate} />
        <StageCard label="SEO/A-B" value={data.pipeline.seo} />
        <StageCard label="Affiliate" value={data.pipeline.affiliate} />
        <StageCard label="Publish" value={data.pipeline.publish} />
        <StageCard label="LC&C" value={data.pipeline.lcc} />
      </div>
      <div className={styles.panel}>
        <p className={styles.panelTitle}>Stage Integrity</p>
        <Progress label="Trends" value={data.pipeline.trends} />
        <Progress label="Generate" value={data.pipeline.generate} />
        <Progress label="SEO/A-B" value={data.pipeline.seo} />
        <Progress label="Affiliate" value={data.pipeline.affiliate} />
        <Progress label="Publish" value={data.pipeline.publish} />
        <Progress label="LC&C" value={data.pipeline.lcc} />
      </div>
      {tiers.length > 0 && (
        <div className={styles.panel}>
          <p className={styles.panelTitle}>Tier Distribution</p>
          <div className={styles.grid3}>
            {tiers.map(([name, count]) => (
              <Kpi key={name} label={name} value={String(count)} accent="#5aa2ff" />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Activity({ data }: { data: Data }) {
  return (
    <div>
      <div className={styles.sectionHeader}>
        <h2 className={styles.sectionTitle}>Live Activity</h2>
      </div>
      <div className={styles.panel}>
        <Feed items={data.activity} />
      </div>
    </div>
  );
}

function Advisor() {
  const [msgs, setMsgs] = useState<{ role: 'user' | 'assistant'; text: string }[]>([
    { role: 'assistant', text: 'ProfitEngine v5.0 online. 10 agents, 6 streams, VHLL, LC&C active. Ask anything.' },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    ref.current?.scrollIntoView({ behavior: 'smooth' });
  }, [msgs]);

  const send = async () => {
    if (!input.trim() || loading) return;
    const msg = input.trim();
    setInput('');
    setLoading(true);
    setMsgs((m) => [...m, { role: 'user', text: msg }]);
    try {
      const r = await fetch('/api/advisor', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: msg }) });
      const d = (await r.json()) as { reply?: string };
      setMsgs((m) => [...m, { role: 'assistant', text: d.reply ?? 'No response.' }]);
    } catch {
      setMsgs((m) => [...m, { role: 'assistant', text: 'Error — check ANTHROPIC_API_KEY in Vercel env vars.' }]);
    }
    setLoading(false);
  };

  return (
    <div className={styles.advisor}>
      <div className={styles.sectionHeader}>
        <h2 className={styles.sectionTitle}>AI Advisor</h2>
        <span className={styles.muted}>claude-sonnet-4 · LC&C context</span>
      </div>
      <div className={styles.chat}>
        {msgs.map((m, i) => (
          <div key={i} className={styles.msg}>
            <span className={cn(styles.msgAvatar, m.role === 'assistant' ? styles.msgBot : styles.msgUser)}>{m.role === 'assistant' ? 'AI' : 'OP'}</span>
            <div className={styles.msgBody}>{m.text}</div>
          </div>
        ))}
        {loading && <p className={styles.muted} style={{ paddingLeft: 36 }}>Thinking...</p>}
        <div ref={ref} />
      </div>
      <div className={styles.inputRow}>
        <input
          className={styles.input}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
          placeholder="Enter a command or question..."
          aria-label="AI Advisor input"
        />
        <button className={styles.sendBtn} onClick={send} disabled={loading || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}

function CommandLogPanel({
  log,
  undo,
  clearLog,
}: {
  log: CommandLogEntry[];
  undo: () => void;
  clearLog: () => void;
}) {
  const statusColor = (s: CommandLogEntry['status']) =>
    s === 'success' ? 'var(--c2-green)' : s === 'error' ? 'var(--c2-red)' : 'var(--c2-amber)';

  return (
    <div className={styles.panel}>
      <div className={styles.sectionHeader}>
        <p className={styles.panelTitle}>Command Log</p>
        <div className={styles.cmdBar}>
          <button
            className={cn(styles.cmdBtn, styles.cmdAmber)}
            onClick={undo}
            disabled={log.length === 0}
          >
            Undo Last
          </button>
          <button
            className={cn(styles.cmdBtn, styles.cmdRed)}
            onClick={clearLog}
            disabled={log.length === 0}
          >
            Clear
          </button>
        </div>
      </div>
      {log.length === 0 ? (
        <p className={styles.muted}>No commands issued this session.</p>
      ) : (
        <div className={styles.feed}>
          {[...log].reverse().map((e) => (
            <div key={e.id} className={styles.feedItem}>
              <span className={styles.badge} style={{ color: statusColor(e.status), borderColor: statusColor(e.status) }}>
                {e.status}
              </span>
              <span className={styles.feedMsg}>{e.command}</span>
              <span className={styles.feedTime}>{new Date(e.at).toLocaleTimeString()}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function System({
  data,
  log,
  undo,
  clearLog,
}: {
  data: Data;
  log: CommandLogEntry[];
  undo: () => void;
  clearLog: () => void;
}) {
  return (
    <div>
      <div className={styles.sectionHeader}>
        <h2 className={styles.sectionTitle}>System</h2>
      </div>
      <div className={styles.grid3}>
        <Kpi label="Health Score" value={`${data.healthScore}/100`} accent={scoreColor(data.healthScore)} />
        <Kpi label="Uptime" value={data.uptime} accent="#5aa2ff" />
        <Kpi label="Tokens Today" value={`${data.tokensToday}K`} accent="#aa00ff" />
        <Kpi label="DLQ Items" value={String(data.dlqItems)} accent={data.dlqItems === 0 ? '#00d084' : '#ff4d4d'} />
        {data.publishedPosts != null && <Kpi label="Published Posts" value={String(data.publishedPosts)} sub={data.lastPublishedDate ?? ''} accent="#ff6600" />}
        {data.totalCycles != null && <Kpi label="Total Cycles" value={data.totalCycles.toLocaleString()} accent="#ffb020" />}
        {data.avgDurationMs != null && <Kpi label="Avg Duration" value={`${data.avgDurationMs}ms`} accent="#00d0ff" />}
        {data.memUsedPct != null && <Kpi label="RAM Usage" value={`${data.memUsedPct}%`} accent={data.memUsedPct > 85 ? '#ff4d4d' : '#5aa2ff'} />}
      </div>
      <CommandLogPanel log={log} undo={undo} clearLog={clearLog} />
      {data.contentSite && (
        <div className={styles.panel} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span className={styles.panelTitle} style={{ margin: 0 }}>Content Site</span>
          <a className={styles.link} href={data.contentSite} target="_blank" rel="noopener noreferrer">
            {data.contentSite.replace('https://', '')}
          </a>
        </div>
      )}
      {data.lastCycleIso && (
        <div className={styles.panel}>
          <p className={styles.panelTitle}>Last Cycle</p>
          <p className={styles.mono}>{data.lastCycleIso}</p>
        </div>
      )}
    </div>
  );
}

function useMobile() {
  const [mobile, setMobile] = useState(false);
  useEffect(() => {
    const update = () => setMobile(window.innerWidth <= 768);
    update();
    window.addEventListener('resize', update);
    return () => window.removeEventListener('resize', update);
  }, []);
  return mobile;
}

export default function Dashboard() {
  const [active, setActive] = useState<SID>('overview');
  const [open, setOpen] = useState(true);
  const mobile = useMobile();
  const { data, connected, ts } = useData();
  const { pending, send, toast, log, undo, clearLog } = useCommand();

  const groups = useMemo(() => [...new Set(NAV.map((n) => n.group))], []);

  useEffect(() => {
    if (mobile) setOpen(false);
  }, [mobile]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.altKey || e.ctrlKey || e.metaKey) return;
      const idx = Number(e.key) - 1;
      if (idx >= 0 && idx < NAV.length) {
        setActive(NAV[idx].id);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const closeOnMobile = useCallback((id: SID) => {
    setActive(id);
    if (mobile) setOpen(false);
  }, [mobile]);

  function Section() {
    if (active === 'overview') return <Overview data={data} pending={pending} send={send} />;
    if (active === 'revenue') return <Revenue data={data} />;
    if (active === 'streams') return <Streams data={data} />;
    if (active === 'agents') return <Agents data={data} />;
    if (active === 'pipeline') return <Pipeline data={data} />;
    if (active === 'activity') return <Activity data={data} />;
    if (active === 'advisor') return <Advisor />;
    if (active === 'system') return <System data={data} log={log} undo={undo} clearLog={clearLog} />;
    return null;
  }

  const sidebarClass = open ? styles.sidebarOpen : styles.sidebarClosed;

  return (
    <div className={styles.dashboard}>
      <aside className={cn(styles.sidebar, sidebarClass)}>
        <div className={styles.brand}>
          <div className={styles.brandMark}>PE</div>
          {open && (
            <div className={styles.brandText}>
              <p className={styles.brandTitle}>ProfitEngine</p>
              <p className={styles.brandSub}>v5.0 · LC&C ARMED</p>
            </div>
          )}
        </div>
        <nav className={styles.nav}>
          {groups.map((group) => (
            <div key={group}>
              {open && <p className={styles.groupLabel}>{group}</p>}
              {NAV.filter((n) => n.group === group).map((item) => {
                const isActive = active === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => closeOnMobile(item.id)}
                    title={item.label}
                    className={cn(styles.navItem, isActive ? styles.navItemActive : undefined)}
                  >
                    <span className={styles.navIcon}>{item.abbr}</span>
                    {open && <span>{item.label}</span>}
                  </button>
                );
              })}
            </div>
          ))}
        </nav>
        <button onClick={() => setOpen((o) => !o)} className={styles.collapseBtn} aria-label={open ? 'Collapse sidebar' : 'Expand sidebar'}>
          {open ? '◀' : '▶'}
        </button>
      </aside>

      {mobile && open && <div className={styles.overlay} onClick={() => setOpen(false)} aria-hidden="true" />}

      <div className={styles.main}>
        <header className={styles.header}>
          <div className={styles.headerLeft}>
            <button
              className={styles.menuToggle}
              onClick={() => setOpen((o) => !o)}
              aria-label="Toggle navigation"
              aria-expanded={open}
              type="button"
            >
              ☰
            </button>
            <span className={styles.classification}>UNCLASSIFIED // ASI · VHLL · LC&C ARMED</span>
            <span className={styles.profitReadout}>${data.todayProfit.toFixed(2)}</span>
            <span className={styles.readoutSub}>+${data.ratePerHour}/hr · {data.activeStreams} streams live</span>
          </div>
          <div className={styles.headerRight}>
            <ThemeToggle />
            <span className={styles.statusText}>
              <span className={cn(styles.statusDot, connected ? styles.statusDotLive : styles.statusDotDemo)} />
              {connected ? 'LIVE' : 'DEMO'}
            </span>
            <span className={styles.clock}>{ts ? ts.toLocaleTimeString() : '--:--:--'}</span>
          </div>
        </header>

        <main className={styles.content}>
          <Section />
        </main>
      </div>

      {toast && (
        <div
          className={styles.toast}
          style={{
            borderLeftColor: toast.tone === 'good' ? '#00d084' : toast.tone === 'bad' ? '#ff4d4d' : '#00d0ff',
          }}
        >
          {toast.message}
        </div>
      )}
    </div>
  );
}
