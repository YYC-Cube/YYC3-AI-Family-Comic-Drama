/**
 * Agent Runtime — 独立服务入口
 *
 * 用途：容器化部署（Dockerfile stage: agent-runtime）
 * 以 Hono + @hono/node-server 暴露 Agent 生命周期与对话 HTTP 接口
 *
 * 安全默认（P2 同构收敛，对齐 gateway/mcp-runtime 契约）：
 * - 默认绑定 127.0.0.1（回环），仅经 AGENT_HOST/HOST 显式覆盖才对外监听；
 *   容器内由 compose 显式设 AGENT_HOST=0.0.0.0（网络命名空间隔离 + 端口仅发布回环）
 * - 除 /health 与 / 外全部端点要求 API Key（YYC3_API_KEYS），未配置即 fail-closed 503
 * - 内存限流 + 受信代理跳数（YYC3_TRUSTED_PROXY_HOPS）+ 安全头（含 CSP/HSTS）
 *   + 请求体限制（Content-Length 快速拒绝 + chunked 流式计数）
 * - AGENT_STORE_FILE 配置后智能体状态写穿落盘并在启动时恢复（重启即失 → 可恢复）
 */
import { serve } from '@hono/node-server';
import { AgentRuntime } from './runtime.js';
import { createAgentServerApp } from './server-app.js';
import { apiKeysFromEnv, trustedProxyHopsFromEnv } from './server-security.js';
import { FileStore } from '@yyc3/store';

const port = Number(process.env.PORT ?? 3032);
// 默认回环：裸机直接运行不对局域网暴露；compose/K8s 需显式 AGENT_HOST=0.0.0.0
const hostname = process.env.AGENT_HOST ?? process.env.HOST ?? '127.0.0.1';

// 可选持久化：AGENT_STORE_FILE 指向挂载卷内的 JSON 文件
const storeFile = process.env.AGENT_STORE_FILE;
const store = storeFile ? new FileStore(storeFile) : undefined;

const runtime = new AgentRuntime({ autoHeartbeat: true, store });
if (store) {
  const restored = await runtime.restore();
  console.warn(`[AgentRuntime] 已从 ${storeFile} 恢复 ${restored} 个智能体`);
}

const app = createAgentServerApp(runtime, {
  apiKeys: apiKeysFromEnv(process.env.YYC3_API_KEYS),
  trustedProxyHops: trustedProxyHopsFromEnv(process.env.YYC3_TRUSTED_PROXY_HOPS),
});

serve({ fetch: app.fetch, port, hostname });
console.warn(`[AgentRuntime] 启动于 http://${hostname}:${port}（/api 需 API Key 认证）`);

process.on('SIGTERM', () => process.exit(0));
process.on('SIGINT', () => process.exit(0));
