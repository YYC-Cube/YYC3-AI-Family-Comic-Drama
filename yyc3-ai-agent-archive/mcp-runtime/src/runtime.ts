/**
 * @description YYC³ 统一 MCP 运行时核心
 * @module @yyc3/mcp-runtime/runtime
 *
 * 统一调度所有工具来源（Skill Registry / CowAgent / 内置），
 * 提供单一入口的 tools/list 和 tools/call 接口。
 */

import type { SkillExecutor, SkillRegistry } from '@yyc3/skill-registry';
import { EventEmitter } from 'eventemitter3';
import { randomBytes } from 'node:crypto';
import { SkillMCPBridge } from './bridge.js';
import { CowAgentMCPBridge } from './cowagent-bridge.js';
import type { MCPTool, MCPToolCall, MCPToolResult, SourcedTool } from './types.js';

/** 生成调用 ID：crypto 随机（同毫秒并发不碰撞，P2） */
function generateCallId(): string {
  return `call-${randomBytes(8).toString('hex')}`;
}

// ==================== 运行时事件 ====================

export interface RuntimeEventMap {
  'tool:registered': { name: string; source: SourcedTool['source'] };
  'tool:unregistered': { name: string };
  'tool:called': { name: string; callId: string };
  'tool:succeeded': { name: string; callId: string };
  'tool:failed': { name: string; callId: string; error: string };
  'runtime:initialized': { totalTools: number };
}

export interface RuntimeConfig {
  skillRegistry?: SkillRegistry;
  skillExecutor?: SkillExecutor;
  cowagentRoot?: string;
  pythonPath?: string;
  /** 是否启用 CowAgent 工具桥接 */
  enableCowAgent?: boolean;
  /** 是否启用 Skill 注册中心桥接 */
  enableSkillBridge?: boolean;
  /** 自定义工具注册 */
  customTools?: SourcedTool[];
  /** 自定义工具执行器 */
  customExecutor?: (call: MCPToolCall) => Promise<MCPToolResult>;
}

export class UnifiedMCPRuntime extends EventEmitter<RuntimeEventMap> {
  private skillBridge: SkillMCPBridge | null = null;
  private cowagentBridge: CowAgentMCPBridge | null = null;
  private toolIndex: Map<string, SourcedTool> = new Map();
  private config: RuntimeConfig;

  constructor(config: RuntimeConfig = {}) {
    super();
    this.config = {
      enableSkillBridge: true,
      enableCowAgent: true,
      ...config,
    };
  }

  /**
   * 初始化运行时
   */
  async initialize(): Promise<void> {
    // 初始化 Skill 桥接
    if (this.config.enableSkillBridge && this.config.skillRegistry && this.config.skillExecutor) {
      this.skillBridge = new SkillMCPBridge(
        this.config.skillRegistry,
        this.config.skillExecutor
      );
      this.indexTools(this.skillBridge.toMCPTools());
    }

    // 初始化 CowAgent 桥接
    if (this.config.enableCowAgent && this.config.cowagentRoot) {
      this.cowagentBridge = new CowAgentMCPBridge({
        cowagentRoot: this.config.cowagentRoot,
        pythonPath: this.config.pythonPath,
      });
      this.indexTools(this.cowagentBridge.toMCPTools());
    }

    // 注册自定义工具
    if (this.config.customTools) {
      this.indexTools(this.config.customTools);
    }

    this.emit('runtime:initialized', { totalTools: this.toolIndex.size });
  }

  /**
   * 索引工具
   */
  private indexTools(tools: SourcedTool[]): void {
    for (const sourced of tools) {
      this.toolIndex.set(sourced.tool.name, sourced);
    }
  }

  /**
   * 列出所有工具
   */
  listAllTools(): MCPTool[] {
    return Array.from(this.toolIndex.values()).map(s => s.tool);
  }

  /**
   * 列出所有工具（含来源信息）
   */
  listAllSourcedTools(): SourcedTool[] {
    return Array.from(this.toolIndex.values());
  }

  /**
   * 按来源过滤工具
   */
  listToolsBySource(source: SourcedTool['source']): MCPTool[] {
    return Array.from(this.toolIndex.values())
      .filter(s => s.source === source)
      .map(s => s.tool);
  }

  /**
   * 获取工具详情
   */
  getTool(name: string): MCPTool | undefined {
    return this.toolIndex.get(name)?.tool;
  }

  /**
   * 统一工具调用入口（自动路由到正确的来源）
   */
  async callTool(name: string, args: Record<string, unknown>): Promise<MCPToolResult> {
    const sourced = this.toolIndex.get(name);
    if (!sourced) {
      return {
        id: generateCallId(),
        content: [{ type: 'text', text: `Tool not found: ${name}` }],
        isError: true,
      };
    }

    const call: MCPToolCall = {
      id: generateCallId(),
      name,
      arguments: args,
    };

    this.emit('tool:called', { name, callId: call.id });

    let result: MCPToolResult;
    switch (sourced.source) {
      case 'skill-registry':
        if (this.skillBridge) {
          result = await this.skillBridge.handleToolCall(call);
          this.emitToolResult(name, call.id, result);
          return result;
        }
        break;

      case 'cowagent':
        if (this.cowagentBridge) {
          result = await this.cowagentBridge.handleToolCall(call);
          this.emitToolResult(name, call.id, result);
          return result;
        }
        break;

      case 'custom':
        if (this.config.customExecutor) {
          result = await this.config.customExecutor(call);
          this.emitToolResult(name, call.id, result);
          return result;
        }
        break;
    }

    result = {
      id: call.id,
      content: [{ type: 'text', text: `No executor available for tool: ${name} (source: ${sourced.source})` }],
      isError: true,
    };
    this.emitToolResult(name, call.id, result);
    return result;
  }

  /**
   * 根据执行结果发出成功/失败事件
   */
  private emitToolResult(name: string, callId: string, result: MCPToolResult): void {
    if (result.isError) {
      const text = result.content.find(c => c.type === 'text')?.text ?? 'unknown error';
      this.emit('tool:failed', { name, callId, error: text });
    } else {
      this.emit('tool:succeeded', { name, callId });
    }
  }

  /**
   * 注册自定义工具
   */
  registerTool(sourced: SourcedTool): void {
    this.toolIndex.set(sourced.tool.name, sourced);
    this.emit('tool:registered', {
      name: sourced.tool.name,
      source: sourced.source,
    });
  }

  /**
   * 注销工具
   */
  unregisterTool(name: string): boolean {
    const removed = this.toolIndex.delete(name);
    if (removed) {
      this.emit('tool:unregistered', { name });
    }
    return removed;
  }

  /**
   * 获取运行时统计
   */
  getStats(): {
    totalTools: number;
    bySource: Record<string, number>;
  } {
    const bySource: Record<string, number> = {};
    for (const [, sourced] of this.toolIndex) {
      bySource[sourced.source] = (bySource[sourced.source] ?? 0) + 1;
    }
    return {
      totalTools: this.toolIndex.size,
      bySource,
    };
  }
}
