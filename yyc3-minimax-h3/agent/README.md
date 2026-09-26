# YYC3 MiniMax-H3 多Agent 框架（H3 Agent Family）v1.0

> 言启象限 · 语枢未来 —— H3 视听生成层接入 YYC³ AI Family 多Agent 协同体系

## 定位

本框架将 [YYC3-AI-Family-Comic-Drama-Agent](../../../YYC3%20AI%20Family-Comic%20Drama/docs/YYC3-AI-Family-Comic-Drama-Agent/INDEX.md) 的多Agent 设计**适配落地到本仓库（YYC3-MiniMax-H3）**，承担漫剧生产六阶段之**阶段4（04_audiovisual_gen 视听生成）**的执行层：

```
漫剧编排层（元启·天枢 / DramaStageAdapter）          ← 参照项目（调用方）
        ↓ A2A 协议（Redis Streams / REST，消息 9 字段逐一同名）
┌────────────────────────────────────────────────────┐
│  YYC3-MiniMax-H3  agent/                           │
│  ├─ H3·织影 生产官   video_generation（阶段4主责） │ ← 白名单脚本调度（铁律④）
│  ├─ 格物·质检官(H3)  quality_check（0-10 红线）    │ ← 纯规则，确定性
│  ├─ 智云·安全哨(H3)  security_audit（fail-closed） │ ← claim HMAC + 泄漏扫描
│  └─ H3StageOrchestrator  生成→质检→打回重做闭环    │ ← 状态机五态兼容
└────────────────────────────────────────────────────┘
        ↓ argv 白名单调用（零 shell 拼接）
既有生产资产：pipeline_auto / batch_ref2va_nf4 / score_lipsync / export_dashboard_data
```

## 对齐映射表

| 参照项目 | 本框架 | 说明 |
| -------- | ------ | ---- |
| 91-A2A `a2a_protocol.py` | `h3_agent/protocol.py` | 消息 9 字段 / 注册中心 / 消费者组 / DLQ / 审计全同构；**新增传输抽象**（Redis 不可达自动降级 InMemory） |
| 00-公共基座 `BaseAgent` | `h3_agent/base_agent.py` | LLM 依赖移除（执行层无 LLM）；**新增安全闸**（claim + 载荷白名单） |
| 02-智云守护-安全官 | `agents/security_agent.py` | H3 侧纯规则实现：claim 自检 + 产物密钥扫描 + 审计回放 |
| 03-格物宗师-质量官 | `agents/quality_agent.py` | 0-10 红线（≥6 过 / ≥8 良 / ≥9 优）+ score_norm ≥0.75（同 DramaToolGateway） |
| 99 `DramaStageAdapter` | `h3_agent/orchestrator.py` | `StageStatus` 五态逐值兼容；快照落 `projects/{id}/state/` |
| 99 `DramaToolGateway.image_to_video` | `agents/production_agent.py` | H3 真实实现位（stub → 本框架） |

未迁移的 6 个 LLM Agent（元启天枢/创想灵韵/言启千行/语枢万物/预见先知/知遇伯乐）属**创作/决策层**，归漫剧项目承载；本框架经 A2A 协议与之上游对接。

## 快速开始

```bash
# 1) 安装依赖（redis 可选；fastapi 仅网关需要）
pip install -r agent/requirements.txt

# 2) 配置 claim 密钥（生产必须；缺省=写操作全拒）
mkdir -p .secrets && echo 'AGENT_CLAIM_SECRET=<随机长随机串>' > .secrets/agent_claim.env && chmod 600 .secrets/agent_claim.env

# 3) 离线冒烟（无 Redis / 无 GPU 即可跑）
python3 -m unittest discover -s agent/tests -v

# 4) 启动网关（默认 127.0.0.1:8300）
uvicorn agent.h3_agent.gateway:app --port 8300
#   GET  /api/healthz  GET /api/agents
#   POST /api/tasks    POST /api/stages/audiovisual?batch=93&dry_run=true
#   写操作需 claim：python3 -m agent.h3_agent.cli --task-type generate_batch  → 输出即 X-Claim-Token
#
# 5) 跨仓对接（漫剧项目侧）：H3_AGENT_GATEWAY=http://127.0.0.1:8300 + 同一 AGENT_CLAIM_SECRET
#    → DramaToolGateway.image_to_video 自动经网关下发（未配置自动回落 stub）
```

环境变量（全部可选，见 `h3_agent/config.py`）：`REDIS_HOST/PORT/PASSWORD`、`AGENT_CLAIM_SECRET`、`H3_AGENT_TASK_TIMEOUT`（默认 16200s，对齐生产实测）、`H3_PYTHON_BIN`、`H3_QC_PASS_SCORE`（默认 6.0）。

## 目录结构

```
agent/
├── README.md                 # 本文档
├── API.md                    # A2A 消息契约 + REST API + Agent Card
├── requirements.txt
├── h3_agent/
│   ├── config.py             # 配置/白名单/阈值（单一配置源）
│   ├── security.py           # claim HMAC / 白名单校验 / 审计 JSONL
│   ├── protocol.py           # A2A 协议（Redis/InMemory 双传输）
│   ├── base_agent.py         # Agent 基类（安全闸 + 协议循环）
│   ├── agents/               # 织影 / 格物 / 智云
│   ├── orchestrator.py       # 阶段4 闭环编排（五态状态机）
│   └── gateway.py            # FastAPI 网关
├── tests/test_smoke.py       # 离线冒烟（协议/安全/质检/编排全链路）
└── data/audit_log.jsonl      # 审计事件（NAS 同步）
```

## 安全设计（对齐仓库铁律）

1. **零命令拼接**：subprocess 仅 argv 数组 + `SCRIPT_ALLOWLIST` 白名单键 + 批次名 `[0-9A-Za-z_-]+`
2. **密钥零入库**：claim 密钥只走 env / `.secrets/`（gitignore 隔离）；网关写操作 fail-closed
3. **强制超时**：所有执行默认 16200s 超时（对齐 P0-C1 结论）
4. **高可用降级**：Redis 不可达 → InMemory（单进程演示）；LLM 不在关键路径
5. **可审计**：全链路事件双写 `stream:audit:log` + `agent/data/audit_log.jsonl`
