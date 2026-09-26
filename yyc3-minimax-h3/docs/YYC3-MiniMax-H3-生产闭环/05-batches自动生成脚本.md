---
file: 05-batches自动生成脚本.md
description: 面板数据契约归一决策记录与 NAS 分发层说明（P1-C2：唯一写端 export_dashboard_data.py，旧扁平数组生成器已废弃）
author: Intelligent Application Implementation Expert <admin@0379.email>
version: v1.2.0
created: 2026-09-25
updated: 2026-09-26
status: active
tags: [batches],[contract],[nas],[adr]
category: design
language: zh-CN
changelog:
  - { version: v1.0.0, date: 2026-09-25, author: 智能应用落地专家, change: 原始版本收录（生成于外部会话，含 update_dashboard_batch.py 方案） }
  - { version: v1.1.0, date: 2026-09-25, author: 智能应用落地专家, change: P1-D1 规范化整备（补齐 YAML FM） }
  - { version: v1.2.0, date: 2026-09-26, author: 智能应用落地专家, change: P1-C2 契约归一重构——废弃双源生成器（原代码含 shell=True 注入违规，已移除），归一至仓库真源契约 batchesPayloadSchema；转为 ADR + NAS 分发说明 }
---

# 面板数据契约归一决策与 NAS 分发说明（P1-C2）

> 本篇原为「batches.json 自动生成脚本」（`update_dashboard_batch.py` 方案）。经 P1-C2 审计，该方案与仓库真源契约存在**双源冲突**，已整体废弃；本篇重构为归一决策记录（ADR）与 NAS 分发层说明。

---

## 一、归一决策记录（ADR）

### 1.1 背景

仓库已存在面板数据桥的唯一落地实现：

- **写端**：[`scripts/pipeline-tools/export_dashboard_data.py`](file:///Users/yanyu/YYC-Cube/YYC3-MiniMax-H3/scripts/pipeline-tools/export_dashboard_data.py)，由 [`pipeline_auto.py`](file:///Users/yanyu/YYC-Cube/YYC3-MiniMax-H3/scripts/pipeline-tools/pipeline_auto.py) ⑤' 节点在批次完成后**静默调用**（失败不阻断流水线）
- **契约**：[`packages/manifest-schema/src/index.ts`](file:///Users/yanyu/YYC-Cube/YYC3-MiniMax-H3/packages/manifest-schema/src/index.ts) 的 `batchesPayloadSchema`（zod，双端契约唯一真源）
- **输出**：`dashboard/data/batches.json`，现网面板 `fetch('./data/batches.json')` 消费

原方案另行引入 `update_dashboard_batch.py` 增量写 `dashboard/batches.json`，形成双源。

### 1.2 冲突清单（废弃理由）

| # | 维度 | 原方案（已废弃） | 仓库真源 |
| - | ---- | ---------------- | -------- |
| 1 | 输出路径 | `dashboard/batches.json` | `dashboard/data/batches.json` |
| 2 | 数据结构 | 扁平数组 `[{...}]` | envelope `{schema_version, generated_at, score_scale, batches[], top10[]}` |
| 3 | 评分刻度 | `sync_score` 0-1 + `quality_level`（0.95/0.90/0.75 阈值） | `avgScore/maxScore` **0-10**（score_norm×10 或 human 1~10 直用） |
| 4 | 字段口径 | `batch_id/create_time/mode/total_time(s)` 等 14 个自造字段 | `id/time/pipeline/durationMin(min)` 等，与 zod 契约逐字段对应 |
| 5 | 触发机制 | 手工插入流水线末尾（subprocess `shell=True` 拼接） | pipeline_auto ⑤' 已内置，argv 数组调用，静默不阻断 |
| 6 | 历史管理 | 追加+去重+截断（MAX_BATCHES=100） | 每次全量重建（扫描全部 `output_batch*`），天然幂等无截断 |

> 注：`0.98/0.76` 为 score_lipsync 启发式评分的**标定基准**（同步/错位样本实测分），并非质量分级阈值——原方案将其误用为分级依据，亦为废弃原因之一。

### 1.3 决策

1. **唯一写端**：`export_dashboard_data.py`。任何面板数据生成需求一律在该脚本内演进。
2. **唯一契约**：`batchesPayloadSchema`。结构变更须先改 zod 契约并同步 Python 写端（对齐 `manifest-schema` 文件头双端约定）。
3. **唯一路径**：`dashboard/data/batches.json`；NAS 镜像与网关路径见 §三。
4. **评分刻度**：0-10。原 `quality_level` 不入契约；如面板需要质量分级，由展示层从 `avgScore` 派生（见 [06 篇](./06-面板完整HTML代码.md) `qualityOf()`：≥9 优秀 / ≥8 良好 / ≥6 合格 / 其余待优化）。
5. **原方案代码处置**：`update_dashboard_batch.py` 及其流水线插入片段**从本文档移除，不得落地**（含 `shell=True` f-string 拼接，违反仓库安全铁律④；历史版本可追溯 git 提交 `b4277d8`）。

---

## 二、真源契约链路（唯一链路）

```
pipeline_auto.py ⑤' 节点（批次完成后自动触发）
    ↓ argv 数组静默调用
export_dashboard_data.py：扫描 output_batch*/manifest.json → 全量重建
    ↓ 写出（envelope 结构，契约 batchesPayloadSchema）
Mac：dashboard/data/batches.json
    ↓ sync_h3_core_up.sh 增量同步
NAS RAID1：/volume1/RAID1/yyc3-core/h3-dashboard/data/batches.json
    ↓ 静态站点（dashboard-h3.0379.world）或网关代理（api.0379.world/h3-dashboard/）
面板 fetch './data/batches.json'（cache: no-store；失败自动降级内置模拟数据，永不断流）
```

**降级策略**：与 score_lipsync 双后端策略一致——fetch 失败时面板渲染内置模拟数据并告警日志，功能永不断流。

---

## 三、NAS 分发层配置

| 层 | 路径 | 说明 |
| -- | ---- | ---- |
| 本地真源 | `dashboard/data/batches.json` | export 脚本唯一输出 |
| NAS 镜像 | `/volume1/RAID1/yyc3-core/h3-dashboard/data/batches.json` | `dashboard/` 整目录纳入 sync_h3_core_up.sh（见 [01 篇](./01-NAS自动同步配置与目录映射清单.md)） |
| 静态站点 | `https://dashboard-h3.0379.world/data/batches.json` | NAS 站点根 = `…/h3-dashboard/` |
| 网关代理 | `https://api.0379.world/h3-dashboard/data/batches.json` | Nginx alias 指向 NAS 挂载（见 [07 篇](./07-面板接入公网网关的Nginx配置.md)） |

**多终端一致性**：export 为全量幂等重建（无增量追加语义），NAS 覆盖同步后各终端读取内容一致；面板 `no-store` 拉取 + 定时刷新对齐同步周期。

---

## 四、废弃字段映射表（旧 → 真源）

供历史数据/外部对照使用：

| 废弃字段（原方案） | 真源字段 | 口径说明 |
| ------------------ | -------- | -------- |
| `batch_id` | `batches[].id` | `batchXX` |
| `create_time` | `batches[].time` | 批次启动时间 |
| `mode` | `batches[].pipeline` | ref2va 等 |
| `status` | `batches[].status` | completed / running |
| `total_time`（秒） | `batches[].durationMin`（分钟） | 单位变化 |
| `sync_score`（0-1） | `batches[].avgScore` / `maxScore`（0-10） | 刻度 ×10 |
| `quality_level` | （无契约字段） | 面板侧 `qualityOf(avgScore)` 派生 |
| `peak_memory` | `batches[].videos[].peak_rss_gb` | 批次级取 max 派生 |
| `seed` | `batches[].seeds`（计数）/ `videos[].seed`（明细） | 单值 → 计数+明细 |
| `video_path` | `batches[].videos[].video_path` | 批次级 → 条目级 |
| `model_version` | `batches[].model` | NF4 / PRUNED |
| `resolution/fps/steps` | `batches[].params` | 原样透传 |
| `input_text` / `ref_image` | （聚合层不承载） | 语义属单条记录，见 `manifest.json` |

---

## 五、对接自检清单

- [ ] 面板 fetch 路径 = `./data/batches.json`（相对 `dashboard/`）
- [ ] 解析 envelope：`payload.batches` 数组渲染，非顶层数组
- [ ] 评分按 0-10 刻度展示（勿再做 ×10 或阈值 0-1 判断）
- [ ] 消费字段与 `batchesPayloadSchema` 一致（以 zod 契约为准）
- [ ] fetch 失败降级路径可用（模拟数据 + 控制台告警）
- [ ] 未在任何新代码中引入第二个 batches 生成器

---

> 📌 关联文档：部署模式与数据链路见 [04-可视化面板对接NAS数据源的配置.md](./04-可视化面板对接NAS数据源的配置.md)；契约对齐后的面板蓝图见 [06-面板完整HTML代码.md](./06-面板完整HTML代码.md)。
