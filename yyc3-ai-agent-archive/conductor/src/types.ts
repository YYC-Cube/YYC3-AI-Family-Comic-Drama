/**
 * Conductor 协同编排引擎 — 类型定义
 * @module @yyc3/conductor
 */

/** 任务状态 */
export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'skipped' | 'cancelled';

/** 流水线状态 */
export type PipelineStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

/** 任务重试策略 */
export interface RetryPolicy {
  maxRetries: number;
  /** 重试间隔（毫秒） */
  delayMs: number;
  /** 是否使用指数退避 */
  backoff?: boolean;
  /** 退避倍数 */
  backoffMultiplier?: number;
}

/** 任务依赖 */
export interface TaskDependency {
  taskId: string;
  /** 依赖类型: required 必须成功 / optional 可选 */
  type: 'required' | 'optional';
}

/** 单个任务定义 */
export interface TaskDef {
  id: string;
  name?: string;
  description?: string;
  /** 技能 ID */
  skillId?: string;
  /** 传递给技能的参数 */
  params?: Record<string, unknown>;
  /** 依赖 */
  dependsOn?: TaskDependency[];
  /** 重试策略 */
  retry?: RetryPolicy;
  /** 超时（毫秒） */
  timeout?: number;
  /** 前置条件：返回 true 才执行 */
  condition?: (ctx: PipelineContext) => boolean | Promise<boolean>;
  /** 自定义执行器（优先于 skillId） */
  executor?: (ctx: PipelineContext) => Promise<unknown>;
}

/** 任务执行结果 */
export interface TaskResult {
  taskId: string;
  status: TaskStatus;
  output?: unknown;
  error?: string;
  startedAt: string;
  finishedAt?: string;
  duration: number;
  retries: number;
}

/** 流水线上下文 */
export interface PipelineContext {
  pipelineId: string;
  startedAt: string;
  /** 任务输出池，key=taskId, value=output */
  outputs: Map<string, unknown>;
  /** 全局变量 */
  vars: Record<string, unknown>;
  /** 环境变量 */
  env: Record<string, string>;
}

/** 流水线定义 */
export interface PipelineDef {
  id: string;
  name: string;
  description?: string;
  tasks: TaskDef[];
  /** 全局超时 */
  timeout?: number;
  /** 并发任务数上限 */
  concurrency?: number;
  /** 失败策略: stop 停止 / continue 继续 */
  onFailure?: 'stop' | 'continue';
}

/** 流水线执行结果 */
export interface PipelineResult {
  pipelineId: string;
  status: PipelineStatus;
  tasks: TaskResult[];
  startedAt: string;
  finishedAt?: string;
  duration: number;
  error?: string;
}

/** 编排器事件 */
export interface ConductorEvents {
  'pipeline:start': (pipeline: PipelineDef) => void;
  'pipeline:complete': (result: PipelineResult) => void;
  'pipeline:fail': (result: PipelineResult) => void;
  'task:start': (taskId: string, ctx: PipelineContext) => void;
  'task:complete': (taskId: string, result: TaskResult) => void;
  'task:fail': (taskId: string, result: TaskResult) => void;
  'task:retry': (taskId: string, attempt: number, error: string) => void;
}

/** 编排器配置 */
export interface ConductorConfig {
  /** 默认并发数 */
  defaultConcurrency: number;
  /** 默认超时（毫秒） */
  defaultTimeout: number;
  /** 默认重试策略 */
  defaultRetry: RetryPolicy;
}
