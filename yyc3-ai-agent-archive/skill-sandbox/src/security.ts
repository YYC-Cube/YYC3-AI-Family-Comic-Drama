/**
 * Skill Sandbox — 安全原语
 * @module @yyc3/skill-sandbox/security
 *
 * 可复用的执行期安全控制函数，供 SkillSandbox 与 @yyc3/skill-registry
 * 的执行链路共同消费，确保「执行路径必经控制点」：
 * - confineWithinRoot：路径收敛，防止 entry 穿越技能根目录（../ 逃逸 / 绝对路径逃逸）
 * - buildSafeEnv：环境变量白名单，杜绝宿主密钥全量透传给技能子进程
 * - normalizeTimeout：超时值规范化，0/负数/NaN 不得绕过为「无超时」
 *
 * 注意：这些是进程内控制（纵深防御的一道），真正的强安全边界由容器 /
 * OS 级隔离提供（见 docker-compose.yml 的 security_opt/cap_drop/read_only）。
 */
import path from 'node:path';

/** 路径穿越错误（执行器捕获后转换为 SECURITY_BLOCKED 结果） */
export class PathTraversalError extends Error {
  constructor(
    public readonly target: string,
    public readonly root: string,
  ) {
    super(`ENTRY_TRAVERSAL: path "${target}" escapes confinement root "${root}"`);
    this.name = 'PathTraversalError';
  }
}

/**
 * 将目标路径收敛在 rootDir 之内，返回规范化后的绝对路径。
 * 解析结果若不在 rootDir 子树内（含 ../ 逃逸与指向根外的绝对路径），抛 PathTraversalError。
 */
export function confineWithinRoot(rootDir: string, targetPath: string): string {
  const root = path.resolve(rootDir);
  const full = path.resolve(root, targetPath);
  if (full !== root && !full.startsWith(root + path.sep)) {
    throw new PathTraversalError(targetPath, root);
  }
  return full;
}

/**
 * 无收敛根（source）时的入口校验：
 * 禁止绝对路径与任何以 `..` 分段的路径，只允许相对路径（相对调用方 cwd）。
 */
export function assertSafeRelativeEntry(entry: string): void {
  if (!entry || path.isAbsolute(entry) || entry.split(/[\\/]/).includes('..')) {
    throw new PathTraversalError(entry ?? '(empty)', '(relative-only)');
  }
}

/**
 * 构造技能子进程的最小环境：
 * 仅透传白名单中的宿主变量（默认 PATH/HOME 等运行必需项），
 * 叠加调用方显式注入的变量（key 必须是合法 shell 标识符）。
 * 宿主的 API Key / Token 等不会进入技能进程。
 */
export function buildSafeEnv(
  allowedEnv: readonly string[],
  extra?: Record<string, string>,
): Record<string, string> {
  const env: Record<string, string> = {};
  for (const key of allowedEnv) {
    const value = process.env[key];
    if (value !== undefined) {
      env[key] = value;
    }
  }
  if (extra) {
    for (const [key, value] of Object.entries(extra)) {
      if (/^[A-Za-z_][A-Za-z0-9_]*$/.test(key)) {
        env[key] = value;
      }
    }
  }
  return env;
}

/**
 * 超时值规范化：
 * - undefined / 非有限数 / <=0 → 回退到默认值（防止 timeout:0 被 spawn 解释为「无超时」）
 * - 超过最大值 → 截断到最大值
 */
export function normalizeTimeout(value: number | undefined, fallback: number, max: number): number {
  if (value === undefined || !Number.isFinite(value) || value <= 0) {
    return fallback;
  }
  return Math.min(value, max);
}
