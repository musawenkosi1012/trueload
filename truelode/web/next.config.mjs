/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Hide the dev-tools bubble / route indicators — recordings and judge
  // walkthroughs should see the product, not the framework chrome.
  devIndicators: false,
};

export default nextConfig;
