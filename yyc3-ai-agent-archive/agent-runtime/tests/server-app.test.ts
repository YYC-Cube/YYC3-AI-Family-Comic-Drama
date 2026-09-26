/// <reference types="node" />
/**
 * Agent Runtime 独立服务 — 认证 / 限流 / 边界 / 持久化测试（P2 同构收敛）
 */
import { FileStore } from '@yyc3/store';
import type { Hono } from 'hono';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { beforeEach, describe, expect, it } from 'vitest';
import { AgentRuntime } from '../src/runtime.js';
import { createAgentServerApp } from '../src/server-app.js';
import { resolveClientIp, trustedProxyHopsFromEnv } from '../src/server-security.js';

function freshApp(runtime: AgentRuntime, apiKeys: string[], trustedProxyHops = 0): Hono {
  return createAgentServerApp(runtime, { apiKeys, trustedProxyHops });
}

const KEY = 'test-agent-key';

describe('Agent Runtime 独立服务安全（P2 同构收敛）', () => {
  let runtime: AgentRuntime;
  let app: Hono;

  beforeEach(() => {
    runtime = new AgentRuntime();
    app = freshApp(runtime, [KEY]);
  });

  describe('环境解析（纯函数）', () => {
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
      const locked = freshApp(new AgentRuntime(), []);
      const res = await locked.request('/api/v1/profiles');
      expect(res.status).toBe(503);
      expect((await res.json()).error.code).toBe('AUTH_SERVICE_DISABLED');
    });

    it('无凭据访问 profiles 返回 401', async () => {
      const res = await app.request('/api/v1/profiles');
      expect(res.status).toBe(401);
      expect((await res.json()).error.code).toBe('UNAUTHORIZED');
    });

    it('X-API-Key 正确可访问，错误返回 403', async () => {
      const ok = await app.request('/api/v1/profiles', { headers: { 'X-API-Key': KEY } });
      expect(ok.status).toBe(200);

      const bad = await app.request('/api/v1/profiles', { headers: { 'X-API-Key': 'wrong' } });
      expect(bad.status).toBe(403);
      expect((await bad.json()).error.code).toBe('FORBIDDEN');
    });

    it('Authorization: Bearer 方式同样有效', async () => {
      const res = await app.request('/api/v1/agents', {
        headers: { Authorization: `Bearer ${KEY}` },
      });
      expect(res.status).toBe(200);
    });

    it('POST /api/v1/agents 无凭据返回 401（未授权创建面封闭）', async () => {
      const res = await app.request('/api/v1/agents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profileName: 'QianHang' }),
      });
      expect(res.status).toBe(401);
    });
  });

  describe('请求体边界（Zod 式手检 + chunked 计数）', () => {
    const auth = { 'Content-Type': 'application/json', 'X-API-Key': KEY };

    it('非法 JSON 返回 400', async () => {
      const res = await app.request('/api/v1/agents', {
        method: 'POST',
        headers: auth,
        body: '{broken',
      });
      expect(res.status).toBe(400);
      expect((await res.json()).error.code).toBe('BAD_REQUEST');
    });

    it('缺少 profileName 返回 400', async () => {
      const res = await app.request('/api/v1/agents', {
        method: 'POST',
        headers: auth,
        body: JSON.stringify({ id: 'x' }),
      });
      expect(res.status).toBe(400);
    });

    it('未知档案返回 404', async () => {
      const res = await app.request('/api/v1/agents', {
        method: 'POST',
        headers: auth,
        body: JSON.stringify({ profileName: 'No-Such-Agent' }),
      });
      expect(res.status).toBe(404);
    });

    it('合法创建返回智能体 ID', async () => {
      const res = await app.request('/api/v1/agents', {
        method: 'POST',
        headers: auth,
        body: JSON.stringify({ profileName: 'QianHang', id: 'qianhang-1' }),
      });
      expect(res.status).toBe(200);
      const body = await res.json();
      expect(body.ok).toBe(true);
      expect(body.data.id).toBe('qianhang-1');
    });

    it('Content-Length 超限返回 413（认证后、业务前拦截）', async () => {
      const largeBody = 'x'.repeat(2 * 1024 * 1024);
      const res = await app.request('/api/v1/agents', {
        method: 'POST',
        headers: { ...auth, 'Content-Length': String(largeBody.length) },
        body: largeBody,
      });
      expect(res.status).toBe(413);
      expect((await res.json()).error.code).toBe('PAYLOAD_TOO_LARGE');
    });

    it('chunked（无 Content-Length）超限流式计数返回 413 而非绕过', async () => {
      // 构造无 Content-Length 的流式请求体（2MB，分块推送）
      const chunk = 'x'.repeat(64 * 1024);
      const stream = new ReadableStream<Uint8Array>({
        start(controller) {
          for (let i = 0; i < 32; i++) {
            controller.enqueue(new TextEncoder().encode(chunk));
          }
          controller.close();
        },
      });
      const req = new Request('http://localhost/api/v1/agents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-API-Key': KEY },
        body: stream,
        duplex: 'half',
      } as RequestInit);
      const res = await app.request(req);
      expect(res.status).toBe(413);
      expect((await res.json()).error.code).toBe('PAYLOAD_TOO_LARGE');
    });

    it('chunked 未超限正常通过', async () => {
      const stream = new ReadableStream<Uint8Array>({
        start(controller) {
          controller.enqueue(new TextEncoder().encode('{"profileName":"QianHang"}'));
          controller.close();
        },
      });
      const req = new Request('http://localhost/api/v1/agents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-API-Key': KEY },
        body: stream,
        duplex: 'half',
      } as RequestInit);
      const res = await app.request(req);
      expect(res.status).toBe(200);
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
      const limited = freshApp(new AgentRuntime(), [KEY], 0);
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

  describe('未知路由与单查', () => {
    it('认证通过后未知路径返回 404 JSON', async () => {
      const res = await app.request('/no-such-path', { headers: { 'X-API-Key': KEY } });
      expect(res.status).toBe(404);
      expect((await res.json()).error.code).toBe('NOT_FOUND');
    });

    it('GET /api/v1/agents/:id 概要查询', async () => {
      await app.request('/api/v1/agents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-API-Key': KEY },
        body: JSON.stringify({ profileName: 'QianHang', id: 'q-lookup' }),
      });
      const ok = await app.request('/api/v1/agents/q-lookup', { headers: { 'X-API-Key': KEY } });
      expect(ok.status).toBe(200);
      const missing = await app.request('/api/v1/agents/ghost', { headers: { 'X-API-Key': KEY } });
      expect(missing.status).toBe(404);
    });
  });

  describe('Store 持久化接线（重启可恢复）', () => {
    it('FileStore 写穿 + 新实例 restore 恢复智能体与消息', async () => {
      const dir = await mkdtemp(join(tmpdir(), 'yyc3-agent-store-'));
      const file = join(dir, 'agents.json');

      const s1 = new FileStore(file, { debounceMs: 0 });
      const rt1 = new AgentRuntime({ store: s1 });
      const app1 = freshApp(rt1, [KEY]);
      await app1.request('/api/v1/agents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-API-Key': KEY },
        body: JSON.stringify({ profileName: 'QianHang', id: 'persist-1' }),
      });
      rt1.sendMessage('你好', 'user-1', 'persist-1');
      await rt1.flushPending();
      await s1.close();

      // 模拟重启：新 Store + 新 Runtime + restore
      const s2 = new FileStore(file, { debounceMs: 0 });
      const rt2 = new AgentRuntime({ store: s2 });
      const restored = await rt2.restore();
      expect(restored).toBe(1);
      const agent = rt2.getAgent('persist-1');
      expect(agent).toBeDefined();
      expect(agent!.status).toBe('idle');
      expect(agent!.messages.length).toBe(1);
      expect(agent!.messages[0].content).toBe('你好');
      await s2.close();
      await rm(dir, { recursive: true, force: true });
    });

    it('destroyAgent 同步删除持久化键', async () => {
      const dir = await mkdtemp(join(tmpdir(), 'yyc3-agent-store-'));
      const file = join(dir, 'agents.json');
      const s = new FileStore(file, { debounceMs: 0 });
      const rt = new AgentRuntime({ store: s });
      const profile = {
        familyId: 'F1',
        nameCN: '启航',
        nameEN: 'QianHang',
        role: 'r',
        tier: 'decision' as const,
        motto: 'm',
        phone: 'p',
        capabilities: [],
        systemPrompt: '',
        collaborators: [],
        emoji: '🚀',
        color: '#fff',
      };
      rt.createAgent(profile, 'del-1');
      await rt.flushPending();
      expect((await s.keys('agent:'))).toContain('agent:del-1');
      rt.destroyAgent('del-1');
      await new Promise((r) => setTimeout(r, 20));
      expect(await s.keys('agent:')).toEqual([]);
      await s.close();
      await rm(dir, { recursive: true, force: true });
    });

    it('restore 对损坏数据跳过而非崩溃', async () => {
      const dir = await mkdtemp(join(tmpdir(), 'yyc3-agent-store-'));
      const file = join(dir, 'agents.json');
      const s = new FileStore(file, { debounceMs: 0 });
      await s.put('agent:broken', '{not-json');
      const rt = new AgentRuntime({ store: s });
      await expect(rt.restore()).resolves.toBe(0);
      await s.close();
      await rm(dir, { recursive: true, force: true });
    });
  });
});
