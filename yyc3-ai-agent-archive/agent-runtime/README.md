# @yyc3/agent-runtime

> Agent 智能体运行时 —— 生命周期 / 对话 / 工具调用 / Family 协议

![Version](https://img.shields.io/badge/version-1.2.0-00d4ff?style=flat-square)
![Tests](https://img.shields.io/badge/tests-65%20passing-00FF88?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-FF6600?style=flat-square)

## 定位

运行时层服务（默认端口 **3032**）：`AgentRuntime` 管理 Agent 生命周期
（6 态状态机）、消息历史（`maxMessages` 裁剪）、内存 KV、Family Message 协议，
经 `FileStore` 写穿持久化实现重启恢复。内置 8 位 AI Family 档案
（`family-registry.ts`，含 systemPrompt / collaborators）。

## 核心机制

| 机制 | 实现 |
| ---- | ---- |
| 写穿持久化 | fire-and-forget + `pendingWrites` 集合 + `flushPending()`（优雅停机/测试确定性） |
| 重启恢复 | `restore()` 对损坏数据跳过而非崩溃 |
| 历史裁剪 | 单 agent 消息历史上限，防内存无界 |
| 安全中间件 | 与 mcp-runtime 同构收敛（同环境变量 / 同错误码 / fail-closed） |

## 使用

```ts
import { AgentRuntime } from '@yyc3/agent-runtime';

const rt = new AgentRuntime({ familyRegistry });
const agent = await rt.create({ profileId: 'yanyu' });
await rt.sendMessage(agent.id, { role: 'user', content: 'hi' });
await rt.flushPending();   // 停机前确保落盘
```

```bash
AGENT_STORE_FILE=./data/agents.json pnpm --filter @yyc3/agent-runtime start   # 127.0.0.1:3032
```

## 端点（需认证，`/health` 豁免）

| 方法 | 路径 |
| ---- | ---- |
| GET | `/api/v1/agents` |
| POST | `/api/v1/agents` |
| POST | `/api/v1/agents/:id/messages` |
| GET | `/api/v1/family/profiles` |

完整 API 见 [`docs/developers/API.md`](../../docs/developers/API.md)。

## 测试

```bash
pnpm --filter @yyc3/agent-runtime test     # 65 用例（生命周期 42 + 服务 23，含 FileStore 写穿恢复、chunked 413、伪造 XFF）
```

## 许可证

MIT © 2026 YanYuCloudCube Team
