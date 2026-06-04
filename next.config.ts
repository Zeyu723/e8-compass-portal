import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/assessments/:path*",
        destination: "http://23.254.236.178:8000/assessments/:path*",
      },
      {
        source: "/api/demo/:path*",
        destination: "http://23.254.236.178:8000/demo/:path*",
      },
      {
        source: "/api/health",
        destination: "http://23.254.236.178:8000/health",
      },
    ];
  },
};

export default nextConfig;
