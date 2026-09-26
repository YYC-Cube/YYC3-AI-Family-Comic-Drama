# @yyc3/skill-sandbox

> Skill 沙箱执行环境 —— Node / Python / Shell 三运行时 + 纵深防御原语

![Version](https://img.shields.io/badge/version-1.0.1-00d4ff?style=flat-square)
![Tests](https://img.shields.io/badge/tests-76%20passing-00FF88?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-FF6600?style=flat-square)

## 定位

核心层最底层包（零 `@yyc3` 依赖）：提供受策略保护的技能执行门面与安全原语，
被 `skill-registry` 执行链共同消费。

> ⚠️ **诚实声明**：进程内正则黑名单是尽力而为的**内容策略层**，不是强安全边界。
> 不可信技能必须运行在容器级 OS 隔离之下（见根目录 `docker-compose.yml` 加固配置）。

## 模块分层

```
SkillSandbox（唯一受策略保护的执行入口）
  ├─ security.ts   纯函数安全原语：resolveSkillEntry / buildSafeEnv / normalizeTimeout
  ├─ sanitizer.ts  正则黑名单内容策略 + 反规避矩阵 + 命令黑名单
  └─ executor.ts   低层 spawn 原语（刻意不内置检查，勿直接用于不可信输入）
```

## 执行管线

静态内容校验 → 命令黑名单（native/strict）→ cwd 收敛（CWD_ESCAPE）→
环境白名单 → 参数净化 + 超时钳制 → 低层执行 → 事件广播（start/complete/blocked/timeout/error）

## 使用

```ts
import { SkillSandbox } from '@yyc3/skill-sandbox';

const sandbox = new SkillSandbox({ mode: 'strict' });
const result = await sandbox.execute({
  runtime: 'node',
  entry: '/skills/demo/run.js',
  timeoutMs: 30_000,      // 0/负/NaN 自动回退默认（防「0 = 无超时」陷阱）
  maxOutputBytes: 1024*1024,
});
```

## 反规避矩阵（对抗测试覆盖）

- Python：`__import__` / getattr builtins / 字符串拼接 import
- Node：`process.binding` / `globalThis` 动态索引
- Shell：base64 解码管道注入
- 实弹回归：`rm -rf /`、`sudo sh`、`killall` 返回 `COMMAND_BLOCKED`（不产生子进程）
- 宿主密钥隔离：真实子进程探针验证白名单外变量不可见

## 测试

```bash
pnpm --filter @yyc3/skill-sandbox test    # 76 用例（Sanitizer 20 / Executor 17 / 门面 7 / 安全原语与对抗 32）
```

## 许可证

MIT © 2026 YanYuCloudCube Team
