# @yyc3/skill-registry

> Skill 注册中心 —— 扫描 / 解析 / 校验 / 执行 / 熔断

![Version](https://img.shields.io/badge/version-1.3.0-00d4ff?style=flat-square)
![Tests](https://img.shields.io/badge/tests-83%20passing-00FF88?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-FF6600?style=flat-square)

## 定位

Monorepo 核心层包：将 `SKILL.md`（YAML frontmatter + 正文）解析为 `UnifiedSkill`
并注册、索引、校验、隔离与执行。上游被 `skill-gateway` / `mcp-runtime` 消费，
下游依赖 `@yyc3/skill-sandbox` 的安全原语（依赖方向不得反向）。

## 核心模块

| 模块 | 职责 |
| ---- | ---- |
| `frontmatter.ts` | 零依赖 YAML 子集解析器（引号/内联数组/`>` `\|` 块标量/CRLF，引号感知注释剥离） |
| `registry.ts` | `SkillRegistry`：domain/tag 双索引 + SemVer 同名冲突治理（variants）+ 类型化事件总线 |
| `loader.ts` | 文件系统扫描 → 领域优先级解析 → 注册前校验 + 隔离区（quarantine） |
| `validator.ts` | Zod 双层校验（`validateFrontmatter` / `validateUnifiedSkill`，与 doctor 单一事实源共用） |
| `executor.ts` | `SkillExecutor`：熔断器（半开探测）+ 递归降级链 + spawn 三重安全控制点 |

## 安装与使用

```ts
import { SkillRegistry, SkillExecutor } from '@yyc3/skill-registry';

const registry = new SkillRegistry();
await registry.register(manifest);          // 同名高版本自动胜出，低版本入 variants
registry.on('skill:quarantined', (e) => {}); // 9 种强类型事件

const executor = new SkillExecutor(registry);
const result = await executor.execute('paper-quick-reader', { input });
// entry 路径收敛 + env 白名单 + 超时钳制 + 1MB 输出上限
```

## 安全特性

- 执行三重控制点：entry 路径收敛（防穿越）→ 环境变量白名单（宿主密钥不透传）→ 超时钳制
- callId 使用 `crypto.randomBytes`；熔断器半开计数真实生效（half-open 探测）
- 非法资产注册前隔离（`skill:quarantined` 事件），不进入可执行索引

## 测试

```bash
pnpm --filter @yyc3/skill-registry test   # 83 用例（含 8 条安全回归：5 路径穿越 + 3 env 白名单）
```

## 许可证

MIT © 2026 YanYuCloudCube Team
