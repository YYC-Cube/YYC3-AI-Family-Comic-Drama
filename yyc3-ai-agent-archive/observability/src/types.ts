/**
 * Observability — 类型定义
 * @module @yyc3/observability
 */

/** 日志级别 */
export type LogLevel = 'debug' | 'info' | 'warn' | 'error' | 'fatal';

/** 日志条目 */
export interface LogEntry {
  level: LogLevel;
  message: string;
  timestamp: string;
  /** 请求追踪 ID */
  traceId?: string;
  /** 跨度 ID */
  spanId?: string;
  /** 模块/组件名 */
  component?: string;
  /** 上下文数据 */
  context?: Record<string, unknown>;
}

/** 日志配置 */
export interface LoggerConfig {
  minLevel: LogLevel;
  /** 是否输出到 stdout */
  enableConsole: boolean;
  /** 格式化器 */
  formatter: 'json' | 'text';
  /** 自定义传输器 */
  transports?: ((entry: LogEntry) => void)[];
  /**
   * 内存日志环上限（P2）：超出后丢弃最旧条目，防止长驻进程无界增长。
   * 0 = 不保留内存历史（仅 console/transports）。默认 1000。
   */
  maxEntries?: number;
}

/** 指标类型 */
export type MetricType = 'counter' | 'gauge' | 'histogram';

/** 指标标签 */
export type Labels = Record<string, string>;

/** 指标定义 */
export interface MetricDef {
  name: string;
  type: MetricType;
  help: string;
  labels?: Labels;
}

/** 指标快照 */
export interface MetricSnapshot {
  name: string;
  type: MetricType;
  help: string;
  value: number;
  labels?: Labels;
  /** 直方图分桶 */
  buckets?: Record<string, number>;
  /** 计数 */
  count?: number;
  /** 总和 */
  sum?: number;
}

/** 跨度状态 */
export interface Span {
  id: string;
  traceId: string;
  parentId?: string;
  name: string;
  startTime: number;
  endTime?: number;
  status: 'ok' | 'error';
  tags?: Record<string, string>;
  events?: SpanEvent[];
}

/** 跨度事件 */
export interface SpanEvent {
  name: string;
  timestamp: number;
  attributes?: Record<string, string>;
}

/** 追踪配置 */
export interface TracerConfig {
  /** 采样率 (0-1) */
  sampleRate: number;
  /** 是否启用 */
  enabled: boolean;
  /** 自定义 Span 导出器（未指定时按 OTEL_EXPORTER_OTLP_ENDPOINT 自动创建，未配置则禁用） */
  exporter?: SpanExporter | null;
  /** 是否输出 exporter 调试日志（默认 false） */
  debug?: boolean;
}

/** Span 导出器接口（如 OTLP HTTP、Jaeger、控制台等） */
export interface SpanExporter {
  /** 导出单个已结束的 Span；实现应异步且不抛错到调用栈 */
  export(span: Span): Promise<void> | void;
}

/** 健康状态 */
export type HealthStatus = 'healthy' | 'degraded' | 'unhealthy';

/** 健康检查结果 */
export interface HealthCheckResult {
  component: string;
  status: HealthStatus;
  message?: string;
  latency: number;
  timestamp: string;
}

/** 健康检查器 */
export interface HealthChecker {
  name: string;
  check: () => Promise<Omit<HealthCheckResult, 'timestamp'>>;
}