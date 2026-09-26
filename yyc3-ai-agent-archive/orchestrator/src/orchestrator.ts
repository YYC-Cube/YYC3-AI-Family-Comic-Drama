/**
 * Orchestrator — 智能编排引擎
 *
 * 整合任务分解、智能调度、工作流管理，实现：
 * 目标 → 任务分解 → 能力匹配 → 智能调度 → 并行执行 → 结果汇总
 */
import type { AgentProfile } from '@yyc3/agent-runtime';
import { EventEmitter } from 'eventemitter3';
import { TaskDecomposer } from './decomposer.js';
import { SmartScheduler } from './scheduler.js';
import type {
  AtomicTask,
  OrchestratorConfig,
  OrchestratorEvents,
  SchedulingDecision,
  TaskPriority,
  Workflow,
} from './types.js';

const DEFAULT_CONFIG: OrchestratorConfig = {
  maxConcurrency: 5,
  defaultPriority: 'medium',
  schedulingStrategy: 'capability-match',
  autoRetry: true,
  maxRetries: 3,
};

let counter = 0;

export class Orchestrator extends EventEmitter<OrchestratorEvents> {
  readonly config: OrchestratorConfig;
  readonly decomposer: TaskDecomposer;
  readonly scheduler: SmartScheduler;

  private workflows = new Map<string, Workflow>();
  private taskHandlers = new Map<string, (task: AtomicTask) => Promise<unknown>>();

  constructor(config: Partial<OrchestratorConfig> = {}) {
    super();
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.decomposer = new TaskDecomposer();
    this.scheduler = new SmartScheduler({ strategy: this.config.schedulingStrategy });
  }

  /**
   * 注册任务执行器
   */
  registerHandler(capability: string, handler: (task: AtomicTask) => Promise<unknown>): void {
    this.taskHandlers.set(capability, handler);
  }

  /**
   * 创建并执行工作流
   * 完整流程：目标 → 分解 → 调度 → 执行
   */
  async execute(
    goal: string,
    requiredCapabilities: string[],
    availableAgents: AgentProfile[],
    priority?: TaskPriority
  ): Promise<Workflow> {
    // 1. 创建 Workflow
    const workflow: Workflow = {
      id: `wf-${++counter}`,
      name: goal,
      goal,
      tasks: [],
      status: 'pending',
      createdAt: new Date().toISOString(),
    };

    // 2. 分解任务
    const result = this.decomposer.decompose(goal, requiredCapabilities);
    const tasks: AtomicTask[] = result.tasks.map((t, i) => ({
      ...t,
      id: `${workflow.id}-t${i + 1}`,
      status: 'pending',
      priority: priority ?? t.priority,
      createdAt: new Date().toISOString(),
      // 修复依赖：将描述文本依赖转为实际任务 ID 依赖
      dependencies: t.dependencies.map(desc => {
        const depIdx = result.tasks.findIndex(rt => rt.description === desc);
        return depIdx >= 0 ? `${workflow.id}-t${depIdx + 1}` : desc;
      }),
    }));
    workflow.tasks = tasks;
    this.workflows.set(workflow.id, workflow);
    this.emit('workflow:created', workflow);
    this.emit('task:decomposed', goal, tasks);

    // 3. 调度 - 分配智能体
    const decisions: SchedulingDecision[] = [];
    for (const task of tasks) {
      try {
        const decision = this.scheduler.schedule(task, availableAgents);
        task.assignedAgentId = decision.assignedAgentId;
        decisions.push(decision);
        this.emit('scheduled', decision);
      } catch {
        // 如果无法调度，标记为失败
        task.status = 'failed';
        task.error = `No suitable agent found for capabilities: ${task.requiredCapabilities.join(', ')}`;
        this.emit('task:failed', task, task.error);
      }
    }

    // 4. 并行执行
    try {
      workflow.status = 'running';
      await this.executeWorkflow(workflow);
      workflow.status = 'completed';
      workflow.completedAt = new Date().toISOString();
      this.emit('workflow:completed', workflow);
    } catch (err) {
      workflow.status = 'failed';
      const errorMsg = err instanceof Error ? err.message : String(err);
      this.emit('workflow:failed', workflow, errorMsg);
    }

    return workflow;
  }

  /**
   * 执行工作流中的所有任务
   */
  private async executeWorkflow(workflow: Workflow): Promise<void> {
    let remaining = workflow.tasks.filter(t => t.status !== 'failed');
    const retryCount = new Map<string, number>();

    while (remaining.length > 0) {
      // 获取可执行任务（依赖已满足），传入完整任务列表以正确计算依赖
      const ready = this.scheduler.getReadyTasks(workflow.tasks);
      if (ready.length === 0) {
        // 检查是否有卡住的任务（依赖了失败的任务，需基于全量任务判断）
        const failedIds = new Set(
          workflow.tasks.filter(t => t.status === 'failed').map(t => t.id)
        );
        const stuck = workflow.tasks.filter(
          t => t.status === 'pending' && t.dependencies.some(d => failedIds.has(d))
        );
        if (stuck.length > 0) {
          for (const t of stuck) {
            t.status = 'failed';
            t.error = 'Dependency failed';
            this.emit('task:failed', t, t.error);
          }
        }
        break;
      }

      // 并发限制
      const batch = ready.slice(0, this.config.maxConcurrency);

      // 执行批次
      const results = await Promise.allSettled(
        batch.map(task => this.executeTask(task))
      );

      results.forEach((r, i) => {
        if (r.status === 'fulfilled') {
          batch[i].status = 'completed';
          batch[i].output = r.value;
          batch[i].completedAt = new Date().toISOString();
          this.emit('task:completed', batch[i]);
        } else {
          batch[i].error = r.reason instanceof Error ? r.reason.message : String(r.reason);
          const currentRetries = retryCount.get(batch[i].id) ?? 0;
          if (this.config.autoRetry && currentRetries < this.config.maxRetries) {
            batch[i].status = 'pending';
            retryCount.set(batch[i].id, currentRetries + 1);
          } else {
            batch[i].status = 'failed';
            this.emit('task:failed', batch[i], batch[i].error!);
          }
        }
      });

      remaining = remaining.filter(t => t.status === 'pending');
    }

    // 检查是否全部完成
    const allDone = workflow.tasks.every(t => t.status === 'completed');
    if (!allDone) {
      const failedCount = workflow.tasks.filter(t => t.status === 'failed').length;
      throw new Error(`Workflow partially completed: ${failedCount} task(s) failed`);
    }
  }

  /**
   * 执行单个任务
   */
  private async executeTask(task: AtomicTask): Promise<unknown> {
    task.status = 'running';
    task.startedAt = new Date().toISOString();
    this.emit('task:started', task);

    // 尝试找到匹配的处理器
    for (const cap of task.requiredCapabilities) {
      const handler = this.taskHandlers.get(cap);
      if (handler) {
        return handler(task);
      }
    }

    // 默认：模拟执行
    return Promise.resolve({ result: `Task "${task.description}" completed` });
  }

  /**
   * 获取工作流
   */
  getWorkflow(id: string): Workflow | undefined {
    return this.workflows.get(id);
  }

  /**
   * 列出所有工作流
   */
  listWorkflows(): Workflow[] {
    return Array.from(this.workflows.values());
  }
}
