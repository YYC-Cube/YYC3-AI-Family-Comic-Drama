/**
 * @description YYC³ Skill → MCP Tool 桥接器
 * @module @yyc3/mcp-runtime/bridge
 *
 * 将统一 Skill 注册中心中的 Skill 转换为 MCP Tool，
 * 实现"一次注册，处处可用"的能力暴露。
 */

import type {
  MCPTool,
  MCPToolCall,
  MCPToolResult,
  SourcedTool,
} from './types.js';
import type {
  SkillRegistry,
  SkillExecutor,
  UnifiedSkill,
} from '@yyc3/skill-registry';

export class SkillMCPBridge {
  constructor(
    private registry: SkillRegistry,
    private executor: SkillExecutor
  ) {}

  /**
   * 将所有 Skill 转换为 MCP Tool
   */
  toMCPTools(): SourcedTool[] {
    const skills = this.registry.getAll();
    return skills.map(skill => ({
      tool: this.skillToMCPTool(skill),
      source: 'skill-registry' as const,
      sourceId: skill.id,
    }));
  }

  /**
   * 按领域过滤并转换为 MCP Tool
   */
  toMCPToolsByDomain(domain: string): SourcedTool[] {
    const skills = this.registry.search({ domain: domain as any });
    return skills.map(skill => ({
      tool: this.skillToMCPTool(skill),
      source: 'skill-registry' as const,
      sourceId: skill.id,
    }));
  }

  /**
   * 将单个 Skill 转换为 MCP Tool
   */
  private skillToMCPTool(skill: UnifiedSkill): MCPTool {
    const properties: Record<string, any> = {};

    for (const input of skill.inputs) {
      properties[input.name] = {
        type: input.type,
        description: input.description,
        enum: input.enum,
        default: input.default,
      };
    }

    // 如果 Skill 没有定义 inputs，提供默认参数
    if (Object.keys(properties).length === 0) {
      properties['args'] = {
        type: 'object',
        description: 'Skill execution arguments (JSON)',
      };
    }

    return {
      name: skill.id,
      description: skill.description,
      inputSchema: {
        type: 'object',
        properties,
        required: skill.inputs
          .filter(i => i.required)
          .map(i => i.name),
      },
    };
  }

  /**
   * 通过 MCP Tool 调用接口执行 Skill
   */
  async handleToolCall(call: MCPToolCall): Promise<MCPToolResult> {
    const result = await this.executor.execute(call.name, call.arguments, {
      callId: call.id,
    });

    return {
      id: call.id,
      content: [
        {
          type: 'text',
          text: typeof result.output === 'string'
            ? result.output
            : JSON.stringify(result.output),
        },
      ],
      isError: !result.success,
    };
  }
}
