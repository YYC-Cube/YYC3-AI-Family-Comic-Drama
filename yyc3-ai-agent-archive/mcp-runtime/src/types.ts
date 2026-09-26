/**
 * @description YYC³ 统一 MCP 运行时类型
 * @module @yyc3/mcp-runtime/types
 *
 * 统一了 mcp/ (VS Code 网关接口) + mcp-server/ + mcp-client/ 的类型。
 * 向后兼容现有代码，同时提供统一的对外接口。
 */

// ==================== MCP 协议核心类型 ====================
// 与 mcp-server/src/types.ts 保持兼容

export interface MCPTool {
  name: string;
  description: string;
  inputSchema: {
    type: 'object';
    properties: Record<string, MCPToolProperty>;
    required?: string[];
  };
}

export interface MCPToolProperty {
  type: 'string' | 'number' | 'boolean' | 'object' | 'array';
  description?: string;
  enum?: string[];
  default?: unknown;
  items?: MCPToolProperty;
  properties?: Record<string, MCPToolProperty>;
}

export interface MCPToolCall {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
}

export interface MCPToolResult {
  id: string;
  content: MCPContent[];
  isError?: boolean;
}

export interface MCPContent {
  type: 'text' | 'image' | 'resource';
  text?: string;
  data?: string;
  mimeType?: string;
}

export interface MCPResource {
  uri: string;
  name: string;
  description?: string;
  mimeType?: string;
}

export interface MCPPrompt {
  name: string;
  description?: string;
  arguments?: { name: string; description?: string; required?: boolean }[];
}

// ==================== 网关接口（来自 mcp/common/mcpGateway.ts） ====================

export interface MCPServerDescriptor {
  readonly id: string;
  readonly label: string;
}

export interface MCPServerInfo {
  readonly label: string;
  readonly address: string;
}

export interface GatewayDto {
  readonly servers: readonly MCPServerInfo[];
  readonly gatewayId: string;
}

// ==================== 工具来源标识 ====================

export type ToolSource =
  | 'skill-registry'    // 来自 Skill 注册中心
  | 'cowagent'          // 来自 CowAgent Python 工具
  | 'native'            // 内置工具
  | 'external-mcp'      // 外部 MCP 服务器
  | 'custom';           // 自定义注册

export interface SourcedTool {
  tool: MCPTool;
  source: ToolSource;
  sourceId: string;     // 来源标识（如 skill ID 或 tool name）
}
