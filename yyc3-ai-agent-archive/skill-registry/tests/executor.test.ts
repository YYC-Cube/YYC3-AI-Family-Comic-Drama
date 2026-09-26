/**
 * SkillExecutor 执行器测试 — 降级链与熔断器
 */
import { chmodSync, mkdtempSync, rmSync, writeFileSync } from 'fs';
import { tmpdir } from 'os';
import { join } from 'path';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { SkillExecutor } from '../src/executor.js';
import { SkillRegistry } from '../src/registry.js';
import type { UnifiedSkill } from '../src/types.js';

/** 临时目录：存放真实可执行脚本 fixture */
let FIXTURES_DIR: string;

beforeAll(() => {
  FIXTURES_DIR = mkdtempSync(join(tmpdir(), 'yyc3-exec-'));
  writeFileSync(join(FIXTURES_DIR, 'main.js'), "console.log('node-script-ok');\n");
  writeFileSync(join(FIXTURES_DIR, 'fail.js'), 'process.exit(1);\n');
  const sh = join(FIXTURES_DIR, 'main.sh');
  writeFileSync(sh, '#!/bin/sh\necho "shell-script-ok"\n');
  chmodSync(sh, 0o755);
});

afterAll(() => {
  rmSync(FIXTURES_DIR, { recursive: true, force: true });
});

function makeSkill(overrides: Partial<UnifiedSkill> = {}): UnifiedSkill {
  return {
    id: 'X-001',
    name: '执行测试技能',
    description: '用于执行器测试',
    domain: 'custom',
    type: 'hybrid',
    runtime: 'native',
    entry: '',
    inputs: [],
    outputs: [{ type: 'text' }],
    ...overrides,
  };
}

/** 构造一个必然失败的 skill：node 运行时 + 不存在的入口 */
function makeFailingSkill(overrides: Partial<UnifiedSkill> = {}): UnifiedSkill {
  return makeSkill({
    runtime: 'node',
    entry: 'nonexistent-entry.js',
    source: '/nonexistent',
    ...overrides,
  });
}

describe('SkillExecutor', () => {
  it('执行 native 技能成功', async () => {
    const registry = new SkillRegistry();
    registry.register(makeSkill());
    const executor = new SkillExecutor(registry);

    const result = await executor.execute('X-001', { input: 'demo' });
    expect(result.success).toBe(true);
    expect(result.skillId).toBe('X-001');
    expect(result.executedSkillId).toBe('X-001');
    expect(result.callId).toBeTruthy();
  });

  it('技能不存在时返回失败', async () => {
    const registry = new SkillRegistry();
    const executor = new SkillExecutor(registry);

    const result = await executor.execute('NOT-EXIST', {});
    expect(result.success).toBe(false);
    expect(result.error).toContain('not found');
  });

  it('执行失败自动走降级链', async () => {
    const registry = new SkillRegistry();
    registry.register(makeFailingSkill({ id: 'X-FAIL', fallback: 'X-OK' }));
    registry.register(makeSkill({ id: 'X-OK' }));
    const executor = new SkillExecutor(registry);

    const result = await executor.execute('X-FAIL', {});
    expect(result.success).toBe(true);
    expect(result.fellBack).toBe(true);
    expect(result.executedSkillId).toBe('X-OK');
    expect(result.metadata?.originalError).toBeTruthy();
  });

  it('allowFallback=false 时不降级', async () => {
    const registry = new SkillRegistry();
    registry.register(makeFailingSkill({ id: 'X-FAIL2', fallback: 'X-OK2' }));
    registry.register(makeSkill({ id: 'X-OK2' }));
    const executor = new SkillExecutor(registry);

    const result = await executor.execute('X-FAIL2', {}, { allowFallback: false });
    expect(result.success).toBe(false);
    expect(result.fellBack).toBeFalsy();
  });

  it('连续失败后熔断器打开', async () => {
    const registry = new SkillRegistry();
    registry.register(makeFailingSkill({ id: 'X-CB' }));
    const executor = new SkillExecutor(registry, { failureThreshold: 3, recoveryTimeout: 60_000 });

    // 连续失败 3 次（无降级）
    for (let i = 0; i < 3; i++) {
      const r = await executor.execute('X-CB', {}, { allowFallback: false });
      expect(r.success).toBe(false);
    }

    // 熔断器打开：直接拒绝执行
    expect(executor.getCircuitState('X-CB')).toBe('open');
    const blocked = await executor.execute('X-CB', {}, { allowFallback: false });
    expect(blocked.success).toBe(false);
    expect(blocked.error).toContain('Circuit breaker');

    // 重置后恢复
    executor.resetBreaker('X-CB');
    expect(executor.getCircuitState('X-CB')).toBe('closed');
  });

  it('成功执行后熔断器计数复位', async () => {
    const registry = new SkillRegistry();
    registry.register(makeFailingSkill({ id: 'X-MIX' }));
    registry.register(makeSkill({ id: 'X-NATIVE' }));
    const executor = new SkillExecutor(registry, { failureThreshold: 3 });

    await executor.execute('X-MIX', {}, { allowFallback: false }); // 失败 1 次
    expect(executor.getCircuitState('X-MIX')).toBe('closed');

    registry.unregister('X-MIX');
    registry.register(makeSkill({ id: 'X-MIX' })); // 换成 native 成功执行
    const ok = await executor.execute('X-MIX', {});
    expect(ok.success).toBe(true);
  });

  it('脚本技能无 entry 时返回失败', async () => {
    const registry = new SkillRegistry();
    registry.register(makeSkill({ id: 'X-NOENTRY', runtime: 'node', entry: '' }));
    const executor = new SkillExecutor(registry);

    const result = await executor.execute('X-NOENTRY', {}, { allowFallback: false });
    expect(result.success).toBe(false);
    expect(result.error).toContain('No entry point');
  });

  it('node 脚本技能成功执行并捕获输出', async () => {
    const registry = new SkillRegistry();
    registry.register(
      makeSkill({
        id: 'X-NODE',
        runtime: 'node',
        entry: 'main.js',
        source: FIXTURES_DIR,
      })
    );
    const executor = new SkillExecutor(registry);

    const result = await executor.execute('X-NODE', {});
    expect(result.success).toBe(true);
    expect(String(result.output)).toBe('node-script-ok');
  });

  it('node 脚本非零退出时返回失败', async () => {
    const registry = new SkillRegistry();
    registry.register(
      makeSkill({
        id: 'X-NODE-FAIL',
        runtime: 'node',
        entry: 'fail.js',
        source: FIXTURES_DIR,
      })
    );
    const executor = new SkillExecutor(registry);

    const result = await executor.execute('X-NODE-FAIL', {}, { allowFallback: false });
    expect(result.success).toBe(false);
  });

  it('超过最大降级深度后停止降级', async () => {
    const registry = new SkillRegistry();
    registry.register(makeFailingSkill({ id: 'D0', fallback: 'D1' }));
    registry.register(makeFailingSkill({ id: 'D1', fallback: 'D2' }));
    registry.register(makeFailingSkill({ id: 'D2', fallback: 'D3' }));
    registry.register(makeFailingSkill({ id: 'D3' }));
    const executor = new SkillExecutor(registry);

    const result = await executor.execute('D0', {}, { maxFallbackDepth: 2 });
    expect(result.success).toBe(false);
    expect(result.skillId).toBe('D2'); // 在深度 2 停止
  });

  it('shell 运行时执行真实脚本', async () => {
    const registry = new SkillRegistry();
    registry.register(
      makeSkill({
        id: 'X-SH',
        runtime: 'shell',
        entry: 'main.sh',
        source: FIXTURES_DIR,
      })
    );
    const executor = new SkillExecutor(registry);

    const result = await executor.execute('X-SH', {});
    expect(result.success).toBe(true);
    expect(String(result.output)).toContain('shell-script-ok');
  });

  it('half-open 状态下成功探测后熔断器闭合', async () => {
    const registry = new SkillRegistry();
    registry.register(makeFailingSkill({ id: 'X-HALF' }));
    const executor = new SkillExecutor(registry, {
      failureThreshold: 1,
      recoveryTimeout: 50, // 50ms 后进入 half-open
    });

    await executor.execute('X-HALF', {}, { allowFallback: false }); // 熔断打开
    expect(executor.getCircuitState('X-HALF')).toBe('open');

    await new Promise((r) => setTimeout(r, 80)); // 等待恢复窗口

    registry.unregister('X-HALF');
    registry.register(makeSkill({ id: 'X-HALF' })); // 替换为可成功执行的技能
    const result = await executor.execute('X-HALF', {});
    expect(result.success).toBe(true);
    expect(executor.getCircuitState('X-HALF')).toBe('closed');
  });
});
