/**
 * @yyc3/store — 文件实现（单文件 JSON，原子写 + 防抖落盘）
 *
 * 读写均在内存 Map 上进行（同步快），写入后按 debounceMs 防抖合并落盘；
 * 落盘走 tmp 文件 + rename，保证任意时刻磁盘上要么是旧快照要么是新快照。
 * close() 强制 flush，保证进程退出前数据不丢。
 */
import { mkdir, readFile, rename, writeFile } from 'node:fs/promises';
import { dirname } from 'node:path';
import type { Store } from './types.js';

export interface FileStoreOptions {
  /** 写后防抖落盘间隔（默认 100ms；0 = 每次写立即落盘） */
  debounceMs?: number;
}

export class FileStore implements Store {
  private readonly file: string;
  private readonly debounceMs: number;
  private map = new Map<string, string>();
  private dirty = false;
  private loadPromise: Promise<void> | undefined;
  private timer: ReturnType<typeof setTimeout> | undefined;
  private flushing: Promise<void> = Promise.resolve();

  constructor(file: string, options: FileStoreOptions = {}) {
    this.file = file;
    this.debounceMs = options.debounceMs ?? 100;
  }

  /** 首次访问时从磁盘加载快照（单例 promise：并发 put 不会乱序覆盖） */
  private ensureLoaded(): Promise<void> {
    this.loadPromise ??= this.doLoad();
    return this.loadPromise;
  }

  private async doLoad(): Promise<void> {
    try {
      const raw = await readFile(this.file, 'utf-8');
      const parsed = JSON.parse(raw) as Record<string, string>;
      if (parsed && typeof parsed === 'object') {
        for (const [k, v] of Object.entries(parsed)) {
          this.map.set(k, v);
        }
      }
    } catch {
      // 文件不存在或损坏：视为空库（新实例的正常路径）
    }
  }

  async get(key: string): Promise<string | undefined> {
    await this.ensureLoaded();
    return this.map.get(key);
  }

  async put(key: string, value: string): Promise<void> {
    await this.ensureLoaded();
    this.map.set(key, value);
    this.scheduleFlush();
  }

  async delete(key: string): Promise<boolean> {
    await this.ensureLoaded();
    const deleted = this.map.delete(key);
    if (deleted) this.scheduleFlush();
    return deleted;
  }

  async keys(prefix?: string): Promise<string[]> {
    await this.ensureLoaded();
    const all = Array.from(this.map.keys());
    return prefix ? all.filter((k) => k.startsWith(prefix)) : all;
  }

  async clear(): Promise<void> {
    await this.ensureLoaded();
    this.map.clear();
    this.scheduleFlush();
  }

  /** 立即落盘（close 前调用，亦可在检查点显式调用） */
  async flush(): Promise<void> {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = undefined;
    }
    if (!this.dirty) return;
    // 串行化 flush，避免并发写同一 tmp 文件
    this.flushing = this.flushing.then(() => this.writeSnapshot());
    await this.flushing;
  }

  async close(): Promise<void> {
    await this.flush();
  }

  private scheduleFlush(): void {
    this.dirty = true;
    if (this.debounceMs <= 0) {
      void this.flush();
      return;
    }
    if (this.timer) clearTimeout(this.timer);
    this.timer = setTimeout(() => {
      this.timer = undefined;
      void this.flush();
    }, this.debounceMs);
    // 不阻止进程退出
    if (this.timer.unref) this.timer.unref();
  }

  private async writeSnapshot(): Promise<void> {
    const snapshot: Record<string, string> = {};
    for (const [k, v] of this.map) snapshot[k] = v;
    const tmp = `${this.file}.tmp-${process.pid}-${Date.now()}`;
    await mkdir(dirname(this.file), { recursive: true });
    await writeFile(tmp, JSON.stringify(snapshot), 'utf-8');
    await rename(tmp, this.file);
    this.dirty = false;
  }
}
