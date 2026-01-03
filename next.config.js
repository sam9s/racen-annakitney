/** @type {import('next').NextConfig} */
const nextConfig = {
  async headers() {
    return [
      {
        source: '/widget.js',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=3600, stale-while-revalidate=86400' },
          { key: 'Access-Control-Allow-Origin', value: '*' },
        ],
      },
      {
        source: '/widget.min.js',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=3600, stale-while-revalidate=86400' },
          { key: 'Access-Control-Allow-Origin', value: '*' },
        ],
      },
      {
        source: '/anna-logo.png',
        headers: [
          { key: 'Cache-Control', value: 'public, max-age=86400' },
        ],
      },
    ];
  },
  async rewrites() {
    return [
      {
        source: '/api/chat/:path*',
        destination: 'http://localhost:8080/api/chat/:path*',
      },
      {
        source: '/api/feedback/:path*',
        destination: 'http://localhost:8080/api/feedback/:path*',
      },
      {
        source: '/api/channels/:path*',
        destination: 'http://localhost:8080/api/channels/:path*',
      },
      {
        source: '/webhook/:path*',
        destination: 'http://localhost:8080/webhook/:path*',
      },
      {
        source: '/health',
        destination: 'http://localhost:8080/health',
      },
    ];
  },
};

module.exports = nextConfig;
