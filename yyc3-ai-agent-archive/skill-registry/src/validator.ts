/**
 * @description Skill 校验器 — 基于 Zod 的结构化校验
 * @module @yyc3/skill-registry/validator
 *
 * 提供两个层级的校验：
 * 1. validateFrontmatter — 校验 SKILL.md 解析出的原始清单（供 yyc3 skills validate 使用）
 * 2. validateUnifiedSkill — 校验注册前的 UnifiedSkill 对象
 *
 * 校验结果区分 error（阻断）与 warning（提示），输出结构化问题列表。
 */

import { z } from 'zod';
import type { Frontmatter } from './frontmatter.js';
import { toString, toStringArray } from './frontmatter.js';
import type { UnifiedSkill } from './types.js';
import {
  SKILL_DOMAINS,
  SKILL_RUNTIMES,
  SKILL_STATUSES,
  SKILL_TYPES,
} from './types.js';

// ==================== Zod Schema ====================

const SkillDomainSchema = z.enum(SKILL_DOMAINS);
const SkillTypeSchema = z.enum(SKILL_TYPES);
const SkillRuntimeSchema = z.enum(SKILL_RUNTIMES);
const SkillStatusSchema = z.enum(SKILL_STATUSES);

/** SemVer 2.0.0 宽松匹配（允许 v 前缀） */
const SEMVER_RE = /^v?\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$/;

const UnifiedSkillSchema = z.object({
  id: z.string().min(1, 'id 不能为空'),
  name: z.string().min(1, 'name 不能为空'),
  description: z.string(),
  domain: SkillDomainSchema,
  type: SkillTypeSchema,
  runtime: SkillRuntimeSchema,
  entry: z.string(),
  inputs: z.array(z.any()),
  outputs: z.array(z.any()),
  status: SkillStatusSchema.optional(),
  version: z
    .string()
    .refine(v => SEMVER_RE.test(v), {
      message: 'version 必须符合 SemVer 2.0.0（如 1.0.0）',
    })
    .optional(),
});

// ==================== 校验结果类型 ====================

export type IssueSeverity = 'error' | 'warning';

export interface ValidationIssue {
  /** 问题定位（字段名或对象路径） */
  path: string;
  /** 问题描述 */
  message: string;
  severity: IssueSeverity;
}

export interface ValidationResult {
  /** 是否通过（无 error 即通过，warning 不阻断） */
  valid: boolean;
  errors: ValidationIssue[];
  warnings: ValidationIssue[];
}

// ==================== Frontmatter 校验 ====================

/**
 * 校验 SKILL.md frontmatter 清单
 *
 * 规则（对齐 docs/ Skill 核心设计原则）：
 * - error: name 缺失或为空
 * - error: version 存在但不符合 SemVer
 * - error: allowed-tools / tags 存在但不可解析为数组元素
 * - warning: description 缺失或过短（< 10 字符）
 * - warning: 缺少 category 分类
 */
export function validateFrontmatter(fm: Frontmatter): ValidationResult {
  const errors: ValidationIssue[] = [];
  const warnings: ValidationIssue[] = [];

  // name 必填
  const name = toString(fm['name']).trim();
  if (!name) {
    errors.push({
      path: 'name',
      message: 'name 为必填字段，且不能为空字符串',
      severity: 'error',
    });
  }

  // description 建议填写
  const description = toString(fm['description']).trim();
  if (!description) {
    warnings.push({
      path: 'description',
      message: 'description 缺失，建议补充技能用途说明',
      severity: 'warning',
    });
  } else if (description.length < 10) {
    warnings.push({
      path: 'description',
      message: `description 过短（${description.length} 字符），建议不少于 10 字符`,
      severity: 'warning',
    });
  }

  // version 若存在必须符合 SemVer
  const version = toString(fm['version']).trim();
  if (version && !SEMVER_RE.test(version)) {
    errors.push({
      path: 'version',
      message: `version "${version}" 不符合 SemVer 2.0.0（如 1.0.0）`,
      severity: 'error',
    });
  }

  // category 建议填写
  const category = toString(fm['category']).trim();
  if (!category) {
    warnings.push({
      path: 'category',
      message: 'category 缺失，建议填写 AYNC 分类编码（如 development-code）',
      severity: 'warning',
    });
  }

  // allowed-tools 必须可解析为数组
  if (fm['allowed-tools'] !== undefined) {
    const tools = toStringArray(fm['allowed-tools']);
    if (tools.length === 0) {
      errors.push({
        path: 'allowed-tools',
        message: 'allowed-tools 存在但无法解析出任何工具项',
        severity: 'error',
      });
    }
  }

  return { valid: errors.length === 0, errors, warnings };
}

// ==================== UnifiedSkill 校验 ====================

/**
 * 校验注册前的 UnifiedSkill 对象
 */
export function validateUnifiedSkill(skill: UnifiedSkill): ValidationResult {
  const errors: ValidationIssue[] = [];
  const warnings: ValidationIssue[] = [];

  const parsed = UnifiedSkillSchema.safeParse(skill);
  if (!parsed.success) {
    for (const issue of parsed.error.issues) {
      errors.push({
        path: issue.path.join('.') || '(root)',
        message: issue.message,
        severity: 'error',
      });
    }
  }

  // 降级链自引用检测
  if (skill.fallback === skill.id) {
    errors.push({
      path: 'fallback',
      message: `fallback 不能指向自身（${skill.id}）`,
      severity: 'error',
    });
  }

  // 入口建议
  if (!skill.entry && skill.runtime !== 'native') {
    warnings.push({
      path: 'entry',
      message: `runtime 为 ${skill.runtime} 但未定义 entry，执行时将失败`,
      severity: 'warning',
    });
  }

  // 未纳入安全审计提示
  if (!skill.securityAudited) {
    warnings.push({
      path: 'securityAudited',
      message: '技能未标记安全审计，上线前建议完成四步安全审查',
      severity: 'warning',
    });
  }

  return { valid: errors.length === 0, errors, warnings };
}

// ==================== 批量校验 ====================

export interface BatchValidationReport {
  total: number;
  passed: number;
  failed: number;
  warningCount: number;
  issues: Array<{ id: string; result: ValidationResult }>;
}

/**
 * 批量校验 UnifiedSkill 列表
 */
export function validateAllSkills(
  skills: UnifiedSkill[]
): BatchValidationReport {
  const report: BatchValidationReport = {
    total: skills.length,
    passed: 0,
    failed: 0,
    warningCount: 0,
    issues: [],
  };

  for (const skill of skills) {
    const result = validateUnifiedSkill(skill);
    if (result.valid) {
      report.passed++;
    } else {
      report.failed++;
    }
    report.warningCount += result.warnings.length;
    if (!result.valid || result.warnings.length > 0) {
      report.issues.push({ id: skill.id, result });
    }
  }

  return report;
}
