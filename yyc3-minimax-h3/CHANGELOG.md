---
file: CHANGELOG.md
description: YYC3-MiniMax-H3 变更日志（Keep a Changelog 规范）
author: YanYuCloudCube Team <admin@0379.email>
version: v1.0.0
created: 2026-09-03
updated: 2026-09-03
status: active
tags: [changelog],[history],[release]
category: meta
language: zh-CN
---

# 变更日志

所有对本项目的显著变更将记录于此。
格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本遵循 [语义化版本 2.0.0](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Added

- **GB10 部署包情报整合**（源：NVIDIA 论坛社区部署包克隆，分析见 docs/12，对标清单 docs/13）：
  - 快预览档 `batch_ref2va_nf4.py --preview`（360p/64帧/30步，白天窗口快速迭代）+ `--variant` 参数化（nf4/pruned 切换，CUDA 侧绕过 bnb）
  - int8 黑屏自检纳入 docs/10 §5.2 杠杆 0 与 §8 验收清单（GB10 硅缺陷风险：到货首日 `steps=1` 检查，受影响锁 fp8）
  - docs/10 §5.2 增补低分辨率+超分杠杆（GB10 实测 6.03×）与统一内存带宽墙预案
- **docs/13-自研节点包对标清单.md**：上游 workflow JSON → zod 契约字段映射 + 8 个 custom node 功能对标（P1-P3 优先级）+ 节点包 v0.1 范围与验收门禁；Heretic 无审查 TE 划为合规红线永不纳管

- **Phase 2.1 归档通道**（`scripts/pipeline-tools/archive_to_nas.sh`）：双速制 NAS 归档（manifest 快车道实时 + 媒体慢车道 rsync -z 断点续传）、`.nas_pending` 降级队列 + `--retry-pending` 自愈补同步（对齐《第五能力审核论证》修正 1/3）
- **Phase 2.2 夜间批量**（`scripts/pipeline-tools/nightly_run.sh`）：22:00–08:00 窗口硬约束 + 全链路编排（生成→评分→归档→补同步→面板→次晨报告）+ `H3_FORCE` 调试逃生阀
- **docs/11-第五能力衔接实施方案.md**：三文档（DGX 指南/审核论证/可行性分析）收口 + Phase 2.3 异步任务 API 契约固化

### Fixed

- **CI 供应链加固**：全部第三方 action 以 commit SHA 锁定（tag 可变、SHA 不可变，防 tag 劫持），同时消除 IDE「Unable to resolve action」报错
- **CI 红灯三连修 → 五门禁全绿**：
  1. pnpm 11 `minimumReleaseAge`（24h 供应链冷却）拒绝 lockfile 中当日发布版本（`@types/react-dom@19.2.7`、`postcss@8.5.27`）→ workspace `overrides` pin 到合规版本（8.5.26 / 19.2.5），安全策略不放松
  2. `ERR_PNPM_IGNORED_BUILDS: esbuild` → v11 已移除 `onlyBuiltDependencies`，构建许可迁移至 `allowBuilds: { esbuild: true }` 映射格式
  3. 契约测试在 CI 无 `output_batch*/` 生成数据时退出 1 → 无真实数据回退内置 fixture，门禁双端有效
- 配置收口：移除根 `package.json` 失效的 `pnpm` 字段，`pnpm-workspace.yaml` 归位为依赖设置单一真源

### Added

- **路线B 生产控制台**（`apps/console/`，Next.js 15 + pnpm workspace）
  - `/` 仪表盘：RSC 直读 `output_batch*/manifest.json` 单一事实源，评分趋势/缺陷分布/Seed 对比/缺陷趋势四图（ECharts）
  - `/pipeline` 流水线控制：触发 API + SSE 实时日志台（回填 300 行、15s 心跳、3s 断线重连）
  - `/batches/batchXX` 批次详情：视频卡片网格 + 人工精评抽屉（1~10 滑条 + 缺陷标签）
  - `/api/score`：按 `参考图+Seed` 定位写回 `report_batchXX.md`，完成后静默刷新数据桥
- **manifest 变更自动刷新**：`fs.watch` 递归监听 → 500ms 去抖 → SSE `file` 事件 → `router.refresh()` 无感更新
- **双端 schema 契约**（路线C 契约层，`packages/manifest-schema/`）
  - zod 唯一真源 → `gen-json-schema.ts` 生成 Draft-07 JSON Schema
  - `validate_manifest.py` Python 端校验器（jsonschema 可选，缺失降级结构快检）
  - zod / Python 双端互验通过（真实 batch01 数据）
- **CI 门禁**（`.github/workflows/ci.yml`）：Python 编译 → 契约校验 → schema 漂移检查 → console 构建 → spawn 白名单完整性
- 静态管理面板（`dashboard/`，路线A 数据桥）：fetch `dashboard/data/batches.json`，失败自动降级模拟数据
- `export_dashboard_data.py`：manifest → `batches.json` 聚合层（评分 0-10 统一刻度、缺陷标签聚合、Top10）
- `pipeline_auto.py` CLI：`--batch/--auto/--dry-run`（非交互触发与联调演练），步骤⑤' 自动刷新面板数据
- GitHub 仓库标签体系 v2.0（topics ×10 三层词表：品牌/领域/引擎·平台·生态）

### Changed

- `packages/manifest-schema`：补写端扩展字段（`time/mps_alloc_gb/backend/scored_at`）+ `.passthrough()` 扩展放行
- 文档/代码标头标尾全量规范化（22 py + 15 md，YYC³ FM + 品牌标尾 + 变更历史）
- 根目录整理：源文档归档 `docs/legacy/`，品牌资产 `docs/assets/`，DiffSynth 转 submodule（锁 `b6b279d`）

### Fixed

- `pipeline_auto.py` 四处脚本引用路径错位（`SCRIPTS_DIR/TOOLS_DIR` 锚定）
- `pipeline_auto.py` 非交互 EOF 崩溃（`--auto` 跳过 `input()`）
- 多 lockfile 环境 `outputFileTracingRoot` 误推断（`next.config.ts` 显式锚定）
- Tailwind v4 简写迁移 ×31（`[var(--x)]` → `(--)`）

## [v2.0.0] - 2026-09-02

### Added

- MiniMax-H3 NF4 量化本地推理（Apple M4 Max 128GB 实测基线：≥3.3 it/s、RSS ~32.8GB）
- Ref2VA 端到端流水线：参考图 + 语音 → 说话视频（身份保持）
- SyncNet 自动口型评分 + 启发式降级
- `manifest.json` 双向数据契约（生成侧写、消费侧读）
- 性能基线采集（RSS / MPS 峰值）与批次报告体系

[Unreleased]: https://github.com/YYC-Cube/YYC3-MiniMax-H3/compare/v2.0.0...HEAD
[v2.0.0]: https://github.com/YYC-Cube/YYC3-MiniMax-H3/releases/tag/v2.0.0

---

> 「***YanYuCloudCube***」
> 「***<admin@0379.email>***」
> 「***Words Initiate Quadrants, Language Serves as Core for the Future***」
> 「***All things converge in cloud pivot; Deep stacks ignite a new era of intelligence***」

## 变更历史

| 版本 | 日期 | 作者 | 变更内容 |
| ---- | ---- | ---- | -------- |
| v1.0.0 | 2026-09-03 | YanYuCloudCube Team | 初始版本：收录 v2.0.0 发布基线 + 路线A/B/C 落地记录 |

**© 2025-2026 YanYuCloudCube™. All Rights Reserved.**
