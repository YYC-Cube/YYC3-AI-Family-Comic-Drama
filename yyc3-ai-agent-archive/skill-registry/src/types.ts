/**
 * @description YYC³ 统一 Skill 类型系统
 * @module @yyc3/skill-registry/types
 *
 * 定义所有 Skill 遵循的统一接口标准，
 * 实现"标准化、规范化、可视化、智能化"五标体系。
 */

import type { ValidationIssue } from './validator.js';
export type { ValidationIssue } from './validator.js';

// ==================== Skill 基础类型 ====================
// 采用 const 数组派生联合类型，作为 Zod 校验的单一数据源

export const SKILL_DOMAINS = [
  'glm-ocr',        // GLM OCR 文字识别
  'glm-vision',     // GLM 视觉理解
  'glm-gen',        // GLM 内容生成
  'glm-doc',        // GLM 文档处理
  'glm-finance',    // GLM 金融分析
  'hot',            // 社区热门工具
  'marketing',      // 营销领域
  'engineering',    // 工程实践
  'devflow',        // 开发流程
  'social',         // 社交搜索
  'marketplace',    // 通用技能市场（对应 skills-hub/marketplace/）
  'b2b',            // B2B 销售技能（对应 skills-hub/b2b/）
  'ui-ux',          // UI/UX 设计技能（对应 skills-hub/ui-ux/）
  'ai-ml',          // AI/ML 量化技能（对应 skills-hub/ai-ml/）
  'agent-role',     // Agent 角色
  'custom',         // 自定义扩展
] as const;

export type SkillDomain = (typeof SKILL_DOMAINS)[number];

export const SKILL_TYPES = ['script', 'prompt', 'hybrid'] as const;
export type SkillType = (typeof SKILL_TYPES)[number];

export const SKILL_RUNTIMES = ['python', 'node', 'shell', 'native'] as const;
export type SkillRuntime = (typeof SKILL_RUNTIMES)[number];

export const SKILL_STATUSES = [
  'active',         // 正常可用
  'deprecated',     // 已弃用但保留
  'experimental',   // 实验性
  'disabled',       // 已禁用
] as const;
export type SkillStatus = (typeof SKILL_STATUSES)[number];

export interface SkillParameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'object' | 'array';
  description?: string;
  required?: boolean;
  default?: unknown;
  enum?: string[];
  items?: SkillParameter;
  properties?: Record<string, SkillParameter>;
}

export interface SkillOutput {
  type: 'text' | 'json' | 'file' | 'image' | 'markdown';
  description?: string;
  schema?: Record<string, unknown>;
}

export interface SkillDependency {
  /** 环境变量要求 */
  env?: string[];
  /** 可执行文件要求 */
  bins?: string[];
  /** Python 包要求 */
  pythonPackages?: string[];
  /** npm 包要求 */
  npmPackages?: string[];
}

export interface SkillEval {
  name: string;
  description?: string;
  input: Record<string, unknown>;
  expected?: Record<string, unknown>;
  assertion?: string;
}

export interface SkillEvalSuite {
  version: string;
  cases: SkillEval[];
}

// ==================== 核心 Skill 接口 ====================

export interface UnifiedSkill {
  /** 唯一编码（如 GLM-OCR-001） */
  id: string;
  /** 人类可读名称 */
  name: string;
  /** 简短描述 */
  description: string;
  /** 详细说明 */
  detail?: string;
  /** 领域分类 */
  domain: SkillDomain;
  /** 类型：脚本/Prompt/混合 */
  type: SkillType;
  /** 运行时：python/node/shell/native */
  runtime: SkillRuntime;
  /** 执行入口（脚本路径或函数名） */
  entry: string;
  /** 来源路径（相对于 skills/ 目录） */
  source?: string;
  /** 输入参数定义 */
  inputs: SkillParameter[];
  /** 输出格式定义 */
  outputs: SkillOutput[];
  /** 依赖声明 */
  requires?: SkillDependency;
  /** 降级 Skill ID（当前 Skill 不可用时尝试的替代） */
  fallback?: string;
  /** 评估套件 */
  evals?: SkillEvalSuite;
  /** 标签 */
  tags?: string[];
  /** 版本号 */
  version?: string;
  /** 状态 */
  status?: SkillStatus;
  /** 作者 */
  author?: string;
  /** 安全审计标记 */
  securityAudited?: boolean;
}

// ==================== 执行上下文 ====================

export interface SkillExecutionContext {
  /** 调用 ID */
  callId: string;
  /** 会话 ID */
  sessionId?: string;
  /** 用户 ID */
  userId?: string;
  /** 工作目录 */
  cwd?: string;
  /** 环境变量覆盖（仅这些 key 会显式注入技能进程） */
  env?: Record<string, string>;
  /**
   * 允许从宿主透传给技能进程的环境变量白名单。
   * 不传时使用执行器内置最小白名单（PATH/HOME/LANG 等运行必需项），
   * 宿主上的 API Key/Token 等不会进入技能进程。
   */
  allowedEnv?: string[];
  /** 超时时间（毫秒） */
  timeout?: number;
  /** 是否允许降级 */
  allowFallback?: boolean;
  /** 最大降级深度 */
  maxFallbackDepth?: number;
}

export interface SkillExecutionResult {
  /** 调用 ID */
  callId: string;
  /** Skill ID */
  skillId: string;
  /** 是否成功 */
  success: boolean;
  /** 输出内容 */
  output: unknown;
  /** 错误信息（失败时） */
  error?: string;
  /** 是否经过降级 */
  fellBack?: boolean;
  /** 实际执行的 Skill ID（可能因降级与请求的不同） */
  executedSkillId?: string;
  /** 执行耗时（毫秒） */
  duration?: number;
  /** 元数据 */
  metadata?: Record<string, unknown>;
}

// ==================== 事件定义 ====================

export interface SkillEventMap {
  'skill:registered': { skill: UnifiedSkill };
  'skill:unregistered': { id: string };
  'skill:executed': { result: SkillExecutionResult };
  'skill:failed': { id: string; error: string };
  'skill:fell-back': { from: string; to: string };
  'skill:circuit-open': { id: string; reason: string };
  'skill:circuit-close': { id: string };
  'skill:duplicate': { id: string; kept: UnifiedSkill; variant: UnifiedSkill };
  /** 加载校验失败进入隔离区的技能（P1-3，doctor 与运行时共用同一校验函数） */
  'skill:quarantined': { id: string; source: string; issues: ValidationIssue[] };
}

// ==================== 搜索 ====================

export interface SkillSearchOptions {
  query?: string;
  domain?: SkillDomain;
  tags?: string[];
  type?: SkillType;
  runtime?: SkillRuntime;
  status?: SkillStatus;
  limit?: number;
  offset?: number;
}

export interface SkillRegistryStats {
  totalSkills: number;
  byDomain: Partial<Record<SkillDomain, number>>;
  byType: Partial<Record<SkillType, number>>;
  byRuntime: Partial<Record<SkillRuntime, number>>;
  byStatus: Partial<Record<SkillStatus, number>>;
  withEvals: number;
  withFallback: number;
  /** 存在同名变体冲突的技能数 */
  withVariants: number;
}
