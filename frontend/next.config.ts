import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  allowedDevOrigins: [
    '172.17.74.61',
    '172.17.76.133',
    'localhost',
    '127.0.0.1',
  ],
};

export default nextConfig;
