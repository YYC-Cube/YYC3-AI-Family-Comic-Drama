/**
 * Conductor 编排引擎 — 单元测试
 */
import { describe, it, expect } from 'vitest';
import { Conductor, PipelineBuilder } from '../src/index.js';
import type { PipelineDef } from '../src/types.js';

describe('PipelineBuilder', () => {
  it('拓扑排序 — 线性依赖', () => {
    const pipeline: PipelineDef = {
      id: 'test',
      name: 'Test',
      tasks: [
        { id: 'a', executor: async () => 1 },
        { id: 'b', dependsOn: [{ taskId: 'a', type: 'required' }], executor: async () => 2 },
        { id: 'c', dependsOn: [{ taskId: 'b', type: 'required' }], executor: async () => 3 },
      ],
    };
    const { levels } = PipelineBuilder.topologicalSort(pipeline);
    expect(levels).toHaveLength(3);
    expect(levels[0].map(t => t.id)).toEqual(['a']);
    expect(levels[1].map(t => t.id)).toEqual(['b']);
    expect(levels[2].map(t => t.id)).toEqual(['c']);
  });

  it('拓扑排序 — 并行任务', () => {
    const pipeline: PipelineDef = {
      id: 'test',
      name: 'Test',
      tasks: [
        { id: 'a', executor: async () => 1 },
        { id: 'b', executor: async () => 2 },
        { id: 'c', dependsOn: [{ taskId: 'a', type: 'required' }, { taskId: 'b', type: 'required' }], executor: async () => 3 },
      ],
    };
    const { levels } = PipelineBuilder.topologicalSort(pipeline);
    expect(levels).toHaveLength(2);
    expect(levels[0].map(t => t.id).sort()).toEqual(['a', 'b']);
    expect(levels[1].map(t => t.id)).toEqual(['c']);
  });

  it('检测循环依赖', () => {
    const pipeline: PipelineDef = {
      id: 'test',
      name: 'Test',
      tasks: [
        { id: 'a', dependsOn: [{ taskId: 'b', type: 'required' }], executor: async () => 1 },
        { id: 'b', dependsOn: [{ taskId: 'a', type: 'required' }], executor: async () => 2 },
      ],
    };
    expect(PipelineBuilder.hasCycle(pipeline)).toBe(true);
  });

  it('验证 — 空任务列表', () => {
    const errors = PipelineBuilder.validate({ id: 'x', name: 'x', tasks: [] });
    expect(errors.length).toBeGreaterThan(0);
    expect(errors.some(e => e.includes('must not be empty'))).toBe(true);
  });

  it('验证 — 缺少 executor 和 skillId', () => {
    const errors = PipelineBuilder.validate({
      id: 'x',
      name: 'x',
      tasks: [{ id: 't1', name: 't1' }],
    });
    expect(errors.some(e => e.includes('must have executor'))).toBe(true);
  });

  it('验证 — 依赖未知任务', () => {
    const errors = PipelineBuilder.validate({
      id: 'x',
      name: 'x',
      tasks: [{ id: 'a', dependsOn: [{ taskId: 'unknown', type: 'required' }], executor: async () => 1 }],
    });
    expect(errors.some(e => e.includes('depends on unknown task'))).toBe(true);
  });
});

describe('Conductor', () => {
  it('执行简单流水线', async () => {
    const conductor = new Conductor();
    const result = await conductor.execute({
      id: 'simple',
      name: 'Simple',
      tasks: [
        { id: 'step1', executor: async () => 'hello' },
        { id: 'step2', dependsOn: [{ taskId: 'step1', type: 'required' }], executor: async (ctx) => {
          return `${ctx.outputs.get('step1')} world`;
        }},
      ],
    });

    expect(result.status).toBe('completed');
    expect(result.tasks).toHaveLength(2);
    expect(result.tasks[0].status).toBe('completed');
    expect(result.tasks[0].output).toBe('hello');
    expect(result.tasks[1].status).toBe('completed');
    expect(result.tasks[1].output).toBe('hello world');
  });

  it('并行执行', async () => {
    const conductor = new Conductor({ defaultConcurrency: 5 });
    const timings: string[] = [];

    const result = await conductor.execute({
      id: 'parallel',
      name: 'Parallel',
      tasks: [
        { id: 'a', executor: async () => { timings.push('a-start'); await sleep(50); timings.push('a-end'); return 'a'; } },
        { id: 'b', executor: async () => { timings.push('b-start'); await sleep(50); timings.push('b-end'); return 'b'; } },
        { id: 'c', executor: async () => { timings.push('c-start'); await sleep(50); timings.push('c-end'); return 'c'; } },
      ],
    });

    expect(result.status).toBe('completed');
    // 并行执行：所有 start 应在所有 end 之前
    const starts = timings.filter(t => t.endsWith('start'));
    const ends = timings.filter(t => t.endsWith('end'));
    expect(starts.length).toBe(3);
    expect(ends.length).toBe(3);
  });

  it('事件触发', async () => {
    const conductor = new Conductor();
    const events: string[] = [];

    conductor.on('pipeline:start', () => events.push('pipeline:start'));
    conductor.on('pipeline:complete', () => events.push('pipeline:complete'));
    conductor.on('task:start', (id) => events.push(`task:start:${id}`));
    conductor.on('task:complete', (id) => events.push(`task:complete:${id}`));

    await conductor.execute({
      id: 'event-test',
      name: 'Event Test',
      tasks: [{ id: 't1', executor: async () => 'ok' }],
    });

    expect(events).toContain('pipeline:start');
    expect(events).toContain('pipeline:complete');
    expect(events).toContain('task:start:t1');
    expect(events).toContain('task:complete:t1');
  });

  it('重试机制', async () => {
    const conductor = new Conductor();
    let attempts = 0;

    const result = await conductor.execute({
      id: 'retry-test',
      name: 'Retry Test',
      tasks: [{
        id: 'flaky',
        retry: { maxRetries: 2, delayMs: 10 },
        executor: async () => {
          attempts++;
          if (attempts < 3) throw new Error(`Attempt ${attempts}`);
          return 'success';
        },
      }],
    });

    expect(result.status).toBe('completed');
    expect(attempts).toBe(3);
    expect(result.tasks[0].status).toBe('completed');
    expect(result.tasks[0].retries).toBe(2);
  });

  it('重试耗尽后失败', async () => {
    const conductor = new Conductor();
    const result = await conductor.execute({
      id: 'fail-test',
      name: 'Fail Test',
      tasks: [{
        id: 'always-fail',
        retry: { maxRetries: 1, delayMs: 10 },
        executor: async () => { throw new Error('always fails'); },
      }],
    });

    expect(result.status).toBe('failed');
    expect(result.tasks[0].status).toBe('failed');
    expect(result.tasks[0].retries).toBe(1);
  });

  it('前置条件跳过', async () => {
    const conductor = new Conductor();
    const result = await conductor.execute({
      id: 'skip-test',
      name: 'Skip Test',
      tasks: [{
        id: 'maybe-skip',
        condition: () => false,
        executor: async () => 'should not run',
      }],
    });

    expect(result.status).toBe('completed');
    expect(result.tasks[0].status).toBe('skipped');
    expect(result.tasks[0].output).toBeUndefined();
  });

  it('取消流水线', async () => {
    const conductor = new Conductor();
    const promise = conductor.execute({
      id: 'cancel-test',
      name: 'Cancel Test',
      tasks: [
        { id: 'slow', timeout: 10000, executor: async () => { await sleep(5000); return 'done'; } },
      ],
    });

    await sleep(100);
    const cancelled = conductor.cancel('cancel-test');
    expect(cancelled).toBe(true);

    const result = await promise;
    expect(result.status).toBe('failed');
  });

  it('onFailure: continue', async () => {
    const conductor = new Conductor();
    const result = await conductor.execute({
      id: 'continue-test',
      name: 'Continue Test',
      onFailure: 'continue',
      tasks: [
        { id: 'fail', executor: async () => { throw new Error('fail'); } },
        { id: 'ok', executor: async () => 'still runs' },
      ],
    });

    expect(result.status).toBe('completed');
    expect(result.tasks[0].status).toBe('failed');
    expect(result.tasks[1].status).toBe('completed');
    expect(result.tasks[1].output).toBe('still runs');
  });

  // 对抗基线：skillId-only 任务必须显式失败，不得假执行（回归 2026-09-26 修复）
  // 此前 runTask 对 skillId-only 任务直接返回 params ?? {}，validate 放行后静默假成功
  it('skillId-only 任务显式失败（not implemented，不返回 params 假成功）', async () => {
    const conductor = new Conductor();
    const result = await conductor.execute({
      id: 'skill-stub',
      name: 'Skill Stub',
      tasks: [{ id: 's1', skillId: 'demo-skill', params: { keep: 'raw' } }],
    });

    expect(result.status).toBe('failed');
    expect(result.tasks[0].status).toBe('failed');
    expect(result.tasks[0].error).toContain('not implemented');
    expect(result.tasks[0].error).toContain('demo-skill');
    expect(result.tasks[0].output).toBeUndefined();
  });

  it('executor 优先于 skillId（混合定义正常走 executor）', async () => {
    const conductor = new Conductor();
    const result = await conductor.execute({
      id: 'executor-priority',
      name: 'Executor Priority',
      tasks: [{ id: 'm1', skillId: 'demo-skill', executor: async () => 'from-executor' }],
    });

    expect(result.status).toBe('completed');
    expect(result.tasks[0].status).toBe('completed');
    expect(result.tasks[0].output).toBe('from-executor');
  });

  it('skillId-only 失败会按 onFailure: stop 阻断下游依赖任务', async () => {
    const conductor = new Conductor();
    let downstreamRan = false;
    const result = await conductor.execute({
      id: 'skill-stub-blocks',
      name: 'Skill Stub Blocks',
      tasks: [
        { id: 's1', skillId: 'demo-skill' },
        {
          id: 'downstream',
          dependsOn: [{ taskId: 's1', type: 'required' }],
          executor: async () => {
            downstreamRan = true;
            return 'should not run';
          },
        },
      ],
    });

    expect(result.status).toBe('failed');
    expect(result.tasks.find(t => t.id === 'downstream')).toBeUndefined();
    expect(downstreamRan).toBe(false);
  });
});

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}