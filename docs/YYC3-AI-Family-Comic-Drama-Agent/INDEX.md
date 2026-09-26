---
file: INDEX.md
description: docs/YYC3-AI-Family-Agent 目录总索引 — 全量闭环架构文档查阅入口
author: YanYuCloudCube Team <admin@0379.email>
version: v1.3.0
created: 2026-09-24
updated: 2026-09-26
status: active
tags: [索引],[导航],[架构]
category: index
language: zh-CN
---

<!--
  ============================================================
  YYC³ AI Family — 人从众曌众从人
  亦师亦友亦伯乐 · 一言一语一协同
  ============================================================
-->

# docs/YYC3-AI-Family-Agent 目录索引

> **事实源分层（v1.3.0 治理，原「唯一事实源」声明作废）**：
> ① **架构规范事实源** = 本目录（12 子目录 × README+API.md+代码 三位一体）；
> ② **可运行代码事实源** = `../../../yyc3-ai-agent-archive/components/`（15 组件：13 平移件 + prompt_runtime 装载运行时 + orchestrator_events 事件埋点；降级冒烟 11/11 通过）；
> ③ **上游网关侧实现** = `../../../yyc3-0379-world/core/agents/`（上游同步域，经 scripts/sync-upstreams.sh 管理）。
> 历史文档中的《YYC3-多端部署-Agent代码/YYC3-AI-Family-Agent》路径在本仓**不存在**，一律按上述映射解读。本目录为**架构呈现层**：面向查阅、评审、漫剧落地衔接。

## 一、文档清单

| 文件 | 版本 | 定位 | 适用读者 |
| ---- | ---- | ---- | -------- |
| [YYC3-AI-Family-Agent-全量闭环架构总纲.md](YYC3-AI-Family-Agent-全量闭环架构总纲.md) | v1.0.0 | ★ 核心产出：8Agent 全量闭环架构（设计架构/交互逻辑/功能模块/运行流程四位一体） | 架构师/开发/管理 |
| [YYC3-03-AI漫剧智能体编排方案-对齐版.md](YYC3-03-AI漫剧智能体编排方案-对齐版.md) | v1.1.0 | 漫剧场景化编排（§2.1 已与组件库对齐：三层定位+标准接口+模型映射+知遇伯乐更名+九步映射） | 漫剧生产团队 |
| [YYC3-AI-Family-Skills技能库框架目录.md](YYC3-AI-Family-Skills技能库框架目录.md) | v1.0.0 | Skills 技能库框架：13 域 44 技能（编号与组件库同构，SKILL.md 契约模板 + P0 映射表 + 门禁锚点） | 开发/AI Agent |
| [README.md](README.md) | — | 组件库主 README 副本（总规范：8成员矩阵+ReAct-C九步+目录标准） | 全体 |

## 一a、Agent 专属子目录索引（12 目录 × 三位一体）

每个子目录 = **README.md（规范）+ API.md（接口契约：参数表/错误码/调用示例）+ 代码实现**，与标准组件库逐字同步：

| 子目录 | 成员/能力 | 核心接口 | 代码文件 |
| ------ | --------- | -------- | -------- |
| [00-公共基座/](00-公共基座/README.md) | BaseAgent 统一基类 | `run` / `_mock_run` / `heartbeat` | [base_agent.py](00-公共基座/base_agent.py) |
| [01-元启天枢-决策中枢/](01-元启天枢-决策中枢/README.md) | 元启·天枢 · 总指挥 | `plan_tasks` / `synthesize` / `decide` | [yuanqi_tianshu_agent.py](01-元启天枢-决策中枢/yuanqi_tianshu_agent.py) |
| [02-智云守护-安全官/](02-智云守护-安全官/README.md) | 智云·守护 · 安全官 | `check_input` / `audit` / `write_audit_log` | [zhiyun_shouhu_agent.py](02-智云守护-安全官/zhiyun_shouhu_agent.py) |
| [03-格物宗师-质量官/](03-格物宗师-质量官/README.md) | 格物·宗师 · 质量官 | `validate` / `review_code` | [gewu_zongshi_agent.py](03-格物宗师-质量官/gewu_zongshi_agent.py) |
| [04-创想灵韵-创意官/](04-创想灵韵-创意官/README.md) | 创想·灵韵 · 创意官 | `polish_report` / `brainstorm_ideas` / `generate_marketing_copy` / `visualization_suggestion` | [chuangxiang_lingyun_agent.py](04-创想灵韵-创意官/chuangxiang_lingyun_agent.py) |
| [05-言启千行-导航员/](05-言启千行-导航员/README.md) | 言启·千行 · 导航员 | `run`（8类意图路由） / `format_output` | [yanqi_qianhang_agent.py](05-言启千行-导航员/yanqi_qianhang_agent.py) |
| [06-语枢万物-思考者/](06-语枢万物-思考者/README.md) | 语枢·万物 · 思考者 | `analyze`（四段式） / `decompose_problem` | [yushu_wanwu_agent.py](06-语枢万物-思考者/yushu_wanwu_agent.py) |
| [07-预见先知-预言家/](07-预见先知-预言家/README.md) | 预见·先知 · 预言家 | `full_forecast` / `qualitative_analysis` / `risk_warning` | [yujian_xianzhi_agent.py](07-预见先知-预言家/yujian_xianzhi_agent.py) |
| [08-知遇伯乐-推荐官/](08-知遇伯乐-推荐官/README.md) | 知遇·伯乐 · 推荐官 | `build_user_profile` / `recommend_content` / `plan_growth_path` / `optimize_experience` | [zhiyu_bole_agent.py](08-知遇伯乐-推荐官/zhiyu_bole_agent.py) |
| [90-公共RAG-知识库/](90-公共RAG-知识库/README.md) | 公共RAG · 共享记忆 | `insert_documents` / `search` / `batch_import_from_nas` | [milvus_retriever.py](90-公共RAG-知识库/milvus_retriever.py) |
| [91-A2A-通信协议/](91-A2A-通信协议/README.md) | A2A · 通信底座 | `build_message` / AgentRegistry / AsyncOrchestrator | [a2a_protocol.py](91-A2A-通信协议/a2a_protocol.py) |
| [99-编排引擎-全链路闭环/](99-编排引擎-全链路闭环/README.md) | 编排引擎 · 九步总装 | `execute(user_input, user_id, scene)` | [ai_family_orchestrator.py](99-编排引擎-全链路闭环/ai_family_orchestrator.py) · [drama_stage_adapter.py](99-编排引擎-全链路闭环/drama_stage_adapter.py) |

## 二、源头资源地图

| 资源 | 路径 |
| ---- | ---- |
| 组件可运行事实源（13 平移件 + 冒烟脚本） | `../../../yyc3-ai-agent-archive/components/` |
| 上游网关侧 Agent 实现（上游同步域） | `../../../yyc3-0379-world/core/agents/` |
| Skills 技能库框架（11→13 域，本目录新篇） | [YYC3-AI-Family-Skills技能库框架目录.md](YYC3-AI-Family-Skills技能库框架目录.md) |
| 漫剧编排方案（源文档，已更新至 v1.1.0） | `../YYC3-03-AI漫剧智能体编排方案.md` |

## 三、查阅路径建议

1. **首次了解**：本 INDEX → 总纲 §1 总体设计架构 → §2 8Agent 全量定义总表
2. **接口开发**：总纲 §4 功能模块/错误码 → 组件库对应目录 `API.md`
3. **漫剧落地**：对齐版 §3 六大阶段 → §2.3 九步映射 → 四步实施
4. **运行调试**：总纲 §5 九步闭环 / §7 降级矩阵 → 代码库可运行包

## 四、变更历史

| 版本 | 日期 | 说明 |
| ---- | ---- | ---- |
| v1.0.0 | 2026-09-24 | 建立目录：全量闭环架构总纲 + YYC3-03 对齐版归档 + 组件库 README 副本 |
| v1.1.0 | 2026-09-24 | 补齐 12 个 Agent 专属子目录（README+API+代码 三位一体），新增子目录索引，本目录升级为自包含架构资料包 |
| v1.2.0 | 2026-09-24 | 闭环审核：编排引擎升级 v2.1（scene 分支/RAG 降级/质检复检/trace 透传/真并行），99 目录新增 drama_stage_adapter.py（漫剧六阶段状态机+工具网关桩），总纲补录 §9 审核报告与行业对标 |
| v1.3.0 | 2026-09-26 | 事实源分层治理：作废「唯一事实源」幽灵路径（YYC3-多端部署-Agent代码/ 本仓不存在），改为三层声明（本目录=架构规范 / agent-archive/components/=可运行代码 / 0379-world/core/agents/=上游同步域）；§源头资源地图改指实况路径；新增 YYC3-AI-Family-Skills技能库框架目录.md（13 域 44 技能）；YYC3-03 对齐版标注为 docs 根原版的归档副本 |
| v1.4.0 | 2026-09-27 | M2 收尾组件入库：components 新增 prompt_runtime.py（prompt.md 装载运行时，TC-G2-008）与 orchestrator_events.py（步骤事件埋点，TC-G2-009），平移件计 13→15；编排引擎接入每步埋点（redis 不可达自动降级 JSONL，两份拷贝同步） |

---
<p align="center">
  🌹 <b>YYC³ AI Family</b> · 人从众曌众从人 · 亦师亦友亦伯乐<br>
  <sub>永久开源 · 感恩前行 · matrix.yyc3.top</sub>
</p>
