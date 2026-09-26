# ==============================================================
# H3 多Agent 网关 v1.0（FastAPI · 公网/内网统一入口）
# @file agent/h3_agent/gateway.py
# @author Intelligent Application Implementation Expert <admin@0379.email>
# @version v1.0.0
# @created 2026-09-26
# @status stable
#
# 对齐：09-编排引擎/API.md REST 语义 + 本仓库 doc02 A2A 蓝图（FastAPI + claim）
# 端点：
#   GET  /api/healthz                 健康检查（传输模式/密钥状态）
#   GET  /api/agents                  在线 Agent 卡片（能力发现）
#   POST /api/tasks                   提交任务（X-Claim-Token 或网关签发）
#   GET  /api/tasks/{trace_id}        任务状态（编排引擎内存态；重启即失，快照落盘兜底）
#   POST /api/stages/audiovisual      一键执行阶段4 闭环（同步等待，演示/内网用）
# 安全：写操作强制 claim（X-Claim-Token 头，HMAC 由 security.issue_claim 签发）
# 启动：uvicorn agent.h3_agent.gateway:app --port 8300
# ==============================================================
import os
import time
import uuid

from . import config
from .agents.production_agent import H3ProductionAgent
from .agents.quality_agent import H3QualityAgent
from .agents.security_agent import H3SecurityAgent
from .orchestrator import H3StageOrchestrator
from .protocol import AgentRegistry, build_message, get_transport
from .security import issue_claim, verify_claim

try:
    from fastapi import FastAPI, HTTPException, Request
    from pydantic import BaseModel
except ImportError as e:  # 高可用：未安装 fastapi 时给出明确指引
    raise SystemExit("缺少依赖：pip install fastapi uvicorn（见 agent/requirements.txt）") from e

app = FastAPI(title="YYC3-H3 Agent Gateway", version="1.0.0")
_transport, _mode = get_transport()
_production = H3ProductionAgent(transport=_transport, enforce_claim=False)
_quality = H3QualityAgent(transport=_transport, enforce_claim=False)
_security = H3SecurityAgent(transport=_transport, enforce_claim=False)
_orchestrator = H3StageOrchestrator("gateway-default", transport=_transport,
                                    require_claim=False)

# 进程内任务登记（trace_id -> 状态）；生产可迁 Redis Hash（编排引擎已留接口）
_TASKS: dict[str, dict] = {}


class TaskRequest(BaseModel):
    task_type: str                     # generate_batch | quality_check | security_audit | ...
    payload: dict = {}
    batch: str | None = None           # 快捷字段，自动并入 payload


def _check_write_auth(request: Request, task_type: str):
    """写操作鉴权：X-Claim-Token 必须有效（AGENT_CLAIM_SECRET 未配置则拒绝）"""
    token = request.headers.get("X-Claim-Token", "")
    if not token:
        # 未配置密钥时仅允许内网只读演示：写操作一律 fail-closed
        raise HTTPException(401, "缺少 X-Claim-Token（用 security.issue_claim 签发）")
    try:
        import json as _json
        claim = _json.loads(token)
    except Exception:
        raise HTTPException(401, "X-Claim-Token 非法（应为 issue_claim 返回的 JSON）")
    if not verify_claim(claim):
        raise HTTPException(401, "claim 校验失败（签名/过期）")


@app.get("/api/healthz")
def healthz():
    return {"status": "ok", "transport": _mode,
            "claim_ready": bool(config.load_claim_secret()),
            "time": time.strftime("%Y-%m-%dT%H:%M:%S")}


@app.get("/api/agents")
def agents():
    return {"transport": _mode, "agents": AgentRegistry.get_online_agents(_transport)}


@app.post("/api/tasks")
def submit_task(req: TaskRequest, request: Request):
    _check_write_auth(request, req.task_type)
    trace_id = f"trace-{time.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
    payload = dict(req.payload)
    if req.batch:
        payload["batch"] = req.batch
    _TASKS[trace_id] = {"status": "running", "task_type": req.task_type,
                        "created_at": time.time()}
    try:
        if req.task_type in ("generate_batch", "generate_single",
                             "score_lipsync", "export_dashboard"):
            result = _production.handle_direct(req.task_type, payload, trace_id)
        elif req.task_type == "quality_check":
            result = _quality.handle_direct(req.task_type, payload, trace_id)
        elif req.task_type == "security_audit":
            result = _security.handle_direct(req.task_type, payload, trace_id)
        else:
            raise HTTPException(400, f"不支持的任务类型：{req.task_type}")
        _TASKS[trace_id].update({"status": "completed", "result": result})
        return {"trace_id": trace_id, "status": "completed", "result": result}
    except HTTPException:
        raise
    except Exception as e:
        _TASKS[trace_id].update({"status": "failed", "error": str(e)})
        raise HTTPException(500, str(e)) from e


@app.get("/api/tasks/{trace_id}")
def task_status(trace_id: str):
    task = _TASKS.get(trace_id)
    if not task:
        raise HTTPException(404, "任务不存在（网关重启后内存态清空，快照见 projects/*/state/）")
    return {"trace_id": trace_id, **task}


@app.post("/api/stages/audiovisual")
def run_audiovisual_stage(request: Request, batch: str, dry_run: bool = False):
    """阶段4 一键闭环（同步等待；夜间长任务建议走 /api/tasks 异步 + 外部调度）"""
    _check_write_auth(request, "generate_batch")
    trace_id = f"stage-{time.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
    try:
        result = _orchestrator.run_audiovisual_stage(batch=batch, dry_run=dry_run)
        return {"trace_id": trace_id, **result, "snapshot": _orchestrator.snapshot()}
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


# ---------------- 独立启动（开发调试） ----------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.getenv("H3_AGENT_HOST", "127.0.0.1"),
                port=int(os.getenv("H3_AGENT_PORT", "8300")))
