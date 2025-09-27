const withMDX = require('@next/mdx')({
  extension: /\.mdx?$/
});

module.exports = withMDX({
  pageExtensions: ['js', 'jsx', 'mdx'],
  reactStrictMode: true,
  // static export config
  output: 'export',
  basePath: '/dreamaware.cc',
  assetPrefix: '/dreamaware.cc/'
});