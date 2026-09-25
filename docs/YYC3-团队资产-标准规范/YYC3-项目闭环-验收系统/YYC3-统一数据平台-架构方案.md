---
file: YYC3-统一数据平台-架构方案.md
description: YYC³ 验收系统 — 统一数据平台架构设计与实施方案
author: YanYuCloudCube Team <admin@0379.email>
version: v2.0.0
created: 2026-05-25
updated: 2026-05-30
status: draft
tags: [数据平台],[架构设计],[数据联动],[可观测性]
category: architecture
language: zh-CN
audience: architects,data-engineers,devops,platform-engineers
complexity: advanced
---


## 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
| ---- | ---- | -------- | ---- |
| v2.0.0 | 2026-05-30 | 版本迭代同步 | YanYuCloudCube Team |
| v1.0.0 | 2026-04-03 | 初始版本 | YanYuCloudCube Team |

<div align="center">

# YYC³（YanYuCloudCube）智能应用链

## 统一数据平台架构方案

> **_YanYuCloudCube_**
> _言启象限 | 语枢未来_
> **_Words Initiate Quadrants, Language Serves as Core for Future_**
> _万象归元于云枢 | 深栈智启新纪元_

---

| 属性         | 值                                    |
| ------------ | ------------------------------------- |
| **文档版本** | v2.1.0 Draft                         |
| **发布日期** | 2026-05-25                            |
| **文档性质** | 架构设计方案（技术白皮书）            |
| **适用范围** | YYC³ 全部13个验收阶段的数据整合       |
| **技术栈**   | TypeScript + PostgreSQL + Redis + Grafana |

</div>

---

## 📋 文档目标与定位

### 核心使命

构建**YYC³ 统一数据平台**，打通全部13个验收阶段的数据孤岛，实现：
- **全局数据聚合** - 所有阶段产生的指标、报告、日志统一存储和查询
- **实时可视化** - 提供全局质量仪表板，实时监控项目健康状态
- **智能分析** - 跨阶段关联分析，发现深层问题和优化机会
- **闭环驱动** - 数据驱动的持续改进和决策支持

### 战略价值

```
┌─────────────────────────────────────────────────────────────┐
│                  统一数据平台价值链                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│   │ 数据采集  │ →  │ 数据处理  │ →  │ 数据服务  │              │
│   │ (13个阶段) │    │ (ETL)    │    │ (API/查询) │              │
│   └──────────┘    └──────────┘    └──────────┘              │
│        ↓              ↓              ↓                      │
│   ┌─────────────────────────────────────────────────┐       │
│   │           业务价值实现                             │       │
│   │  • 全局视图 • 智能洞察 • 自动化决策 • 持续优化     │       │
│   └─────────────────────────────────────────────────┘       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏗️ 一、整体架构设计

### 1.1 架构分层图

```
┌─────────────────────────────────────────────────────────────────┐
│                        应用层 (Presentation)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Grafana     │  │ 自定义Dashboard│  │ API Gateway │             │
│  │ Dashboard   │  │ (React App) │  │ (REST/GraphQL)│            │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
├─────────────────────────────────────────────────────────────────┤
│                        服务层 (Service)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Query Engine│  │ Alert Engine│  │ Report Gen  │             │
│  │ (SQL/NoSQL) │  │ (告警规则)  │  │ (报告生成)  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
├─────────────────────────────────────────────────────────────────┤
│                        数据层 (Data)                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │ PostgreSQL      │  │ Redis Cache     │  │ Object Storage  │  │
│  │ (时序/关系数据) │  │ (热数据/会话)   │  │ (文件/报告)    │  │
│  └─────────────────┘  └─────────────────┘  └────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                        采集层 (Ingestion)                        │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ Data Collectors (13个阶段 × N种数据源)                    │ │
│  │ • CI/CD Hooks • Test Runners • Linters • Security Scanners│ │
│  │ • Performance Monitors • AI Reviewers • Manual Inputs     │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 核心组件说明

```typescript
// src/data-platform/core/types.ts

/** 平台核心类型定义 */
interface UnifiedDataPlatform {
  /** 数据采集器 */
  collectors: DataCollector[];
  
  /** 数据处理器 */
  processors: DataProcessor[];
  
  /** 存储引擎 */
  storage: {
    primary: PostgreSQLConfig;
    cache: RedisConfig;
    objectStorage: S3Config;
  };
  
  /** 服务层 */
  services: {
    queryEngine: QueryEngine;
    alertEngine: AlertEngine;
    reportGenerator: ReportGenerator;
  };
  
  /** 应用层 */
  applications: {
    grafanaDashboards: DashboardConfig[];
    customUI: ReactAppConfig;
    apiGateway: APIGatewayConfig;
  };
}

/** 数据采集器接口 */
interface DataCollector {
  id: string; // 唯一标识符
  stageId: string; // 关联的验收阶段 (如 "stage-01", "stage-11")
  name: string; // 显示名称
  version: string;
  
  /** 触发方式 */
  trigger: {
    type: 'event_driven' | 'scheduled' | 'manual';
    events?: string[]; // 如 ['pr.created', 'test.completed']
    schedule?: string; // Cron表达式
  };
  
  /** 采集的数据类型 */
  dataTypes: DataType[];
  
  /** 采集配置 */
  config: CollectorConfig;
}

/** 支持的数据类型 */
type DataType = 
  | 'metrics'          // 数值型指标 (覆盖率、响应时间等)
  | 'logs'             // 日志文本
  | 'events'           // 事件记录 (PR创建、测试通过等)
  | 'reports'          // 结构化报告 (JSON/PDF)
  | 'artifacts'        // 产物文件 (截图、日志文件)
  | 'feedback'         // 用户反馈
  | 'predictions';     // AI预测结果
```

---

## 📊 二、数据模型设计

### 2.1 核心实体关系图

```typescript
// src/data-platform/models/schema.ts

/** 项目实体 */
interface Project {
  id: string;
  name: string;
  repositoryUrl: string;
  techStack: TechStackInfo;
  createdAt: Date;
  updatedAt: Date;
  
  // 关联关系
  stages: AcceptanceStage[];
  runs: AcceptanceRun[];
  metrics: ProjectMetrics;
}

/** 验收阶段实体 */
interface AcceptanceStage {
  id: string; // "stage-01" ~ "stage-13"
  name: string;
  order: number; // 1-13
  category: 'foundation' | 'testing' | 'system' | 'intelligence';
  
  config: StageConfig;
  thresholds: StageThresholds;
  
  // 关联关系
  project: Project;
  runs: StageRun[];
}

/** 单次验收运行 */
interface AcceptanceRun {
  id: string;
  projectId: string;
  stageId: string;
  
  status: 'running' | 'passed' | 'failed' | 'skipped' | 'error';
  startedAt: Date;
  completedAt?: Date;
  duration?: number; // ms
  
  // 结果数据
  results: RunResults;
  artifacts: Artifact[];
  metadata: RunMetadata;
  
  // 关联的度量指标
  metrics: MetricPoint[];
  logs: LogEntry[];
  events: EventRecord[];
}

/** 运行结果 */
interface RunResults {
  score: number; // 0-100
  grade: 'A' | 'B' | 'C' | 'D' | 'F';
  
  criteriaResults: CriteriaResult[]; // 各检查项结果
  summary: string;
  findings: Finding[];
  recommendations: Recommendation[];
}

/** 度量指标点 */
interface MetricPoint {
  id: string;
  runId: string;
  name: string; // "coverage", "lcp", "defect_count"
  value: number;
  unit: string; // "%", "ms", "count"
  tags: Record<string, string>; // { "branch": "main", "env": "prod" }
  timestamp: Date;
}
```

### 2.2 数据库表结构设计

```sql
-- src/data-platform/storage/schema.sql

-- 项目表
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    repository_url TEXT NOT NULL,
    tech_stack JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 验收阶段定义表
CREATE TABLE acceptance_stages (
    id VARCHAR(20) PRIMARY KEY, -- "stage-01" to "stage-13"
    name VARCHAR(255) NOT NULL,
    stage_order INT NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN ('foundation', 'testing', 'system', 'intelligence')),
    config JSONB NOT NULL,
    thresholds JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 验收运行记录表
CREATE TABLE acceptance_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    stage_id VARCHAR(20) REFERENCES acceptance_stages(id),
    
    status VARCHAR(20) NOT NULL DEFAULT 'running',
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_ms INT,
    
    -- 结果摘要
    score INT CHECK (score >= 0 AND score <= 100),
    grade CHAR(1) CHECK (grade IN ('A', 'B', 'C', 'D', 'F')),
    
    -- 详细结果 (JSONB)
    results JSONB,
    
    -- 元数据
    triggered_by VARCHAR(100),
    commit_sha VARCHAR(40),
    branch_name VARCHAR(100),
    pr_number INT,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 时序指标表 (用于趋势分析)
CREATE TABLE metrics (
    id BIGSERIAL PRIMARY KEY,
    run_id UUID REFERENCES acceptance_runs(id),
    metric_name VARCHAR(100) NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    unit VARCHAR(20),
    tags JSONB NOT NULL DEFAULT '{}',
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 创建索引以加速查询
CREATE INDEX idx_metrics_run_id ON metrics(run_id);
CREATE INDEX idx_metrics_name_time ON metrics(metric_name, recorded_at);
CREATE INDEX idx_runs_project_stage ON acceptance_runs(project_id, stage_id);
CREATE INDEX idx_runs_status_time ON acceptance_runs(status, started_at);
```

---

## 🔌 三、数据采集器实现

### 3.1 采集器基类

```typescript
// src/data-platform/collectors/base-collector.ts

import { EventEmitter } from 'events';

/**
 * 数据采集器抽象基类
 * 所有13个阶段的采集器都继承此类
 */
abstract class BaseDataCollector extends EventEmitter {
  abstract readonly collectorId: string;
  abstract readonly stageId: string;
  abstract readonly name: string;
  abstract readonly supportedDataTypes: DataType[];
  
  protected config: CollectorConfig;
  private isRunning: boolean = false;
  
  constructor(config: CollectorConfig) {
    super();
    this.config = config;
  }
  
  /**
   * 初始化采集器
   */
  async initialize(): Promise<void> {
    this.log('info', `初始化采集器: ${this.name}`);
    await this.onInitialize();
    this.isRunning = true;
  }
  
  /**
   * 执行数据采集
   * @param context 采集上下文 (触发事件、项目信息等)
   */
  async collect(context: CollectionContext): Promise<CollectionResult> {
    if (!this.isRunning) {
      throw new Error(`采集器 ${this.name} 未初始化`);
    }
    
    const startTime = Date.now();
    this.log('info', `开始采集数据: ${this.name}`, context);
    
    try {
      // 1. 前置校验
      await this.validateContext(context);
      
      // 2. 执行具体采集逻辑
      const rawData = await this.doCollect(context);
      
      // 3. 数据标准化
      const normalizedData = await this.normalize(rawData);
      
      // 4. 数据验证
      const validatedData = this.validate(normalizedData);
      
      const duration = Date.now() - startTime;
      const result: CollectionResult = {
        success: true,
        collectorId: this.collectorId,
        stageId: this.stageId,
        timestamp: new Date(),
        duration,
        data: validatedData,
        metadata: {
          context,
          rawDataSize: JSON.stringify(rawData).length,
          normalizedDataSize: JSON.stringify(validatedData).length,
        },
      };
      
      this.emit('collected', result);
      this.log('info', `采集完成: ${this.name} (${duration}ms)`, { dataSize: validatedData.length });
      
      return result;
      
    } catch (error) {
      const duration = Date.now() - startTime;
      const errorResult: CollectionResult = {
        success: false,
        collectorId: this.collectorId,
        stageId: this.stageId,
        timestamp: new Date(),
        duration,
        error: error.message,
        metadata: { context },
      };
      
      this.emit('error', errorResult);
      this.log('error', `采集失败: ${this.name}`, { error: error.message, duration });
      
      return errorResult;
    }
  }
  
  /** 子类实现的采集逻辑 */
  protected abstract doCollect(context: CollectionContext): Promise<RawData[]>;
  
  /** 子类实现的初始化逻辑 */
  protected async onInitialize(): Promise<void> {}
  
  /** 子类实现的上下文校验 */
  protected async validateContext(context: CollectionContext): Promise<void> {
    // 默认实现：无校验
  }
  
  /** 数据标准化 */
  protected async normalize(rawData: RawData[]): Promise<NormalizedData[]> {
    return rawData.map(item => ({
      ...item,
      collectorId: this.collectorId,
      stageId: this.stageId,
      normalizedAt: new Date(),
    }));
  }
  
  /** 数据验证 */
  private validate(data: NormalizedData[]): NormalizedData[] {
    return data.filter(item => {
      const isValid = this.validateSchema(item);
      if (!isValid) {
        this.log('warn', '数据验证失败，已过滤', item);
      }
      return isValid;
    });
  }
  
  /** Schema验证 (子类可覆盖) */
  protected validateSchema(data: NormalizedData): boolean {
    return !!data && typeof data === 'object';
  }
  
  /** 日志方法 */
  protected log(level: 'info' | 'warn' | 'error', message: string, data?: any): void {
    console.log(`[${level.toUpperCase()}] [${this.name}] ${message}`, data || '');
  }
}
```

### 3.2 示例采集器：代码语法阶段

```typescript
// src/data-platform/collectors/stage-01-code-syntax.ts

import { BaseDataCollector } from './base-collector';

/**
 * 第一阶段（代码语法测试核验）数据采集器
 * 
 * 采集内容：
 * - TypeScript编译错误/警告
 * - ESLint检查结果
 * - Prettier格式化问题
 * - JSDoc覆盖率
 * - React Console警告
 */
class CodeSyntaxCollector extends BaseDataCollector {
  readonly collectorId = 'collector-stage-01';
  readonly stageId = 'stage-01';
  readonly name = '代码语法测试核验采集器';
  readonly supportedDataTypes: DataType[] = ['metrics', 'logs', 'events'];
  
  constructor(config: CollectorConfig) {
    super(config);
  }
  
  protected async doCollect(context: CollectionContext): Promise<RawData[]> {
    const results: RawData[] = [];
    
    // 1. 运行TypeScript类型检查
    const tscResult = await this.runTypeScriptCheck(context.projectPath);
    results.push({
      type: 'metrics',
      source: 'typescript',
      data: {
        errors: tscResult.errors,
        warnings: tscResult.warnings,
        filesChecked: tscResult.filesChecked,
        duration: tscResult.duration,
      },
    });
    
    // 2. 运行ESLint检查
    const eslintResult = await this.runESLintCheck(context.projectPath);
    results.push({
      type: 'metrics',
      source: 'eslint',
      data: {
        errors: eslintResult.errorCount,
        warnings: eslintResult.warningCount,
        fixableErrors: eslintResult.fixableErrorCount,
        fixableWarnings: eslintResult.fixableWarningCount,
        rules: eslintResult.results,
      },
    });
    
    // 3. 收集JSDoc覆盖率
    const jsdocCoverage = await this.calculateJSDocCoverage(context.projectPath);
    results.push({
      type: 'metrics',
      source: 'jsdoc',
      data: {
        coverageRate: jsdocCoverage.rate,
        documentedFunctions: jsdocCoverage.documented,
        totalFunctions: jsdocCoverage.total,
        undocumentedFunctions: jsdocCoverage.undocumented,
      },
    });
    
    // 4. 记录事件
    results.push({
      type: 'events',
      source: 'code-syntax-check',
      event: {
        type: 'stage_completed',
        stage: 'code-syntax',
        timestamp: new Date(),
        status: this.determineStatus(results),
        context,
      },
    });
    
    return results;
  }
  
  private async runTypeScriptCheck(projectPath: string): Promise<TSCheckResult> {
    const { execSync } = require('child_process');
    
    try {
      const startTime = Date.now();
      const output = execSync('npx tsc --noEmit --pretty false', {
        cwd: projectPath,
        encoding: 'utf-8',
        timeout: 120000, // 2分钟超时
      });
      
      const lines = output.split('\n').filter(line => line.trim());
      const errors = lines.filter(line => line.includes('error TS'));
      const warnings = []; // TSC不输出warnings
      
      return {
        success: true,
        errors: errors.length,
        warnings: warnings.length,
        filesChecked: this.extractFileCount(output),
        duration: Date.now() - startTime,
        details: errors,
      };
      
    } catch (error: any) {
      // TSC返回非零退出码表示有错误
      return {
        success: false,
        errors: this.parseTSCErrors(error.stdout || error.message),
        warnings: 0,
        filesChecked: 0,
        duration: 0,
        details: [],
      };
    }
  }
  
  // ... 其他私有方法的实现
}
```

### 3.3 示例采集器：AI智能验收阶段（第十一阶段）

```typescript
// src/data-platform/collectors/stage-11-ai-intelligence.ts

/**
 * 第十一阶段（智能验收与AI赋能）数据采集器
 * 
 * 采集内容：
 * - AI代码审查结果
 * - 智能测试生成统计
 * - 缺陷预测准确率
 * - 自然语言交互日志
 * - 用户反馈数据
 */
class AIIntelligenceCollector extends BaseDataCollector {
  readonly collectorId = 'collector-stage-11';
  readonly stageId = 'stage-11';
  readonly name = '智能验收与AI赋能采集器';
  readonly supportedDataTypes: DataType[] = ['metrics', 'events', 'feedback', 'predictions'];
  
  constructor(config: CollectorConfig) {
    super(config);
  }
  
  protected async doCollect(context: CollectionContext): Promise<RawData[]> {
    const results: RawData[] = [];
    
    // 1. AI代码审查效果数据
    const aiReviewStats = await this.collectAIReviewStats();
    results.push({
      type: 'metrics',
      source: 'ai-code-reviewer',
      data: {
        totalReviews: aiReviewStats.total,
        avgResponseTime: aiReviewStats.avgTime,
        issuesFound: aiReviewStats.issuesFound,
        accurateFindings: aiReviewStats.accurate,
        falsePositives: aiReviewStats.falsePositives,
        adoptionRate: aiReviewStats.adoptionRate,
      },
    });
    
    // 2. 智能测试生成效果
    const testGenStats = await this.collectTestGenStats();
    results.push({
      type: 'metrics',
      source: 'intelligent-test-generator',
      data: {
        testsGenerated: testGenStats.totalTests,
        directlyUsableRate: testGenStats.usableRate,
        timeSaved: testGenStats.timeSavedPercent,
        coverageImprovement: testGenStats.coverageGain,
      },
    });
    
    // 3. 缺陷预测准确性
    const predictionAccuracy = await this.collectPredictionAccuracy();
    results.push({
      type: 'metrics',
      source: 'defect-predictor',
      data: {
        accuracy: predictionAccuracy.accuracy,
        precision: predictionAccuracy.precision,
        recall: predictionAccuracy.recall,
        f1Score: predictionAccuracy.f1,
        highRiskModulesIdentified: predictionAccuracy.highRiskCount,
      },
    });
    
    // 4. LLM使用统计（成本追踪）
    const llmUsage = await this.collectLLMUsage();
    results.push({
      type: 'metrics',
      source: 'llm-usage',
      data: {
        totalTokens: llmUsage.totalTokens,
        promptTokens: llmUsage.promptTokens,
        completionTokens: llmUsage.completionTokens,
        estimatedCost: llmUsage.costUSD,
        cacheHitRate: llmUsage.cacheHitRate,
      },
    });
    
    // 5. 用户反馈汇总
    const feedbackSummary = await this.aggregateUserFeedback();
    results.push({
      type: 'feedback',
      source: 'user-feedback',
      data: {
        averageRating: feedbackSummary.avgRating,
        totalResponses: feedbackSummary.totalCount,
        positiveRate: feedbackSummary.positiveRate,
        topIssues: feedbackSummary.topComplaints,
        featureRequests: feedbackSummary.requests,
      },
    });
    
    return results;
  }
  
  private async collectAIReviewStats(): Promise<AIReviewStatistics> {
    // 从数据库或缓存中查询最近的AI审查记录
    const recentReviews = await this.queryRecentRecords(
      'ai_code_reviews',
      '7d', // 最近7天
      { projectId: this.config.projectId }
    );
    
    return {
      total: recentReviews.length,
      avgTime: this.average(recentReviews.map(r => r.responseTimeMs)),
      issuesFound: this.sum(recentReviews.map(r => r.issuesFound)),
      accurate: this.sum(recentReviews.filter(r => r.confirmedAsCorrect).map(r => r.issuesFound)),
      falsePositives: this.sum(recentReviews.map(r => r.falsePositives)),
      adoptionRate: this.calculateAdoptionRate(recentReviews),
    };
  }
  
  // ... 其他私有方法
}
```

---

## ⚙️ 四、数据处理流水线

### 4.1 ETL流程设计

```typescript
// src/data-platform/pipelines/etl-pipeline.ts

/**
 * ETL (Extract-Transform-Load) 数据处理流水线
 */
class ETLPipeline {
  private collectors: Map<string, BaseDataCollector>;
  private transformers: DataTransformer[];
  private loaders: DataLoader[];
  private validators: DataValidator[];
  
  constructor(config: PipelineConfig) {
    this.collectors = new Map();
    this.transformers = [];
    this.loaders = [];
    this.validators = [];
    
    this.initializeComponents(config);
  }
  
  /**
   * 执行完整ETL流程
   */
  async execute(pipelineRun: PipelineRunContext): Promise<PipelineResult> {
    console.log(`🚀 开始执行ETL流水线: ${pipelineRun.id}`);
    const startTime = Date.now();
    
    const result: PipelineResult = {
      runId: pipelineRun.id,
      status: 'running',
      startTime: new Date(),
      stages: {},
    };
    
    try {
      // Stage 1: Extract (数据提取)
      console.log('📥 Stage 1: Extract - 数据提取');
      result.stages.extract = await this.executeExtract(pipelineRun);
      
      // Stage 2: Transform (数据转换)
      console.log('🔄 Stage 2: Transform - 数据转换');
      result.stages.transform = await this.executeTransform(result.stages.extract.data);
      
      // Stage 3: Validate (数据验证)
      console.log('✅ Stage 3: Validate - 数据验证');
      result.stages.validate = await this.executeValidate(result.stages.transform.data);
      
      // Stage 4: Load (数据加载)
      console.log('💾 Stage 4: Load - 数据加载');
      result.stages.load = await this.executeLoad(result.stages.validate.validatedData);
      
      // 完成
      result.status = 'completed';
      result.endTime = new Date();
      result.duration = Date.now() - startTime;
      
      console.log(`✨ ETL流水线执行完成! 耗时: ${result.duration}ms`);
      
      return result;
      
    } catch (error) {
      result.status = 'failed';
      result.error = error.message;
      result.endTime = new Date();
      result.duration = Date.now() - startTime;
      
      console.error(`❌ ETL流水线执行失败: ${error.message}`);
      
      throw error;
    }
  }
  
  private async executeExtract(context: PipelineRunContext): Promise<ExtractResult> {
    const extractedData: CollectedData[] = [];
    const errors: Error[] = [];
    
    // 根据触发的阶段选择对应的采集器
    const targetCollectors = context.triggeredStages
      ? this.getCollectorsByStages(context.triggeredStages)
      : Array.from(this.collectors.values());
    
    // 并行执行所有采集器
    const collectionPromises = targetCollectors.map(collector => 
      collector.collect(context.collectionContext)
    );
    
    const results = await Promise.allSettled(collectionPromises);
    
    for (const result of results) {
      if (result.status === 'fulfilled') {
        if (result.value.success) {
          extractedData.push(...result.value.data);
        } else {
          errors.push(new Error(result.value.error));
        }
      } else {
        errors.push(result.reason);
      }
    }
    
    return {
      success: errors.length === 0,
      data: extractedData,
      errors,
      collectorsExecuted: targetCollectors.length,
      dataPointsCollected: extractedData.length,
    };
  }
  
  private async executeTransform(rawData: NormalizedData[]): Promise<TransformResult> {
    let transformedData = [...rawData];
    
    for (const transformer of this.transformers) {
      transformedData = await transformer.process(transformedData);
    }
    
    return {
      inputSize: rawData.length,
      outputSize: transformedData.length,
      data: transformedData,
      transformationsApplied: this.transformers.length,
    };
  }
  
  private async executeValidate(data: NormalizedData[]): Promise<ValidateResult> {
    const validData: NormalizedData[] = [];
    const invalidData: InvalidData[] = [];
    
    for (const validator of this.validators) {
      for (const item of data) {
        const validation = await validator.validate(item);
        if (validation.isValid) {
          validData.push(item);
        } else {
          invalidData.push({
            original: item,
            errors: validation.errors,
            severity: validation.severity,
          });
        }
      }
    }
    
    return {
      totalItems: data.length,
      validItems: validData.length,
      invalidItems: invalidData.length,
      validationRate: (validData.length / data.length) * 100,
      validatedData: validData,
      invalidData,
    };
  }
  
  private async executeLoad(data: NormalizedData[]): Promise<LoadResult> {
    const loadResults = await Promise.all(
      this.loader.map(loader => loader.load(data))
    );
    
    return {
      totalLoaded: loadResults.reduce((sum, r) => sum + r.loadedCount, 0),
      failedLoads: loadResults.reduce((sum, r) => sum + r.failedCount, 0),
      destinations: loadResults.map(r => r.destination),
    };
  }
}
```

### 4.2 数据转换器示例

```typescript
// src/data-platform/transformers/metric-normalizer.ts

/**
 * 指标标准化转换器
 * 将不同来源的指标数据转换为统一格式
 */
class MetricNormalizer implements DataTransformer {
  readonly name = 'metric-normalizer';
  
  async process(data: NormalizedData[]): Promise<NormalizedData[]> {
    return data.map(item => {
      if (item.type !== 'metrics') return item;
      
      // 标准化指标名称
      const normalizedName = this.normalizeMetricName(item.data.source, item.data.metric);
      
      // 标准化单位
      const normalizedUnit = this.normalizeUnit(item.data.unit);
      
      // 标准化值
      const normalizedValue = this.normalizeValue(normalizedName, item.data.value);
      
      return {
        ...item,
        data: {
          ...item.data,
          metric: normalizedName,
          value: normalizedValue,
          unit: normalizedUnit,
          normalizedAt: new Date(),
        },
      };
    });
  }
  
  private normalizeMetricName(source: string, rawName: string): string {
    // 映射表：将不同工具的指标名称映射为统一名称
    const mappings: Record<string, Record<string, string>> = {
      typescript: {
        'errors': 'ts_type_errors',
        'warnings': 'ts_warnings',
        'filesChecked': 'ts_files_checked',
      },
      eslint: {
        'errors': 'eslint_errors',
        'warnings': 'eslint_warnings',
        'errorCount': 'eslint_errors',
        'warningCount': 'eslint_warnings',
      },
      vitest: {
        'coverage': 'test_coverage_percent',
        'passRate': 'test_pass_rate',
        'duration': 'test_duration_ms',
      },
    };
    
    return mappings[source]?.[rawName] || rawName.toLowerCase().replace(/\s+/g, '_');
  }
  
  private normalizeValue(metricName: string, value: number): number {
    // 特殊处理某些指标的值
    switch (metricName) {
      case 'test_coverage_percent':
        return Math.min(100, Math.max(0, value)); // 限制在0-100范围
      case 'response_time_ms':
        return Math.round(value * 100) / 100; // 保留两位小数
      default:
        return value;
    }
  }
}
```

---

## 📈 五、查询与分析服务

### 5.1 统一查询引擎

```typescript
// src/data-platform/services/query-engine.ts

/**
 * 统一查询引擎
 * 支持SQL-like查询语言，跨阶段数据分析
 */
class UnifiedQueryEngine {
  private postgresClient: PostgreSQLClient;
  private redisClient: RedisClient;
  private queryCache: LRUCache;
  
  constructor(config: QueryEngineConfig) {
    this.postgresClient = new PostgreSQLClient(config.postgres);
    this.redisClient = new RedisClient(config.redis);
    this.queryCache = new LRUCache({ max: 1000, ttl: 300 }); // 5分钟缓存
  }
  
  /**
   * 执行查询
   */
  async query(query: UnifiedQuery): Promise<QueryResult> {
    const cacheKey = this.generateCacheKey(query);
    
    // 检查缓存
    const cached = this.queryCache.get(cacheKey);
    if (cached && !query.bypassCache) {
      return { ...cached, fromCache: true };
    }
    
    // 解析并优化查询
    const optimizedQuery = this.optimizeQuery(query);
    
    // 执行查询
    let result: QueryResult;
    
    switch (optimizedQuery.type) {
      case 'metric_aggregation':
        result = await this.executeMetricQuery(optimizedQuery);
        break;
        
      case 'trend_analysis':
        result = await this.executeTrendQuery(optimizedQuery);
        break;
        
      case 'cross_stage_comparison':
        result = await this.executeCrossStageQuery(optimizedQuery);
        break;
        
      case 'correlation_analysis':
        result = await this.executeCorrelationQuery(optimizedQuery);
        break;
        
      default:
        throw new Error(`不支持的查询类型: ${optimizedQuery.type}`);
    }
    
    // 更新缓存
    this.queryCache.set(cacheKey, result);
    
    return { ...result, fromCache: false };
  }
  
  /**
   * 示例查询：获取项目整体健康分数
   */
  async getProjectHealthScore(projectId: string, timeRange: TimeRange): Promise<HealthScoreResult> {
    const query: UnifiedQuery = {
      type: 'metric_aggregation',
      filters: {
        projectId,
        timeRange,
      },
      aggregations: [
        {
          metric: '*',
          operation: 'weighted_average',
          weights: {
            'stage-01': 0.10, // 代码语法
            'stage-02': 0.15, // 功能逻辑
            'stage-03': 0.10, // 测试用例
            'stage-04': 0.10, // 组件测试
            'stage-05': 0.05, // 测试框架
            'stage-06': 0.10, // 闭环验证
            'stage-07': 0.08, // 数据调取
            'stage-08': 0.12, // 安全加固
            'stage-09': 0.05, // 高级功能
            'stage-10': 0.08, // 性能优化
            'stage-11': 0.07, // AI赋能 (新增!)
          },
        },
      ],
      groupBy: ['date'],
    };
    
    return this.query(query) as Promise<HealthScoreResult>;
  }
  
  /**
   * 示例查询：跨阶段相关性分析
   * 例如：分析代码覆盖率与缺陷数量的相关性
   */
  async analyzeCrossStageCorrelation(
    metricX: string,
    metricY: string,
    options: CorrelationOptions
  ): Promise<CorrelationResult> {
    const query: UnifiedQuery = {
      type: 'correlation_analysis',
      metrics: [metricX, metricY],
      filters: {
        projectId: options.projectId,
        timeRange: options.timeRange,
        branches: options.branches,
      },
      options: {
        method: options.method || 'pearson', // pearson, spearman, kendall
        significanceLevel: options.significanceLevel || 0.05,
      },
    };
    
    return this.query(query) as Promise<CorrelationResult>;
  }
}
```

### 5.2 预定义查询库

```typescript
// src/data-platform/services/predefined-queries.ts

/**
 * 预定义查询库
 * 封装常用的分析查询，供Dashboard和API使用
 */
export class PredefinedQueries {
  private queryEngine: UnifiedQueryEngine;
  
  constructor(queryEngine: UnifiedQueryEngine) {
    this.queryEngine = queryEngine;
  }
  
  // ========== 总览查询 ==========
  
  /** 获取项目仪表板概览数据 */
  async getDashboardOverview(projectId: string): Promise<DashboardOverview> {
    const [healthScore, recentRuns, trend, alerts] = await Promise.all([
      this.queryEngine.getProjectHealthScore(projectId, { days: 30 }),
      this.getRecentAcceptanceRuns(projectId, 10),
      this.getScoreTrend(projectId, { days: 90 }),
      this.getActiveAlerts(projectId),
    ]);
    
    return {
      healthScore,
      recentRuns,
      trend,
      activeAlerts: alerts.length,
      lastUpdated: new Date(),
    };
  }
  
  // ========== 阶段特定查询 ==========
  
  /** 获取某个阶段的详细表现 */
  async getStagePerformance(
    projectId: string,
    stageId: string,
    timeRange: TimeRange
  ): Promise<StagePerformance> {
    const [scores, metrics, findings] = await Promise.all([
      this.getStageScoresOverTime(projectId, stageId, timeRange),
      this.getStageDetailedMetrics(projectId, stageId, timeRange),
      this.getStageCriticalFindings(projectId, stageId, timeRange),
    ]);
    
    return {
      stageId,
      scores,
      metrics,
      criticalFindings: findings,
      comparisonWithPrevious: await this.compareWithPreviousPeriod(projectId, stageId),
    };
  }
  
  // ========== AI专项查询 (第十一阶段) ==========
  
  /** 获取AI能力成熟度评估 */
  async getAIMaturityAssessment(projectId: string): Promise<AIMaturityReport> {
    const [
      codeReviewEffectiveness,
      testGenerationEfficiency,
      predictionAccuracy,
      userSatisfaction,
      costEffectiveness,
    ] = await Promise.all([
      this.getCodeReviewMetrics(projectId, { days: 30 }),
      this.getTestGenerationMetrics(projectId, { days: 30 }),
      this.getPredictionAccuracyMetrics(projectId, { days: 30 }),
      this.getUserFeedbackSummary(projectId, { days: 30 }),
      this.getAICostAnalysis(projectId, { days: 30 }),
    ]);
    
    return {
      overallMaturity: this.calculateOverallMaturity([
        codeReviewEffectiveness,
        testGenerationEfficiency,
        predictionAccuracy,
        userSatisfaction,
      ]),
      dimensions: {
        codeReview: codeReviewEffectiveness,
        testGeneration: testGenerationEfficiency,
        defectPrediction: predictionAccuracy,
        naturalLanguageInteraction: userSatisfaction,
        costEfficiency: costEffectiveness,
      },
      trends: await this.getAITrendAnalysis(projectId, { days: 90 }),
      recommendations: this.generateAIRecommendations([
        codeReviewEffectiveness,
        testGenerationEfficiency,
        predictionAccuracy,
      ]),
    };
  }
  
  // ========== 高级分析查询 ==========
  
  /** 质量门禁状态检查 */
  async checkQualityGates(projectId: string): Promise<QualityGateStatus> {
    const latestRuns = await this.getLatestCompletedRunsForAllStages(projectId);
    
    const gateResults = latestRuns.map(run => ({
      stageId: run.stageId,
      passed: run.score >= run.thresholds.minimum,
      score: run.score,
      threshold: run.thresholds.minimum,
      grade: run.grade,
    }));
    
    const allPassed = gateResults.every(gate => gate.passed);
    
    return {
      overallPassed: allPassed,
      gates: gateResults,
      blockingFailures: gateResults.filter(g => !g.passed && g.threshold === 'P0'),
      timestamp: new Date(),
    };
  }
  
  /** 技术债务估算 */
  async estimateTechnicalDebt(projectId: string): Promise<TechnicalDebtEstimate> {
    const [codeQualityDebt, testDebt, securityDebt, performanceDebt] = await Promise.all([
      this.estimateCodeQualityDebt(projectId),
      this.estimateTestDebt(projectId),
      this.estimateSecurityDebt(projectId),
      this.estimatePerformanceDebt(projectId),
    ]);
    
    const totalRemediationHours = 
      codeQualityDebt.hours +
      testDebt.hours +
      securityDebt.hours +
      performanceDebt.hours;
    
    return {
      totalDebtHours: totalRemediationHours,
      estimatedCost: totalRemediationHours * 150, // $150/hour
      breakdown: {
        codeQuality: codeQualityDebt,
        testing: testDebt,
        security: securityDebt,
        performance: performanceDebt,
      },
      priorityRecommendations: this.prioritizeRemediation([
        codeQualityDebt,
        testDebt,
        securityDebt,
        performanceDebt,
      ]),
    };
  }
}
```

---

## 🎯 六、实施路线图

### Phase 1: 基础设施搭建（第1-2周）

**目标**：建立数据平台基础框架

**任务清单**：
- [ ] 设计并实施数据库Schema
- [ ] 开发BaseDataCollector抽象类
- [ ] 实现阶段1-5的基础采集器（代码语法、功能逻辑、测试用例、组件测试、单元框架）
- [ ] 搭建PostgreSQL + Redis开发环境
- [ ] 实现基础的ETL流水线

**交付物**：
- 可运行的采集器框架
- 数据库迁移脚本
- 基础API端点（写入数据）

---

### Phase 2: 核心功能完善（第3-4周）

**目标**：实现主要功能模块

**任务清单**：
- [ ] 完成剩余8个阶段的采集器
- [ ] 实现UnifiedQueryEngine
- [ ] 开发PredefinedQueries库
- [ ] 创建Grafana基础Dashboard（5-10个面板）
- [ ] 实现告警引擎基础版

**交付物**：
- 完整的13阶段数据采集系统
- 查询API文档
- 初始Dashboard原型

---

### Phase 3: 智能化增强（第5-6周）

**目标**：集成AI能力，提升智能化水平

**任务清单**：
- [ ] 实现第十一阶段（AI智能验收）专用采集器
- [ ] 开发跨阶段关联分析算法
- [ ] 实现预测性分析模型
- [ ] 创建AI能力成熟度评估Dashboard
- [ ] 集成自然语言查询接口（可选）

**交付物**：
- AI增强的数据分析能力
- 智能推荐系统原型
- 高级分析Dashboard

---

### Phase 4: 生产就绪（第7-8周）

**目标**：达到生产部署标准

**任务清单**：
- [ ] 性能优化（查询响应时间 < 500ms）
- [ ] 安全加固（权限控制、数据加密）
- [ ] 监控告警完善（平台自身监控）
- [ ] 文档编写（运维手册、API文档）
- [ ] 压力测试和容量规划

**交付物**：
- 生产级部署包
- 完整文档体系
- 运维SOP

---

## 📚 七、附录：关键技术选型

| 组件 | 推荐方案 | 备选方案 | 选择理由 |
|------|---------|---------|----------|
| **数据库** | PostgreSQL 15+ | TimescaleDB, ClickHouse | 成熟稳定，JSON支持好，生态丰富 |
| **缓存** | Redis 7+ | Memcached | 数据结构丰富，支持Pub/Sub |
| **对象存储** | MinIO (自托管) | AWS S3, Aliyun OSS | 成本可控，兼容S3 API |
| **可视化** | Grafana 10+ | Metabase, Superset | 插件生态强大，定制灵活 |
| **消息队列** | RabbitMQ | Kafka, Redis Streams | 可靠性高，管理方便 |
| **API网关** | Express + GraphQL | Fastify, Apollo | 与现有技术栈一致 |
| **ORM** | Prisma | TypeORM, Drizzle | 类型安全，开发体验好 |

---


## 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
| ---- | ---- | -------- | ---- |
| v2.0.0 | 2026-05-30 | 版本迭代同步 | YanYuCloudCube Team |
| v1.0.0 | 2026-04-03 | 初始版本 | YanYuCloudCube Team |

<div align="center">

**— 文档结束 —**

</div>


## 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
| ---- | ---- | -------- | ---- |
| v2.0.0 | 2026-05-30 | 版本迭代同步 | YanYuCloudCube Team |
| v1.0.0 | 2026-04-03 | 初始版本 | YanYuCloudCube Team |

<div align="center">

**© 2026 YanYuCloudCube Team**  
**言启象限 · 语枢未来**

</div>
