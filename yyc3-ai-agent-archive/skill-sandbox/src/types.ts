/**
 * Skill Sandbox — 类型定义
 * @module @yyc3/skill-sandbox
 */

/** 支持的运行时 */
export type SandboxRuntime = 'node' | 'python' | 'shell' | 'native';

/** 沙箱策略 */
export type SandboxPolicy = 'strict' | 'permissive' | 'custom';

/** 沙箱执行请求 */
export interface SandboxRequest {
  /** 运行时 */
  runtime: SandboxRuntime;
  /** 代码 */
  code: string;
  /** 参数 */
  args?: string[];
  /** 环境变量 */
  env?: Record<string, string>;
  /** 工作目录 */
  cwd?: string;
  /** 超时(毫秒) */
  timeout?: number;
  /** 最大输出字节 */
  maxOutput?: number;
}

/** 沙箱执行结果 */
export interface SandboxResult {
  /** 是否成功 */
  ok: boolean;
  /** 退出码 */
  exitCode: number;
  /** stdout */
  stdout: string;
  /** stderr */
  stderr: string;
  /** 执行时长(毫秒) */
  duration: number;
  /** 是否超时 */
  timedOut: boolean;
  /** 错误 */
  error?: string;
  /** 信号 */
  signal?: string;
}

/** 沙箱配置 */
export interface SandboxConfig {
  /** 默认超时 */
  defaultTimeout: number;
  /** 最大超时 */
  maxTimeout: number;
  /** 最大输出字节 */
  maxOutput: number;
  /** 安全策略 */
  policy: SandboxPolicy;
  /** 禁止的命令列表 */
  blockedCommands: string[];
  /** 允许的环境变量 */
  allowedEnv: string[];
  /** 工作目录 */
  workDir: string;
}

/** 沙箱事件 */
export interface SandboxEvents {
  'execution:start': (request: SandboxRequest) => void;
  'execution:complete': (result: SandboxResult) => void;
  'execution:blocked': (request: SandboxRequest, reason: string) => void;
  'execution:timeout': (request: SandboxRequest) => void;
  'execution:error': (request: SandboxRequest, error: string) => void;
}