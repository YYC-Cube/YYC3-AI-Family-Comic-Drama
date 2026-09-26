/**
 * @yyc3/store — 内存实现（默认，零依赖；进程重启即失，测试与降级用）
 */
import type { Store } from './types.js';

export class MemoryStore implements Store {
  private map = new Map<string, string>();

  async get(key: string): Promise<string | undefined> {
    return this.map.get(key);
  }

  async put(key: string, value: string): Promise<void> {
    this.map.set(key, value);
  }

  async delete(key: string): Promise<boolean> {
    return this.map.delete(key);
  }

  async keys(prefix?: string): Promise<string[]> {
    const all = Array.from(this.map.keys());
    return prefix ? all.filter((k) => k.startsWith(prefix)) : all;
  }

  async clear(): Promise<void> {
    this.map.clear();
  }

  async close(): Promise<void> {
    this.map.clear();
  }
}
