import Link from 'next/link';

type StatusItem = {
  label: string;
  state: 'pass' | 'blocked' | 'locked' | 'review';
  detail: string;
};

type StatusPageProps = {
  title: string;
  summary: string;
  items: readonly StatusItem[];
};

const labels = {
  pass: 'Pass',
  blocked: 'Blocked',
  locked: 'Locked',
  review: 'Review'
} as const;

export function StatusPage({ title, summary, items }: StatusPageProps) {
  return (
    <main className="shell">
      <Link className="badge" href="/">Command Center</Link>
      <h1>{title}</h1>
      <p className="muted">{summary}</p>
      <div className="status-list">
        {items.map((item) => (
          <section key={item.label} className={`status-card status-${item.state}`}>
            <div>
              <h2>{item.label}</h2>
              <p className="muted">{item.detail}</p>
            </div>
            <span>{labels[item.state]}</span>
          </section>
        ))}
      </div>
    </main>
  );
}
