'use client';
import { useState, useEffect, useCallback, useRef } from 'react';

interface Stream { name: string; status: string; health: number; revenue30d: number; today: number; trend: string; }
interface Agent { id: string; label: string; status: string; }
interface ActivityItem { type: string; message: string; ago: string; }
interface DashboardData {
  todayProfit: number; ratePerHour: number; activeStreams: number; totalStreams: number;
  revenue30d: number; revenueMoM: number; content24h: number; aiOpsPerCycle: number;
  uptime: string; healthScore: number; tokensToday: number; dlqItems: number;
  engineRunning: boolean; streams: Stream[]; agents: Agent[]; activity: ActivityItem[];
  pipeline: { trends: number; generate: number; seo: number; affiliate: number; publish: number; lcc: number; };
}
const MOCK: DashboardData = {
  todayProfit: 33.09, ratePerHour: 120.95, activeStreams: 6, totalStreams: 6,
  revenue30d: 1451.16, revenueMoM: 23, content24h: 15, aiOpsPerCycle: 2196,
  uptime: '0h 39m', healthScore: 94, tokensToday: 284, dlqItems: 0, engineRunning: true,
  pipeline: { trends: 100, generate: 87, seo: 92, affiliate: 100, publish: 94, lcc: 100 },
  streams: [
    { name: 'AI Blog Network',   status: 'running', health: 94, revenue30d: 260.10, today: 122.30, trend: 'up' },
    { name: 'Faceless Videos',   status: 'running', health: 88, revenue30d: 204.78, today: 118.88, trend: 'up' },
    { name: 'Print-on-Demand A', status: 'running', health: 79, revenue30d: 185.69, today: 120.49, trend: 'up' },
    { name: 'Print-on-Demand B', status: 'running', health: 82, revenue30d: 185.80, today: 120.60, trend: 'down' },
    { name: 'Affiliate Links',   status: 'running', health: 97, revenue30d: 332.97, today: 121.37, trend: 'up' },
    { name: 'Social Automation', status: 'running', health: 85, revenue30d: 168.63, today: 115.83, trend: 'up' },
    { name: 'SEO Content Farm',  status: 'running', health: 91, revenue30d: 312.43, today: 123.13, trend: 'up' },
  ],
  agents: [
    { id: 'trendScanner',    label: 'trendScanner',    status: 'busy' },
    { id: 'contentGen',      label: 'contentGen',      status: 'idle' },
    { id: 'seoAgent',        label: 'seoAgent',        status: 'idle' },
    { id: 'affiliateLinker', label: 'affiliateLinker', status: 'busy' },
    { id: 'socialAgent',     label: 'socialAgent',     status: 'busy' },
    { id: 'earningsAgent',   label: 'earningsAgent',   status: 'busy' },
    { id: 'healthAgent',     label: 'healthAgent',     status: 'idle' },
    { id: 'podAgent',        label: 'podAgent',        status: 'busy' },
    { id: 'revenueAgent',    label: 'revenueAgent',    status: 'busy' },
    { id: 'websiteAgent',    label: 'websiteAgent',    status: 'idle' },
  ],
  activity: [
    { type: 'trends', message: 'Trend scan: 12 new niches found',              ago: '48m ago' },
    { type: 'social', message: 'Reddit scheduled: r/passive_income',           ago: '35m ago' },
    { type: 'merch',  message: 'Printify order fulfilled: $18.40 margin',      ago: '29m ago' },
    { type: 'lcc',    message: 'LC&C: prompt seo_title rewritten (+8% CTR)',   ago: '18m ago' },
    { type: 'blog',   message: 'SEO article published: Dev.to + Hashnode',     ago: '11m ago' },
  ],
};
const NAV = [
  { id: 'overview',  label: 'Operations',   icon: '⚡', group: 'Core'   },
  { id: 'revenue',   label: 'Revenue',       icon: '💰', group: 'Core'   },
  { id: 'streams',   label: 'Streams',       icon: '📡', group: 'Core'   },
  { id: 'agents',    label: 'Agent Fleet',   icon: '🤖', group: 'Engine' },
  { id: 'pipeline',  label: 'Pipeline',      icon: '🔄', group: 'Engine' },
  { id: 'activity',  label: 'Live Activity', icon: '📊', group: 'Engine' },
  { id: 'advisor',   label: 'AI Advisor',    icon: '🧠', group: 'Tools'  },
  { id: 'system',    label: 'System',        icon: '🖥️',  group: 'Tools'  },
] as const;
type SectionId = typeof NAV[number]['id'];

function useDashboard() {
  const [data, setData] = useState<DashboardData>(MOCK);
  const [connected, setConnected] = useState(false);
  const [ts, setTs] = useState(new Date());
  const fetch_ = useCallback(async () => {
    try {
      const r = await fetch('/api/data', { cache: 'no-store' });
      if (!r.ok) throw new Error();
      setData(await r.json());
      setConnected(true);
    } catch { setConnected(false); }
    setTs(new Date());
  }, []);
  useEffect(() => { fetch_(); const t = setInterval(fetch_, 15000); return () => clearInterval(t); }, [fetch_]);
  return { data, connected, ts };
}
function StatCard({ label, value, sub, color = '#00ff88' }: { label: string; value: string; sub?: string; color?: string }) {
  return (
    <div style={{ background: '#111', border: '1px solid #222', borderRadius: 8, padding: '16px 18px', position: 'relative', overflow: 'hidden' }}>
      <div style={{ position: 'absolute', top: 0, left: 0, width: 3, height: '100%', background: color }} />
      <p style={{ color: '#666', fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase' as const, margin: 0, marginBottom: 6 }}>{label}</p>
      <p style={{ color: '#f0f0f0', fontSize: 22, fontWeight: 700, margin: 0, fontFamily: 'monospace' }}>{value}</p>
      {sub && <p style={{ color: '#555', fontSize: 12, margin: 0, marginTop: 4 }}>{sub}</p>}
    </div>
  );
}
function HealthBar({ value }: { value: number }) {
  const c = value >= 90 ? '#00ff88' : value >= 80 ? '#ffcc00' : '#ff4444';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{ flex: 1, height: 6, background: '#222', borderRadius: 3, overflow: 'hidden' }}>
        <div style={{ width: value + '%', height: '100%', background: c }} />
      </div>
      <span style={{ color: c, fontSize: 12, minWidth: 34, textAlign: 'right' as const, fontFamily: 'monospace' }}>{value}%</span>
    </div>
  );
}
function PipeBar({ label, value }: { label: string; value: number }) {
  const c = value >= 95 ? '#00ff88' : value >= 85 ? '#ffcc00' : '#ff4444';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
      <span style={{ color: '#888', fontSize: 12, width: 80, flexShrink: 0 }}>{label}</span>
      <div style={{ flex: 1, height: 8, background: '#1a1a1a', borderRadius: 4, overflow: 'hidden' }}>
        <div style={{ width: value + '%', height: '100%', background: c }} />
      </div>
      <span style={{ color: c, fontSize: 12, width: 38, textAlign: 'right' as const, fontFamily: 'monospace' }}>{value}%</span>
    </div>
  );
}
function Overview({ data }: { data: DashboardData }) {
  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <h2 style={{ color: '#f0f0f0', margin: 0, fontSize: 20, fontWeight: 600 }}>Operations Overview</h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: data.engineRunning ? '#00ff88' : '#ff4444', display: 'inline-block' }} />
          <span style={{ color: data.engineRunning ? '#00ff88' : '#ff4444', fontSize: 12, letterSpacing: '0.1em', fontFamily: 'monospace' }}>
            {data.engineRunning ? 'ENGINE RUNNING' : 'ENGINE PAUSED'}
          </span>
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(200px,1fr))', gap: 12, marginBottom: 24 }}>
        <StatCard label="Today's Profit"  value={'$' + data.todayProfit.toFixed(2)}   sub={'+$' + data.ratePerHour + '/hr'}          color="#00ff88" />
        <StatCard label="Revenue 30D"     value={'$' + data.revenue30d.toFixed(2)}    sub={'+' + data.revenueMoM + '% MoM'}          color="#00aaff" />
        <StatCard label="Active Streams"  value={data.activeStreams + '/' + data.totalStreams} sub="all running · 0 errors"          color="#aa00ff" />
        <StatCard label="Content / 24H"   value={String(data.content24h)}             sub="blogs + videos · 6 platforms"            color="#ff6600" />
        <StatCard label="AI Ops / Cycle"  value={data.aiOpsPerCycle.toLocaleString()} sub="continuously self-improving"             color="#ff0088" />
        <StatCard label="Uptime"          value={data.uptime}                         sub={'health score ' + data.healthScore + '/100'} color="#00ffcc" />
      </div>
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' as const }}>
        {['Run Cycle','Self-Improve','Pause All','Resume All'].map(label => (
          <button key={label}
            onClick={() => fetch('/api/command', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ command: label }) })}
            style={{ padding: '10px 20px', borderRadius: 6, border: label === 'Pause All' ? '1px solid #ff4444' : '1px solid #333', background: label === 'Pause All' ? '#ff444415' : '#1a1a1a', color: label === 'Pause All' ? '#ff4444' : '#ccc', cursor: 'pointer', fontSize: 13 }}>
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
function Revenue({ data }: { data: DashboardData }) {
  const max = Math.max(...data.streams.map(s => s.revenue30d));
  return (
    <div>
      <h2 style={{ color: '#f0f0f0', margin: '0 0 20px', fontSize: 20, fontWeight: 600 }}>Revenue</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(200px,1fr))', gap: 12, marginBottom: 24 }}>
        <StatCard label="Total 30D" value={'$' + data.revenue30d.toFixed(2)} sub={'+' + data.revenueMoM + '% vs last month'} color="#00ff88" />
        <StatCard label="Today"     value={'$' + data.todayProfit.toFixed(2)} sub={'$' + data.ratePerHour + '/hr run rate'}  color="#00aaff" />
      </div>
      <div style={{ background: '#111', border: '1px solid #1e1e1e', borderRadius: 10, padding: 20 }}>
        <p style={{ color: '#555', fontSize: 12, margin: '0 0 16px', textTransform: 'uppercase' as const, letterSpacing: '0.08em' }}>Revenue by Stream — 30 days</p>
        {data.streams.map(s => (
          <div key={s.name} style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
            <span style={{ color: '#888', fontSize: 12, width: 160, flexShrink: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' as const }}>{s.name}</span>
            <div style={{ flex: 1, height: 10, background: '#1a1a1a', borderRadius: 5, overflow: 'hidden' }}>
              <div style={{ width: ((s.revenue30d / max) * 100) + '%', height: '100%', background: 'linear-gradient(90deg,#00ff88,#00aaff)' }} />
            </div>
            <span style={{ color: '#ccc', fontSize: 13, width: 60, textAlign: 'right' as const, fontFamily: 'monospace' }}>${s.revenue30d.toFixed(0)}</span>
            <span style={{ color: s.trend === 'up' ? '#00ff88' : '#ff4444', width: 14 }}>{s.trend === 'up' ? '▲' : '▼'}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
function Streams({ data }: { data: DashboardData }) {
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h2 style={{ color: '#f0f0f0', margin: 0, fontSize: 20, fontWeight: 600 }}>Stream Health</h2>
        <button style={{ padding: '8px 16px', borderRadius: 6, border: '1px solid #00ff88', background: '#00ff8810', color: '#00ff88', cursor: 'pointer', fontSize: 12 }}>+ Add Stream</button>
      </div>
      <div style={{ background: '#111', border: '1px solid #1e1e1e', borderRadius: 10, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' as const }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #1e1e1e' }}>
              {['Stream','Status','Health','30d Revenue','Today','Trend'].map(h => (
                <th key={h} style={{ color: '#555', fontSize: 11, fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase' as const, padding: '12px 16px', textAlign: 'left' as const }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.streams.map((s, i) => (
              <tr key={s.name} style={{ borderBottom: i < data.streams.length - 1 ? '1px solid #151515' : 'none' }}>
                <td style={{ color: '#ccc', fontSize: 13, padding: '12px 16px' }}>{s.name}</td>
                <td style={{ padding: '12px 16px' }}>
                  <span style={{ padding: '3px 10px', borderRadius: 20, fontSize: 11, background: s.status === 'running' ? '#00ff8815' : '#ff444415', color: s.status === 'running' ? '#00ff88' : '#ff4444', border: '1px solid ' + (s.status === 'running' ? '#00ff8840' : '#ff444440') }}>{s.status}</span>
                </td>
                <td style={{ padding: '12px 16px', minWidth: 140 }}><HealthBar value={s.health} /></td>
                <td style={{ color: '#ccc', fontSize: 13, padding: '12px 16px', fontFamily: 'monospace' }}>${s.revenue30d.toFixed(2)}</td>
                <td style={{ color: '#00ff88', fontSize: 13, padding: '12px 16px', fontFamily: 'monospace' }}>+${s.today.toFixed(2)}</td>
                <td style={{ color: s.trend === 'up' ? '#00ff88' : '#ff4444', fontSize: 16, padding: '12px 16px' }}>{s.trend === 'up' ? '▲' : '▼'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
function Agents({ data }: { data: DashboardData }) {
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h2 style={{ color: '#f0f0f0', margin: 0, fontSize: 20, fontWeight: 600 }}>Agent Fleet</h2>
        <span style={{ color: '#555', fontSize: 12 }}>{data.agents.length} agents · LC&C monitoring · circuit breakers OK</span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(200px,1fr))', gap: 10 }}>
        {data.agents.map(a => (
          <div key={a.id} style={{ display: 'flex', alignItems: 'center', gap: 12, background: '#111', border: '1px solid #1e1e1e', borderRadius: 8, padding: '12px 16px' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', flexShrink: 0, background: a.status === 'busy' ? '#00ff88' : a.status === 'error' ? '#ff4444' : '#333', boxShadow: a.status === 'busy' ? '0 0 8px #00ff8880' : 'none' }} />
            <div>
              <p style={{ color: '#ccc', fontSize: 13, margin: 0 }}>{a.label}</p>
              <p style={{ color: a.status === 'busy' ? '#00ff88' : '#555', fontSize: 11, margin: 0 }}>● {a.status}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
function Pipeline({ data }: { data: DashboardData }) {
  const cards = [
    { label: 'RAM Cache (L1)',    val: 'LIVE',   sub: '~40% token save', color: '#00ff88' },
    { label: 'Disk Cache (L2)',   val: 'LIVE',   sub: 'persistent',      color: '#00ff88' },
    { label: 'UCB1 Bandit',       val: 'ARMED',  sub: 'auto-select',     color: '#ffcc00' },
    { label: 'Dead-letter Queue', val: data.dlqItems === 0 ? 'EMPTY' : String(data.dlqItems), sub: data.dlqItems + ' items', color: '#00aaff' },
    { label: 'LC&C VHLL Guard',   val: 'ACTIVE', sub: '30min interval',  color: '#00ff88' },
  ];
  return (
    <div>
      <h2 style={{ color: '#f0f0f0', margin: '0 0 20px', fontSize: 20, fontWeight: 600 }}>VHLL / XAF Pipeline</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(160px,1fr))', gap: 12, marginBottom: 24 }}>
        {cards.map(c => (
          <div key={c.label} style={{ background: '#111', border: '1px solid #1e1e1e', borderRadius: 8, padding: '14px 16px' }}>
            <p style={{ color: '#555', fontSize: 11, margin: '0 0 6px', textTransform: 'uppercase' as const, letterSpacing: '0.07em' }}>{c.label}</p>
            <p style={{ color: c.color, fontSize: 15, fontWeight: 700, margin: '0 0 4px', fontFamily: 'monospace' }}>{c.val}</p>
            <p style={{ color: '#444', fontSize: 11, margin: 0 }}>{c.sub}</p>
          </div>
        ))}
      </div>
      <div style={{ background: '#111', border: '1px solid #1e1e1e', borderRadius: 10, padding: 20 }}>
        <p style={{ color: '#555', fontSize: 11, margin: '0 0 16px', textTransform: 'uppercase' as const, letterSpacing: '0.08em' }}>Pipeline Stages</p>
        <PipeBar label="Trends"    value={data.pipeline.trends}    />
        <PipeBar label="Generate"  value={data.pipeline.generate}  />
        <PipeBar label="SEO / A-B" value={data.pipeline.seo}       />
        <PipeBar label="Affiliate" value={data.pipeline.affiliate}  />
        <PipeBar label="Publish"   value={data.pipeline.publish}    />
        <PipeBar label="LC&C"      value={data.pipeline.lcc}        />
      </div>
    </div>
  );
}
function Activity({ data }: { data: DashboardData }) {
  const tc: Record<string,string> = { trends: '#00aaff', social: '#aa00ff', merch: '#ff6600', lcc: '#00ff88', blog: '#ffcc00', system: '#888' };
  return (
    <div>
      <h2 style={{ color: '#f0f0f0', margin: '0 0 20px', fontSize: 20, fontWeight: 600 }}>Live Activity</h2>
      <div style={{ background: '#111', border: '1px solid #1e1e1e', borderRadius: 10, overflow: 'hidden' }}>
        {data.activity.map((item, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '14px 20px', borderBottom: i < data.activity.length - 1 ? '1px solid #151515' : 'none' }}>
            <span style={{ padding: '3px 10px', borderRadius: 20, fontSize: 11, background: (tc[item.type] ?? '#888') + '20', color: tc[item.type] ?? '#888', border: '1px solid ' + (tc[item.type] ?? '#888') + '40', flexShrink: 0 }}>{item.type}</span>
            <span style={{ color: '#ccc', fontSize: 13, flex: 1 }}>{item.message}</span>
            <span style={{ color: '#444', fontSize: 12, flexShrink: 0, fontFamily: 'monospace' }}>{item.ago}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
function Advisor() {
  const [messages, setMessages] = useState([{ role: 'assistant' as const, text: 'ProfitEngine v5.0 online. I have full telemetry — 10 agents, 6 streams, VHLL, LC&C 4-loop status, revenue. Ask anything.' }]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);
  const send = async () => {
    if (!input.trim() || loading) return;
    const msg = input.trim(); setInput(''); setLoading(true);
    setMessages(m => [...m, { role: 'user', text: msg }]);
    try {
      const r = await fetch('/api/advisor', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: msg }) });
      const d = await r.json();
      setMessages(m => [...m, { role: 'assistant', text: d.reply ?? 'No response.' }]);
    } catch { setMessages(m => [...m, { role: 'assistant', text: 'Connection error.' }]); }
    setLoading(false);
  };
  return (
    <div style={{ display: 'flex', flexDirection: 'column' as const, height: '100%' }}>
      <h2 style={{ color: '#f0f0f0', margin: '0 0 8px', fontSize: 20, fontWeight: 600 }}>AI Operations Advisor</h2>
      <p style={{ color: '#555', fontSize: 12, margin: '0 0 20px' }}>claude-sonnet-4 · Lifelong Catch & Correct · full v5.0 context</p>
      <div style={{ flex: 1, overflowY: 'auto' as const, background: '#0d0d0d', borderRadius: 10, border: '1px solid #1e1e1e', padding: 16, display: 'flex', flexDirection: 'column' as const, gap: 12, minHeight: 300 }}>
        {messages.map((m, i) => (
          <div key={i} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
            <span style={{ width: 28, height: 28, borderRadius: '50%', background: m.role === 'assistant' ? '#00ff8820' : '#00aaff20', border: '1px solid ' + (m.role === 'assistant' ? '#00ff8840' : '#00aaff40'), display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, flexShrink: 0, marginTop: 2 }}>
              {m.role === 'assistant' ? '🧠' : '👤'}
            </span>
            <p style={{ color: m.role === 'assistant' ? '#c0c0c0' : '#e0e0e0', fontSize: 13, margin: 0, lineHeight: 1.6, background: m.role === 'assistant' ? '#111' : '#1a1a2a', padding: '10px 14px', borderRadius: 8, flex: 1 }}>{m.text}</p>
          </div>
        ))}
        {loading && <p style={{ color: '#555', fontSize: 13, margin: 0, paddingLeft: 38 }}>Thinking…</p>}
        <div ref={bottomRef} />
      </div>
      <div style={{ display: 'flex', gap: 10, marginTop: 12 }}>
        <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && send()}
          placeholder="Ask about streams, agents, revenue…" disabled={loading}
          style={{ flex: 1, background: '#111', border: '1px solid #222', borderRadius: 8, padding: '10px 14px', color: '#e0e0e0', fontSize: 13, outline: 'none' }} />
        <button onClick={send} disabled={loading || !input.trim()}
          style={{ padding: '10px 20px', borderRadius: 8, background: '#00ff8820', border: '1px solid #00ff8840', color: '#00ff88', cursor: 'pointer', fontSize: 13, fontWeight: 600 }}>
          Send
        </button>
      </div>
    </div>
  );
}
function System({ data }: { data: DashboardData }) {
  return (
    <div>
      <h2 style={{ color: '#f0f0f0', margin: '0 0 20px', fontSize: 20, fontWeight: 600 }}>System Metrics</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(200px,1fr))', gap: 12 }}>
        <StatCard label="Health Score" value={data.healthScore + '/100'} color="#00ff88" />
        <StatCard label="Uptime"       value={data.uptime}               color="#00aaff" />
        <StatCard label="Tokens Today" value={data.tokensToday + 'K'}   color="#aa00ff" />
        <StatCard label="DLQ Items"    value={String(data.dlqItems)}     color={data.dlqItems === 0 ? '#00ff88' : '#ff4444'} />
      </div>
    </div>
  );
}
export default function DashboardPage() {
  const [active, setActive] = useState<SectionId>('overview');
  const [open, setOpen] = useState(true);
  const { data, connected, ts } = useDashboard();
  const groups = [...new Set(NAV.map(n => n.group))];
  const renderSection = () => {
    switch (active) {
      case 'overview':  return <Overview  data={data} />;
      case 'revenue':   return <Revenue   data={data} />;
      case 'streams':   return <Streams   data={data} />;
      case 'agents':    return <Agents    data={data} />;
      case 'pipeline':  return <Pipeline  data={data} />;
      case 'activity':  return <Activity  data={data} />;
      case 'advisor':   return <Advisor />;
      case 'system':    return <System    data={data} />;
    }
  };
  return (
    <>
      <style>{`*{box-sizing:border-box}body{margin:0;background:#0a0a0a;color:#e0e0e0;font-family:-apple-system,sans-serif}::-webkit-scrollbar{width:6px}::-webkit-scrollbar-track{background:#111}::-webkit-scrollbar-thumb{background:#2a2a2a;border-radius:3px}`}</style>
      <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
        <aside style={{ width: open ? 220 : 60, flexShrink: 0, background: '#0d0d0d', borderRight: '1px solid #1a1a1a', display: 'flex', flexDirection: 'column' as const, transition: 'width 0.25s ease', overflow: 'hidden' }}>
          <div style={{ padding: '18px 16px', borderBottom: '1px solid #1a1a1a', display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ width: 28, height: 28, borderRadius: 6, background: 'linear-gradient(135deg,#00ff88,#00aaff)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, flexShrink: 0 }}>⚡</span>
            {open && <div><p style={{ color: '#f0f0f0', fontSize: 13, fontWeight: 700, margin: 0, whiteSpace: 'nowrap' as const }}>ProfitEngine</p><p style={{ color: '#555', fontSize: 10, margin: 0, whiteSpace: 'nowrap' as const }}>v5.0 · LC&C ARMED</p></div>}
          </div>
          <nav style={{ flex: 1, overflowY: 'auto' as const, padding: '10px 0' }}>
            {groups.map(group => (
              <div key={group}>
                {open && <p style={{ color: '#333', fontSize: 10, fontWeight: 600, letterSpacing: '0.12em', textTransform: 'uppercase' as const, margin: '14px 16px 6px' }}>{group}</p>}
                {NAV.filter(n => n.group === group).map(item => (
                  <button key={item.id} onClick={() => setActive(item.id)} title={item.label}
                    style={{ display: 'flex', alignItems: 'center', gap: 10, width: '100%', padding: '9px 16px', background: active === item.id ? '#00ff8812' : 'transparent', border: 'none', borderLeft: '2px solid ' + (active === item.id ? '#00ff88' : 'transparent'), color: active === item.id ? '#00ff88' : '#888', cursor: 'pointer', textAlign: 'left' as const, whiteSpace: 'nowrap' as const }}>
                    <span style={{ fontSize: 16, flexShrink: 0 }}>{item.icon}</span>
                    {open && <span style={{ fontSize: 13, fontWeight: active === item.id ? 600 : 400 }}>{item.label}</span>}
                  </button>
                ))}
              </div>
            ))}
          </nav>
          <button onClick={() => setOpen(o => !o)} style={{ margin: 12, padding: 8, borderRadius: 6, background: '#1a1a1a', border: '1px solid #222', color: '#555', cursor: 'pointer', fontSize: 14 }}>
            {open ? '←' : '→'}
          </button>
        </aside>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' as const, overflow: 'hidden' }}>
          <header style={{ padding: '14px 24px', borderBottom: '1px solid #1a1a1a', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <span style={{ color: '#00ff88', fontSize: 22, fontWeight: 700, fontFamily: 'monospace' }}>${data.todayProfit.toFixed(2)}</span>
              <span style={{ color: '#555', fontSize: 12 }}>+${data.ratePerHour}/hr · {data.activeStreams} streams live</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <span style={{ color: connected ? '#00ff88' : '#ff6600', fontSize: 11, fontFamily: 'monospace' }}>{connected ? '● LIVE' : '◌ DEMO'}</span>
              <span style={{ color: '#333', fontSize: 11, fontFamily: 'monospace' }}>{ts.toLocaleTimeString()}</span>
            </div>
          </header>
          <main style={{ flex: 1, overflowY: 'auto' as const, padding: 24 }}>{renderSection()}</main>
        </div>
      </div>
    </>
  );
}
