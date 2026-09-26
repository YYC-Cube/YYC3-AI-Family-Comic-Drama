import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 多 lockfile 环境下显式锚定追踪根（否则 Next 可能推断到 ~/ 导致路径越界）
  outputFileTracingRoot: __dirname,
};

export default nextConfig;
