---
file: YYC3-开发者-测试策略.md
description: YYC³ 测试策略与质量保障体系 — Vitest配置、测试分层、覆盖率目标、TDD实践指南
author: YanYuCloudCube Team <admin@0379.email>
version: v1.0.0
created: 2026-07-16
updated: 2026-07-16
status: stable
tags: [testing],[quality],[vitest],[tdd],[coverage]
category: policy
language: zh-CN
audience: developers
complexity: intermediate
project: yyc3-ai-dev
phase: testing
---

<div align="center">

> **_YanYuCloudCube_**
> _言启象限 | 语枢未来_
> **_Words Initiate Quadrants, Language Serves as Core for Future_**
> _万象归元于云枢 | 深栈智启新纪元_
> **_All things converge in cloud pivot; Deep stacks ignite a new era of intelligence_**

---

</div>

# YYC³ 测试策略与质量保障体系

## 一、测试框架配置

### 1.1 Vitest 配置

```typescript
// vitest.config.ts
import { defineConfig } from "vitest/config";
import path from "path";

export default defineConfig({
  resolve: {
    alias: {
      "@yyc3/shell": path.resolve(__dirname, "packages/shell/src"),
      "@yyc3/plugin-target": path.resolve(__dirname, "packages/plugin-target/src"),
      // ...所有插件包别名
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    include: ["packages/**/*.test.*", "apps/**/*.test.*"],
  },
});
```

### 1.2 运行测试

```bash
# 全量测试
npx vitest run

# 指定插件包
npx vitest run packages/plugin-target/

# 详细输出
npx vitest run --reporter=verbose

# 监听模式
npx vitest
```

---

## 二、测试分层

```
┌─────────────────────────────────────────┐
│           E2E 测试 (Phase 3)             │  ← Playwright
├─────────────────────────────────────────┤
│         组件测试 (Phase 2)               │  ← React Testing Library
├─────────────────────────────────────────┤
│         引擎单元测试 (Phase 1) ✅         │  ← Vitest (当前：117 tests)
├─────────────────────────────────────────┤
│         类型检查 (持续) ✅               │  ← tsc --noEmit
└─────────────────────────────────────────┘
```

### 2.1 当前测试基线

| 插件包 | 测试文件 | 测试数量 | 状态 |
|--------|----------|----------|------|
| plugin-target | target-engine.test.ts | 27 | ✅ 全绿 |
| plugin-cost | cost-engine.test.ts | 30 | ✅ 全绿 |
| plugin-marketing | festival-engine.test.ts | 41 | ✅ 全绿 |
| plugin-prompt | business-prompts.test.ts | 19 | ✅ 全绿 |
| shell | event-bus.test.ts + storage.test.ts | 13 | ✅ 全绿 |
| **合计** | **11 files** | **130 tests** | ✅ |

---

## 三、测试用例编写规范

### 3.1 文件命名与位置

```
packages/plugin-target/
├── src/
│   ├── target-engine.ts
│   └── types.ts
└── target-engine.test.ts    ← 与 src 同级，命名: {引擎名}.test.ts
```

### 3.2 纯逻辑测试：使用 `@vitest-environment node`

引擎层测试不需要 DOM 环境，在文件首行添加：

```typescript
// @vitest-environment node
/**
 * file: target-engine.test.ts
 * description: 目标量化引擎测试 — 20+测试用例覆盖正常/边界/异常
 */
import { describe, it, expect } from "vitest";
import { calc, splitPhases } from "./src/target-engine";
```

### 3.3 describe / it 结构

```typescript
describe("TargetEngine.calc — X公式计算", () => {
  // ── 正常值 ──────────────
  it("一线城市中型门店正常增速", () => { ... });

  // ── 边界值 ──────────────
  it("基础营收为0时结果为0", () => { ... });
  it("所有系数取最大值", () => { ... });

  // ── 异常场景 ────────────
  it("基础营收为负数时不抛异常", () => { ... });
});
```

### 3.4 断言规范

```typescript
// ✅ 精度断言：使用 toBeCloseTo 处理浮点
expect(result.annualTarget).toBeCloseTo(702, 1);

// ✅ 精确断言：整数和固定小数位使用 toBe
expect(phases.peak.ratio).toBe(0.5);

// ✅ 类型断言
expect(typeof result.annualTarget).toBe("number");

// ✅ 集合断言
expect(Object.keys(CITY_TIER_COEFFICIENTS)).toHaveLength(6);

// ✅ 异常断言
expect(() => lunarToSolar(2020, 1, 1)).toThrow();
```

---

## 四、测试覆盖要求

### 4.1 引擎测试必须覆盖的三类场景

| 场景类型 | 说明 | 数量要求 |
|----------|------|----------|
| **正常值** | 典型业务输入 | ≥ 3 个 |
| **边界值** | 极大/极小/零值 | ≥ 2 个 |
| **异常值** | 非法输入/越界/类型错误 | ≥ 1 个 |

### 4.2 每引擎最低测试数量

| 引擎 | 最低测试数 | 当前数量 |
|------|-----------|----------|
| TargetEngine | ≥ 20 | 27 ✅ |
| CostEngine | ≥ 20 | 30 ✅ |
| FestivalEngine + LunarEngine | ≥ 25 | 41 ✅ |
| BusinessPrompts | ≥ 15 | 19 ✅ |

---

## 五、TDD 实践流程

遵循用户指令"完成一项任务并确保其稳定运行后，再推进下一项"：

```
1. 编写引擎代码（types.ts + engine.ts）
       ↓
2. 编写测试文件（engine.test.ts）
       ↓
3. 运行测试 → 修复至全绿
       ↓
4. tsc --noEmit → 修复至零错误
       ↓
5. 提交代码 → 推进下一个引擎
```

### 5.1 质量门禁

| 门禁 | 命令 | 要求 |
|------|------|------|
| 类型检查 | `npx tsc --noEmit` | 零错误 |
| 全量测试 | `npx vitest run` | 全绿 |
| 新增测试 | 每引擎 ≥ 20 | 覆盖正常/边界/异常 |

---

## 六、测试文件标头

```typescript
// @vitest-environment node
/**
 * file: target-engine.test.ts
 * description: 目标量化引擎测试 — 20+测试用例覆盖正常/边界/异常
 * author: YanYuCloudCube Team
 * version: v1.0.0
 * created: 2026-07-16
 * updated: 2026-07-16
 * status: active
 * tags: [test],[unit],[engine]
 */
```

---

## 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| v1.0.0 | 2026-07-16 | 初始版本，当前130 tests 全绿 | YanYuCloudCube Team |
