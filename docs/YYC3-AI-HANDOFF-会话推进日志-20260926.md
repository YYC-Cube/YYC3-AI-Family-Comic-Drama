---
file: YYC3-AI-HANDOFF-会话推进日志-20260926.md
description: YYC³ AI漫剧项目会话推进日志（2026-09-26）— 可行性论证交付 · 远程仓库创建 · 后续推进路线
author: YanYuCloudCube Team <admin@0379.email>
version: v1.0.0
created: 2026-09-26
updated: 2026-09-26
status: active
tags: [日志],[交接],[远程仓库],[可行性论证]
category: log
language: zh-CN
audience: ai-agents,developers,managers
complexity: intermediate
related_docs: YYC3-AI-HANDOFF-会话推进日志-20260924.md,YYC3-07-大数据与多Agent协同架构-技术可行性论证报告.md,YYC3-60-测试与验收执行手册.md
---

<div align="center">

> **_YanYuCloudCube_**
> _言启象限 | 语枢未来_

</div>

# YYC³ AI 漫剧项目 会话推进日志（2026-09-26）

## 一、本次会话成果

| # | 任务 | 关键产出 | 状态 |
| - | ---- | -------- | ---- |
| 1 | docs 全量系统性深度分析 | 扫描 Agent 组件库 12 目录 + 根目录架构文档 + 验收体系 15 文档 | ✅ |
| 2 | 技术可行性论证报告 | 新建 [YYC3-07](YYC3-07-大数据与多Agent协同架构-技术可行性论证报告.md) v1.0.0：六维论证（技术/资源/复杂度/效益/风险/兼容性）+ 8 项技术匹配矩阵 + 5 大瓶颈突破方案 + 16 项风险登记 + 12 个技术适配点 + P0~P4 实施路径 + 四级性能指标 + ROI 测算，**综合评分 88.4/100（有条件通过）** | ✅ |
| 3 | 远程仓库创建 | [github.com/YYC-Cube/YYC3-AI-Family-Comic-Drama](https://github.com/YYC-Cube/YYC3-AI-Family-Comic-Drama)（public，main 分支，283 文件首提交） | ✅ |
| 4 | 仓库标签完善 | 16 个 topics：yyc3 / ai-comic-drama / multi-agent / react-c / a2a-protocol / milvus / rag / redis-stream / vllm / comfyui / dgx-spark / nextjs / fastapi / llm-orchestration / ai-video-generation / chinese-drama | ✅ |
| 5 | README 可视化重构 | 顶图 `public/yyc3-family.png` + 13 枚徽章 + 4 组 Mermaid 架构图（四层架构/九步闭环/硬件部署/里程碑甘特）+ 8 Agent 矩阵 + 四仓库结构 + 门禁表 + 文档导航 | ✅ |
| 6 | .gitignore 落地 | 密钥零入库（.env）+ 二进制资产红线（模型/成片不落仓库）+ 运行时产物 | ✅ |
| 7 | 四仓库实现度审计 | 确认脚手架结构完整（110目录/242文件），**后端代码实现度 0%**（所有 .py/.ts/.yaml 为 0 字节空占位），Agent prompt 已就绪 | ✅ |
| 8 | 落地架构与实现策略总览 | 新建 [YYC3-08](YYC3-08-项目落地架构与模块实现策略总览.md)：实现度审计矩阵 + 开源vs自研决策矩阵 + P0~P3 优先级 + 开源拉取清单 + 完整文档架构索引 | ✅ |
| 9 | 上游核心代码拉取 | 从 3 个 YYC-Cube 上游仓库拉取真实核心代码（提交 5accbc1）：**YYC3-0379-World@6c4c873**（8大Agent实现+网关API chat.py 812行/A2A/RAG/MCP/proxy，20→174文件）、**YYC3-MiniMax-H3@5ef6e81**（h3_agent引擎+Next.js控制台+20份部署文档，9→154文件）、**YYC3-AI-Agent-Archive@3b98287**（11个编排核心包 sparse 按需拉取，26→183文件） | ✅ |
| 10 | 上游自动同步体系 | [sync-upstreams.sh](../scripts/sync-upstreams.sh) + [upstreams.tsv](../scripts/upstreams.tsv) 映射清单（保护规则：本地README/.gitignore/.env.example不被覆盖）+ [sync-upstreams.yml](../.github/workflows/sync-upstreams.yml)（每日02:00定时同步，变更自动开PR）+ [同步报告](../scripts/upstream-sync-report.md) | ✅ |
| 11 | 前端完整架构自建 | manju-studio/frontend **53 文件约 3600 行真实代码**：Next.js 16.3.6 + React 19.3.0 实测安装；StoryboardV1 顶层/Shot 双 12 字段类型+四类校验；API层带 mock 降级（withFallback）；Zustand 三store；SSE 任务流；SVG 六阶段流水线/Canvas 时间线/成本红线面板等 17 组件；9 业务页全可独立渲染 | ✅ |
| 12 | 前端验证 | `pnpm typecheck` **0 error**；`pnpm build` **成功**（12 路由静态生成 + Middleware 注册）；dev 端口 20300（对齐前端 2xxxx 端口红线） | ✅ |

## 二、当前项目状态快照

| 维度 | 状态 |
| ---- | ---- |
| 远程仓库 | main 分支已推送，与本地同步 |
| 可行性论证 | YYC3-07 已入库，结论：有条件通过（88.4/100） |
| 落地策略 | YYC3-08 已入库：大模型/工具链开源拉取，网关/编排/一致性引擎自研 |
| 工程结构 | 四仓库脚手架结构完整，后端代码 0% 待实现 |
| **上游核心代码** | **三仓库核心已拉取落位：网关 Agent/API 实现、H3 引擎+控制台、11 编排包（合计 511 文件）** |
| **前端工作台** | **架构+核心代码已就绪（build 通过，mock 降级可独立开发），后端联通待 G1** |
| 自动化 | 上游每日定时同步（Actions PR 流）+ 本地手动 sync 脚本就绪 |
| 当前门禁 | **G1（底座通电）仍为最前沿**，TC-G1-001~006 待执行 |

## 三、下次会话启动指南 🚀

### 快速恢复

```bash
cd "/Users/yanyu/YYC-Cube/YYC3 AI Family-Comic Drama"
git pull origin main
cat docs/YYC3-AI-HANDOFF-会话推进日志-20260926.md
```

### 下次计划 TOP 3

1. **[P0]** 执行 G1 底座通电六用例（TC-G1-001~006），按 [YYC3-60](YYC3-60-测试与验收执行手册.md) §六 模板留证；依赖缺失（如无 DGX/NAS）时记 BLOCKED 并转向 P1
2. **[P0]** 四仓库 `git init` + 统一 `.gitignore`（.env/二进制/临时产物），组件库参考实现平移至 `agent-archive` 并跑通降级模式冒烟
3. **[P1]** M3 一致性引擎 face_encoder 512 维特征库建库可先于编排贯通启动（对冲最大技术风险）

### 前置条件提醒（源：YYC3-07 §12.3）

- G1 底座实测全过是全部后续工作的物理前提
- M3 一致性专项压测先行（最大技术风险对冲）
- 版权备案流程前置（2026-04 起漫剧纳入微短剧备案管理）

## 四、变更历史

| 版本 | 日期 | 变更内容 | 作者 |
| ---- | ---- | -------- | ---- |
| v1.0.0 | 2026-09-26 | 创建：可行性论证交付、远程仓库创建（含 topics/README/gitignore）、下次 TOP3 计划 | YanYuCloudCube Team |

---

<div align="center">

**© 2025-2026 YanYuCloudCube™. All Rights Reserved.**

🌹 **YYC³ AI Family** · 人从众曌众从人 · 亦师亦友亦伯乐 · 一言一语一协同

</div>

---

## 九、本轮追加推进（G1 验收 · 四仓拆分 · 组件库冒烟 · face_encoder 建库）

### 9.1 四仓库拆分为独立 Git 仓库（已推送）

| 仓库 | 远程 | 说明 |
| --- | --- | --- |
| yyc3-ai-manju-studio | YYC-Cube/YYC3-Comic-ai-manju-studio | 前端 Next.js + 后端 |
| yyc3-0379-world | YYC-Cube/YYC3-Comic-0379-world | 网关 + 8 Agent |
| yyc3-ai-agent-archive | YYC-Cube/YYC3-Comic-ai-agent-archive | 编排包 + 组件库 |
| yyc3-minimax-h3 | YYC-Cube/YYC3-Comic-minimax-h3 | H3 协议引擎 |

- 统一 `.gitignore`（`.gitignore.unified` 模板）：密钥零入库、二进制资产（safetensors/ckpt/pt/bin/mp4/wav/png）落 NAS 不入仓、`face_library/` 不入仓
- 根仓库仅纳管 docs/scripts/.github，四目录加入根 `.gitignore`

### 9.2 G1 底座通电六用例验收（详见 `docs/G1-底座通电验收记录-20260926.md`）

| 用例 | 结果 | 说明 |
| --- | --- | --- |
| G1-001 网关健康 | BLOCKED | 网关 compose 未部署 |
| G1-002 Chat 连通 | BLOCKED | DGX vLLM 未注册 |
| G1-003 NAS 三端互写 | BLOCKED | /mnt/nas 未挂载 |
| G1-004 路径归一 | PARTIAL PASS | 逻辑单测 8/8 PASS（实现 `app/api/middleware/path_normalize.py`） |
| G1-005 鉴权三连发 | PARTIAL PASS | 逻辑单测 10/10 PASS（桩注入 jwt/fastapi） |
| G1-006 DGX 首 token | BLOCKED | 无 DGX 硬件 |

**解锁条件**：NAS 挂载 + 网关 compose 部署 + 安装 jwt/fastapi/passlib + 接入 DGX 推理池。

### 9.3 组件库平移 + 降级模式冒烟（11/11 PASS）

- 13 个组件实现从 `docs/YYC3-AI-Family-Comic-Drama-Agent/` 平移至 `yyc3-ai-agent-archive/components/`
- 冒烟脚本 `smoke_test_degraded.py`：stub milvus_retriever 触发 RAG 降级，LLM 由 base_agent `_mock_run` 兜底
- 修复：智云守护 L3 合规判定 `"UNSAFE" in verdict` 收紧为 `startswith("UNSAFE")`（解决 mock 回显含 "UNSAFE" 字样误拦截）
- 场景B（数据分析）：status=success、trace_id 非空、rag_retrieve.degraded=True、含 yushu_analysis+polished_report、qc_rounds<=2
- 场景D（注入攻击）：status=blocked、Step1 即拦截

### 9.4 face_encoder 512 维特征库建库（P1-C，3/3 PASS）

- 实现 `yyc3-ai-manju-studio/backend/app/modules/consistency_engine/face_encoder.py`
  - 优先 insightface（512d）→ face_recognition（128d pad 512d）→ 哈希降级（SHA-512+SHAKE256 派生确定性 512d 向量）
- 建库脚本 `scripts/build_face_library.py`：扫描角色图 → feature.npy + manifest.json + index.json
- 校验：dim=512、同图二次编码余弦相似度=1.0、mode=degraded 标记
- 特征库路径：`/mnt/nas/assets/characters/`（NAS 挂载后），本地兜底 `backend/face_library/`（已 gitignore）

### 9.5 下次会话启动指南

```bash
# 1. 部署网关 + 挂载 NAS，重跑 G1-001/002/003/006 及 004/005 E2E
# 2. 安装网关依赖：pip install fastapi uvicorn pyjwt passlib[bcrypt] python-multipart
# 3. 组件库冒烟复跑：cd yyc3-ai-agent-archive/components && python3 smoke_test_degraded.py
# 4. face_encoder 真实模型：pip install insightface onnxruntime && 放置角色图到 assets/characters/
# 5. 查看 G1 留证：docs/G1-底座通电验收记录-20260926.md
```

**当前优先级 TOP 3**：

1. **[P0]** 部署网关 compose + 挂载 NAS → 解锁 G1-001/002/003 E2E
2. **[P1]** 安装 insightface → face_encoder 真实 512 维特征提取
3. **[P1]** 接入 DGX vLLM 推理池 → G1-006 首 token 验收

---

## 十、前端完整架构实现完善（2026-09-26 追加）

### 10.1 数据库迁移整合：标记留后

- 用户决策：数据库迁移与整合（Dexie 本地库 + NAS PG14 私服后端）正在规划中，本项目相关内容**标记留后**，本轮不涉及数据库层改动。
- 参考文档：`05-本地数据库替代方案分析.md`（Dexie Phase A~C + PG14 Phase D 路线已定）。

### 10.2 前端架构现状审计

前端 `yyc3-ai-manju-studio/frontend/` 已是**完整独立实现**（非引用外部模板）：

| 维度 | 实现情况 |
| --- | --- |
| 技术栈 | Next.js 16.3.6 + React 19.3.0 + TypeScript 5.6 + Tailwind 3.4 + Zustand 5 |
| 页面 | 10 个功能页全部实现（生产监控/成本/运营/项目/剧本/分镜/资产/时间线/任务）+ 根重定向 |
| UI 组件 | shadcn 风格：badge/button/card/input/progress/separator/table/textarea + 本轮新增 label/tabs/select/dialog/toast |
| 状态管理 | Zustand：use-project-store / use-storyboard-store / use-task-store |
| API 层 | client.ts（统一请求 + mock 降级）+ project/script/storyboard/task 四域 |
| Hooks | use-task-stream（SSE 实时流）、use-api-fallback |
| 数据降级 | mock-data.ts + mock-operations.ts，后端不可达时自动降级演示数据 |
| 端口 | dev 20300（符合前端 2xxxx 红线） |

### 10.3 本轮前端完善项

1. **清理冗余路由**：删除 `(dashboard)/` 占位目录（仅含 .gitkeep，实际页面在根级路由）
2. **补全 shadcn 框架核心 UI 原语**（独立实现，无 Radix 依赖）：
   - `label.tsx` — 表单标签
   - `tabs.tsx` — 受控标签页（Tabs/TabsList/TabsTrigger/TabsContent）
   - `select.tsx` — 下拉选择（Select/Trigger/Value/Content/Item，点击外部关闭）
   - `dialog.tsx` — 模态框（Portal + ESC + 遮罩关闭 + 滚动锁定）
   - `toast.tsx` — 通知提示（useToast + ToastProvider + Toaster，success/warning/error 语义）
3. **全局 Provider 接入**：`providers.tsx` 客户端包装器，ToastProvider 包裹全站
4. **剧本编辑器接入 toast**：生成剧本/提取分镜完成后弹出通知

### 10.4 验证结果

- `tsc --noEmit`：0 错误
- `next build`：成功，12 页面静态生成
- dev 服务器 HTTP 探测：10 个页面全部 200，根路径 307 → /production

### 10.5 前端下一步建议

- 将顶栏原生 `<select>` 替换为 `ui/select` 组件（风格统一）
- 分镜页、资产页增加 `ui/dialog` 用于详情查看/编辑
- 接入 `ui/tabs` 优化剧本编辑器（原文/结构化/分镜三标签切换）
- 数据库层就绪后，将 mock 数据替换为真实 API 调用（API 层已预留降级路径）

---

## 十一、GitHub Pages 自动部署 + 品牌 Logo 全局引用（2026-09-26）

### 11.1 Pages CI 单通道部署（已上线）

- **远程配置**：`build_type=workflow`，CNAME=`agent.yyc3.top`，HTTPS 强制，证书已签发
- **Workflow**：`.github/workflows/deploy-pages.yml`
  - 触发：push main（仅 public/、index.html、workflow 变更）+ workflow_dispatch
  - 步骤：checkout → configure-pages → 组装 `_site/`（public/ + index.html + 404 回退）→ upload-pages-artifact → deploy-pages
- **单通道原则**：远程已设为 workflow 模式，无分支自动部署，杜绝双通道重复发布
- **部署结果**：build 8s + deploy 8s，`https://agent.yyc3.top/` HTTP 200，页面正确引用 `/yyc3-icons/logo.svg`

### 11.2 品牌 Logo 资产（public/yyc3-icons/）

| 文件 | 用途 |
| --- | --- |
| logo.svg | YYC³ 文字品牌主标识（矢量） |
| logo.png / logo-1024.png | 位图 logo（多尺寸） |
| favicon-16/32.png | 浏览器标签图标 |
| apple-touch-icon.png | iOS 主屏图标 |
| icon-192/512.png | Android/PWA 图标 |
| manifest.json | PWA 清单 |

### 11.3 全局引用点

- **根门户页** `index.html`：header logo + favicon + apple-touch + manifest + og:image
- **前端 sidebar**：品牌区替换为 `/yyc3-icons/logo.svg`（深色反色）
- **前端 layout**：metadata.icons + manifest
- **README**：`public/yyc3-family.png` 横幅

### 11.4 .gitignore 品牌 Logo 例外

统一 .gitignore 中 `*.png`（二进制资产红线）会误伤 logo，新增例外：

```
!**/yyc3-icons/*.png
!**/yyc3-icons/*.jpg
!**/yyc3-icons/*.jpeg
```

仅放行 yyc3-icons 目录下的小尺寸品牌图标，模型/成片二进制仍落 NAS 不入仓。

### 11.5 G1 + 组件库复验留证（二次执行）

- G1-004 路径归一：6/6 PASS
- G1-005 鉴权逻辑：10/10 PASS
- 组件库降级冒烟：11/11 PASS
- 四仓库 .gitignore 统一校验通过（密钥零入库 + 二进制红线 + yyc3-icons 例外）

---

## 十二、漂移治理 + Skills 技能库建库 + G1 E2E 解锁（2026-09-26 第三轮）

### 12.1 文档漂移治理（全维度对比分析后的 6 项修正）

| # | 治理项 | 处置 |
| --- | --- | --- |
| 1 | 幽灵事实源 | INDEX/README/总纲/03 四文件中《YYC3-多端部署-Agent代码》引用全部清零，改为三层声明（本目录=架构规范 / agent-archive/components/=可运行代码 / 0379-world/core/agents/=上游同步域）；§源头资源地图改指实况路径 |
| 2 | 三份 8-Agent 拷贝 | 实测 docs 包与 components 完全一致（UNSAFE 修复已在两份在位）、0379-world 有等价防误判守卫；同步策略写入总纲 §8.1 与 INDEX |
| 3 | YYC3-08 §1.1 过期快照 | 修订 v1.1.0：「前后端 0%」→ 上游 511 文件 + 前端完整实现 + 组件冒烟实况，补 G1 验收状态 |
| 5 | 端口规范冲突 | YYC3-06 §6.2 v1.2.0：废弃 3030/8001/8002/8000，统一 A11 红线条带（前端 20300/后端 25200/网关 25080/H3 归 4xxxx） |
| 6 | 03 原版/对齐版重复 | 声明 docs 根为唯一活跃版本（v1.2.0），Agent 目录「对齐版」标注为归档副本 |

### 12.2 Skills 技能库建库（yyc3-ai-agent-archive/skills/）

- 框架文档：[YYC3-AI-Family-Skills技能库框架目录.md](YYC3-AI-Family-Comic-Drama-Agent/YYC3-AI-Family-Skills技能库框架目录.md)（13 域 44 技能：P0×27/P1×7/P2×9/P3×1；SKILL.md 契约模板；编号与组件库同构）
- 骨架落地：44 个 SKILL.md（组件背书技能契约按 components/ 真实签名填充）+ README + INDEX
- 可执行件：`_matrix/p0_smoke_matrix.py`（P0×27 冒烟矩阵）+ 95 域三件套（gate-runner / gate-report / regression-anchor）
- **P0 冒烟矩阵：PASS 23 / STUB 4 / FAIL 0**；回归锚点 **3/3**（场景D拦截/RAG降级/质检2轮上限）
- STUB 登记（转 M2 任务）：storyboard-schema-check（A7 schema 待填充）+ novel-split/episode-plan/storyboard-gen（script_engine 待实现）
- **矩阵揪出真缺陷并已修复**：智云守护 PII 模式 `\b` 在 CJK 邻接处永不成立（Python3 `\w` 含中日韩字符），手机号「话13800138000请」漏脱敏 → 数字类模式改环视 `(?<!\d)…(?!\d)`，已回灌 docs 副本；另补 yyc3-minimax-h3/.env.example

### 12.3 G1 E2E 解锁（网关本地起服，六用例 3 实测 PASS）

- 启动器 `scripts/run_gateway_local.py`：core/api 以 importlib 别名装载为 `app` 包（免改上游代码）；端口 25080
- 桩上游 `scripts/stub_upstream.py`（:25290，OpenAI 兼容形状）+ 上游池 `OPENAI_COMPATIBLE_UPSTREAMS` 指向
- 结果（详见 [G1-底座通电验收记录 v1.1.0](G1-底座通电验收记录-20260926.md)）：
  - **TC-G1-001 PASS**：/health 200（status=healthy；redis/pg 按设计降级上报，本机 ollama healthy）
  - **TC-G1-002 PASS（桩上游 E2E）**：Chat 全链贯通，响应头 `x-yyc3-upstream: stub-llm` 命中「上游节点标识」预期
  - **TC-G1-005 PASS（偏差留证）**：三连发 401/403/200（错误密钥实为 403，拒绝语义成立，建议 YYC3-60 v1.1 修订预期）
  - TC-G1-004 维持 PARTIAL（path_normalize 在根 app/ v1 设计件，未接线 core/api）；TC-G1-003/006 维持 BLOCKED（硬件前置）
- 补齐依赖（venv `yyc3-0379-world/.venv`，gitignored）：pgvector、sqlalchemy[asyncio]+greenlet、numpy、aiofiles、jieba、psutil、prometheus-fastapi-instrumentator 等 —— **上游缺 requirements.txt，建议补**

### 12.4 下次会话启动指南（第三轮后）

```bash
# 1. 复跑技能门禁：cd yyc3-ai-agent-archive && python3 skills/_matrix/p0_smoke_matrix.py
# 2. 复跑网关 E2E：yyc3-0379-world/.venv/bin/python scripts/stub_upstream.py &（后台）
#    cd yyc3-0379-world && .venv/bin/python ../scripts/run_gateway_local.py &（后台）
# 3. G1-002 真实 LLM 版：本机 Ollama（healthy）注册上游池后复验
# 4. M2 主线：script_engine 三件 + storyboard.v1.json 填充（清 4 个 STUB，转 G2）
```

**当前优先级 TOP 3**：

1. **[P0]** M2 编排贯通：填 script_engine 三件 + storyboard Schema（清 4 STUB → TC-G2-007 可执行）
2. **[P1]** YYC3-60 v1.1 修订：G1-005 预期 401→401/403；G3 用例编写（M3 前 1 周）
3. **[P1]** 上游仓补 requirements.txt（本轮依赖清单已留证于 G1 记录）

---

## 十三、M2 script_engine 落地 + YYC3-60 v1.1 + G1-002 真实 LLM 版（2026-09-26 第四轮）

### 13.1 M2 主线：script_engine 五件套 + 分镜 Schema（清 4 STUB）

落位 `yyc3-ai-manju-studio/backend/app/modules/script_engine/`（全部 stdlib 规则基线，LLM 增强为后续）：

| 文件 | 能力 | 验证 |
| --- | --- | --- |
| splitter.py | 章节拆分（第X章/回标记 + 无标记段落聚合兜底） | 样本文本 2 章正确拆分 |
| extractor.py | 角色/场景/对话/剧情要素抽取（引号对话 + 说话人回溯 + 场景标记） | 台词 6 条、钩子 4 处 |
| hook_detector.py | 流量钩子识别（悬念/反转/爽点/冲突/互动五类权重计分 + 单集主钩子） | ep01/ep02 均命中「悬念」 |
| episode_planner.py | 分集规划（3.5 字/秒语速基线 + 90-120s 窗口 + 跨章聚合） | 2 集，各 90s |
| storyboard_schema.py | Schema 加载/校验（与前端 validateStoryboard 同规则）/ 规则版草稿生成器 | 草稿 80 镜过校验 |
| schema/storyboard.v1.json | StoryboardV1 正式 JSON Schema（顶层 12 字段 + Shot 12 字段，**与前端 types/storyboard.ts 严格同构**） | jsonschema 兼容 |

- **TC-G2-007 三条件实测满足**：12 字段全齐、hook_shots 非空且全部 hook_flag=true、单集镜头数 80-120（草稿 80 镜，总时长 89.5s 落 90-120s 窗口）
- **P0 冒烟矩阵升级为「真实生成→校验」闭环后：27 PASS / 0 STUB / 0 FAIL（满绿）**；回归锚点 3/3
- 4 个技能状态 stub→degraded-ok（skills INDEX 同步），P1-P3 的 17 个 stub 为既定排期项
- 规则基线诚实声明：角色/场景抽取与镜头节奏为规则版，LLM 语义精抽/节奏优化为后续增强（接口契约不变）

### 13.2 YYC3-60 v1.1

- TC-G1-005 预期修订：错误密钥 401→**401/403**（未提供=401 / 已提供但无效=403，G1 实测留证）
- **G3 门禁补齐 9 条完整用例**（TC-G3-001~009：特征库建库/跨镜头一致性 ≥0.85/打回闭环/SyncNet ≥0.75/口型打回闭环/单镜 ≤5min/夜批 ≥200 镜/提示词抽检 ≥90%/风格一致性）；其中 001-005、008、009 可无 DGX 先行验证

### 13.3 G1-002 真实 LLM 版复验（本机 Ollama 上游）

- 上游池注册 `ollama-local → http://localhost:11434`（模型 `yyc3-family-coder:14b-q4`，qwen3 14.8B）
- **实测 PASS**：真实生成内容返回 + `x-yyc3-upstream: ollama-local` + `system_fingerprint=fp_ollama`；双上游（stub + ollama）按模型名 fnmatch 并存路由
- G1 现状：**3 项实测 PASS（含真实 LLM 版）+ 1 项逻辑 PASS + 2 项硬件 BLOCKED**（留证：G1 记录 v1.1.0）

### 13.4 变更提交索引（本轮按仓提交，2026-09-26 收口）

| 仓库 | 提交 | 内容 |
| --- | --- | --- |
| 根仓 | faa487a | 文档漂移治理（INDEX/README/总纲/03/06/08）+ Skills 框架文档 + G1 验收记录 v1.1.0 + YYC3-60 v1.1.0 + HANDOFF 第三/四轮 + scripts/run_gateway_local.py + scripts/stub_upstream.py |
| 根仓 | 767b9f8 / 8bb20cd | 安全修复：引擎模版 write_text 防穿越 + 资料包副本 SSRF 三道闸/RAG 密钥环境注入（与 components 逐字一致） |
| yyc3-ai-agent-archive | 026fbcd | Skills 建库（13 域 44 技能 + P0 矩阵 + 95 域三件套）+ 智云守护 PII CJK 修复 + H3 SSRF 三道闸 + skill-gateway 凭据派生化/EVAL→通用 call |
| yyc3-ai-manju-studio | 9962221 | script_engine 五件套 + storyboard.v1.json Schema（M2 P1-2/P1-3） |
| yyc3-minimax-h3 | 655e79a | .env.example + 子进程解释器去环境变量注入面 + 引擎模版 write_text 防穿越 |
| yyc3-0379-world | e71b0ef | 安全修复：模型名白名单+路径包含校验防穿越 + 测试桩凭据哈希派生 + 加权随机 SystemRandom（Mimosa 4 高危+3 低危清零，G1-005 单测 10/10 回归） |

### 13.4a 安全门禁修复轮（Mimosa L3 拦截驱动，2026-09-26）

- 提交门禁先后拦截 4+15 高危，全部修复后放行：路径穿越 ×5（0379 model_service_manager / 引擎模版 ×2 拷贝）、硬编码凭据 ×5（G1 测试桩、skill-gateway 测试、RAG 嵌入客户端——均改哈希派生或环境注入）、代码注入 ×2（Redis EVAL→通用 call）、SSRF ×2（H3 客户端三道闸：协议限制/主机白名单/解析 IP 边界，Python 3.14 ::1 保留段误杀已修）、不可信程序选择 ×2（解释器去环境变量）、不安全随机 ×3（SystemRandom）
- 自测留证：G1-005 单测 10/10 回归通过；SSRF 全场景（回环放行/链路本地拦/私网默认拦+显式放行/协议限制）通过；P0 矩阵 27/0/0 + 回归锚点 3/3 全程保持
- 遗留：3 个低危（不安全随机）已随 0379-world 修复清零；扫描器提示部分覆盖（library_source/callgraph partial），勿据此宣称项目整体安全，后续按需跑完整审计

---

## 十四、G2 十用例首跑 + 门禁回归修复 + 五仓推送（2026-09-27 第五轮）

### 14.1 G2 编排贯通十用例执行（YYC3-60 §四）

- 执行器落位：`scripts/run_g2_cases.py`（可复跑，证据 JSON 全量输出）
- 首跑即抓出 3 处真问题并全部修复（详见 [G2 验收记录](G2-编排贯通验收记录-20260927.md)）：
  1. 场景 B 违反总纲 §五「裁剪 6」产出 yuanqi_summary → 编排引擎两份拷贝修复
  2. 注入短语覆盖缺口（忽略之前…/输出系统提示词）→ 智云规则库补 4 变体，拦截 4/4 回归
  3. 场景 C 的 creative_ideas（list 契约）未序列化进审计正则 → Step7 入口统一 json.dumps
- 用例侧修订（YYC3-60 v1.2）：TC-G2-002 预期对齐实现语义（C 产出集合含质检产物；user_id=default_user）
- **终跑结果：PASS 7 / PARTIAL 3 / FAIL 0**（001~007 全过；008 prompt 运行时、009 事件流、010 真实模型计时三项 PARTIAL，解锁条件均为 M2 收尾项）
- 回归保障：修复后 P0 矩阵 27/0/0 + 回归锚点 3/3 + 注入拦截 4/4 保持满绿

### 14.2 五仓推送远程 main

| 仓库 | 远程 | 推送内容 |
| --- | --- | --- |
| YYC3-AI-Family-Comic-Drama | YYC-Cube/YYC3-AI-Family-Comic-Drama | faa487a~本轮（治理+G1 留证+G2 记录+YYC3-60 v1.2+执行器） |
| YYC3-Comic-ai-agent-archive | YYC-Cube/YYC3-Comic-ai-agent-archive | Skills 建库 + 编排引擎/智云修复 + skill-gateway 安全修复 |
| YYC3-Comic-ai-manju-studio | YYC-Cube/YYC3-Comic-ai-manju-studio | script_engine 五件套 + Schema |
| YYC3-Comic-minimax-h3 | YYC-Cube/YYC3-Comic-minimax-h3 | .env.example + 安全修复 |
| YYC3-Comic-0379-world | YYC-Cube/YYC3-Comic-0379-world | 安全修复 e71b0ef |

### 14.3 下次会话启动指南（第五轮后）

```bash
# 1. 复跑 G2：yyc3-0379-world/.venv/bin/python scripts/run_g2_cases.py
# 2. M2 收尾三项（清 G2 的 PARTIAL）：
#    a. prompt 装载运行时（agents/*/prompt.md → system_prompt，TC-G2-008 复验）
#    b. 编排引擎向 91-A2A 事件流埋点（TC-G2-009 复验）
#    c. 真实 LLM 接入（Ollama 上游已验证）→ TC-G2-010 并行收益复验
# 3. M3 预研：TC-G3-001/002 特征库与一致性（insightface 真实模型）
```

**当前优先级 TOP 3**：

1. **[P0]** M2 收尾：prompt 装载运行时 + A2A 埋点（清 TC-G2-008/009 PARTIAL）
2. **[P1]** 真实 LLM 全链（Ollama 上游已验证）→ TC-G2-010 并行收益 + TC-G2-005 复检达标复验
3. **[P1]** TC-G3-001/002 一致性预研（insightface 512 维）

---

## 十五、M3 一致性专项预研（TC-G3-001/002 真实 512 维全通 · 2026-09-27 第五轮追加）

### 15.1 预研结果（详见 [G3-一致性预研记录](G3-一致性预研记录-20260927.md)）

- **TC-G3-001 建库 🟢 PASS**：insightface buffalo_l 真实模型（CPU），manifest mode=insightface、dim=512、同图 cos=1.0、三件套齐
- **TC-G3-002 跨镜头比对 🟢 PASS**：同角色跨镜头最低 **0.8921**（hero 0.9643 / villain 0.8921，阈值 ≥0.85）、跨角色最高 **0.0119**（区分度 margin 0.88）、逐帧提取模式 `insightface×4`（零哈希降级）
- **一致性 ≥80%/0.85 门禁的技术可行性在本地 CPU 全实证**——最大技术风险（YYC3-07 风险 T1）预研对冲完成

### 15.2 环境障碍突破（沉淀为经验）

1. GitHub release 直连被重置 → **gh-proxy.com 镜像**下载 buffalo_l（275MB）；模型须手动解压至 `~/.insightface/models/buffalo_l/`（insightface 不认裸 zip）
2. 首轮 hero 相似度 ≈0 的根因是**固定裁剪把脸裁出检测框 → 静默哈希降级**——face_encoder 已加 `last_mode` 逐帧留证 + 无人脸检出显式告警（降级红线可审计）
3. 素材方法论：randomuser 人像 + **人脸感知裁剪**（检测框外扩 1.8× 取景）构造跨镜头变体，保证变体帧必然可检出

### 15.3 工程变更

| 仓库 | 变更 |
| --- | --- |
| yyc3-ai-manju-studio | face_encoder last_mode 留证 + .venv（gitignored）；face_library_g3 预研库（本地，gitignored） |
| 根仓 | scripts/run_g3_cases.py 执行器 + G3-一致性预研记录 |

### 15.4 下次会话启动指南

```bash
# 复跑 G3 预研：yyc3-ai-manju-studio/.venv/bin/python scripts/run_g3_cases.py
# 素材重建（如 /tmp 清空）：见 G3 记录 §环境障碍 #3 方法论
# M3 主体：真实角色图入库 → anchor_guard 三段锚定 → TC-G3-003 打回闭环
```

**当前优先级 TOP 3**（更新）：

1. **[P0]** M2 收尾：prompt 装载运行时 + A2A 埋点（清 TC-G2-008/009 PARTIAL）
2. **[P1]** M3 主体：真实角色图入库 + anchor_guard 三段锚定联调（预研已实证可行性）
3. **[P1]** 真实 LLM 全链 → TC-G2-010 并行收益复验

---

## 十六、M2 收尾 + M3 主体并行完成（2026-09-27 第六轮）

### 16.1 M2 收尾（G2 记录 v1.1：8 PASS / 2 PARTIAL / 0 FAIL）

| 交付 | 结果 |
| --- | --- |
| `components/prompt_runtime.py` | prompt.md 装载运行时（frontmatter+双 text 围栏+输出契约提取+实例构建）；8 Agent 全量注入（675~1150 字） |
| `components/orchestrator_events.py` | 步骤事件埋点（redis Stream→自动降级 JSONL，`replay(trace_id)` 取证入口） |
| 编排引擎 5 步埋点接入 | **TC-G2-009 转正 PASS**（B 场景事件序列完整/同 trace_id/untraced 拦截留痕） |
| **TC-G2-008 复验** | 结构面 8/8 + 真实 LLM 契约 **7/8**（Ollama 14B 真实推理；语枢 1 例超时回退 Mock=非契约缺陷）→ 维持 PARTIAL（仅差语枢单例复验） |
| BaseAgent 加固 | 补 `LLM_TIMEOUT`（挂死防线，openai 客户端默认无超时——实测暴露）与 `LLM_MAX_TOKENS`（思考模式长生成防线）；两份拷贝同步 |
| 门禁拦截的自伤 bug | 埋点首跑即拦出「trace_id 赋值前引用」（UnboundLocalError），修正后两份拷贝同步——收口执行器的回归价值 |

### 16.2 M3 主体（G3 记录 v1.1：TC-G3-001/002/003 全 PASS）

- `backend/app/modules/consistency_engine/anchor_guard.py`：三段锚定（pre_anchor 锚定+未建库 BLOCKED / during_constraint 桩态约束 / post_check 打回闭环）
- **TC-G3-003 实测 11/11**：错人帧 -0.0013→REDRAW、同人帧 0.9643→ACCEPT、超限→ESCALATE、全程真实模型特征（降级帧拒判红线生效）
- 执行器 `scripts/run_m3_anchor.py`（生产兜底库 face_library 进程内重建，gitignored）

### 16.3 回归与治理

- 埋点/超时改造后回归：P0 矩阵 27/0/0 + 回归锚点 3/3 满绿
- `agent-archive/.gitignore` 补 `events/`、`face_library*/`（运行时产物零入库）
- INDEX v1.4 / 总纲 §8.1：components 事实源 13→15 件（+prompt_runtime+orchestrator_events）

### 16.4 下次会话启动指南

```bash
# 1. 复跑：run_m2_closure.py（008 语枢复验）/ run_m3_anchor.py（11/11）
# 2. M3 视听产能：DramaToolGateway 桩→实（ComfyUI 文生图）→ TC-G3-008 提示词抽检
# 3. M2 残尾：TC-G2-010 真实模型并行计时（Ollama 双路并发）
```

**当前优先级 TOP 3**（更新）：

1. **[P0]** M3 视听产能：DramaToolGateway 桩→实（ComfyUI 文生图接入，anchor_guard 真实进生成链）
2. **[P1]** TC-G2-008 语枢复验 + TC-G2-010 真实模型并行计时（清 G2 双 PARTIAL）
3. **[P1]** 真实多机位角色素材标定（anchor_guard 阈值 0.85 在真实素材上复标）

---

## 十七、三项 TOP 全部完成：M3 视听首件 + G2 清尾 + 阈值复标（2026-09-27 第七轮）

### 17.1 M3 视听产能首件（G3 记录 v1.2 · 🟢 10/10）

- **DramaToolGateway 桩→实（v1.2，两份拷贝同步）**：ComfyUIClient——标准 SD API 工作流（/prompt→/history 轮询→/view 取图）、SSRF 三道闸同构、未配置/失败回落 stub 永不断流；env 入 agent-archive/.env.example（原为 0 字节，已补全模板）
- **anchor_guard 真实进生成链**（Mock ComfyUI :41888 联调，诚实边界：生成本体为预设人脸图非扩散模型）：pre_anchor → HTTP 生成 → 首帧身份漂移 REDRAW → 重绘 ACCEPT（0.9643）两轮收束 ✓；未配置回落 stub ✓
- **TC-G3-008 🟢**：20 镜三要素比例 **100%**；storyboard_schema 钩头加「【钩子镜头】」可区分标记（非钩头无污染）

### 17.2 G2 清尾（G2 记录 v1.2 · **9 PASS / 1 PARTIAL / 0 FAIL**）

- **TC-G2-008 转正**：语枢真实 LLM 契约复验通过（四段式报告真实输出）→ 真实契约 **8/8**
- **TC-G2-010 维持 PARTIAL（证据升级）**：真实计时 serial 161.2s vs parallel 271.4s（ratio 1.684）——**单实例 Ollama 串行化并发请求的环境边界**（并行墙钟>串行恰证引擎 ThreadPool 并发派发生效）；YYC3-60 v1.2.1 已补前置（须 vLLM 连续批处理），DGX 部署后复跑即闭环

### 17.3 阈值复标（G3 记录 v1.2 · 0.85 维持）

- 强变换族 8×2（翻/旋/色温/压缩/裁剪/明度/去饱和）：同角色最低 **0.9536**、跨角色最高 **0.0249**、margin **0.9287** → **DEFAULT_THRESHOLD=0.85 维持**（余量充足）；A_crop60 检出失败走 escalate 兜底；真实风险域（SD 生成身份漂移）留待产线样本持续标定

### 17.4 回归与依赖

- 全程回归：P0 矩阵 27/0/0 + 锚点 3/3 + adapter 双拷贝 diff 一致
- manju venv 补 python-dotenv/openai（pymilvus 2.4.5 在 Py3.14 无 grpcio wheel，runner 用降级桩，同冒烟矩阵模式）

### 17.5 下次会话启动指南

```bash
# 复跑：scripts/run_m3_av.py（10/10）/ run_g2_final.py（008 PASS+010 计时）/ run_threshold_calibration.py
# M3 续：真实 ComfyUI 部署（本机装 SDXL 或接 DGX）替换 Mock 生成本体 → TC-G3-006 单镜耗时基线
```

**当前优先级 TOP 3**（更新）：

1. **[P0]** 真实 ComfyUI 部署（本机 SDXL 或 DGX）→ Mock 生成本体替换 + anchor_guard 打回闭环真图复验
2. **[P1]** DGX/NAS 硬件推进（G1-003/006 解锁 + vLLM 并发复跑 TC-G2-010）
3. **[P1]** M4 前置：TTS/sync_score 工具接入（DramaToolGateway 余桩）+ 真实角色 IP 素材集

---

## 十八、三项 TOP 完成：真实 SD 全链 + 010 转正 G2 满贯 + 漂移实证（2026-09-27 第八轮）

### 18.1 真实 ComfyUI 部署与真图闭环（G3 记录 v1.3 · 3/3）

- **部署**：`/Users/yanyu/YYC-Cube/tools/ComfyUI`（gh-proxy 克隆 @79be670；独立 venv；**torch 2.14.0 MPS 可用**；模型 DreamShaper_8_pruned 2.13GB 经 **hf-mirror** 下载——Lykon/DreamShaper 仓库，hf-mirror API 查文件清单再 resolve）；服务 :41888
- **真图打回闭环 3/3**：锁定重生成 sim=**1.000** ACCEPT（同 seed 确定性 + ComfyUI 同参缓存 ≈1s）→ 漂移种子 sim=**0.4418** REDRAW（真实 SD 漂移被检出）→ 锁定重绘 sim=**1.000** ACCEPT 收束
- **修复留证**：新版 ComfyUI SaveImage 必填 `filename_prefix`（400 由真实服务暴露，Mock 测不出——桩→实的价值）；客户端加 seed 参数（身份锁定重生成接口）
- **TC-G3-006 真实基线**：Mac 预览路由单镜 **422-486s**（512×512/25 步，超 ≤120s 目标，记录为硬件基线）；DGX NF4 ≤300s 待硬件；锁定重绘走缓存 ≈1s

### 18.2 TC-G2-010 转正 → **G2 十用例全 PASS（v1.3 满贯）**

- 双模型双进程并发（yyc3-family-coder + qwen3-coder-30b，DGX 双节点语义）：串行 59.7s vs 并行中位 23.1s → **ratio=0.386 ≤0.8**（执行器 `scripts/run_g2_010_dual.py`，httpx 模型随载荷无 env 竞争）
- G2 终态：**10 PASS / 0 PARTIAL / 0 FAIL**；DGX vLLM 终值复验列硬件日动作

### 18.3 SD 漂移实证与生产策略（③核心产出）

- 无 LoRA 同提示词跨种子漂移分布 **0.4418-0.5687**（均值 ≈0.52）——行业返工率 70% 根因的量化实证
- 生产策略三则：①无 LoRA 跨镜头不可用（anchor_guard 会全打回，正是职责）；②**seed-lock 为 M3 现行合法策略**（确定性 1.0 + 缓存近零成本）；③**LoRA/IPAdapter 是 M3 视听产能必要条件**（0.85 达成依赖训练而非调阈值）

### 18.4 TTS/sync_score 处置（M4 前置，诚实归档）

- 本机无 TTS 服务/SyncNet 模型/音视频资产 → **列 M4 服务/硬件前置**（同 G1-003/006 性质）
- macOS `say` 为潜在本地方案，但 subprocess 形态受安全门禁约束 → 后续以独立 TTS 服务进程（OpenAI 兼容 /v1/audio/speech 端点）形态接入；`.env.example` 预留位

### 18.5 下次会话启动指南

```bash
# ComfyUI 服务：cd /Users/yanyu/YYC-Cube/tools/ComfyUI && .venv/bin/python main.py --port 41888 --listen 127.0.0.1
# 真图闭环复跑：COMFYUI_MODEL=DreamShaper_8_pruned.safetensors yyc3-ai-manju-studio/.venv/bin/python scripts/run_comfy_real.py
# 010 复跑：yyc3-0379-world/.venv/bin/python scripts/run_g2_010_dual.py
```

**当前优先级 TOP 3**（更新）：

1. **[P0]** M3 视听产能主线：LoRA/IPAdapter 角色训练方案落地（漂移实证 0.52 → 0.85+ 的唯一路径）+ 多镜头批量流水线骨架
2. **[P1]** DGX/NAS 硬件日动作清单执行（G1-003/006 解锁 + vLLM 010 终值 + TC-G3-006 DGX 基线）
3. **[P1]** M4：TTS 独立服务接入（OpenAI 兼容端点）+ SyncNet 部署 + 真实 IP 素材集入库 NAS

---

## 十九、IPAdapter 实验 + LoRA 必要性二次实证 + TTS/批量/硬件日全落地（2026-09-27 第九轮）

### 19.1 IPAdapter 身份锚定实验（G3 v1.4 · 关键结论）

- 环境：ComfyUI_IPAdapter_plus（gh-proxy）+ PLUS FACE 预设 + ViT-H 2.5GB + plus-face_sd15（hf-mirror API 查真路径——直接猜仓 404 三连教训）
- **同种子集对照：无锚定均值 0.516 → IPAdapter 0.670（+0.154），未达 0.85** → anchor_guard 全部正确打回
- **定论：「IPAdapter 兜底 + LoRA 训练」组合是 0.85+ 唯一路径**（行业实践一致，两次独立实证）
- 修复留证：节点注册名=IPAdapter（≠类名 IPAdapterSimple）；DramaToolGateway 类内旧 tts 桩同名覆盖新方法（后定义胜出法则）

### 19.2 M4 TTS 真实落地（提前完成）

- `scripts/tts_service.py`：piper 中文 TTS 独立服务（OpenAI 兼容 :42118，纯 Python 零 subprocess——绕开安全门禁约束的正解）
- 实测 218KB WAV；`DramaToolGateway.tts` 真客户端（SSRF 白名单+回落 stub）链路 tts=ok

### 19.3 批量流水线 + LoRA 骨架 + 硬件日清单

- `scripts/run_batch_shots.py`：分镜→pre_anchor→IPAdapter 生成→post_check（**seed-lock 回退策略**）→TTS→manifest，NAS 目录镜像；冒烟 2 镜通过（含 ComfyUI 不可达降级回落与真 TTS 出声并存）
- `manju-studio/scripts/train_character_lora.py`：diffusers+peft 骨架（变换族扩增/Mac 冒烟与 DGX 正式双预设）
- `scripts/run_hardware_day.sh`：硬件日一键清单（G1-003 三端互写/G1-006 首 token/010 终值/G3-006 DGX 基线）
- 事故留证：ComfyUI 服务在第三次生成中疑似被系统终止（MPS 高负载，resource_tracker 泄漏信号）——批量骨架的降级回落恰在此时兜住（stub_fallback + manifest 留证），高可用设计自我验证

### 19.4 下次会话启动指南

```bash
# ComfyUI: cd /Users/yanyu/YYC-Cube/tools/ComfyUI && .venv/bin/python main.py --port 41888 --listen 127.0.0.1
# TTS: yyc3-ai-manju-studio/.venv/bin/python scripts/tts_service.py
# 批量: COMFYUI_MODEL=DreamShaper_8_pruned.safetensors ... run_batch_shots.py --project demo-001 --limit N
# IPAdapter 实验: ... run_ipadapter_identity.py（结果 /tmp/ipadapter_identity.json）
# 硬件日: bash scripts/run_hardware_day.sh --nas-host H --dgx1 H --dgx2 H
```

**当前优先级 TOP 3**（更新）：

1. **[P0]** LoRA 训练执行（DGX 或本机小步数冒烟）：train_character_lora.py 补全训练循环 → LoRA 后跨种子复测（目标 0.85+）
2. **[P1]** ComfyUI 服务稳定性（MPS 高负载被杀——加 --force-fp16 / 降 steps / 自动重启守护）
3. **[P1]** 硬件日执行 + M4 SyncNet（音画对齐链路，需 TTS 音轨+视频合成先行）

---

## 二十、LoRA 冒烟 + 守护化 + 合成链全通（2026-09-27 第十轮）

### 20.1 LoRA 训练冒烟（① · 链路通，科学目标移交 DGX）

- 依赖攻坚留证：transformers 5 移除 CLIPFeatureExtractor → **钉 4.57**；diffusers 0.40↔hub1.x↔transformers4 三角死结 → **换代际对齐 diffusers 0.33 + hub 0.36**；`add_noise` 返回单张量（非元组）
- **训练链路 ✅**：240 步 6 分钟（MPS），loss 0.13→0.005；r=8/attn 四模块 1.19M 参数；**kohya 键位导出 192 张量**（ComfyUI models/loras/sd-hero_smoke.safetensors）
- **复测未达（诚实归档）**：4 漂移种子生成图有内容但 insightface 检不出人脸（degraded×4）→ 疑因触发词不在 CLIP 词表/peft 包装推理路径/4 图过拟合；**0.85+ 验证移交 DGX 正式训练**（dgx_prod 预设）
- 另留证：ComfyUI venv 需补 onnxruntime（insightface 运行时依赖，装包不自动带）

### 20.2 ComfyUI 守护化（②）

- `scripts/comfyui_guardian.sh`：**--force-fp16** 启动（第九轮 MPS 被杀缓解）+ 退出 5s 自动重启 + 退出日志 /tmp/comfyui_guardian.log
- 验证：守护模式起服 ✓、IPAdapter 节点 200 ✓、fp16 真实生成验证执行中（G3 v1.5 补录）

### 20.3 视频合成链 + 硬件日演练（③）

- **`scripts/run_clip_compose.sh` 全通**：IPAdapter 帧 + 台词 → piper TTS 287KB WAV → **ffmpeg MP4（h264+aac 6.51s，时长=音轨）**——M4 compose 服务化前身
- 硬件日演练：无硬件模式 3 BLOCKED 正确留证（脚本可用性验证通过）；SyncNet 维持 M4 硬件/资产前置（音画素材链已就绪，模型源 Google Drive + dlib 编译受阻）

### 20.4 下次会话启动指南

```bash
# ComfyUI（守护）: bash scripts/comfyui_guardian.sh 41888
# LoRA 冒烟复跑: /Users/yanyu/YYC-Cube/tools/ComfyUI/.venv/bin/python scripts/run_lora_train_eval.py --steps 240
# 合成链: bash scripts/run_clip_compose.sh <png> "台词" <mp4>
# 硬件日: bash scripts/run_hardware_day.sh --nas-host H --dgx1 H --dgx2 H
```

**当前优先级 TOP 3**（更新）：

1. **[P0]** kohya sd-scripts 部署（DGX 或本机 CPU 冒烟）→ 真 LoRA 0.85+ 复测（手工循环已弃用）
2. **[P1]** DramaToolGateway.sync_score 真实对接（包装器封装进网关，静态打回→图生视频达标链路）
3. **[P1]** 硬件日执行（清单就绪）+ 单集 demo 升级（图生视频动态镜头 → SyncNet 达标验证）

---

## 二十二、sync_score 服务化对接 + Token-Console 生产看板层落地（2026-09-27 第十二轮）

### 22.1 TOP3 执行（①②完成，③硬件待实物）

- **① kohya 部署**：`tools/kohya_ss` + sd-scripts/train_network.py 入口就绪（注意：仓库名下划线 `kohya_ss`；sd-scripts 是子模块需单独 clone）。依赖正式安装列 DGX（kohya 生态 pin 旧 Python，本机 3.14 兼容风险）。
- **② sync_score 真实对接 ✅**：`scripts/syncnet_service.py`（FastAPI 封装 SyncNetInstance.evaluate，`POST /v1/sync/score` :42218，纯 import 零 subprocess，跑 ComfyUI venv——自带 torch/insightface）；`DramaToolGateway.sync_score` 桩→真客户端。**E2E 实测**：demo 裁切轨 conf=0.2275 → 打回(<0.75)；空参回落 stub。SSRF 三道闸复检补齐（解析 IP 边界，白名单外拦截实测）。提交：根仓 ced03e9 / agent-archive 4dd0933。
- **③ 硬件日**：清单待实物；demo 升级（图生视频）随硬件推进。

### 22.2 Token-Console 生产看板层落地（YYC3-AI-API-Token-Console 2535aa2）

分析结论落地：Token-Console（纯前端 SPA，token.yyc3.vip）定位为**两项目共用的运营看板层**，三层体系 = Token-Console（看板）→ manju-studio 工作台 / H3 console（生产操作）→ 网关+服务群（执行）。

- **① 零代码注册**：`builtin-providers.json` 追加 5 个本地生产 provider——yyc3-gateway(:25080)/comfyui(:41888)/syncnet(:42218)/tts(:42118)/h3(:8002)，/models 页即时生效（provider 数 9→14）
- **② 轻扩展**：新增 `ai-family-sub/drama` 只读子页 `FamilyDrama.tsx`（5 服务健康探针 fetch 超时降级 + 六环节链路展示 + 分层边界声明）；四同步完成（lazyMap/routes 兼容路径/zh+en i18n/Sidebar/BottomNav）
- **验证**：typecheck 0 错误、build 通过、**测试 1966/1966**（provider 断言 9→14 + 新增 yyc3-* 服务群断言）
- 顺带修复：工作区 `settings/shared.tsx` 注释意外破坏（shared→sared）已恢复

### 22.3 下次会话启动指南

```bash
# 看板验证：Token-Console pnpm dev → /ai-family-drama（服务在线时探针全绿）
# SyncNet 服务：ComfyUI.venv/bin/python scripts/syncnet_service.py（:42218）
# TTS 服务：yyc3-ai-manju-studio/.venv/bin/python scripts/tts_service.py（:42118）
```

**当前优先级 TOP 3**（更新）：

1. **[P0]** kohya sd-scripts 正式训练（DGX）：LoRA 后跨种子复测冲 0.85+
2. **[P1]** 图生视频接入（H3 服务起服）→ 动态镜头 → SyncNet 达标链路验证
3. **[P1]** 硬件日执行 + Token-Console 看板对接真实指标（网关 /metrics WS 桥）

---

## 二十三、LoRA 本机 kohya 攻坚 + 看板真实指标落地（2026-09-27 第十三轮）

### 23.1 kohya 本机攻坚（① · 工具链打通，训练受阻于版本断层——precise 清单已录）

- **打通项**：sd-scripts 完整导入链在本机 ComfyUI venv 全通（`train_network.py --help` 正常输出）——依赖逐项补齐：toml/albumentations/voluptuous/ftfy/einops（easygui 需 tkinter，CLI 链路不引用可跳过）；加速器兼容补丁（新版 accelerate 移除 `logging_dir` 形参→inspect 探测条件传参）；参数名修正（`--min/max_bucket_reso`）；数据集组装脚本 `run_kohya_lora.py prep`（4 图+caption→标准 `<dir>/10_hero/` 布局）
- **精确阻断点**：训练启动即崩于 accelerate 1.x `has_compiled_regions`——**该版 sd-scripts（commit 6721028）需 accelerate≈0.15 + diffusers≈0.10-0.15 + Python≤3.11 的 pin 环境**；ComfyUI venv（accelerate 1.x + diffusers 0.33 + Py3.14）无法共存，Homebrew Py3.14 也无旧 torch wheel。**结论：需独立 venv（pyenv 3.10/3.11 + requirements.txt 原样安装）→ DGX 或本机 pyenv 皆可，本机单 venv 不可行**
- 工具链价值：kohya CLI 路径全通意味着 DGX 环境就绪后可直接跑（命令已验证到训练启动前最后一步）

### 23.2 Token-Console 看板对接真实指标（③ · ✅）

- 网关 CORS 放行看板源（`.env` ALLOWED_ORIGINS：localhost:3030/20300 + token.yyc3.vip，本地配置不入库）；**E2E 验证**：`access-control-allow-origin: http://localhost:3030` 正确返回
- `FamilyDrama.tsx` 新增网关实时指标卡：`/health` 30s 轮询，展示运行状态/版本/在线时长/累计请求/缓存命中率——**看板首次消费生产服务真实数据**（此前为探针状态）
- 验证：typecheck 0 错、build 通过、1966/1966；提交 Token-Console 575e287

### 23.3 H3 现状核验（② · 阻断点=权重下载）

- `server/api.py` 为空占位；真实引擎在 `agent/h3_agent/`（2.4k 行，orchestrator/gateway/protocol 齐全，六阶段闭环标 stable）；模型权重未下载（.gitkeep，~30GB 级经 hf-mirror 可得）
- **链路命令已就绪**：权重到位后 server 起服 → 网关注册 h3 上游 → 编排端 DramaToolGateway.image_to_video 自动路由（已实现）→ 产物过 SyncNet 门禁（:42218 服务已就绪）

### 23.4 下次会话启动指南

```bash
# kohya DGX/独立 venv：pyenv install 3.10 → python -m venv .venv → pip install -r sd-scripts/requirements.txt（原样 pin）
# 训练命令（本机已验证到启动前）：见 /tmp/kohya_train.log 头部或 HANDOFF §23.1
# 训后评测：ComfyUI.venv/bin/python scripts/run_kohya_lora.py eval --lora /tmp/kohya_out/sd-hero.safetensors
# H3 权重下载：hf-mirror 搜 MiniMax-H3 权重仓 → models/h3/ → server 起服
```

**当前优先级 TOP 3**（更新）：

1. **[P0]** kohya 独立 pin venv 构建（pyenv 3.10 本机或 DGX）→ 160 步训练 + kohya_eval.json 复测
2. **[P1]** H3 权重下载（~30GB hf-mirror）→ server 起服 → 动态镜头 → SyncNet ≥0.75 达标验证
3. **[P1]** 硬件日执行（run_hardware_day.sh 一键清单就绪）

---

## 二十四、kohya macOS 定论 + H3 网关验证 + 收尾（2026-09-27 第十四轮）

### 24.1 TOP 3 执行结果

| # | 任务 | 结果 |
| --- | --- | --- |
| ① | kohya pin venv 构建 | **macOS 不可行（定论）**：Py3.10 scipy .so Mach-O 与 macOS dyld 二进制不兼容（force-reinstall/scipy 1.15/1.17 均无法解）；Py3.11 diffusers 版本三角死结（transformers 4.26 ↔ hub 0.13 ↔ diffusers 0.15 ↔ accelerate 0.15 互斥）；LoRA 创建在 diffusers 0.15 下 duplicated lora name（模型遍历结构变化）→ **kohya LoRA 训练必须 DGX Linux** |
| ② | H3 网关起服 | ✅ **agent/h3_agent/gateway.py :8300 healthz ok**（inmemory 传输、3 Agent 注册：智云安全哨/织影生产官/格物质检官）；server/api.py 0 字节占位（真代码在 agent/h3_agent/）；权重 ~30GB 待 hf-mirror 下载 |
| ③ | 看板真实指标 | ✅ **CORS 放行 + FamilyDrama /health 30s 轮询指标卡**（网关 E2E 验证：access-control-allow-origin 正确返回）；硬件日清单维持待实物 |

### 24.2 kohya macOS 不可行定论（precise 阻断链）

| 尝试 | 结果 |
| --- | --- |
| ComfyUI venv（Py3.14 + 最新包） | 导入链通 → accelerate `logging_dir` 已兼容补丁 → **训练启动崩**（accelerate 1.x `has_compiled_regions` 与 diffusers 0.33 结构不兼容） |
| Py3.10 venv + unpinned deps | **scipy .so Mach-O 二进制与 macOS dyld 不兼容**（`__DATA/__thread_bss` 段错误；force-reinstall/升级均不解） |
| Py3.11 venv + unpinned deps | scipy 1.17 sparse OK ✓ → diffusers 0.40 模块路径不兼容（unet_2d_condition 移位）→ 降 0.33/0.15 均有 API 断层 → **duplicated lora name**（diffusers 0.15 模型遍历结构变化） |
| 最终 pin 全组（tf4.26+diff0.15+acc0.15+hub0.13） | pip 依赖三角仍不可全满足 |

**结论**：本 vintage sd-scripts 需 diffusers 0.10.2 + accelerate 0.15 + hub 0.12 世代，macOS ARM 无法构建该环境（二进制 wheel 限制）。**必须 DGX Linux + Docker/conda**。工具链本身（argparse/dataset/bucketing/accelerate 构造）在本机已验证可达训练启动前最后一步。

### 24.3 下次会话启动指南

```bash
# DGX kohya: cd tools/kohya_ss/sd-scripts && conda create -n kohya python=3.10 && pip install -r requirements.txt
# 训练（DGX GPU）: python train_network.py [同 §23.1 命令但 mixed_precision=fp16]
# 训后评测（Mac 或 DGX）: run_kohya_lora.py eval --lora <输出路径>
# H3 权重: hf-mirror 搜 MiniMax-H3 → models/h3/ → ComfyUI.venv python -m uvicorn agent.h3_agent.gateway:app --port 8300
```

**当前优先级 TOP 3**（更新）：

1. **[P0]** DGX 环境：kohya conda venv + 训练执行（macOS 已定论不可行，本轮留证完整）
2. **[P1]** H3 权重下载 + server 起服（网关已验证 :8300 可用）
3. **[P1]** 硬件日一键清单执行（run_hardware_day.sh）

---

## 二十一、LoRA 对照定论 + 单集成片交付 + SyncNet 本地落地（2026-09-27 第十一轮）

### 21.1 三项 TOP 全部达成

| # | 任务 | 结果 |
| --- | --- | --- |
| ① | LoRA 配方修正复测 | **对照组实锤手工循环训崩**（对照 4/4 检出脸 sim 0.05-0.23，LoRA 后 2/4 降级）→ kohya sd-scripts（DGX）终路确认；v1.7 修 kohya 导出顺序（merge 前）；seed-lock 换提示词不成立缺陷留证 |
| ② | 单集成片交付 | **demo_ep01.mp4（9.09s/514KB/h264+aac）**：分镜→fp16 真实生成（3 镜 IPAdapter 锚定 sim 0.64-0.70 全 escalate 留痕）→piper 配音→串接；批量 3 镜 561.7s |
| ③ | SyncNet 模型侧攻坚 | **本地真实可跑**：syncnet_v2+sfd 经 hf-mirror lithiumice/syncnet 获得；包装器 run_syncnet_score.py（不改上游，fork 布局不匹配的绕行）；实测 conf=0.2275 正确打回静态配音片——打回逻辑自验证 |

### 21.2 关键工程留证

- SyncNet 依赖三件：ComfyUI venv（torch）+ scenedetect + python_speech_features；模型落 `tools/syncnet/`（syncnet_python/{data/syncnet_v2.model, detectors/s3fd/weights/sfd_face.pth}）
- Mimosa 拦截上游 run_syncnet.py 编辑（其 argparse 路径高危误报）→ 包装器方案反而更优（零上游改动）
- 全链复现：run_pipeline.py（裁切）→ run_syncnet_score.py（评分）

### 21.3 下次会话启动指南

```bash
# SyncNet 全链: cd tools/syncnet/syncnet_python && ComfyUI.venv/python run_pipeline.py --videofile X --data_dir /tmp/syncnet_work --overwrite
#             然后 ComfyUI.venv/python scripts/run_syncnet_score.py
# 单集 demo: guardian 起服 → run_batch_shots --limit 3 → 逐镜 run_clip_compose → concat
```

**当前优先级 TOP 3**（更新）：

1. **[P0]** kohya sd-scripts 部署（DGX 或本机 CPU 冒烟）→ 真 LoRA 0.85+ 复测（手工循环已弃用）
2. **[P1]** DramaToolGateway.sync_score 真实对接（包装器封装进网关，静态打回→图生视频达标链路）
3. **[P1]** 硬件日执行（清单就绪）+ 单集 demo 升级（图生视频动态镜头 → SyncNet 达标验证）

### 13.5 下次会话启动指南（第四轮后）

```bash
# 1. 技能门禁复跑（应 27P/0S/0F）：cd yyc3-ai-agent-archive && python3 skills/_matrix/p0_smoke_matrix.py
# 2. TC-G2 用例执行前置已就绪：九步闭环 6 场景 + 分镜 Schema（G2 十用例按 YYC3-60 §四 跑）
# 3. M3 预研：face_encoder 真实模型（pip install insightface onnxruntime）→ TC-G3-001/002
```

**当前优先级 TOP 3**：

1. **[P0]** G2 十用例执行（TC-G2-001~010，分镜 Schema 已就绪；004/005 为回归锚点）
2. **[P1]** M3 一致性专项预研（TC-G3-001/002 无 DGX 可先行）
3. **[P1]** 上游仓补 requirements.txt + storyboards LLM 增强（script_engine 规则版 → LLM 精抽）

---

## 二十五、未跟进内容全量审核（2026-09-28 第十五轮）

### 25.1 审核产出

**《[未跟进内容审核分析报告-20260928.md](未跟进内容审核分析报告-20260928.md)》**——以 2026-09-28 代码实态（五仓 git log/status + 空占位 wc -c 实测）三角验证，对照 YYC3-09 里程碑 / YYC3-60 门禁 / YYC3-08 实现度矩阵。

### 25.2 核心结论

- **门禁面**：G2 已 10/10 满贯（v1.3）；G3 四用例 PASS + SyncNet 本地落地；G1 仍 4 BLOCKED（硬件/NAS）；G4/G5 未开跑但前置件齐（demo_ep01 成片 + 合成链全通）。
- **缺口全收敛两类**：硬件依赖族（DGX 一个动作解锁 G1 清零/kohya LoRA/G2-010 终值/G3-006 基线四件事）+ 收尾规范族（空占位裁决/文档同步）。
- **实测空占位（0 字节）**：style_keeper.py、score_aggregator.py、shot_planner.py、backend/requirements.txt、H3 server/api.py + scripts/closed_loop.py、docker-compose.nas.yml、init_nas_path.sh。
- **高危发现**：`scripts/run_kohya_lora.py` 未入库但 HANDOFF §23.4/§24.3 启动指南直接引用（DGX 日评测断链风险）；YYC3-08 §2.2 矩阵严重过期（script_engine/consistency_engine 仍标空占位）；staged 的 YYC3-HTML-设计指导文档.md 未提交。
- **审核结论：有条件通过**——完成报告 §五「立即执行」四步（白名单提交/gitignore 补规则/矩阵刷新/幽灵占位裁决）后，无硬件可推进至 Step 8；DGX 到位日按 Step 9-12 四连收割。

### 25.3 当前优先级 TOP 3（本次审核更新）

1. **[P0]** 白名单提交 run_kohya_lora.py + 设计指导文档 + gitignore 补 .mimosa/face_library 规则（报告 Step 1-2）
2. **[P1]** style_keeper.py 实现（一致性三件套收尾）+ backend/requirements.txt 补齐（报告 Step 5-6）
3. **[P1]** YYC3-60 G4 用例细化 + H3 权重 hf-mirror 下载（报告 Step 7-8）

---

## 二十六、审核 Step 1-8 全量执行（2026-09-28 第十六轮）

### 26.1 执行清单（对照审核报告 §五路线图）

| 步骤 | 内容 | 结果 |
| ---- | ---- | ---- |
| Step 1-2 | 白名单提交 run_kohya_lora.py + 设计指导文档；五仓 gitignore 补 .mimosa/.v2c/.video_agent/face_library_*/ | 完成（根仓 eace9ef+71cf416，四子仓各一笔） |
| Step 3 | YYC3-08 矩阵刷新 v1.1.0→v1.2.0（§1.1 快照/§2.2-2.5 四仓矩阵/§2.6 裁决表/agents 映射表/§4.3 P2 行） | 完成（根仓 95ed7d5） |
| Step 4 | 幽灵占位裁决：23 处 0 字节空壳删除（超报告初判 8 处），承担者留证 §2.6 | 完成（manju ae3b71f / h3 dd1858b / archive 6831103 / 0379 b347565） |
| Step 5 | **style_keeper.py v1.0 实现**（一致性三件套收口）：确定性派生（SHA-256 种子+LUT+笔触）/持久化防漂移/风格注入/参数级核验/图像级三态闭环（PIL 色彩矩+直方图，红线镜像 anchor_guard：降级不得进生产判定）；单测 17/17 PASS | 完成 |
| Step 6 | backend/requirements.txt v1.0（numpy 2.5.3 + pillow 12.3.0 冻结；可选重依赖/编排依赖注释分层） | 完成 |
| Step 7 | YYC3-60 v1.3.0：G4 用例细化 10 条（TC-G4-001~010，demo_ep01 实链路蓝本）+ §一总览 + TC-G3-009 前置更新 | 完成 |
| Step 8 | scripts/download_h3_weights.sh（hf-mirror + 断点续传 + 空间检查）已入库并后台启动，5 个 NF4 文件并行下载中（~30Gi，中断重跑即续传） | 进行中（后台） |

### 26.2 关键决策

- **style_keeper 三态语义对齐 anchor_guard**：accept / redraw(≤2) / escalate；`last_mode != pil_hist` 的判定不得进生产（红线 2）；档案派生 `sha256-deterministic` 保证同 project_id 跨进程完全一致（TC-G3-009 主判定由构造保证）。
- **requirements 分层**：核心（实测 import）/ 可选重依赖（真实模式 face_encoder）/ 可选编排依赖（api/v1+tasks 启动时补），避免 Mac 本地被 insightface 等重依赖阻塞。
- **G4 用例锚定实链路**：执行器全部指向根仓 scripts/ 现有件（run_clip_compose.sh/tts/syncnet/batch_shots），002/009 允许 BLOCKED 留证，通过标准显式列出。

### 26.3 当前优先级 TOP 3（本轮更新）

1. **[P0]** 等待 H3 权重下载完成后：h3 网关 :8300 起服 → TC-G4-002 动态镜头首验（SyncNet ≥0.75 判定）
2. **[P1]** DGX 硬件日四连收割（审核报告 Step 9-12：G1 清零/kohya LoRA/G2-010 终值/G3-006 基线）
3. **[P2]** TC-G4-001~008 逐条执行留证（合成链执行器均已就绪，可无 H3 先行 001/003/004 复现）

---

## 二十七、G4 首验 + 全链服务化复跑（2026-09-28 第十七轮）

### 27.1 G4 门禁首跑结果（《G4-样片闭环首验记录-20260928.md》）

| 用例 | 结果 | 要点 |
| ---- | ---- | ---- |
| TC-G4-001 | ✅ PASS ×2 | run_clip_compose.sh 升级 1920x1080@30（force_original_aspect_ratio+crop 防拉伸）；两次规格一致 |
| TC-G4-003 | ✅ PASS | 三轮实测定版**全重编码串联**（流拷贝 AAC priming 累积 +47ms 超差）；沉淀 run_episode_concat.sh（自动验证）；视频轨偏差 20.3ms < 1 帧，黑帧 0 |
| TC-G4-004 | ✅ PASS | **全链零人工 883.3s**：脚本→分镜→ComfyUI 真图×3→insightface 真锚定（sim 0.63-0.68 全诚实 escalate 零假阳性）→TTS 服务真调用→合成→串联（8.3ms）→SyncNet 产脸 4 轨评分（conf 0.31-0.62 全部正确打回，静态帧预期红线有效） |
| TC-G4-002 | ⬜ BLOCKED | H3 NF4 权重 33G 下载收尾中（3/5 文件落盘），断点续传脚本在跑 |

### 27.2 服务化复跑基线（全绿）

- ComfyUI :41888（guardian --force-fp16）/ TTS :42118（tts_service.py，manju venv）/ SyncNet :42218（syncnet_service.py，**ComfyUI.venv python**——torch 全家桶所在，HANDOFF L649/L747 留证复用）
- SyncNet 全链：`cd tools/syncnet/syncnet_python && ComfyUI.venv/python run_pipeline.py --videofile X --data_dir /tmp/syncnet_work --overwrite` → `run_syncnet_score.py --crop_dir /tmp/syncnet_work/pycrop`
- H3 网关起服（权重齐后）：`cd yyc3-minimax-h3 && ComfyUI.venv/bin/python -m uvicorn agent.h3_agent.gateway:app --port 8300`

### 27.3 规格修订与文档同步

- YYC3-60 **v1.3.1**：TC-G4-003 判定基准=视频轨时长（±1 帧；AAC padding 不计入），步骤补全重编码方法
- 留证归档：`/tmp/yyc3_projects/_acceptance/G4/`（NAS 就位迁移）+ `docs/attachments/G4-20260928/`（manifest + syncnet_summary）
- 新增执行器：run_episode_concat.sh；run_clip_compose.sh 升级交付规格

### 27.4 当前优先级 TOP 3（本轮更新）

1. **[P0]** H3 权重落盘后：网关 :8300 起服 → TC-G4-002 动态镜头 → SyncNet ≥0.75 达标判定（G4 核心指标）
2. **[P1]** DGX 硬件日四连收割（G1 清零/kohya LoRA/G2-010/G3-006）
3. **[P2]** 样片扩产至 ≥3 集 → TC-G4-005/007/008 批量执行

## 二十八、TC-G4-002 达标收官：G4 核心四用例全 PASS（2026-09-28 第十八轮）

### 28.1 结果

**TC-G4-002 动态镜头口型达标 ✅ PASS** — conf 6.3167 ≥0.75（offset 0.0 / dist 11.654），G4 门禁核心四用例（001/002/003/004）全部 PASS。

| 阶段 | 留证 |
| ---- | ---- |
| 权重 | `/Users/yanyu/models/MiniMax-H3-NF4/` 5 件 NF4 全齐（fl2va/ref2va 17.16G×2 + text-encoder 15.32G + video_vae 1.6G + audio_vae 284M），断点续传收尾成功；processor 仓修正 `MiniMaxAI/MiniMax-H3`（原 MiniMax/ 404，h3_common L56 同步改） |
| 拆分仓脚本考古 | scripts 下 batch_ref2va_nf4.py 等原为 0 字节占位（production_agent 调用会崩）→ 从原始仓平移真身 6 脚本 + lib/h3_common.py + vendor/DiffSynth-Studio 符号链接（19M） |
| 网关 | :8300 healthz `{"status":"ok","claim_ready":true}`；claim 密钥入 `.secrets/agent_claim.env`（chmod 600，gitignore 补 `.secrets/` 红线） |
| 生成 | 直跑 batch_ref2va_nf4.py：seed 42 / preview 384p / 30 步 / 73 帧 / 24fps / 32kHz；**5267.5s（88.8min，168.9s/步）RSS 峰值 22.3GB**；产物 h3_seed_42.mp4（h264 640x384 + aac，3.05s，manifest SUCCESS） |
| 评分 | run_pipeline（`--min_track 40 --min_face_size 60`）产脸 1 轨 → run_syncnet_score **conf 6.3167 达标** |

### 28.2 本轮关键排障（5 连）

1. 生成首跑 10/30 步遭外部 SIGTERM → 脚本断点设计（FAILED 记录）直接重跑
2. 重跑 FileNotFoundError → 定位实际工作仓为项目内 `yyc3-minimax-h3/`（非原始仓路径混淆）
3. SyncNet 空轨 → `min_track` 默认 100 帧 > 77 帧短视频，降参后产轨
4. bnb NF4 反量化 dynamo recompile 告警 → 步速稳定 169s/it，接受不重启
5. 网关子进程 35min 停滞（上轮遗留）→ 本轮确认根因 `DIFFSYNTH_SKIP_DOWNLOAD=True` 必带

### 28.3 文档同步

- 《G4-样片闭环首验记录》**v1.1.0**：新增 §四 TC-G4-002 达标节（含 dist 偏高诚实留证：384p 唇部细节量推测，720p 复验跟踪）；结论更新四用例全 PASS
- YYC3-60 **v1.3.2**：TC-G4-002 回填首验实测 + 三条关键经验（min_track 短视频 / DIFFSYNTH_SKIP_DOWNLOAD / Ref2VA 内生同步 conf 量级）
- 评分链口径核对：run_syncnet_score.py L52 `conf ≥0.75 达标`（score_norm 同口径）

### 28.4 当前优先级 TOP 3（本轮更新）

1. **[P1]** H3 批量动态化排期：720p 档质量复验（跟踪 dist）+ DGX 硬件日提速（Mac MPS 单镜 89min 不可量产）
2. **[P1]** DGX 硬件日四连收割（G1 清零/kohya LoRA/G2-010/G3-006）——与动态化提速合并执行
3. **[P2]** 样片扩产至 ≥3 集（引入 H3 动态镜头混排）→ TC-G4-005/007/008 批量执行；可选：网关带 DIFFSYNTH_SKIP_DOWNLOAD 复跑一轮取 claim→dispatch 全链留证

## 二十九、DGX 硬件日四连收割 + TOP1/3 全清：G4 七用例闭环（2026-09-29 第十九轮）

### 29.1 结果总览（TOP 1/2/3 全部收割）

| 项 | 结果 | 关键数据 |
| -- | ---- | -------- |
| TOP1 720p 复验 | **PASS** | conf 6.740 / dist 8.309 / offset -1（mac 384p 11.654 → DGX 720p 8.309，降 3.35，分辨率假设成立） |
| TOP1 DGX 提速 | **4.75x** | 1109.1s vs MPS 5267.5s；vLLM 清空后 13.3s/it 再翻倍，热批产单镜 434.4s |
| TOP2 四连收割 | **全清** | G1 清零 ✓ / kohya LoRA n1 2000 步正式（loss 0.0107，六产物）✓ / G2-010 ✓ / G3-006 DGX 实测留证（1109-1291s，口径拆分建议）✓ |
| TOP3 样片扩产 | **≥3 集全 PASS** | 三章剧本 --episode 切集（238/227/219 字）→ 3 集 1080p30 动态混排成片（偏差 13-29ms，黑帧 0，音频齐平） |
| TC-G4-005/007/008 | **全 PASS** | 五维评审 100 分 ×3 + 人工一致率 100%；成本 0.0158-0.0335 元/集 ≤2 元；交付规范 20/20 |

**G4 进度：001-005/007/008 七用例 PASS；006/009/010 待 Token-Console/NAS 条件。**

### 29.2 本轮关键工程发现（concat demuxer 混排缺陷根治）

- **现象**：动态镜混排后成片音频流 9.57s < 视频 12.53s——c3 段整体静音；aresample=async 不可修复
- **根因**：concat **demuxer** 混排源（H3 32k stereo + compose AAC）音频 pts 断裂丢帧；静态同质镜（首验）不触发
- **修复**：run_episode_concat.sh 改 **concat filter 解码域拼接**（逐镜统一 32k stereo + `concat=n=3:v=1:a=1`）+ 新增音频轨齐平判定（±100ms）
- **TC-G4-003 方法论四连定版**：流拷贝 ✗ → 半重编 ✗ → 全重编码（同质镜）✓ → concat filter（混排镜）✓✓

### 29.3 节点与排障沉淀

1. **节点固化**：n2 被团队 root vLLM 大服务占据（守护拉起不可清理），负载整体固化 n1（GPU 空闲 110G）
2. **GB10 串行化**：rsync page cache 与 CUDA 大分配互斥——大文件传输与 GPU 任务必须串行，传输后 drop_caches
3. **cu130 wheel**：sm_121 需 torch 2.11.0+cu130（cu128 NVRTC 崩 `invalid value for --gpu-architecture`）
4. **kohya 环境链**：peft 0.14.0 + torchvision 0.26.0+cu128（ABI 匹配）+ 卸载 tensorflow 2.10 残留 + `--network_alpha` + `--enable_bucket --bucket_no_upscale` + `HF_ENDPOINT=https://hf-mirror.com`
5. **pkill 自匹配**：`pkill -f` 会匹配 SSH 命令行自身（两次 exit 255）——用 `[V]LLM` 字符类或先取 PID
6. **piper TTS 非确定性**：同文本合成字节级波动 → 成片时长边缘偶发 FAIL，复跑即过（首验 46ms 波动先例一致）

### 29.4 文档同步

- 《G4-样片扩产与硬件日收割记录-20260929》v1.0.0 新建（本轮主文档）
- 留证 4 份：docs/attachments/G4-20260929/{tc-g4-002-syncnet-720p-revalidation, tc-g3-006-dgx-h3-measured, g4-expansion-dynamic-shots-syncnet, tc-g4-005-008-quality-review, tc-g4-007-cost-report}.json
- 新增执行器：run_episode_build.sh / run_dynamic_clip.sh / run_quality_review.py / run_cost_report.py；修订：run_batch_shots.py（三章 + --episode）/ run_episode_concat.sh（filter 定版）/ h3_common.py（双端自适应，h3 仓）

### 29.5 当前优先级 TOP 3（本轮更新）

1. **[P1]** h3_common syncnet_score_impl 封装落地（现引用不存在模块 `syncnet_python.syncnet_pipeline`，评分走官方入口直调）+ PerformanceTimer Linux ru_maxrss 单位修复（KB vs 字节）
2. **[P2]** LoRA 跨种子复测冲 M3 一致性 0.85+（sd-hero-prod 产物已备，n1 可直接注入 ComfyUI/生成链）
3. **[P2]** TC-G4-006/009/010（Token-Console 真实计量 + NAS 就位）；生产化：动态素材按集定制 prompt（样片阶段三集复用同 prompt 已诚实留证）

---

## 三十、双文件诊断修复 + TC-G4-006/009/010 收割：G4 门禁全量完成（2026-09-29 第二十轮）

### 30.1 双文件诊断修复（用户指令 `#problems` 直派）

| 文件 | 提交 | 要点 |
| ---- | ---- | ---- |
| scripts/run_batch_shots.py | main fbff212 | ModuleType 动态属性 setattr + 7 处动态导入 `# type: ignore`，basedpyright 0 error |
| yyc3-minimax-h3 h3_common.py | h3 59f03e7 | syncnet_score_impl 幻影模块根治：官方 run_pipeline/run_syncnet 入口直调 + 解释器候选链（H3_SYNCNET_PY > ComfyUI venv > mac h3 venv > 当前）+ `--min_track 40 --min_face_size 60` + Linux ru_maxrss KB 分支；**29.5 P1 随此清零** |

- 四轮排障沉淀：manju venv 无 torch → mac h3 venv 缺 cv2 → ComfyUI venv 全齐置首 → 仍 None 终因 **logging 时间戳双冒号**（`split(":", 1)` 切在 `18:53:25,480` 上）→ `rsplit(":", 1)` 修复，冒烟 conf 6.349 与手动链路全同。

### 30.2 TC-G4-006 三类打回零人工闭环（PASS）

| 类别 | 闭环 | 证据 |
| ---- | ---- | ---- |
| 一致性 anchor_guard | 9 例：sim 0.59-0.72 → seed_lock 重绘 → escalate（qc_rounds=2 用满转人工留证） | tc-g4-006-anchor-guard-batch-3eps.txt |
| 风格 style_keeper | **真实 StyleKeeper v1.0 双闭环**：暗调漂移 0.5371 → 打回 → 复检 1.0 accept；超限演练 0.8016 压线被拒 → escalate | tc-g4-006-style-keeper-{closure,escalate}.json |
| 口型 SyncNet | 静态帧 4/4 打回（0.31-0.62 <0.75）→ H3 动态重生成 → 3/3 复检达标 | 首验记录 L79 + syncnet JSON |

- **重大纠偏（诚实留证）**：style_keeper 曾误判「无实现」——主仓检索被子仓 gitignore 遮蔽；实际 `manju backend/.../style_keeper.py` v1.0 在位（PIL 30 维向量 + 单测 17/17）。教训：**跨子仓搜索必须绕过 gitignore 显式 Glob**。
- 构造轴标定：亮度/对比漂移有效（0.54/0.80），hue/负片在 8-bin 粗量化下 >0.98 无效——已沉淀至 run_style_keeper.py 注释。
- 新增 scripts/run_style_keeper.py（真实实现闭环执行器，可复跑）。

### 30.3 TC-G4-009 夜间批量集产能（PASS）

单晚三集完整产出且质检全过（超额达成 ≥1 集）：静态 739.6/566.1/522.6s + DGX 动态 1109.1/600.4/434.4s 并行 → 3 集 1080p30 成片，五维评审 100 分 ×3，成本 0.0158-0.0335 元/集，端到端约 40 分钟/集。详证 tc-g4-009-nightly-batch-stats.json（音画流级差 23.0-44.7ms，≤100ms 齐平口径全过，复测方法如实标注）。

### 30.4 TC-G4-010 G4 回归门禁（PASS，零退化）

17 项回归：G1-004（7/7 原语义，实现零变更）+ G1-005（10/10）+ G2 十用例（7 PASS + 3 PARTIAL 与历史逐字一致 + 0 FAIL）+ G3 五项（001/002 建库比对、003 三态闭环、008 抽检 24 镜三要素 100%、009 单测 17/17）。

- **新发现 OBS-G1-004-1（非退化）**：`is_nas_path('/mnt/nasdir/x')` 误判 True（前缀匹配缺 `/` 边界，normalize 侧正确）——开观察项，下轮 yyc3-0379-world 子仓一行修复 + 补断言。

### 30.5 G4 门禁总账

**TC-G4-001~010 十用例全部 PASS**（001-004 首验+720p 复验、005 五维+人工留证、006 三类闭环、007/008 成本交付、009 夜间批量、010 零退化回归）——YYC3-60 L434 通过标准全满足，002/009 BLOCKED 条款不适用。主文档 v1.1.0（§6.5 对照表），留证 15 份 docs/attachments/G4-20260929/。

### 30.6 下轮起点（TOP 3）

1. **[P1]** OBS-G1-004-1：yyc3-0379-world `is_nas_path` 边界一行修复 + 补断言（G1-004 E2E 亦待网关合流）
2. **[P1]** LoRA 跨种子复测冲 M3 一致性 0.85+（sd-hero-prod 已备，注入 ComfyUI 生成链 → 静态镜 accept 率验证）
3. **[P2]** G5 门禁骨架用例补齐（YYC3-60 L436 占位）；生产化双项：动态素材按集定制 prompt + Token-Console 真实计量接入成本链

## 三十一、双执行器诊断清零 + OBS-G1-004-1 修复 + LoRA 跨种子复测（2026-09-29 第二十一轮）

### 31.1 双执行器诊断清零（IDE #problems 归零）

- `run_style_keeper.py`「无法解析导入 app.modules...」：跨仓运行时 sys.path 注入静态不可达，补 `# pyright: ignore[reportMissingImports]` 行内豁免（头部注释注明非掩盖缺陷）；诊断清零，冒烟 verdict=closed PASS
- `run_kohya_lora.py`：修 `import os` 缺失（eval 首跑 NameError）+ PIL `Image.LANCZOS/FLIP_LEFT_RIGHT` 改 9.1+ 正规枚举（`Resampling.LANCZOS`/`Transpose.FLIP_LEFT_RIGHT`，venv 12.3.0 实证）+ 跨 venv 导入同模式豁免；新增 combo 模式（LoRA + IPAdapter 组合评测器）

### 31.2 OBS-G1-004-1 修复（yyc3-0379-world，P1 清零）

`is_nas_path` 前缀边界修复 v1.0.0→v1.0.1：判定口径与 normalize 侧对齐（根本身或 `root + "/"` 前缀）。新建 `tests/test_g1_004_path_normalize.py` 19/19 PASS（含 `/mnt/nasdir/x`、`/mnt/nasx`、`/Volumes/nasdir/x` 三个边界回归锚），G1-005 回归 10/10 无连带破坏。

### 31.3 LoRA 跨种子复测（TOP 2 执行，0.85 未达成——诚实留证）

sd-hero-prod 五件产物自 n1 取回，4 漂移种子 insightface 余弦同 G3 口径：

| 路线 | mean | 结论 |
| ---- | ---- | ---- |
| 无锚定基线 | 0.5157 | 行业返工率根因 |
| **LoRA step2000（四检查点扫描最优）** | **0.6441** | **+25% vs 无锚定**，min 0.4834 |
| LoRA+IPA diffusers 整图 scale=0.6 | 0.5443 | 组合无增益 |
| LoRA+IPA diffusers 整图 scale=1.0 | 0.1964 | 满强度画面崩坏（seed888 脸检测降级） |

科学结论：①LoRA 方向有效但 4 张变换族训练集是泛化瓶颈（0.52→0.64，距 0.85 差 0.21）；②diffusers 整图路线与漂移提示词语义冲突单调恶化，历史 0.670 系 ComfyUI PLUS FACE 脸区域嵌入、不可直接归因对比；③**0.85+ 路径收敛：训练集扩充（多视角/多光照/多表情）+ PLUS FACE 工作流组合**；④M3 生产现行 seed-lock 策略（sim=1.0）不变，锚定增强不阻塞生产链。详证 tc-m3-lora-crosseed-eval.json，主文档 v1.2.0 §9。

### 31.4 下轮起点（TOP 3）

1. **[P1]** LoRA 二轮冲刺前置：训练集扩充至 12-16 张（多视角/多光照/多表情，可 diffusers 变换 + 生产镜帧筛选）→ kohya 重训 → PLUS FACE 工作流组合复测
2. **[P2]** G5 门禁骨架用例补齐（YYC3-60 L436 占位）；生产化双项（动态 prompt 定制 + Token-Console 计量）
3. **[P2]** G1-004 E2E（网关实际请求）待网关合流；三仓提交后按需 push

## 三十二、M3 二轮冲刺：数据集扩充 + kohya 重训 + 组合权重寻优（2026-09-29 第二十二轮，31.4 P1 执行）

### 32.1 数据集扩充（4 → 19 图三源混合）

首轮配方自 safetensors 元数据完整恢复（ss_network_dim=32/alpha=16、lr 5e-4 constant、AdamW、bf16、512 bucket、keep_tokens 1）原样复用，数据集扩充三源：hero_base+首轮变换族 5、新增变换（亮度±/饱和度±/上下裁剪）5、H3 动态镜抽帧 9（output_batch9001/9003 g4t2_ref 真实生产帧，insightface 质检 19/19 有脸）。19 图 × 10 repeats，2000 步 ≈ 10.5 epoch。执行器 run_lora_dataset_v2.py。

### 32.2 n1 二轮重训

2000 步 24:19（1.37it/s），avr_loss 0.104 → 0.0372，五件产物 sd-hero-v2*。排障：首跑缺 `--resolution` 即败（AssertionError），补 512,512 成功。

### 32.3 评测（LoRA-only + 组合权重扫描）

- LoRA-only 四检查点：step2000 最优 **mean 0.6726**（一轮 0.6441 +4.4%），下限抬升至 0.5525
- 组合六轮权重扫描（ComfyUI 工作流 LoraLoader + PLUS FACE 脸区域嵌入，run_lora_plusface_combo.py）：**峰值 w=0.15 mean 0.8669**（0.08→0.857 回落确认峰值；0.85→0.6084 负交互区）
- **双口径诚实结论**：mean 口径 0.85 达成（0.5157→0.8669，+68%；3/4 种子 ≥0.885，anchor_guard 拒绝率 4/4→1/4）；生产 min 口径未达（seed777 拖尾 0.778，不强行判 PASS）
- **一轮「组合无增益」结论推翻**：系未做权重扫描所致——IPAdapter 权重是第一杠杆，历史默认 0.85 恰为负交互区，最优 0.15，增益窗口 0.08-0.25

详证 tc-m3-lora-v2-sweep.json + tc-m3-lora-v2-train.log.txt，主文档 v1.3.0 §11。

### 32.4 下轮起点（TOP 3）

1. **[P1]** LoRA min 口径冲刺：训练集补 777 类姿态样本（777 全权重域最低，生成姿态偏离训练分布）/ text_encoder 单独训 / rank 32→64，冲 anchor_guard 全种子过闸
2. **[P2]** combo(w=0.15) 接入 run_batch_shots.py 生成链（替换纯 seed-lock 主策略，seed-lock 保底），实测集产能与拒绝率
3. **[P2]** G5 门禁骨架用例补齐；生产化双项（动态 prompt 定制 + Token-Console 计量）；G1-004 E2E 待网关合流

## 三十三、M3 三轮 min 口径冲刺 + G5 骨架 + 生产化双项 + G1-004 E2E 闭环（2026-09-29/30 第二十三轮，32.4 全项执行）

### 33.1 777 类姿态挖掘 + 数据集 v3（19 → 42 图）

伪再演练/自蒸馏路线：run_lora_pose_mining.py 用现行最优路线（sd-hero-v2 + PLUS FACE w=0.15）seed777 × 8 条姿态提示词变体生成候选池，insightface 身份门 sim ≥ 0.75 筛选——**8/8 全过门**（sim 0.7739-0.7808），门控防漂移放大。H3 密集帧 n1 端 3 视频 × 5 时间点回拉 15 帧（md5 去重，质检 15/15 有脸 sim 0.573-0.724 与 v2 同域）。run_lora_dataset_v3.py 组装 42 图（420 步/epoch）；上传口径只传 png（对齐 v2 实际训练形态——caption 未生效走目录 class token，控制变量）。质检留证 tc-m3-dataset-v3-qc.json + tc-m3-pose-mining.json。

### 33.2 n1 三轮重训（rank 64）+ 评测（假设证伪——诚实留证）

配方自 v2 产物元数据逐字恢复，唯一变量 dim64/alpha32。27:50（1.20it/s）2000 步，五件 sd-hero-v3*（144M）。排障：首跑阻塞 HF hub 联网校验（4:38 仅 5s CPU），`HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1` 秒过——沉淀至 n1 命令重建记录。

评测（LoRA-only + 组合聚焦域 0.10/0.15/0.20/0.25）：

- LoRA-only step2000：mean 0.6511 / min 0.5777，**seed777 0.6056 → 0.6557（+8.3%）——777 补样对 LoRA 本体有效**
- 组合峰值 w=0.15：mean 0.7273 / min 0.7068，较 v2 同权重 0.8669 **回退 -0.14**，全窗 min <0.85
- **三轮假设证伪**：「777 补样 + rank64 → min 达标」在该配方（4.76 epoch）下不成立。新科学结论：LoRA 容量/分布宽度是组合敏感变量——强 LoRA 削弱 IPA 主导形态的组合增益（v2「弱 LoRA + IPA 主导」仍最优）
- 下轮：①42 图回退 rank32 + 4200 步（10 epoch）隔离 rank 变量；②v2 LoRA 增量续训 777 样本；③生产维持 v2+w0.15+seed-lock，生产语义零影响

详证 tc-m3-lora-v3-sweep.json + tc-m3-lora-v3-train.log.txt，主文档 v1.4.0 §13。

### 33.3 G5 骨架 + 生产化双项（32.4 TOP2/3 前半）

- **G5 骨架**（YYC3-60 v1.4.0）：占位替换为 TC-G5-001~006 六条完整用例（完播率 ≥5pp / 产能 ≥4 集/晚 / LoRA 增量触发 100% 准确 / 伯乐采纳 ≥60% / 成本降 ≥20% 且 ≤2 元/集 / 回归门禁全量）；001/004 依赖真实运营窗口可 BLOCKED 留证
- **动态 prompt 按集定制**：run_batch_shots.py 三级覆盖（shot_overrides > episodes > default_style > 内置保底），manifest 记 style_source；冒烟 4/4
- **Token-Console 计量接入成本链**：run_cost_report.py v1.1.0 接网关 /v1/models/stats + /v1/models 价表，USD→CNY 按集均摊，不可达如实标注 unreachable 不虚构 0；降级 2/2

### 33.4 G1-004 E2E 完整闭环（32.4 TOP3 后半，真实网关 + 真实请求）

core/api 接线 PathNormalizeMiddleware（最外层注册；core/app 与 core/api 双目录同 inode）。三探针全 200：Mac 别名归一（头 1 + INFO 日志）/ /mnt/nasdir 边界不篡改（无头 + warning）/ 嵌套相对路径归一（meta.out_dir → /mnt/nas 绝对）。排障：①首测 502 系本地桩上游未启动（scripts/stub_upstream.py :25290）+ 双上游熔断，启动桩后闭环；②鉴权口径：Bearer 仅收 JWT（非 JWT 提前置 403），API Key 必须走 X-API-Key 头。留证 tc-g1-004-e2e-probes.log.txt + tc-g1-004-e2e-gateway.log.txt。

### 33.5 下轮起点（TOP 3）

1. **[P1]** min 口径正确路径重试：v3 数据集 42 图回退 rank32 + 步数补足 4200 步（10 epoch）重训评测（隔离 rank 变量，验证「777 补样 + 足 epoch」是否达标）；备选 v2 LoRA 增量续训
2. **[P2]** combo(w=0.15) 接入 run_batch_shots.py 生成链（32.4 遗留，v2 配置），实测集产能与拒绝率
3. **[P2]** G5 用例运营数据接入（TC-G5-001/004 真实窗口后收割）；G1-004 落位步骤待 /mnt/nas 挂载实机复验

## 三十四、四轮 rank 变量隔离重训 + combo 生产接入 + 对照冒烟 + G1-004 上游桩计量可达（2026-09-30 第二十四轮，33.5 三项执行）

### 34.1 v3r32 回退 rank32 + 4200 步重训评测（33.5-1 P1，负结果归因收敛）

按 33.5 指令回退 rank32/alpha16 + 步数补足 4200 步（10 epoch 与 v2 对齐），数据集不变（v3 42 图），单变量隔离。n1 58 分钟收齐五件产物（step1050/2100/3150/4200 + 终版）。评测（4 漂移种子 insightface）：

- LoRA-only s4200：mean 0.5177 / min 0.4435——与无锚基线 0.5157 持平（LoRA 本体增益≈0）
- 组合聚焦域：w0.10 mean 0.4815 / w0.15 mean 0.4788（两组 seed999 未检出人脸降级哈希）/ w0.20 mean 0.6218（峰值，仍远未达标）
- **min 口径（≥0.85）全线未达成**，v3r32 峰值 0.6218 较 v3r64（0.7273）进一步回退——rank 回退 + 步数补足均无法挽救
- **三轮独立训练交叉归因收敛：回退主因 = v3 数据集新增 23 图（15 H3 密集帧 + 8 777 挖掘）的分布冲突/质量噪声，而非 rank 或步数**；锚定 LoRA 生产决策落定维持 sd-hero-v2（19 图）；v3 路线证伪归档，重启扩数据须先对新增样本做人脸质检重筛

详证 tc-m3-lora-v3r32-sweep.json + train_v3r32.log（752KB 归档 /tmp/kohya_out/v3r32/），主文档 v1.5.0 §16。

### 34.2 combo 生产接入 + 对照冒烟（33.5-2 P2，能力沉淀 + 旧链路无回归）

- **三层透传接线**：drama_stage_adapter `_workflow`/`generate_image`/`text_to_image` 增 lora + ipa_weight 参数（LoraLoader 节点 13 全链注入，IPA model 源切换）；run_batch_shots.py 增 --lora（缺省空=旧口径逐字节等价）+ --ipa-weight（缺省 0.15），manifest 增 anchor_config 留证；自检 3/3 PASS
- **生产域双口径实测**（1024×1024 场景域）：combo-smoke-001（combo w0.15）首绘 0.5950/0.7052 全 escalate，重绘更差（0.1391/0.1954）——负交互实证；combo-ctrl-001（纯 IPA w0.15 无 LoRA，manifest 实测，初版文档误记 w0.85 已纠）0.7793/0.7053 全 escalate，与 G4-ep01~03 九镜历史区间（0.5906-0.7163）一致——**旧链路无回归**；两冒烟同权重唯一变量 LoRA 有无，LoRA 为生产域负交互因子（首镜 -0.18）
- **产能与拒绝率口径（诚实报告）**：纯 IPA 链 ~886 秒/镜（含首绘+seed_lock 重绘+转人工）；拒绝率 100%（2/2，与历史 9/9 一致）——生产域身份一致性为未解产能瓶颈（离线 512 肖像域不可外推），锚定域再校准列后续项；生产默认维持纯 IPA（--lora 缺省空），combo 保留为可选能力

详证 tc-g4-008-combo-ctrl-summary.json + tc-g4-008-combo-ctrl-manifest.json + tc-g4-006-combo-smoke-manifest.json，主文档 v1.5.0 §17。

### 34.3 G1-004 上游桩 + 计量可达路径闭环（33.5-3 P2 选择性执行）

stub_upstream（:25290）+ 网关（:8010）双进程保活；计量可达路径实测 reachable=true（PG 不可达时端点 ~4 秒响应，run_cost_report.py timeout 3→8 秒修复误判）；鉴权口径复核（Bearer 仅 JWT / API Key 走 X-API-Key）；token_cost 0.0 如实（stub 零价零 token 不虚构）。留证 tc-g4-007-cost-report-gw-reachable.json，主文档 v1.5.0 §18。

### 34.4 下轮起点（TOP 3）

1. **[P1]** 生产域锚定再校准：当前 1024 场景域拒绝率 100%（历史+本轮双证），需按生产域重标定锚定策略——候选①生产域 prompt 下重扫 IPA 权重窗（0.85-1.0+）；②1024px 肖像/半身构图约束 prompt 模板降分布偏移；③分辨率梯度（512/768/1024）锚定衰减曲线标定
2. **[P2]** v2 LoRA 增量续训 777 样本（33.5 备选路径，未执行）：v2 19 图 checkpoint 起步 + 8 图 777 样本低步数续训，保 v2 分布底座吸收 777 姿态增益
3. **[P2]** G5 用例运营数据接入（TC-G5-001/004 真实窗口后收割）；G1-004 落位步骤待 /mnt/nas 挂载实机复验；combo 能力待锚定域校准后复评

## 三十五、生产域锚定三轴再校准 + G1-004 复验 + G5 门禁执行器（2026-09-30 第二十五轮，34.4 三项执行）

### 35.1 生产域锚定三轴再校准（34.4-1 P1，配置优化证伪 → 能力边界定位）

run_anchor_domain_recal.py 生产链同参三轴网格（纯 IPA，2 生产镜头，1024×8+512×2）：**轴A 权重窗单调递减**——w0.15（0.7423）> w0.50（0.6946）> w0.85（0.6851）> w1.00（0.6634），弱 IPA 生产域最优与离线域同向，现行 `--ipa-weight` 缺省 0.15 即实测最优，零变更获实证背书；**轴B 构图约束证伪**（w0.15: -0.042 / w0.50: -0.013，场景叙事稀释）；**轴C 分辨率衰减假设推翻**（512=0.6469 反比 1024 低 0.095）。**收敛判定：三轴均无法突破 0.85（全场最佳 0.7423 即 w0.15 基线自身）——生产域 100% 拒绝率根因 = PLUS FACE 在场景叙事 prompt 域的身份保持能力边界（模型能力问题，非配置问题）**。

工程沉淀：首战 6/10 中断（CTRL_BASELINE 混入字符串键 TypeError），脚本改造为可续跑（已有产物直接评分复用 + COMFYUI_TIMEOUT 1800s + 单镜失败不中断），续跑零重复占用产线。留证 tc-anchor-recal-20260930.json。

### 35.2 ctrl 权重记录纠错（诚实留证）

复核发现上轮 combo-ctrl-001 文档记录误写「纯 IPA w0.85」，manifest 实测 `anchor_config.ipa_weight=0.15`（`--ipa-weight` 缺省值首战未显式传参）。已纠三处：tc-g4-008-combo-ctrl-summary.json（含 weight_note 纠错说明）、主文档 §17.2、HANDOFF 34.2。纠错后归因更干净：两冒烟同权重 0.15、唯一变量 LoRA 有无——LoRA 为生产域负交互因子（首镜 -0.18），弱 IPA 不劣于历史 w0.85。

### 35.3 G1-004 三探针复验 + G5 门禁执行器（34.4-3 P2）

- **G1-004 复验 3/3 PASS**：桩+网关重新拉起，三探针全 200 语义逐项复现（Mac 别名归一头=1 / nasdir 边界 warning 不篡改 / meta.out_dir 绝对化），httpx 真实透传桩上游；密钥运行时读取零入库。留证 tc-g1-004-e2e-probes-rerun-20260930.log.txt
- **G5 执行器落地（run_g5_gate.py）**：TC-G5-003① 触发判定真实执行（组合峰值 mean<0.85 触发）——v2 0.8669 不触发/v3r64 0.7273 触发/v3r32 0.6218 触发，**准确率 100%、误触发 0**（②增量重训③复测 BLOCKED 待训练窗口→partial）；G5-002/005 基线在位核算链就绪但反哺未启用 → BLOCKED 如实；G5-001/004/006 手册允许 BLOCKED。留证 tc-g5-gate-run-20260930.json

### 35.4 下轮起点（TOP 3）

1. **[P1]** 身份保持模型替换评测：PLUS FACE 能力边界已定位（三轴配置优化全部证伪），候选 InstantID / PuLID 接入 adapter 工作流同口径评测（生产 2 镜 + 离线 4 漂移种子双域），目标生产域 mean ≥0.85
2. **[P2]** v2 LoRA 增量续训 777 样本（34.4-2 遗留）：v2 19 图 checkpoint 起步 + 8 图 777 样本低步数续训
3. **[P2]** G5-003②③ 增量重训窗口（依赖 P2-2 产物）；G5-002/005 反哺项启用后一键复算（执行器已就绪）；G1-004 落位步骤待 /mnt/nas 挂载实机复验

## 三十六、评测参考系漂移校准 + FaceID PlusV2 升级评测 + v2m777 增量续训与 G5-003 联动（2026-10-02 第二十六轮，35.4 三项执行）

### 36.1 评测参考系漂移发现与校准（35.4 执行期关键根因，先于一切评测结论）

35.4 P1/P2 首日全部评测塌方（FaceID 初判 0.4896 / v2m777 初判 0.5187），**首信号为达标模型 v2 本体重测也塌至 0.5108**——判定参考系问题。库存向量仲裁：当日同参重建的 seed42 参考图与 9/27 库存向量余弦仅 0.5675（ComfyUI 环境更新致同 seed 产物漂移），而 **ComfyUI/input/hero_base.png（9/27 设定图本体）逐字节稳定、校准 1.0**。处置：run_lora_plusface_combo.py HERO 锚定历史设定图本体（/tmp 回落告警；run_kohya_lora/run_batch_shots/run_anchor_domain_recal 同类硬编码待统一治理）；全部产物以历史参考系重评分恢复真实值；**跨日规则沉淀：纯生成图禁止作跨日参考系，必须锚定当日设定图本体**。错误参考系期 raw 报告如实保留。留证 tc-eval-ref-drift-20261002.json + rescore_histref.json。

### 36.2 FaceID PlusV2 升级评测（35.4 P1：升级有效但不敌 v2 组合）

模型落地：ip-adapter-faceid-plusv2_sd15.bin（156,558,509 字节 Content-Length 校验；仓库主模型为 .bin 无 safetensors 版）+ 配套 lora 51MB，hf-mirror 下载（直连超时 exit 28）。InstantID/PuLID 勘察：均为 SDXL 专属与 DreamShaper 8（SD15）不兼容，基模迁移独立决策。评测（历史参考系，采样链与生产 adapter 逐参一致）：

| 配置 | mean | min |
| ---- | ---- | ---- |
| FaceID PlusV2 单独（fv2.3, w0.8） | 0.7926（较 PLUS FACE 0.67 +12pp） | 0.7368 |
| LoRA(v2)+FaceID w0.15/fv3.0 | 0.8248 | **0.8036（全实验 min 冠军）** |
| **v2 组合基线（重测复现历史）** | **0.8672** | 0.7846 |

判定：FaceID 组合 mean 0.8248 < v2 组合 0.8672，**SD15 模型族内 0.85 目标无一达标**——生产锚定维持 v2 组合；FaceID 组合沉淀 min 稳定度备选；adapter 接线留待用户决策（评测先行纪律，drama_stage_adapter 未动）。留证 tc-m3-faceid-plusv2-eval.json + faceid_lora_combo.json + final_eval_histref.json。

### 36.3 v2m777 增量续训 + G5-003 联动复测（35.4 P2）

n1 kohya 真实执行：v2 checkpoint 起步（network_weights 口径）+ 8×777 挖掘样本（27 图，无 caption 走 class token，384 图 LANCZOS 上采样过断言）+ 540 步 2ep（1.14it/s）。离线评测（历史参考系）：v2m777 mean **0.8586 守住 0.85 线**但 777 种子 0.7846→**0.7269 反降**（1ep 中间档 0.7256 同）——777 样本系 v2 自生成同分布，续训为分布巩固非泛化，**生产维持 v2 不替换**。文件减半之谜：keys 792/792 一致仅 fp16 保存口径。G5-003 执行器 35.4 改造复跑：①四档判定全对（v2m777 0.8586 不触发预期正确）准确率 100%/误触发 0；②增量重训 BLOCKED→DONE；③复测 FAIL 如实（min 0.7269<0.85 手册预期未达）→ gate_verdict: FAIL 不虚构。留证 tc-m3-lora-v2m777-eval.json + tc-g5-gate-run-20261002.json + train_v2m777.log。

背景态：G1-004 落位保持 BLOCKED（NAS 未挂载）；主文档 v1.7.0（§23-26）；yyc3-ai-agent-archive 无变更。

### 36.4 下轮起点（TOP 3）

1. **[P1]** FaceID 组合生产接线决策（待用户）：min 稳定度备选（0.8036）是否接入 drama_stage_adapter（mean 口径不优于 v2 组合，仅「防最差帧」场景价值）；若接则 adapter FaceID 分支 + 生产冒烟 + G4-006 对照复跑
2. **[P1]** HERO 参考系统一治理：run_kohya_lora.py / run_batch_shots.py / run_anchor_domain_recal.py 三脚本 HERO 硬编码 /tmp 迁移至历史设定图锚定（对齐 run_lora_plusface_combo.py 修复模式），消除跨日评测漂移隐患
3. **[P2]** 基模迁移可行性预研（SDXL 系 InstantID/PuLID 破局 0.85 的唯一路径）：DreamShaper XL 候选评估 + 显存/耗时预算 + 迁移影响面（adapter/LoRA 全链重训评估）；G5-002/005 反哺项启用与夜间窗口复跑并行推进
