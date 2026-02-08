/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  output: 'standalone', // Required for Docker standalone build
  images: {
    domains: ['localhost'],
  },
}

module.exports = nextConfig
