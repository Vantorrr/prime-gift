/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  // PROXY CONFIGURATION
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://prime-gift-production.up.railway.app/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
