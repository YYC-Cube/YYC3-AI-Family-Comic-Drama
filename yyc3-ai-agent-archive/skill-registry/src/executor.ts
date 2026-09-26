/**
 * @description YYC³ Skill 执行器 — 含降级熔断机制
 * @module @yyc3/skill-registry/executor
 *
 * 实现 Skill 的安全执行：
 * - 参数验证
 * - 超时控制
 * - 降级链自动执行
 * - 熔断器模式（Circuit Breaker）
 * - 执行结果追踪
 */

import {
  assertSafeRelativeEntry,
  buildSafeEnv,
  confineWithinRoot,
  normalizeTimeout,
} from '@yyc3/skill-sandbox';
import { spawn } from 'child_process';
import { randomBytes } from 'node:crypto';
import type { SkillRegistry } from './registry.js';
import type {
  SkillExecutionContext,
  SkillExecutionResult,
  UnifiedSkill,
} from './types.js';

/**
 * 技能子进程默认环境白名单：仅运行所必需的最小集合。
 * 宿主上的 API Key / Token / 数据库口令等不会透传给（可能来自社区的）技能。
 */
const DEFAULT_ALLOWED_ENV = [
  'PATH',
  'HOME',
  'LANG',
  'LC_ALL',
  'TZ',
  'TMPDIR',
  // Windows 运行时必需
  'SYSTEMROOT',
  'APPDATA',
  'LOCALAPPDATA',
];

/** 默认超时（毫秒） */
const DEFAULT_EXEC_TIMEOUT = 30_000;
/** 最大超时（毫秒） */
const MAX_EXEC_TIMEOUT = 300_000;
/** 单流输出累积上限（字节），防止技能无限输出撑爆内存 */
const MAX_OUTPUT_BYTES = 1024 * 1024;

/**
 * 将技能 entry 收敛到技能 source 根目录之内。
 * - 有 source：entry 解析后必须位于 source 子树（拦截 `../../x` 与根外绝对路径）
 * - 无 source：只允许不含 `..` 段的相对路径
 * @returns 收敛后的入口路径；校验失败返回 null（调用方转 ENTRY_TRAVERSAL 错误）
 */
function resolveEntryPath(skill: UnifiedSkill): string | null {
  try {
    if (skill.source) {
      return confineWithinRoot(skill.source, skill.entry);
    }
    assertSafeRelativeEntry(skill.entry);
    return skill.entry;
  } catch {
    return null;
  }
}

// ==================== 熔断器 ====================

type CircuitState = 'closed' | 'open' | 'half-open';

interface CircuitBreakerConfig {
  /** 失败阈值（连续失败多少次后熔断） */
  failureThreshold: number;
  /** 熔断恢复时间（毫秒） */
  recoveryTimeout: number;
  /** 半开状态最大探测请求数 */
  halfOpenMaxCalls: number;
}

class CircuitBreaker {
  private state: CircuitState = 'closed';
  private failureCount: number = 0;
  private lastFailureTime: number = 0;
  private halfOpenCalls: number = 0;

  constructor(private config: CircuitBreakerConfig) { }

  canExecute(): boolean {
    switch (this.state) {
      case 'closed':
        return true;
      case 'open': {
        const elapsed = Date.now() - this.lastFailureTime;
        if (elapsed >= this.config.recoveryTimeout) {
          this.state = 'half-open';
          // 恢复窗口后首个调用本身就是一次半开探测，必须计数，
          // 否则 halfOpenMaxCalls 形同虚设（此前缺陷：计数只被读从不自增）
          this.halfOpenCalls = 1;
          return true;
        }
        return false;
      }
      case 'half-open':
        if (this.halfOpenCalls < this.config.halfOpenMaxCalls) {
          this.halfOpenCalls++;
          return true;
        }
        return false;
    }
  }

  recordSuccess(): void {
    this.failureCount = 0;
    if (this.state === 'half-open') {
      this.state = 'closed';
    }
  }

  recordFailure(): void {
    this.failureCount++;
    this.lastFailureTime = Date.now();
    if (this.state === 'half-open') {
      this.state = 'open';
    } else if (this.failureCount >= this.config.failureThreshold) {
      this.state = 'open';
    }
  }

  getState(): CircuitState {
    return this.state;
  }

  reset(): void {
    this.state = 'closed';
    this.failureCount = 0;
    this.lastFailureTime = 0;
    this.halfOpenCalls = 0;
  }
}

// ==================== 执行器 ====================

export class SkillExecutor {
  private breakers: Map<string, CircuitBreaker> = new Map();
  private defaultConfig: CircuitBreakerConfig = {
    failureThreshold: 3,
    recoveryTimeout: 60_000,
    halfOpenMaxCalls: 1,
  };

  constructor(
    private registry: SkillRegistry,
    breakerConfig?: Partial<CircuitBreakerConfig>
  ) {
    if (breakerConfig) {
      this.defaultConfig = { ...this.defaultConfig, ...breakerConfig };
    }
  }

  /**
   * 执行 Skill（含降级链自动执行）
   */
  async execute(
    skillId: string,
    args: Record<string, unknown>,
    context?: Partial<SkillExecutionContext>
  ): Promise<SkillExecutionResult> {
    const ctx: SkillExecutionContext = {
      // callId 用 crypto 随机（Math.random 非密码学且同毫秒存在碰撞面，P2）
      callId: context?.callId || `call-${randomBytes(8).toString('hex')}`,
      allowFallback: context?.allowFallback ?? true,
      maxFallbackDepth: context?.maxFallbackDepth ?? 3,
      timeout: context?.timeout ?? 30_000,
      cwd: context?.cwd,
      env: context?.env,
      ...context,
    };

    return this.executeWithFallback(skillId, args, ctx, 0);
  }

  /**
   * 带降级链的递归执行
   */
  private async executeWithFallback(
    skillId: string,
    args: Record<string, unknown>,
    ctx: SkillExecutionContext,
    depth: number
  ): Promise<SkillExecutionResult> {
    const skill = this.registry.get(skillId);
    if (!skill) {
      return {
        callId: ctx.callId,
        skillId,
        success: false,
        output: null,
        error: `Skill not found: ${skillId}`,
      };
    }

    // 检查熔断器
    const breaker = this.getOrCreateBreaker(skillId);
    if (!breaker.canExecute()) {
      // 尝试降级
      if (ctx.allowFallback && skill.fallback && depth < (ctx.maxFallbackDepth ?? 3)) {
        return this.executeWithFallback(skill.fallback, args, ctx, depth + 1);
      }
      return {
        callId: ctx.callId,
        skillId,
        success: false,
        output: null,
        error: `Circuit breaker is open for skill: ${skillId}`,
        fellBack: depth > 0,
        executedSkillId: depth > 0 ? skillId : undefined,
      };
    }

    // 执行
    const startTime = Date.now();
    try {
      const result = await this.executeSkill(skill, args, ctx);
      const duration = Date.now() - startTime;

      if (result.success) {
        breaker.recordSuccess();
      } else {
        breaker.recordFailure();
        // 执行失败，尝试降级
        if (ctx.allowFallback && skill.fallback && depth < (ctx.maxFallbackDepth ?? 3)) {
          const fallbackResult = await this.executeWithFallback(
            skill.fallback,
            args,
            ctx,
            depth + 1
          );
          return {
            ...fallbackResult,
            fellBack: true,
            executedSkillId: fallbackResult.executedSkillId || skill.fallback,
            metadata: {
              ...fallbackResult.metadata,
              originalError: result.error,
              originalDuration: duration,
            },
          };
        }
      }

      return {
        ...result,
        duration,
        fellBack: depth > 0,
        executedSkillId: skillId,
      };
    } catch (error) {
      breaker.recordFailure();
      const errorMsg = error instanceof Error ? error.message : String(error);
      const duration = Date.now() - startTime;

      // 尝试降级
      if (ctx.allowFallback && skill.fallback && depth < (ctx.maxFallbackDepth ?? 3)) {
        const fallbackResult = await this.executeWithFallback(
          skill.fallback,
          args,
          ctx,
          depth + 1
        );
        return {
          ...fallbackResult,
          fellBack: true,
          executedSkillId: fallbackResult.executedSkillId || skill.fallback,
          metadata: {
            ...fallbackResult.metadata,
            originalError: errorMsg,
            originalDuration: duration,
          },
        };
      }

      return {
        callId: ctx.callId,
        skillId,
        success: false,
        output: null,
        error: errorMsg,
        duration,
        fellBack: depth > 0,
        executedSkillId: skillId,
      };
    }
  }

  /**
   * 执行单个 Skill
   */
  private async executeSkill(
    skill: UnifiedSkill,
    args: Record<string, unknown>,
    ctx: SkillExecutionContext
  ): Promise<SkillExecutionResult> {
    switch (skill.runtime) {
      case 'python':
        return this.executeScript('python3', skill, args, ctx);
      case 'node':
        return this.executeScript('node', skill, args, ctx);
      case 'shell':
        return this.executeScript('bash', skill, args, ctx);
      case 'native':
        return {
          callId: ctx.callId,
          skillId: skill.id,
          success: true,
          output: { message: 'Native skill executed (placeholder)', skill: skill.id, args },
        };
      default:
        return {
          callId: ctx.callId,
          skillId: skill.id,
          success: false,
          output: null,
          error: `Unsupported runtime: ${skill.runtime}`,
        };
    }
  }

  /**
   * 通过子进程执行脚本（安全控制点）
   *
   * 安全保证：
   * - entry 路径收敛：技能入口不得穿越 source 根目录（防 `../../etc/x` 任意脚本执行）
   * - 环境白名单：宿主密钥不全量透传，仅允许白名单变量 + ctx.env 显式注入项
   * - 超时钳制：0/负数/NaN 回退默认值，上限 5 分钟
   * - 输出上限：stdout/stderr 各最多累积 1MB，防内存 DoS
   */
  private executeScript(
    command: string,
    skill: UnifiedSkill,
    args: Record<string, unknown>,
    ctx: SkillExecutionContext
  ): Promise<SkillExecutionResult> {
    return new Promise(resolve => {
      if (!skill.entry) {
        resolve({
          callId: ctx.callId,
          skillId: skill.id,
          success: false,
          output: null,
          error: `No entry point defined for skill: ${skill.id}`,
        });
        return;
      }

      // 安全控制点 1：entry 收敛到技能根目录
      const entryPath = resolveEntryPath(skill);
      if (entryPath === null) {
        resolve({
          callId: ctx.callId,
          skillId: skill.id,
          success: false,
          output: null,
          error:
            `ENTRY_TRAVERSAL: skill entry "${skill.entry}" escapes source root` +
            (skill.source ? ` "${skill.source}"` : ' (relative entry required)'),
        });
        return;
      }

      // 安全控制点 2：环境变量白名单（不再 ...process.env 全量透传）
      const env = buildSafeEnv(ctx.allowedEnv ?? DEFAULT_ALLOWED_ENV, ctx.env);

      // 安全控制点 3：超时钳制
      const timeout = normalizeTimeout(ctx.timeout, DEFAULT_EXEC_TIMEOUT, MAX_EXEC_TIMEOUT);

      const proc = spawn(command, [entryPath, JSON.stringify(args)], {
        cwd: ctx.cwd,
        env,
        timeout,
      });

      let stdout = '';
      let stderr = '';
      let truncated = false;

      const append = (current: string, chunk: Buffer): string => {
        if (current.length >= MAX_OUTPUT_BYTES) {
          truncated = true;
          return current;
        }
        const next = current + chunk.toString();
        if (next.length > MAX_OUTPUT_BYTES) {
          truncated = true;
          return next.slice(0, MAX_OUTPUT_BYTES);
        }
        return next;
      };

      proc.stdout.on('data', (data: Buffer) => {
        stdout = append(stdout, data);
      });

      proc.stderr.on('data', (data: Buffer) => {
        stderr = append(stderr, data);
      });

      proc.on('error', err => {
        resolve({
          callId: ctx.callId,
          skillId: skill.id,
          success: false,
          output: null,
          error: `Process error: ${err.message}`,
        });
      });

      proc.on('close', code => {
        const tail = truncated ? '\n[output truncated at 1MB]' : '';
        if (code === 0) {
          resolve({
            callId: ctx.callId,
            skillId: skill.id,
            success: true,
            output: (stdout.trim() || stderr.trim()) + tail,
          });
        } else {
          resolve({
            callId: ctx.callId,
            skillId: skill.id,
            success: false,
            output: null,
            error: stderr.trim() || `Process exited with code ${code}`,
          });
        }
      });
    });
  }

  /**
   * 获取或创建熔断器
   */
  private getOrCreateBreaker(skillId: string): CircuitBreaker {
    if (!this.breakers.has(skillId)) {
      this.breakers.set(skillId, new CircuitBreaker(this.defaultConfig));
    }
    return this.breakers.get(skillId)!;
  }

  /**
   * 获取熔断器状态
   */
  getCircuitState(skillId: string): CircuitState | undefined {
    return this.breakers.get(skillId)?.getState();
  }

  /**
   * 重置指定 Skill 的熔断器
   */
  resetBreaker(skillId: string): void {
    this.breakers.get(skillId)?.reset();
  }
}
