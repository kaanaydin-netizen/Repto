import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async redirects() {
    return [
      // 301-redirect van vercel.app naar repto.be zodra domein live is.
      // Schakel in door de `disabled`-vlag te verwijderen.
      {
        source: '/:path*',
        has: [{ type: 'host', value: 'repto-three.vercel.app' }],
        destination: 'https://repto.be/:path*',
        permanent: true,
        missing: [],
      },
    ].filter(() => process.env.REPTO_DOMAIN_LIVE === 'true')
  },
};

export default nextConfig;
