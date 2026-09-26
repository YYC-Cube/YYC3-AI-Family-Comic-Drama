/**
 * Conductor 协同编排引擎 — 核心编排器
 *
 * 负责流水线执行、任务调度、并行控制、错误恢复
 */
import { EventEmitter } from 'eventemitter3';
import { PipelineBuilder } from './pipeline.js';
import type {
  PipelineDef,
  PipelineResult,
  PipelineContext,
  PipelineStatus,
  TaskDef,
  TaskResult,
  TaskStatus,
  ConductorConfig,
  ConductorEvents,
} from './types.js';

const DEFAULT_CONFIG: ConductorConfig = {
  defaultConcurrency: 5,
  defaultTimeout: 60_000,
  defaultRetry: { maxRetries: 0, delayMs: 1000 },
};

export class Conductor extends EventEmitter<ConductorEvents> {
  readonly config: ConductorConfig;
  private running = new Map<string, AbortController>();

  constructor(config: Partial<ConductorConfig> = {}) {
    super();
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /** 执行流水线 */
  async execute(pipeline: PipelineDef): Promise<PipelineResult> {
    const errors = PipelineBuilder.validate(pipeline);
    if (errors.length > 0) {
      throw new Error(`Pipeline validation failed: ${errors.join('; ')}`);
    }

    const { levels } = PipelineBuilder.topologicalSort(pipeline);
    const ctx: PipelineContext = {
      pipelineId: pipeline.id,
      startedAt: new Date().toISOString(),
      outputs: new Map(),
      vars: {},
      env: {},
    };

    const results: TaskResult[] = [];
    const abortController = new AbortController();
    this.running.set(pipeline.id, abortController);

    const startTime = Date.now();
    let pipelineStatus: PipelineStatus = 'running';

    this.emit('pipeline:start', pipeline);

    try {
      for (const level of levels) {
        const concurrency = pipeline.concurrency ?? this.config.defaultConcurrency;
        const batches = this.chunkArray(level, concurrency);

        for (const batch of batches) {
          if (abortController.signal.aborted) break;

          const batchResults = await Promise.all(
            batch.map(task => this.executeTask(task, ctx, pipeline, abortController.signal))
          );
          results.push(...batchResults);

          // 检查是否有 required 依赖失败
          if (pipeline.onFailure !== 'continue') {
            const hasFailure = results.some(r => r.status === 'failed');
            if (hasFailure) {
              pipelineStatus = 'failed';
              break;
            }
          }
        }

        if (pipelineStatus === 'failed') break;
      }

      if (pipelineStatus === 'running') {
        pipelineStatus = 'completed';
      }
    } catch (err) {
      pipelineStatus = 'failed';
    } finally {
      this.running.delete(pipeline.id);
    }

    const result: PipelineResult = {
      pipelineId: pipeline.id,
      status: pipelineStatus,
      tasks: results,
      startedAt: ctx.startedAt,
      finishedAt: new Date().toISOString(),
      duration: Date.now() - startTime,
    };

    if (pipelineStatus === 'completed') {
      this.emit('pipeline:complete', result);
    } else {
      this.emit('pipeline:fail', result);
    }

    return result;
  }

  /** 取消流水线 */
  cancel(pipelineId: string): boolean {
    const controller = this.running.get(pipelineId);
    if (controller) {
      controller.abort();
      return true;
    }
    return false;
  }

  /** 执行单个任务 */
  private async executeTask(
    task: TaskDef,
    ctx: PipelineContext,
    pipeline: PipelineDef,
    signal: AbortSignal
  ): Promise<TaskResult> {
    // 检查前置条件
    if (task.condition) {
      try {
        const ok = await task.condition(ctx);
        if (!ok) {
          return this.makeResult(task.id, 'skipped', undefined, undefined, 0, 0);
        }
      } catch {
        return this.makeResult(task.id, 'skipped', undefined, undefined, 0, 0);
      }
    }

    const retry = task.retry ?? this.config.defaultRetry;
    let lastError: string | undefined;
    let attempts = 0;

    this.emit('task:start', task.id, ctx);

    const startTime = Date.now();
    const timeout = task.timeout ?? pipeline.timeout ?? this.config.defaultTimeout;

    for (attempts = 0; attempts <= retry.maxRetries; attempts++) {
      if (signal.aborted) {
        return this.makeResult(task.id, 'cancelled', undefined, undefined, Date.now() - startTime, attempts);
      }

      try {
        const output = await this.withTimeout(
          this.runTask(task, ctx),
          timeout,
          signal
        );

        const result = this.makeResult(task.id, 'completed', output, undefined, Date.now() - startTime, attempts);
        ctx.outputs.set(task.id, output);
        this.emit('task:complete', task.id, result);
        return result;
      } catch (err) {
        lastError = err instanceof Error ? err.message : 'Unknown error';

        if (attempts < retry.maxRetries) {
          this.emit('task:retry', task.id, attempts + 1, lastError);
          const delay = retry.backoff
            ? retry.delayMs * Math.pow(retry.backoffMultiplier ?? 2, attempts)
            : retry.delayMs;
          await this.sleep(delay);
        }
      }
    }

    const result = this.makeResult(task.id, 'failed', undefined, lastError, Date.now() - startTime, retry.maxRetries);
    this.emit('task:fail', task.id, result);
    return result;
  }

  /** 运行任务（自定义执行器 或 技能执行） */
  private async runTask(task: TaskDef, ctx: PipelineContext): Promise<unknown> {
    if (task.executor) {
      return task.executor(ctx);
    }

    // skillId 执行尚未接通：原型边界上显式失败，而非静默假执行。
    // 修复记录：此前对仅有 skillId 的任务直接返回 params ?? {}，
    // 与 PipelineBuilder.validate「必须有 executor 或 skillId」的承诺矛盾
    // （validate 放行 → 执行假成功）。后续接入 SkillExecutor 后移除此限制。
    throw new Error(
      `Task '${task.id}': skillId execution is not implemented yet ` +
        `(prototype boundary; skillId '${String(task.skillId)}' reserved). ` +
        `Provide an executor for now.`
    );
  }

  /** 带超时的执行 */
  private async withTimeout<T>(
    promise: Promise<T>,
    ms: number,
    signal: AbortSignal
  ): Promise<T> {
    return new Promise<T>((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error(`Task timed out after ${ms}ms`)), ms);
      const onAbort = () => {
        clearTimeout(timer);
        reject(new Error('Task cancelled'));
      };
      signal.addEventListener('abort', onAbort, { once: true });

      promise
        .then(result => {
          clearTimeout(timer);
          signal.removeEventListener('abort', onAbort);
          resolve(result);
        })
        .catch(err => {
          clearTimeout(timer);
          signal.removeEventListener('abort', onAbort);
          reject(err);
        });
    });
  }

  private makeResult(
    taskId: string,
    status: TaskStatus,
    output?: unknown,
    error?: string,
    duration: number = 0,
    retries: number = 0
  ): TaskResult {
    return {
      taskId,
      status,
      output,
      error,
      startedAt: new Date(Date.now() - duration).toISOString(),
      finishedAt: status === 'completed' || status === 'failed' ? new Date().toISOString() : undefined,
      duration,
      retries,
    };
  }

  private chunkArray<T>(arr: T[], size: number): T[][] {
    const chunks: T[][] = [];
    for (let i = 0; i < arr.length; i += size) {
      chunks.push(arr.slice(i, i + size));
    }
    return chunks;
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}