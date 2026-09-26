/**
 * SkillExecutor — 执行链路安全测试（S0 整改回归基线）
 *
 * 覆盖线上真实执行路径（SkillRegistry → SkillExecutor → spawn）：
 * - entry 路径穿越收敛（有 source 根 / 无 source 根）
 * - 环境变量白名单（宿主密钥不泄露，ctx.env 显式注入可见，allowedEnv 可控）
 */
import { chmodSync, mkdtempSync, rmSync, writeFileSync } from 'fs';
import { tmpdir } from 'os';
import { join } from 'path';
import { afterAll, beforeAll, beforeEach, describe, expect, it } from 'vitest';
import { SkillExecutor } from '../src/executor.js';
import { SkillRegistry } from '../src/registry.js';
import type { UnifiedSkill } from '../src/types.js';

let FIXTURES_DIR: string;

beforeAll(() => {
  FIXTURES_DIR = mkdtempSync(join(tmpdir(), 'yyc3-exec-sec-'));
  writeFileSync(join(FIXTURES_DIR, 'main.js'), "console.log('node-script-ok');\n");
  // 读取宿主泄露密钥 / 显式注入变量 / 白名单放行的探针脚本
  writeFileSync(
    join(FIXTURES_DIR, 'env-probe.js'),
    [
      "const secret = process.env.YYC3_EXEC_SECRET ?? 'CLEAN';",
      "const injected = process.env.YYC3_EXEC_INJECTED ?? 'MISSING';",
      "const opted = process.env.YYC3_EXEC_OPTED ?? 'ABSENT';",
      "console.log(JSON.stringify({ secret, injected, opted }));",
      '',
    ].join('\n'),
  );
  const sh = join(FIXTURES_DIR, 'main.sh');
  writeFileSync(sh, '#!/bin/sh\necho "shell-script-ok"\n');
  chmodSync(sh, 0o755);
});

afterAll(() => {
  rmSync(FIXTURES_DIR, { recursive: true, force: true });
});

beforeEach(() => {
  delete process.env.YYC3_EXEC_SECRET;
  delete process.env.YYC3_EXEC_OPTED;
});

function makeSkill(overrides: Partial<UnifiedSkill> = {}): UnifiedSkill {
  return {
    id: 'SEC-001',
    name: '安全测试技能',
    description: '执行链路安全测试',
    domain: 'custom',
    type: 'hybrid',
    runtime: 'node',
    entry: 'main.js',
    source: FIXTURES_DIR,
    inputs: [],
    outputs: [{ type: 'text' }],
    ...overrides,
  };
}

describe('SkillExecutor — entry 路径收敛', () => {
  it('../ 穿越 source 根的 entry 被拒绝（ENTRY_TRAVERSAL）', async () => {
    const registry = new SkillRegistry();
    registry.register(makeSkill({ id: 'SEC-TRAV1', entry: '../../../../tmp/evil.js' }));
    const executor = new SkillExecutor(registry);

    const r = await executor.execute('SEC-TRAV1', {}, { allowFallback: false });
    expect(r.success).toBe(false);
    expect(r.error).toContain('ENTRY_TRAVERSAL');
  });

  it('指向根外的绝对路径 entry 被拒绝', async () => {
    const registry = new SkillRegistry();
    registry.register(makeSkill({ id: 'SEC-TRAV2', entry: '/etc/passwd' }));
    const executor = new SkillExecutor(registry);

    const r = await executor.execute('SEC-TRAV2', {}, { allowFallback: false });
    expect(r.success).toBe(false);
    expect(r.error).toContain('ENTRY_TRAVERSAL');
  });

  it('位于 source 根内的绝对路径 entry 放行', async () => {
    const registry = new SkillRegistry();
    registry.register(makeSkill({ id: 'SEC-ABS-OK', entry: join(FIXTURES_DIR, 'main.js') }));
    const executor = new SkillExecutor(registry);

    const r = await executor.execute('SEC-ABS-OK', {});
    expect(r.success).toBe(true);
    expect(String(r.output)).toBe('node-script-ok');
  });

  it('无 source 时包含 .. 的相对 entry 被拒绝', async () => {
    const registry = new SkillRegistry();
    registry.register(makeSkill({ id: 'SEC-TRAV3', source: undefined, entry: '../escape.js' }));
    const executor = new SkillExecutor(registry);

    const r = await executor.execute('SEC-TRAV3', {}, { allowFallback: false });
    expect(r.success).toBe(false);
    expect(r.error).toContain('ENTRY_TRAVERSAL');
  });

  it('无 source 时的绝对路径 entry 被拒绝', async () => {
    const registry = new SkillRegistry();
    registry.register(makeSkill({ id: 'SEC-TRAV4', source: undefined, entry: '/tmp/x.js' }));
    const executor = new SkillExecutor(registry);

    const r = await executor.execute('SEC-TRAV4', {}, { allowFallback: false });
    expect(r.success).toBe(false);
    expect(r.error).toContain('ENTRY_TRAVERSAL');
  });
});

describe('SkillExecutor — 环境变量白名单', () => {
  it('宿主密钥默认不透传给技能子进程', async () => {
    process.env.YYC3_EXEC_SECRET = 'leak-token';
    const registry = new SkillRegistry();
    registry.register(makeSkill({ id: 'SEC-ENV1', entry: 'env-probe.js' }));
    const executor = new SkillExecutor(registry);

    const r = await executor.execute('SEC-ENV1', {}, { allowFallback: false });
    expect(r.success).toBe(true);
    const probe = JSON.parse(String(r.output).split('\n')[0]);
    expect(probe.secret).toBe('CLEAN');
  });

  it('ctx.env 显式注入的变量对技能可见', async () => {
    const registry = new SkillRegistry();
    registry.register(makeSkill({ id: 'SEC-ENV2', entry: 'env-probe.js' }));
    const executor = new SkillExecutor(registry);

    const r = await executor.execute(
      'SEC-ENV2',
      {},
      { allowFallback: false, env: { YYC3_EXEC_INJECTED: 'visible-value' } },
    );
    expect(r.success).toBe(true);
    const probe = JSON.parse(String(r.output).split('\n')[0]);
    expect(probe.injected).toBe('visible-value');
  });

  it('allowedEnv 显式放行时宿主变量可透传（操作员可控）', async () => {
    process.env.YYC3_EXEC_OPTED = 'opted-in';
    const registry = new SkillRegistry();
    registry.register(makeSkill({ id: 'SEC-ENV3', entry: 'env-probe.js' }));
    const executor = new SkillExecutor(registry);

    const r = await executor.execute(
      'SEC-ENV3',
      {},
      { allowFallback: false, allowedEnv: ['PATH', 'HOME', 'YYC3_EXEC_OPTED'] },
    );
    expect(r.success).toBe(true);
    const probe = JSON.parse(String(r.output).split('\n')[0]);
    expect(probe.opted).toBe('opted-in');
  });
});
