import type { MetadataRoute } from 'next';

const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://app.alreadyherellc.com';

// Public marketing/content routes only. Internal ops pages under
// /command-center/* must stay out of the index — see app/robots.ts.
const routes = [
  '/',
  '/newsletter',
  '/newsletter/30-day-checklist',
  '/marketing',
  '/widget-kit'
];

export default function sitemap(): MetadataRoute.Sitemap {
  return routes.map((route) => ({
    url: `${baseUrl}${route}`,
    lastModified: new Date()
  }));
}
