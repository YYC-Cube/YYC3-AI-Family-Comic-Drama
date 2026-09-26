/// <reference types="node" />
/**
 * Skill Gateway — 端到端测试
 */
import type { UnifiedSkill } from '@yyc3/skill-registry';
import { SkillExecutor, SkillLoader, SkillRegistry } from '@yyc3/skill-registry';
import { mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { beforeAll, describe, expect, it, vi } from 'vitest';
import { SkillGateway } from '../src/gateway.js';

function makeSkill(overrides: Partial<UnifiedSkill> = {}): UnifiedSkill {
  return {
    id: 'GW-001',
    name: 'Gateway 测试技能',
    description: '用于 Gateway 测试',
    domain: 'marketplace',
    type: 'hybrid',
    runtime: 'native',
    entry: '',
    inputs: [{ name: 'text', type: 'string', description: '输入文本', required: true }],
    outputs: [{ type: 'text' }],
    ...overrides,
  };
}

describe('SkillGateway', () => {
  let gateway: SkillGateway;
  let registry: SkillRegistry;

  beforeAll(() => {
    registry = new SkillRegistry();
    registry.register(makeSkill());
    registry.register(makeSkill({ id: 'GW-002', domain: 'glm-ocr' }));

    const loader = new SkillLoader(registry, { rootDir: './skills' });
    const executor = new SkillExecutor(registry);

    gateway = new SkillGateway({ registry, loader, executor }, { apiKeys: ['test-key'] });
  });

  const AUTH_HEADERS = { 'X-API-Key': 'test-key' };

  it('创建 app 实例', () => {
    expect(gateway.app).toBeDefined();
    expect(gateway.config.port).toBe(3030);
  });

  describe('GET /api/v1/health', () => {
    it('返回健康状态', async () => {
      const res = await gateway.app.request('/api/v1/health');
      expect(res.status).toBe(200);
      const body = await res.json();
      expect(body.ok).toBe(true);
      expect(body.data.status).toBe('ok');
    });

    it('返回技能总数', async () => {
      const res = await gateway.app.request('/api/v1/health');
      const body = await res.json();
      expect(body.data.skills.total).toBe(2);
    });
  });

  describe('GET /api/v1/health/ready', () => {
    it('返回就绪状态', async () => {
      const res = await gateway.app.request('/api/v1/health/ready');
      expect(res.status).toBe(200);
      const body = await res.json();
      expect(body.data.ready).toBe(true);
    });
  });

  describe('GET /api/v1/health/version', () => {
    it('返回版本信息', async () => {
      const res = await gateway.app.request('/api/v1/health/version');
      expect(res.status).toBe(200);
      const body = await res.json();
      expect(body.data.version).toBe('1.0.0');
    });
  });

  describe('GET /api/v1/skills', () => {
    it('返回技能列表', async () => {
      const res = await gateway.app.request('/api/v1/skills');
      expect(res.status).toBe(200);
      const body = await res.json();
      expect(body.ok).toBe(true);
      expect(Array.isArray(body.data)).toBe(true);
      expect(body.data.length).toBe(2);
      expect(body.meta.total).toBe(2);
    });

    it('分页', async () => {
      const res = await gateway.app.request('/api/v1/skills?pageSize=1&page=1');
      const body = await res.json();
      expect(body.data.length).toBe(1);
      expect(body.meta.page).toBe(1);
      expect(body.meta.pageSize).toBe(1);
    });

    it('按领域过滤', async () => {
      const res = await gateway.app.request('/api/v1/skills?domain=glm-ocr');
      const body = await res.json();
      expect(body.data.length).toBe(1);
      expect(body.data[0].id).toBe('GW-002');
    });
  });

  describe('GET /api/v1/skills/:id', () => {
    it('返回单个技能', async () => {
      const res = await gateway.app.request('/api/v1/skills/GW-001');
      expect(res.status).toBe(200);
      const body = await res.json();
      expect(body.data.id).toBe('GW-001');
    });

    it('不存在的技能返回 404', async () => {
      const res = await gateway.app.request('/api/v1/skills/NOT-EXIST');
      expect(res.status).toBe(404);
    });
  });

  describe('GET /api/v1/skills/stats', () => {
    it('返回统计信息', async () => {
      const res = await gateway.app.request('/api/v1/skills/stats');
      expect(res.status).toBe(200);
      const body = await res.json();
      expect(body.data.totalSkills).toBe(2);
    });
  });

  describe('GET /api/v1/skills/domains', () => {
    it('返回领域列表', async () => {
      const res = await gateway.app.request('/api/v1/skills/domains');
      expect(res.status).toBe(200);
      const body = await res.json();
      expect(body.data).toContain('glm-ocr');
      expect(body.data).toContain('marketplace');
    });
  });

  describe('POST /api/v1/skills/reload', () => {
    it('reload 以磁盘为唯一事实源：已删除技能被清除（P2 sync 语义）', async () => {
      // 临时技能目录：两个磁盘技能 + 一个手工注册的"幽灵"（磁盘上不存在）
      const dir = join(tmpdir(), `yyc3-reload-${Date.now()}`);
      mkdirSync(join(dir, 'skill-a'), { recursive: true });
      mkdirSync(join(dir, 'skill-b'), { recursive: true });
      writeFileSync(join(dir, 'skill-a', 'SKILL.md'),
        '---\nname: reload-a\nid: GW-RELOAD-A\ndomain: marketplace\nversion: 1.0.0\n---\n\nbody');
      writeFileSync(join(dir, 'skill-b', 'SKILL.md'),
        '---\nname: reload-b\nid: GW-RELOAD-B\ndomain: marketplace\nversion: 1.0.0\n---\n\nbody');

      const reg = new SkillRegistry();
      const loader = new SkillLoader(reg, { rootDir: dir });
      const gw = new SkillGateway(
        { registry: reg, loader, executor: new SkillExecutor(reg) },
        { apiKeys: ['test-key'] },
      );
      await gw.initialize();
      reg.register(makeSkill({ id: 'GW-STALE' }));
      expect(reg.get('GW-STALE')).toBeDefined();

      const res = await gw.app.request('/api/v1/skills/reload', {
        method: 'POST',
        headers: AUTH_HEADERS,
      });
      expect(res.status).toBe(200);
      const body = await res.json();
      expect(body.data.reloaded).toBe(2);

      // 幽灵技能被清除（此前缺陷：只增不删，已删除技能仍可执行）
      expect(reg.get('GW-STALE')).toBeUndefined();
      // 磁盘技能仍在
      expect(reg.get('GW-RELOAD-A')).toBeDefined();
      expect(reg.get('GW-RELOAD-B')).toBeDefined();

      rmSync(dir, { recursive: true, force: true });
    });
  });

  describe('POST /api/v1/execute', () => {
    it('缺少参数返回 400', async () => {
      const res = await gateway.app.request('/api/v1/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...AUTH_HEADERS },
        body: JSON.stringify({}),
      });
      expect(res.status).toBe(400);
    });

    it('不存在的技能返回 404', async () => {
      const res = await gateway.app.request('/api/v1/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...AUTH_HEADERS },
        body: JSON.stringify({ skillId: 'NOT-EXIST', params: {} }),
      });
      expect(res.status).toBe(404);
    });

    it('成功执行 native 技能', async () => {
      const res = await gateway.app.request('/api/v1/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...AUTH_HEADERS },
        body: JSON.stringify({ skillId: 'GW-001', params: { text: 'demo' } }),
      });
      expect(res.status).toBe(200);
      const body = await res.json();
      expect(body.ok).toBe(true);
      expect(body.data.skillId).toBe('GW-001');
      expect(body.data.output).toBeTruthy();
    });

    it('执行抛错时返回 500 与 EXECUTION_ERROR', async () => {
      // 注册一个执行时必然抛错的技能（node 运行时 + 不存在入口）
      registry.register(
        makeSkill({
          id: 'GW-BOOM',
          runtime: 'node',
          entry: 'nope.js',
          source: '/nonexistent-gw',
        })
      );
      const res = await gateway.app.request('/api/v1/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...AUTH_HEADERS },
        body: JSON.stringify({ skillId: 'GW-BOOM', params: {} }),
      });
      expect(res.status).toBe(500);
      const body = await res.json();
      expect(body.error.code).toBe('EXECUTION_ERROR');
    });

    it('timeout 超过上限时被截断（不抛错）', async () => {
      const res = await gateway.app.request('/api/v1/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...AUTH_HEADERS },
        body: JSON.stringify({ skillId: 'GW-001', params: {}, timeout: 999_999 }),
      });
      expect(res.status).toBe(200);
    });

    it('缺少认证凭据返回 401（认证层集成）', async () => {
      const res = await gateway.app.request('/api/v1/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ skillId: 'GW-001', params: {} }),
      });
      expect(res.status).toBe(401);
    });

    it('timeout 低于下界时被钳制到 1000ms', async () => {
      const res = await gateway.app.request('/api/v1/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...AUTH_HEADERS },
        body: JSON.stringify({ skillId: 'GW-001', params: {}, timeout: 1 }),
      });
      expect(res.status).toBe(200);
    });

    it('非法 JSON 返回 400 而非 500', async () => {
      const res = await gateway.app.request('/api/v1/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...AUTH_HEADERS },
        body: '{invalid json',
      });
      expect(res.status).toBe(400);
      const body = await res.json();
      expect(body.error.code).toBe('BAD_REQUEST');
    });

    it('body 为 null 返回 400', async () => {
      const res = await gateway.app.request('/api/v1/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...AUTH_HEADERS },
        body: 'null',
      });
      expect(res.status).toBe(400);
      const body = await res.json();
      expect(body.error.code).toBe('BAD_REQUEST');
    });
  });

  describe('POST /api/v1/execute/mcp/list', () => {
    it('无 MCP 运行时返回 503', async () => {
      const res = await gateway.app.request('/api/v1/execute/mcp/list', {
        method: 'POST',
        headers: AUTH_HEADERS,
      });
      expect(res.status).toBe(503);
    });
  });

  describe('POST /api/v1/execute/mcp/call', () => {
    it('无 MCP 运行时返回 503', async () => {
      const res = await gateway.app.request('/api/v1/execute/mcp/call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...AUTH_HEADERS },
        body: JSON.stringify({ name: 'x', args: {} }),
      });
      expect(res.status).toBe(503);
    });
  });

  describe('搜索与元信息分支', () => {
    it('按关键词搜索', async () => {
      const res = await gateway.app.request('/api/v1/skills?q=Gateway');
      const body = await res.json();
      expect(body.data.length).toBeGreaterThan(0);
    });

    it('按类型与运行时过滤', async () => {
      const res = await gateway.app.request('/api/v1/skills?type=hybrid&runtime=native&status=active');
      const body = await res.json();
      expect(body.data.length).toBeGreaterThan(0);
    });

    it('非法分页参数回退默认值', async () => {
      const res = await gateway.app.request('/api/v1/skills?page=-3&pageSize=0');
      const body = await res.json();
      // page=-3 → NaN → 1; pageSize=0 → Number('0')=0 falsy → 默认 20（上限逻辑不影响）
      expect(body.meta.page).toBe(1);
      expect(body.meta.pageSize).toBe(20);
    });
  });

  describe('错误处理中间件', () => {
    it('路由抛错时返回 500 INTERNAL_ERROR', async () => {
      // 注册损坏的 registry 行为：让 stats 抛错触发 errorHandler
      const broken = new SkillRegistry();
      const brokenLoader = new SkillLoader(broken, { rootDir: './skills' });
      const brokenExecutor = new SkillExecutor(broken);
      const brokenGateway = new SkillGateway({
        registry: broken,
        loader: brokenLoader,
        executor: brokenExecutor,
      });
      vi.spyOn(brokenGateway.deps.registry, 'getStats').mockImplementation(() => {
        throw new Error('boom');
      });
      const res = await brokenGateway.app.request('/api/v1/health');
      expect(res.status).toBe(500);
      const body = await res.json();
      expect(body.error.code).toBe('INTERNAL_ERROR');
    });
  });

  describe('gateway 生命周期', () => {
    it('initialize 后 getUptime 大于 0', async () => {
      const fresh = new SkillGateway({
        registry,
        loader: new SkillLoader(registry, { rootDir: './skills' }),
        executor: new SkillExecutor(registry),
      });
      expect(fresh.getUptime()).toBe(0);
      await fresh.initialize();
      expect(fresh.getUptime()).toBeGreaterThanOrEqual(0);
    });
  });

  describe('GET /api/v1/registry（MCP Registry 聚合，Task G1-4）', () => {
    it('透传 registry.json（导出产物已存在时）', async () => {
      const res = await gateway.app.request('/api/v1/registry');
      // CI 环境可能未先执行 export-mcp，仅在产物存在时校验 200 结构
      if (res.status === 200) {
        const body = await res.json();
        expect(body.$schema).toContain('server.schema.json');
        expect(Array.isArray(body.servers)).toBe(true);
      } else {
        expect(res.status).toBe(404);
        const body = await res.json();
        expect(body.error.code).toBe('REGISTRY_NOT_EXPORTED');
      }
    });

    it('servers 列表返回 ApiResponse 包装', async () => {
      const res = await gateway.app.request('/api/v1/registry/servers');
      expect(res.status).toBe(200);
      const body = await res.json();
      expect(body.ok).toBe(true);
      expect(Array.isArray(body.data)).toBe(true);
      expect(body.data.length).toBeGreaterThan(0);
      expect(body.meta.total).toBe(body.data.length);
      for (const s of body.data) {
        expect(s.name).toMatch(/^io\.github\.yyc-cube\//);
      }
    });

    it('q 关键词过滤生效', async () => {
      const all = await (await gateway.app.request('/api/v1/registry/servers')).json();
      const res = await gateway.app.request('/api/v1/registry/servers?q=12306');
      const body = await res.json();
      expect(body.data.length).toBeGreaterThan(0);
      expect(body.data.length).toBeLessThan(all.data.length);
    });

    it('按 slug 查询单个 server', async () => {
      const res = await gateway.app.request('/api/v1/registry/servers/12306');
      expect(res.status).toBe(200);
      const body = await res.json();
      expect(body.ok).toBe(true);
      expect(body.data.name).toBe('io.github.yyc-cube/12306');
    });

    it('不存在的 slug 返回 404 SERVER_NOT_FOUND', async () => {
      const res = await gateway.app.request('/api/v1/registry/servers/no-such-slug-xyz');
      expect(res.status).toBe(404);
      const body = await res.json();
      expect(body.error.code).toBe('SERVER_NOT_FOUND');
    });
  });

  describe('Security', () => {
    it('应包含安全响应头', async () => {
      const res = await gateway.app.request('/api/v1/health');
      expect(res.headers.get('x-content-type-options')).toBe('nosniff');
      expect(res.headers.get('x-frame-options')).toBe('DENY');
      expect(res.headers.get('referrer-policy')).toBe('strict-origin-when-cross-origin');
    });

    it('应包含 CSP 与 HSTS 头（P2 补齐）', async () => {
      const res = await gateway.app.request('/api/v1/health');
      expect(res.headers.get('content-security-policy')).toBe(
        "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
      );
      expect(res.headers.get('strict-transport-security')).toBe(
        'max-age=31536000; includeSubDomains',
      );
    });

    it('不应暴露服务端标识', async () => {
      const res = await gateway.app.request('/api/v1/health');
      expect(res.headers.get('x-powered-by')).toBeNull();
    });

    it('速率限制应返回限流头', async () => {
      const res = await gateway.app.request('/api/v1/health');
      expect(res.headers.get('x-ratelimit-limit')).toBe('100');
      expect(res.headers.get('x-ratelimit-remaining')).toBeDefined();
      expect(res.headers.get('x-ratelimit-reset')).toBeDefined();
    });

    it('超过速率限制应返回 429', async () => {
      // 快速耗尽 tokens
      for (let i = 0; i < 101; i++) {
        await gateway.app.request('/api/v1/health');
      }
      const res = await gateway.app.request('/api/v1/health');
      expect(res.status).toBe(429);
      const body = await res.json();
      expect(body.error.code).toBe('RATE_LIMIT_EXCEEDED');
    });

    it('请求体过大应返回 413', async () => {
      const largeBody = 'x'.repeat(2 * 1024 * 1024); // 2MB
      const res = await gateway.app.request('/api/v1/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Content-Length': String(largeBody.length) },
        body: largeBody,
      });
      expect(res.status).toBe(413);
    });

    it('chunked（无 Content-Length）超限流式计数返回 413 而非绕过（P2）', async () => {
      // 独立实例：避免共享 gateway 的限流桶已被前序测试耗尽导致 429 干扰
      const fresh = new SkillGateway(
        { registry, loader: new SkillLoader(registry, { rootDir: './skills' }), executor: new SkillExecutor(registry) },
        { apiKeys: ['test-key'] },
      );
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
      const req = new Request('http://localhost/api/v1/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-API-Key': 'test-key' },
        body: stream,
        duplex: 'half',
      } as RequestInit);
      const res = await fresh.app.request(req);
      expect(res.status).toBe(413);
      expect((await res.json()).error.code).toBe('PAYLOAD_TOO_LARGE');
    });

    it('XFF 伪造不应影响直连场景的限流键（默认 hops=0）', async () => {
      // 默认 trustedProxyHops=0 时不信任 XFF，所有请求共享同一限流键
      const limitGateway = new SkillGateway(
        { registry, loader: new SkillLoader(registry, { rootDir: './skills' }), executor: new SkillExecutor(registry) },
        { apiKeys: ['test-key'], trustedProxyHops: 0 },
      );
      // 连发 101 次，每次伪造不同 XFF
      for (let i = 0; i < 101; i++) {
        await limitGateway.app.request('/api/v1/health', {
          headers: { 'X-Forwarded-For': `10.0.0.${i}` },
        });
      }
      const res = await limitGateway.app.request('/api/v1/health', {
        headers: { 'X-Forwarded-For': '10.0.0.999' },
      });
      expect(res.status).toBe(429);
    });

    it('XFF 倒数第 hops 跳作为真实客户端 IP', async () => {
      const proxyGateway = new SkillGateway(
        { registry, loader: new SkillLoader(registry, { rootDir: './skills' }), executor: new SkillExecutor(registry) },
        { apiKeys: ['test-key'], trustedProxyHops: 2 },
      );
      // 101 次同一真实 IP（链倒数第二跳）→ 耗尽；伪造前缀不改变限流键
      for (let i = 0; i < 101; i++) {
        await proxyGateway.app.request('/api/v1/health', {
          headers: { 'X-Forwarded-For': `1.2.3.${i}, 10.0.0.1, 192.168.1.100` },
        });
      }
      const blocked = await proxyGateway.app.request('/api/v1/health', {
        headers: { 'X-Forwarded-For': '9.9.9.9, 10.0.0.1, 192.168.1.100' },
      });
      expect(blocked.status).toBe(429);

      // 另一真实 IP 不受影响
      const ok = await proxyGateway.app.request('/api/v1/health', {
        headers: { 'X-Forwarded-For': '5.5.5.5, 10.0.0.2, 192.168.1.100' },
      });
      expect(ok.status).toBe(200);
    });
  });
});
