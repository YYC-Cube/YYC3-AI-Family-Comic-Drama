/**
 * @yyc3/store
 * YYC³ 持久化抽象层 — Store 接口 + 内存/文件/Redis 三适配器
 *
 * 使用方式：
 * - 测试/默认：`new MemoryStore()`
 * - 单机持久化：`new FileStore(path, { debounceMs })`（JSON 原子写）
 * - 分布式：`RedisStore.connect(url)`（失败自动降级，由调用方兜底）
 * - 环境驱动：`createStoreFromEnv()`（REDIS_URL 优先，失败/未配置降级 FileStore，STORE_MEMORY=1 强制内存）
 */
export { FileStore, type FileStoreOptions } from './file-store.js';
export { MemoryStore } from './memory-store.js';
export { RedisStore } from './redis-store.js';
export { getJson, putJson } from './types.js';
export type { Store } from './types.js';
import { FileStore } from './file-store.js';
import { MemoryStore } from './memory-store.js';
import { RedisStore } from './redis-store.js';
import type { Store } from './types.js';

/** 环境驱动的存储工厂结果 */
export interface StoreSelection {
  store: Store;
  backend: 'redis' | 'file' | 'memory';
  /** 非 backend 首选时的降级原因（诊断用） */
  degradedReason?: string;
}

/**
 * 按环境变量选择实现：
 * - `REDIS_URL` 存在且连接成功 → RedisStore；失败降级 FileStore
 * - `STORE_FILE`（默认 `.yyc3-store.json`）→ FileStore
 * - `STORE_MEMORY=1` → 强制 MemoryStore（测试隔离）
 */
export async function createStoreFromEnv(
  env: { REDIS_URL?: string; STORE_FILE?: string; STORE_MEMORY?: string } = process.env,
): Promise<StoreSelection> {
  if (env.STORE_MEMORY === '1') {
    return { store: new MemoryStore(), backend: 'memory' };
  }

  if (env.REDIS_URL) {
    const redis = await RedisStore.connect(env.REDIS_URL);
    if (redis.isReady()) {
      return { store: redis, backend: 'redis' };
    }
    await redis.close();
    return {
      store: new FileStore(env.STORE_FILE ?? '.yyc3-store.json'),
      backend: 'file',
      degradedReason: redis.degradedReason,
    };
  }

  return { store: new FileStore(env.STORE_FILE ?? '.yyc3-store.json'), backend: 'file' };
}
