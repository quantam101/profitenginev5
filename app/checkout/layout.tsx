// Internal tool page — not for search indexing. Mirrors the command-center
// layout's noindex so direct links can't leak these routes into results.
export const metadata = { robots: { index: false, follow: false } };

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}
