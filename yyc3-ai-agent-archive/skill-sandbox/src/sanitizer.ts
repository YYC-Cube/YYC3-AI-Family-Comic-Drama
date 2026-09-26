/**
 * Skill Sandbox — 输入净化器
 *
 * 负责检测和阻止危险代码、命令注入、路径遍历等攻击。
 *
 * ⚠️ 安全定位：正则黑名单是「尽力而为的内容策略」（纵深防御的一道），
 * 理论上无法穷举所有等价写法，**不得作为唯一安全边界**。
 * 真正的强隔离由执行路径控制点（SkillSandbox 统一入口 + 命令黑名单）
 * 与容器/OS 级隔离（非 root、cap_drop、只读根文件系统、资源限额）共同保证。
 */
import type { SandboxPolicy, SandboxRuntime } from './types.js';

/** 危险模式列表 */
const DANGEROUS_PATTERNS: Record<SandboxRuntime, RegExp[]> = {
  python: [
    /__import__\s*\(\s*['"]os['"]\s*\)/,
    /__import__\s*\(\s*['"]subprocess['"]\s*\)/,
    /__import__\s*\(\s*['"]sys['"]\s*\)/,
    /__import__\s*\(\s*['"]shutil['"]\s*\)/,
    /os\.system\s*\(/,
    /os\.popen\s*\(/,
    /subprocess\.(call|Popen|run|check_output)\s*\(/,
    /eval\s*\(/,
    /exec\s*\(/,
    /compile\s*\(/,
    /open\s*\([^)]*['"]w/,
    /shutil\.(rmtree|move|copy)\s*\(/,
    /os\.(remove|unlink|rmdir|chmod|chown)\s*\(/,
    /socket\./,
    /requests\.(get|post|put|delete|patch)\s*\(/,
    /urllib\./,
    // 反规避（evasion）：别名导入 subprocess（import subprocess as x; x.run(...)）
    /\bimport\s+subprocess\s+as\s+\w+/,
    // 反规避：通过 getattr(__builtins__...) 动态拿 __import__
    /getattr\s*\(\s*__(builtins|import)__/,
    // 反规避：字符串拼接隐藏 __import__（'__imp'+'ort__'）
    /['"]__imp['"]?\s*\+/,
  ],
  node: [
    // 危险模块说明符：require() 与 ESM 静态导入两种形态统一拦截。
    // 模块名兼容 node: 协议前缀（如 require('node:child_process')，Node 12.20+）
    // 与子路径说明符（如 fs/promises）—— 此前裸模块名黑名单可被这两种写法完全绕过。
    /(?:require\s*\(\s*|\bimport\s+[\w$*\s{},]*?\bfrom\s+|\bimport\s*)['"](?:node:)?(?:child_process|fs\/promises|fs|net|http|https|dgram)['"]/,
    /process\.(exit|kill|abort)\s*\(/,
    /eval\s*\(/,
    /Function\s*\(/,
    /__proto__/,
    /constructor\s*\[/,
    /import\s*\(/,
    // 反规避：process.binding 直接取底层绑定
    /process\.binding\s*\(/,
    // 反规避：对全局对象的动态索引访问（globalThis['eva'+'l'] 等拼接取值），
    // 技能脚本中几乎无合法用法，一律拦截
    /\b(globalThis|global|self)\s*\[/,
  ],
  shell: [
    /rm\s+(-rf?\s+)?[~/]/,
    /mkfs\./,
    /dd\s+if=/,
    />\s*\/dev\//,
    /curl\s+.*\|\s*(ba)?sh/,
    /wget\s+.*\|\s*(ba)?sh/,
    /chmod\s+777/,
    /chown\s+root/,
    /:\s*\(\)\s*\{/,
    /\$\(\s*\)\s*\{/,
    /sudo\s+/,
    /passwd\s+/,
    /reboot/,
    /shutdown/,
    /kill\s+-9/,
    /mkfifo\s+/,
    /nc\s+-[el]/,
    // 反规避：base64/xxd/openssl 解码后管道给 shell 解释器
    /\|\s*(base64|xxd|openssl\s+enc)\b[^|]*\|\s*(ba|z|fi|da)?sh\b/,
  ],
  native: [],
};

/** 黑名单命令 */
const BLOCKED_COMMANDS = new Set([
  'rm', 'rmdir', 'mkfs', 'dd', 'shutdown', 'reboot',
  'kill', 'pkill', 'killall', 'sudo', 'su', 'passwd',
  'chmod', 'chown', 'mount', 'umount', 'mkfifo',
  'groupadd', 'groupdel', 'groupmod', 'useradd', 'userdel', 'usermod',
  'ifdown', 'ifup', 'route', 'sysctl', 'systemctl',
  'lvremove', 'pvremove', 'vgremove',
]);

export class Sanitizer {
  private blockedCommands: Set<string>;
  private policy: SandboxPolicy;

  constructor(policy: SandboxPolicy = 'strict', extraBlocked: string[] = []) {
    this.policy = policy;
    this.blockedCommands = new Set([...BLOCKED_COMMANDS, ...extraBlocked]);
  }

  /** 净化代码，返回 { safe, reason } */
  validate(code: string, runtime: SandboxRuntime): { safe: boolean; reason?: string } {
    if (this.policy === 'permissive') {
      return { safe: true };
    }

    // 检查长度
    if (code.length > 100_000) {
      return { safe: false, reason: 'Code exceeds maximum length (100KB)' };
    }

    // 检查危险模式
    const patterns = DANGEROUS_PATTERNS[runtime];
    for (const pattern of patterns) {
      if (pattern.test(code)) {
        return { safe: false, reason: `Dangerous pattern detected: ${pattern.source}` };
      }
    }

    // 检查路径遍历
    if (/\.\.\/|\.\.\\/.test(code)) {
      return { safe: false, reason: 'Path traversal detected' };
    }

    return { safe: true };
  }

  /** 净化命令行参数 */
  sanitizeArgs(args: string[]): string[] {
    return args.map(arg => this.sanitizeArg(arg));
  }

  /** 净化单个参数 */
  sanitizeArg(arg: string): string {
    // 移除 shell 特殊字符
    return arg.replace(/[;&|`$(){}[\]<>!\\]/g, '');
  }

  /** 检查命令是否被禁止 */
  isCommandBlocked(command: string): boolean {
    // 取第一个空白分隔 token 的 basename（兼容绝对路径/尾部斜杠）
    const firstToken = command.trim().split(/\s+/)[0] ?? '';
    const base = firstToken.split('/').filter(Boolean).pop() ?? '';
    return this.blockedCommands.has(base.toLowerCase());
  }

  /** 净化环境变量 */
  sanitizeEnv(env: Record<string, string>): Record<string, string> {
    const sanitized: Record<string, string> = {};
    for (const [key, value] of Object.entries(env)) {
      // 只允许字母数字和下划线组成的 key
      if (/^[A-Za-z_][A-Za-z0-9_]*$/.test(key)) {
        sanitized[key] = this.sanitizeArg(value);
      }
    }
    return sanitized;
  }
}
