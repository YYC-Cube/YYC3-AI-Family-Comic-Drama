/**
 * 生产任务类型定义（六阶段流水线）
 */

/** 任务状态：待执行/执行中/成功/失败/返工 */
export const TASK_STATUSES = [
  "pending",
  "running",
  "success",
  "failed",
  "rework",
] as const;
export type TaskStatus = (typeof TASK_STATUSES)[number];

/** 生产阶段：创意立项/剧本分镜/视听生成/音画同步/合成交付/运营反哺 */
export const PRODUCTION_STAGES = [
  "creative",
  "script",
  "visual",
  "audio",
  "compose",
  "ops",
] as const;
export type ProductionStage = (typeof PRODUCTION_STAGES)[number];

/** 生产任务 */
export interface ProductionTask {
  task_id: string;
  project_id: string;
  /** 所属六阶段之一 */
  stage: ProductionStage;
  status: TaskStatus;
  /** 进度 0-100 */
  progress: number;
  /** 执行 Agent 名称 */
  agent: string;
  /** 链路追踪 ID */
  trace_id: string;
  created_at: string;
  updated_at: string;
  /** 失败/返工原因（正常为 null） */
  error: string | null;
}
