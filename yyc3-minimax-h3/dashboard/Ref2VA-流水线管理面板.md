---
file: Ref2VA-流水线管理面板.md
description: Ref2VA 流水线管理面板 - 五大模块设计与数据接入说明
author: YanYuCloudCube Team <admin@0379.email>
version: v1.1.0
created: 2026-09-02
updated: 2026-09-03
status: active
tags: [reference],[dashboard],[visualization]
category: reference
language: zh-CN
---

# Ref2VA 流水线管理面板已就绪

这是一个深色技术风格的桌面端管理后台，将你之前构建的整套 Python 流水线可视化，包含五大模块：

## 模块功能

| 模块 | 功能 |
| ------ | ------ |
| **仪表盘** | 累计视频数、成功率、平均评分、缺陷数四大指标；评分趋势图、缺陷分布图；最近批次概览表 |
| **流水线控制** | 5节点流程图（生成→打分→分析→更新Seed→下一轮）；一键模拟运行，带终端实时输出和进度条；本轮配置参数展示 |
| **脚本管理** | 7个脚本清单（pipeline_auto / batch_ref2va_nf4 / pruned / analyze_report / update_seed_list / export_multi_batch / clean_batch），含类型标签和状态 |
| **批次管理** | 批次卡片网格（batch01/02/03），展示模型版本、评分条、成功/失败/最高分；点击卡片弹出详情抽屉，含报告文件、视频缩略图网格 |
| **跨批次对比** | 三批次平均分对比卡片；各Seed评分柱状对比图；缺陷趋势折线图；各参考图最优Seed对比表；全局Top10高分样本表 |

## 设计要点

- 深色主题（`#0d1117` 背景 + `#00d4aa` 青绿色主调），适配 AI 模型训练/运维场景
- 左侧固定导航 + 顶部状态栏（流水线状态、当前批次），hash 路由切换视图
- ECharts 交互式图表（评分趋势、缺陷分布、Seed对比、缺陷趋势），带 ResizeObserver 自适应
- 终端风格状态指示器（脉冲动画）、monospace 字体数据展示
- 批次详情侧滑抽屉，视频缩略图网格预览
- 最小宽度 1200px，面向桌面端管理场景

## 使用方式

直接在浏览器中打开即可使用。点击左侧导航切换模块，在「流水线控制」页点击「运行流水线」可模拟完整执行流程，终端会逐行输出日志。

> 提示：面板中的数据为基于你之前流水线结构的模拟数据（3个批次、7个脚本），实际部署时可将 Python 脚本的输出 JSON 接入面板数据源。
---

## 变更历史

| 版本   | 日期       | 变更内容 | 作者 |
| ------ | ---------- | -------- | ---- |
| v1.0.1 | 2026-09-03 | 补齐 YYC3 品牌标尾与变更历史（文档规范审计） | Impl Expert |
| v1.0.0 | 2026-09-02 | 初始版本 | YanYuCloudCube Team |

---

<div align="center">

> 「***YanYuCloudCube***」
> 「***<admin@0379.email>***」
> 「***Words Initiate Quadrants, Language Serves as Core for the Future***」
> 「***All things converge in cloud pivot; Deep stacks ignite a new era of intelligence***」

**© 2025-2026 YanYuCloudCube™. All Rights Reserved.**

</div>
