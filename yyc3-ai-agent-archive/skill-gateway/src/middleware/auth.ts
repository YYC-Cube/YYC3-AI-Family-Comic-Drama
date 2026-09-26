/**
 * Skill Gateway — API 认证中间件
 *
 * 策略: fail-closed（未配置密钥时拒绝受保护端点）
 * - YYC3_API_KEYS: 逗号分隔的多 key 列表（环境变量注入）
 * - 支持 Authorization: Bearer <key> 与 X-API-Key: <key> 两种携带方式
 * - 只保护写操作/执行类路径；GET 发现类端点保持公开（可经 config 改为全保护）
 */
import type { MiddlewareHandler } from 'hono';
import { timingSafeEqual } from 'node:crypto';
import type { ApiResponse } from '../types.js';

/** 时延恒定字符串比较，防止时序侧信道 */
function secureCompare(a: string, b: string): boolean {
  const ba = Buffer.from(a, 'utf-8');
  const bb = Buffer.from(b, 'utf-8');
  if (ba.length !== bb.length) {
    // 长度不同也要消耗等量比较，避免长度泄露
    timingSafeEqual(ba, ba);
    return false;
  }
  return timingSafeEqual(ba, bb);
}

export interface AuthConfig {
  /** 允许的 API Key 列表；为空时 fail-closed 拒绝受保护路径 */
  apiKeys: string[];
  /** 额外保护的路径前缀（默认 /api/v1/execute 与所有 POST 写操作） */
  protectedPrefixes?: string[];
}

/** 从请求中提取 caller 提供的 key */
function extractKey(headers: Headers): string | undefined {
  const bearer = headers.get('authorization');
  if (bearer?.startsWith('Bearer ')) {
    return bearer.slice(7).trim() || undefined;
  }
  return headers.get('x-api-key')?.trim() || undefined;
}

export function apiKeyAuth(config: AuthConfig): MiddlewareHandler {
  const keys = config.apiKeys.filter((k) => k.length > 0);
  const extraPrefixes = config.protectedPrefixes ?? [];

  return async (c, next) => {
    const path = new URL(c.req.url).pathname;
    const isProtected =
      path.startsWith('/api/v1/execute') ||
      extraPrefixes.some((p) => path.startsWith(p)) ||
      c.req.method !== 'GET';

    // 公开端点直接放行
    if (!isProtected) {
      return next();
    }

    // fail-closed: 未配置任何 key 时拒绝
    if (keys.length === 0) {
      const resp: ApiResponse = {
        ok: false,
        error: {
          code: 'AUTH_SERVICE_DISABLED',
          message: '服务端未配置 API Key（YYC3_API_KEYS），受保护端点已禁用',
        },
      };
      c.status(503);
      return c.json(resp);
    }

    const provided = extractKey(c.req.raw.headers);
    if (!provided) {
      const resp: ApiResponse = {
        ok: false,
        error: {
          code: 'UNAUTHORIZED',
          message: '缺少认证凭据，请通过 Authorization: Bearer <key> 或 X-API-Key 提供',
        },
      };
      c.status(401);
      return c.json(resp);
    }

    const valid = keys.some((k) => secureCompare(provided, k));
    if (!valid) {
      const resp: ApiResponse = {
        ok: false,
        error: { code: 'FORBIDDEN', message: 'API Key 无效' },
      };
      c.status(403);
      return c.json(resp);
    }

    return next();
  };
}

/** 从环境变量解析 API Key 列表 */
export function apiKeysFromEnv(env: string | undefined): string[] {
  return (env ?? '')
    .split(',')
    .map((k) => k.trim())
    .filter((k) => k.length > 0);
}
