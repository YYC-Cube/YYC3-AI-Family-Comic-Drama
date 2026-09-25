---
file: YYC3-开发者-快速入门.md
description: YYC³ AI-Dev 开发者快速入门指南 — 环境搭建、项目认知、首个插件开发全流程
author: YanYuCloudCube Team <admin@0379.email>
version: v1.0.0
created: 2026-07-16
updated: 2026-07-16
status: stable
tags: [guide],[getting-started],[onboarding],[development]
category: guide
language: zh-CN
audience: developers
complexity: basic
project: yyc3-ai-dev
phase: development
---

<div align="center">

> **_YanYuCloudCube_**
> _言启象限 | 语枢未来_
> **_Words Initiate Quadrants, Language Serves as Core for Future_**
> _万象归元于云枢 | 深栈智启新纪元_
> **_All things converge in cloud pivot; Deep stacks ignite a new era of intelligence_**

---

</div>

# YYC³ AI-Dev 开发者快速入门指南

## 一、环境准备

### 1.1 必备工具

| 工具 | 版本要求 | 说明 |
|------|----------|------|
| Node.js | ≥ 20.0.0 | 推荐 LTS 版本 |
| pnpm | ≥ 9.0.0 | 包管理器（禁止使用 npm/yarn） |
| Git | ≥ 2.40 | 版本控制 |
| VS Code / Trae IDE | 最新版 | 推荐编辑器 |

### 1.2 安装步骤

```bash
# 1. 克隆项目
git clone <repo-url> YYC3-CloudPivot-Intelli-Matrix-Dev
cd YYC3-CloudPivot-Intelli-Matrix-Dev

# 2. 安装依赖（使用 pnpm）
pnpm install

# 3. 验证环境
npx tsc --noEmit          # TypeScript 零错误
npx vitest run             # 全量测试通过
```

### 1.3 开发服务器启动

```bash
# AI Family 独立应用（已配置 vite）
cd apps/standalone-ai-family
pnpm install
pnpm dev                    # → http://localhost:3218

# 合并版应用
cd apps/full
pnpm dev
```

---

## 二、项目结构认知

### 2.1 Monorepo 总览

```
YYC3-CloudPivot-Intelli-Matrix-Dev/
├── packages/               ← 所有插件包
│   ├── shell/              ← 系统外壳（核心，勿随意修改）
│   ├── plugin-ai-family/   ← AI Family 中枢系统
│   ├── plugin-target/      ← 目标量化引擎
│   ├── plugin-cost/        ← 成本盈亏引擎
│   ├── plugin-marketing/   ← 节日营销引擎
│   ├── plugin-prompt/      ← AI 提示词库
│   ├── plugin-monitor/     ← 监控中心
│   ├── plugin-ops/         ← 运维管理
│   ├── plugin-ai/          ← AI 智能
│   ├── plugin-dev/         ← 开发工具
│   └── plugin-admin/       ← 系统管理
├── apps/                   ← 独立应用入口
│   ├── full/               ← 合并版
│   └── standalone-*/       ← 各系统独立版
├── docs/                   ← 项目文档
│   ├── YYC3-团队通用-标准规范/  ← 团队标准（只读参考）
│   ├── YYC3-项目架构-设计总纲.md
│   ├── YYC3-任务看板-Phase0-1.md
│   └── YYC3-全链路智能应用-阶段节点设计落地大纲.md
├── vitest.config.ts        ← 测试配置
├── tsconfig.json           ← TypeScript 配置
└── package.json            ← 工作区根配置
```

### 2.2 核心概念速览

| 概念 | 说明 | 文件参考 |
|------|------|----------|
| **Shell** | 系统外壳，提供注册/路由/存储/事件总线 | `packages/shell/src/` |
| **SystemRegistration** | 每个插件包的注册接口 | `packages/shell/src/types.ts` |
| **EventBus** | 跨插件包通信总线 | `packages/shell/src/event-bus.ts` |
| **AI Family** | 8位家人中枢系统 | `packages/plugin-ai-family/` |
| **双主题** | THEME_MODERN + THEME_ANCIENT | `packages/shell/src/theme.ts` |

---

## 三、五分钟创建你的第一个插件

### 3.1 创建包骨架

```bash
mkdir -p packages/plugin-example/src/pages
```

### 3.2 package.json

```json
{
  "name": "@yyc3/plugin-example",
  "version": "1.0.0",
  "description": "示例插件 — 快速入门",
  "main": "src/index.ts",
  "peerDependencies": {
    "react": "^18||^19",
    "lucide-react": "^0.500",
    "@yyc3/shell": "workspace:*"
  }
}
```

### 3.3 注册文件

```typescript
// src/register.ts
import { Sparkles } from "lucide-react";
import type { SystemRegistration } from "@yyc3/shell";

export function register(): SystemRegistration {
  return {
    id: "example",
    name: "示例插件",
    description: "快速入门示例",
    icon: Sparkles,
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

### 3.4 入口文件

```typescript
// src/index.ts
export { register } from "./register";
```

### 3.5 注册到 vitest 别名

在 `vitest.config.ts` 的 `resolve.alias` 中添加：

```typescript
"@yyc3/plugin-example": path.resolve(__dirname, "packages/plugin-example/src"),
```

### 3.6 验证

```bash
npx tsc --noEmit   # 零错误
```

---

## 四、开发红线

| 红线 | 说明 |
|------|------|
| ❌ 禁止直接 import 其他插件包的内部组件 | 使用 EventBus 通信 |
| ❌ 禁止直接读写其他插件包的 localStorage | 使用各自 `createSystemStorage(id)` |
| ❌ 禁止修改 `packages/shell/src/types.ts` 的接口定义 | 通过扩展而非修改 |
| ❌ 禁止使用 npm/yarn 安装依赖 | 统一使用 pnpm |
| ❌ 禁止提交 TypeScript 有错误的代码 | `tsc --noEmit` 必须通过 |
| ❌ 禁止提交测试未通过的代码 | `vitest run` 必须全绿 |

---

## 五、下一步

| 文档 | 说明 |
|------|------|
| [项目架构总纲](./YYC3-开发者-架构总纲.md) | 深入理解 Shell + 插件体系 |
| [插件开发指南](./YYC3-开发者-插件开发指南.md) | 完整插件开发流程 |
| [编码规范手册](./YYC3-开发者-编码规范.md) | 代码标头、命名、风格 |
| [测试策略](./YYC3-开发者-测试策略.md) | 测试编写指南 |

---

## 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| v1.0.0 | 2026-07-16 | 初始版本 | YanYuCloudCube Team |
