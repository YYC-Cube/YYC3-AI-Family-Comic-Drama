/**
 * @description YYC³ 统一 Skill 注册中心 — 入口
 * @module @yyc3/skill-registry
 *
 * 五标体系：标准化注册 | 规范化管理 | 自动化加载 | 可视化统计 | 智能化降级
 *
 * 使用方式：
 * ```ts
 * import { globalSkillRegistry, SkillLoader, SkillExecutor } from '@yyc3/skill-registry';
 *
 * // 1. 加载文件系统中的 Skill
 * const loader = new SkillLoader(globalSkillRegistry, {
 *   rootDir: './skills',
 *   recursive: true,
 *   maxDepth: 2,
 * });
 * loader.load();
 *
 * // 2. 查询 Skill
 * const skills = globalSkillRegistry.search({ domain: 'glm-ocr' });
 *
 * // 3. 执行 Skill（含降级熔断）
 * const executor = new SkillExecutor(globalSkillRegistry);
 * const result = await executor.execute('GLM-OCR-001', { image: '/path/to/image.png' });
 * ```
 */

// 类型导出
export type {
  UnifiedSkill,
  SkillDomain,
  SkillType,
  SkillRuntime,
  SkillStatus,
  SkillParameter,
  SkillOutput,
  SkillDependency,
  SkillEval,
  SkillEvalSuite,
  SkillExecutionContext,
  SkillExecutionResult,
  SkillEventMap,
  SkillSearchOptions,
  SkillRegistryStats,
} from './types.js';
export {
  SKILL_DOMAINS,
  SKILL_TYPES,
  SKILL_RUNTIMES,
  SKILL_STATUSES,
} from './types.js';

// Frontmatter 解析
export {
  parseFrontmatter,
  parseYamlSubset,
  parseInlineArray,
  toString as frontmatterToString,
  toStringArray as frontmatterToStringArray,
} from './frontmatter.js';
export type { Frontmatter, FrontmatterValue } from './frontmatter.js';

// 注册中心
export { SkillRegistry, globalSkillRegistry } from './registry.js';

// 加载器
export { SkillLoader, frontmatterToManifest } from './loader.js';
export type { SkillManifest, LoaderOptions } from './loader.js';

// 校验器
export { validateFrontmatter, validateUnifiedSkill, validateAllSkills } from './validator.js';
export type {
  ValidationIssue,
  ValidationResult,
  BatchValidationReport,
} from './validator.js';

// 执行器
export { SkillExecutor } from './executor.js';
