/// <reference types="node" />
/**
 * @yyc3/store — 持久化抽象层测试
 *
 * 覆盖：接口契约（Memory/File 双实现一致性）、FileStore 原子落盘与重载、
 * RedisStore 未安装降级路径、createStoreFromEnv 环境选择、getJson/putJson。
 */
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import {
  createStoreFromEnv,
  FileStore,
  getJson,
  MemoryStore,
  putJson,
  RedisStore,
  type Store,
} from '../src/index.js';

/** 接口契约：所有实现必须通过（新适配器接入时在此登记） */
function contract(name: string, make: () => Promise<Store> | Store) {
  describe(`接口契约 — ${name}`, () => {
    let store: Store;
    beforeEach(async () => {
      store = await make();
    });
    afterEach(async () => {
      await store.close();
    });

    it('put/get 往返', async () => {
      await store.put('k1', 'v1');
      expect(await store.get('k1')).toBe('v1');
    });

    it('get 不存在的键返回 undefined', async () => {
      expect(await store.get('nope')).toBeUndefined();
    });

    it('put 覆盖旧值', async () => {
      await store.put('k', 'a');
      await store.put('k', 'b');
      expect(await store.get('k')).toBe('b');
    });

    it('delete 返回是否删除成功', async () => {
      await store.put('k', 'v');
      expect(await store.delete('k')).toBe(true);
      expect(await store.delete('k')).toBe(false);
      expect(await store.get('k')).toBeUndefined();
    });

    it('keys 支持前缀过滤与全量', async () => {
      await store.put('agent:1', 'a');
      await store.put('agent:2', 'b');
      await store.put('plugin:x', 'c');
      expect((await store.keys('agent:')).sort()).toEqual(['agent:1', 'agent:2']);
      expect((await store.keys()).sort()).toEqual(['agent:1', 'agent:2', 'plugin:x']);
    });

    it('clear 清空全部', async () => {
      await store.put('a', '1');
      await store.put('b', '2');
      await store.clear();
      expect(await store.keys()).toEqual([]);
    });
  });
}

contract('MemoryStore', () => new MemoryStore());

describe('FileStore', () => {
  let dir: string;
  let file: string;

  beforeEach(async () => {
    dir = await mkdtemp(join(tmpdir(), 'yyc3-store-'));
    file = join(dir, 'state.json');
  });

  afterEach(async () => {
    await rm(dir, { recursive: true, force: true });
  });

  contract('FileStore', () => new FileStore(file, { debounceMs: 0 }));

  it('close 后数据落盘，新实例可恢复（重启即失 → 重启可恢复）', async () => {
    const s1 = new FileStore(file, { debounceMs: 1000 });
    await s1.put('agent:a1', '{"status":"idle"}');
    await s1.put('agent:a2', '{"status":"thinking"}');
    await s1.delete('agent:a2');
    await s1.close(); // 强制 flush

    const s2 = new FileStore(file);
    expect(await s2.get('agent:a1')).toBe('{"status":"idle"}');
    expect(await s2.get('agent:a2')).toBeUndefined();
    expect(await s2.keys('agent:')).toEqual(['agent:a1']);
    await s2.close();
  });

  it('落盘为合法 JSON 快照（原子写的最终态）', async () => {
    const s = new FileStore(file, { debounceMs: 0 });
    await s.put('k', 'v');
    await s.close();
    const raw = JSON.parse(await readFile(file, 'utf-8')) as Record<string, string>;
    expect(raw.k).toBe('v');
  });

  it('损坏快照视为空库而非崩溃', async () => {
    const { writeFile } = await import('node:fs/promises');
    await writeFile(file, '{broken json', 'utf-8');
    const s = new FileStore(file);
    expect(await s.get('k')).toBeUndefined();
    await s.close();
  });

  it('防抖窗口内多次写合并为一次落盘', async () => {
    const s = new FileStore(file, { debounceMs: 50 });
    for (let i = 0; i < 10; i++) {
      await s.put(`k${i}`, String(i));
    }
    await s.close();
    const s2 = new FileStore(file);
    expect((await s2.keys()).length).toBe(10);
    await s2.close();
  });
});

describe('RedisStore（未安装/不可达降级路径）', () => {
  it('连接不可达地址后 isReady=false 且带降级原因', async () => {
    // 127.0.0.1:1 保留端口，连接必然快速失败（重试 3 次后返回）
    const s = await RedisStore.connect('redis://127.0.0.1:1');
    expect(s.isReady()).toBe(false);
    expect(s.degradedReason.length).toBeGreaterThan(0);
    await s.close();
  }, 10_000);

  it('未就绪时操作抛错（由调用方降级，不静默）', async () => {
    const s = await RedisStore.connect('redis://127.0.0.1:1');
    await expect(s.get('k')).rejects.toThrow('not ready');
    await s.close();
  }, 10_000);
});

describe('createStoreFromEnv', () => {
  it('STORE_MEMORY=1 强制内存实现', async () => {
    const sel = await createStoreFromEnv({ STORE_MEMORY: '1' });
    expect(sel.backend).toBe('memory');
    await sel.store.close();
  });

  it('无 REDIS_URL 时默认 FileStore（文件可指定）', async () => {
    const dir = await mkdtemp(join(tmpdir(), 'yyc3-store-env-'));
    const sel = await createStoreFromEnv({ STORE_FILE: join(dir, 's.json') });
    expect(sel.backend).toBe('file');
    await sel.store.put('k', 'v');
    await sel.store.close();
    await rm(dir, { recursive: true, force: true });
  });

  it('REDIS_URL 不可达时降级 File 并附原因', async () => {
    const dir = await mkdtemp(join(tmpdir(), 'yyc3-store-env-'));
    const sel = await createStoreFromEnv({
      REDIS_URL: 'redis://127.0.0.1:1',
      STORE_FILE: join(dir, 's.json'),
    });
    expect(sel.backend).toBe('file');
    expect(sel.degradedReason).toBeTruthy();
    await sel.store.close();
    await rm(dir, { recursive: true, force: true });
  }, 10_000);
});

describe('JSON 便捷读写', () => {
  it('putJson/getJson 对象往返', async () => {
    const s = new MemoryStore();
    await putJson(s, 'obj', { a: 1, nested: { b: [1, 2] } });
    expect(await getJson<{ a: number; nested: { b: number[] } }>(s, 'obj')).toEqual({
      a: 1,
      nested: { b: [1, 2] },
    });
    // 底层仍是 string
    expect(typeof (await s.get('obj'))).toBe('string');
  });

  it('getJson 不存在的键返回 undefined', async () => {
    const s = new MemoryStore();
    expect(await getJson(s, 'nope')).toBeUndefined();
  });
});
