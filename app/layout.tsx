import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import Providers from './providers';
import './style.css';

export const metadata: Metadata = {
  title: 'ProfitEngine Command Center',
  description: 'Production-gated ProfitEngine command center with zero-spend controls, disabled stale source, and explicit deployment readiness state.'
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
