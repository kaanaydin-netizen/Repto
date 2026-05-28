import type { MetadataRoute } from 'next'

const BASE = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://repto.be'

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date()
  return [
    { url: `${BASE}/`,            lastModified: now, changeFrequency: 'weekly', priority: 1.0 },
    { url: `${BASE}/sign-in`,     lastModified: now, changeFrequency: 'yearly', priority: 0.3 },
    { url: `${BASE}/sign-up`,     lastModified: now, changeFrequency: 'yearly', priority: 0.5 },
    { url: `${BASE}/privacy`,     lastModified: now, changeFrequency: 'yearly', priority: 0.2 },
    { url: `${BASE}/voorwaarden`, lastModified: now, changeFrequency: 'yearly', priority: 0.2 },
  ]
}
