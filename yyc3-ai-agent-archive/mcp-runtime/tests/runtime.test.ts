/**
 * UnifiedMCPRuntime 运行时与 SkillMCPBridge 桥接测试
 */
import { describe, it, expect } from 'vitest';
import { UnifiedMCPRuntime } from '../src/runtime.js';
import { SkillMCPBridge } from '../src/bridge.js';
import type { SourcedTool, MCPToolResult } from '../src/types.js';
import {
  SkillRegistry,
  SkillExecutor,
} from '@yyc3/skill-registry';
import type { UnifiedSkill } from '@yyc3/skill-registry';

function makeSkill(overrides: Partial<UnifiedSkill> = {}): UnifiedSkill {
  return {
    id: 'RT-001',
    name: '运行时技能',
    description: '用于运行时测试的技能',
    domain: 'marketplace',
    type: 'hybrid',
    runtime: 'native',
    entry: '',
    inputs: [
      { name: 'query', type: 'string', description: '查询文本', required: true },
    ],
    outputs: [{ type: 'text' }],
    ...overrides,
  };
}

describe('UnifiedMCPRuntime', () => {
  it('空配置初始化成功', async () => {
    const runtime = new UnifiedMCPRuntime();
    await runtime.initialize();
    expect(runtime.listAllTools()).toHaveLength(0);
    expect(runtime.getStats().totalTools).toBe(0);
  });

  it('Skill 桥接后工具可列出', async () => {
    const registry = new SkillRegistry();
    registry.register(makeSkill());
    const runtime = new UnifiedMCPRuntime({
      skillRegistry: registry,
      skillExecutor: new SkillExecutor(registry),
      enableCowAgent: false,
    });
    await runtime.initialize();

    const tools = runtime.listAllTools();
    expect(tools).toHaveLength(1);
    expect(tools[0].name).toBe('RT-001');
    expect(tools[0].inputSchema.properties['query']).toBeDefined();
    expect(tools[0].inputSchema.required).toContain('query');
  });

  it('callTool 自动路由到 Skill 桥接并执行成功', async () => {
    const registry = new SkillRegistry();
    registry.register(makeSkill());
    const runtime = new UnifiedMCPRuntime({
      skillRegistry: registry,
      skillExecutor: new SkillExecutor(registry),
      enableCowAgent: false,
    });
    await runtime.initialize();

    const result = await runtime.callTool('RT-001', { query: 'hello' });
    expect(result.isError).toBeFalsy();
    expect(result.content[0].type).toBe('text');
  });

  it('调用不存在的工具返回 isError', async () => {
    const runtime = new UnifiedMCPRuntime();
    await runtime.initialize();
    const result = await runtime.callTool('no-such-tool', {});
    expect(result.isError).toBe(true);
    expect(result.content[0].text).toContain('not found');
  });

  it('自定义工具注册与执行', async () => {
    const custom: SourcedTool = {
      tool: {
        name: 'my_custom_tool',
        description: '自定义工具',
        inputSchema: { type: 'object', properties: {} },
      },
      source: 'custom',
      sourceId: 'my_custom_tool',
    };
    const runtime = new UnifiedMCPRuntime({
      customTools: [custom],
      customExecutor: async call => ({
        id: call.id,
        content: [{ type: 'text', text: `executed:${call.name}` }],
      }),
    });
    await runtime.initialize();

    expect(runtime.listToolsBySource('custom')).toHaveLength(1);
    const result = await runtime.callTool('my_custom_tool', {});
    expect(result.content[0].text).toBe('executed:my_custom_tool');
  });

  it('运行时事件：注册/调用/成功/注销', async () => {
    const events: string[] = [];
    const registry = new SkillRegistry();
    registry.register(makeSkill());
    const runtime = new UnifiedMCPRuntime({
      skillRegistry: registry,
      skillExecutor: new SkillExecutor(registry),
      enableCowAgent: false,
    });
    runtime.on('runtime:initialized', ({ totalTools }) =>
      events.push(`init:${totalTools}`)
    );
    runtime.on('tool:called', ({ name }) => events.push(`called:${name}`));
    runtime.on('tool:succeeded', ({ name }) => events.push(`ok:${name}`));

    await runtime.initialize();
    await runtime.callTool('RT-001', {});

    expect(events).toContain('init:1');
    expect(events).toContain('called:RT-001');
    expect(events).toContain('ok:RT-001');

    // 动态注册与注销
    const regEvents: string[] = [];
    runtime.on('tool:registered', ({ name }) => regEvents.push(`+${name}`));
    runtime.on('tool:unregistered', ({ name }) => regEvents.push(`-${name}`));
    runtime.registerTool({
      tool: { name: 'extra', description: '额外工具', inputSchema: { type: 'object', properties: {} } },
      source: 'custom',
      sourceId: 'extra',
    });
    expect(runtime.unregisterTool('extra')).toBe(true);
    expect(runtime.unregisterTool('extra')).toBe(false);
    expect(regEvents).toEqual(['+extra', '-extra']);
  });

  it('失败调用发出 tool:failed 事件', async () => {
    const failures: string[] = [];
    const runtime = new UnifiedMCPRuntime();
    await runtime.initialize();
    runtime.on('tool:failed', ({ error }) => failures.push(error));

    await runtime.callTool('missing', {});
    expect(failures).toHaveLength(0); // 不存在的工具不进入执行流程，不触发 failed
  });

  it('来源桥接缺失时返回 No executor 错误（skill-registry / cowagent / custom）', async () => {
    const runtime = new UnifiedMCPRuntime();
    await runtime.initialize();
    runtime.registerTool({
      tool: { name: 'orphan_skill', description: '', inputSchema: { type: 'object', properties: {} } },
      source: 'skill-registry',
      sourceId: 'orphan_skill',
    });
    runtime.registerTool({
      tool: { name: 'orphan_cow', description: '', inputSchema: { type: 'object', properties: {} } },
      source: 'cowagent',
      sourceId: 'orphan_cow',
    });

    const r1 = await runtime.callTool('orphan_skill', {});
    expect(r1.isError).toBe(true);
    expect(r1.content[0].text).toContain('No executor available');
    expect(r1.content[0].text).toContain('skill-registry');

    const r2 = await runtime.callTool('orphan_cow', {});
    expect(r2.isError).toBe(true);
    expect(r2.content[0].text).toContain('cowagent');
  });

  it('custom 来源未配置执行器时返回 No executor 错误', async () => {
    const runtime = new UnifiedMCPRuntime({
      customTools: [
        {
          tool: { name: 'c_noexec', description: '', inputSchema: { type: 'object', properties: {} } },
          source: 'custom',
          sourceId: 'c_noexec',
        },
      ],
    });
    await runtime.initialize();
    const result = await runtime.callTool('c_noexec', {});
    expect(result.isError).toBe(true);
    expect(result.content[0].text).toContain('source: custom');
  });

  it('执行器返回失败结果时发出 tool:failed 事件', async () => {
    const failures: string[] = [];
    const runtime = new UnifiedMCPRuntime({
      customTools: [
        {
          tool: { name: 'c_fail', description: '', inputSchema: { type: 'object', properties: {} } },
          source: 'custom',
          sourceId: 'c_fail',
        },
      ],
      customExecutor: async call => ({
        id: call.id,
        content: [{ type: 'text', text: 'boom' }],
        isError: true,
      }),
    });
    await runtime.initialize();
    runtime.on('tool:failed', ({ error }) => failures.push(error));

    const result = await runtime.callTool('c_fail', {});
    expect(result.isError).toBe(true);
    expect(failures).toEqual(['boom']);
  });

  it('统计按来源聚合', async () => {
    const registry = new SkillRegistry();
    registry.register(makeSkill({ id: 'S-A' }));
    registry.register(makeSkill({ id: 'S-B' }));
    const runtime = new UnifiedMCPRuntime({
      skillRegistry: registry,
      skillExecutor: new SkillExecutor(registry),
      enableCowAgent: false,
      customTools: [
        {
          tool: { name: 'c1', description: '', inputSchema: { type: 'object', properties: {} } },
          source: 'custom',
          sourceId: 'c1',
        },
      ],
    });
    await runtime.initialize();

    const stats = runtime.getStats();
    expect(stats.totalTools).toBe(3);
    expect(stats.bySource['skill-registry']).toBe(2);
    expect(stats.bySource['custom']).toBe(1);
  });
});

describe('SkillMCPBridge', () => {
  it('按领域过滤转换', () => {
    const registry = new SkillRegistry();
    registry.register(makeSkill({ id: 'B-1', domain: 'marketplace' }));
    registry.register(makeSkill({ id: 'B-2', domain: 'b2b' }));
    const bridge = new SkillMCPBridge(registry, new SkillExecutor(registry));

    const tools = bridge.toMCPToolsByDomain('b2b');
    expect(tools).toHaveLength(1);
    expect(tools[0].sourceId).toBe('B-2');
  });

  it('无 inputs 的 Skill 提供默认 args 参数', () => {
    const registry = new SkillRegistry();
    registry.register(makeSkill({ id: 'NOIN', inputs: [] }));
    const bridge = new SkillMCPBridge(registry, new SkillExecutor(registry));

    const tools = bridge.toMCPTools();
    expect(tools[0].tool.inputSchema.properties['args']).toBeDefined();
  });

  it('handleToolCall 返回文本内容', async () => {
    const registry = new SkillRegistry();
    registry.register(makeSkill());
    const bridge = new SkillMCPBridge(registry, new SkillExecutor(registry));

    const result: MCPToolResult = await bridge.handleToolCall({
      id: 'call-1',
      name: 'RT-001',
      arguments: { query: 'test' },
    });
    expect(result.id).toBe('call-1');
    expect(result.isError).toBeFalsy();
    expect(typeof result.content[0].text).toBe('string');
  });
});
