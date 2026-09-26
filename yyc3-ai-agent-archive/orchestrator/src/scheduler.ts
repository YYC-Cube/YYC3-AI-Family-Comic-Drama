/**
 * Orchestrator — 智能调度器
 *
 * 基于能力匹配将任务分配给最合适的 AI Family 智能体。
 * 支持多种调度策略和负载均衡。
 */
import type { AgentProfile } from '@yyc3/agent-runtime';
import type { AtomicTask, CapabilityScore, SchedulingDecision, TaskPriority } from './types.js';

export interface SchedulerConfig {
  strategy: 'capability-match' | 'round-robin' | 'load-balance';
  /** 能力匹配阈值（低于此分数不分配） */
  minScoreThreshold: number;
}

export class SmartScheduler {
  readonly config: SchedulerConfig;
  private roundRobinIndex = 0;

  constructor(config: Partial<SchedulerConfig> = {}) {
    this.config = {
      strategy: 'capability-match',
      minScoreThreshold: 0.3,
      ...config,
    };
  }

  /**
   * 为任务分配最佳智能体
   */
  schedule(task: AtomicTask, availableAgents: AgentProfile[]): SchedulingDecision {
    if (availableAgents.length === 0) {
      throw new Error(`No available agents to schedule task "${task.id}"`);
    }

    switch (this.config.strategy) {
      case 'round-robin':
        return this.roundRobinSchedule(task, availableAgents);
      case 'load-balance':
        return this.loadBalanceSchedule(task, availableAgents);
      case 'capability-match':
      default:
        return this.capabilityMatchSchedule(task, availableAgents);
    }
  }

  /**
   * 能力匹配调度
   */
  private capabilityMatchSchedule(
    task: AtomicTask,
    agents: AgentProfile[]
  ): SchedulingDecision {
    const scores = this.scoreAgents(task, agents);
    // 按分数降序排列
    scores.sort((a, b) => b.score - a.score);

    const best = scores[0];
    if (best.score < this.config.minScoreThreshold) {
      throw new Error(
        `No agent meets capability threshold for task "${task.id}". Best score: ${best.score.toFixed(2)}`
      );
    }

    return {
      taskId: task.id,
      assignedAgentId: best.agentId,
      agentName: best.agentName,
      score: best.score,
      reasoning: `匹配 ${best.matchedCapabilities.length} 项能力: ${best.matchedCapabilities.join(', ')}`,
    };
  }

  /**
   * 轮询调度
   */
  private roundRobinSchedule(
    task: AtomicTask,
    agents: AgentProfile[]
  ): SchedulingDecision {
    const agent = agents[this.roundRobinIndex % agents.length];
    this.roundRobinIndex++;
    return {
      taskId: task.id,
      assignedAgentId: agent.nameEN,
      agentName: agent.nameCN,
      score: 1.0,
      reasoning: '轮询调度',
    };
  }

  /**
   * 负载均衡调度（选择能力匹配且负载最低的）
   */
  private loadBalanceSchedule(
    task: AtomicTask,
    agents: AgentProfile[]
  ): SchedulingDecision {
    const scores = this.scoreAgents(task, agents);
    // 负载均衡：为每个智能体叠加一次独立的随机扰动（≤0.2）后再排序，
    // 避免所有任务都分配给同一智能体。
    // 修复记录：此前实现在比较器内部对两侧减去同一个 loadAdj，
    // 数学上相互抵消（(b-l)-(a-l) === b-a），扰动完全失效，退化为 capability-match。
    const perturbed = scores
      .map(entry => ({ entry, adj: entry.score - Math.random() * 0.2 }))
      .sort((a, b) => b.adj - a.adj);
    const best = perturbed[0].entry;
    return {
      taskId: task.id,
      assignedAgentId: best.agentId,
      agentName: best.agentName,
      score: best.score,
      reasoning: `负载均衡: 匹配 ${best.matchedCapabilities.length} 项能力`,
    };
  }

  /**
   * 计算所有智能体对任务的能力匹配分数
   */
  scoreAgents(task: AtomicTask, agents: AgentProfile[]): CapabilityScore[] {
    return agents.map(agent => {
      const matched: string[] = [];
      const missing: string[] = [];

      for (const cap of task.requiredCapabilities) {
        const found = agent.capabilities.some(
          ac => ac.toLowerCase().includes(cap.toLowerCase()) ||
            cap.toLowerCase().includes(ac.toLowerCase())
        );
        if (found) {
          matched.push(cap);
        } else {
          missing.push(cap);
        }
      }

      const score = task.requiredCapabilities.length > 0
        ? matched.length / task.requiredCapabilities.length
        : 0.5;

      return {
        agentId: agent.nameEN,
        agentName: agent.nameCN,
        score,
        matchedCapabilities: matched,
        missingCapabilities: missing,
      };
    });
  }

  /**
   * 按优先级排序任务
   */
  sortByPriority(tasks: AtomicTask[]): AtomicTask[] {
    const priorityOrder: Record<TaskPriority, number> = {
      critical: 0,
      high: 1,
      medium: 2,
      low: 3,
    };
    return [...tasks].sort(
      (a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]
    );
  }

  /**
   * 获取可执行任务（依赖已满足的任务）
   */
  getReadyTasks(tasks: AtomicTask[]): AtomicTask[] {
    const completedIds = new Set(
      tasks.filter(t => t.status === 'completed').map(t => t.id)
    );
    return tasks.filter(
      t =>
        t.status === 'pending' &&
        t.dependencies.every(depId => completedIds.has(depId))
    );
  }
}