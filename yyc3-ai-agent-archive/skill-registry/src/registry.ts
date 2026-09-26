/**
 * @description YYC³ 统一 Skill 注册中心
 * @module @yyc3/skill-registry/registry
 *
 * 实现 Skill 的标准化注册、发现、分类管理与搜索。
 * 对齐 MCP 架构，可桥接为 MCP Tool。
 */

import type {
  UnifiedSkill,
  SkillDomain,
  SkillType,
  SkillRuntime,
  SkillStatus,
  SkillSearchOptions,
  SkillRegistryStats,
  SkillEventMap,
} from './types.js';

type EventHandler<T> = (payload: T) => void;

/** SemVer 宽松比较：返回版本更高的一方；无法解析时保留首个（existing） */
function higherVersion(a: UnifiedSkill, b: UnifiedSkill): UnifiedSkill {
  const pa = parseSemver(a.version);
  const pb = parseSemver(b.version);
  if (!pa || !pb) return a;
  for (let i = 0; i < 3; i++) {
    if (pa[i] !== pb[i]) return pa[i] > pb[i] ? a : b;
  }
  return a;
}

function parseSemver(v?: string): [number, number, number] | null {
  if (!v) return null;
  const m = v.match(/^v?(\d+)\.(\d+)\.(\d+)/);
  if (!m) return null;
  return [Number(m[1]), Number(m[2]), Number(m[3])];
}

export class SkillRegistry {
  private skills: Map<string, UnifiedSkill> = new Map();
  private domainIndex: Map<SkillDomain, Set<string>> = new Map();
  private tagIndex: Map<string, Set<string>> = new Map();
  /** 同名变体：主技能 ID → 被压制的历史版本列表 */
  private variants: Map<string, UnifiedSkill[]> = new Map();
  private listeners: { [K in keyof SkillEventMap]?: Set<EventHandler<SkillEventMap[K]>> } = {};

  /**
   * 注册一个 Skill
   *
   * 同名冲突治理：保留版本号更高（SemVer 比较）的一方为主技能，
   * 落选方记录为变体并发出 skill:duplicate 事件，注册结果确定且可观测。
   */
  register(skill: UnifiedSkill): void {
    const existing = this.skills.get(skill.id);
    if (existing) {
      const winner = higherVersion(existing, skill);
      const loser = winner === existing ? skill : existing;
      this.variants.set(skill.id, [...(this.variants.get(skill.id) ?? []), loser]);
      if (winner === skill) {
        this.skills.set(skill.id, skill);
      }
      this.emit('skill:duplicate', { id: skill.id, kept: winner, variant: loser });
      return;
    }

    this.skills.set(skill.id, skill);

    // 索引：按领域
    if (!this.domainIndex.has(skill.domain)) {
      this.domainIndex.set(skill.domain, new Set());
    }
    this.domainIndex.get(skill.domain)!.add(skill.id);

    // 索引：按标签
    if (skill.tags) {
      for (const tag of skill.tags) {
        if (!this.tagIndex.has(tag)) {
          this.tagIndex.set(tag, new Set());
        }
        this.tagIndex.get(tag)!.add(skill.id);
      }
    }

    this.emit('skill:registered', { skill });
  }

  /**
   * 批量注册
   */
  bulkRegister(skills: UnifiedSkill[]): void {
    for (const skill of skills) {
      this.register(skill);
    }
  }

  /**
   * 注销 Skill
   */
  unregister(id: string): boolean {
    const skill = this.skills.get(id);
    if (!skill) return false;

    this.skills.delete(id);
    this.variants.delete(id);
    this.domainIndex.get(skill.domain)?.delete(id);

    if (skill.tags) {
      for (const tag of skill.tags) {
        this.tagIndex.get(tag)?.delete(id);
      }
    }

    this.emit('skill:unregistered', { id });
    return true;
  }

  /**
   * 清空全部注册状态（技能/索引/变体）— reload 前重建用（P2：reload 只增不删导致
   * 磁盘已删除技能仍残留可执行）。逐个发 skill:unregistered 事件保持可观测。
   */
  clear(): void {
    for (const id of Array.from(this.skills.keys())) {
      this.unregister(id);
    }
    this.variants.clear();
    this.domainIndex.clear();
    this.tagIndex.clear();
  }

  /**
   * 获取 Skill
   */
  get(id: string): UnifiedSkill | undefined {
    return this.skills.get(id);
  }

  /**
   * 获取所有 Skill
   */
  getAll(): UnifiedSkill[] {
    return Array.from(this.skills.values());
  }

  /**
   * 是否存在
   */
  has(id: string): boolean {
    return this.skills.has(id);
  }

  /**
   * 按领域获取
   */
  getByDomain(domain: SkillDomain): UnifiedSkill[] {
    const ids = this.domainIndex.get(domain);
    if (!ids) return [];
    return Array.from(ids)
      .map(id => this.skills.get(id)!)
      .filter(Boolean);
  }

  /**
   * 按标签获取
   */
  getByTag(tag: string): UnifiedSkill[] {
    const ids = this.tagIndex.get(tag);
    if (!ids) return [];
    return Array.from(ids)
      .map(id => this.skills.get(id)!)
      .filter(Boolean);
  }

  /**
   * 搜索 Skill
   */
  search(options: SkillSearchOptions = {}): UnifiedSkill[] {
    let results = Array.from(this.skills.values());

    // 文本搜索
    if (options.query) {
      const q = options.query.toLowerCase();
      results = results.filter(
        s =>
          s.name.toLowerCase().includes(q) ||
          s.description.toLowerCase().includes(q) ||
          s.id.toLowerCase().includes(q) ||
          (s.tags?.some(t => t.toLowerCase().includes(q)) ?? false)
      );
    }

    // 按领域筛选
    if (options.domain) {
      results = results.filter(s => s.domain === options.domain);
    }

    // 按类型筛选
    if (options.type) {
      results = results.filter(s => s.type === options.type);
    }

    // 按运行时筛选
    if (options.runtime) {
      results = results.filter(s => s.runtime === options.runtime);
    }

    // 按状态筛选（默认仅返回 active）
    if (options.status) {
      results = results.filter(s => (s.status ?? 'active') === options.status);
    } else {
      results = results.filter(s => (s.status ?? 'active') === 'active');
    }

    // 按标签筛选
    if (options.tags && options.tags.length > 0) {
      results = results.filter(s =>
        options.tags!.some(t => s.tags?.includes(t))
      );
    }

    // 分页
    const offset = options.offset ?? 0;
    const limit = options.limit ?? results.length;
    return results.slice(offset, offset + limit);
  }

  /**
   * 获取降级链
   */
  getFallbackChain(id: string, maxDepth: number = 5): string[] {
    const chain: string[] = [id];
    let current = id;
    let depth = 0;

    while (depth < maxDepth) {
      const skill = this.skills.get(current);
      if (!skill?.fallback) break;
      if (chain.includes(skill.fallback)) break; // 防止循环
      chain.push(skill.fallback);
      current = skill.fallback;
      depth++;
    }

    return chain;
  }

  /**
   * 获取指定技能的同名变体（被压制的其他版本）
   */
  getVariants(id: string): UnifiedSkill[] {
    return this.variants.get(id) ?? [];
  }

  /**
   * 获取全部存在同名冲突的技能 ID
   */
  getDuplicateIds(): string[] {
    return Array.from(this.variants.keys());
  }

  /**
   * 获取注册中心统计信息
   */
  getStats(): SkillRegistryStats {
    const stats: SkillRegistryStats = {
      totalSkills: this.skills.size,
      byDomain: {},
      byType: {},
      byRuntime: {},
      byStatus: {},
      withEvals: 0,
      withFallback: 0,
      withVariants: this.variants.size,
    };

    for (const skill of this.skills.values()) {
      stats.byDomain[skill.domain] = (stats.byDomain[skill.domain] ?? 0) + 1;
      stats.byType[skill.type] = (stats.byType[skill.type] ?? 0) + 1;
      stats.byRuntime[skill.runtime] = (stats.byRuntime[skill.runtime] ?? 0) + 1;
      const status = skill.status ?? 'active';
      stats.byStatus[status] = (stats.byStatus[status] ?? 0) + 1;
      if (skill.evals) stats.withEvals++;
      if (skill.fallback) stats.withFallback++;
    }

    return stats;
  }

  /**
   * 导出注册表（用于序列化/持久化）
   */
  export(): UnifiedSkill[] {
    return this.getAll();
  }

  /**
   * 导入注册表
   */
  import(skills: UnifiedSkill[]): void {
    this.bulkRegister(skills);
  }

  // ==================== 事件系统 ====================

  on<K extends keyof SkillEventMap>(
    event: K,
    handler: EventHandler<SkillEventMap[K]>
  ): () => void {
    if (!this.listeners[event]) {
      this.listeners[event] = new Set() as any;
    }
    this.listeners[event]!.add(handler as any);
    return () => this.off(event, handler);
  }

  off<K extends keyof SkillEventMap>(
    event: K,
    handler: EventHandler<SkillEventMap[K]>
  ): void {
    this.listeners[event]?.delete(handler as any);
  }

  private emit<K extends keyof SkillEventMap>(
    event: K,
    payload: SkillEventMap[K]
  ): void {
    this.listeners[event]?.forEach(handler => {
      try {
        handler(payload as any);
      } catch (e) {
        console.error(`[SkillRegistry] Event handler error for "${String(event)}":`, e);
      }
    });
  }

  /**
   * 发射注册中心事件（供 SkillLoader 等协作组件转发内部事件，
   * 如 skill:quarantined——加载校验失败的隔离通知）。
   */
  emitEvent<K extends keyof SkillEventMap>(event: K, payload: SkillEventMap[K]): void {
    this.emit(event, payload);
  }
}

/** 全局注册中心实例 */
export const globalSkillRegistry = new SkillRegistry();
