# @yyc3/plugin-marketplace

> Plugin Marketplace 运行时 —— 注册 / 发现 / 安装 / 激活生命周期

![Version](https://img.shields.io/badge/version-1.1.0-00d4ff?style=flat-square)
![Tests](https://img.shields.io/badge/tests-32%20passing-00FF88?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-FF6600?style=flat-square)

## 定位

插件注册表运行时：插件（`vendor/name` ID + SemVer）的注册、依赖解析校验、
安装、激活/停用与写穿持久化。当前为**注册表语义**（不落盘安装文件），
文件系统级安装见根 README 实现状态矩阵。

## 生命周期与约束

| 能力 | 实现 |
| ---- | ---- |
| 注册 | ID 格式 `vendor/name` 强校验；SemVer 严格校验 |
| 安装 | 直接依赖存在性 + 版本满足校验（`>=` 语义，降级需 force） |
| 激活 | 依赖闭包检查：激活前校验全部传递依赖均已激活 |
| 停用/移除 | 反向依赖检查：防级联卸载仍被依赖的插件 |
| 持久化 | 写穿 + `flushPending()` / `restore()`（与 agent-runtime 同构） |

## 使用

```ts
import { PluginMarketplace } from '@yyc3/plugin-marketplace';

const market = new PluginMarketplace({ rootDir: './plugins' });
await market.register(manifest);
await market.install('vendor/demo', '1.2.0');
await market.activate('vendor/demo');
market.on('plugin:activated', (e) => {});
```

## 测试

```bash
pnpm --filter @yyc3/plugin-marketplace test   # 32 用例
```

## 许可证

MIT © 2026 YanYuCloudCube Team
