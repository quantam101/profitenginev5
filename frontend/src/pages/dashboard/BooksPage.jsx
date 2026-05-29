import React, { useEffect, useState } from "react";
import { BookOpen } from "lucide-react";
import { PageHeader, Metric } from "./_shared";
import { getBooks } from "../../lib/api";

export default function BooksPage() {
  const [books, setBooks] = useState([]);
  useEffect(() => { getBooks().then(setBooks).catch(() => {}); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, []);
  const revenue = books.reduce((s, b) => s + b.revenue, 0);
  const sold = books.reduce((s, b) => s + b.sold, 0);
  return (
    <div className="px-6 py-10 md:px-10" data-testid="books-page">
      <PageHeader eyebrow="// books" title="Digital products." subtitle="Long-form assets you've packaged and shipped. Revenue + downloads attributed per title." />
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 mb-6">
        <Metric label="titles" value={books.length} testId="books-titles" />
        <Metric label="copies sold" value={sold.toLocaleString()} testId="books-sold" />
        <Metric label="lifetime revenue" value={`$${revenue.toLocaleString()}`} testId="books-revenue" />
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {books.map((b) => (
          <div key={b.id} className="ent-card p-5" data-testid={`book-${b.id}`}>
            <div className="mb-2 flex items-center gap-2 text-[11px] uppercase tracking-widest text-ink-muted">
              <BookOpen className="h-3.5 w-3.5 text-ok" /> {b.channel}
            </div>
            <h3 className="font-display text-lg">{b.title}</h3>
            <div className="mt-1 text-[11px] text-ink-faint">by {b.author}</div>
            <div className="mt-4 grid grid-cols-3 gap-3 border-t border-line pt-3 text-[11px]">
              <div><div className="text-ink-faint uppercase tracking-widest">price</div><div className="text-ink">${b.price}</div></div>
              <div><div className="text-ink-faint uppercase tracking-widest">sold</div><div className="text-ok">{b.sold}</div></div>
              <div><div className="text-ink-faint uppercase tracking-widest">revenue</div><div className="text-ok">${b.revenue.toLocaleString()}</div></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
