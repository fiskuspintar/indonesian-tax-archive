import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  output: 'export',
  distDir: 'dist',
  images: {
    unoptimized: true,
  },
  trailingSlash: true,
  // Ensure static files are copied
  async headers() {
    return []
  },
}

export default nextConfig
