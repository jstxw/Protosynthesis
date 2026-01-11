import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: [
    '172.17.74.61',
    'localhost',
    '127.0.0.1',
  ],
};

export default nextConfig;
