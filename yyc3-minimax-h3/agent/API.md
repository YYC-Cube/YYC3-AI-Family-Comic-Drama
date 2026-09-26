---
file: API.md
description: YYC3 MiniMax-H3 多Agent 框架 API 契约（A2A 消息 / Agent Card / REST 网关）
author: Intelligent Application Implementation Expert <admin@0379.email>
version: v1.0.0
created: 2026-09-26
status: active
tags: [api],[a2a],[contract],[multi-agent]
category: api
language: zh-CN
---

# YYC3 MiniMax-H3 多Agent 框架 · API 契约 v1.0

与漫剧项目 `91-A2A-通信协议/API.md`、`99-编排引擎/API.md` 同构对齐；差异以「H3」标注。

## 一、A2A 消息契约（Redis Streams）

流命名（与参照项目同名）：

| 流 | 方向 | 用途 |
| -- | ---- | ---- |
| `stream:agent:request:{agent}` | 编排→Agent | 任务分发（下表） |
| `stream:agent:result:callback` | Agent→编排 | 结果/错误回调 |
| `stream:audit:log` | 全员 | 审计（H3 侧同步双写 JSONL） |
| `stream:system:broadcast` | 系统 | 系统事件广播 |
| `{stream}:dlq` | 框架 | 死信（重试 ≥3） |

消息 9 字段（逐字段同参照项目）：

```json
{
  "msg_id": "msg-1760000000000-a1b2c3d4",
  "trace_id": "trace-20260926-0001",
  "msg_type": "task_request | task_result | error | system_event",
  "sender": "yuanqi-tianshu-001",
  "receiver": "h3-zhiying-001",
  "task_type": "generate_batch",
  "payload": "{...JSON字符串}",
  "priority": 5,
  "timestamp": 1760000000000,
  "ttl": 300
}
```

**H3 差异**：`task_request.payload` 可含 `claim`（HMAC 令牌对象，见 §三）；Agent 侧安全闸默认强制校验。

## 二、Agent Card 与任务类型

| agent_id | 名称 | capabilities | 流 | task_type |
| -------- | ---- | ------------ | -- | --------- |
| `h3-zhiying-001` | H3·织影 生产官 | video_generation, image_to_video | `...:h3-production` | generate_batch / generate_single / score_lipsync / export_dashboard |
| `h3-gewu-001` | 格物·质检官(H3) | quality_check | `...:h3-quality` | quality_check |
| `h3-zhiyun-001` | 智云·安全哨(H3) | security_audit | `...:h3-security` | security_audit |

任务载荷示例：

```jsonc
// generate_batch（批次闭环）
{"batch": "93", "dry_run": false, "timeout": 16200, "claim": {...}}
// generate_single（任务式单条，不改源文件）
{"batch": "93", "seeds": "42,10", "variant": "pruned", "preview": false,
 "prompt_file": "prompts/shot01.txt"}
// quality_check（质检红线）
{"batch": "93"}          // → {qc_score, verdict: passed|rework|blocked, suggestions[]}
// security_audit（安全巡检）
{"scan_glob": "output_batch*/**/*.json"}
```

## 三、Claim 令牌（H3 新增安全层）

```jsonc
// security.issue_claim(trace_id, task_type) →
{"trace_id": "...", "task_type": "generate_batch",
 "issued_at": 1760000000, "ttl": 300,
 "signature": "<HMAC-SHA256(trace_id|task_type|issued_at|ttl)>"}
```

- 算法：HMAC-SHA256，密钥 `AGENT_CLAIM_SECRET`（env 或 `.secrets/agent_claim.env`）
- 校验失败/过期/密钥未配置 → 一律拒绝（fail-closed）；安全违规不重试不入死信

## 四、REST 网关（FastAPI，默认 127.0.0.1:8300）

| 方法 | 路径 | 鉴权 | 说明 |
| ---- | ---- | ---- | ---- |
| GET | `/api/healthz` | 无 | 传输模式 + claim 就绪状态 |
| GET | `/api/agents` | 无 | 在线 Agent 卡片（能力发现） |
| POST | `/api/tasks` | `X-Claim-Token` | 提交任务（§二全部 task_type），同步返回结果 |
| GET | `/api/tasks/{trace_id}` | 无 | 任务状态（网关内存态） |
| POST | `/api/stages/audiovisual?batch=93&dry_run=true` | `X-Claim-Token` | 阶段4 一键闭环（生成→质检→打回→快照） |

`X-Claim-Token`：`issue_claim()` 返回对象的 JSON 字符串。

### 响应示例

```jsonc
// POST /api/tasks {"task_type":"quality_check","batch":"91"}
{"trace_id": "trace-20260926-xxxx", "status": "completed",
 "result": {"qc_score": 8.42, "verdict": "passed",
            "detail": {"avg_score": 8.1, "sync_norm_avg": 0.8153,
                       "success_rate": 0.75, "success": 3, "failed": 0},
            "thresholds": {"pass": 6.0, "good": 8.0, "excellent": 9.0,
                           "sync_norm": 0.75},
            "suggestions": []}}
```

## 五、状态机与快照（与漫剧 DramaStageAdapter 兼容）

- 状态：`pending → running → passed | rework | blocked`（rework 可重做 ≤2 次）
- 快照：`projects/{project_id}/state/audiovisual_state.json`（NAS 六环节落位对齐）
- 上游漫剧编排消费：`StageStatus` 枚举逐值兼容，`qc_score` 为 0-10 刻度
