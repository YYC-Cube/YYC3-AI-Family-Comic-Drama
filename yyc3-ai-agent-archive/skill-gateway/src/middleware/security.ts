/**
 * Skill Gateway — 安全中间件
 *
 * 提供: 速率限制 / 安全头 / 请求体大小限制
 */
import type { MiddlewareHandler } from 'hono';
import type { ApiResponse } from '../types.js';
import { createRateLimitStore, MemoryStore, type RateLimitStore } from './rate-limit-store.js';

// ================================================================
// 0. 受信代理解析（XFF 防伪）
// ================================================================

/**
 * 从 X-Forwarded-For 解析真实客户端 IP（受信代理跳数模型）。
 *
 * XFF 链格式：`client, proxy1, proxy2, ..., proxyN`（左→右，最左是原始客户端）。
 * 部署在 N 层受信代理之后时，取倒数第 N 跳（即 client 到第一个代理的 IP）。
 * 伪造的 XFF 前缀会出现在链左端，倒数取值天然将其排除。
 *
 * - `hops <= 0`（或 XFF 长度不足）：不信任 XFF，回退连接对端地址（Hono 未暴露 socket 时用占位）
 * - 环境变量 `YYC3_TRUSTED_PROXY_HOPS`：正整数，默认 0（直连，不信任 XFF）
 */
export function resolveClientIp(
  headers: { 'x-forwarded-for'?: string; 'x-real-ip'?: string },
  trustedProxyHops: number,
  fallbackIp = '127.0.0.1',
): string {
  if (trustedProxyHops > 0) {
    const xff = headers['x-forwarded-for'];
    if (xff) {
      const chain = xff.split(',').map((s) => s.trim()).filter(Boolean);
      // 倒数第 hops 跳：hops=1 → 最后一个（直连代理的上游即客户端）
      const idx = chain.length - trustedProxyHops;
      if (idx >= 0 && chain[idx]) return chain[idx];
      // 链短于信任跳数：攻击者伪造了过短的链，取最左端（最保守）
      if (chain.length > 0) return chain[0];
    }
    // 无 XFF：可能是直连，也看 x-real-ip（单代理场景）
    const realIp = headers['x-real-ip'];
    if (realIp) return realIp.trim();
  }
  return fallbackIp;
}

/** 从环境变量解析受信代理跳数（非法值回退 0） */
export function trustedProxyHopsFromEnv(raw: string | undefined): number {
  const n = Number(raw ?? '0');
  return Number.isInteger(n) && n >= 0 ? n : 0;
}

// ================================================================
// 1. 速率限制 (Token Bucket + 可插拔存储)
// ================================================================

interface RateLimitConfig {
  windowMs: number;
  maxRequests: number;
  /** 自定义存储后端（默认按 REDIS_URL 环境变量自动选择） */
  store?: RateLimitStore;
  keyGenerator?: (c: Parameters<MiddlewareHandler>[0]) => string;
  /**
   * 受信代理跳数：>0 时从 XFF 链倒数第 N 跳取真实客户端 IP；
   * 0（默认）不信任 XFF，用连接对端地址。
   * 部署在反向代理之后时必须显式设置，否则限流键可被伪造。
   */
  trustedProxyHops?: number;
}

interface CreatedRateLimiter extends MiddlewareHandler {
  /** 释放底层存储资源（server.ts 关闭时调用） */
  close: () => Promise<void>;
}

export function rateLimiter(config: RateLimitConfig = {
  windowMs: 60_000,
  maxRequests: 100,
}): CreatedRateLimiter {
  const { windowMs, maxRequests, keyGenerator, trustedProxyHops = 0 } = config;

  // 存储异步初始化：首个请求前若未就绪则临时用内存桶，就绪后切换
  let store: RateLimitStore = new MemoryStore(windowMs);
  let backendName: 'redis' | 'memory' = 'memory';
  // 存储连续失败计数（fail-open 告警用，恢复后清零）
  let storeFailures = 0;
  const ownedStore = config.store ? undefined : createRateLimitStore(windowMs);
  ownedStore
    ?.then(({ store: s, backend }) => {
      // 异步切换：保留内存桶中已扣减状态无必要（初始化窗口极短）
      const old = store;
      store = s;
      backendName = backend;
      if (old !== s) void old.close();
    })
    .catch(() => {
      // createRateLimitStore 内部已降级，此处仅兜底
    });

  const middleware = (async (c, next) => {
    const key = keyGenerator
      ? keyGenerator(c)
      : resolveClientIp(
        {
          'x-forwarded-for': c.req.header('x-forwarded-for'),
          'x-real-ip': c.req.header('x-real-ip'),
        },
        trustedProxyHops,
      );

    let bucket: { tokens: number; lastRefill: number };
    try {
      bucket = await store.consume(key, { windowMs, maxRequests });
      storeFailures = 0;
    } catch {
      // Redis 运行时故障：fail-open 记录并放行（高可用优先）
      bucket = { tokens: maxRequests - 1, lastRefill: Date.now() };
      // 连续失败告警：不再静默（P2）— 首次与每第 5 次连续失败告警一次，避免日志洪水
      storeFailures += 1;
      if (storeFailures === 1 || storeFailures % 5 === 0) {
        console.warn(
          `[RateLimit] store consume failed (${storeFailures} consecutive) — fail-open on backend '${backendName}'`
        );
      }
    }

    if (bucket.tokens < 0) {
      const resp: ApiResponse = {
        ok: false,
        error: {
          code: 'RATE_LIMIT_EXCEEDED',
          message: `请求过于频繁，请稍后重试。限制: ${maxRequests} 次/${windowMs / 1000}s`,
        },
      };
      c.status(429);
      c.header('Retry-After', String(Math.ceil(windowMs / 1000)));
      return c.json(resp);
    }

    c.header('X-RateLimit-Limit', String(maxRequests));
    c.header('X-RateLimit-Remaining', String(Math.floor(bucket.tokens)));
    c.header('X-RateLimit-Reset', String(Math.ceil((bucket.lastRefill + windowMs) / 1000)));
    c.header('X-RateLimit-Backend', backendName);

    await next();
  }) as CreatedRateLimiter;

  middleware.close = async () => {
    if (ownedStore) {
      const { store: s } = await ownedStore;
      await s.close();
    } else if (config.store) {
      await config.store.close();
    }
  };

  return middleware;
}

// ================================================================
// 2. 安全头 (Helmet-like)
// ================================================================

export function securityHeaders(): MiddlewareHandler {
  return async (c, next) => {
    await next();

    // 防止 MIME 类型嗅探
    c.header('X-Content-Type-Options', 'nosniff');
    // 防止点击劫持
    c.header('X-Frame-Options', 'DENY');
    // XSS 保护
    c.header('X-XSS-Protection', '0');
    // 引用策略
    c.header('Referrer-Policy', 'strict-origin-when-cross-origin');
    // 权限策略
    c.header('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');
    // CSP：纯 JSON API 不加载任何前端资源（P2 补齐）
    c.header('Content-Security-Policy', "default-src 'none'; frame-ancestors 'none'; base-uri 'none'");
    // HSTS：经 TLS 终止代理部署时强制 HTTPS（RFC 6797 规定明文传输下 UA 忽略本头，无条件发送安全）
    c.header('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
    // 移除服务端标识
    c.res.headers.delete('X-Powered-By');
    c.res.headers.delete('Server');
  };
}

// ================================================================
// 3. 请求体大小限制（Content-Length 快速拒绝 + chunked 流式计数）
// ================================================================

/** 请求体实际字节数超限：由计数流在消费时抛出，经 onError 映射为 413 */
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

export function bodySizeLimit(maxBytes: number = 1024 * 1024): MiddlewareHandler {
  return async (c, next) => {
    const contentLength = Number(c.req.header('content-length') || 0);
    if (contentLength > maxBytes) {
      const resp: ApiResponse = {
        ok: false,
        error: {
          code: 'PAYLOAD_TOO_LARGE',
          message: `请求体过大，最大允许 ${(maxBytes / 1024 / 1024).toFixed(1)}MB`,
        },
      };
      c.status(413);
      return c.json(resp);
    }
    // chunked 无 Content-Length：包装请求体为计数流，超限在消费时中断（P2 补齐）
    if (c.req.raw.body) {
      Object.defineProperty(c.req, 'raw', {
        value: wrapBodyWithLimit(c.req.raw, maxBytes),
        configurable: true,
      });
    }
    await next();
  };
}
