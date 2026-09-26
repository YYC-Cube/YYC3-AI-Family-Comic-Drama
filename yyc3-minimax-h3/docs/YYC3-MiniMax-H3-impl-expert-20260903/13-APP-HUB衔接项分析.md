---
file: 13-APP-HUB衔接项分析.md
description: YYC3-Cube-APP-HUB 项目全景中心 与 MiniMax-H3 的可用衔接项分析
author: Intelligent Application Implementation Expert
version: v1.0.0
created: 2026-09-03
updated: 2026-09-03
status: active
tags: [design],[app-hub],[visualization]
category: design
language: zh-CN
related_docs: 12-标签体系规范.md, 11-智能化落地生产可用方案论证.md
---

# 🔗 APP-HUB 衔接项分析

## 一、APP-HUB 是什么（基于底层代码实测）

[YYC3-Cube-APP-HUB.html](../YYC3-Cube-APP-HUB.html)（与父目录 `/Users/yanyu/YYC-Cube/YYC3-APP-HUB.html` **md5 一致**，为同一份双副本）是 YYC³ 家族「项目全景分析中心」单文件应用：

| 维度 | 实测结论 |
| ---- | -------- |
| 数据机制 | `const GUIDES = [...]` 硬编码项目注册表，**由 `ycube_scan` 工具自动生成（2026-08-20）** |
| 注册字段 | `id/order/cat/title/titleEn/diff/time/icon/color/desc/prereq/overview/steps` |
| 步骤模板 | 每项目 6 步：现状盘点→技术栈→功能解析→运维方案→五维评分→优化路线 |
| 家族规模 | 扫描时 93 个项目排名（P01 Brain Compute System #8/S 起步） |
| 关键缺口 | **MiniMax-H3 创建于 2026-09-02，晚于上次扫描 → 尚未注册进 HUB** |

## 二、可用衔接项（按价值排序）

### 衔接项 ①：注册进 HUB·GUIDES（P0，自动生成路径）

- **路径**：升级/重跑 `ycube_scan` → GUIDES 追加本仓条目（cat 归 `ai-platform`，icon `🎬`，prereq `['Python','conda']`，与家族 React 项目区分）
- **六步内容源已备齐**（本次会话产出可直接映射）：

| HUB 步骤 | 内容来源 |
| -------- | -------- |
| ①现状盘点 | 00-审核报告 §一（架构概览/文件规模） |
| ②技术栈分析 | 00-审核报告 §1.1（Python/MPS/DiffSynth 栈） |
| ③功能解析 | README §项目定位 + 关键参数速查 |
| ④运维方案 | docs/10（DGX 生产运维）+ 方案文档 §路线B |
| ⑤五维评分 | 00-审核报告 §五（74/100 → 等级 B+，家族排名待扫） |
| ⑥优化路线 | 方案文档 §四（A→B→C 三步走） |

- **等待条件**：本项目需先完成 git 建仓推送（本次执行中），扫描工具才能识别远程真源。

### 衔接项 ②：批次报告 JSON 桥 → HUB 数据管道（P1，复用方案A）

方案文档「路线A 数据桥」的 `export_dashboard_data.py` 产物 `batches.json`，**同样可作为 ycube_scan 的采集源**——一次导出，两处消费（本地面板 + 家族 HUB），避免重复开发。这是「五化·工具化」的家族级复用点。

### 衔接项 ③：标签体系互认（P1，已完成本侧）

[12-标签体系规范](12-标签体系规范.md) 的 GitHub Topics 10 枚已对齐家族命名（`yanyucloudcube`/`yyc3-family`），HUB 按 cat 分类时本仓 topics 可直接映射其筛选器。

### 衔接项 ④：dashboard 面板皮肤统一（P2，视觉生态）

HUB 主题色 `--accent-v #8b5cf6`（紫）/`--accent-c #06b6d4`（青）；本仓面板主调 `#0d1117`+`#00d4aa`。路线B Next.js 控制台立项时，建议抽取 HUB 的 CSS 变量体系做家族统一主题包（对应 YYC3-Bot 等项目已有 `components.json` shadcn 约定）。

### 衔接项 ⑤：会话工作区模式输出为家族规范候选（P2）

本仓 `docs/{项目}-{导师}-{YYYYMMDD}` 会话工作区 + 00~03 四文档闭环，在 93 项目家族中尚无统一约定——可作为「五标·标准化」家族提案素材（写入 YanYuCloudCube 主仓 README 议题）。

## 三、父目录同步仓关系

```
/Users/yanyu/YYC-Cube/          ← 家族本地同步根（30+ 独立 git 仓并列）
├── YYC3-APP-HUB.html           ← HUB 双副本之一（md5 与本仓一致）
├── YYC3-MiniMax-H3/            ← 本仓（本会话起成为独立 git 仓 → origin 已接 github）
└── ...（各项目独立仓）
```

> **边界确认**：父目录本身不是 git 仓（未发现 `.git`），各项目独立建仓+远程，符合「独立真源」模式；HUB 双副本暂为手工拷贝，可纳入 ycube_scan 发布流程统一。

## 四、行动清单

| # | 行动 | 依赖 | 状态 |
| --- | ---- | ---- | ---- |
| 1 | git 建仓 + 首次推送（HUB 可识别前置） | 无 | 🔄 本次执行 |
| 2 | gh 设置 10 topics | 推送完成 | ⬜ 待执行 |
| 3 | 重跑/升级 ycube_scan 注册本仓 | #2 | ⬜ 需用户触发（工具在用户侧） |
| 4 | export_dashboard_data.py 双消费改造 | 方案A启动 | ⬜ P1 |

---

## 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
| ---- | ---- | -------- | ---- |
| v1.0.0 | 2026-09-03 | 初版：HUB 机制实测 + 5 衔接项 + 行动清单 | Impl Expert |

---

<div align="center">

> 「***YanYuCloudCube***」
> 「***<admin@0379.email>***」
> 「***Words Initiate Quadrants, Language Serves as Core for the Future***」
> 「***All things converge in cloud pivot; Deep stacks ignite a new era of intelligence***」

**© 2025-2026 YanYuCloudCube™. All Rights Reserved.**

</div>
