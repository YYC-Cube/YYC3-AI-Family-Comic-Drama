import type { NextConfig } from "next";

// YYC3 漫剧工作台前端配置
// 说明：JWT 鉴权统一在 API 网关层完成，前端不持有任何密钥（密钥零入库红线）
const nextConfig: NextConfig = {
  reactStrictMode: true,
};

export default nextConfig;
