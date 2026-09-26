# @yyc3/observability

> 可观测性监控 —— 结构化日志 / 指标 / 链路追踪 / 健康聚合

![Version](https://img.shields.io/badge/version-1.2.0-00d4ff?style=flat-square)
![Tests](https://img.shields.io/badge/tests-65%20passing-00FF88?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-FF6600?style=flat-square)

## 定位

基础设施层包：为三服务提供统一可观测性原语，零框架绑定。

| 模块 | 能力 |
| ---- | ---- |
| `logger.ts` | 结构化日志 + 内存环（上限防无界）+ 多 transport |
| `metrics.ts` | Counter / Gauge / Histogram；语义对齐 Prometheus（累计桶、`_sum/_count`、标签分区渲染）；高基数防御 `maxSeries` + 一次性告警 |
| `tracer.ts` | Span + OTLP exporter（env 未配置时零开销）；`crypto.randomBytes` 生成 W3C 对齐 ID；跨服务 traceId 继承防断链 |
| `health.ts` | 多检查器聚合（live/ready 两态） |

## 使用

```ts
import { createLogger, createMetrics, createTracer, createHealth } from '@yyc3/observability';

const log = createLogger({ name: 'skill-gateway' });
const metrics = createMetrics({ maxSeries: 1000 });
const tracer = createTracer({ serviceName: 'skill-gateway' }); // OTEL_EXPORTER_OTLP_ENDPOINT 配置后启用
const health = createHealth();
health.register('registry', async () => ({ ok: true }));

metrics.counter('skill_execute_total').inc(1);
const span = tracer.startSpan('execute');
metrics.toPrometheus();   // 文本 exposition 格式
```

## 测试

```bash
pnpm --filter @yyc3/observability test     # 65 用例（四模块单文件覆盖，密度全仓领先）
```

## 许可证

MIT © 2026 YanYuCloudCube Team
