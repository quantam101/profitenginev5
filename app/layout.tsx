import type { Metadata } from 'next';
import Script from 'next/script';
import { Analytics } from '@vercel/analytics/react';
import Providers from './providers';
import './style.css';

export const metadata: Metadata = {
  title: 'ProfitEngine Command Center',
  description: 'Production-gated ProfitEngine command center with zero-spend controls, disabled stale source, and explicit deployment readiness state.'
};

const GA_ID = process.env.NEXT_PUBLIC_GA_ID ?? '';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        {/* Google Analytics 4 */}
        {GA_ID && (
          <>
            <Script
              src={`https://www.googletagmanager.com/gtag/js?id=${GA_ID}`}
              strategy="afterInteractive"
            />
            <Script id="ga4-init" strategy="afterInteractive">
              {`
                window.dataLayer = window.dataLayer || [];
                function gtag(){dataLayer.push(arguments);}
                gtag('js', new Date());
                gtag('config', '${GA_ID}', { page_path: window.location.pathname });
              `}
            </Script>
          </>
        )}
        <Providers>{children}</Providers>
        {/* Vercel Analytics — automatic page views + Web Vitals */}
        <Analytics />
      </body>
    </html>
  );
}
