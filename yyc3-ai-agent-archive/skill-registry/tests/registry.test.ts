/**
 * SkillRegistry 注册中心测试
 */
import { describe, it, expect } from 'vitest';
import { SkillRegistry } from '../src/registry.js';
import type { UnifiedSkill } from '../src/types.js';

function makeSkill(overrides: Partial<UnifiedSkill> = {}): UnifiedSkill {
  return {
    id: 'TEST-001',
    name: '测试技能',
    description: '用于单元测试的示例技能',
    domain: 'custom',
    type: 'hybrid',
    runtime: 'native',
    entry: '',
    inputs: [],
    outputs: [{ type: 'text' }],
    tags: ['test'],
    ...overrides,
  };
}

describe('SkillRegistry', () => {
  it('注册并获取 Skill', () => {
    const registry = new SkillRegistry();
    const skill = makeSkill();
    registry.register(skill);

    expect(registry.has('TEST-001')).toBe(true);
    expect(registry.get('TEST-001')).toEqual(skill);
    expect(registry.getAll()).toHaveLength(1);
  });

  it('注册时发出 skill:registered 事件', () => {
    const registry = new SkillRegistry();
    const events: string[] = [];
    registry.on('skill:registered', ({ skill }) => events.push(skill.id));
    registry.register(makeSkill());
    expect(events).toEqual(['TEST-001']);
  });

  it('注销 Skill 并发出事件', () => {
    const registry = new SkillRegistry();
    registry.register(makeSkill());
    const events: string[] = [];
    registry.on('skill:unregistered', ({ id }) => events.push(id));

    expect(registry.unregister('TEST-001')).toBe(true);
    expect(registry.has('TEST-001')).toBe(false);
    expect(registry.unregister('NOT-EXIST')).toBe(false);
    expect(events).toEqual(['TEST-001']);
  });

  it('事件处理器抛错不影响其他处理器', () => {
    const registry = new SkillRegistry();
    const received: string[] = [];
    registry.on('skill:registered', () => {
      throw new Error('handler error');
    });
    registry.on('skill:registered', ({ skill }) => received.push(skill.id));
    registry.register(makeSkill());
    expect(received).toEqual(['TEST-001']);
  });

  it('off 取消订阅', () => {
    const registry = new SkillRegistry();
    const received: string[] = [];
    const handler = ({ id }: { id: string }) => received.push(id);
    registry.on('skill:unregistered', handler);
    registry.off('skill:unregistered', handler);
    registry.register(makeSkill());
    registry.unregister('TEST-001');
    expect(received).toEqual([]);
  });

  it('按领域与标签索引查询', () => {
    const registry = new SkillRegistry();
    registry.register(makeSkill({ id: 'A-001', domain: 'glm-ocr', tags: ['ocr', 'vision'] }));
    registry.register(makeSkill({ id: 'A-002', domain: 'glm-vision', tags: ['vision'] }));
    registry.register(makeSkill({ id: 'A-003', domain: 'glm-ocr', tags: [] }));

    expect(registry.getByDomain('glm-ocr')).toHaveLength(2);
    expect(registry.getByTag('vision')).toHaveLength(2);
    expect(registry.getByTag('ocr')).toHaveLength(1);
  });

  it('文本搜索匹配 name/description/id/tags', () => {
    const registry = new SkillRegistry();
    registry.register(makeSkill({ id: 'B-001', name: '论文速读', description: '论文阅读工具', tags: ['paper'] }));
    registry.register(makeSkill({ id: 'B-002', name: '股票分析', description: '金融分析', tags: [] }));

    expect(registry.search({ query: '论文' })).toHaveLength(1);
    expect(registry.search({ query: '金融' })).toHaveLength(1);
    expect(registry.search({ query: 'B-001' })).toHaveLength(1);
    expect(registry.search({ query: 'paper' })).toHaveLength(1);
    expect(registry.search({ query: '不存在' })).toHaveLength(0);
  });

  it('组合筛选与分页', () => {
    const registry = new SkillRegistry();
    for (let i = 1; i <= 5; i++) {
      registry.register(
        makeSkill({ id: `C-${String(i).padStart(3, '0')}`, domain: 'marketplace' })
      );
    }
    registry.register(makeSkill({ id: 'C-006', domain: 'b2b' }));

    const results = registry.search({ domain: 'marketplace', limit: 2, offset: 1 });
    expect(results).toHaveLength(2);
    expect(results[0].id).toBe('C-002');
  });

  it('默认仅返回 active 状态的 Skill', () => {
    const registry = new SkillRegistry();
    registry.register(makeSkill({ id: 'D-001', status: 'active' }));
    registry.register(makeSkill({ id: 'D-002', status: 'deprecated' }));
    registry.register(makeSkill({ id: 'D-003', status: 'disabled' }));

    expect(registry.search()).toHaveLength(1);
    expect(registry.search({ status: 'deprecated' })).toHaveLength(1);
  });

  it('降级链解析（含循环防护）', () => {
    const registry = new SkillRegistry();
    registry.register(makeSkill({ id: 'E-001', fallback: 'E-002' }));
    registry.register(makeSkill({ id: 'E-002', fallback: 'E-003' }));
    registry.register(makeSkill({ id: 'E-003' }));
    expect(registry.getFallbackChain('E-001')).toEqual(['E-001', 'E-002', 'E-003']);

    // 循环引用防护：F-001 → F-002 → F-001
    registry.register(makeSkill({ id: 'F-001', fallback: 'F-002' }));
    registry.register(makeSkill({ id: 'F-002', fallback: 'F-001' }));
    expect(registry.getFallbackChain('F-001')).toEqual(['F-001', 'F-002']);
  });

  it('统计信息聚合', () => {
    const registry = new SkillRegistry();
    registry.register(
      makeSkill({ id: 'G-001', domain: 'glm-ocr', fallback: 'G-002', evals: { version: '1', cases: [] } })
    );
    registry.register(makeSkill({ id: 'G-002', domain: 'glm-vision', type: 'script', runtime: 'python' }));

    const stats = registry.getStats();
    expect(stats.totalSkills).toBe(2);
    expect(stats.byDomain['glm-ocr']).toBe(1);
    expect(stats.byRuntime['python']).toBe(1);
    expect(stats.withEvals).toBe(1);
    expect(stats.withFallback).toBe(1);
  });

  it('export / import 往返', () => {
    const registry = new SkillRegistry();
    registry.register(makeSkill());
    const restored = new SkillRegistry();
    restored.import(registry.export());
    expect(restored.get('TEST-001')).toEqual(registry.get('TEST-001'));
  });

  it('同名冲突：高版本胜出，低版本记录为变体', () => {
    const registry = new SkillRegistry();
    const dupEvents: string[] = [];
    registry.on('skill:duplicate', ({ id, kept, variant }) =>
      dupEvents.push(`${id}:${kept.version}>${variant.version}`)
    );

    registry.register(makeSkill({ id: 'DUP-001', version: '1.0.0' }));
    registry.register(makeSkill({ id: 'DUP-001', version: '1.2.0' }));

    expect(registry.get('DUP-001')!.version).toBe('1.2.0');
    expect(registry.getVariants('DUP-001')).toHaveLength(1);
    expect(registry.getVariants('DUP-001')[0].version).toBe('1.0.0');
    expect(registry.getDuplicateIds()).toEqual(['DUP-001']);
    expect(dupEvents).toEqual(['DUP-001:1.2.0>1.0.0']);
  });

  it('同名冲突：后续低版本不覆盖主技能', () => {
    const registry = new SkillRegistry();
    registry.register(makeSkill({ id: 'DUP-002', version: '2.0.0' }));
    registry.register(makeSkill({ id: 'DUP-002', version: '1.0.0' }));

    expect(registry.get('DUP-002')!.version).toBe('2.0.0');
    expect(registry.getVariants('DUP-002')).toHaveLength(1);
    expect(registry.getVariants('DUP-002')[0].version).toBe('1.0.0');
  });

  it('同名冲突：版本不可解析时保留先注册者', () => {
    const registry = new SkillRegistry();
    registry.register(makeSkill({ id: 'DUP-003', version: 'stable' }));
    registry.register(makeSkill({ id: 'DUP-003', version: '1.0.0' }));

    expect(registry.get('DUP-003')!.version).toBe('stable');
    expect(registry.getVariants('DUP-003')).toHaveLength(1);
  });

  it('注销时清理变体记录，统计含 withVariants', () => {
    const registry = new SkillRegistry();
    registry.register(makeSkill({ id: 'DUP-004', version: '1.0.0' }));
    registry.register(makeSkill({ id: 'DUP-004', version: '1.1.0' }));
    expect(registry.getStats().withVariants).toBe(1);

    registry.unregister('DUP-004');
    expect(registry.getVariants('DUP-004')).toHaveLength(0);
    expect(registry.getStats().withVariants).toBe(0);
  });
});
