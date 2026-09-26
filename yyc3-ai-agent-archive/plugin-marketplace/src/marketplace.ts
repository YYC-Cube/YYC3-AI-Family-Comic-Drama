/**
 * Plugin Marketplace 运行时 — 插件注册、发现、安装、生命周期管理
 *
 * 核心能力：
 * - 插件注册表（内存索引）
 * - 语义化版本匹配
 * - 依赖解析 & 冲突检测
 * - 安装/卸载/更新/激活/停用
 * - 事件驱动
 */
import { EventEmitter } from 'eventemitter3';
import { satisfies, valid } from 'semver';
import type {
  InstalledPlugin,
  MarketplaceConfig,
  MarketplaceEvents,
  PluginInstallOptions,
  PluginManifest,
  PluginSearchOptions,
  PluginUpdateOptions
} from './types.js';

const DEFAULT_CONFIG: MarketplaceConfig = {
  rootDir: './plugins',
  autoActivate: true,
};

export class PluginMarketplace extends EventEmitter<MarketplaceEvents> {
  readonly config: MarketplaceConfig;
  /** 注册表: id → InstalledPlugin */
  private plugins = new Map<string, InstalledPlugin>();
  /** 写穿持久化在飞写入集合（flushPending 等待用） */
  private pendingWrites = new Set<Promise<unknown>>();

  constructor(config: Partial<MarketplaceConfig> = {}) {
    super();
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /** 写穿持久化：fire-and-forget，失败仅告警；成功/失败都从 pending 移除 */
  private persist(pluginId: string, plugin: InstalledPlugin): void {
    const store = this.config.store;
    if (!store) return;
    const write = store
      .put(`plugin:${pluginId}`, JSON.stringify(plugin))
      .catch((err: unknown) => {
        console.warn(`[Marketplace] persist '${pluginId}' failed:`, err instanceof Error ? err.message : err);
      })
      .finally(() => {
        this.pendingWrites.delete(write);
      });
    this.pendingWrites.add(write);
  }

  private unpersist(pluginId: string): void {
    this.config.store?.delete(`plugin:${pluginId}`).catch(() => { });
  }

  /**
   * 从持久化存储恢复插件注册表（启动时调用一次）。
   * 已在内存中的同名插件不覆盖；返回恢复数量。
   */
  async restore(): Promise<number> {
    const store = this.config.store;
    if (!store) return 0;
    const keys = await store.keys('plugin:');
    let restored = 0;
    for (const key of keys) {
      const id = key.slice('plugin:'.length);
      if (this.plugins.has(id)) continue;
      try {
        const raw = await store.get(key);
        if (!raw) continue;
        const plugin = JSON.parse(raw) as InstalledPlugin;
        this.plugins.set(id, plugin);
        restored += 1;
      } catch (err) {
        console.warn(`[Marketplace] restore '${key}' failed:`, err instanceof Error ? err.message : err);
      }
    }
    return restored;
  }

  /** 等待全部在飞持久化写入完成（优雅停机/测试确定性断言用） */
  async flushPending(): Promise<void> {
    while (this.pendingWrites.size > 0) {
      await Promise.all(Array.from(this.pendingWrites));
    }
  }

  /** 注册插件清单到市场 */
  register(manifest: PluginManifest): InstalledPlugin {
    this.validateManifest(manifest);

    if (this.plugins.has(manifest.id)) {
      throw new Error(`Plugin '${manifest.id}' already registered`);
    }

    const plugin: InstalledPlugin = {
      manifest,
      status: this.config.autoActivate ? 'active' : 'inactive',
      installedAt: new Date().toISOString(),
      path: `${this.config.rootDir}/${manifest.id}`,
    };

    this.plugins.set(manifest.id, plugin);
    this.persist(manifest.id, plugin);
    this.emit('plugin:installed', plugin);

    if (this.config.autoActivate) {
      this.emit('plugin:activated', manifest.id);
    }

    return plugin;
  }

  /** 安装插件（支持依赖解析） */
  install(manifest: PluginManifest, options: PluginInstallOptions = {}): InstalledPlugin {
    this.validateManifest(manifest);

    const existing = this.plugins.get(manifest.id);
    if (existing && !options.force) {
      if (satisfies(existing.manifest.version, `>=${manifest.version}`)) {
        return existing;
      }
      throw new Error(`Plugin '${manifest.id}' v${existing.manifest.version} already installed. Use force=true to reinstall.`);
    }

    // 依赖检查
    if (!options.skipDependencies && manifest.dependencies) {
      for (const [depId, versionRange] of Object.entries(manifest.dependencies)) {
        const dep = this.plugins.get(depId);
        if (!dep) {
          throw new Error(`Plugin '${manifest.id}' depends on '${depId}' which is not installed`);
        }
        if (!satisfies(dep.manifest.version, versionRange)) {
          throw new Error(
            `Plugin '${manifest.id}' requires '${depId}@${versionRange}', but v${dep.manifest.version} is installed`
          );
        }
      }
    }

    const plugin: InstalledPlugin = {
      manifest,
      status: this.config.autoActivate ? 'active' : 'inactive',
      installedAt: existing?.installedAt ?? new Date().toISOString(),
      updatedAt: existing ? new Date().toISOString() : undefined,
      path: `${this.config.rootDir}/${manifest.id}`,
    };

    this.plugins.set(manifest.id, plugin);
    this.persist(manifest.id, plugin);

    if (existing) {
      this.emit('plugin:updated', plugin, existing.manifest.version);
    } else {
      this.emit('plugin:installed', plugin);
    }

    if (this.config.autoActivate) {
      this.emit('plugin:activated', manifest.id);
    }

    return plugin;
  }

  /** 更新插件 */
  update(pluginId: string, manifest: Partial<PluginManifest>, options: PluginUpdateOptions = {}): InstalledPlugin {
    const existing = this.plugins.get(pluginId);
    if (!existing) {
      throw new Error(`Plugin '${pluginId}' not found`);
    }

    const updatedManifest = { ...existing.manifest, ...manifest };
    const oldVersion = existing.manifest.version;

    // 版本检查
    if (options.version && !satisfies(updatedManifest.version, options.version)) {
      throw new Error(`Updated version ${updatedManifest.version} does not satisfy ${options.version}`);
    }

    // 依赖更新
    if (options.updateDependencies && updatedManifest.dependencies) {
      for (const [depId, versionRange] of Object.entries(updatedManifest.dependencies)) {
        const dep = this.plugins.get(depId);
        if (!dep) {
          throw new Error(`Dependency '${depId}' not found`);
        }
        if (!satisfies(dep.manifest.version, versionRange)) {
          throw new Error(`Dependency '${depId}' v${dep.manifest.version} does not satisfy ${versionRange}`);
        }
      }
    }

    this.validateManifest(updatedManifest);

    const plugin: InstalledPlugin = {
      ...existing,
      manifest: updatedManifest,
      updatedAt: new Date().toISOString(),
    };

    this.plugins.set(pluginId, plugin);
    this.persist(pluginId, plugin);
    this.emit('plugin:updated', plugin, oldVersion);
    return plugin;
  }

  /** 卸载插件 */
  remove(pluginId: string): boolean {
    const plugin = this.plugins.get(pluginId);
    if (!plugin) return false;

    // 检查是否有其他插件依赖此插件
    const dependents = this.getDependents(pluginId);
    if (dependents.length > 0) {
      throw new Error(
        `Cannot remove '${pluginId}': still required by ${dependents.join(', ')}`
      );
    }

    this.plugins.delete(pluginId);
    this.unpersist(pluginId);
    this.emit('plugin:removed', pluginId);
    this.emit('plugin:deactivated', pluginId);
    return true;
  }

  /** 激活插件 */
  activate(pluginId: string): boolean {
    const plugin = this.plugins.get(pluginId);
    if (!plugin) return false;

    // 检查依赖是否都已激活
    if (plugin.manifest.dependencies) {
      for (const depId of Object.keys(plugin.manifest.dependencies)) {
        const dep = this.plugins.get(depId);
        if (!dep || dep.status !== 'active') {
          throw new Error(`Cannot activate '${pluginId}': dependency '${depId}' is not active`);
        }
      }
    }

    plugin.status = 'active';
    this.persist(pluginId, plugin);
    this.emit('plugin:activated', pluginId);
    return true;
  }

  /** 停用插件 */
  deactivate(pluginId: string): boolean {
    const plugin = this.plugins.get(pluginId);
    if (!plugin) return false;

    // 检查是否有依赖此插件的活跃插件
    const dependents = this.getDependents(pluginId).filter(id => {
      const p = this.plugins.get(id);
      return p?.status === 'active';
    });
    if (dependents.length > 0) {
      throw new Error(
        `Cannot deactivate '${pluginId}': active dependents: ${dependents.join(', ')}`
      );
    }

    plugin.status = 'inactive';
    this.persist(pluginId, plugin);
    this.emit('plugin:deactivated', pluginId);
    return true;
  }

  /** 获取插件 */
  get(pluginId: string): InstalledPlugin | undefined {
    return this.plugins.get(pluginId);
  }

  /** 列出所有插件 */
  list(): InstalledPlugin[] {
    return Array.from(this.plugins.values());
  }

  /** 搜索插件 */
  search(options: PluginSearchOptions = {}): InstalledPlugin[] {
    let results = this.list();

    if (options.query) {
      const q = options.query.toLowerCase();
      results = results.filter(p =>
        p.manifest.id.toLowerCase().includes(q) ||
        p.manifest.name.toLowerCase().includes(q) ||
        p.manifest.description?.toLowerCase().includes(q)
      );
    }

    if (options.category) {
      results = results.filter(p => p.manifest.category === options.category);
    }

    if (options.tags?.length) {
      results = results.filter(p =>
        options.tags!.some(t => p.manifest.tags?.includes(t))
      );
    }

    if (options.status) {
      results = results.filter(p => p.status === options.status);
    }

    if (options.author) {
      results = results.filter(p => p.manifest.author === options.author);
    }

    return results;
  }

  /** 获取依赖此插件的其他插件 */
  private getDependents(pluginId: string): string[] {
    const dependents: string[] = [];
    for (const [id, plugin] of this.plugins) {
      if (plugin.manifest.dependencies?.[pluginId]) {
        dependents.push(id);
      }
    }
    return dependents;
  }

  /** 验证插件清单 */
  private validateManifest(manifest: PluginManifest): void {
    if (!manifest.id) throw new Error('Plugin manifest must have an id');
    if (!manifest.name) throw new Error('Plugin manifest must have a name');
    if (!manifest.version) throw new Error('Plugin manifest must have a version');

    if (!valid(manifest.version)) {
      throw new Error(`Invalid semver version: ${manifest.version}`);
    }

    // 检查 ID 格式: vendor/name
    if (!/^[a-z0-9_-]+\/[a-z0-9_-]+$/i.test(manifest.id)) {
      throw new Error(`Invalid plugin ID format: '${manifest.id}'. Expected format: vendor/name`);
    }
  }

  /** 获取统计信息 */
  stats(): { total: number; active: number; inactive: number; error: number } {
    const all = this.list();
    return {
      total: all.length,
      active: all.filter(p => p.status === 'active').length,
      inactive: all.filter(p => p.status === 'inactive').length,
      error: all.filter(p => p.status === 'error').length,
    };
  }
}
