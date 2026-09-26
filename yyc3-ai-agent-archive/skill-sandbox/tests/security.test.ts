/**
 * Skill Sandbox — 安全对抗矩阵（evasion / 控制点接线测试）
 *
 * 本文件是 S0 安全整改的回归基线：
 * 与 sandbox.test.ts 中「黑名单正面命中」用例互补，这里专门验证：
 * 1. 真实执行路径（SkillSandbox.execute）必须经过命令黑名单控制点；
 * 2. 已知规避写法（别名导入 / 动态导入 / 编码管道）必须被内容策略拦截；
 * 3. 环境变量白名单 / cwd 收敛 / timeout 钳制在子进程层面真实生效。
 */
import { afterEach, describe, expect, it } from 'vitest';
import {
  PathTraversalError,
  Sanitizer,
  SkillSandbox,
  assertSafeRelativeEntry,
  buildSafeEnv,
  confineWithinRoot,
  normalizeTimeout,
} from '../src/index.js';

describe('安全原语 security.ts', () => {
  describe('confineWithinRoot', () => {
    it('根内相对路径放行并返回绝对路径', () => {
      const full = confineWithinRoot('/tmp/skill-root', 'scripts/main.js');
      expect(full).toBe('/tmp/skill-root/scripts/main.js');
    });

    it('../ 穿越被拒绝', () => {
      expect(() => confineWithinRoot('/tmp/skill-root', '../../etc/passwd')).toThrow(PathTraversalError);
    });

    it('指向根外的绝对路径被拒绝', () => {
      expect(() => confineWithinRoot('/tmp/skill-root', '/etc/passwd')).toThrow(PathTraversalError);
    });

    it('根目录自身放行', () => {
      expect(confineWithinRoot('/tmp/skill-root', '.')).toBe('/tmp/skill-root');
    });
  });

  describe('assertSafeRelativeEntry', () => {
    it('普通相对路径放行', () => {
      expect(() => assertSafeRelativeEntry('main.js')).not.toThrow();
    });

    it('绝对路径拒绝', () => {
      expect(() => assertSafeRelativeEntry('/tmp/x.js')).toThrow(PathTraversalError);
    });

    it('包含 .. 段拒绝', () => {
      expect(() => assertSafeRelativeEntry('../x.js')).toThrow();
      expect(() => assertSafeRelativeEntry('a/../../b')).toThrow();
    });

    it('空路径拒绝', () => {
      expect(() => assertSafeRelativeEntry('')).toThrow();
    });
  });

  describe('buildSafeEnv', () => {
    const saved = { ...process.env };

    afterEach(() => {
      process.env = { ...saved };
    });

    it('仅透传白名单中的宿主变量', () => {
      process.env.ALLOWED_KEEP = 'keep';
      process.env.YYC3_SECRET_TOKEN = 'super-secret';
      const env = buildSafeEnv(['ALLOWED_KEEP']);
      expect(env.ALLOWED_KEEP).toBe('keep');
      expect(env.YYC3_SECRET_TOKEN).toBeUndefined();
    });

    it('叠加合法的显式注入项', () => {
      const env = buildSafeEnv([], { SKILL_ARG: 'value' });
      expect(env.SKILL_ARG).toBe('value');
    });

    it('非法环境变量名被忽略', () => {
      const env = buildSafeEnv([], { 'BAD-NAME': 'x', '9LEAD': 'y', OK_NAME: 'z' } as never);
      expect(env['BAD-NAME']).toBeUndefined();
      expect(env['9LEAD']).toBeUndefined();
      expect(env.OK_NAME).toBe('z');
    });
  });

  describe('normalizeTimeout', () => {
    it('undefined 回退默认值', () => {
      expect(normalizeTimeout(undefined, 30_000, 300_000)).toBe(30_000);
    });

    it('0 / 负数 / NaN 回退默认值（不得变成 spawn 的「无超时」）', () => {
      expect(normalizeTimeout(0, 30_000, 300_000)).toBe(30_000);
      expect(normalizeTimeout(-5, 30_000, 300_000)).toBe(30_000);
      expect(normalizeTimeout(Number.NaN, 30_000, 300_000)).toBe(30_000);
    });

    it('超过最大值截断', () => {
      expect(normalizeTimeout(999_999, 30_000, 300_000)).toBe(300_000);
    });

    it('合法正值原样保留', () => {
      expect(normalizeTimeout(500, 30_000, 300_000)).toBe(500);
    });
  });
});

describe('反规避内容策略（evasion patterns）', () => {
  const sanitizer = new Sanitizer('strict');

  it('Python: 别名导入 subprocess 被拦截', () => {
    const r = sanitizer.validate('import subprocess as x; x.run(["id"])', 'python');
    expect(r.safe).toBe(false);
  });

  it('Python: getattr(__builtins__) 动态取 __import__ 被拦截', () => {
    const r = sanitizer.validate("getattr(__builtins__, '__imp' + 'ort__')('os')", 'python');
    expect(r.safe).toBe(false);
  });

  it('Python: 字符串拼接隐藏 __import__ 被拦截', () => {
    const r = sanitizer.validate("const name = '__imp' + 'ort__';", 'python');
    expect(r.safe).toBe(false);
  });

  it('Node: process.binding 底层绑定被拦截', () => {
    const r = sanitizer.validate('process.binding("spawn_sync")', 'node');
    expect(r.safe).toBe(false);
  });

  it('Node: globalThis 动态索引取 eval 被拦截', () => {
    const r = sanitizer.validate("globalThis['eva' + 'l']('1+1')", 'node');
    expect(r.safe).toBe(false);
  });

  it('Node: node: 协议前缀 require 被拦截（scheme 绕过回归）', () => {
    expect(sanitizer.validate("require('node:fs')", 'node').safe).toBe(false);
    expect(sanitizer.validate('require("node:child_process")', 'node').safe).toBe(false);
    expect(sanitizer.validate("require('node:net')", 'node').safe).toBe(false);
    expect(sanitizer.validate("require('node:http')", 'node').safe).toBe(false);
    expect(sanitizer.validate("require('node:https')", 'node').safe).toBe(false);
    expect(sanitizer.validate("require('node:dgram')", 'node').safe).toBe(false);
  });

  it('Node: fs/promises 子路径说明符被拦截', () => {
    expect(sanitizer.validate("require('fs/promises')", 'node').safe).toBe(false);
    expect(sanitizer.validate("require('node:fs/promises')", 'node').safe).toBe(false);
  });

  it('Node: ESM 静态导入危险模块被拦截', () => {
    expect(sanitizer.validate("import { readFile } from 'node:fs';", 'node').safe).toBe(false);
    expect(sanitizer.validate('import fs from "fs";', 'node').safe).toBe(false);
    expect(sanitizer.validate("import { spawn } from 'node:child_process';", 'node').safe).toBe(false);
    expect(sanitizer.validate("import 'node:fs';", 'node').safe).toBe(false);
  });

  it('Node: 动态 import() 加载 node:fs 被拦截', () => {
    expect(sanitizer.validate("import('node:fs').then(m => m.readFile)", 'node').safe).toBe(false);
  });

  it('Shell: base64 解码后管道给 sh 被拦截', () => {
    const r = sanitizer.validate('echo ZWxv | base64 -d | sh', 'shell');
    expect(r.safe).toBe(false);
  });

  it('正常代码不受新增模式误伤', () => {
    expect(sanitizer.validate('const x = "import subprocess as nothing"; console.log(x);', 'node').safe).toBe(true);
    expect(sanitizer.validate('print("base64 is a word, not a pipe")', 'python').safe).toBe(true);
    // 非黑名单模块（含 node: 前缀）保持放行
    expect(sanitizer.validate("const z = require('node:zlib'); console.log(typeof z);", 'node').safe).toBe(true);
    // 叙述性文本中含 import ... from 不构成模块导入
    expect(sanitizer.validate("const note = 'please import helpers from the shared registry';", 'node').safe).toBe(true);
  });
});

describe('SkillSandbox 执行路径控制点', () => {
  it('native: rm 命令在执行路径被黑名单拦截（不产生子进程）', async () => {
    const sandbox = new SkillSandbox({ policy: 'strict' });
    const r = await sandbox.execute({ runtime: 'native', code: 'rm -rf /' });
    expect(r.ok).toBe(false);
    expect(r.error).toContain('COMMAND_BLOCKED');
  });

  it('native: sudo/killall 被拦截', async () => {
    const sandbox = new SkillSandbox({ policy: 'strict' });
    const r1 = await sandbox.execute({ runtime: 'native', code: 'sudo sh' });
    const r2 = await sandbox.execute({ runtime: 'native', code: 'killall node' });
    expect(r1.error).toContain('COMMAND_BLOCKED');
    expect(r2.error).toContain('COMMAND_BLOCKED');
  });

  it('拦截时发出 execution:blocked 事件', async () => {
    const sandbox = new SkillSandbox({ policy: 'strict' });
    let blockedReason = '';
    sandbox.on('execution:blocked', (_req, reason) => {
      blockedReason = reason;
    });
    await sandbox.execute({ runtime: 'native', code: 'chmod 777 x' });
    expect(blockedReason).toContain('chmod');
  });

  it('native 正常命令（echo）仍可执行', async () => {
    const sandbox = new SkillSandbox({ policy: 'strict' });
    const r = await sandbox.execute({ runtime: 'native', code: 'echo ok', args: ['pass'] });
    expect(r.ok).toBe(true);
    expect(r.stdout).toContain('ok pass');
  });

  it('permissive 策略跳过黑名单（保持「全部放行」语义）', async () => {
    const sandbox = new SkillSandbox({ policy: 'permissive' });
    const r = await sandbox.execute({ runtime: 'native', code: 'killall' });
    // 关键断言：没有被 COMMAND_BLOCKED 拦截（实际执行：usage 退出或 ENOENT）
    expect(r.error ?? '').not.toContain('COMMAND_BLOCKED');
  });

  it('环境隔离：宿主密钥不透传给技能子进程', async () => {
    process.env.YYC3_EVASION_SECRET = 'leak-token';
    try {
      const sandbox = new SkillSandbox({ policy: 'strict' });
      const r = await sandbox.execute({
        runtime: 'node',
        code: 'console.log(process.env.YYC3_EVASION_SECRET ?? "CLEAN");',
      });
      expect(r.ok).toBe(true);
      expect(r.stdout.trim()).toBe('CLEAN');
    } finally {
      delete process.env.YYC3_EVASION_SECRET;
    }
  });

  it('显式注入的环境变量对技能可见', async () => {
    const sandbox = new SkillSandbox({ policy: 'strict' });
    const r = await sandbox.execute({
      runtime: 'node',
      code: 'console.log(process.env.SKILL_GREETING);',
      env: { SKILL_GREETING: 'hello-from-ctx' },
    });
    expect(r.stdout.trim()).toBe('hello-from-ctx');
  });

  it('cwd 收敛：逃逸收敛根的工作目录被拒绝', async () => {
    const sandbox = new SkillSandbox({ policy: 'strict', workDir: process.cwd() });
    const r = await sandbox.execute({ runtime: 'node', code: 'console.log(1)', cwd: '/' });
    expect(r.ok).toBe(false);
    expect(r.error).toContain('CWD_ESCAPE');
  });

  it('cwd 收敛：根内目录放行', async () => {
    const sandbox = new SkillSandbox({ policy: 'strict', workDir: process.cwd() });
    const r = await sandbox.execute({
      runtime: 'node',
      code: 'console.log("in-root");',
      cwd: process.cwd(),
    });
    expect(r.ok).toBe(true);
    expect(r.stdout.trim()).toBe('in-root');
  });

  it('timeout: 0 被钳制为配置的默认超时（长任务仍被杀）', async () => {
    const sandbox = new SkillSandbox({
      policy: 'strict',
      defaultTimeout: 300,
      maxTimeout: 5_000,
    });
    const r = await sandbox.execute({ runtime: 'node', code: 'while (true) {}', timeout: 0 });
    expect(r.timedOut).toBe(true);
    expect(r.ok).toBe(false);
    expect(r.duration).toBeLessThan(2_000);
  });
});
