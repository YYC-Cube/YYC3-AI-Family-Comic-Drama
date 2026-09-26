/**
 * @description YYC³ 统一 MCP 运行时 — 入口
 * @module @yyc3/mcp-runtime
 *
 * 整合了原有的 4 套 MCP 实现：
 * - mcp/common/mcpGateway.ts → 统一网关接口
 * - mcp-server/ → 统一服务器
 * - mcp-client/ → 统一客户端
 * - claude-prompts-mcp/ → Prompt 引擎
 *
 * 新增桥接能力：
 * - Skill Registry → MCP Tool (SkillMCPBridge)
 * - CowAgent Tools → MCP Tool (CowAgentMCPBridge)
 *
 * 使用方式：
 * ```ts
 * import { UnifiedMCPRuntime } from '@yyc3/mcp-runtime';
 * import { globalSkillRegistry, SkillLoader, SkillExecutor } from '@yyc3/skill-registry';
 *
 * // 初始化统一运行时
 * const runtime = new UnifiedMCPRuntime({
 *   skillRegistry: globalSkillRegistry,
 *   skillExecutor: new SkillExecutor(globalSkillRegistry),
 *   cowagentRoot: './CowAgent',
 * });
 *
 * await runtime.initialize();
 *
 * // 获取所有可用工具（含 Skill + CowAgent + 内置）
 * const tools = runtime.listAllTools();
 *
 * // 执行工具调用（自动路由到正确的来源）
 * const result = await runtime.callTool('GLM-OCR-001', { image: 'test.png' });
 * ```
 */

// 类型导出
export type {
  MCPTool,
  MCPToolProperty,
  MCPToolCall,
  MCPToolResult,
  MCPContent,
  MCPResource,
  MCPPrompt,
  MCPServerDescriptor,
  MCPServerInfo,
  GatewayDto,
  ToolSource,
  SourcedTool,
} from './types.js';

// Skill 桥接
export { SkillMCPBridge } from './bridge.js';

// CowAgent 桥接
export { CowAgentMCPBridge, COWAGENT_TOOLS } from './cowagent-bridge.js';
export type { CowAgentBridgeConfig } from './cowagent-bridge.js';

// 统一运行时
export { UnifiedMCPRuntime } from './runtime.js';
export type { RuntimeConfig, RuntimeEventMap } from './runtime.js';

// 独立 HTTP 服务（P1-2：默认回环绑定 + fail-closed 认证 + 限流/安全头）
export { createMcpServerApp } from './server-app.js';
export type { McpServerOptions } from './server-app.js';
export {
  apiKeysFromEnv,
  resolveClientIp,
  trustedProxyHopsFromEnv,
  mcpApiKeyAuth,
  mcpSecurityHeaders,
  mcpBodySizeLimit,
  mcpRateLimiter,
} from './server-security.js';
