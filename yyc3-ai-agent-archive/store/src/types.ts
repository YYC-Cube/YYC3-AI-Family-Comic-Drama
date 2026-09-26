/**
 * @yyc3/store — 持久化抽象层类型定义
 *
 * 面向会话/插件注册表/指标等有状态组件的统一 KV 语义：
 * 值恒为 string（调用方自行 JSON 序列化），键支持前缀扫描。
 * 适配器：MemoryStore（测试/默认）、FileStore（JSON 原子写）、RedisStore（lazy ioredis）。
 */

/** 持久化存储后端接口 — 同步语义异步化，便于横向替换实现 */
export interface Store {
  /** 读取键值；不存在返回 undefined */
  get(key: string): Promise<string | undefined>;
  /** 写入键值（覆盖） */
  put(key: string, value: string): Promise<void>;
  /** 删除键；返回是否存在 */
  delete(key: string): Promise<boolean>;
  /** 列出键（可选前缀过滤） */
  keys(prefix?: string): Promise<string[]>;
  /** 清空全部键 */
  clear(): Promise<void>;
  /** 释放后端资源（FileStore 落盘、RedisStore 断连） */
  close(): Promise<void>;
}

/** JSON 便捷读写（值序列化/反序列化由本层承担） */
export function getJson<T>(store: Store, key: string): Promise<T | undefined> {
  return store.get(key).then((raw) => (raw === undefined ? undefined : (JSON.parse(raw) as T)));
}

export async function putJson(store: Store, key: string, value: unknown): Promise<void> {
  await store.put(key, JSON.stringify(value));
}
