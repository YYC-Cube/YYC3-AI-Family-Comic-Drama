/**
 * Agent Runtime 独立服务 — Hono App 工厂（P2 同构收敛）
 *
 * 与启动入口 server.ts 分离：本模块不发起网络监听，可直接在测试中
 * 通过 app.request() 验证认证/限流/路由行为。
 */
import { Hono } from 'hono';
import { AI_FAMILY_PROFILES } from './family-registry.js';
import type { AgentRuntime } from './runtime.js';
import {
  agentApiKeyAuth,
  agentBodySizeLimit,
  agentRateLimiter,
  agentSecurityHeaders,
  PayloadTooLargeError,
} from './server-security.js';

export interface AgentServerOptions {
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

export function createAgentServerApp(
  runtime: AgentRuntime,
  options: AgentServerOptions,
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

  app.use('*', agentSecurityHeaders());
  app.use('*', agentBodySizeLimit(1024 * 1024));
  app.use(
    '*',
    agentRateLimiter({
      windowMs: options.rateLimitWindowMs ?? 60_000,
      maxRequests: options.rateLimitMax ?? 100,
      trustedProxyHops: options.trustedProxyHops ?? 0,
    }),
  );
  // 认证置于路由前：/health 与 / 公开，其余全部保护
  app.use('*', agentApiKeyAuth(options.apiKeys));

  app.get('/', (c) => c.json({ ok: true, data: { service: 'yyc3-agent-runtime' } }));

  // 健康检查（Docker HEALTHCHECK 探测路径，无需认证）
  app.get('/health', (c) => {
    return c.json({
      ok: true,
      data: { status: 'ok', uptime: process.uptime(), agents: runtime.listAgents().length },
    });
  });

  // 列出可用 Family 档案
  app.get('/api/v1/profiles', (c) => {
    return c.json({ ok: true, data: AI_FAMILY_PROFILES });
  });

  // 创建智能体
  app.post('/api/v1/agents', async (c) => {
    const rawBody = await safeJson(c);
    if (rawBody === null || typeof rawBody !== 'object') {
      return c.json(
        { ok: false, error: { code: 'BAD_REQUEST', message: 'invalid JSON body' } },
        400,
      );
    }
    const body = rawBody as { profileName?: unknown; id?: unknown };
    if (typeof body.profileName !== 'string' || body.profileName.length === 0) {
      return c.json(
        { ok: false, error: { code: 'BAD_REQUEST', message: 'profileName is required' } },
        400,
      );
    }
    if (body.id !== undefined && typeof body.id !== 'string') {
      return c.json(
        { ok: false, error: { code: 'BAD_REQUEST', message: 'id must be a string' } },
        400,
      );
    }
    const profile = AI_FAMILY_PROFILES.find(
      (p) => p.nameEN === body.profileName || p.nameCN === body.profileName,
    );
    if (!profile) {
      return c.json(
        {
          ok: false,
          error: { code: 'NOT_FOUND', message: `Unknown profile: ${body.profileName}` },
        },
        404,
      );
    }
    const agent = runtime.createAgent(profile, body.id);
    return c.json({ ok: true, data: { id: agent.id, status: agent.status } });
  });

  // 列出已创建智能体
  app.get('/api/v1/agents', (c) => {
    return c.json({
      ok: true,
      data: runtime.listAgents().map((a) => ({ id: a.id, status: a.status })),
    });
  });

  // 获取单个智能体概要
  app.get('/api/v1/agents/:id', (c) => {
    const agent = runtime.getAgent(c.req.param('id'));
    if (!agent) {
      return c.json(
        { ok: false, error: { code: 'NOT_FOUND', message: `Agent not found: ${c.req.param('id')}` } },
        404,
      );
    }
    return c.json({
      ok: true,
      data: {
        id: agent.id,
        status: agent.status,
        createdAt: agent.createdAt,
        lastActiveAt: agent.lastActiveAt,
        messages: agent.messages.length,
      },
    });
  });

  app.notFound((c) =>
    c.json({ ok: false, error: { code: 'NOT_FOUND', message: 'Not Found' } }, 404),
  );

  return app;
}
