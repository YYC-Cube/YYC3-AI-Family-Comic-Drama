import { NextResponse, type NextRequest } from "next/server";

/**
 * 安全响应头中间件
 * 说明：JWT 鉴权统一在 API 网关层完成，前端仓库不落地任何密钥（密钥零入库红线）
 */
export function middleware(_request: NextRequest) {
  const response = NextResponse.next();
  response.headers.set("X-Frame-Options", "DENY");
  response.headers.set("X-Content-Type-Options", "nosniff");
  response.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
  return response;
}

export const config = {
  // 跳过静态资源
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
