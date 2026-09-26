/**
 * MCP Runtime 独立服务 — 认证 / 限流 / 边界测试（P1-2）
 */
import { Hono } from 'hono';
import { beforeEach, describe, expect, it } from 'vitest';
import { UnifiedMCPRuntime } from '../src/runtime.js';
import { createMcpServerApp } from '../src/server-app.js';
import { resolveClientIp, trustedProxyHopsFromEnv } from '../src/server-security.js';

async function freshApp(apiKeys: string[], trustedProxyHops = 0): Promise<Hono> {
  const runtime = new UnifiedMCPRuntime();
  await runtime.initialize();
  return createMcpServerApp(runtime, { apiKeys, trustedProxyHops });
}

const KEY = 'test-mcp-key';

describe('MCP Runtime 独立服务安全（P1-2）', () => {
  let app: Hono;

  beforeEach(async () => {
    app = await freshApp([KEY]);
  });

  describe('绑定默认值与环境解析（纯函数）', () => {
    it('trustedProxyHopsFromEnv 非法值回退 0', () => {
      expect(trustedProxyHopsFromEnv(undefined)).toBe(0);
      expect(trustedProxyHopsFromEnv('abc')).toBe(0);
      expect(trustedProxyHopsFromEnv('-1')).toBe(0);
      expect(trustedProxyHopsFromEnv('2')).toBe(2);
    });

    it('resolveClientIp hops=0 时忽略 XFF', () => {
      expect(resolveClientIp({ 'x-forwarded-for': '1.2.3.4' }, 0)).toBe('127.0.0.1');
    });

    it('resolveClientIp hops=2 取倒数第二跳', () => {
      expect(
        resolveClientIp({ 'x-forwarded-for': '9.9.9.9, 10.0.0.1, 192.168.1.100' }, 2),
      ).toBe('10.0.0.1');
    });
  });

  describe('健康检查', () => {
    it('GET /health 无需认证（容器探测路径）', async () => {
      const res = await app.request('/health');
      expect(res.status).toBe(200);
      const body = await res.json();
      expect(body.ok).toBe(true);
      expect(body.data.status).toBe('ok');
    });
  });

  describe('fail-closed 认证', () => {
    it('未配置 API Key 时 /api 端点 503（fail-closed）', async () => {
      const locked = await freshApp([]);
      const res = await locked.request('/api/v1/tools');
      expect(res.status).toBe(503);
      const body = await res.json();
      expect(body.error.code).toBe('AUTH_SERVICE_DISABLED');
    });

    it('无凭据访问 tools/list 返回 401', async () => {
      const res = await app.request('/api/v1/tools');
      expect(res.status).toBe(401);
      expect((await res.json()).error.code).toBe('UNAUTHORIZED');
    });

    it('X-API-Key 正确可访问，错误返回 403', async () => {
      const ok = await app.request('/api/v1/tools', { headers: { 'X-API-Key': KEY } });
      expect(ok.status).toBe(200);

      const bad = await app.request('/api/v1/tools', { headers: { 'X-API-Key': 'wrong' } });
      expect(bad.status).toBe(403);
      expect((await bad.json()).error.code).toBe('FORBIDDEN');
    });

    it('Authorization: Bearer 方式同样有效', async () => {
      const res = await app.request('/api/v1/tools', {
        headers: { Authorization: `Bearer ${KEY}` },
      });
      expect(res.status).toBe(200);
    });

    it('POST tools/call 无凭据返回 401（未授权 RCE 面封闭）', async () => {
      const res = await app.request('/api/v1/tools/call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'x', args: {} }),
      });
      expect(res.status).toBe(401);
    });
  });

  describe('请求体边界', () => {
    const auth = { 'Content-Type': 'application/json', 'X-API-Key': KEY };

    it('非法 JSON 返回 400', async () => {
      const res = await app.request('/api/v1/tools/call', {
        method: 'POST',
        headers: auth,
        body: '{broken',
      });
      expect(res.status).toBe(400);
      expect((await res.json()).error.code).toBe('BAD_REQUEST');
    });

    it('缺少 name 返回 400', async () => {
      const res = await app.request('/api/v1/tools/call', {
        method: 'POST',
        headers: auth,
        body: JSON.stringify({ args: {} }),
      });
      expect(res.status).toBe(400);
    });

    it('请求体超过 1MB 返回 413（认证前拦截）', async () => {
      const largeBody = 'x'.repeat(2 * 1024 * 1024);
      const res = await app.request('/api/v1/tools/call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Content-Length': String(largeBody.length) },
        body: largeBody,
      });
      expect(res.status).toBe(413);
      expect((await res.json()).error.code).toBe('PAYLOAD_TOO_LARGE');
    });

    it('chunked（无 Content-Length）超限流式计数返回 413 而非绕过（P2）', async () => {
      const chunk = 'x'.repeat(64 * 1024);
      const stream = new ReadableStream<Uint8Array>({
        start(controller) {
          for (let i = 0; i < 32; i++) {
            controller.enqueue(new TextEncoder().encode(chunk));
          }
          controller.close();
        },
      });
      const req = new Request('http://localhost/api/v1/tools/call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-API-Key': KEY },
        body: stream,
        duplex: 'half',
      } as RequestInit);
      const res = await app.request(req);
      expect(res.status).toBe(413);
      expect((await res.json()).error.code).toBe('PAYLOAD_TOO_LARGE');
    });
  });

  describe('安全头与限流', () => {
    it('响应包含安全头（含 CSP/HSTS）且不暴露服务端标识', async () => {
      const res = await app.request('/health');
      expect(res.headers.get('x-content-type-options')).toBe('nosniff');
      expect(res.headers.get('x-frame-options')).toBe('DENY');
      expect(res.headers.get('content-security-policy')).toBe(
        "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
      );
      expect(res.headers.get('strict-transport-security')).toBe(
        'max-age=31536000; includeSubDomains',
      );
      expect(res.headers.get('x-powered-by')).toBeNull();
    });

    it('默认 hops=0：伪造不同 XFF 无法绕过限流', async () => {
      const limited = await freshApp([KEY], 0);
      for (let i = 0; i < 101; i++) {
        await limited.request('/health', { headers: { 'X-Forwarded-For': `10.1.${i % 250}.${i}` } });
      }
      const res = await limited.request('/health', {
        headers: { 'X-Forwarded-For': '10.9.9.9' },
      });
      expect(res.status).toBe(429);
      expect((await res.json()).error.code).toBe('RATE_LIMIT_EXCEEDED');
    });
  });

  describe('未知路由', () => {
    it('认证通过后返回 404 JSON', async () => {
      const res = await app.request('/no-such-path', { headers: { 'X-API-Key': KEY } });
      expect(res.status).toBe(404);
      expect((await res.json()).error.code).toBe('NOT_FOUND');
    });
  });
});
