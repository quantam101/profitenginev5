'use client';

import { FormEvent, useMemo, useState } from 'react';

type WorkType = 'Trailer' | 'Courier' | 'Field Tech' | 'Low Voltage' | 'IT Support' | 'Follow Up';
type Status = 'New' | 'Applied' | 'Call Today' | 'Waiting' | 'Booked' | 'Rejected';
type ApprovalStatus = 'Pending' | 'Approved' | 'Blocked';

type Lead = {
  id: string;
  title: string;
  source: string;
  type: WorkType;
  location: string;
  pay: number;
  miles: number;
  urgency: number;
  fit: number;
  probability: number;
  nextAction: string;
  url: string;
  status: Status;
};

type Approval = {
  id: string;
  action: string;
  item: string;
  risk: string;
  status: ApprovalStatus;
};

const seedLeads: Lead[] = [
  {
    id: 'source-support-hpe',
    title: 'Source Support — HPE CyrusOne confirmed FE assignment',
    source: 'Gmail',
    type: 'Field Tech',
    location: 'Chandler, AZ',
    pay: 130,
    miles: 28,
    urgency: 10,
    fit: 10,
    probability: 10,
    nextAction: 'Call Source Support and ask for same-week overflow work before the June 9 assignment.',
    url: 'https://mail.google.com/mail/#all/19e8a183ca777fc1',
    status: 'Booked',
  },
  {
    id: 'ameriship-scottsdale',
    title: 'Ameriship Parcel Delivery — Courier / Independent Contractor',
    source: 'Monster',
    type: 'Courier',
    location: 'Scottsdale / Phoenix',
    pay: 900,
    miles: 35,
    urgency: 9,
    fit: 8,
    probability: 6,
    nextAction: 'Apply and position Already Here LLC as a reliable medical and business courier.',
    url: 'https://www.monster.com/job-openings/courier-independent-contractor-scottsdale-az--2e3f8539-e8e1-4d45-a23c-1ba6ea37cf90',
    status: 'New',
  },
  {
    id: 'rocky-labs-tempe',
    title: 'Rocky Mountain Laboratories — Medical Courier Driver Evening 1099',
    source: 'Direct Apply',
    type: 'Courier',
    location: 'Tempe / Phoenix',
    pay: 22,
    miles: 25,
    urgency: 8,
    fit: 7,
    probability: 7,
    nextAction: 'Apply for emergency coverage and ask if routes can be stacked around Source Support work.',
    url: 'https://rockylabs.applytojob.com/apply/XCUTOvoIk8/Medical-Courier-Driver-Evening-1099',
    status: 'New',
  },
  {
    id: 'rapid-chandler-phx',
    title: 'Rapid Medical — Chandler to Phoenix route',
    source: 'ZipRecruiter',
    type: 'Courier',
    location: 'Chandler / Phoenix',
    pay: 110,
    miles: 103,
    urgency: 8,
    fit: 7,
    probability: 6,
    nextAction: 'Apply only if the route does not block higher-paying IT work.',
    url: 'https://www.ziprecruiter.com/c/Rapid-Medical/Job/Chandler-to-Phoenix-103-miles-(-5:00-PM-start,-M-F)/-in-Chandler,AZ?jid=9521d78fb4f2734f',
    status: 'New',
  },
  {
    id: 'trailer-craigslist',
    title: '16 ft trailer same-day hauling post',
    source: 'Owned Offer',
    type: 'Trailer',
    location: 'Phoenix metro',
    pay: 150,
    miles: 20,
    urgency: 10,
    fit: 9,
    probability: 8,
    nextAction: 'Post approved copy and require deposit before dispatch.',
    url: 'https://post.craigslist.org/c/phx',
    status: 'Call Today',
  },
];

const seedApprovals: Approval[] = [
  { id: 'post-trailer-ad', action: 'Post Ad', item: '16 ft trailer hauling ad', risk: 'Craigslist final submit/payment must stay human-approved.', status: 'Pending' },
  { id: 'apply-ameriship', action: 'Apply', item: 'Ameriship courier contractor route', risk: 'Confirm insurance, miles, schedule, and net pay before accepting.', status: 'Pending' },
  { id: 'call-source-support', action: 'Call', item: 'Source Support overflow work', risk: 'Low risk. High-fit client channel.', status: 'Pending' },
];

const craigslistCopy = `16 FT TRAILER AVAILABLE TODAY — PICKUP / DELIVERY / JUNK / SMALL MOVES\n\n16 ft trailer available for same-day local hauling in the Phoenix metro area.\n\nServices:\n- Furniture pickup and delivery\n- Appliance pickup\n- Small moves\n- Garage cleanouts\n- Junk hauling\n- Marketplace pickup/delivery\n- Contractor material runs\n- Home Depot / Lowe's / Costco pickup\n- Light commercial delivery\n- IT equipment pickup/delivery\n- Office cleanout support\n- Printer / POS / network equipment transport\n\nService area:\nPhoenix, Glendale, Peoria, Tempe, Mesa, Chandler, Scottsdale, Avondale, Goodyear, and nearby areas.\n\nRates:\n- Local minimum: $85\n- Small local pickup/delivery: $85–$125\n- Medium load: $150–$250\n- Junk/removal: priced by load + dump fees\n- Contractor/material runs: flat rate quoted before dispatch\n- Deposit required before dispatch\n\nText/call with pickup address, drop-off address, photo of items, desired time, and stairs/no stairs.\n\nReliable, professional, veteran-owned business.\nAlready Here LLC\nPhone: 619-884-9241\nEmail: alreadyherellc@gmail.com\nWebsite: alreadyherellc.com\n\nNo hazardous materials. No illegal dumping.`;

const sourceSupportScript = `Hi, this is Stephen Franklin. I confirmed the HPE / CyrusOne Source Support assignment for June 9 at 6 PM. I am also available this week for Phoenix, Chandler, Tempe, Mesa, Scottsdale, Glendale, and surrounding-area overflow work. I can cover smart hands, HPE/server support, network troubleshooting, rack/stack, cabling, AP/POS support, printer support, onsite verification, and urgent dispatch. Do you have any same-week or next-day work I can pick up before the June 9 assignment?`;

function scoreLead(lead: Lead): number {
  const estimatedNet = lead.type === 'Courier' || lead.type === 'Trailer' ? Math.max(lead.pay - lead.miles * 0.72, 0) : lead.pay;
  const payScore = Math.min(estimatedNet / 25, 10);
  const distancePenalty = Math.min(lead.miles / 35, 4);
  return Math.round((payScore * 2.4 + lead.urgency * 2.2 + lead.fit * 2.1 + lead.probability * 2.1 - distancePenalty) * 10) / 10;
}

export default function CashDeskClient() {
  const [leads, setLeads] = useState<Lead[]>(seedLeads);
  const [approvals, setApprovals] = useState<Approval[]>(seedApprovals);
  const [form, setForm] = useState({ title: '', source: '', type: 'Trailer' as WorkType, location: '', pay: '150', miles: '20', url: '', nextAction: '' });

  const ranked = useMemo(() => [...leads].sort((a, b) => scoreLead(b) - scoreLead(a)), [leads]);
  const booked = leads.filter((lead) => lead.status === 'Booked').length;
  const pipeline = leads.reduce((sum, lead) => sum + lead.pay, 0);
  const topScore = ranked[0] ? scoreLead(ranked[0]) : 0;

  function updateStatus(id: string, status: Status) {
    setLeads((items) => items.map((lead) => (lead.id === id ? { ...lead, status } : lead)));
  }

  function updateApproval(id: string, status: ApprovalStatus) {
    setApprovals((items) => items.map((item) => (item.id === id ? { ...item, status } : item)));
  }

  function addLead(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const lead: Lead = {
      id: `lead-${Date.now()}`,
      title: form.title.trim(),
      source: form.source.trim() || 'Manual',
      type: form.type,
      location: form.location.trim() || 'Phoenix metro',
      pay: Number(form.pay) || 0,
      miles: Number(form.miles) || 0,
      urgency: 8,
      fit: 8,
      probability: 6,
      nextAction: form.nextAction.trim() || 'Call/apply and confirm pay, date, requirements, and net profit before accepting.',
      url: form.url.trim(),
      status: 'New',
    };
    if (!lead.title) return;
    setLeads((items) => [lead, ...items]);
    setForm({ title: '', source: '', type: 'Trailer', location: '', pay: '150', miles: '20', url: '', nextAction: '' });
  }

  return (
    <section className="cd-shell">
      <header className="cd-hero">
        <span className="cd-kicker">Already Here LLC AI VP</span>
        <h1>Cash Desk Command Center</h1>
        <p>Find money, score the opportunity, prepare the action, require approval, and keep Stephen on the highest-probability paid work.</p>
      </header>

      <div className="cd-metrics" aria-label="Cash desk metrics">
        <article><span>Top score</span><strong>{topScore}</strong></article>
        <article><span>Pipeline</span><strong>${pipeline.toLocaleString()}</strong></article>
        <article><span>Booked</span><strong>{booked}</strong></article>
        <article><span>Pending approvals</span><strong>{approvals.filter((a) => a.status === 'Pending').length}</strong></article>
      </div>

      <div className="cd-grid two">
        <section className="cd-card">
          <h2>Today's ranked work</h2>
          <div className="cd-list">
            {ranked.map((lead) => (
              <article key={lead.id} className="cd-lead">
                <div>
                  <span className="cd-pill">{lead.type}</span>
                  <h3>{lead.title}</h3>
                  <p>{lead.location} · {lead.source} · score {scoreLead(lead)}</p>
                  <p className="cd-action">{lead.nextAction}</p>
                </div>
                <div className="cd-side">
                  <strong>${lead.pay.toLocaleString()}</strong>
                  <small>{lead.miles} miles</small>
                  <select value={lead.status} onChange={(event) => updateStatus(lead.id, event.target.value as Status)} aria-label={`Update ${lead.title} status`}>
                    {['New', 'Applied', 'Call Today', 'Waiting', 'Booked', 'Rejected'].map((status) => <option key={status}>{status}</option>)}
                  </select>
                  {lead.url && <a href={lead.url} target="_blank" rel="noreferrer">Open</a>}
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="cd-card">
          <h2>Add lead</h2>
          <form className="cd-form" onSubmit={addLead}>
            <label>Title<input value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} /></label>
            <label>Source<input value={form.source} onChange={(event) => setForm({ ...form, source: event.target.value })} /></label>
            <label>Type<select value={form.type} onChange={(event) => setForm({ ...form, type: event.target.value as WorkType })}>{['Trailer', 'Courier', 'Field Tech', 'Low Voltage', 'IT Support', 'Follow Up'].map((type) => <option key={type}>{type}</option>)}</select></label>
            <label>Location<input value={form.location} onChange={(event) => setForm({ ...form, location: event.target.value })} /></label>
            <label>Pay<input type="number" value={form.pay} onChange={(event) => setForm({ ...form, pay: event.target.value })} /></label>
            <label>Miles<input type="number" value={form.miles} onChange={(event) => setForm({ ...form, miles: event.target.value })} /></label>
            <label>URL<input value={form.url} onChange={(event) => setForm({ ...form, url: event.target.value })} /></label>
            <label>Next action<textarea value={form.nextAction} onChange={(event) => setForm({ ...form, nextAction: event.target.value })} /></label>
            <button type="submit">Add to cash desk</button>
          </form>
        </section>
      </div>

      <div className="cd-grid two">
        <section className="cd-card">
          <h2>Approval queue</h2>
          {approvals.map((item) => (
            <article key={item.id} className="cd-approval">
              <h3>{item.action}: {item.item}</h3>
              <p>{item.risk}</p>
              <div>
                <button onClick={() => updateApproval(item.id, 'Approved')}>Approve</button>
                <button onClick={() => updateApproval(item.id, 'Blocked')}>Block</button>
                <span>{item.status}</span>
              </div>
            </article>
          ))}
        </section>

        <section className="cd-card">
          <h2>Execution packet</h2>
          <h3>Craigslist / local hauling copy</h3>
          <textarea className="cd-copy" readOnly value={craigslistCopy} />
          <h3>Source Support overflow script</h3>
          <textarea className="cd-copy small" readOnly value={sourceSupportScript} />
        </section>
      </div>
    </section>
  );
}
