import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async redirects() {
    return [
      {
        source: '/:path*',
        has: [{ type: 'host' as const, value: 'repto-three.vercel.app' }],
        destination: 'https://repto.be/:path*',
        permanent: true,
      },
    ]
  },
};

export default nextConfig;

// auto-deploy test 01-06-2026 — kan verwijderd worden
