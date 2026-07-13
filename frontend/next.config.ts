import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "lh3.googleusercontent.com",
        pathname: "/**",
      },
    ],
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
      {
        source: "/ws/:path*",
        destination: "http://localhost:8000/ws/:path*",
      },
      {
        source: "/product/:path*",
        destination: "http://localhost:8000/product/:path*",
      },
      {
        source: "/workspace/:path*",
        destination: "http://localhost:8000/workspace/:path*",
      },
      {
        source: "/workspaces/:path*",
        destination: "http://localhost:8000/workspaces/:path*",
      },
      {
        source: "/admin/:path*",
        destination: "http://localhost:8000/admin/:path*",
      },
      {
        source: "/github/:path*",
        destination: "http://localhost:8000/github/:path*",
      },
      {
        source: "/workflows/:path*",
        destination: "http://localhost:8000/workflows/:path*",
      },
      {
        source: "/workflows",
        destination: "http://localhost:8000/workflows",
      },
      {
        source: "/resume/:path*",
        destination: "http://localhost:8000/resume/:path*",
      },
    ];
  },
};

export default nextConfig;
