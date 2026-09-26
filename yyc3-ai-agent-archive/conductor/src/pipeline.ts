/**
 * Conductor — 流水线 DAG 构建器
 *
 * 负责验证流水线定义、构建依赖图、拓扑排序
 */
import type { PipelineDef, TaskDef } from './types.js';

export class PipelineBuilder {
  /** 验证流水线定义 */
  static validate(pipeline: PipelineDef): string[] {
    const errors: string[] = [];
    const taskIds = new Set(pipeline.tasks.map(t => t.id));

    if (!pipeline.id) errors.push('pipeline.id is required');
    if (!pipeline.tasks?.length) errors.push('pipeline.tasks must not be empty');

    for (const task of pipeline.tasks) {
      if (!task.id) {
        errors.push('task.id is required');
        continue;
      }
      if (!task.executor && !task.skillId) {
        errors.push(`Task '${task.id}': must have executor or skillId`);
      }
      if (task.dependsOn) {
        for (const dep of task.dependsOn) {
          if (!taskIds.has(dep.taskId)) {
            errors.push(`Task '${task.id}': depends on unknown task '${dep.taskId}'`);
          }
        }
      }
    }

    return errors;
  }

  /** 拓扑排序，返回执行层级 */
  static topologicalSort(pipeline: PipelineDef): { levels: TaskDef[][]; allTasks: TaskDef[] } {
    const taskMap = new Map(pipeline.tasks.map(t => [t.id, t]));
    const inDegree = new Map<string, number>();
    const dependents = new Map<string, string[]>();

    for (const task of pipeline.tasks) {
      inDegree.set(task.id, 0);
      dependents.set(task.id, []);
    }

    for (const task of pipeline.tasks) {
      if (task.dependsOn) {
        for (const dep of task.dependsOn) {
          inDegree.set(task.id, (inDegree.get(task.id) || 0) + 1);
          dependents.get(dep.taskId)?.push(task.id);
        }
      }
    }

    const levels: TaskDef[][] = [];
    const processed = new Set<string>();

    while (processed.size < pipeline.tasks.length) {
      const currentLevel: TaskDef[] = [];
      for (const task of pipeline.tasks) {
        if (processed.has(task.id)) continue;
        if (inDegree.get(task.id) === 0) {
          currentLevel.push(task);
        }
      }

      if (currentLevel.length === 0) {
        throw new Error('Circular dependency detected in pipeline');
      }

      levels.push(currentLevel);
      for (const task of currentLevel) {
        processed.add(task.id);
        for (const dep of dependents.get(task.id) || []) {
          inDegree.set(dep, (inDegree.get(dep) || 0) - 1);
        }
      }
    }

    return { levels, allTasks: pipeline.tasks };
  }

  /** 检测循环依赖 */
  static hasCycle(pipeline: PipelineDef): boolean {
    try {
      this.topologicalSort(pipeline);
      return false;
    } catch {
      return true;
    }
  }
}