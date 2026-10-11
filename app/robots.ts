import type { MetadataRoute } from 'next';

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: '*',
      allow: '/'
      // NOTE: do NOT disallow /command-center here. The layout emits
      // noindex, and crawlers must keep fetching the pages to see it —
      // a disallow would trap already-indexed URLs in search results
      // forever. Once Search Console shows them gone, disallow can be
      // added to cut crawl waste.
    }
  };
}
