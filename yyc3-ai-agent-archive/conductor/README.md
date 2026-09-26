# @yyc3/conductor

> 协同编排引擎 —— DAG 流水线 / 分层并发 / 取消与重试

![Version](https://img.shields.io/badge/version-1.0.1-00d4ff?style=flat-square)
![Tests](https://img.shields.io/badge/tests-14%20passing-00FF88?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-FF6600?style=flat-square)
![Status](https://img.shields.io/badge/status-%F0%9F%94%B4%20%E5%8E%9F%E5%9E%8B-FF3B30?style=flat-square)

## 定位

编排层包：`PipelineBuilder` 负责任务校验 + Kahn 分层拓扑排序 + 环检测；
`Conductor` 按层并发执行（批次内 `Promise.all`），支持 `AbortController` 取消、
任务级超时与指数退避重试。

> 🔴 **原型状态如实说明**：`skillId` 执行分支尚未接通——校验允许、但执行时
> **显式失败**（not implemented），不再假执行；混合定义时 `executor` 优先。
> 与 orchestrator 职责重叠，依赖方向偏离文档约定的整合方案讨论中。
> 生产链路请勿使用 `skillId` 任务（请提供 `executor`）。

## 使用

```ts
import { PipelineBuilder, Conductor } from '@yyc3/conductor';

const pipeline = new PipelineBuilder()
  .task({ id: 'a', executor: async () => 1 })
  .task({ id: 'b', executor: async (ctx) => ctx.results.a + 1, dependsOn: ['a'] })
  .build();                                   // 环检测在此抛出

const conductor = new Conductor({ maxRetries: 2 });
const result = await conductor.run(pipeline, { signal });
// result: 每任务 duration / retries / startedAt / status
```

## 测试

```bash
pnpm --filter @yyc3/conductor test         # 14 用例（拓扑分层 / 环检测 / 重试 / 取消）
```

## 许可证

MIT © 2026 YanYuCloudCube Team
