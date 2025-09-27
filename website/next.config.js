/** @type {import('next').NextConfig} */
const withMDX = require('@next/mdx')({
 extension: /\.mdx?$/
});

module.exports = withMDX({
 // Static export for GitHub Pages
 output: 'export',
 // Project Pages path: https://<org>.github.io/<repo>/
 basePath: '/dreamaware.cc',
 assetPrefix: '/dreamaware.cc/',
 // Generate /path/index.html for GH Pages compatibility
 trailingSlash: true,
 // MDX support
 pageExtensions: ['js', 'jsx', 'ts', 'tsx', 'md', 'mdx'],
 // Required for next export when using images
 images: { unoptimized: true },
 reactStrictMode: true
});