/**
 * Skill Gateway — 限流存储抽象
 *
 * 提供 Token Bucket 的可插拔存储后端：
 * - MemoryStore：单进程内存态（默认，零依赖）
 * - RedisStore：基于 REDIS_URL 的分布式实现（lazy import ioredis，未安装或连接失败自动降级）
 */
import { setTimeout as sleep } from 'node:timers/promises';

/** 桶状态：令牌数 + 上次补充时间戳 */
export interface Bucket {
  tokens: number;
  lastRefill: number;
}

/** 限流存储后端接口 — 原子化「读取-补充-扣减」 */
export interface RateLimitStore {
  /** 原子扣减 1 个令牌，返回扣减后的桶状态；令牌不足时 tokens 为负 */
  consume(key: string, config: { windowMs: number; maxRequests: number }): Promise<Bucket>;
  /** 释放后端资源 */
  close(): Promise<void>;
}

// ================================================================
// 内存实现（单进程）
// ================================================================

export class MemoryStore implements RateLimitStore {
  private buckets = new Map<string, Bucket>();
  private cleanupInterval: NodeJS.Timeout;

  constructor(windowMs: number) {
    // 定期清理过期桶，防止内存泄漏
    this.cleanupInterval = setInterval(() => {
      const now = Date.now();
      for (const [key, bucket] of this.buckets) {
        if (now - bucket.lastRefill > windowMs * 2) {
          this.buckets.delete(key);
        }
      }
    }, windowMs * 5);
    if (this.cleanupInterval.unref) this.cleanupInterval.unref();
  }

  async consume(
    key: string,
    config: { windowMs: number; maxRequests: number }
  ): Promise<Bucket> {
    const now = Date.now();
    let bucket = this.buckets.get(key);

    if (!bucket) {
      bucket = { tokens: config.maxRequests, lastRefill: now };
      this.buckets.set(key, bucket);
    }

    const elapsed = now - bucket.lastRefill;
    const refillTokens = (elapsed / config.windowMs) * config.maxRequests;
    bucket.tokens = Math.min(config.maxRequests, bucket.tokens + refillTokens);
    bucket.lastRefill = now;
    bucket.tokens -= 1;

    return { tokens: bucket.tokens, lastRefill: bucket.lastRefill };
  }

  async close(): Promise<void> {
    clearInterval(this.cleanupInterval);
    this.buckets.clear();
  }
}

// ================================================================
// Redis 实现（分布式，lazy import + 降级）
// ================================================================

const RETRY_DELAYS_MS = [100, 200, 400];

export class RedisStore implements RateLimitStore {
  private client: unknown;
  private ready = false;
  /** 降级原因（诊断用） */
  degradedReason = '';

  private constructor() {}

  /**
   * 连接 Redis；最多重试 3 次（指数退避），失败后由调用方降级 MemoryStore
   */
  static async connect(url: string): Promise<RedisStore> {
    const store = new RedisStore();
    // lazy import：ioredis 为可选依赖，未安装时降级
    let RedisCtor: (new (url: string, opts?: unknown) => unknown) | undefined;
    try {
      const mod = (await import('ioredis')) as { default: new (u: string, o?: unknown) => unknown };
      RedisCtor = mod.default;
    } catch {
      store.degradedReason = 'ioredis not installed';
      return store;
    }

    for (const delay of RETRY_DELAYS_MS) {
      try {
        const client = new RedisCtor(url, {
          lazyConnect: false,
          maxRetriesPerRequest: 1,
          connectTimeout: 2000,
          // 快速失败：连接失败时命令直接 reject，而非挂入 offline queue 永久等待
          enableOfflineQueue: false,
          retryStrategy: () => null,
        });
        const c = client as { ping(): Promise<string>; on(ev: string, fn: () => void): void; disconnect(): void };
        c.on('error', () => {
          // 忽略连接错误事件，由 ping 探测决定可用性
        });
        await c.ping();
        store.client = client;
        store.ready = true;
        return store;
      } catch (err) {
        store.degradedReason = err instanceof Error ? err.message : String(err);
        await sleep(delay);
      }
    }
    return store;
  }

  isReady(): boolean {
    return this.ready;
  }

  async consume(
    key: string,
    config: { windowMs: number; maxRequests: number }
  ): Promise<Bucket> {
    if (!this.ready || !this.client) {
      throw new Error('RedisStore not ready');
    }
    const c = this.client as {
      eval(script: string, numKeys: number, key: string, ...args: (number | string)[]): Promise<[number, number]>;
    };
    // Lua 原子脚本：读取 → 按时间补充 → 扣减 → 回写
    const script = `
      local t = tonumber(redis.call('hget', KEYS[1], 'tokens') or '-1')
      local last = tonumber(redis.call('hget', KEYS[1], 'last') or '0')
      local now = tonumber(ARGV[1])
      local window = tonumber(ARGV[2])
      local max = tonumber(ARGV[3])
      if t < 0 then
        t = max
        last = now
      end
      local refill = ((now - last) / window) * max
      t = math.min(max, t + refill)
      last = now
      t = t - 1
      redis.call('hset', KEYS[1], 'tokens', t, 'last', last)
      redis.call('pexpire', KEYS[1], window * 2)
      return {t, last}
    `;
    const [tokens, last] = await c.eval(
      script,
      1,
      `yyc3:ratelimit:${key}`,
      Date.now(),
      config.windowMs,
      config.maxRequests
    );
    return { tokens, lastRefill: last };
  }

  async close(): Promise<void> {
    if (this.client) {
      (this.client as { disconnect(): void }).disconnect();
      this.client = undefined;
      this.ready = false;
    }
  }
}

/**
 * 存储工厂：REDIS_URL 存在且连接成功 → RedisStore；否则 → MemoryStore 降级
 */
export async function createRateLimitStore(
  windowMs: number
): Promise<{ store: RateLimitStore; backend: 'redis' | 'memory'; degradedReason?: string }> {
  const redisUrl = process.env.REDIS_URL;
  if (redisUrl) {
    const redis = await RedisStore.connect(redisUrl);
    if (redis.isReady()) {
      return { store: redis, backend: 'redis' };
    }
    await redis.close();
    return { store: new MemoryStore(windowMs), backend: 'memory', degradedReason: redis.degradedReason };
  }
  return { store: new MemoryStore(windowMs), backend: 'memory' };
}
