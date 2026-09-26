/**
 * YYC³ Skill 沙箱执行环境
 * @module @yyc3/skill-sandbox
 *
 * 安全隔离执行引擎，支持：
 * - 多运行时 (Node/Python/Shell/Native)
 * - 代码安全检测（危险模式拦截）
 * - 输入净化（命令注入/XSS/路径遍历防护）
 * - 资源限制（超时/输出截断/进程隔离）
 * - 事件驱动（执行/完成/超时/错误/拦截）
 *
 * 使用方式：
 * ```ts
 * import { SkillSandbox } from '@yyc3/skill-sandbox';
 *
 * const sandbox = new SkillSandbox({ policy: 'strict' });
 *
 * sandbox.on('execution:complete', (result) => {
 *   console.log(`Exit: ${result.exitCode}, ${result.duration}ms`);
 * });
 *
 * const result = await sandbox.execute({
 *   runtime: 'python',
 *   code: 'print("hello world")',
 *   timeout: 5000,
 * });
 * ```
 */

export { SkillSandbox } from './sandbox.js';
export { Sanitizer } from './sanitizer.js';
export { Executor } from './executor.js';
export {
  PathTraversalError,
  confineWithinRoot,
  assertSafeRelativeEntry,
  buildSafeEnv,
  normalizeTimeout,
} from './security.js';
export type {
  SandboxRequest,
  SandboxResult,
  SandboxConfig,
  SandboxRuntime,
  SandboxPolicy,
  SandboxEvents,
} from './types.js';