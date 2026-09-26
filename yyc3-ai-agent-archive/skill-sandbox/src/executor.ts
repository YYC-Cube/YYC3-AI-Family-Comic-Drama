/**
 * Skill Sandbox — 核心执行引擎
 *
 * 基于 child_process 实现安全隔离执行
 * 支持 Node / Python / Shell 运行时
 */
import { execFileSync, spawn } from 'node:child_process';
import { normalizeTimeout } from './security.js';
import type { SandboxRequest, SandboxResult, SandboxRuntime } from './types.js';

/** 运行时命令映射 */
const RUNTIME_COMMANDS: Record<SandboxRuntime, string> = {
  node: 'node',
  python: 'python3',
  shell: 'sh',
  native: '',
};

/** 底层执行器硬超时上限（毫秒），防止调用方漏配 maxTimeout */
const HARD_MAX_TIMEOUT = 300_000;
/** 默认超时（毫秒） */
const DEFAULT_TIMEOUT = 30_000;

export class Executor {
  /** 执行沙箱请求 */
  static async execute(request: SandboxRequest, signal?: AbortSignal): Promise<SandboxResult> {
    const startTime = Date.now();

    try {
      const { command, args } = this.buildCommand(request);
      // 非法超时值（0/负数/NaN）回退默认值，防止 spawn timeout:0 退化为「无超时」
      const timeout = normalizeTimeout(request.timeout, DEFAULT_TIMEOUT, HARD_MAX_TIMEOUT);
      const maxOutput = request.maxOutput ?? 1024 * 1024; // 1MB

      return new Promise<SandboxResult>((resolve) => {
        const child = spawn(command, args, {
          // 安全约定：SkillSandbox 传入的 env 是白名单裁剪后的最小集合，
          // 此处不得再合并 process.env；仅当底层 Executor 被直接调用且未给 env
          // 时才回退继承当前环境（保持向后兼容）。
          env: request.env ?? process.env,
          cwd: request.cwd ?? process.cwd(),
          timeout,
          stdio: ['pipe', 'pipe', 'pipe'],
        });

        let stdout = '';
        let stderr = '';
        let timedOut = false;
        let killed = false;

        const onData = (chunk: Buffer, stream: 'stdout' | 'stderr') => {
          const text = chunk.toString('utf-8');
          if (stream === 'stdout') {
            if (stdout.length < maxOutput) {
              stdout += text;
              if (stdout.length > maxOutput) {
                stdout = stdout.slice(0, maxOutput);
              }
            }
          } else {
            if (stderr.length < maxOutput) {
              stderr += text;
              if (stderr.length > maxOutput) {
                stderr = stderr.slice(0, maxOutput);
              }
            }
          }
        };

        child.stdout?.on('data', (chunk: Buffer) => onData(chunk, 'stdout'));
        child.stderr?.on('data', (chunk: Buffer) => onData(chunk, 'stderr'));

        child.on('error', (err: Error) => {
          if (!killed) {
            resolve({
              ok: false,
              exitCode: -1,
              stdout: stdout.trimEnd(),
              stderr: stderr.trimEnd(),
              duration: Date.now() - startTime,
              timedOut: false,
              error: err.message,
            });
            killed = true;
          }
        });

        child.on('close', (exitCode: number | null, signal: NodeJS.Signals | null) => {
          if (killed) return;
          killed = true;

          resolve({
            ok: exitCode === 0,
            exitCode: exitCode ?? -1,
            stdout: stdout.trimEnd(),
            stderr: stderr.trimEnd(),
            duration: Date.now() - startTime,
            timedOut: signal === 'SIGTERM' || timedOut,
            signal: signal ?? undefined,
          });
        });

        // 监听 abort signal
        if (signal) {
          if (signal.aborted) {
            child.kill('SIGTERM');
            return;
          }
          signal.addEventListener('abort', () => {
            child.kill('SIGTERM');
          }, { once: true });
        }

        // 超时
        const timer = setTimeout(() => {
          timedOut = true;
          child.kill('SIGTERM');
        }, timeout);

        child.on('close', () => clearTimeout(timer));

        // 写入 stdin（子进程可能提前退出导致管道关闭，吞掉 EPIPE）
        if (request.code) {
          child.stdin?.on('error', () => { });
          child.stdin?.write(request.code);
          child.stdin?.end();
        }
      });
    } catch (err) {
      return {
        ok: false,
        exitCode: -1,
        stdout: '',
        stderr: '',
        duration: Date.now() - startTime,
        timedOut: false,
        error: err instanceof Error ? err.message : 'Unknown execution error',
      };
    }
  }

  /** 构建命令和参数 */
  private static buildCommand(request: SandboxRequest): { command: string; args: string[] } {
    const runtime = RUNTIME_COMMANDS[request.runtime];
    const code = request.code;

    switch (request.runtime) {
      case 'node':
        return { command: runtime, args: ['-e', code] };
      case 'python':
        return { command: runtime, args: ['-c', code] };
      case 'shell':
        return { command: runtime, args: ['-c', code] };
      case 'native': {
        const parts = code.split(/\s+/);
        const cmd = parts[0];
        if (!cmd || cmd.includes('/') || cmd.includes('..')) {
          throw new Error(`Invalid native command: ${cmd}`);
        }
        return {
          command: cmd,
          args: [...parts.slice(1), ...(request.args ?? [])],
        };
      }
      default:
        throw new Error(`Unsupported runtime: ${request.runtime}`);
    }
  }

  /** 检查运行时是否可用（同步等待 which 退出码，缺失时返回 false） */
  static isRuntimeAvailable(runtime: SandboxRuntime): boolean {
    if (runtime === 'native') return true;
    try {
      execFileSync('which', [RUNTIME_COMMANDS[runtime]], { stdio: 'ignore' });
      return true;
    } catch {
      return false;
    }
  }
}
