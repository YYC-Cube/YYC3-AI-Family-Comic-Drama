---
file: YYC3-AI-Family-Skills技能库框架目录.md
description: YYC³ AI Family Skills 技能库框架目录 — 以 8 Agent 组件库编号同构的技能分层体系（结合四仓库实况与 G 门禁制定）
author: YanYuCloudCube Team <admin@0379.email>
version: v1.0.0
created: 2026-09-26
updated: 2026-09-26
status: active
tags: [Skills],[技能库],[Agent],[漫剧生产],[门禁]
category: architecture
language: zh-CN
audience: developers,architects,ai-agents
complexity: advanced
related_docs: YYC3-AI-Family-Agent-全量闭环架构总纲.md,../../YYC3-03-AI漫剧智能体编排方案.md,../../YYC3-08-项目落地架构与模块实现策略总览.md,../../YYC3-60-测试与验收执行手册.md,../../YYC3-AI-Family-Comic-Drama-完整版文件树.md
---

<!--
  ============================================================
  YYC³ AI Family — 人从众曌众从人
  亦师亦友亦伯乐 · 一言一语一协同
  ============================================================
-->

# YYC³ AI Family Skills 技能库框架目录

> **文档定位**：为 8 Agent 组件库（本目录 12 子目录三位一体）配套制定**技能（Skill）层框架目录**。组件库回答「Agent 是谁、接口是什么」，技能库回答「Agent 具体怎么干活的技能清单是什么、每个技能怎么验收」。目录编号与组件库 1:1 同构，落实「目录即架构、结构即流程」。
> **制定依据（实况基线 2026-09-26）**：G1 验收 4 BLOCKED / 2 PARTIAL PASS；组件库降级冒烟 11/11 PASS；四仓库已拆分推送；上游代码已拉取（0379-world 网关 1.68 万行 / archive TS 编排族 1.57 万行 / manju 前端 3600 行 / H3 引擎 2.4 千行）；依赖（openai/pymilvus/redis/insightface 等）未安装，全链路仅降级模式验证过。

---

## 一、设计原则（六条）

| # | 原则 | 说明 |
| - | ---- | ---- |
| 1 | **编号同构** | 技能域目录编号与组件库完全对应（00 公共基座 → 01~08 八成员 → 90 RAG → 91 A2A → 95 验收门禁 → 99 编排引擎），一个 Agent 一个技能域，零翻译成本 |
| 2 | **一技能一契约** | 每技能目录必含 `SKILL.md`（触发条件/输入输出契约/依赖/验收锚点），可含可执行脚本；契约字段对齐组件库 API.md 风格 |
| 3 | **桩先行** | 每个技能必须先具备降级/桩模式可冒烟（对齐 G2-004「降级正向验收」文化），再追求真实链路；硬件/模型不可达不算缺陷，BLOCKED 留证 |
| 4 | **门禁挂锚** | 每技能声明其验收锚点（对应 YYC3-60 的 TC 编号或 G 门禁），无锚点技能不得注册 |
| 5 | **分级落地** | P0（M1-M2 必需）→ P1（M3 视听）→ P2（M4 样片）→ P3（M5 运营），与 YYC3-08 §四 优先级一致；INDEX 中标注 |
| 6 | **单一事实源** | 技能实现落位四仓库（对齐完整版文件树），本目录只登记「技能 ↔ 仓库路径 ↔ 组件 ↔ 门禁」映射，不在 docs 里复制代码 |

---

## 二、技能库框架目录总树

```text
skills/                                        # 技能库根（建议落位 yyc3-ai-agent-archive/skills/）
├── README.md                                  # 技能库总规范：注册流程/命名/契约模板/分级/验收纪律
├── INDEX.md                                   # 技能总索引：名称↔Agent↔门禁↔仓库路径↔P级
│
├── 00-公共基座/                               # 全体 Agent 共享（对应 base_agent.py）
│   ├── llm-call/          [P0]                # 统一 LLM 调用：网关 base_url 单入口 + mock 降级（锚点 TC-G1-002）
│   ├── nas-path/          [P0]                # /mnt/nas 路径归一与三端校验（锚点 TC-G1-003/004）
│   ├── audit-log/         [P0]                # 审计留痕：trace_id 关联 + stream:audit:log / NAS RAID1 落盘
│   ├── env-config/        [P0]                # .env.example 模板 + 密钥零入库校验（.gitignore 红线）
│   └── acceptance-evidence/ [P0]              # 验收留证三件套（命令原文+JSON+trace_id）归档
│
├── 01-元启天枢/                               # 决策中枢域
│   ├── five-step-decision/ [P0]               # 五步决策法：问题定义→信息→≥3方案→加权评分→推荐
│   ├── plan-tasks/        [P0]                # 六阶段任务分解 → 生成工单（锚点 TC-G2-001 综合场景）
│   └── capacity-schedule/ [P2]                # 双 DGX 算力分配 / 昼夜错峰排产（preview/quality 标签路由）
│
├── 02-智云守护/                               # 安全官域
│   ├── input-screening/   [P0]                # 输入三级过滤：注入→PII→合规（锚点 TC-G2-003 场景D拦截）
│   ├── output-audit/      [P0]                # 输出审计与脱敏（锚点 steps.output_audit）
│   ├── consistency-check/ [P1]                # 人物一致性/画面崩坏校验 + 不合格打回（对接 anchor_guard）
│   └── content-compliance/[P1]                # 版权校验 + 微短剧备案合规预检（风险登记册 #4）
│
├── 03-格物宗师/                               # 质量官域
│   ├── four-dim-validate/ [P0]                # 四维质检（数值/逻辑/溯源/结构，≥80 红线，锚点 TC-G2-005）
│   ├── fact-trace/        [P0]                # RAG 溯源核查：无 [来源：] 断言标 unverified（幻觉率<3%）
│   └── storyboard-schema-check/ [P0]          # storyboard.v1.json 12 字段 Schema 校验（锚点 TC-G2-007）
│
├── 04-创想灵韵/                               # 创意官域
│   ├── ip-design/         [P0]                # 人设/画风/世界观（Character DNA 字典，锚点资产记忆）
│   ├── prompt-engineering/[P1]                # 分镜提示词工程 + 负面清单（对接 prompt_engine）
│   ├── style-keeping/     [P1]                # 风格种子/LUT/色彩配置持久化（对接 style_keeper）
│   └── keyframe-review/   [P2]                # 关键帧终审 + 重绘建议（对接 face_library 特征比对）
│
├── 05-言启千行/                               # 导航员域
│   ├── intent-routing/    [P0]                # 意图识别路由：通用 8 类 + 漫剧 4 类扩展（总纲 §9.3 遗留项）
│   ├── tool-gateway/      [P0]                # DramaToolGateway 桩→实：ComfyUI/H3/SyncNet 对接（锚点 A8）
│   ├── batch-submit/      [P2]                # 批量任务提交 + 异常分级重试（轻/中/重）
│   └── script-dev/        [P1]                # 生产自动化脚本开发（nightly_run.sh / init_nas_path.sh 维护）
│
├── 06-语枢万物/                               # 思考者域（剧本分镜工程师）
│   ├── novel-split/       [P0]                # 小说清洗/章节拆分/剧情要素抽取（对接 script_engine）
│   ├── episode-plan/      [P0]                # 分集规划 + 流量钩子植入（对接 hook_detector）
│   └── storyboard-gen/    [P0]                # 标准化分镜生成：12 字段 JSON（锚点 TC-G2-007）
│
├── 07-预见先知/                               # 预言家域（运营优化分析师）
│   ├── hit-forecast/      [P2]                # 爆款潜质预测（95%CI 定量 + LLM 定性）
│   ├── ops-data-collect/  [P2]                # 多平台播放数据采集（对接 feedback/collector）
│   └── pace-diagnosis/    [P3]                # 节奏诊断 → 反哺 hook_detector 参数（数据闭环）
│
├── 08-知遇伯乐/                               # 推荐官域（产能资源管理者）
│   ├── capacity-profile/  [P2]                # 产能画像与效能分析（对接项目进度/监控数据）
│   ├── asset-recommend/   [P2]                # Seed/LoRA/模板复用推荐（match_score + 理由链）
│   └── asset-deposit/     [P2]                # 优质资产自动沉淀 → NAS assets/ + 注册 Skill（资产闭环）
│
├── 90-公共RAG/                                # 共享记忆域（对应 milvus_retriever.py）
│   ├── rag-retrieve/      [P0]                # 检索 + [来源：] 注入 + min_score=0.6 红线 + 降级直答（锚点 TC-G2-004）
│   └── kb-import-nas/     [P1]                # NAS 文档批量入库管道（OCR→embed→Milvus）
│
├── 91-A2A/                                    # 通信底座域（对应 a2a_protocol.py）
│   ├── a2a-message/       [P0]                # 消息封套 10 字段 + trace_id 全链透传（锚点 TC-G2-009）
│   ├── agent-registry/    [P0]                # Agent Card 注册/心跳/剔除改派（30s/90s）
│   └── a2a-v1-mapping/    [P1]                # 向 A2A v1.0 标准 Agent Card 映射（升级不替换，遗留项②）
│
├── 95-验收门禁/                               # 质量门禁域（新增，组件库无对应件）
│   ├── gate-runner/       [P0]                # TC 用例执行器：G1/G2 用例批量跑 + PASS/FAIL/BLOCKED 判定
│   ├── gate-report/       [P0]                # 门禁报告生成（对齐 YYC3-60 §六 留证模板格式）
│   └── regression-anchor/ [P0]                # 回归锚点守护：G2-004/005 必测，FAIL 即回退引擎版本
│
└── 99-编排引擎/                               # 全链路总装域（对应 ai_family_orchestrator.py + drama_stage_adapter.py）
    ├── scene-branch/      [P0]                # ReAct-C 场景分支 A-F 裁剪执行（锚点 TC-G2-002）
    ├── stage-adapter/     [P0]                # 六阶段状态机 run/rewind/snapshot（锚点 TC-G2-006）
    ├── qc-rework-loop/    [P0]                # 质检→重绘→复检闭环 ≤2 轮（锚点 TC-G2-005）
    └── nightly-batch/     [P2]                # 昼夜错峰批量流水线编排（对接 nightly_run.sh）
```

> **合计**：13 个技能域 / 44 个技能（P0×27、P1×7、P2×9、P3×1）。P0 技能全部可在当前无 NAS/DGX 环境下降级冒烟，是解锁 G2 的最小技能集。

---

## 三、SKILL.md 契约模板（每个技能目录必备）

```markdown
---
skill: <kebab-case 技能名>
domain: <所属技能域，如 06-语枢万物>
owner_agent: <主责 Agent，如 语枢·万物>
priority: P0 | P1 | P2 | P3
version: v0.1.0
status: stub | degraded-ok | verified   # 桩 → 降级可跑 → 真实链路验证
---

# <技能名>

## 触发条件
<什么情况下编排引擎/上层 Agent 调用本技能>

## 输入契约
| 参数 | 类型 | 必填 | 说明 |

## 输出契约
| 字段 | 类型 | 说明 |
（含错误码：沿用 YYC3-AGT-4xxx/5xxx 体系）

## 依赖
上游组件（组件库目录）/ 模型 / 硬件 / 仓库落位路径

## 降级模式
<依赖不可达时的桩行为——必须可冒烟>

## 验收锚点
TC-G?-???（YYC3-60）｜失败处置：BUG-G?-?? 缺陷单
```

---

## 四、技能 ↔ 组件 ↔ 仓库 ↔ 门禁 映射（P0 最小集）

| 技能 | 依赖组件（本目录） | 实现落位（仓库路径） | 验收锚点 |
| ---- | ------------------ | -------------------- | -------- |
| llm-call | 00-公共基座/base_agent | agent-archive/components/ + 0379-world core/api | TC-G1-002 |
| nas-path | 00-公共基座 | manju-studio/scripts/init_nas_path.sh + 0379-world app/api/middleware/path_normalize.py | TC-G1-003/004 |
| input-screening / output-audit | 02-智云守护 | agent-archive/components/zhiyun_shouhu_agent.py | TC-G2-003 |
| four-dim-validate / fact-trace | 03-格物宗师 | agent-archive/components/gewu_zongshi_agent.py | TC-G2-005 |
| intent-routing | 05-言启千行 | agent-archive/components/yanqi_qianhang_agent.py（待扩展漫剧意图） | TC-G2-001 |
| novel-split / episode-plan / storyboard-gen | 06-语枢万物 | manju-studio backend/modules/script_engine + storyboard_engine | TC-G2-007 |
| rag-retrieve | 90-公共RAG | agent-archive/components/milvus_retriever.py | TC-G2-004 |
| a2a-message / agent-registry | 91-A2A | agent-archive/components/a2a_protocol.py | TC-G2-009 |
| scene-branch / qc-rework-loop | 99-编排引擎 | agent-archive/components/ai_family_orchestrator.py | TC-G2-002/005 |
| stage-adapter | 99-编排引擎 | agent-archive/components/drama_stage_adapter.py | TC-G2-006 |
| gate-runner / gate-report | 95-验收门禁 | scripts/（根仓）+ docs/G1-验收记录 模板 | 全门禁 |

---

## 五、实施步骤（三步走）

1. **建库（0.5 天）**：在 `yyc3-ai-agent-archive/skills/` 按上述目录树建骨架，每技能先落 `SKILL.md`（status=stub），INDEX 登记。
2. **契约填充（1 天）**：从组件库 13 个 .py 的现有函数签名反填输入输出契约；漫剧专属技能（storyboard-gen 等）从 `agents/*/prompt.md` 的输出契约 JSON Schema 反填。
3. **降级冒烟（1 天）**：扩展现有 `smoke_test_degraded.py` 为按技能域分组的冒烟矩阵，P0 技能 27 个全绿（或明确 STUB 留证）后即视为 G2 技能面就绪，转入 TC-G2 用例执行。

---

## 六、变更历史

| 版本 | 日期 | 变更内容 | 作者 |
| ---- | ---- | -------- | ---- |
| v1.0.0 | 2026-09-26 | 创建：基于全维度对比分析（12 主文档 + 组件资料包 + 四仓库实况 + G1 验收留证）制定技能库框架目录，11 域 36 技能，含契约模板、P0 映射表与三步实施 | YanYuCloudCube Team |

---

<div align="center">

🌹 **YYC³ AI Family** · 人从众曌众从人 · 亦师亦友亦伯乐 · 一言一语一协同

**© 2025-2026 YanYuCloudCube™. All Rights Reserved.**

</div>
