import type { MetadataRoute } from 'next';

const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://profitengine.alreadyherellc.com';

const routes = [
  '/',
  '/command-center/agents',
  '/command-center/approvals',
  '/command-center/changelog',
  '/command-center/connectors',
  '/command-center/costs',
  '/command-center/logs',
  '/command-center/modules',
  '/command-center/security',
  '/command-center/workflows'
];

export default function sitemap(): MetadataRoute.Sitemap {
  return routes.map((route) => ({
    url: `${baseUrl}${route}`,
    lastModified: new Date()
  }));
}
