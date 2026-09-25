---
file: YYC3-开发者-编码规范.md
description: YYC³ 编码规范手册 — TypeScript/React/命名/代码标头/样式 全量标准，团队强制执行
author: YanYuCloudCube Team <admin@0379.email>
version: v1.0.0
created: 2026-07-16
updated: 2026-07-16
status: stable
tags: [coding-standard],[typescript],[react],[naming],[code-quality]
category: policy
language: zh-CN
audience: developers
complexity: intermediate
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

# YYC³ 编码规范手册

## 一、TypeScript 规范

### 1.1 严格模式

项目 `tsconfig.json` 已开启 `strict: true`，以下为强制要求：

| 规则 | 要求 |
|------|------|
| `noImplicitAny` | ✅ 禁止隐式 any |
| `strictNullChecks` | ✅ 必须显式处理 null/undefined |
| `strictFunctionTypes` | ✅ 函数类型严格检查 |
| `noUnusedLocals` | ✅ 禁止未使用的局部变量 |
| `noUnusedParameters` | ✅ 禁止未使用的参数 |

### 1.2 类型定义规范

```typescript
// ✅ 正确：接口用于对象形状
export interface TargetParams {
  baseRevenue: number;
  cityTier: CityTier;
}

// ✅ 正确：联合类型用于枚举
export type CityTier = "tier-1" | "new-tier-1" | "tier-2";

// ✅ 正确：const 对象 + as const 用于常量表
export const CITY_TIER_COEFFICIENTS = {
  "tier-1": { min: 1.2, max: 1.5, label: "一线城市" },
} as const;

// ❌ 错误：使用 enum（项目统一使用联合类型）
enum CityTier { TIER_1 = "tier-1" }
```

### 1.3 数字精度处理

所有金额计算结果必须保留两位小数：

```typescript
// ✅ 正确
const result = Number((a * b * c).toFixed(2));

// ❌ 错误：浮点精度丢失
const result = a * b * c;
```

---

## 二、代码文件标头

### 2.1 TypeScript/TSX 标头格式

所有 `.ts` / `.tsx` 文件必须包含 JSDoc 标头：

```typescript
/**
 * file: target-engine.ts
 * description: 目标量化核心计算引擎 — X公式 + 三阶段拆分 + 月度节点
 * author: YanYuCloudCube Team
 * version: v1.0.0
 * created: 2026-07-16
 * updated: 2026-07-16
 * status: active
 * tags: [engine],[calculation],[target]
 */
```

### 2.2 必填字段

| 字段 | 说明 | 示例 |
|------|------|------|
| `file` | 文件名 | `target-engine.ts` |
| `description` | 一句话描述（≤50字） | `目标量化核心计算引擎` |
| `author` | 作者 | `YanYuCloudCube Team` |
| `version` | 语义化版本 | `v1.0.0` |
| `created` | 创建日期 | `2026-07-16` |
| `updated` | 更新日期 | `2026-07-16` |
| `status` | 状态 | `active` |
| `tags` | 2-4个标签 | `[engine],[calculation]` |

---

## 三、命名规范

### 3.1 文件命名

| 对象 | 规范 | 示例 |
|------|------|------|
| 组件文件 | PascalCase.tsx | `Dashboard.tsx`, `MonitorPage.tsx` |
| 引擎文件 | kebab-case-engine.ts | `target-engine.ts`, `cost-engine.ts` |
| 类型文件 | types.ts | `types.ts` |
| 注册文件 | register.ts | `register.ts` |
| 测试文件 | {name}.test.ts | `target-engine.test.ts` |
| 常量数据 | kebab-case.ts | `festivals.ts`, `business-prompts.ts` |

### 3.2 组件命名模式

| 模式 | 示例 | 说明 |
|------|------|------|
| PascalCase 功能名 | `Dashboard`, `MonitorPage` | 页面组件 |
| XxxPage | `FamilyHomePage`, `MonitorPage` | 完整页面 |
| XxxCard | `AgentCard`, `FamilyCard` | 卡片组件 |
| XxxBar | `ProgressStepBar`, `PersonaBar` | 条状组件 |
| XxxModal | `CreateRuleModal` | 弹窗组件 |
| XxxEngine | `TargetEngine`, `CostEngine` | 引擎对象 |

### 3.3 函数命名

| 类型 | 规范 | 示例 |
|------|------|------|
| 计算函数 | camelCase 动词开头 | `calc()`, `forecastRevenue()` |
| 拆分函数 | `split*` | `splitPhases()`, `splitMonthly()` |
| 校验函数 | `validate*` | `validate()`, `validateParams()` |
| 转换函数 | `XToY` | `lunarToSolar()`, `solarToLunar()` |
| 获取函数 | `get*` | `getFestivalStage()`, `getWeekday()` |
| 筛选函数 | `filter*` | `filterByStage()`, `filterByType()` |
| 构建/生成 | `build*` | `buildFestivalCalendar()` |

### 3.4 变量命名

```typescript
// ✅ 布尔值用 is/has/can/should 前缀
const isValid = true;
const hasChildren = false;
const canProceed = true;

// ✅ 常量全大写下划线
const MAX_RETRY = 3;
const DEFAULT_PAGE_SIZE = 20;

// ✅ 集合用复数
const festivals = [...];
const menuItems = [...];
```

---

## 四、React 规范

### 4.1 组件定义

```typescript
// ✅ 正确：函数声明 + 明确返回类型
export function AgentCard({ agent, onSelect }: AgentCardProps): JSX.Element {
  return <div>...</div>;
}

// ❌ 错误：箭头函数组件（项目统一使用 function 声明）
const AgentCard = ({ agent }: AgentCardProps) => <div>...</div>;
```

### 4.2 Props 类型定义

```typescript
// ✅ 正确：interface 定义 Props
interface AgentCardProps {
  agent: Agent;
  onSelect?: (id: string) => void;
}

// ❌ 错误：内联类型
function AgentCard({ agent }: { agent: Agent }) { ... }
```

### 4.3 Hook 使用规范

```typescript
// ✅ useEffect 必须有清理函数（订阅/定时器）
useEffect(() => {
  const unsub = eventBus.on("ai:response", handler);
  return unsub;
}, []);

// ✅ 依赖数组必须完整
useEffect(() => {
  fetchData(id);
}, [id]); // ← 依赖项不可遗漏
```

---

## 五、引擎层编码规范

### 5.1 纯函数要求

| 规则 | 说明 |
|------|------|
| 无副作用 | 不修改入参，不依赖外部可变状态 |
| 确定性 | 相同输入永远产生相同输出 |
| 可测试性 | 无需 mock 即可单元测试 |
| 零 UI 依赖 | 引擎不 import 任何 React 组件 |

### 5.2 精度规范

```typescript
// 金额：保留 2 位小数
const revenue = Number((base * coefficient).toFixed(2));

// 百分比：保留 1 位小数
const margin = Number((profit / revenue * 100).toFixed(1));

// 倍数：保留 3 位小数
const multiplier = Number((target / base).toFixed(3));
```

---

## 六、注释规范

### 6.1 区域注释（分隔符）

```typescript
// ============================================================
// 核心计算：X = 基础基数 × 城市系数 × 规模系数 × 增速系数 × 调整系数
// ============================================================
```

### 6.2 复杂逻辑注释

```typescript
// 旺季天数包含：春节(7天)+暑期(45天)+国庆(7天)+周末(43天) ≈ 102天
peak: { ratio: 0.50, days: 102 },
```

### 6.3 TODO 注释

```typescript
// TODO: Phase 2 填充实际页面组件
routes: [],
```

---

## 七、Git 提交规范

### 7.1 提交信息格式

```
{type}: {description}

type 可选值:
  feat     新功能
  fix      修复
  docs     文档
  test     测试
  refactor 重构
  chore    杂项
```

### 7.2 示例

```bash
git commit -m "feat: plugin-target 目标量化引擎 + 27测试"
git commit -m "fix: 修正中秋节农历转换日期偏移"
git commit -m "docs: 新增开发者编码规范手册"
git commit -m "test: plugin-cost 成本引擎30个测试全绿"
```

---

## 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| v1.0.0 | 2026-07-16 | 初始版本 | YanYuCloudCube Team |
