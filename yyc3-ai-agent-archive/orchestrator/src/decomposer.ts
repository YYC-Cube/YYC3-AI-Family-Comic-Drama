/**
 * Orchestrator — 任务分解器
 *
 * 将高层目标分解为可执行的原子任务，基于能力图谱映射。
 * 支持两大类分解策略：
 * 1. 基于规则（Rule-based）：按能力关键词匹配分解
 * 2. 基于 LLM（预留接口）：调用 LLM 进行语义分解
 */
import type { AtomicTask, DecompositionResult, TaskPriority } from './types.js';

/** 任务分解器配置 */
export interface DecomposerConfig {
  /** 分解策略 */
  strategy: 'rule-based' | 'llm';
  /** LLM 端点（strategy=llm 时使用） */
  llmEndpoint?: string;
  /** 最大子任务数 */
  maxSubTasks: number;
  /** 默认优先级 */
  defaultPriority: TaskPriority;
}

/**
 * 能力 → 子任务模板映射
 * 基于规则的任务分解知识库
 */
const CAPABILITY_TASK_TEMPLATES: Record<string, string[]> = {
  '自然语言理解': ['意图分析', '实体提取', '语义消歧'],
  '语义推理': ['逻辑推理', '因果分析', '类比推理'],
  '意图分类': ['意图识别', '分类路由', '置信度评估'],
  '深度数据分析': ['数据清洗', '特征提取', '模式识别'],
  '归纳推理': ['数据聚合', '规律总结', '假设生成'],
  '代码审查': ['静态分析', '模式检测', '规范检查'],
  '性能分析': ['性能剖析', '瓶颈识别', '优化建议'],
  '安全防护': ['威胁建模', '漏洞扫描', '风险评估'],
  '创意生成': ['头脑风暴', '方案设计', '原型构思'],
  '推荐算法': ['用户画像', '候选生成', '排序优化'],
  '知识图谱构建': ['实体识别', '关系抽取', '图谱融合'],
  '运筹优化': ['资源建模', '约束分析', '最优求解'],
};

/** 通用分解模板（当无法匹配具体能力时） */
const GENERIC_DECOMPOSITION: Record<string, string[]> = {
  analyze: ['收集信息', '分析数据', '得出结论'],
  build: ['需求分析', '架构设计', '逐步实现', '测试验证'],
  optimize: ['现状评估', '瓶颈识别', '方案设计', '实施优化', '效果验证'],
  review: ['材料收集', '逐项审查', '问题汇总', '改进建议'],
  plan: ['目标定义', '资源评估', '方案制定', '风险分析', '执行计划'],
  default: ['理解需求', '制定方案', '逐步执行', '验证结果'],
};

export class TaskDecomposer {
  readonly config: DecomposerConfig;

  constructor(config: Partial<DecomposerConfig> = {}) {
    this.config = {
      strategy: 'rule-based',
      maxSubTasks: 10,
      defaultPriority: 'medium',
      ...config,
    };
  }

  /**
   * 分解高层目标为原子任务
   */
  decompose(goal: string, requiredCapabilities: string[]): DecompositionResult {
    if (this.config.strategy === 'llm') {
      return this.decomposeViaLLM(goal, requiredCapabilities);
    }
    return this.decomposeViaRules(goal, requiredCapabilities);
  }

  /**
   * 基于规则分解
   */
  private decomposeViaRules(goal: string, capabilities: string[]): DecompositionResult {
    const tasks: Omit<AtomicTask, 'id' | 'status' | 'createdAt'>[] = [];
    const seen = new Set<string>();

    // 1. 尝试匹配能力模板
    for (const cap of capabilities) {
      const templates = CAPABILITY_TASK_TEMPLATES[cap];
      if (templates) {
        for (const t of templates) {
          if (!seen.has(t) && tasks.length < this.config.maxSubTasks) {
            seen.add(t);
            tasks.push({
              description: t,
              requiredCapabilities: [cap],
              priority: this.config.defaultPriority,
              dependencies: [],
              estimatedComplexity: 3,
            });
          }
        }
      }
    }

    // 2. 如果能力匹配不足，使用通用模板
    if (tasks.length === 0) {
      const template = this.matchGenericTemplate(goal);
      tasks.push(...template.map((t, i) => ({
        description: t,
        requiredCapabilities: capabilities.slice(0, 1),
        priority: this.config.defaultPriority,
        dependencies: i > 0 ? [template[i - 1]] : [],
        estimatedComplexity: Math.ceil(10 / template.length),
      })));
    }

    // 3. 设置依赖关系（按顺序依赖）
    for (let i = 1; i < tasks.length; i++) {
      if (tasks[i].dependencies.length === 0) {
        tasks[i].dependencies = [tasks[i - 1].description];
      }
    }

    // 4. 限制任务数量
    const finalTasks = tasks.slice(0, this.config.maxSubTasks);

    return {
      tasks: finalTasks,
      reasoning: `基于 ${capabilities.length} 项能力，将目标「${goal}」分解为 ${finalTasks.length} 个子任务`,
    };
  }

  /**
   * 匹配通用任务模板
   */
  private matchGenericTemplate(goal: string): string[] {
    const lower = goal.toLowerCase();
    for (const [keyword, template] of Object.entries(GENERIC_DECOMPOSITION)) {
      if (lower.includes(keyword)) {
        return template;
      }
    }
    return GENERIC_DECOMPOSITION.default;
  }

  /**
   * 基于 LLM 分解（预留接口）
   */
  private decomposeViaLLM(goal: string, capabilities: string[]): DecompositionResult {
    throw new Error(
      `LLM decomposition not yet implemented. Configure llmEndpoint to enable. Goal: "${goal}"`
    );
  }
}