/**
 * @yyc3/store — Redis 实现（lazy import ioredis，未安装或连接失败自动降级）
 *
 * 键统一加 `yyc3:store:` 前缀；keys() 用 SCAN 游标遍历（非阻塞），
 * 不用 KEYS（O(N) 阻塞主线程）。
 */
import { setTimeout as sleep } from 'node:timers/promises';
import type { Store } from './types.js';

const KEY_PREFIX = 'yyc3:store:';
const RETRY_DELAYS_MS = [100, 200, 400];

/** Redis 客户端最小接口（避免引入 ioredis 类型依赖） */
interface RedisClient {
  get(key: string): Promise<string | null>;
  set(key: string, value: string): Promise<unknown>;
  del(key: string): Promise<number>;
  scan(cursor: string, matchToken: 'MATCH', pattern: string, countToken: 'COUNT', count: number): Promise<[string, string[]]>;
  quit(): Promise<unknown>;
}

export class RedisStore implements Store {
  private client: RedisClient | undefined;
  private ready = false;
  /** 降级原因（诊断用） */
  degradedReason = '';

  private constructor() { }

  /** 连接 Redis；最多重试 3 次（指数退避），失败后由调用方降级其他实现 */
  static async connect(url: string): Promise<RedisStore> {
    const store = new RedisStore();
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
        const raw = new RedisCtor(url, {
          lazyConnect: false,
          maxRetriesPerRequest: 1,
          connectTimeout: 2000,
          enableOfflineQueue: false,
          retryStrategy: () => null,
        }) as RedisClient & { on(ev: string, fn: () => void): void };
        raw.on('error', () => {
          // 忽略连接错误事件，由首个命令探测决定可用性
        });
        await raw.get(`${KEY_PREFIX}__probe__`);
        store.client = raw;
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

  private requireClient(): RedisClient {
    if (!this.ready || !this.client) {
      throw new Error('RedisStore not ready');
    }
    return this.client;
  }

  async get(key: string): Promise<string | undefined> {
    const v = await this.requireClient().get(KEY_PREFIX + key);
    return v === null ? undefined : v;
  }

  async put(key: string, value: string): Promise<void> {
    await this.requireClient().set(KEY_PREFIX + key, value);
  }

  async delete(key: string): Promise<boolean> {
    return (await this.requireClient().del(KEY_PREFIX + key)) > 0;
  }

  async keys(prefix?: string): Promise<string[]> {
    const c = this.requireClient();
    const pattern = `${KEY_PREFIX}${prefix ?? ''}*`;
    const found: string[] = [];
    let cursor = '0';
    do {
      const [next, batch] = await c.scan(cursor, 'MATCH', pattern, 'COUNT', 100);
      cursor = next;
      for (const k of batch) found.push(k.slice(KEY_PREFIX.length));
    } while (cursor !== '0');
    return found;
  }

  async clear(): Promise<void> {
    const all = await this.keys();
    const c = this.requireClient();
    for (const k of all) {
      await c.del(KEY_PREFIX + k);
    }
  }

  async close(): Promise<void> {
    if (this.client) {
      await this.client.quit().catch(() => undefined);
      this.client = undefined;
      this.ready = false;
    }
  }
}
