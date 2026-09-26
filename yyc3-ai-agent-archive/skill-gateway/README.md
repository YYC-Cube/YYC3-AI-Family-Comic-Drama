# @yyc3/skill-gateway

> Skill Gateway API —— REST 网关（Hono / Zod / 安全中间件管线）

![Version](https://img.shields.io/badge/version-1.4.0-00d4ff?style=flat-square)
![Tests](https://img.shields.io/badge/tests-63%20passing-00FF88?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-FF6600?style=flat-square)

## 定位

接入层网关（默认端口 **3030**）：对外暴露技能发现 / 执行 / MCP registry 聚合 /
健康检查四组路由，组装完整安全中间件管线。依赖 `@yyc3/skill-registry`
（执行）与 `@yyc3/mcp-runtime`（MCP 桥接）。

## 中间件管线（gateway.ts）

```
cors → securityHeaders → bodySizeLimit(1MB) → rateLimiter(100/min)
    → logger → apiKeyAuth(fail-closed) → onError → DI 上下文 → routes
```

## 安全工程

| 能力 | 实现 |
| ---- | ---- |
| 认证 | Bearer / X-API-Key 双通道；`timingSafeEqual` 长度均衡时序防护；**未配置 key 返回 503 fail-closed** |
| 限流 | Token Bucket 100 req/min，可插拔 Memory/Redis（Lua 原子扣减），Redis 故障降级 + 告警限频 |
| 请求体 | Content-Length 快速拒绝 + chunked 流式字节计数（防头部绕过），413 统一映射 |
| 真实 IP | 受信代理解析模型（`YYC3_TRUSTED_PROXY_HOPS`，默认 0 不信任 XFF） |
| 响应头 | CSP `default-src 'none'` / HSTS / nosniff / 移除 `X-Powered-By`、`Server` |

## 快速开始

```bash
pnpm --filter @yyc3/skill-gateway dev          # 开发
YYC3_API_KEYS=key1,key2 pnpm start             # 生产（必须配置 key，否则 503）
```

```ts
// App 工厂与监听分离，可直接 app.request() 做端到端测试
import { createGatewayApp } from '@yyc3/skill-gateway';
const app = createGatewayApp({ registry, loader });
const res = await app.request('/api/v1/skills');
```

### 主要端点

| 方法 | 路径 | 说明 |
| ---- | ---- | ---- |
| GET | `/api/v1/skills` | 列表 / 分页 / 领域过滤 / 统计 |
| POST | `/api/v1/execute` | 技能执行（Zod 校验 + timeout 钳制 1s–120s） |
| POST | `/api/v1/reload` | 同步重载注册表（sync 语义清除幽灵技能） |
| GET | `/health` `/health/live` `/health/ready` | 三级健康检查（免认证） |
| GET | `/registry.json` 等 | MCP registry 静态聚合（mtime 缓存） |

完整 API 见 [`docs/developers/API.md`](../../docs/developers/API.md)。

## 测试

```bash
pnpm --filter @yyc3/skill-gateway test      # 63 用例（43 端到端 + 20 认证/限流单元，含 XFF 伪造、chunked 绕过对抗）
```

## 许可证

MIT © 2026 YanYuCloudCube Team
