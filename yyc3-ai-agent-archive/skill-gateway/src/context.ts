/**
 * Skill Gateway — Hono 上下文类型扩展
 */
import type { SkillRegistry, SkillLoader, SkillExecutor } from '@yyc3/skill-registry';
import type { UnifiedMCPRuntime } from '@yyc3/mcp-runtime';
import type { SkillGateway } from './gateway.js';
import type { GatewayConfig } from './types.js';

declare module 'hono' {
  interface ContextVariableMap {
    registry: SkillRegistry;
    loader: SkillLoader;
    executor: SkillExecutor;
    mcpRuntime: UnifiedMCPRuntime | undefined;
    gateway: SkillGateway | undefined;
    gatewayConfig: Required<GatewayConfig>;
  }
}