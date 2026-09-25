---
file: YYC3-开发者-插件开发指南.md
description: YYC³ 插件开发完整指南 — 从骨架创建到注册上线全流程，含 SystemRegistration/EventBus/存储最佳实践
author: YanYuCloudCube Team <admin@0379.email>
version: v1.0.0
created: 2026-07-16
updated: 2026-07-16
status: stable
tags: [guide],[plugin],[development],[system-registration],[event-bus]
category: guide
language: zh-CN
audience: developers
complexity: intermediate
project: yyc3-ai-dev
phase: development
---

<div align="center">

> **_YanYuCloudCube_**
> _言启象角 | 语枢未来_
> **_Words Initiate Quadrants, Language Serves as Core for Future_**
> _万象归元于云枢 | 深栈智启新纪元_
> **_All things converge in cloud pivot; Deep stacks ignite a new era of intelligence_**

---

</div>

# YYC³ 插件开发完整指南

## 一、插件包标准结构

每个插件包必须遵循以下目录结构：

```
packages/plugin-{name}/
├── src/
│   ├── index.ts          ← 包入口（导出 register + 引擎）
│   ├── register.ts       ← SystemRegistration 注册
│   ├── types.ts          ← TypeScript 类型定义（引擎插件）
│   ├── {name}-engine.ts  ← 核心计算引擎（引擎插件）
│   ├── pages/            ← 页面组件
│   │   └── *.tsx
│   ├── components/       ← 私有组件
│   │   └── *.tsx
│   └── data.ts           ← 静态数据
├── {name}.test.ts        ← 测试文件（与 src 同级）
├── package.json
└── README.md
```

### 1.1 两种插件类型

| 类型 | 特征 | 示例 | 是否有引擎 |
|------|------|------|-----------|
| **引擎型** | 有纯函数计算引擎 + 类型定义 | target, cost, marketing, prompt | ✅ |
| **界面型** | 以页面/组件为主，无独立引擎 | monitor, ops, ai, dev, admin | ❌ |

---

## 二、package.json 模板

### 2.1 引擎型插件

```json
{
  "name": "@yyc3/plugin-{name}",
  "version": "1.0.0",
  "description": "插件描述 — 一句话说明",
  "main": "src/index.ts",
  "peerDependencies": {
    "react": "^18||^19",
    "lucide-react": "^0.500",
    "@yyc3/shell": "workspace:*"
  }
}
```

### 2.2 依赖其他插件包

如果需要引用 AI Family 人格数据（如 plugin-prompt）：

```json
{
  "peerDependencies": {
    "react": "^18||^19",
    "lucide-react": "^0.500",
    "@yyc3/shell": "workspace:*",
    "@yyc3/plugin-ai-family": "workspace:*"
  }
}
```

---

## 三、register.ts 标准模板

### 3.1 最小注册

```typescript
import { Globe } from "lucide-react";
import type { SystemRegistration } from "@yyc3/shell";

export function register(): SystemRegistration {
  return {
    id: "example",
    name: "示例插件",
    description: "一句话描述插件功能",
    icon: Globe,
    color: "#00FF88",
    order: 50,
    menuItems: [
      { path: "/example", label: "首页" },
    ],
    routes: [],
    hubCommands: [],
  };
}
```

### 3.2 完整注册（含 Hub 命令）

参考 `packages/plugin-monitor/src/register.ts`：

```typescript
import { Activity } from "lucide-react";
import type { SystemRegistration } from "@yyc3/shell";
import { MONITOR_HUB_COMMANDS } from "./agents";

export function register(): SystemRegistration {
  return {
    id: "monitor",
    name: "监控中心",
    description: "Dashboard 监控中心 · 实时数据可视化",
    icon: Activity,
    color: "#00d4ff",
    order: 50,
    menuItems: [
      { path: "/monitor",       label: "总览" },
      { path: "/monitor/alerts", label: "告警" },
      { path: "/monitor/metrics", label: "指标" },
      { path: "/monitor/logs",   label: "日志" },
    ],
    routes: [/* RouteObject[] */],
    hubCommands: MONITOR_HUB_COMMANDS,
  };
}
```

---

## 四、引擎层开发规范

### 4.1 引擎必须是纯函数

```typescript
// ✅ 正确：纯函数，无副作用，可独立测试
export function calc(params: TargetParams): TargetResult {
  const result = params.baseRevenue * params.cityCoefficient;
  return { annualTarget: Number(result.toFixed(2)) };
}

// ❌ 错误：依赖外部状态、有副作用
let cache = {};
export function calc(params) {
  if (cache[params.id]) return cache[params.id]; // 禁止：引擎不应有缓存副作用
  // ...
}
```

### 4.2 引擎对象模式

将所有计算函数聚合为命名空间对象：

```typescript
export const TargetEngine = {
  calc,
  splitPhases,
  splitMonthly,
  validate,
};
```

### 4.3 类型先行原则

先定义 `types.ts`，再编写引擎：

```typescript
// types.ts
export interface TargetParams { ... }
export interface TargetResult { ... }

// target-engine.ts
import type { TargetParams, TargetResult } from "./types";
export function calc(params: TargetParams): TargetResult { ... }
```

---

## 五、index.ts 导出规范

### 5.1 引擎型插件导出

```typescript
// src/index.ts
export { TargetEngine } from "./target-engine";
export { calc, splitPhases, splitMonthly, validate } from "./target-engine";
export { register } from "./register";
export type { TargetParams, TargetResult, PhaseAllocation } from "./types";
export { CITY_TIER_COEFFICIENTS, STORE_SCALE_COEFFICIENTS } from "./types";
```

### 5.2 导出原则

| 导出内容 | 必须 | 说明 |
|----------|------|------|
| `register` 函数 | ✅ | Shell 注册入口 |
| 引擎对象 + 方法 | 引擎型必须 | 供外部调用 |
| 类型定义 (type) | 引擎型必须 | 供外部类型推断 |
| 常量配置 | 推荐 | 如系数表、默认值 |
| 页面组件 | ❌ | 不应跨包导出 |

---

## 六、事件订阅与发出

### 6.1 插件监听 Shell 事件

```typescript
import { eventBus } from "@yyc3/shell";
import { useEffect } from "react";

function MyPage() {
  useEffect(() => {
    const unsub = eventBus.on("ai:persona-changed", (data) => {
      console.log("家人切换:", data.personaId);
    });
    return unsub; // 自动清理
  }, []);
}
```

### 6.2 插件发出自定义事件

```typescript
eventBus.emit("target:calc-completed", {
  annualTarget: 702,
  multiplier: 1.404,
});
```

### 6.3 事件命名规则

```
{插件id}:{动作-描述}

target:calc-completed
cost:analysis-done
marketing:festival-resolved
monitor:alert-triggered
```

---

## 七、vitest.config.ts 别名注册

每新增一个插件包，必须在根目录 `vitest.config.ts` 添加路径别名：

```typescript
import path from "path";

export default defineConfig({
  resolve: {
    alias: {
      "@yyc3/shell": path.resolve(__dirname, "packages/shell/src"),
      "@yyc3/plugin-target": path.resolve(__dirname, "packages/plugin-target/src"),
      "@yyc3/plugin-cost": path.resolve(__dirname, "packages/plugin-cost/src"),
      // ← 新增插件在此添加
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    include: ["packages/**/*.test.*", "apps/**/*.test.*"],
  },
});
```

---

## 八、FamilySkill 开发（AI Family 技能）

### 8.1 FamilySkill 契约

FamilySkill 是 AI Family 智能体的技能单元，通过 `defineSkill()` 工厂函数创建：

```typescript
import { defineSkill } from "@yyc3/family-skills";

export const mySkill = defineSkill(
  // 1. 配置
  {
    id: "data-cleanse",
    name: "数据清洗",
    description: "清洗并标准化输入数据",
    family: "thinker",              // 归属家人 ID
    version: "1.0.0",
    tags: ["data", "clean"],
  },
  // 2. 执行函数
  async (input: unknown, ctx: SkillContext) => {
    const data = input as Record<string, unknown>[];
    const cleaned = data.filter(row => row.id != null);
    return { cleaned, count: cleaned.length };
  },
  // 3. 可选：验证函数
  async (input: unknown) => Array.isArray(input),
);
```

### 8.2 家人 ID 映射

| 家人 ID | 角色领域 |
|---------|----------|
| `qianhang` | 自然语言导航、意图识别 |
| `thinker` | 数据分析、逻辑推理 |
| `prophet` | 预测建模、趋势分析 |
| `bole` | 个性化推荐、用户画像 |
| `tianshu` | 全局调度、资源编排 |
| `guardian` | 安全检测、威胁响应 |
| `grandmaster` | 代码审查、架构分析 |
| `grace` | 创意生成、多模态创作 |

### 8.3 NVIDIA 技能桥接

`family-skills` 内置 NVIDIA SDK 桥接器，自动从 `docs/skills/` 目录发现 NVIDIA 组件。离线时使用静态 catalog fallback，提供 200+ NVIDIA 技能（NIM / Guardrails / Riva / CUOpt / RAG / TAO / Dynamo / Earth-2）。

---

## 九、插件开发 Checklist

| # | 检查项 | 验证命令 |
|---|--------|----------|
| 1 | package.json 名称格式 `@yyc3/plugin-*` | 目视检查 |
| 2 | register.ts 返回完整的 SystemRegistration | `tsc --noEmit` |
| 3 | index.ts 正确导出 register | `tsc --noEmit` |
| 4 | vitest.config.ts 已添加别名 | 目视检查 |
| 5 | 引擎层为纯函数（引擎型插件） | 代码审查 |
| 6 | 测试文件已编写且全绿 | `vitest run` |
| 7 | TypeScript 零错误 | `tsc --noEmit` |

---

## 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| v1.0.0 | 2026-07-16 | 初始版本 | YanYuCloudCube Team |
| v1.1.0 | 2026-07-24 | 新增 FamilySkill 开发（§八），补全家人 ID 映射表 | YanYuCloudCube Team |
