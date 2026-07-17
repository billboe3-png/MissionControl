const withMDX = require('@next/mdx')({
  extension: /\.mdx?$/,
  options: {
    remarkPlugins: [require('remark-gfm')],
    rehypePlugins: [require('rehype-highlight')],
  },
})

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: process.env.NEXT_OUTPUT || undefined,
  images: {
    unoptimized: process.env.NEXT_OUTPUT === 'export',
  },
  pageExtensions: ['ts', 'tsx', 'mdx'],
}

module.exports = withMDX(nextConfig)
