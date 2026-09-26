/**
 * Orchestrator — 类型定义
 * @module @yyc3/orchestrator
 */

import type { AgentProfile } from '@yyc3/agent-runtime';

/** 任务优先级 */
export type TaskPriority = 'critical' | 'high' | 'medium' | 'low';

/** 任务状态 */
export type TaskStatus = 'pending' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';

/** 原子任务 */
export interface AtomicTask {
  id: string;
  /** 任务描述 */
  description: string;
  /** 所需能力 */
  requiredCapabilities: string[];
  /** 优先级 */
  priority: TaskPriority;
  /** 状态 */
  status: TaskStatus;
  /** 依赖的任务 ID */
  dependencies: string[];
  /** 分配的智能体 ID */
  assignedAgentId?: string;
  /** 预估复杂度 (1-10) */
  estimatedComplexity: number;
  /** 输入参数 */
  input?: Record<string, unknown>;
  /** 输出结果 */
  output?: unknown;
  /** 错误信息 */
  error?: string;
  /** 创建时间 */
  createdAt: string;
  /** 开始时间 */
  startedAt?: string;
  /** 完成时间 */
  completedAt?: string;
}

/** 工作流（DAG） */
export interface Workflow {
  id: string;
  /** 工作流名称 */
  name: string;
  /** 原始目标描述 */
  goal: string;
  /** 分解后的任务列表 */
  tasks: AtomicTask[];
  /** 状态 */
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  /** 创建时间 */
  createdAt: string;
  /** 完成时间 */
  completedAt?: string;
  /** 元数据 */
  meta?: Record<string, unknown>;
}

/** 任务分解结果 */
export interface DecompositionResult {
  tasks: Omit<AtomicTask, 'id' | 'status' | 'createdAt'>[];
  reasoning: string;
}

/** 调度决策 */
export interface SchedulingDecision {
  taskId: string;
  assignedAgentId: string;
  agentName: string;
  score: number;
  reasoning: string;
}

/** 能力匹配分数 */
export interface CapabilityScore {
  agentId: string;
  agentName: string;
  score: number;
  matchedCapabilities: string[];
  missingCapabilities: string[];
}

/** 编排器配置 */
export interface OrchestratorConfig {
  /** 最大并发任务数 */
  maxConcurrency: number;
  /** 默认任务优先级 */
  defaultPriority: TaskPriority;
  /** 调度策略 */
  schedulingStrategy: 'capability-match' | 'round-robin' | 'load-balance';
  /** 是否启用自动重试 */
  autoRetry: boolean;
  /** 最大重试次数 */
  maxRetries: number;
}

/** 编排器事件 */
export interface OrchestratorEvents {
  'workflow:created': (workflow: Workflow) => void;
  'workflow:completed': (workflow: Workflow) => void;
  'workflow:failed': (workflow: Workflow, error: string) => void;
  'task:decomposed': (goal: string, tasks: AtomicTask[]) => void;
  'task:started': (task: AtomicTask) => void;
  'task:completed': (task: AtomicTask) => void;
  'task:failed': (task: AtomicTask, error: string) => void;
  'scheduled': (decision: SchedulingDecision) => void;
}