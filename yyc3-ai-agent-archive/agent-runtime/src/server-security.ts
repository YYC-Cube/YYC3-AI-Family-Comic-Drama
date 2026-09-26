/**
 * Agent Runtime 独立服务 — 安全中间件（P2 同构收敛）
 *
 * 与 skill-gateway / mcp-runtime 保持【契约一致】（依赖方向约束：不可互相导入）：
 * - 同一环境变量 YYC3_API_KEYS / YYC3_TRUSTED_PROXY_HOPS
 * - 同一凭据携带方式（Authorization: Bearer / X-API-Key）
 * - 同一错误码（AUTH_SERVICE_DISABLED 503 / UNAUTHORIZED 401 / FORBIDDEN 403）
 * - 同一 fail-closed 策略与时延恒定比较
 * - 同一请求体限制（Content-Length 快速拒绝 + chunked 流式计数）
 * - 同一安全头集合（含 CSP/HSTS）
 *
 * /health 与 / 公开（容器健康探测），其余路径一律要求认证。
 */
import type { MiddlewareHandler } from 'hono';
import { timingSafeEqual } from 'node:crypto';

// ----------------------------------------------------------------
// 认证
// ----------------------------------------------------------------

/** 时延恒定字符串比较，防止时序侧信道 */
function secureCompare(a: string, b: string): boolean {
  const ba = Buffer.from(a, 'utf-8');
  const bb = Buffer.from(b, 'utf-8');
  if (ba.length !== bb.length) {
    timingSafeEqual(ba, ba);
    return false;
  }
  return timingSafeEqual(ba, bb);
}

/** 从环境变量解析 API Key 列表（逗号分隔） */
export function apiKeysFromEnv(env: string | undefined): string[] {
  return (env ?? '')
    .split(',')
    .map((k) => k.trim())
    .filter((k) => k.length > 0);
}

function extractKey(headers: Headers): string | undefined {
  const bearer = headers.get('authorization');
  if (bearer?.startsWith('Bearer ')) {
    return bearer.slice(7).trim() || undefined;
  }
  return headers.get('x-api-key')?.trim() || undefined;
}

/**
 * fail-closed API Key 认证：保护除 /health 与 / 外的全部路径。
 * 未配置任何 key 时返回 503（服务不可用），而非静默放行。
 */
export function agentApiKeyAuth(apiKeys: string[]): MiddlewareHandler {
  const keys = apiKeys.filter((k) => k.length > 0);

  return async (c, next) => {
    const path = new URL(c.req.url).pathname;
    if (path === '/health' || path === '/') {
      return next();
    }

    if (keys.length === 0) {
      c.status(503);
      return c.json({
        ok: false,
        error: {
          code: 'AUTH_SERVICE_DISABLED',
          message: 'Agent Runtime 未配置 API Key（YYC3_API_KEYS），独立服务端点已禁用',
        },
      });
    }

    const provided = extractKey(c.req.raw.headers);
    if (!provided) {
      c.status(401);
      return c.json({
        ok: false,
        error: {
          code: 'UNAUTHORIZED',
          message: '缺少认证凭据，请通过 Authorization: Bearer <key> 或 X-API-Key 提供',
        },
      });
    }

    if (!keys.some((k) => secureCompare(provided, k))) {
      c.status(403);
      return c.json({ ok: false, error: { code: 'FORBIDDEN', message: 'API Key 无效' } });
    }

    return next();
  };
}

// ----------------------------------------------------------------
// 安全头（含 CSP/HSTS，与 gateway/mcp 同契约）
// ----------------------------------------------------------------

export function agentSecurityHeaders(): MiddlewareHandler {
  return async (c, next) => {
    await next();
    c.header('X-Content-Type-Options', 'nosniff');
    c.header('X-Frame-Options', 'DENY');
    c.header('X-XSS-Protection', '0');
    c.header('Referrer-Policy', 'strict-origin-when-cross-origin');
    c.header('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');
    // CSP：纯 JSON API 不加载任何前端资源
    c.header('Content-Security-Policy', "default-src 'none'; frame-ancestors 'none'; base-uri 'none'");
    // HSTS：TLS 终止代理部署时强制 HTTPS（明文下 UA 按规范忽略本头，无条件发送安全）
    c.header('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
    c.res.headers.delete('X-Powered-By');
    c.res.headers.delete('Server');
  };
}

// ----------------------------------------------------------------
// 请求体大小限制（Content-Length 快速拒绝 + chunked 流式计数）
// ----------------------------------------------------------------

/** 请求体实际字节数超限：由计数流在消费时抛出，经 app.onError 映射为 413 */
export class PayloadTooLargeError extends Error {
  constructor(maxBytes: number) {
    super(`请求体过大，最大允许 ${(maxBytes / 1024 / 1024).toFixed(1)}MB`);
    this.name = 'PayloadTooLargeError';
  }
}

/**
 * 将请求体包装为带字节计数的流：累计超过 maxBytes 即取消上游并报错。
 * 用于 chunked 传输（无 Content-Length）场景，防止只看头部被绕过。
 */
function wrapBodyWithLimit(raw: Request, maxBytes: number): Request {
  const source = raw.body;
  if (!source) return raw;

  const limited = new ReadableStream<Uint8Array>({
    start(controller) {
      const reader = source.getReader();
      void (async () => {
        let received = 0;
        try {
          for (; ;) {
            const { done, value } = await reader.read();
            if (done) break;
            received += value.byteLength;
            if (received > maxBytes) {
              await reader.cancel().catch(() => { });
              controller.error(new PayloadTooLargeError(maxBytes));
              return;
            }
            controller.enqueue(value);
          }
          controller.close();
        } catch (err) {
          controller.error(err);
        }
      })();
    },
  });

  return new Request(raw.url, {
    method: raw.method,
    headers: raw.headers,
    body: limited,
    duplex: 'half',
  } as RequestInit);
}

export function agentBodySizeLimit(maxBytes = 1024 * 1024): MiddlewareHandler {
  return async (c, next) => {
    const contentLength = Number(c.req.header('content-length') || 0);
    if (contentLength > maxBytes) {
      c.status(413);
      return c.json({
        ok: false,
        error: {
          code: 'PAYLOAD_TOO_LARGE',
          message: `请求体过大，最大允许 ${(maxBytes / 1024 / 1024).toFixed(1)}MB`,
        },
      });
    }
    if (c.req.raw.body) {
      Object.defineProperty(c.req, 'raw', {
        value: wrapBodyWithLimit(c.req.raw, maxBytes),
        configurable: true,
      });
    }
    await next();
  };
}

// ----------------------------------------------------------------
// 受信代理跳数解析（与 gateway/mcp resolveClientIp 同契约）
// ----------------------------------------------------------------

export function resolveClientIp(
  headers: { 'x-forwarded-for'?: string; 'x-real-ip'?: string },
  trustedProxyHops: number,
  fallbackIp = '127.0.0.1',
): string {
  if (trustedProxyHops > 0) {
    const xff = headers['x-forwarded-for'];
    if (xff) {
      const chain = xff.split(',').map((s) => s.trim()).filter(Boolean);
      const idx = chain.length - trustedProxyHops;
      if (idx >= 0 && chain[idx]) return chain[idx];
      if (chain.length > 0) return chain[0];
    }
    const realIp = headers['x-real-ip'];
    if (realIp) return realIp.trim();
  }
  return fallbackIp;
}

export function trustedProxyHopsFromEnv(raw: string | undefined): number {
  const n = Number(raw ?? '0');
  return Number.isInteger(n) && n >= 0 ? n : 0;
}

// ----------------------------------------------------------------
// 内存 Token Bucket 限流（独立服务单机部署足够；分布式需求走 Redis Store）
// ----------------------------------------------------------------

interface Bucket {
  tokens: number;
  lastRefill: number;
}

export interface MemoryRateLimitOptions {
  windowMs: number;
  maxRequests: number;
  trustedProxyHops?: number;
}

export function agentRateLimiter(options: MemoryRateLimitOptions): MiddlewareHandler {
  const { windowMs, maxRequests, trustedProxyHops = 0 } = options;
  const buckets = new Map<string, Bucket>();

  return async (c, next) => {
    const key = resolveClientIp(
      {
        'x-forwarded-for': c.req.header('x-forwarded-for'),
        'x-real-ip': c.req.header('x-real-ip'),
      },
      trustedProxyHops,
    );

    const now = Date.now();
    const bucket = buckets.get(key) ?? { tokens: maxRequests, lastRefill: now };
    const elapsed = now - bucket.lastRefill;
    if (elapsed >= windowMs) {
      bucket.tokens = maxRequests;
      bucket.lastRefill = now;
    }
    bucket.tokens -= 1;
    buckets.set(key, bucket);

    c.header('X-RateLimit-Limit', String(maxRequests));
    c.header('X-RateLimit-Remaining', String(Math.max(0, Math.floor(bucket.tokens))));
    c.header('X-RateLimit-Reset', String(Math.ceil((bucket.lastRefill + windowMs) / 1000)));

    if (bucket.tokens < 0) {
      c.status(429);
      c.header('Retry-After', String(Math.ceil(windowMs / 1000)));
      return c.json({
        ok: false,
        error: {
          code: 'RATE_LIMIT_EXCEEDED',
          message: `请求过于频繁，请稍后重试。限制: ${maxRequests} 次/${windowMs / 1000}s`,
        },
      });
    }

    await next();
  };
}
