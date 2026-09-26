/**
 * Plugin Marketplace — 类型定义
 * @module @yyc3/plugin-marketplace
 */

/** 插件状态 */
export type PluginStatus = 'active' | 'inactive' | 'error' | 'installing' | 'uninstalled';

/** 插件安装来源 */
export type PluginSource = 'registry' | 'local' | 'git' | 'url';

/** 插件清单 */
export interface PluginManifest {
  /** 唯一标识，格式: vendor/name */
  id: string;
  /** 显示名称 */
  name: string;
  /** 版本，遵循 semver */
  version: string;
  /** 描述 */
  description?: string;
  /** 作者 */
  author?: string;
  /** 许可证 */
  license?: string;
  /** 分类 */
  category?: string;
  /** 标签 */
  tags?: string[];
  /** 依赖（其他插件 ID） */
  dependencies?: Record<string, string>;
  /** 入口文件 */
  entry?: string;
  /** 安装来源 */
  source?: PluginSource;
  /** 仓库地址 */
  repository?: string;
  /** 主页 */
  homepage?: string;
  /** 图标 */
  icon?: string;
  /** 自定义元数据 */
  meta?: Record<string, unknown>;
}

/** 已安装插件 */
export interface InstalledPlugin {
  manifest: PluginManifest;
  status: PluginStatus;
  /** 安装时间 */
  installedAt: string;
  /** 更新时间 */
  updatedAt?: string;
  /** 安装路径 */
  path?: string;
  /** 错误信息 */
  error?: string;
}

/** 搜索选项 */
export interface PluginSearchOptions {
  query?: string;
  category?: string;
  tags?: string[];
  status?: PluginStatus;
  author?: string;
}

/** 安装选项 */
export interface PluginInstallOptions {
  /** 是否强制重装 */
  force?: boolean;
  /** 是否跳过依赖 */
  skipDependencies?: boolean;
  /** 目标路径 */
  targetPath?: string;
}

/** 更新选项 */
export interface PluginUpdateOptions {
  /** 最新版本约束 */
  version?: string;
  /** 是否更新依赖 */
  updateDependencies?: boolean;
}

/** 市场事件 */
export interface MarketplaceEvents {
  'plugin:installed': (plugin: InstalledPlugin) => void;
  'plugin:removed': (pluginId: string) => void;
  'plugin:updated': (plugin: InstalledPlugin, oldVersion: string) => void;
  'plugin:error': (pluginId: string, error: string) => void;
  'plugin:activated': (pluginId: string) => void;
  'plugin:deactivated': (pluginId: string) => void;
}

/** 市场配置 */
export interface MarketplaceConfig {
  /** 插件安装根目录 */
  rootDir: string;
  /** 默认注册表 URL */
  registryUrl?: string;
  /** 是否自动激活 */
  autoActivate: boolean;
  /**
   * 可选持久化存储（P2）：提供后插件注册表写穿落盘，
   * restore() 可在重启后恢复（插件 manifest 均为 JSON 可序列化）。
   */
  store?: import('@yyc3/store').Store;
}