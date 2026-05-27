import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async redirects() {
    // Schakel de redirect in via Vercel env var REPTO_DOMAIN_LIVE=true
    if (process.env.REPTO_DOMAIN_LIVE !== 'true') return []
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
