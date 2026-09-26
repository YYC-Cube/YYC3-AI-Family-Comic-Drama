---
file: CHANGELOG.md
description: YYC³ 0379-world 项目版本变更日志
author: YanYuCloudCube Team <admin@0379.email>
version: v1.1.0
created: 2026-04-04
updated: 2026-09-23
status: active
tags: [changelog],[version],[history]
category: project
language: zh-CN
---

> ***YanYuCloudCube***
> *言启象限 | 语枢未来*
> ***Words Initiate Quadrants, Language Serves as Core for Future***
> *万象归元于云枢 | 深栈智启新纪元*
> ***All things converge in cloud pivot; Deep stacks ignite a new era of intelligence***

---

# 变更日志 (Changelog)

本文档记录 YYC³ 0379-world 项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [Unreleased] - 待发布

### 新增 (Added)

- 🆕 pytest 分层体系（P1-1）：默认快速回归层 `-m "not integration"`（34 用例 ~1.6s）；`make test-fast` / `make test-integration` / `make test`（全量）三目标；CI 按事件分层分发（PR 快速层 / main 全量）
- 🆕 三云适配器 + ollama 全链路测试套件 `tests/test_cloud_adapters_fullpath.py`（15 用例：同步/流式 × 参数化、reasoning 折叠、错误分支、主备切换、全塔断路、host 归一）
- 🆕 pytest.ini 注册 `fast` marker，`integration` marker 语义明确化
- 🆕 CI release job（P2-4）：tag 推送 → 版本一致性门禁（tag ↔ CHANGELOG 定版段 ↔ README 徽章三方对齐）→ ReleaseNotes 自动提取 → GitHub Release（tag 含 `-` 自动 prerelease）
- 🆕 docs 内链检查器 `core/scripts/check_doc_links.py`（P2-5）：markdown 相对链接→文件存在性静态检查，进 CI lint job 正式门禁
- 🆕 ADMIN_API_KEYS 分离语义测试 `tests/test_admin_key_separation.py`（P2-6，6 用例：回退/互斥/容错/模板锚）
- 🆕 API认证使用指南「管理面密钥分离」章节：语义契约 + 生产 runbook + 90 天轮换策略
- 🆕 ADMIN_API_KEYS 生产验证脚本 `core/scripts/verify_admin_keys.sh`（三连验证一键化：403/200/200 + 精准处置提示）
- 🆕 生产 .env 写入示例命令固化：API认证使用指南 runbook 升级四步可复制（生成/幂等写入/滚动生效/三连验证）+ 轮换与回滚段
- 🆕 A2A 通信协议层 `core/api/services/a2a_protocol.py`：Redis Stream 消费者组原语（ensure_group BUSYGROUP 幂等 / poll_messages 非阻塞修正 / send_task/result / nack+DLQ / XAUTOCLAIM claim_stale_messages 兼容 2·3 元响应）
- 🆕 外置 Agent Worker 装配 `core/api/services/agent_workers.py` + 独立进程入口 `core/scripts/agent_worker.py`（A2A_ENABLED × AGENT_WORKER_ENABLED 双控；3 Agent 单机装配）
- 🆕 A2A 投递端点 `POST /v1/agent/a2a/tasks` + 同步闭环端点 `POST /v1/agent/a2a/tasks/sync`（注册聚合器 → 投递 → drain 追平 → wait_one 等齐，超时不丢任务）
- 🆕 ResultHub 结果流消费端 `core/api/services/a2a_result.py`：sender 覆盖式幂等聚合 + asyncio.Event 事件驱动 wait_one/wait_all + XAUTOCLAIM 挂起回收（60s 空闲阈值 / 30s 扫描）+ 孤儿回执审计
- 🆕 多 Agent 编排端点 `POST /v1/agent/a2a/orchestrate`：capability 在线 Agent 全量扇出 + wait_all 等齐（completed/partial/timeout + 部分 results）
- 🆕 vk（虚拟密钥）计费门控接入 `/v1/agent/**`：三端点内联门控（白名单 403 / 预算 402 / TPM 429，task_type 作 model 语义）+ 中间件协同事务记账（X-A2A-Cost > X-Total-Cost 双探针 + 兜底 0.001 USD，请求内 await 落队）
- 🆕 A2A 可观测面 `core/api/services/a2a_metrics.py`：孤儿/回收/死信 Counter + DLQ 深度/结果流堆积/双端 PEL Gauge（XAUTOCLAIM dryrun 只读采集，30s 周期随消费端生命周期）+ Grafana `a2a-observability` 七面板（堆积阈值 500/2000 告警配色）
- 🆕 A2A 审计流 Loki 消费端 `core/api/services/a2a_audit.py`：stream:audit:log → Loki 批量推送（labels job=a2a-audit/event/agent，推送成功才 XACK，抖动退避）；A2A_ENABLED × A2A_AUDIT_LOKI_ENABLED 双控；Grafana Loki 数据源 provisioning 补齐 + 告警规则三条（死信/孤儿/回收停滞）
- 🆕 A2A 成本直报：pricing.py 任务类型固定定价表 TASK_TYPE_PRICES + task_cost()；三端点回填 X-A2A-Cost 响应头（编排=单价×扇出数），中间件记账双探针优先取直报值
- 🆕 A2A Worker 扩面：格物·宗师（content_validation/code_review）+ 演启·乾行（content_formatting）入编，编队 3→5；A2A_WORKER_AGENTS 配置化部署
- 🆕 协同事务价格表管理端点：GET/PUT `/v1/admin/pricing/task-types`（TASK_TYPE_PRICES 运行时覆盖，负价 422 / 未知类型预置 / RBAC）
- 🆕 编排器独立部署面：`core/scripts/orchestrator.py`（--consumer/--no-metrics/--with-audit）+ compose `orchestrator` profile；内嵌/独立/混合三形态
- 🆕 生产灰度修复：compose grafana 挂载 provisioning（数据源/告警/仪表盘随启动加载）+ Loki local-config 补建（原挂载目标缺失）+ 灰度验证脚本（Redis→shipper→Loki 端到端 + Grafana 告警联系人路由绑定，实环境三连全通）
- 🆕 NAS 生产栈全套灰度：nas compose 补 agent-worker（5 编队）+ orchestrator profile + 网关 A2A 全 env（A2A_AUDIT_LOKI_ENABLED 缺省开闸）；监控 compose 补 Loki（named volume）；容器入口 app.worker_entry / app.orchestrator_entry；deploy 脚本补 core/agents 同步 + NAS 布局 Dockerfile（修复部署链断点：Worker 依赖原先不在部署目录）
- 🆕 协同事务价格表 PG 持久化：004_task_prices.sql 迁移 + load_task_prices_from_db 启动加载（表覆盖内存）+ upsert_task_price_persisted 双写（DB 不可达降级仅内存，响应 persisted 标志）
- 🆕 A2A 开放 API 契约：docs/架构与部署/A2A开放API契约.md（端点/认证/计费/错误码/可靠性语义）+ 三端点 OpenAPI tags/summary/description
- 🆕 A2A 测试体系 `tests/test_a2a_{protocol,worker,result}.py`（68 integration 用例）+ conftest 顶层统一密钥注入（收集顺序加固：测试文件只读不写，合跑 9 failed → 全绿）

### 变更 (Changed)

- 🔄 AuthMiddleware `_authenticate` api_key 分支提取 `_authenticate_vk_or_static` 类方法（vk 校验链优先、静态/管理键降级语义不变；可测试打桩）
- 🔄 CI 六 job 补 `timeout-minutes`（lint 10 / test 25 / security 10 / build 30 / deploy 15 / release 10），防 runner 挂死空转
- 🔄 test_gateway_api / test_admin_rbac / test_proxy_api 三文件标记 `integration`（TestClient 全链路归集成层，语义不变）
- 🔄 CI test job 分层：`pull_request` 且非目标 main 时跑快速层；push/PR→main 跑全量
- 🔄 CI 触发器补 `tags: ["v*.*.*"]`

### 修复 (Fixed)

- 🔧 `redis.exceptions.ResponseError` 改 `from redis.exceptions import ResponseError` 直接导入（test_a2a_worker / test_a2a_result 两处；消除 IDE 类型桩「exceptions 不是 redis 已知属性」误报）
- 🔧 覆盖率缺口补齐：deepseek 24→87% / openai 27→83% / ollama 53→84% / zhipu 13→86% / key_guard 30→100%
- 🔧 README 版本徽章漂移修复（v9 提交意外回退 v2.2.0 → 恢复 v2.3.0，由 release 门禁逻辑在验证时发现）
- 🔧 存量死链修复 32 处：core/README 幽灵架构文档链重指 SSOT 真身；操作指南三文件"相关文档"段四机时代旧链重写；验收系统两文档旧目录名修正；MCP README 四处 BigModel 死链降级；.env.0379-world 两文档根级幽灵链重写

### 移除 (Removed)

- 🗑️ core/scripts 旧本地模型路线 5 文件：cogagent_chat.py / cogvideox_generator.py / deploy-cogvideox.sh / test-local-models.py / update-model-configs.sql（全仓零引用；推理已 DGX 化）
- 🗑️ 变量清单 MODEL_COGAGENT_*/ MODEL_COGVIDEOX_* 环境变量 6 行（消费者已删）

---

## [2.3.0] - 2026-09-23

### 新增 (Added)

- 🆕 流式 SSE chunk 级 PII 脱敏（carry 缓冲拼接跨 chunk 截断 PII，流末 flush 滞缓冲）
- 🆕 vk 管理看板与 Playwright 真浏览器 e2e 基建（chromium channel=chrome）
- 🆕 三层防御体系：vk 403 / 预算 402 / TPM 429
- 🆕 错误重试测试套件 `tests/test_error_retry.py`（6 用例，含零空转断言）
- 🆕 三云适配器 Key 校验参数化矩阵（`_CLOUD_ADAPTERS` 表驱动，断言面=声明面）
- 🆕 IDE 导入解析三件套：`pyrightconfig.json` + 根级 `app` symlink + `.markdownlint.json`
- 🆕 Redis 从节点部署 (yyc3-45:6399)，避开系统 Redis 6379
- 🆕 CodeGeeX4 Agent 实现 (`agents/yyc3_code_agent.py`，唯一真源)

### 变更 (Changed)

- 🔄 ZHIPU/DeepSeek/OpenAI 三云适配器 Key 前置校验同构化（`ensure_api_key` 公共件落位 `app/errors/key_guard.py`）
- 🔄 DeepSeek/OpenAI Key 从模块级快照改为延迟读取（运行时热加载）
- 🔄 4xx 确定性失败跳过重试（`ErrorHandler._is_retryable`，终结空转重试）
- 🔄 ZHIPU 同步入口接入 `_ensure_key()`（空 Key 401 明确报错，替代模糊 502）
- 🔄 Gateway 容器 (NAS) 配置修正：DB_HOST/REDIS_HOST/HOST_IP 指向正确地址
- 🔄 Gateway 健康检查从 `curl` 改为 `python3 urllib`（容器内无 curl）
- 🔄 Gateway 重启策略从 `unless-stopped` 改为 `no`（防止无限重启崩溃系统）

### 修复 (Fixed)

- 🔧 **P0 致命**: 修复 Gateway 容器 `unhealthy` → `healthy`
  - 根因：DB_HOST=127.0.0.1 导致启动失败 + restart 无限循环 → 系统崩溃
  - 方案：修正环境变量指向实际服务地址，禁用自动重启
- 🔧 **P0 致命**: Redis 从节点端口冲突解决
  - 根因：Docker Redis 映射 6379 与 NAS 系统 Redis 冲突（TANS/TOS 缓存）
  - 方案：使用端口 6399 避开系统服务，建立主从复制
- 🔧 确认 NAS 系统服务安全：Redis(6379) / PG13(5032) 未受任何干扰
- 🔧 OBS-1 空转重试：401 等 4xx 确定性失败不再消耗 3 轮重试（耗时 <0.5s）
- 🔧 OBS-2 DeepSeek 空 Key 模糊 502 → 401 明确报错；OpenAI 无校验 → 补齐前置校验
- 🔧 移除重复 agent 副本 `core/scripts/yyc3_code_agent.py`（lint 清理旧版，零外部引用）

---

## [2.2.0] - 2026-09-14

### 新增 (Added)

- 🆕 DGX 双机 TP=2 公网三能力（chat/embeddings/rerank）全绿
- 🆕 上游池 env 化（`OPENAI_COMPATIBLE_UPSTREAMS`）+ 熔断降级
- 🆕 CI 五段流水线 + 四层冒烟保障
- 🆕 文档体系 SSOT 对齐（架构/部署/CI-CD/前端设计三合一）
- 🆕 生产域名 `https://api.0379.world`（ECS Traefik 边缘 → NAS 网关:8000）

### 变更 (Changed)

- 🔄 响应头 `X-YYC3-Upstream` 契约落地

---

## [2.1.0] - 2026-07-10

### 安全 (Security)

- 🔒 消除全部硬编码密钥，统一环境变量配置
- 🔒 `docs/` 敏感遗留清理

---

## [2.0.0] - 2026-04-08

### 新增 (Added)

- 🆕 自适应路由引擎（EWMA 动态权重）
- 🆕 RAG 知识库
- 🆕 MCP 工具集成

---

## [1.0.0] - 2026-04-04

### 新增 (Added)

#### 核心功能

- ✅ FastAPI 应用框架搭建
- ✅ PostgreSQL 数据库集成
- ✅ Redis 缓存服务集成
- ✅ API 网关服务
- ✅ 多模型 AI 服务集成（OpenAI、智谱 AI、Ollama）
- ✅ MCP 工具集成
- ✅ Prometheus + Grafana 监控系统

#### API 服务

- ✅ CloudPivot Matrix API 服务（端口 3118）
- ✅ CloudPivot Matrix WebSocket 服务（端口 3113）
- ✅ YYC³ AIFY 服务（端口 3200）
- ✅ YYC³ MCP 服务（端口 3203）

#### 数据库

- ✅ 主数据库：0379_world
- ✅ 核心共享库：yyc3_core
- ✅ AI 助手库：yyc3_aify
- ✅ 企业管理库：yyc3_my
- ✅ MCP API 服务库：yyc3_mcp
- ✅ 开发测试库：yyc3_dev

#### 工具和脚本

- ✅ 环境变量验证脚本
- ✅ 性能基线测试脚本
- ✅ 监控启动脚本
- ✅ Grafana 仪表盘配置脚本
- ✅ 告警通知脚本

#### 文档

- ✅ 项目 README.md
- ✅ API 全链路架构文档
- ✅ 整体架构设计文档
- ✅ 多端架构说明文档
- ✅ 项目现状分析文档
- ✅ 部署完成总结文档

### 文档规范

#### 合规性统一

- ✅ 所有 Markdown 文档添加 YAML Front Matter 标头
- ✅ 所有 Python 代码文件添加 JSDoc 标头注释
- ✅ 文件命名规范化（snake_case）
- ✅ 项目目录结构规范化
- ✅ 创建合规性检查工具集

#### 新增文档

- ✅ CHANGELOG.md - 版本变更日志
- ✅ CONTRIBUTING.md - 贡献指南
- ✅ LICENSE - MIT 开源许可证
- ✅ Makefile - 构建脚本
- ✅ Dockerfile - Docker 构建文件

### 变更 (Changed)

#### 项目结构优化

- 🔄 重组项目目录结构
- 🔄 规范化配置文件管理
- 🔄 优化 Docker Compose 配置

#### 性能优化

- 🔄 数据库连接池优化
- 🔄 Redis 缓存策略优化
- 🔄 API 限流配置优化

### 修复 (Fixed)

#### 环境配置

- 🐛 修复环境变量配置问题
- 🐛 修复 Docker 网络冲突问题
- 🐛 修复 NFS 挂载中断问题

#### 服务稳定性

- 🐛 修复健康检查失败问题
- 🐛 修复服务自动重启问题
- 🐛 修复监控数据采集问题

---

## [0.9.0] - 2026-03-21

### 新增 (Added)

#### 基础架构

- ✅ 项目初始化
- ✅ 基础目录结构创建
- ✅ Git 仓库初始化
- ✅ 基础配置文件

#### 数据库服务

- ✅ PostgreSQL 数据库部署
- ✅ Redis 缓存服务部署
- ✅ 数据库初始化脚本

#### 容器化

- ✅ Docker Compose 配置
- ✅ 基础镜像构建
- ✅ 容器网络配置

---

## 版本说明

### 版本号格式

遵循语义化版本 2.0.0 规范：`主版本号.次版本号.修订号`

- **主版本号（MAJOR）**: 不兼容的 API 修改
- **次版本号（MINOR）**: 向下兼容的功能性新增
- **修订号（PATCH）**: 向下兼容的问题修正

### 变更类型

- **新增 (Added)**: 新功能
- **变更 (Changed)**: 对现有功能的变更
- **弃用 (Deprecated)**: 即将删除的功能
- **移除 (Removed)**: 已删除的功能
- **修复 (Fixed)**: 任何 bug 修复
- **安全 (Security)**: 安全相关的修复

---

## 路线图

### v1.1.0 (计划中)

- [ ] 完善测试覆盖（单元测试、集成测试）
- [ ] 添加 API 文档（Swagger/OpenAPI）
- [ ] 优化监控告警规则
- [ ] 添加自动化运维脚本

### v1.2.0 (计划中)

- [ ] CI/CD 流程配置
- [ ] 自动化部署流程
- [ ] 性能优化和压力测试
- [ ] 安全加固和渗透测试

### v2.0.0 (长期规划)

- [ ] 微服务架构重构
- [ ] Kubernetes 部署支持
- [ ] 多租户支持
- [ ] 插件化架构

---

## 贡献

如果您想为本项目做出贡献，请参阅 [CONTRIBUTING.md](./CONTRIBUTING.md)。

---

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](./LICENSE)。

---

**维护团队**: YanYuCloudCube Team
**联系方式**: <admin@0379.email>
**项目地址**: <https://github.com/YYC-Cube/yyc3-api-world>

---

[1.0.0]: https://github.com/YYC-Cube/yyc3-api-world/releases/tag/v1.0.0
[0.9.0]: https://github.com/YYC-Cube/yyc3-api-world/releases/tag/v0.9.0
