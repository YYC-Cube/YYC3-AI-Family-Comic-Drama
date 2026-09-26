/**
 * Observability — 结构化日志器
 *
 * 支持多级别日志、请求追踪、上下文注入、自定义传输器
 */
import type { LogEntry, LogLevel, LoggerConfig } from './types.js';

const LOG_LEVEL_WEIGHT: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
  fatal: 4,
};

const DEFAULT_CONFIG: LoggerConfig = {
  minLevel: 'info',
  enableConsole: true,
  formatter: 'json',
};

export class Logger {
  readonly config: LoggerConfig;
  private entries: LogEntry[] = [];
  /** 内存环上限（0 = 不保留内存历史） */
  private readonly maxEntries: number;

  constructor(config: Partial<LoggerConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.maxEntries = this.config.maxEntries ?? 1000;
  }

  debug(message: string, context?: Record<string, unknown>): void {
    this.log('debug', message, context);
  }

  info(message: string, context?: Record<string, unknown>): void {
    this.log('info', message, context);
  }

  warn(message: string, context?: Record<string, unknown>): void {
    this.log('warn', message, context);
  }

  error(message: string, context?: Record<string, unknown>): void {
    this.log('error', message, context);
  }

  fatal(message: string, context?: Record<string, unknown>): void {
    this.log('fatal', message, context);
  }

  /** 创建子日志器（继承配置，附加上下文） */
  child(component: string, baseContext?: Record<string, unknown>): Logger {
    const childLogger = new Logger(this.config);
    // 注入 component 和 baseContext
    const originalLog = childLogger.log.bind(childLogger);
    childLogger.log = (level, message, context) => {
      originalLog(level, message, { ...baseContext, component, ...context });
    };
    return childLogger;
  }

  /** 获取历史日志 */
  getEntries(): LogEntry[] {
    return [...this.entries];
  }

  /** 清空日志 */
  clear(): void {
    this.entries = [];
  }

  /** 按级别过滤 */
  filterByLevel(level: LogLevel): LogEntry[] {
    const minWeight = LOG_LEVEL_WEIGHT[level];
    return this.entries.filter(e => LOG_LEVEL_WEIGHT[e.level] >= minWeight);
  }

  /** 导出为 JSON */
  toJSON(): string {
    return JSON.stringify(this.entries);
  }

  private log(level: LogLevel, message: string, context?: Record<string, unknown>): void {
    if (LOG_LEVEL_WEIGHT[level] < LOG_LEVEL_WEIGHT[this.config.minLevel]) {
      return;
    }

    const entry: LogEntry = {
      level,
      message,
      timestamp: new Date().toISOString(),
      context,
    };

    this.entries.push(entry);

    // 内存环上限：超出丢弃最旧（P2，无界增长防御）
    if (this.maxEntries > 0 && this.entries.length > this.maxEntries) {
      this.entries.splice(0, this.entries.length - this.maxEntries);
    } else if (this.maxEntries === 0) {
      this.entries = [];
    }

    // 控制台输出
    if (this.config.enableConsole) {
      const formatted = this.format(entry);
      const consoleMethod = level === 'error' || level === 'fatal' ? 'error' : level === 'warn' ? 'warn' : 'log';
      // eslint-disable-next-line no-console
      console[consoleMethod](formatted);
    }

    // 自定义传输器
    for (const transport of this.config.transports ?? []) {
      try {
        transport(entry);
      } catch {
        // 传输器失败不应影响主流程
      }
    }
  }

  private format(entry: LogEntry): string {
    if (this.config.formatter === 'json') {
      return JSON.stringify(entry);
    }
    // 文本格式
    const ctx = entry.context ? ` ${JSON.stringify(entry.context)}` : '';
    return `[${entry.timestamp}] ${entry.level.toUpperCase()} ${entry.message}${ctx}`;
  }
}
