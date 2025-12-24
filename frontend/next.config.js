/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',

  // API Rewrites - This is the magic that eliminates CORS and Traefik
  // All /api/* requests are proxied to the backend container internally
  // The browser only ever talks to the frontend on port 3000
  async rewrites() {
    // Backend URL from environment or default for Docker Compose
    const backendUrl = process.env.BACKEND_URL || 'http://backend:8000';

    return [
      // Proxy /api/docs to FastAPI Swagger UI
      {
        source: '/api/docs',
        destination: `${backendUrl}/docs`,
      },
      // Proxy /api/openapi.json for Swagger
      {
        source: '/api/openapi.json',
        destination: `${backendUrl}/openapi.json`,
      },
      // Proxy all /api/v1/* requests to backend
      {
        source: '/api/v1/:path*',
        destination: `${backendUrl}/api/v1/:path*`,
      },
      // Proxy /api/health for monitoring
      {
        source: '/api/health',
        destination: `${backendUrl}/health`,
      },
    ];
  },

  // Environment variables exposed to the browser
  env: {
    // Empty string means "same origin" - API calls go to /api/*
    // which Next.js rewrites to the backend
    NEXT_PUBLIC_API_URL: '',
  },
};

module.exports = nextConfig;
