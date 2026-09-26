/**
 * Skill Sandbox — 安全隔离执行环境
 *
 * 提供安全沙箱执行能力，包括：
 * - 多运行时支持 (Node/Python/Shell/Native)
 * - 代码安全检测（危险模式拦截）
 * - 命令黑名单（native 运行时执行路径强制校验）
 * - 输入净化（命令注入防护）
 * - 路径收敛（cwd 不得逃逸收敛根）
 * - 环境变量白名单（宿主密钥不透传）
 * - 资源限制（超时钳制/输出截断）
 * - 进程隔离（child_process + 容器级 OS 隔离，见 docker-compose.yml）
 *
 * ⚠️ SkillSandbox.execute 是唯一受安全策略保护的执行入口；
 * Executor.execute 为低层原语，不内置内容/黑名单检查，禁止在未经
 * SkillSanitizer/黑名单校验的情况下直接用于不可信输入。
 */
import { EventEmitter } from 'node:events';
import path from 'node:path';
import { Executor } from './executor.js';
import { Sanitizer } from './sanitizer.js';
import {
  PathTraversalError,
  buildSafeEnv,
  confineWithinRoot,
  normalizeTimeout,
} from './security.js';
import type {
  SandboxConfig,
  SandboxPolicy,
  SandboxRequest,
  SandboxResult,
  SandboxRuntime
} from './types.js';

const DEFAULT_CONFIG: Omit<SandboxConfig, 'workDir'> & { workDir: string } = {
  defaultTimeout: 30_000,
  maxTimeout: 300_000,
  maxOutput: 1024 * 1024, // 1MB
  policy: 'strict',
  blockedCommands: [],
  allowedEnv: ['PATH', 'HOME', 'USER', 'LANG', 'LC_ALL', 'TZ', 'TMPDIR'],
  // 空字符串：构造时解析为 process.cwd()（收敛根默认为调用方当前目录）
  workDir: '',
};

export class SkillSandbox extends EventEmitter {
  readonly config: SandboxConfig;
  readonly sanitizer: Sanitizer;

  constructor(config: Partial<SandboxConfig> = {}) {
    super();
    this.config = {
      ...DEFAULT_CONFIG,
      ...config,
      // 收敛根：显式配置则用之，否则默认当前工作目录
      workDir: path.resolve(config.workDir || process.cwd()),
    };
    this.sanitizer = new Sanitizer(this.config.policy, this.config.blockedCommands);
  }

  /** 构造拦截结果并广播 blocked 事件 */
  private block(request: SandboxRequest, code: string, reason: string): SandboxResult {
    this.emit('execution:blocked', request, reason);
    return {
      ok: false,
      exitCode: -1,
      stdout: '',
      stderr: reason,
      duration: 0,
      timedOut: false,
      error: `${code}: ${reason}`,
    };
  }

  /** 执行代码（唯一受安全策略保护的执行入口） */
  async execute(request: SandboxRequest, signal?: AbortSignal): Promise<SandboxResult> {
    // 1. 静态内容策略（正则危险模式 + 路径遍历 + 长度）
    const validation = this.sanitizer.validate(request.code, request.runtime);
    if (!validation.safe) {
      return this.block(request, 'SECURITY_BLOCKED', validation.reason ?? 'Blocked by security policy');
    }

    // 1b. 命令黑名单必须接入执行路径（此前 isCommandBlocked 仅被测试调用）。
    // permissive 策略显式选择「全部放行」时跳过（保持该策略既有语义）。
    if (
      this.config.policy !== 'permissive' &&
      request.runtime === 'native' &&
      this.sanitizer.isCommandBlocked(request.code)
    ) {
      return this.block(request, 'COMMAND_BLOCKED', `Blocked command: ${request.code.split(/\s+/)[0]}`);
    }

    // 2. cwd 收敛：请求的工作目录必须位于收敛根之内，杜绝跳出技能目录
    let cwd: string;
    try {
      cwd = request.cwd
        ? confineWithinRoot(this.config.workDir, request.cwd)
        : this.config.workDir;
    } catch (err) {
      const reason = err instanceof PathTraversalError ? err.message : 'Invalid working directory';
      return this.block(request, 'CWD_ESCAPE', reason);
    }

    // 3. 环境变量白名单：宿主密钥不进入技能进程；显式注入项经 key 校验 + 值净化
    const env = buildSafeEnv(
      this.config.allowedEnv,
      request.env ? this.sanitizer.sanitizeEnv(request.env) : undefined,
    );

    // 4. 参数净化 + 超时规范化（0/负数/NaN 回退默认值，不得绕过为无超时）
    const sanitizedRequest: SandboxRequest = {
      ...request,
      args: request.args ? this.sanitizer.sanitizeArgs(request.args) : undefined,
      env,
      cwd,
      timeout: normalizeTimeout(request.timeout, this.config.defaultTimeout, this.config.maxTimeout),
      maxOutput: request.maxOutput ?? this.config.maxOutput,
    };

    // 5. 执行
    this.emit('execution:start', sanitizedRequest);

    const result = await Executor.execute(sanitizedRequest, signal);

    if (result.timedOut) {
      this.emit('execution:timeout', sanitizedRequest);
    } else if (!result.ok) {
      this.emit('execution:error', sanitizedRequest, result.error ?? result.stderr);
    } else {
      this.emit('execution:complete', result);
    }

    return result;
  }

  /** 检查运行时是否可用 */
  static isRuntimeAvailable(runtime: SandboxRuntime): boolean {
    return Executor.isRuntimeAvailable(runtime);
  }

  /** 获取安全策略 */
  getPolicy(): SandboxPolicy {
    return this.config.policy;
  }
}

// 重新导出类型
export { Executor } from './executor.js';
export { Sanitizer } from './sanitizer.js';
export type {
  SandboxConfig, SandboxEvents, SandboxPolicy, SandboxRequest,
  SandboxResult, SandboxRuntime
} from './types.js';
