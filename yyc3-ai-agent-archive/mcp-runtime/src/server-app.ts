/**
 * MCP Runtime 独立服务 — Hono App 工厂
 *
 * 与启动入口 server.ts 分离：本模块不发起网络监听，可直接在测试中
 * 通过 app.request() 验证认证/限流/路由行为。
 */
import { Hono } from 'hono';
import type { UnifiedMCPRuntime } from './runtime.js';
import {
  mcpApiKeyAuth,
  mcpBodySizeLimit,
  mcpRateLimiter,
  mcpSecurityHeaders,
  PayloadTooLargeError,
} from './server-security.js';

export interface McpServerOptions {
  /** 允许的 API Key（通常来自 YYC3_API_KEYS）；空数组 = fail-closed */
  apiKeys: string[];
  /** 受信代理跳数（限流键取 XFF 倒数第 N 跳） */
  trustedProxyHops?: number;
  /** 限流窗口/上限 */
  rateLimitWindowMs?: number;
  rateLimitMax?: number;
}

/** 安全解析 JSON：非法 JSON / null 返回 null（调用方转 400）；计数流超限上抛 413 */
async function safeJson(c: { req: { json: () => Promise<unknown> } }): Promise<unknown | null> {
  try {
    return (await c.req.json()) ?? null;
  } catch (err) {
    if (err instanceof PayloadTooLargeError) throw err;
    return null;
  }
}

export function createMcpServerApp(
  runtime: UnifiedMCPRuntime,
  options: McpServerOptions,
): Hono {
  const app = new Hono();

  app.onError((err, c) => {
    // chunked 计数流超限：映射为 413（而非 500）
    if (err instanceof PayloadTooLargeError) {
      return c.json(
        { ok: false, error: { code: 'PAYLOAD_TOO_LARGE', message: err.message } },
        413,
      );
    }
    const message = err instanceof Error ? err.message : 'Internal Server Error';
    return c.json({ ok: false, error: { code: 'INTERNAL_ERROR', message } }, 500);
  });

  app.use('*', mcpSecurityHeaders());
  app.use('*', mcpBodySizeLimit(1024 * 1024));
  app.use(
    '*',
    mcpRateLimiter({
      windowMs: options.rateLimitWindowMs ?? 60_000,
      maxRequests: options.rateLimitMax ?? 100,
      trustedProxyHops: options.trustedProxyHops ?? 0,
    }),
  );
  // 认证置于路由前：/health 公开，/api 全部保护（含 GET tools/list）
  app.use('*', mcpApiKeyAuth(options.apiKeys));

  app.get('/', (c) => c.json({ ok: true, data: { service: 'yyc3-mcp-runtime' } }));

  // 健康检查（Docker HEALTHCHECK 探测路径，无需认证）
  app.get('/health', (c) => {
    const tools = runtime.listAllTools();
    return c.json({
      ok: true,
      data: { status: 'ok', uptime: process.uptime(), tools: tools.length },
    });
  });

  // MCP tools/list
  app.get('/api/v1/tools', (c) => {
    return c.json({ ok: true, data: runtime.listAllSourcedTools() });
  });

  // MCP tools/call
  app.post('/api/v1/tools/call', async (c) => {
    const rawBody = await safeJson(c);
    if (rawBody === null || typeof rawBody !== 'object') {
      return c.json(
        { ok: false, error: { code: 'BAD_REQUEST', message: 'invalid JSON body' } },
        400,
      );
    }
    const body = rawBody as { name?: unknown; args?: Record<string, unknown> };
    if (typeof body.name !== 'string' || body.name.length === 0) {
      return c.json(
        { ok: false, error: { code: 'BAD_REQUEST', message: 'name is required' } },
        400,
      );
    }
    const args = body.args && typeof body.args === 'object' ? body.args : {};
    const result = await runtime.callTool(body.name, args);
    return c.json({ ok: !result.isError, data: result });
  });

  app.notFound((c) =>
    c.json({ ok: false, error: { code: 'NOT_FOUND', message: 'Not Found' } }, 404),
  );

  return app;
}
