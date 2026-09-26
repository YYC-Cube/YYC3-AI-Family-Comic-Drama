/**
 * MCP Runtime — 独立服务入口
 *
 * 用途：容器化部署（Dockerfile stage: mcp-runtime）
 * 以 Hono + @hono/node-server 暴露 MCP tools/list 与 tools/call HTTP 接口
 *
 * 安全默认（P1-2）：
 * - 默认绑定 127.0.0.1（回环），仅经 MCP_HOST/HOST 显式覆盖才对外监听；
 *   容器内由 compose 显式设 MCP_HOST=0.0.0.0（网络命名空间隔离 + 端口仅发布回环）
 * - 除 /health 外全部端点要求 API Key（YYC3_API_KEYS），未配置即 fail-closed 503
 */
import { serve } from '@hono/node-server';
import { UnifiedMCPRuntime } from './runtime.js';
import { createMcpServerApp } from './server-app.js';
import { apiKeysFromEnv, trustedProxyHopsFromEnv } from './server-security.js';

const port = Number(process.env.PORT ?? 3031);
// 默认回环：裸机直接运行不对局域网暴露；compose/K8s 需显式 MCP_HOST=0.0.0.0
const hostname = process.env.MCP_HOST ?? process.env.HOST ?? '127.0.0.1';

const runtime = new UnifiedMCPRuntime({
  enableSkillBridge: false, // 独立部署时不桥接 Skill Registry（由 Gateway 侧组装）
  enableCowAgent: false,
});
await runtime.initialize();

const app = createMcpServerApp(runtime, {
  apiKeys: apiKeysFromEnv(process.env.YYC3_API_KEYS),
  trustedProxyHops: trustedProxyHopsFromEnv(process.env.YYC3_TRUSTED_PROXY_HOPS),
});

serve({ fetch: app.fetch, port, hostname });
console.warn(`[MCPRuntime] 启动于 http://${hostname}:${port}（/api 需 API Key 认证）`);

process.on('SIGTERM', () => process.exit(0));
process.on('SIGINT', () => process.exit(0));
