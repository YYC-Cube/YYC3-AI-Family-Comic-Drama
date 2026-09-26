/**
 * YYC³ Conductor 协同编排引擎
 * @module @yyc3/conductor
 *
 * DAG 流水线编排引擎，支持：
 * - 任务依赖管理（拓扑排序）
 * - 并行执行（层级并发）
 * - 错误恢复 & 重试（指数退避）
 * - 事件驱动（完整生命周期事件）
 * - 取消 & 超时控制
 *
 * 使用方式：
 * ```ts
 * import { Conductor } from '@yyc3/conductor';
 *
 * const conductor = new Conductor({ defaultConcurrency: 3 });
 *
 * conductor.on('task:complete', (id, result) => {
 *   console.log(`Task ${id} completed in ${result.duration}ms`);
 * });
 *
 * const result = await conductor.execute({
 *   id: 'my-pipeline',
 *   name: '演示流水线',
 *   tasks: [
 *     { id: 'fetch', executor: async (ctx) => ({ data: 'fetched' }) },
 *     { id: 'process', dependsOn: [{ taskId: 'fetch', type: 'required' }],
 *       executor: async (ctx) => {
 *         const fetched = ctx.outputs.get('fetch');
 *         return `processed: ${JSON.stringify(fetched)}`;
 *       }
 *     },
 *   ],
 * });
 * ```
 */

export { Conductor } from './conductor.js';
export { PipelineBuilder } from './pipeline.js';
export type {
  TaskDef,
  TaskResult,
  TaskStatus,
  PipelineDef,
  PipelineResult,
  PipelineStatus,
  PipelineContext,
  RetryPolicy,
  TaskDependency,
  ConductorConfig,
  ConductorEvents,
} from './types.js';