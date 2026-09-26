/**
 * @description YYC³ Skill 文件系统加载器
 * @module @yyc3/skill-registry/loader
 *
 * 从文件系统自动扫描、解析、注册 Skill。
 * 支持 Markdown SKILL.md frontmatter 和 JSON 清单。
 */

import { existsSync, readdirSync, readFileSync, statSync } from 'fs';
import { basename, join } from 'path';
import type { Frontmatter } from './frontmatter.js';
import {
  parseFrontmatter,
  toString,
  toStringArray,
} from './frontmatter.js';
import type { SkillRegistry } from './registry.js';
import type { SkillDomain, SkillRuntime, SkillType, UnifiedSkill } from './types.js';
import type { ValidationIssue } from './validator.js';
import { validateUnifiedSkill } from './validator.js';

// 向后兼容导出：frontmatter 解析已迁移至独立模块
export { parseFrontmatter } from './frontmatter.js';

// ==================== Skill 清单解析 ====================

export interface SkillManifest {
  id?: string;
  name?: string;
  description?: string;
  domain?: string;
  type?: string;
  runtime?: string;
  entry?: string;
  fallback?: string;
  tags?: string[];
  version?: string;
  status?: string;
  /** AYNC 分类编码（如 development-code） */
  category?: string;
  /** 允许使用的工具列表 */
  allowedTools?: string[];
}

/**
 * 将 frontmatter 映射到 SkillManifest
 */
export function frontmatterToManifest(
  fm: Frontmatter,
  dirName: string
): SkillManifest {
  return {
    id: toString(fm['id']) || toString(fm['name']) || dirName,
    name: toString(fm['name']) || toString(fm['id']) || dirName,
    description: toString(fm['description']),
    domain: toString(fm['domain']),
    category: toString(fm['category']),
    type: toString(fm['type']),
    runtime: toString(fm['runtime']),
    entry: toString(fm['entry']),
    fallback: toString(fm['fallback']),
    tags: toStringArray(fm['tags']),
    allowedTools: toStringArray(fm['allowed-tools']),
    version: toString(fm['version']),
    status: toString(fm['status']),
  };
}

/**
 * AYNC 分类编码 → SkillDomain 映射
 */
function categoryToDomain(category: string): SkillDomain {
  const normalized = category.toLowerCase();
  if (normalized.includes('business')) return 'marketplace';
  if (normalized.includes('document')) return 'glm-doc';
  if (normalized.includes('ai-ml') || normalized.includes('ai_ml')) return 'ai-ml';
  if (normalized.includes('marketing')) return 'marketing';
  if (normalized.includes('development') || normalized.includes('dev')) return 'devflow';
  if (normalized.includes('social')) return 'social';
  if (normalized.includes('b2b')) return 'b2b';
  if (normalized.includes('ui') || normalized.includes('design')) return 'ui-ux';
  return 'custom';
}

/**
 * 从目录名推断领域
 */
function inferDomain(dirName: string): SkillDomain {
  if (dirName.startsWith('glm') || dirName.startsWith('GLM')) {
    if (dirName.includes('ocr')) return 'glm-ocr';
    if (dirName.includes('caption') || dirName.includes('grounding') || dirName.includes('vision'))
      return 'glm-vision';
    if (dirName.includes('gen') || dirName.includes('image')) return 'glm-gen';
    if (dirName.includes('pdf') || dirName.includes('doc') || dirName.includes('prd') || dirName.includes('web'))
      return 'glm-doc';
    if (dirName.includes('stock') || dirName.includes('finance')) return 'glm-finance';
    return 'glm-gen';
  }
  return 'custom';
}

/**
 * 检测目录中的脚本文件，推断运行时
 */
function detectRuntime(skillDir: string): SkillRuntime {
  try {
    const entries = readdirSync(skillDir);
    const hasPython = entries.some(e => e.endsWith('.py'));
    const hasNode = entries.some(e => e.endsWith('.js') || e.endsWith('.ts'));
    const hasShell = entries.some(e => e.endsWith('.sh'));

    if (hasPython) return 'python';
    if (hasNode) return 'node';
    if (hasShell) return 'shell';
  } catch {
    // ignore
  }
  return 'native';
}

/**
 * 查找脚本入口
 */
function findEntry(skillDir: string, runtime: SkillRuntime): string {
  try {
    const scriptsDir = join(skillDir, 'scripts');
    if (existsSync(scriptsDir)) {
      const scripts = readdirSync(scriptsDir);
      const ext =
        runtime === 'python' ? '.py' :
          runtime === 'node' ? '.js' :
            runtime === 'shell' ? '.sh' : '';

      const main = scripts.find(
        s => s.endsWith(ext) && (s.includes('main') || s.includes('cli') || s.includes('run'))
      );
      if (main) return join('scripts', main);

      const first = scripts.find(s => s.endsWith(ext));
      if (first) return join('scripts', first);
    }
  } catch {
    // ignore
  }
  return '';
}

// ==================== 目录扫描加载器 ====================

export interface LoaderOptions {
  /** 根目录路径 */
  rootDir: string;
  /** 领域前缀映射（如 { 'GLM-skills/skills': 'glm-*' }） */
  domainMap?: Record<string, SkillDomain>;
  /** 是否递归扫描 */
  recursive?: boolean;
  /** 最大扫描深度 */
  maxDepth?: number;
  /**
   * 是否在注册前运行 validateUnifiedSkill（P1-3）。
   * - true（默认）：校验不通过的技能拒绝注册，记入 quarantine 并发
   *   skill:quarantined 事件，与 doctor 共用同一校验函数（单一事实源）。
   * - false：宽容模式，仅记 quarantine 不阻止注册（向后兼容旧行为）。
   */
  validate?: boolean;
  /**
   * 载入前是否清空注册表（P2：reload 只增不删导致磁盘已删除技能残留可执行）。
   * - false（默认）：追加注册（首次启动语义）。
   * - true：先 registry.clear() 再注册（重载语义，磁盘为唯一事实源）。
   */
  sync?: boolean;
}

export class SkillLoader {
  /** 隔离区：校验失败的技能 id（含来源路径）与问题列表 */
  readonly quarantine: Array<{ id: string; source: string; issues: ValidationIssue[] }> = [];

  constructor(
    private registry: SkillRegistry,
    private options: LoaderOptions
  ) { }

  /**
   * 扫描并加载所有 Skill
   */
  load(): UnifiedSkill[] {
    const loaded: UnifiedSkill[] = [];
    const {
      rootDir,
      domainMap,
      recursive = true,
      maxDepth = 2,
      validate = true,
      sync = false,
    } = this.options;

    if (!existsSync(rootDir)) {
      console.warn(`[SkillLoader] Root directory not found: ${rootDir}`);
      return loaded;
    }

    if (sync) {
      // 重载语义：磁盘为唯一事实源，清掉已删除的技能（P2）
      this.registry.clear();
    }

    this.scanDir(rootDir, loaded, domainMap, recursive, maxDepth, 0, validate);
    this.registry.bulkRegister(loaded);
    return loaded;
  }

  /**
   * 重载：sync 语义的便捷入口（清空后按磁盘重建）
   */
  reload(): UnifiedSkill[] {
    this.options = { ...this.options, sync: true };
    return this.load();
  }

  private scanDir(
    dir: string,
    loaded: UnifiedSkill[],
    domainMap: Record<string, SkillDomain> | undefined,
    recursive: boolean,
    maxDepth: number,
    currentDepth: number,
    validate: boolean
  ): void {
    if (currentDepth > maxDepth) return;

    let entries: string[];
    try {
      entries = readdirSync(dir);
    } catch {
      return;
    }

    // 如果目录中有 SKILL.md，则将其作为一个 Skill 加载
    if (entries.includes('SKILL.md')) {
      const skill = this.loadSkillFromDir(dir, domainMap, validate);
      if (skill) {
        loaded.push(skill);
        return; // 不继续递归子目录
      }
    }

    if (!recursive) return;

    // 递归扫描子目录
    for (const entry of entries) {
      const fullPath = join(dir, entry);
      try {
        if (!statSync(fullPath).isDirectory()) continue;
      } catch {
        continue;
      }

      // 跳过隐藏目录和 node_modules
      if (entry.startsWith('.') || entry === 'node_modules' || entry === '__pycache__') {
        continue;
      }

      this.scanDir(fullPath, loaded, domainMap, recursive, maxDepth, currentDepth + 1, validate);
    }
  }

  private loadSkillFromDir(
    skillDir: string,
    domainMap: Record<string, SkillDomain> | undefined,
    validate: boolean
  ): UnifiedSkill | null {
    const skillMdPath = join(skillDir, 'SKILL.md');
    const dirName = basename(skillDir);

    let content = '';
    try {
      content = readFileSync(skillMdPath, 'utf-8');
    } catch {
      return null;
    }

    const fm = parseFrontmatter(content);
    const manifest = frontmatterToManifest(fm, dirName);

    // 领域优先级：frontmatter domain > category 映射 > domainMap 路径映射 > 目录名推断
    let domain: SkillDomain = (manifest.domain as SkillDomain) || 'custom';
    if (!manifest.domain && manifest.category) {
      domain = categoryToDomain(manifest.category);
    }
    if (domain === 'custom' && domainMap) {
      for (const [path, dom] of Object.entries(domainMap)) {
        if (skillDir.includes(path)) {
          domain = dom;
          break;
        }
      }
    }
    if (!manifest.domain && !manifest.category && domain === 'custom') {
      domain = inferDomain(dirName);
    }

    // 检测运行时和入口
    const runtime = (manifest.runtime as SkillRuntime) || detectRuntime(skillDir);
    const entry = manifest.entry || findEntry(skillDir, runtime);

    // 构建相对路径
    const source = skillDir.replace(this.options.rootDir + '/', '');

    const skill: UnifiedSkill = {
      id: manifest.id || `${domain}-${dirName}`,
      name: manifest.name || dirName,
      description: manifest.description || `Skill: ${dirName}`,
      domain,
      type: (manifest.type as SkillType) || 'hybrid',
      runtime,
      entry,
      source,
      inputs: [],
      outputs: [{ type: 'markdown' }],
      fallback: manifest.fallback,
      tags: manifest.tags || [],
      version: manifest.version || '1.0.0',
      status: (manifest.status as UnifiedSkill['status']) || 'active',
    };

    // P1-3：注册前校验，非法资产进隔离区，与 doctor 共用同一校验函数
    if (validate) {
      const result = validateUnifiedSkill(skill);
      if (!result.valid) {
        this.quarantine.push({ id: skill.id, source: skill.source ?? skillDir, issues: result.errors });
        this.registry.emitEvent('skill:quarantined', {
          id: skill.id,
          source: skill.source ?? skillDir,
          issues: result.errors,
        });
        return null;
      }
    }

    return skill;
  }
}
