/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  basePath: '/miniapp',
  images: {
    unoptimized: true,
  },
  trailingSlash: true,
};

export default nextConfig;
