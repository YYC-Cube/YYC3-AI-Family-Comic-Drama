# @yyc3/orchestrator

> 智能编排调度器 —— 目标分解 / 多策略调度 / 并行执行

![Version](https://img.shields.io/badge/version-1.0.1-00d4ff?style=flat-square)
![Tests](https://img.shields.io/badge/tests-39%20passing-00FF88?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-FF6600?style=flat-square)
![Status](https://img.shields.io/badge/status-%F0%9F%9F%A1%20%E5%8E%9F%E5%9E%8B%E6%BC%94%E8%BF%9B%E4%B8%AD-FF6600?style=flat-square)

## 定位

编排层包：`目标 → 分解 → 调度 → 并行执行 → 汇总`，事件驱动。
依赖 `@yyc3/agent-runtime`（仅类型，弱耦合）。

## 模块

| 模块 | 职责 | 状态 |
| ---- | ---- | ---- |
| `decomposer.ts` | 规则模板分解；LLM 分解策略为预留接口（未实现，调用即 throw） | 🟡 |
| `scheduler.ts` | 三策略：capability-match / load-balance / round-robin | 🟡 |
| `orchestrator.ts` | 依赖就绪循环 + `maxConcurrency` 批次 + `Promise.allSettled` 自动重试 + 失败依赖传播（stuck 检测） | ✅ |

## 使用

```ts
import { Orchestrator } from '@yyc3/orchestrator';

const orch = new Orchestrator({ scheduler, maxConcurrency: 3 });
const wf = await orch.executeWorkflow({ goal: '整理本周技能资产报告' });
orch.on('workflow:completed', (e) => console.log(e));
```

## 实现状态诚实说明

- 分解结果当前为模板产出的**串行任务链**（并行能力依赖就绪循环，模板不产生并行分叉）
- `sortByPriority` 尚未接入执行主路径（优先级暂为元数据）
- 已知问题与整改计划见[审核报告](../../docs/0379-yyc3-archive-claude-20260926/00-项目现状审核报告.md)

## 测试

```bash
pnpm --filter @yyc3/orchestrator test      # 39 用例（含 ai-family 集成测试）
```

## 许可证

MIT © 2026 YanYuCloudCube Team
