---
file: YYC3-开发者-架构总纲.md
description: YYC³ AI-Dev 项目架构总纲 — Shell+插件体系、事件总线、存储分层、路由系统的完整设计规范
author: YanYuCloudCube Team <admin@0379.email>
version: v1.0.0
created: 2026-07-16
updated: 2026-07-16
status: stable
tags: [architecture],[design],[shell],[plugin],[event-bus]
category: technical
language: zh-CN
audience: developers
complexity: advanced
project: yyc3-ai-dev
phase: development
design_type: architecture
review_status: approved
---

<div align="center">

> **_YanYuCloudCube_**
> _言启象限 | 语枢未来_
> **_Words Initiate Quadrants, Language Serves as Core for Future_**
> _万象归元于云枢 | 深栈智启新纪元_
> **_All things converge in cloud pivot; Deep stacks ignite a new era of intelligence_**

---

</div>

# YYC³ AI-Dev 项目架构总纲

## 一、架构设计哲学

### 1.1 五高架构映射

| 五高维度 | 架构落地 | 实现方式 |
|----------|----------|----------|
| **高可用** | ErrorBoundary 全覆盖 + 插件隔离 | Shell 层错误边界捕获，单插件崩溃不影响全局 |
| **高性能** | 懒加载路由 + 纯函数引擎 | 引擎层（target/cost/marketing）零 UI 依赖，测试 < 5ms |
| **高安全** | 命名空间隔离 + 类型安全 | localStorage 按插件 ID 分区 + TypeScript strict |
| **高扩展** | SystemRegistration 统一接口 | 新增插件只需实现接口 + 注册到 Shell |
| **高智能** | EventBus 跨系统协同 + AI Family | 8位家人人格驱动 + 多智能体协同 |

### 1.2 五维评估体系

| 维度 | 评估对象 | 度量指标 |
|------|----------|----------|
| 时间维 | 构建速度、测试耗时 | `tsc --noEmit` < 5s, 760+ tests < 1s |
| 空间维 | 包体积、代码组织 | 每插件包独立，引擎/界面分离 |
| 属性维 | 类型安全、测试覆盖 | TS 零错误 + 760+ tests 全绿 |
| 事件维 | 用户交互、系统事件 | EventBus 松耦合事件驱动 |
| 关联维 | 插件依赖、生态连接 | peerDependencies 声明 + workspace 协议 |

---

## 二、分层架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户交互层                                 │
│    WelcomePage · AIAssistantHub · 各系统页面                      │
├─────────────────────────────────────────────────────────────────┤
│                        路由层                                     │
│    React Router · 懒加载 · 系统级路由前缀                          │
├─────────────────────────────────────────────────────────────────┤
│                        Shell 层（核心外壳）                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ 注册中心  │  │ 事件总线  │  │ 存储工厂  │  │ 错误边界  │        │
│  │ Registry │  │ EventBus │  │ Storage  │  │ ErrorBnd │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
├─────────────────────────────────────────────────────────────────┤
│                   AI Family 层（智能体协同）                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │family-core│ │family-skills│ │family-ui │                      │
│  │ 家族宪章  │  │ FamilySkill│ │ 情感交互  │                      │
│  │ 八位家人  │  │ defineSkill│ │ 语音/面板 │                      │
│  │ 五维五高  │  │ NVIDIA桥接 │ │ 双主题    │                      │
│  └──────────┘  └──────────┘  └──────────┘                      │
│  ┌──────────┐                                                    │
│  │family-agents│ 8家人 Agent实例 + 编排器                         │
│  └──────────┘                                                    │
├─────────────────────────────────────────────────────────────────┤
│                    插件层（15个插件包）                            │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐               │
│  │  shell  │ │ai-family│ │ target  │ │  cost   │               │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘               │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│  │marketing│ │ prompt  │ │ monitor │ │   ops   │ │   ai    │  │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘  │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐               │
│  │   dev   │ │  admin  │ │business │ │   llm   │               │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘               │
├─────────────────────────────────────────────────────────────────┤
│                        引擎层（纯函数计算）                        │
│  TargetEngine · CostEngine · FestivalEngine · LunarEngine       │
├─────────────────────────────────────────────────────────────────┤
│                        基础设施层                                  │
│  TypeScript · Vitest · pnpm workspace · Tailwind CSS            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 三、Shell 核心外壳

### 3.1 职责边界

Shell 是整个系统的"操作系统"，负责：

1. **注册管理** — 接收所有插件包的 `SystemRegistration` 并组装侧边栏/路由
2. **事件总线** — 提供跨插件包通信的 `EventBus` 单例
3. **存储工厂** — 提供 `createSystemStorage(id)` 按命名空间隔离存储
4. **错误边界** — `ErrorBoundary` 组件防止单插件崩溃蔓延
5. **主题系统** — `THEME_MODERN` + `THEME_ANCIENT` 双主题

### 3.2 Shell 导出接口

```typescript
// packages/shell/src/index.ts
export { EventBus, eventBus, Events } from "./event-bus";
export { createSystemStorage, storage, StorageKeys } from "./storage";
export { WelcomePage } from "./WelcomePage";
export { AIAssistantHub } from "./AIAssistantHub";
export { ErrorBoundary } from "./ErrorBoundary";
export { getTheme, THEME_MODERN, THEME_ANCIENT } from "./theme";
export type { SystemRegistration, MenuItem, HubCommand } from "./types";
```

### 3.3 禁止修改项

| 文件 | 原因 |
|------|------|
| `shell/src/types.ts` | 接口定义是全系统契约 |
| `shell/src/event-bus.ts` | 事件总线是核心基础设施 |
| `shell/src/index.ts` | 导出接口被所有插件包依赖 |

---

## 四、SystemRegistration 接口

### 4.1 接口定义

```typescript
interface SystemRegistration {
  id: string;                    // 唯一标识，如 "target"
  name: string;                  // 显示名称，如 "目标量化"
  description: string;           // 一句话描述
  icon: React.ElementType;       // lucide-react 图标组件
  color: string;                 // 主题色 HEX，如 "#00FF88"
  order: number;                 // 侧边栏排序权重

  menuItems: MenuItem[];         // 侧边栏菜单项
  routes: RouteObject[];         // React Router 路由配置
  i18n?: Record<string, string>; // 国际化贡献
  hubCommands?: HubCommand[];    // 浮窗 Hub 快捷命令
}
```

### 4.2 现有注册清单

| id | name | color | order | 包路径 |
|----|------|-------|-------|--------|
| `ai-family` | AI Family | `#00FF88` | 5 | plugin-ai-family |
| `target` | 目标量化 | `#00FF88` | 10 | plugin-target |
| `cost` | 成本盈亏 | `#FF6600` | 20 | plugin-cost |
| `marketing` | 节日营销 | `#AA55FF` | 30 | plugin-marketing |
| `prompt` | 提示词库 | `#3399FF` | 40 | plugin-prompt |
| `monitor` | 监控中心 | `#00d4ff` | 50 | plugin-monitor |
| `ops` | 运维管理 | `#FF6600` | 60 | plugin-ops |
| `ai` | AI智能 | `#AA55FF` | 70 | plugin-ai |
| `dev` | 开发工具 | `#E8E8E8` | 80 | plugin-dev |
| `admin` | 系统管理 | `#FFDD00` | 90 | plugin-admin |
| `business` | 业务管理 | `#06b6d4` | 95 | plugin-business |
| `llm` | LLM桥接 | `#8b5cf6` | 96 | plugin-llm |

---

## 五、EventBus 事件总线

### 5.1 事件命名规范

```
{系统名}:{动作}

ai:persona-changed     ← AI Family 发出
ai:ask                 ← AI Family 发出
ai:response            ← AI Family 发出
hub:open               ← 浮窗 Hub 发出
hub:close              ← 浮窗 Hub 发出
hub:navigate           ← 浮窗 Hub 发出
hub:command            ← 浮窗 Hub 发出
shell:welcome-dismiss  ← Shell 发出
shell:sidebar-toggle   ← Shell 发出
system:notify          ← 任何系统可发出
```

### 5.2 使用示例

```typescript
import { eventBus } from "@yyc3/shell";

// 监听事件
const unsubscribe = eventBus.on("ai:response", (data) => {
  console.log(`${data.personaId}: ${data.content}`);
});

// 发出事件
eventBus.emit("system:notify", {
  level: "info",
  message: "目标计算完成",
  systemId: "target",
});

// 组件卸载时取消订阅
useEffect(() => unsubscribe, []);
```

---

## 六、存储架构

### 6.1 命名空间隔离

```
localStorage Key 格式: yyc3:{systemId}:{key}

yyc3:shell:theme              → "dark"
yyc3:shell:sidebarCollapsed   → false
yyc3:ai-family:activePersona  → "meta-oracle"
yyc3:target:lastCalcResult    → { annualTarget: 702, ... }
```

### 6.2 API 使用

```typescript
import { createSystemStorage } from "@yyc3/shell";

const storage = createSystemStorage("target");

// 写入
storage.set("lastCalcResult", { annualTarget: 702 });

// 读取（带默认值）
const result = storage.get("lastCalcResult", { annualTarget: 0 });

// 删除
storage.remove("lastCalcResult");

// 清空本系统所有数据
storage.clear();
```

---

## 七、双主题系统

### 7.1 主题常量

| 主题 | 常量 | 底色 | 主色 | 适用场景 |
|------|------|------|------|----------|
| 现代深空 | `THEME_MODERN` | `#040814` | `#00d4ff` | AI Family、监控、运维 |
| 古文化鎏金 | `THEME_ANCIENT` | `#1E180E` | `#C9A96E` | 古风场景备用主题 |

### 7.2 主题切换

```typescript
import { getTheme, THEME_MODERN, THEME_ANCIENT } from "@yyc3/shell";

// 获取当前主题
const theme = getTheme();
```

---

## 八、AI Family 智能体层

### 8.1 三层架构

```
┌──────────────────────────────────────────────────────┐
│            family-core (家族宪章 · 唯一真相源)         │
│  八位家人档案 · 五维/五高/五标/五化/五环 · 标头标尾生成  │
├──────────────────────────────────────────────────────┤
│            family-skills (技能契约层)                  │
│  defineSkill() · FamilySkill 接口 · NVIDIA 桥接       │
│  63 基础技能 + 198 NVIDIA 技能 (catalog fallback)     │
├──────────────────────────────────────────────────────┤
│            family-agents (Agent 实例层)               │
│  8 位家人 Agent · 编排器 · 工作流 · 审批门控           │
├──────────────────────────────────────────────────────┤
│            family-ui (交互表现层)                     │
│  语音系统 · 模型设置 · 活动中心 · 双主题面板           │
└──────────────────────────────────────────────────────┘
```

### 8.2 八位家人 ID

| 家人名 | ID | 角色 | 主题色 |
|--------|-----|------|--------|
| 千航·引路人 | `qianhang` | 自然语言导航 | `#8b5cf6` |
| 思辨·智库 | `thinker` | 数据洞察分析 | `#06b6d4` |
| 预见·先知 | `prophet` | 趋势预测 | `#10b981` |
| 千里·伯乐 | `bole` | 个性化推荐 | `#f59e0b` |
| 元启·天枢 | `tianshu` | 全局调度 | `#ec4899` |
| 守望·哨兵 | `guardian` | 安全响应 | `#ef4444` |
| 方圆·宗师 | `grandmaster` | 代码审查 | `#6366f1` |
| 语枢·万物 | `grace` | 创意生成 | `#14b8a6` |

### 8.3 FamilySkill 契约

```typescript
// 通过 defineSkill 工厂函数创建技能
import { defineSkill } from "@yyc3/family-skills";

const mySkill = defineSkill(
  {
    id: "my-skill",
    name: "示例技能",
    description: "技能描述",
    family: "grandmaster",        // 归属家人
    version: "1.0.0",
    tags: ["analysis"],
  },
  async (input, ctx) => {
    // 执行逻辑
    return { result: "..." };
  },
  // 可选：输入验证
  async (input) => {
    return input !== null;
  }
);
```

### 8.4 NVIDIA 桥接

`family-skills` 包含 NVIDIA SDK 离线桥接器，通过静态 catalog fallback 在无 SDK 环境下提供 200+ NVIDIA 技能映射（NIM、Guardrails、Riva、CUOpt、RAG、TAO、Dynamo、Earth-2）。

---

## 九、系统间通信原则

```
✅ 允许: EventBus → 松耦合通信
✅ 允许: Hub 浮窗 → 统一入口
✅ 允许: 统一存储 → 共享配置（各自命名空间）
✅ 允许: peerDependencies 声明依赖

❌ 禁止: 直接 import 其他插件包的组件
❌ 禁止: 直接读写其他插件包的存储
❌ 禁止: 互相依赖路由结构
❌ 禁止: 修改 Shell 核心类型定义
```

---

## 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| v1.0.0 | 2026-07-16 | 初始版本，整合 ARCHITECTURE.md 核心内容 | YanYuCloudCube Team |
| v1.1.0 | 2026-07-24 | 新增 AI Family 智能体层（§八），更新插件清单至 15 个，更新测试数至 760+ | YanYuCloudCube Team |
