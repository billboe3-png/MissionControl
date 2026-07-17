/** @type {import('next').NextConfig} */
const nextConfig = {
  output: process.env.NEXT_OUTPUT === 'standalone' ? 'standalone' : undefined,
  images: {
    unoptimized: process.env.NEXT_OUTPUT === 'export',
  },
  pageExtensions: ['ts', 'tsx', 'mdx'],
}

module.exports = nextConfig
