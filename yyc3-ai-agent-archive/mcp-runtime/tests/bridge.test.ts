/**
 * SkillMCPBridge 桥接器测试 — Skill → MCP Tool 转换
 */
import { describe, it, expect } from 'vitest';
import { SkillMCPBridge } from '../src/bridge.js';
import { SkillRegistry, SkillExecutor } from '@yyc3/skill-registry';
import type { UnifiedSkill } from '@yyc3/skill-registry';

function makeSkill(overrides: Partial<UnifiedSkill> = {}): UnifiedSkill {
  return {
    id: 'B-001',
    name: '桥接测试技能',
    description: '用于桥接器测试',
    domain: 'marketplace',
    type: 'hybrid',
    runtime: 'native',
    entry: '',
    inputs: [
      { name: 'query', type: 'string', description: '查询文本', required: true },
      { name: 'limit', type: 'number', description: '返回数量', required: false, default: 10 },
    ],
    outputs: [{ type: 'text' }],
    ...overrides,
  };
}

describe('SkillMCPBridge', () => {
  it('将单个 Skill 转换为 MCP Tool', () => {
    const registry = new SkillRegistry();
    registry.register(makeSkill());
    const bridge = new SkillMCPBridge(registry, new SkillExecutor(registry));

    const tools = bridge.toMCPTools();
    expect(tools).toHaveLength(1);
    const tool = tools[0].tool;
    expect(tool.name).toBe('B-001');
    expect(tool.description).toBe('用于桥接器测试');
    expect(tool.inputSchema.type).toBe('object');
    expect(tool.inputSchema.properties['query'].type).toBe('string');
    expect(tool.inputSchema.properties['limit'].type).toBe('number');
    expect(tool.inputSchema.required).toContain('query');
    expect(tool.inputSchema.required).not.toContain('limit');
  });

  it('无 inputs 的 Skill 自动生成默认 args 参数', () => {
    const registry = new SkillRegistry();
    registry.register(makeSkill({ id: 'B-002', inputs: [] }));
    const bridge = new SkillMCPBridge(registry, new SkillExecutor(registry));

    const tools = bridge.toMCPTools();
    expect(tools).toHaveLength(1);
    expect(tools[0].tool.inputSchema.properties['args']).toBeDefined();
    expect(tools[0].tool.inputSchema.properties['args'].type).toBe('object');
  });

  it('按领域过滤转换', () => {
    const registry = new SkillRegistry();
    registry.register(makeSkill({ id: 'B-003', domain: 'glm-ocr' }));
    registry.register(makeSkill({ id: 'B-004', domain: 'marketplace' }));
    const bridge = new SkillMCPBridge(registry, new SkillExecutor(registry));

    const glmTools = bridge.toMCPToolsByDomain('glm-ocr');
    expect(glmTools).toHaveLength(1);
    expect(glmTools[0].tool.name).toBe('B-003');

    const mpTools = bridge.toMCPToolsByDomain('marketplace');
    expect(mpTools).toHaveLength(1);
    expect(mpTools[0].tool.name).toBe('B-004');
  });

  it('所有工具标记 source 为 skill-registry', () => {
    const registry = new SkillRegistry();
    registry.register(makeSkill());
    const bridge = new SkillMCPBridge(registry, new SkillExecutor(registry));

    for (const t of bridge.toMCPTools()) {
      expect(t.source).toBe('skill-registry');
      expect(t.sourceId).toBeDefined();
    }
  });

  it('空注册表返回空工具列表', () => {
    const registry = new SkillRegistry();
    const bridge = new SkillMCPBridge(registry, new SkillExecutor(registry));

    expect(bridge.toMCPTools()).toHaveLength(0);
    expect(bridge.toMCPToolsByDomain('marketplace')).toHaveLength(0);
  });

  it('带 enum 和 default 的 input 正确转换', () => {
    const registry = new SkillRegistry();
    registry.register(
      makeSkill({
        id: 'B-005',
        inputs: [
          {
            name: 'mode',
            type: 'string',
            description: '处理模式',
            required: true,
            enum: ['fast', 'deep', 'balanced'],
            default: 'fast',
          },
        ],
      })
    );
    const bridge = new SkillMCPBridge(registry, new SkillExecutor(registry));

    const prop = bridge.toMCPTools()[0].tool.inputSchema.properties['mode'];
    expect(prop.enum).toEqual(['fast', 'deep', 'balanced']);
    expect(prop.default).toBe('fast');
  });

  it('多个 Skill 同时转换', () => {
    const registry = new SkillRegistry();
    registry.register(makeSkill({ id: 'B-006' }));
    registry.register(makeSkill({ id: 'B-007' }));
    registry.register(makeSkill({ id: 'B-008' }));
    const bridge = new SkillMCPBridge(registry, new SkillExecutor(registry));

    const tools = bridge.toMCPTools();
    expect(tools).toHaveLength(3);
    const names = tools.map(t => t.tool.name).sort();
    expect(names).toEqual(['B-006', 'B-007', 'B-008']);
  });
});