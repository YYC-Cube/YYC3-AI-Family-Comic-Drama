# @yyc3/mcp-runtime

> 统一 MCP 运行时 —— Skill / CowAgent / 自定义工具统一桥接 + 事件层

![Version](https://img.shields.io/badge/version-1.5.0-00d4ff?style=flat-square)
![Tests](https://img.shields.io/badge/tests-40%20passing-00FF88?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-FF6600?style=flat-square)

## 定位

运行时层服务（默认端口 **3031**）：维护单一 `toolIndex`，把 Skill Registry、
CowAgent（Python）与自定义工具统一为标准 MCP `tools/list` / `tools/call` 入口，
按 `source` 路由执行。依赖 `@yyc3/skill-registry`（不得反向）。

## 架构

```
UnifiedMCPRuntime（runtime.ts）
  ├─ SkillBridge（bridge.ts）        ← @yyc3/skill-registry
  ├─ CowAgentBridge（cowagent-bridge.ts） ← Python 子进程（stdin + JSON 参数）
  └─ customTools                     ← 运行时注入
server.ts + server-app.ts（App 工厂，可直接 app.request() 测试）+ server-security.ts
```

## 安全工程

- 工具名白名单 `^[a-z][a-z0-9_]*$`（防 Python 源码注入）；参数经 stdin + `json.loads`（杜绝命令行注入）
- 子进程单流 1MB 输出上限；stdin EPIPE 吞错防崩溃
- 与 skill-gateway 同构的安全中间件：fail-closed 认证 / `timingSafeEqual` / 1MB 请求体
  + chunked 流式计数 / Token Bucket 限流 / CSP·HSTS 安全头

## 使用

```ts
import { UnifiedMCPRuntime } from '@yyc3/mcp-runtime';

const runtime = new UnifiedMCPRuntime({ registry });
await runtime.indexTools();
const tools = await runtime.listTools();
const out = await runtime.callTool('paper-quick-reader', { input });
```

```bash
pnpm --filter @yyc3/mcp-runtime dev        # http://127.0.0.1:3031（默认仅绑回环）
```

## 测试

```bash
pnpm --filter @yyc3/mcp-runtime test       # 40 用例（fail-closed 三态 / 413 chunked 绕过 / 伪造 XFF 限流 / 安全头矩阵）
```

## 许可证

MIT © 2026 YanYuCloudCube Team
