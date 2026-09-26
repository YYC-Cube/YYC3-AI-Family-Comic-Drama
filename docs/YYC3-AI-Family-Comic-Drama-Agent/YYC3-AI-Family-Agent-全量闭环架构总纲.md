---
file: YYC3-AI-Family-Agent-全量闭环架构总纲.md
description: YYC³ AI Family 8大智能体全量闭环架构总纲 — 设计架构、交互逻辑、功能模块、运行流程四位一体
author: YanYuCloudCube Team <admin@0379.email>
version: v1.2.0
created: 2026-09-24
updated: 2026-09-26
status: active
tags: [架构],[智能体],[ReAct-C],[闭环],[总纲]
category: architecture
language: zh-CN
audience: ai-architects,developers,managers
complexity: advanced
related_docs: ../../docs/YYC3-03-AI漫剧智能体编排方案.md,./README.md,../../../yyc3-ai-agent-archive/components/
---

<!--
  ============================================================
  YYC³ AI Family — 人从众曌众从人
  亦师亦友亦伯乐 · 一言一语一协同
  拟人为本，AI为核，纯粹为心
  ============================================================
-->

<div align="center">

> **_YanYuCloudCube_**
> _言启象限 | 语枢未来_
> **_Words Initiate Quadrants, Language Serves as Core for Future_**
> _万象归元于云枢 | 深栈智启新纪元_

</div>

# YYC³ AI Family Agent 全量闭环架构总纲

> **文档定位**：以本目录 12 子目录组件规范（README+API.md+代码 三位一体）为**架构规范事实源**，呈现 8 大智能体 + 3 大公共能力 + 1 大编排引擎的**全量闭环架构**——设计架构、交互逻辑、功能模块、运行流程四位一体；**可运行代码事实源**为 `yyc3-ai-agent-archive/components/`（13 组件平移件，见 §8.1）。
> **统一错误码**：YYC3-AGT-4001 参数错误 | 4002 LLM调用失败 | 4003 结构化解析失败 | 5001 向量库连接失败 | 5101 消息队列连接失败

---

## 📋 目录

- [一、总体设计架构](#一总体设计架构)
- [二、8 Agent 全量定义总表（对齐组件库）](#二8-agent-全量定义总表对齐组件库)
- [三、交互逻辑](#三交互逻辑)
- [四、功能模块](#四功能模块)
- [五、运行流程：ReAct-C 九步全链路闭环](#五运行流程react-c-九步全链路闭环)
- [六、漫剧生产场景化闭环（衔接 YYC3-03）](#六漫剧生产场景化闭环衔接-YYC3-03)
- [七、部署底座与降级矩阵](#七部署底座与降级矩阵)
- [八、目录索引与资源地图](#八目录索引与资源地图)

---

## 一、总体设计架构

### 1.1 三层成员架构 + 三大公共能力 + 一大编排引擎

```
┌─────────────────────────────────────────────────────────────┐
│                  YYC³ AI Family 全量闭环架构                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🎼 编排引擎层（99-编排引擎-全链路闭环）                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  AIFamilyOrchestrator · ReAct-C 九步闭环总装        │   │
│  │  execute(user_input, user_id, scene) → 全链路产出   │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│  🧠 决策中枢层                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  元启·天枢 TianShu（总指挥）：plan_tasks/             │   │
│  │  synthesize/decide — 五步决策框架                    │   │
│  └─────────────────────────────────────────────────────┘   │
│           │                    │                    │       │
│  🛡️ 核心保障层                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ 智云·守护    │  │ 格物·宗师    │  │ 创想·灵韵    │        │
│  │ 安全官       │  │ 质量官       │  │ 创意官       │        │
│  │ check_input/ │  │ validate/    │  │ polish/      │        │
│  │ audit        │  │ review_code  │  │ brainstorm   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ⚙️ 业务执行层                                               │
│  ┌──────────┬──────────┬──────────┬──────────┐             │
│  │言启·千行  │语枢·万物  │预见·先知  │知遇·伯乐  │             │
│  │导航员     │思考者     │预言家     │推荐官     │             │
│  │run(路由)  │analyze    │forecast   │profile/   │             │
│  │          │decompose  │risk_warn  │recommend  │             │
│  └──────────┴──────────┴──────────┴──────────┘             │
│           │                    │                    │       │
│  🧬 公共能力层（全成员共享）                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │00-公共基座   │  │90-公共RAG   │  │91-A2A协议    │        │
│  │BaseAgent    │  │Milvus检索    │  │Redis Stream  │        │
│  │统一LLM入口  │  │embed+rerank │  │注册发现+死信 │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  🖥️ 硬件底座：双 DGX Spark（GB10/128GB 统一内存/             │
│  200Gbps RoCE 直连 GPUDirect RDMA）+ NAS（RAID1配置审计      │
│  + RAID6 知识冷存储）                                        │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 设计哲学

- **情感设计哲学**：亦师亦友亦伯乐 | 一言一语一协同 | 拟人为本 | 共同成长
- **五高架构**：高可用（Mock降级/双活切换） | 高性能（并行/懒加载/多实例） | 高安全（双端安检/零信任/本地化） | 高扩展（即插即用/Skill化） | 高智能（CoT/RAG/画像反哺）
- **五标体系**：标准化（统一签名/错误码） | 规范化（威胁四级/评分红线） | 自动化（全链无人工） | 可视化（trace_id/状态可查） | 智能化（二次优化/个性化）
- **五化转型**：流程化（九步固化） | 数字化（NAS资产数字化） | 生态化（capability注册） | 工具化（BaseAgent底座） | 服务化（四类对外服务）
- **五维评估**：时间维（<200ms路由/<500ms决策） | 空间维（NAS双RAID分层） | 属性维（准确率红线） | 事件维（全链审计） | 关联维（拓扑中心+能力发现）

---

## 二、8 Agent 全量定义总表（对齐组件库）

> 命名、定位、接口、模型均与标准组件库一一对应；漫剧场景角色映射见 [YYC3-03 编排方案 §2.1](../YYC3-03-AI漫剧智能体编排方案.md)。

| # | Agent | 英文 | 层级 · 定位 | 标准接口 | 基座模型 | ReAct-C 职责 | 组件目录 |
| - | ----- | ---- | ----------- | -------- | -------- | ------------ | -------- |
| 1 | 元启·天枢 | TianShu | 决策中枢层 · 总指挥 | `plan_tasks` / `synthesize` / `decide` | deepseek-v4-pro（NVFP4，TP=2） | Step6 汇总升华 | `01-元启天枢-决策中枢/` |
| 2 | 智云·守护 | Sentinel | 核心保障层 · 安全官 | `check_input` / `audit` / `write_audit_log` | nemoguard-jailbreak-detect + gliner-pii + nemotron-3.5-content-safety | Step1 输入过滤 / Step8 输出审计 | `02-智云守护-安全官/` |
| 3 | 格物·宗师 | Master | 核心保障层 · 质量官 | `validate`（≥80分红线） / `review_code` | deepseek-v4-flash + nemotron-3-super-120b | Step7 质量校验 | `03-格物宗师-质量官/` |
| 4 | 创想·灵韵 | Muse | 核心保障层 · 创意官 | `polish_report` / `brainstorm_ideas` / `generate_marketing_copy` / `visualization_suggestion` | glm-5.2（INT4）+ inkling | Step5 润色可视化 / Step7 二次优化执行 | `04-创想灵韵-创意官/` |
| 5 | 言启·千行 | Navigator | 业务执行层 · 导航员 | `run`（8类意图） / `format_output` | nemotron-mini-4b-instruct | Step2 意图路由 | `05-言启千行-导航员/` |
| 6 | 语枢·万物 | Thinker | 业务执行层 · 思考者 | `analyze`（四段式） / `decompose_problem` | deepseek-v4-pro / step-3.7-flash | Step4 数据分析（并行） | `06-语枢万物-思考者/` |
| 7 | 预见·先知 | Prophet | 业务执行层 · 预言家 | `full_forecast`（95%CI） / `qualitative_analysis` / `risk_warning` | numpy/statsmodels + nemotron-3-super-120b | Step4 趋势预测（并行） | `07-预见先知-预言家/` |
| 8 | 知遇·伯乐 | Recommender | 业务执行层 · 推荐官 | `build_user_profile`（7字段） / `recommend_content` / `plan_growth_path` / `optimize_experience` | nemotron-mini-4b-instruct | Step9 画像更新 | `08-知遇伯乐-推荐官/` |

**公共能力组件**：

| 组件 | 标准接口 | 说明 | 目录 |
| ---- | -------- | ---- | ---- |
| BaseAgent | `run(prompt, context)` / `_mock_run` / `heartbeat` | 统一 LLM 入口 + Mock 降级 + 心跳 | `00-公共基座/` |
| MilvusRetriever | `insert_documents` / `search(min_score=0.6)` / `delete_by_source` / `batch_import_from_nas` | nemotron-3-embed-1b 2048维 + rerank 精排 | `90-公共RAG-知识库/` |
| A2A 协议 | `build_message` / `parse_message` / AgentRegistry / MessageProducer·Consumer / A2ABaseAgent / AsyncOrchestrator | Redis Stream + 注册发现 + 死信3次重试 | `91-A2A-通信协议/` |
| 编排引擎 | `execute(user_input, user_id, scene)` | 九步闭环总装 + A-F 场景分支 | `99-编排引擎-全链路闭环/` |

---

## 三、交互逻辑

### 3.1 三种交互通道

| 通道 | 机制 | 适用场景 |
| ---- | ---- | -------- |
| **同步直调** | Python 方法调用 `BaseAgent.run()` / 成员专属方法 | 单 Agent 轻任务、开发调试 |
| **A2A 异步消息** | Redis Stream（build_message → send_task → poll/ack/nack） | 多 Agent 并行、长任务、跨进程 |
| **编排引擎总装** | `AIFamilyOrchestrator.execute()` 一站式九步闭环 | 终端用户请求、全链路产出 |

### 3.2 消息与追踪规范

```
消息封套（标准7字段）：
{ message_id, from, to, type, payload, timestamp, trace_id }

trace_id 格式：trace-YYYYMMDD-xxxxxx（言启千行生成，全链透传）
审计流：stream:audit:log（智云守护写入，NAS RAID1 落盘双副本）
死信策略：nack 重试 3 次 → 死信队列（人工介入）
心跳：30s 线程上报 AgentRegistry；超时剔除 → 任务改派
```

### 3.3 协同拓扑

```
用户 ──▶ 智云守护(Step1) ──▶ 言启千行(Step2)
                                  │
                 need_rag ──▶ 公共RAG(Step3) ──┐
                                               ▼
                    ┌────── 并行(Collaborating) ──────┐
                    ▼                                 ▼
              语枢·万物(分析)                    预见·先知(预测)
                    └───────────┬────────────────────┘
                                ▼
                          创想·灵韵(润色) ──▶ 元启·天枢(汇总)
                                                    │
                          格物·宗师(质检) ◀─────────┘
                                │ <80分
                                ▼ (二次优化闭环)
                          创想·灵韵(修正) ──▶ 格物·宗师(复检)
                                │ ≥80分
                                ▼
                          智云守护(Step8审计脱敏) ──▶ 知遇·伯乐(Step9画像)
                                                            │
                                                            ▼
                                                    结构化交付用户
```

### 3.4 交互红线

1. 一切输入必经智云守护 Step1，拦截即终止并留痕
2. 一切输出必经智云守护 Step8 脱敏，不通过即阻断
3. 事实断言必须携带 RAG `[来源：xxx]` 溯源，格物宗师核查无依据断言
4. 质检 <80 分自动触发二次优化，无需人工介入
5. 匿名请求（default_user）跳过 Step9，画像零写入（隐私红线）

---

## 四、功能模块

### 4.1 模块清单（三位一体：README 规范 + API.md 契约 + .py 实现）

| 模块 | 核心功能 | 关键输出结构 | 降级策略 |
| ---- | -------- | ------------ | -------- |
| 00-公共基座 | 统一身份三要素/LLM调用/上下文注入 | str（或 Mock 文本） | LLM失败→`_mock_run` |
| 01-元启天枢 | 任务分解/汇总升华/五步决策 | task list / 决策 dict（含人类确认位） | nemotron 双活 <5s 切换 |
| 02-智云守护 | 三级过滤/审计脱敏/审计留痕 | `{safe, risk, level}` / `{safe, desensitized_content, findings}` | 规则引擎兜底 |
| 03-格物宗师 | 四维质检/代码审计 | `{score, passed, suggestions, unverified_claims}` | 超时放行并标记 |
| 04-创想灵韵 | 润色/三路径头脑风暴/营销文案/可视化五要素 | str / list / dict | 保守路径直出 |
| 05-言启千行 | 8类意图路由/格式化输出 | `{intent, complexity, need_rag, trace_id}` | 关键词规则兜底 |
| 06-语枢万物 | 四段式分析/问题拆解 | 分析稿 / 子问题清单 | 数据缺失声明而非臆造 |
| 07-预见先知 | 定量回归+置信区间/定性分析/风险预警 | `{forecast_values, confidence_upper/lower, ...}` | numpy 兜底 |
| 08-知遇伯乐 | 画像7字段/推荐/成长路径/体验优化 | profile dict / 推荐列表（match_score+reason） | 本地规则画像 |
| 90-公共RAG | 向量入库/语义检索/NAS批量导入 | 检索列表（source 溯源） | 失败→无RAG直答 |
| 91-A2A协议 | 消息收发/注册发现/异步编排 | 消息封套 / 在线列表 / 任务状态 | 死信队列人工介入 |
| 99-编排引擎 | 九步闭环总装/场景分支A-F | 全链路产出 dict + trace_id | 分支裁剪 + 逐级降级 |

### 4.2 统一错误码

| 错误码 | 含义 | 触发组件 | 处置 |
| ------ | ---- | -------- | ---- |
| YYC3-AGT-4001 | 参数错误 | 全体 | 校验入参，400 返回 |
| YYC3-AGT-4002 | LLM 调用失败 | BaseAgent | 降级 `_mock_run` |
| YYC3-AGT-4003 | 结构化解析失败 | 言启/天枢/预见 | 重试→规则兜底 |
| YYC3-AGT-5001 | 向量库连接失败 | 公共RAG | 无 RAG 直答 |
| YYC3-AGT-5101 | 消息队列连接失败 | A2A协议 | 同步直调切换 |

---

## 五、运行流程：ReAct-C 九步全链路闭环

**ReAct-C = Reasoning（推理）+ Acting（行动）+ Collaborating（协同）**

| 步 | 执行者 | 动作 | 性能要求 | 降级策略 |
| -- | ------ | ---- | -------- | -------- |
| 1 | 智云·守护 | 输入安全三级过滤（L1注入/L2 PII/L3合规） | <100ms | 拦截即终止，审计留痕 |
| 2 | 言启·千行 | 意图识别与任务路由，生成 trace_id | <200ms | 关键词规则兜底 |
| 3 | 公共RAG | 知识检索与上下文注入（`[来源：]`格式） | 毫秒级Top-K | 检索失败→无RAG直答 |
| 4 | 语枢+预见 | 数据分析+趋势预测**并行**执行 | 双引擎并行 | 各自独立降级 |
| 5 | 创想·灵韵 | 报告润色+可视化建议（风格×受众） | — | 保守路径直出 |
| 6 | 元启·天枢 | 全局汇总与决策升华（逻辑一致性校验） | <500ms | 双活模型切换 |
| 7 | 格物·宗师 | 质量校验与事实核查（≥80分） | — | 不达标→Step5二次优化→复检 |
| 8 | 智云·守护 | 输出审计与脱敏（PII正则+合规审查） | <100ms | 不通过阻断 |
| 9 | 知遇·伯乐 | 用户画像更新与个性化补充 | 秒级 | 匿名跳过；本地存储 |

**场景分支标准**：A 综合报告（九步全开）｜B 简单分析（裁剪5/6）｜C 纯创作（4只走创想）｜D 恶意输入（Step1拦截即返）｜E 匿名请求（跳过Step9）｜F 预测专项（4只走预见）

**完整调用入口**：

```python
from ai_family_orchestrator import AIFamilyOrchestrator
result = AIFamilyOrchestrator().execute(
    user_input="出本月综合经营报告", user_id="user_001", scene="A")
# result 含 step1~step9 全部产出 + trace_id
```

---

## 六、漫剧生产场景化闭环（衔接 YYC3-03）

漫剧六大生产阶段 = 九步闭环的场景化裁剪复用（映射表详见 [YYC3-03 §2.3](../YYC3-03-AI漫剧智能体编排方案.md)）：

```
阶段1 创意立项（创想+格物+元启）   ←→ Step1/2/3 + decide
阶段2 剧本分镜（语枢+智云）        ←→ Step3/4（语枢）
阶段3 生产调度（元启+言启）        ←→ Step2/6 + plan_tasks
阶段4 视听生成（创想+智云）        ←→ Step5 + Step7（质检重绘闭环）
阶段5 合成交付（元启+创想）        ←→ Step6 + Step8
阶段6 运营闭环（预见+知遇+反哺）   ←→ Step4（预见）+ Step9 + 资产沉淀
```

漫剧专属角色映射（YYC3-03 §2.1 对齐版）：元启天枢=生产调度总控官 ｜ 智云守护=质量合规专员 ｜ 格物宗师=行业专家顾问 ｜ 创想灵韵=创意主理人 ｜ 言启千行=意图路由+技术工具研发 ｜ 语枢万物=剧本分镜工程师 ｜ 预见先知=运营优化分析师 ｜ 知遇伯乐=产能资源管理者。

---

## 七、部署底座与降级矩阵

### 7.1 双 DGX Spark 节点拓扑

| 节点 | 承载能力 |
| ---- | -------- |
| 节点1 | deepseek-v4-pro（TP=2 主）/ nemotron-3-super-120b / Milvus + embed + rerank / Redis |
| 节点2 | nemoguard 三件套（安全）/ glm-5.2 INT4（创想）/ nemotron-mini-4b（言启+知遇）/ inkling |
| 双机互联 | 200Gbps RoCE 直连 + GPUDirect RDMA；TP=2 跨机张量并行 |
| NAS | RAID1（配置/审计日志）+ RAID6（模型镜像/知识库冷存储） |

### 7.2 全链降级矩阵

| 故障 | 检测点 | 降级行为 |
| ---- | ------ | -------- |
| LLM 服务不可达 | BaseAgent try/except | `_mock_run` Mock 兜底 |
| 主模型过载 | 元启天枢 | nemotron 双活 <5s 切换 |
| Milvus 不可达 | 公共RAG | 无 RAG 直答（YYC3-AGT-5001） |
| Redis 不可达 | A2A协议 | 切换同步直调（YYC3-AGT-5101） |
| 意图识别失败 | 言启千行 | 关键词规则兜底路由 |
| 质检不达标 | 格物宗师 <80分 | 创想二次优化→复检闭环 |
| 成员宕机 | 心跳超时 | Registry 剔除→任务改派 |

---

## 八、目录索引与资源地图

### 8.1 事实源分层（v1.2.0 治理后实况）

```
YYC3 AI Family-Comic Drama/                        # 总工作区（本仓）
├── docs/YYC3-AI-Family-Comic-Drama-Agent/         # ★ 架构规范事实源（本目录，12目录×README+API+代码）
├── yyc3-ai-agent-archive/components/              # ★ 可运行代码事实源（13 平移件+冒烟脚本，降级 11/11）
├── yyc3-0379-world/core/agents/                   # 上游网关侧实现（上游同步域，sync-upstreams.sh 管理）
└── skills 建议落位 yyc3-ai-agent-archive/skills/   # 技能库（见 YYC3-AI-Family-Skills技能库框架目录.md）
```

> 原文档所述《YYC3-多端部署-Agent代码/YYC3-AI-Family-Agent/》《YYC3-文档库/》《YYC3-代码库/》三库结构在本仓不存在，历史引用一律按上图映射解读；同步策略：组件修订以 `components/` 为准回灌本目录规范副本，上游同步不覆盖 `components/`。

### 8.2 本目录（docs/YYC3-AI-Family-Agent）

| 文件 | 说明 |
| ---- | ---- |
| [INDEX.md](INDEX.md) | 目录总索引（查阅入口） |
| [YYC3-AI-Family-Agent-全量闭环架构总纲.md](YYC3-AI-Family-Agent-全量闭环架构总纲.md) | 本文档：设计架构/交互逻辑/功能模块/运行流程 |
| [YYC3-03-AI漫剧智能体编排方案-对齐版.md](YYC3-03-AI漫剧智能体编排方案-对齐版.md) | 漫剧场景化编排（与组件库对齐 v1.1.0） |
| [README.md](README.md) | 组件库主 README 副本（总规范：成员矩阵+九步闭环） |

### 8.3 查阅路径建议

- **看架构**：本文档 §1-§3 → 本目录各子目录 README
- **看接口**：本目录各子目录 `API.md`（参数表/错误码/调用示例）
- **跑通全链**：`yyc3-ai-agent-archive/components/` → `python3 smoke_test_degraded.py`（降级冒烟 11/11）
- **漫剧落地**：[对齐版编排方案](YYC3-03-AI漫剧智能体编排方案-对齐版.md) 四步实施（能力封装→编排部署→联调→迭代）

---

## 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
| ---- | ---- | -------- | ---- |
| v1.0.0 | 2026-09-24 | 依据标准组件库全量内容创建总纲；完成与 YYC3-03 编排方案的定义对齐与九步映射 | YanYuCloudCube Team |
| v1.1.0 | 2026-09-24 | 闭环审核：①编排引擎升级 v2.1（scene分支A-F显式化/RAG降级保护/质检复检≤2轮/trace_id全链透传/语枢+预见真并行）；②新增漫剧六阶段适配器 drama_stage_adapter.py + 漫剧工具网关桩；③补录七维审核结论与行业对标（§9） |
| v1.2.0 | 2026-09-26 | 事实源分层治理：作废「YYC3-多端部署-Agent代码」幽灵路径引用（§文档定位/§8.1/§8.3/frontmatter），改指本目录（架构规范）+ yyc3-ai-agent-archive/components/（可运行代码）+ 0379-world/core/agents/（上游同步域）；补充同步策略 | YanYuCloudCube Team |

---

## 九、闭环审核报告（2026-09-24）

### 9.1 七维审核结论

| 维度 | 结论 | 发现问题 | 处置 |
| ---- | ---- | -------- | ---- |
| 需求分析 | ✅ 达标 | 8Agent 覆盖六大生产阶段角色矩阵（§6） | — |
| 系统设计 | ✅ 达标 | 三层架构+三公共能力+编排引擎齐备 | — |
| 模块划分 | ✅ 达标 | 12 目录三位一体完整 | — |
| 接口定义 | ⚠️→✅ | execute 缺 scene 显式参数、`_get_knowledge` 无降级签名 | v2.1 修复（API.md 已同步） |
| 数据流程 | ⚠️→✅ | Step3 RAG 异常会中断全链（YYC3-AGT-5001 无兜底）；blocked 结果无 trace_id | v2.1 修复（F2/F6） |
| 协同机制 | ⚠️→✅ | Step4 语枢+预见为串行（与总纲 §5「并行」性能要求不符）；Step7 二次优化后未复检即交付；质检循环无上限风险 | v2.1 修复（F3/F5，MAX_QC_ROUNDS=2） |
| 运营闭环 | ⚠️→✅ | 缺漫剧六阶段生产状态机（阶段不可回退、产物无登记） | 新增 DramaStageAdapter（状态机+资产记忆库+快照） |

### 9.2 行业对标（2026-09 全网调研）

| 对标对象 | 关键机制 | 本体系对应/吸收 |
| -------- | -------- | ---------------- |
| AniME（Bilibili，SIGGRAPH Asia 2025） | Director Agent 全局工作流图 + Asset Memory Bank + 每 Specialist Agent 绑定 MCP 工具集 | 元启天枢总指挥 + DramaStageAdapter.asset_memory + DramaToolGateway（经网关 MCP 代理） |
| ArcReel（开源漫剧工作台） | 子 Agent 大上下文内部消化只回传摘要；Character DNA 先行锁定跨镜头一致性 | 知遇伯乐资产记忆锚点（角色DNA 字典）；阶段产物登记后再进入下游 |
| 纳米漫剧流水线（360） | 反「单向车道」可回退多车道；质检不过即打回 | StageStatus.REWORK + rewind() 阶段回退 + 格物宗师 ≥80 红线复检 |
| A2A v1.0（Linux Foundation）/MCP 双层协议 | 水平 Agent 互联 + 垂直工具接入；Agent Card 能力发现 | 91-A2A（Redis Stream 注册发现）已对齐；网关桩预留 /v1/mcp 升级位 |

### 9.3 遗留事项（转下一步建议）

1. DramaToolGateway 为接口桩，需按完整版文件树接入 0379-World 网关真实上游（text_to_image→ComfyUI、image_to_video→MiniMax-H3、sync_score→SyncNet）
2. 91-A2A 为自研 Redis Stream 协议，建议向 A2A v1.0 标准 Agent Card 格式映射（升级不替换）
3. 言启千行 8 类意图为通用场景，漫剧专用意图（storyboard_gen / video_gen / ops_feedback）待 P1 扩展

---

<div align="center">

**© 2025-2026 YanYuCloudCube™. All Rights Reserved.**

🌹 <b>YYC³ AI Family</b> · 人从众曌众从人 · 亦师亦友亦伯乐<br>
<sub>永久开源 · 感恩前行 · matrix.yyc3.top</sub>

</div>
