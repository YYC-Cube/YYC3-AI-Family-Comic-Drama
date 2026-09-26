/**
 * Skill Gateway — 日志中间件
 */
import type { MiddlewareHandler } from 'hono';

export function logger(): MiddlewareHandler {
  return async (c, next) => {
    const start = Date.now();
    const { method, url } = c.req;
    await next();
    const ms = Date.now() - start;
    console.warn(`[Gateway] ${method} ${url} ${c.res.status} ${ms}ms`);
  };
}