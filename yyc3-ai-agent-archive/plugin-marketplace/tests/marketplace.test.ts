/**
 * Plugin Marketplace — 单元测试
 */
import { beforeEach, describe, expect, it } from 'vitest';
import { PluginMarketplace } from '../src/index.js';
import type { PluginManifest } from '../src/types.js';

function makePlugin(overrides: Partial<PluginManifest> = {}): PluginManifest {
  return {
    id: 'yyc3/test-plugin',
    name: 'Test Plugin',
    version: '1.0.0',
    description: 'A test plugin',
    category: 'testing',
    tags: ['test'],
    ...overrides,
  };
}

describe('PluginMarketplace', () => {
  let marketplace: PluginMarketplace;

  beforeEach(() => {
    marketplace = new PluginMarketplace({ rootDir: './test-plugins', autoActivate: true });
  });

  describe('register', () => {
    it('注册插件', () => {
      const plugin = marketplace.register(makePlugin());
      expect(plugin.status).toBe('active');
      expect(plugin.manifest.id).toBe('yyc3/test-plugin');
      expect(marketplace.get('yyc3/test-plugin')).toBeDefined();
    });

    it('重复注册失败', () => {
      marketplace.register(makePlugin());
      expect(() => marketplace.register(makePlugin())).toThrow('already registered');
    });

    it('无效 ID 格式', () => {
      expect(() => marketplace.register(makePlugin({ id: 'invalid-id' }))).toThrow('Invalid plugin ID');
    });

    it('无效版本号', () => {
      expect(() => marketplace.register(makePlugin({ version: 'not-semver' }))).toThrow('Invalid semver');
    });
  });

  describe('install', () => {
    it('安装插件', () => {
      const plugin = marketplace.install(makePlugin());
      expect(plugin.status).toBe('active');
    });

    it('安装已存在插件 - 相同版本', () => {
      marketplace.install(makePlugin());
      const plugin = marketplace.install(makePlugin());
      expect(plugin.manifest.version).toBe('1.0.0');
    });

    it('安装已存在插件 - 旧版本', () => {
      marketplace.install(makePlugin({ version: '2.0.0' }));
      const plugin = marketplace.install(makePlugin({ version: '1.0.0' }));
      expect(plugin.manifest.version).toBe('2.0.0');
    });

    it('强制重装', () => {
      marketplace.install(makePlugin({ version: '1.0.0' }));
      const plugin = marketplace.install(
        makePlugin({ version: '2.0.0' }),
        { force: true }
      );
      expect(plugin.manifest.version).toBe('2.0.0');
    });

    it('依赖检查 - 缺失依赖', () => {
      expect(() =>
        marketplace.install(makePlugin({
          id: 'yyc3/consumer',
          dependencies: { 'yyc3/missing': '^1.0.0' },
        }))
      ).toThrow('depends on');
    });

    it('依赖检查 - 版本不满足', () => {
      marketplace.install(makePlugin({ id: 'yyc3/dep', version: '1.0.0' }));
      expect(() =>
        marketplace.install(makePlugin({
          id: 'yyc3/consumer',
          dependencies: { 'yyc3/dep': '^2.0.0' },
        }))
      ).toThrow('requires');
    });

    it('依赖检查 - 版本满足', () => {
      marketplace.install(makePlugin({ id: 'yyc3/dep', version: '1.5.0' }));
      const plugin = marketplace.install(makePlugin({
        id: 'yyc3/consumer',
        dependencies: { 'yyc3/dep': '^1.0.0' },
      }));
      expect(plugin.status).toBe('active');
    });

    it('跳过依赖检查', () => {
      const plugin = marketplace.install(
        makePlugin({
          dependencies: { 'yyc3/missing': '^1.0.0' },
        }),
        { skipDependencies: true }
      );
      expect(plugin.status).toBe('active');
    });
  });

  describe('update', () => {
    it('更新插件', () => {
      marketplace.install(makePlugin());
      const updated = marketplace.update('yyc3/test-plugin', { version: '2.0.0' });
      expect(updated.manifest.version).toBe('2.0.0');
    });

    it('更新不存在的插件', () => {
      expect(() => marketplace.update('yyc3/nonexistent', { version: '2.0.0' })).toThrow('not found');
    });
  });

  describe('remove', () => {
    it('卸载插件', () => {
      marketplace.install(makePlugin());
      expect(marketplace.remove('yyc3/test-plugin')).toBe(true);
      expect(marketplace.get('yyc3/test-plugin')).toBeUndefined();
    });

    it('卸载不存在的插件', () => {
      expect(marketplace.remove('yyc3/nonexistent')).toBe(false);
    });

    it('被依赖时不能卸载', () => {
      marketplace.install(makePlugin({ id: 'yyc3/dep' }));
      marketplace.install(makePlugin({
        id: 'yyc3/consumer',
        dependencies: { 'yyc3/dep': '^1.0.0' },
      }));
      expect(() => marketplace.remove('yyc3/dep')).toThrow('still required');
    });
  });

  describe('activate/deactivate', () => {
    it('停用插件', () => {
      marketplace.install(makePlugin());
      expect(marketplace.deactivate('yyc3/test-plugin')).toBe(true);
      expect(marketplace.get('yyc3/test-plugin')?.status).toBe('inactive');
    });

    it('重新激活', () => {
      marketplace.install(makePlugin());
      marketplace.deactivate('yyc3/test-plugin');
      expect(marketplace.activate('yyc3/test-plugin')).toBe(true);
      expect(marketplace.get('yyc3/test-plugin')?.status).toBe('active');
    });

    it('依赖未激活时不能激活', () => {
      marketplace.install(makePlugin({ id: 'yyc3/dep' }));
      marketplace.install(makePlugin({
        id: 'yyc3/consumer',
        dependencies: { 'yyc3/dep': '^1.0.0' },
      }));
      marketplace.deactivate('yyc3/consumer');
      marketplace.deactivate('yyc3/dep');
      expect(() => marketplace.activate('yyc3/consumer')).toThrow('not active');
    });

    it('被依赖时不能停用', () => {
      marketplace.install(makePlugin({ id: 'yyc3/dep' }));
      marketplace.install(makePlugin({
        id: 'yyc3/consumer',
        dependencies: { 'yyc3/dep': '^1.0.0' },
      }));
      expect(() => marketplace.deactivate('yyc3/dep')).toThrow('active dependents');
    });
  });

  describe('search', () => {
    beforeEach(() => {
      marketplace.install(makePlugin({ id: 'yyc3/plugin-a', name: 'Alpha', category: 'ai', tags: ['ocr'] }));
      marketplace.install(makePlugin({ id: 'yyc3/plugin-b', name: 'Beta', category: 'data', tags: ['db'] }));
      marketplace.install(makePlugin({ id: 'yyc3/plugin-c', name: 'Gamma', category: 'ai', tags: ['ocr', 'vision'] }));
    });

    it('按名称搜索', () => {
      const results = marketplace.search({ query: 'alpha' });
      expect(results).toHaveLength(1);
      expect(results[0].manifest.id).toBe('yyc3/plugin-a');
    });

    it('按分类搜索', () => {
      const results = marketplace.search({ category: 'ai' });
      expect(results).toHaveLength(2);
    });

    it('按标签搜索', () => {
      const results = marketplace.search({ tags: ['ocr'] });
      expect(results).toHaveLength(2);
    });

    it('组合搜索', () => {
      const results = marketplace.search({ category: 'ai', tags: ['vision'] });
      expect(results).toHaveLength(1);
      expect(results[0].manifest.id).toBe('yyc3/plugin-c');
    });
  });

  describe('stats', () => {
    it('返回统计信息', () => {
      marketplace.install(makePlugin({ id: 'yyc3/a' }));
      marketplace.install(makePlugin({ id: 'yyc3/b' }));
      marketplace.deactivate('yyc3/b');

      const stats = marketplace.stats();
      expect(stats.total).toBe(2);
      expect(stats.active).toBe(1);
      expect(stats.inactive).toBe(1);
    });
  });

  describe('events', () => {
    it('触发安装事件', () => {
      const events: string[] = [];
      marketplace.on('plugin:installed', (p) => events.push(p.manifest.id));
      marketplace.on('plugin:activated', (id) => events.push(`activated:${id}`));

      marketplace.install(makePlugin({ id: 'yyc3/evt' }));

      expect(events).toContain('yyc3/evt');
      expect(events).toContain('activated:yyc3/evt');
    });

    it('触发移除事件', () => {
      const events: string[] = [];
      marketplace.on('plugin:removed', (id) => events.push(id));
      marketplace.on('plugin:deactivated', (id) => events.push(`deactivated:${id}`));

      marketplace.install(makePlugin({ id: 'yyc3/evt' }));
      marketplace.remove('yyc3/evt');

      expect(events).toContain('yyc3/evt');
      expect(events).toContain('deactivated:yyc3/evt');
    });

    it('触发更新事件', () => {
      const events: string[] = [];
      marketplace.on('plugin:updated', (p, oldVer) => {
        events.push(`updated:${p.manifest.id}:${oldVer}→${p.manifest.version}`);
      });

      marketplace.install(makePlugin({ id: 'yyc3/evt', version: '1.0.0' }));
      marketplace.update('yyc3/evt', { version: '2.0.0' });

      expect(events).toContain('updated:yyc3/evt:1.0.0→2.0.0');
    });
  });

  // P2：可选 Store 持久化 — 注册表写穿 + restore 重启恢复
  describe('store 持久化', () => {
    it('install/activate 状态写穿，新实例 restore 恢复', async () => {
      const { FileStore } = await import('@yyc3/store');
      const { mkdtemp, rm } = await import('node:fs/promises');
      const { tmpdir } = await import('node:os');
      const { join } = await import('node:path');

      const dir = await mkdtemp(join(tmpdir(), 'yyc3-pm-store-'));
      const file = join(dir, 'plugins.json');

      const s1 = new FileStore(file, { debounceMs: 0 });
      const m1 = new PluginMarketplace({ rootDir: './p', autoActivate: false, store: s1 });
      m1.install(makePlugin({ id: 'yyc3/persisted' }));
      m1.activate('yyc3/persisted');
      await m1.flushPending();
      await s1.close();

      // 模拟重启
      const s2 = new FileStore(file, { debounceMs: 0 });
      const m2 = new PluginMarketplace({ rootDir: './p', store: s2 });
      const restored = await m2.restore();
      expect(restored).toBe(1);
      const p = m2.get('yyc3/persisted');
      expect(p).toBeDefined();
      expect(p!.status).toBe('active'); // activate 状态也已落盘
      expect(p!.manifest.version).toBe('1.0.0');
      await s2.close();
      await rm(dir, { recursive: true, force: true });
    });

    it('remove 同步删除持久化键，restore 后不再出现', async () => {
      const { FileStore } = await import('@yyc3/store');
      const { mkdtemp, rm } = await import('node:fs/promises');
      const { tmpdir } = await import('node:os');
      const { join } = await import('node:path');

      const dir = await mkdtemp(join(tmpdir(), 'yyc3-pm-store-'));
      const file = join(dir, 'plugins.json');

      const s = new FileStore(file, { debounceMs: 0 });
      const m = new PluginMarketplace({ rootDir: './p', store: s });
      m.install(makePlugin({ id: 'yyc3/temp' }));
      await m.flushPending();
      m.remove('yyc3/temp');
      await new Promise((r) => setTimeout(r, 20));
      await s.close();

      const s2 = new FileStore(file, { debounceMs: 0 });
      const m2 = new PluginMarketplace({ rootDir: './p', store: s2 });
      expect(await m2.restore()).toBe(0);
      expect(m2.get('yyc3/temp')).toBeUndefined();
      await s2.close();
      await rm(dir, { recursive: true, force: true });
    });

    it('未配置 store 时 restore 返回 0（零开销禁用）', async () => {
      const m = new PluginMarketplace({ rootDir: './p' });
      expect(await m.restore()).toBe(0);
    });
  });
});
