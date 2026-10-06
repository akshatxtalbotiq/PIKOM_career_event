const apiTarget = process.env.DJANGO_API_URL || "http://127.0.0.1:8000";

/** @type {import('next').NextConfig} */
const nextConfig = {
  skipTrailingSlashRedirect: true,
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${apiTarget}/api/:path*/` },
      { source: "/media/:path*", destination: `${apiTarget}/media/:path*` },
    ];
  },
};

export default nextConfig;
