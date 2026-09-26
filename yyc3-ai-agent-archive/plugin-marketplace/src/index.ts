/**
 * YYC³ Plugin Marketplace 运行时
 * @module @yyc3/plugin-marketplace
 *
 * 插件生态管理引擎，支持：
 * - 插件注册 & 发现（ID/名称/分类/标签搜索）
 * - 语义化版本管理（semver）
 * - 依赖解析 & 冲突检测
 * - 安装/卸载/更新/激活/停用
 * - 事件驱动生命周期
 *
 * 使用方式：
 * ```ts
 * import { PluginMarketplace } from '@yyc3/plugin-marketplace';
 *
 * const marketplace = new PluginMarketplace({ rootDir: './plugins' });
 *
 * marketplace.on('plugin:installed', (plugin) => {
 *   console.log(`Plugin ${plugin.manifest.id} installed`);
 * });
 *
 * marketplace.install({
 *   id: 'yyc3/glm-ocr',
 *   name: 'GLM OCR',
 *   version: '1.0.0',
 *   category: 'ocr',
 *   tags: ['vision', 'ocr'],
 * });
 * ```
 */

export { PluginMarketplace } from './marketplace.js';
export type {
  PluginManifest,
  InstalledPlugin,
  PluginStatus,
  PluginSource,
  PluginSearchOptions,
  PluginInstallOptions,
  PluginUpdateOptions,
  MarketplaceConfig,
  MarketplaceEvents,
} from './types.js';