/**
 * Skill Gateway — 认证中间件与限流存储测试
 */
import type { UnifiedSkill } from '@yyc3/skill-registry';
import { SkillExecutor, SkillLoader, SkillRegistry } from '@yyc3/skill-registry';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { SkillGateway } from '../src/gateway.js';
import { apiKeyAuth, apiKeysFromEnv } from '../src/middleware/auth.js';
import { MemoryStore, RedisStore, createRateLimitStore } from '../src/middleware/rate-limit-store.js';
import { rateLimiter } from '../src/middleware/security.js';

function makeSkill(overrides: Partial<UnifiedSkill> = {}): UnifiedSkill {
  return {
    id: 'AUTH-001',
    name: '认证测试技能',
    description: '用于认证/限流测试',
    domain: 'marketplace',
    type: 'hybrid',
    runtime: 'native',
    entry: '',
    inputs: [{ name: 'text', type: 'string', description: '输入文本', required: true }],
    outputs: [{ type: 'text' }],
    ...overrides,
  };
}

// ================================================================
// apiKeysFromEnv
// ================================================================

describe('apiKeysFromEnv', () => {
  it('解析逗号分隔多 key 并去除空白', () => {
    expect(apiKeysFromEnv(' a , b ,, c ')).toEqual(['a', 'b', 'c']);
  });

  it('undefined 与空串返回空数组', () => {
    expect(apiKeysFromEnv(undefined)).toEqual([]);
    expect(apiKeysFromEnv('')).toEqual([]);
    expect(apiKeysFromEnv('  ,,  ')).toEqual([]);
  });
});

// ================================================================
// apiKeyAuth — fail-closed 语义
// ================================================================

describe('apiKeyAuth', () => {
  const makeCtx = (method = 'POST', path = '/api/v1/execute', headers: Record<string, string> = {}) => {
    const h = new Headers(headers);
    return {
      req: { method, url: `http://localhost:3030${path}`, raw: { headers: h }, header: (n: string) => h.get(n) },
      reqUrl: `http://localhost:3030${path}`,
      header: (n: string) => h.get(n),
      json: vi.fn(async (body: unknown, status?: number) => ({ status: status ?? 200, body })),
      status: vi.fn(),
    };
  };

  it('未配置任何 key 时 fail-closed 返回 503 AUTH_SERVICE_DISABLED', async () => {
    const mw = apiKeyAuth({ apiKeys: [] });
    const c = makeCtx();
    const next = vi.fn();
    await mw(c as never, next);
    expect(next).not.toHaveBeenCalled();
    expect(c.status).toHaveBeenCalledWith(503);
  });

  it('配置 key 后：无凭据 POST 返回 401', async () => {
    const mw = apiKeyAuth({ apiKeys: ['secret-1'] });
    const c = makeCtx();
    const next = vi.fn();
    await mw(c as never, next);
    expect(next).not.toHaveBeenCalled();
    expect(c.status).toHaveBeenCalledWith(401);
  });

  it('错误 key 返回 403', async () => {
    const mw = apiKeyAuth({ apiKeys: ['secret-1'] });
    const c = makeCtx('POST', '/api/v1/execute', { 'x-api-key': 'wrong' });
    const next = vi.fn();
    await mw(c as never, next);
    expect(next).not.toHaveBeenCalled();
    expect(c.status).toHaveBeenCalledWith(403);
  });

  it('Bearer 凭据正确时放行', async () => {
    const mw = apiKeyAuth({ apiKeys: ['secret-1', 'secret-2'] });
    const c = makeCtx('POST', '/api/v1/execute', { authorization: 'Bearer secret-2' });
    const next = vi.fn();
    await mw(c as never, next);
    expect(next).toHaveBeenCalledTimes(1);
  });

  it('X-API-Key 凭据正确时放行', async () => {
    const mw = apiKeyAuth({ apiKeys: ['secret-1'] });
    const c = makeCtx('POST', '/api/v1/execute', { 'x-api-key': 'secret-1' });
    const next = vi.fn();
    await mw(c as never, next);
    expect(next).toHaveBeenCalledTimes(1);
  });

  it('GET 公开端点无需凭据', async () => {
    const mw = apiKeyAuth({ apiKeys: ['secret-1'] });
    const c = makeCtx('GET', '/api/v1/skills');
    const next = vi.fn();
    await mw(c as never, next);
    expect(next).toHaveBeenCalledTimes(1);
  });

  it('authMode=all: 额外前缀下 GET 也需认证', async () => {
    const mw = apiKeyAuth({ apiKeys: ['secret-1'], protectedPrefixes: ['/api/v1'] });
    const c = makeCtx('GET', '/api/v1/skills');
    const next = vi.fn();
    await mw(c as never, next);
    expect(next).not.toHaveBeenCalled();
    expect(c.status).toHaveBeenCalledWith(401);
  });

  it('长度不同的 key 不相等且不抛错（时序安全比较分支）', async () => {
    const mw = apiKeyAuth({ apiKeys: ['short'] });
    const c = makeCtx('POST', '/api/v1/execute', { 'x-api-key': 'a-much-longer-key' });
    const next = vi.fn();
    await mw(c as never, next);
    expect(c.status).toHaveBeenCalledWith(403);
  });
});

// ================================================================
// MemoryStore — Token Bucket 语义
// ================================================================

describe('MemoryStore', () => {
  it('连续扣减至负值（触发限流）', async () => {
    const store = new MemoryStore(60_000);
    const cfg = { windowMs: 60_000, maxRequests: 3 };
    // max=3：连续扣减单调递减（refill 浮点漂移不做精确断言），耗尽后为负
    let prev = Infinity;
    for (let i = 0; i < 3; i++) {
      const b = await store.consume('k1', cfg);
      expect(b.tokens).toBeLessThanOrEqual(prev);
      prev = b.tokens;
    }
    const exhausted = await store.consume('k1', cfg);
    expect(exhausted.tokens).toBeLessThan(0);
    await store.close();
  });

  it('不同 key 桶相互隔离', async () => {
    const store = new MemoryStore(60_000);
    const cfg = { windowMs: 60_000, maxRequests: 1 };
    await store.consume('a', cfg);
    const b2 = await store.consume('b', cfg);
    expect(b2.tokens).toBe(0);
    // a 桶已耗尽
    const a2 = await store.consume('a', cfg);
    expect(a2.tokens).toBeLessThan(0);
    await store.close();
  });

  it('随时间补充令牌（模拟经过半个窗口）', async () => {
    vi.useFakeTimers();
    const store = new MemoryStore(60_000);
    const cfg = { windowMs: 60_000, maxRequests: 2 };
    const now = Date.now();
    vi.setSystemTime(now);
    await store.consume('t', cfg);
    await store.consume('t', cfg);
    const exhausted = await store.consume('t', cfg);
    expect(exhausted.tokens).toBe(-1);
    // 时间前进整个窗口 → 补充 min(max, -1+2)=1 → 扣减后 0
    vi.setSystemTime(now + 60_000);
    const refilled = await store.consume('t', cfg);
    expect(refilled.tokens).toBe(0);
    vi.useRealTimers();
    await store.close();
  });
});

// ================================================================
// createRateLimitStore 工厂 — 降级路径
// ================================================================

describe('createRateLimitStore', () => {
  const ENV_BACKUP = { ...process.env };

  afterEach(() => {
    process.env = { ...ENV_BACKUP };
  });

  it('无 REDIS_URL 时返回 memory 后端', async () => {
    delete process.env.REDIS_URL;
    const { backend } = await createRateLimitStore(60_000);
    expect(backend).toBe('memory');
  });

  it('REDIS_URL 不可达时自动降级 memory 并给出原因', async () => {
    process.env.REDIS_URL = 'redis://127.0.0.1:59999';
    const { backend, degradedReason } = await createRateLimitStore(60_000);
    expect(backend).toBe('memory');
    expect(degradedReason).toBeTruthy();
  }, 15_000);
});

// ================================================================
// RedisStore.connect 降级 — ioredis 未安装场景由工厂覆盖
// ================================================================

describe('RedisStore', () => {
  it('连接失败时 isReady 为 false 且记录原因', async () => {
    const store = await RedisStore.connect('redis://127.0.0.1:59999');
    expect(store.isReady()).toBe(false);
    expect(store.degradedReason).toBeTruthy();
    await expect(store.consume('k', { windowMs: 1000, maxRequests: 1 })).rejects.toThrow();
    await store.close();
  }, 15_000);
});

// ================================================================
// 集成：Gateway 开启认证后 execute 需凭据
// ================================================================

describe('Gateway x Auth 集成', () => {
  it('write 模式：POST /execute 无凭据 401，带 key 200', async () => {
    const registry = new SkillRegistry();
    registry.register(makeSkill());
    const gateway = new SkillGateway(
      { registry, loader: new SkillLoader(registry, { rootDir: './skills' }), executor: new SkillExecutor(registry) },
      { apiKeys: ['it-key-1'] }
    );

    const noAuth = await gateway.app.request('/api/v1/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ skillId: 'AUTH-001', params: { text: 'x' } }),
    });
    expect(noAuth.status).toBe(401);

    const withAuth = await gateway.app.request('/api/v1/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: 'Bearer it-key-1' },
      body: JSON.stringify({ skillId: 'AUTH-001', params: { text: 'x' } }),
    });
    expect(withAuth.status).toBe(200);

    // GET 端点不受 write 模式影响
    const list = await gateway.app.request('/api/v1/skills');
    expect(list.status).toBe(200);
  });

  it('write 模式 + 未配置 key：POST 返回 503 fail-closed', async () => {
    const registry = new SkillRegistry();
    registry.register(makeSkill());
    const gateway = new SkillGateway(
      { registry, loader: new SkillLoader(registry, { rootDir: './skills' }), executor: new SkillExecutor(registry) },
      { apiKeys: [] }
    );
    const res = await gateway.app.request('/api/v1/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ skillId: 'AUTH-001', params: {} }),
    });
    expect(res.status).toBe(503);
    const body = await res.json();
    expect(body.error.code).toBe('AUTH_SERVICE_DISABLED');
  });

  it('rateLimiter 中间件暴露 close 方法（资源释放）', async () => {
    const limiter = rateLimiter({ windowMs: 1000, maxRequests: 5 });
    expect(typeof limiter.close).toBe('function');
    await expect(limiter.close()).resolves.toBeUndefined();
  });

  it('限流响应头包含 backend 标识', async () => {
    const registry = new SkillRegistry();
    const gateway = new SkillGateway(
      { registry, loader: new SkillLoader(registry, { rootDir: './skills' }), executor: new SkillExecutor(registry) },
      { apiKeys: ['k'] }
    );
    const res = await gateway.app.request('/api/v1/skills');
    expect(res.headers.get('x-ratelimit-backend')).toBe('memory');
  });
});
