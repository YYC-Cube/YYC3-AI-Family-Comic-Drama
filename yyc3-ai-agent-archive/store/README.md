# @yyc3/store

> 持久化抽象层 —— Store 接口 + Memory / File / Redis 三适配器

![Version](https://img.shields.io/badge/version-1.0.0-00d4ff?style=flat-square)
![Tests](https://img.shields.io/badge/tests-17%20passing-00FF88?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-FF6600?style=flat-square)

## 定位

基础设施层最底层包：最小 `Store` 接口（`get/put/delete/keys/clear/close`），
三个可互换适配器，供 `agent-runtime` 等按环境选择。

| 适配器 | 特性 |
| ------ | ---- |
| `MemoryStore` | 进程内 Map，开发/测试默认 |
| `FileStore` | 原子写（tmp + rename）；防抖 flush 串行化链；`timer.unref()` 不阻塞退出 |
| `RedisStore` | lazy import ioredis（未安装自动降级并记录 `degradedReason`）；3 次指数退避；**SCAN 替代 KEYS**（防 O(N) 阻塞） |

## 使用

```ts
import { FileStore } from '@yyc3/store';

const store = new FileStore({ filePath: './data/agents.json' });
await store.put('agent:1', { state: 'idle' });
const agent = await store.get('agent:1');
await store.close();          // 确保防抖窗口内的写入落盘
```

## 已知边界（如实说明）

- FileStore 为全量快照写放大模型，适合小数据量（agent 档案/配置），不适合高频大 value
- 防抖窗口内的写入在 `close()` 或下次 flush 时落盘

## 测试

```bash
pnpm --filter @yyc3/store test             # 17 用例（原子写 / 并发加载 / 降级路径）
```

## 许可证

MIT © 2026 YanYuCloudCube Team
