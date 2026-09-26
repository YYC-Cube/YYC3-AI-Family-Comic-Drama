# file: a2a.py
# description: A2A 协议端点 - Agent Card 能力发现 + 外置 Agent 注册/心跳 + 单 Agent 任务提交（Phase 2）
# author: YanYuCloudCube Team <admin@0379.email>
# created: 2026-09-26
# status: active
# tags: [api],[a2a],[registry],[redis-stream]

"""
@file: app/api/a2a.py
@description: A2A 通信协议端点。
    - GET  /v1/a2a/agents?capability=          能力发现：在线 Agent Card 列表（90s 心跳超时离线）
    - POST /v1/agent/a2a/tasks                 单 Agent 任务提交（信封投递 stream:agent:task:{id}）
    - POST /v1/agent/a2a/tasks/sync            同步任务提交：投递后等待结果回执（请求-响应闭环）
    - POST /v1/admin/a2a/agents/register       外置 Agent 注册（独立进程 Worker 接入）
    - POST /v1/admin/a2a/agents/{id}/heartbeat 外置 Agent 心跳保活
内置编队 8 张卡片由网关启动时自动注册（A2A_ENABLED，见 services/a2a_protocol.py）；
/v1/admin/** 由 AuthMiddleware 以 ADMIN_API_KEYS 自动保护；消费侧由外置 Worker
（core/scripts/agent_worker.py）经消费者组 XREADGROUP 认领，ACK/重试/DLQ 见协议层；
结果回执由编排器聚合消费端（services/a2a_result.py）经 stream:agent:result:callback 等待。
"""

import asyncio
import logging
import uuid
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.services import a2a_protocol, a2a_result, pricing

logger = logging.getLogger(__name__)

router = APIRouter()

# ── 请求常量（跨端点共享）──────────────────────────────────────

_AGENTS_ENDPOINT_PREFIX = "/v1/agent/a2a/"  # 编排/任务提交端点前缀（vk 计费面）
_CONCURRENCY_COST_ESTIMATE = 0.0  # 协同事务 token usage 未知：预算检查按已花超限（est=0）
_ORCHESTRATION_URGENCY_COST = 0.001  # 编排单兜底成本（双探针均缺失时，避免协同事务长期 0 计量）


# ── 薄封装（测试桩替点，范式同 agent.py）──────────────────────


async def _list_online(capability: Optional[str] = None) -> List[dict]:
    return await a2a_protocol._registry_online_cards(capability)


async def _register(card: dict) -> dict:
    return await a2a_protocol._registry_register(card)


async def _heartbeat(agent_id: str) -> bool:
    return await a2a_protocol._registry_heartbeat(agent_id)


async def _submit(receiver_agent_id: str, message: dict) -> str:
    return await a2a_protocol.send_task_message(receiver_agent_id, message)


async def _resolve_receiver(receiver_agent_id: Optional[str], capability: Optional[str]) -> str:
    """路由目标解析：receiver 直投优先，否则 capability 能力发现（取首个在线）。"""
    if receiver_agent_id:
        return receiver_agent_id
    if not capability:
        raise HTTPException(
            status_code=400, detail={"error": "receiver_agent_id 或 capability 必填其一"}
        )
    online = await _list_online(capability)
    if not online:
        raise HTTPException(
            status_code=404, detail={"error": "no_online_agent", "capability": capability}
        )
    return online[0]["agent_id"]


def _resolve_vk(request: Request):
    """请求上下文中的虚拟密钥记录（AuthMiddleware 校验链已注入 request.state.user）。"""
    user_ctx = getattr(request.state, "user", None)
    return user_ctx.get("vk") if isinstance(user_ctx, dict) else None


async def _enforce_agent_vk_gates(vk, model: str) -> None:
    """TOP1 vk 计费门控：模型白名单（403）+ 预算闸门（402）+ TPM 滑窗限流（429）。

    仅对虚拟密钥身份生效（env 静态 API Key / 管理键直调不计费，对齐 chat 语义）；
    对齐 chat 链路范式（services/pricing + virtual_key_manager，见 api/chat.py L326+）。
    """
    if vk is None:
        return
    from app.services.virtual_key_manager import vk_manager

    if not vk_manager.check_model_allowed(vk, model):
        raise HTTPException(
            status_code=403,
            detail={
                "error": {"message": f"虚拟密钥无权访问模型 {model}", "type": "model_not_allowed"}
            },
        )
    if not vk_manager.check_budget(vk, est_cost=_CONCURRENCY_COST_ESTIMATE):
        raise HTTPException(
            status_code=402,
            detail={"error": {"message": "虚拟密钥预算已耗尽", "type": "budget_exceeded"}},
        )
    if not await vk_manager.check_tpm(vk):
        raise HTTPException(
            status_code=429,
            detail={"error": {"message": "虚拟密钥 TPM 限流触发", "type": "rate_limit_exceeded"}},
        )


# ── 模型 ────────────────────────────────────────────────────


class AgentCardRequest(BaseModel):
    """外置 Agent 注册卡片"""

    agent_id: str = Field(..., max_length=128, description="Agent 唯一标识（如 yushu-wanwu-002）")
    agent_name: str = Field(..., max_length=128, description="人格化名称（如 语枢·万物）")
    role: str = Field(..., max_length=128, description="角色定位（如 思考者）")
    capabilities: List[str] = Field(default_factory=list, description="能力标签（能力路由依据）")
    endpoint: str = Field(
        ..., max_length=256, description="任务接收流或端点（如 stream:agent:request:yushu）"
    )
    layer: str = Field("business", max_length=32, description="架构层级（decision/core/business）")


class A2ATaskRequest(BaseModel):
    """单 Agent 任务提交（信封投递，外置 Worker 消费者组认领）"""

    task_type: str = Field(..., max_length=64, description="任务类型（如 data_analysis）")
    payload: dict = Field(
        ..., description="任务载荷（input 主输入 + 方法参数 + knowledge_context）"
    )
    receiver_agent_id: Optional[str] = Field(
        None, max_length=128, description="目标 Agent（直投）；与 capability 二选一"
    )
    capability: Optional[str] = Field(
        None,
        max_length=64,
        description="能力路由（在线 Agent 中发现）；与 receiver_agent_id 二选一",
    )
    priority: int = Field(5, ge=1, le=9, description="优先级（1 最高，9 最低）")


# ── 端点 ────────────────────────────────────────────────────


@router.get("/v1/a2a/agents")
async def list_agents(capability: Optional[str] = None):
    """能力发现：在线 Agent Card 列表（心跳超时 90s 即离线不返回）。"""
    agents = await _list_online(capability)
    return {"agents": agents, "count": len(agents)}


@router.post("/v1/admin/a2a/agents/register")
async def register_agent(card: AgentCardRequest):
    """外置 Agent 注册（幂等；首次注册时间保留，重注册即刷新心跳）。"""
    full = await _register(card.model_dump())
    logger.info("[a2a] Agent %s(%s) 注册成功", card.agent_name, card.agent_id)
    return {"agent_id": card.agent_id, "status": full["status"]}


@router.post("/v1/admin/a2a/agents/{agent_id}/heartbeat")
async def agent_heartbeat(agent_id: str):
    """外置 Agent 心跳保活；未注册返回 404（对齐原型静默语义的显式化）。"""
    ok = await _heartbeat(agent_id)
    if not ok:
        raise HTTPException(status_code=404, detail={"error": "agent_not_registered"})
    return {"agent_id": agent_id, "status": "online"}


@router.post(
    "/v1/agent/a2a/tasks",
    status_code=202,
    tags=["A2A 协同事务"],
    summary="异步任务投递（202 即返）",
    description="外部契约见《docs/架构与部署/A2A开放API契约.md》；X-A2A-Cost 响应头为计费成本。",
)
async def submit_a2a_task(req: A2ATaskRequest, request: Request, response: Response):
    """提交单 Agent A2A 任务：信封投递至目标任务流（202 即返，消费者组异步认领）。

    路由：receiver_agent_id 直投优先；否则按 capability 在在线 Agent 中发现（取首个）。
    vk 计费门控：模型白名单（403）/ 预算（402）/ TPM 限流（429）——静态/管理键不计费。
    成本直报：X-A2A-Cost 响应头按任务类型固定定价（pricing.task_cost），中间件记账优先取本头。
    """
    vk = _resolve_vk(request)
    await _enforce_agent_vk_gates(
        vk, req.task_type
    )  # task_type 作 model 语义（白名单 fnmatch 支持按任务类型管控）
    receiver = await _resolve_receiver(req.receiver_agent_id, req.capability)
    trace_id = uuid.uuid4().hex
    message = a2a_protocol.build_message(
        trace_id=trace_id,
        msg_type="task_request",
        sender="gateway",
        receiver=receiver,
        task_type=req.task_type,
        payload=req.payload,
        priority=req.priority,
    )
    await _submit(receiver, message)
    response.headers["X-A2A-Cost"] = f"{pricing.task_cost(req.task_type):.6f}"
    logger.info("[a2a] 任务 %s 已投递 %s（task_type=%s）", trace_id, receiver, req.task_type)
    return {
        "msg_id": message["msg_id"],
        "trace_id": trace_id,
        "receiver": receiver,
        "stream": a2a_protocol.task_stream(receiver),
        "status": "queued",
    }


class A2ASyncTaskRequest(A2ATaskRequest):
    """同步任务提交：投递后在超时窗口内等待结果回执（请求-响应闭环）"""

    trace_id: Optional[str] = Field(
        None, max_length=64, description="链路追踪 ID（调用方指定用于关联回执；缺省自动生成）"
    )
    timeout_seconds: int = Field(30, ge=1, le=120, description="结果等待超时（秒）")


@router.post(
    "/v1/agent/a2a/tasks/sync",
    tags=["A2A 协同事务"],
    summary="同步闭环（投递 + 等待回执）",
    description="超时返回 status=timeout（任务不撤回照常消费）；超时也计费（任务已入队）。",
)
async def submit_a2a_task_sync(req: A2ASyncTaskRequest, request: Request, response: Response):
    """提交单 Agent 任务并同步等待结果回执（编排器聚合 stream:agent:result:callback）。

    时序：vk 门控 → 注册聚合器 → 投递任务流 → 追平在途回执 → 事件驱动等待。
    超时返回 status=timeout（任务仍留在任务流由 Worker 正常消费，结果不丢）。
    成本直报：X-A2A-Cost 按任务类型固定定价（成功/超时下均回填，超时成本照计——任务已入队）。
    """
    vk = _resolve_vk(request)
    await _enforce_agent_vk_gates(vk, req.task_type)
    receiver = await _resolve_receiver(req.receiver_agent_id, req.capability)
    trace_id = req.trace_id or uuid.uuid4().hex
    hub = a2a_result.result_hub()
    hub.register(trace_id)
    try:
        message = a2a_protocol.build_message(
            trace_id=trace_id,
            msg_type="task_request",
            sender="gateway",
            receiver=receiver,
            task_type=req.task_type,
            payload=req.payload,
            priority=req.priority,
        )
        await _submit(receiver, message)
        response.headers["X-A2A-Cost"] = f"{pricing.task_cost(req.task_type):.6f}"
        await hub.run_once()  # 追平「注册前已写入结果流」的在途回执（防漏 + 降首响应延迟）
        try:
            result = await hub.wait_one(trace_id, timeout=req.timeout_seconds)
        except asyncio.TimeoutError:
            logger.info(
                "[a2a] 任务 %s 等待回执超时（%ss），任务流仍由 Worker 消费",
                trace_id,
                req.timeout_seconds,
            )
            return {
                "trace_id": trace_id,
                "receiver": receiver,
                "status": "timeout",
                "result": None,
            }
        status = "succeeded" if result["msg_type"] == "task_result" else "failed"
        logger.info("[a2a] 任务 %s 同步闭环完成（status=%s）", trace_id, status)
        return {"trace_id": trace_id, "receiver": receiver, "status": status, "result": result}
    finally:
        hub.discard(trace_id)


class A2AOrchestrationRequest(BaseModel):
    """多 Agent 编排：扇出批量任务提交 + wait_all 等齐回执（单 trace 扇入聚合）"""

    capability: str = Field(..., max_length=64, description="能力路由（在线 Agent 中全量扇出）")
    task_type: str = Field(..., max_length=64, description="任务类型（各 Agent 同型）")
    payload: dict = Field(..., description="任务载荷（input 主输入 + 知识上下文）")
    priority: int = Field(5, ge=1, le=9, description="优先级（1 最高，9 最低）")
    timeout_seconds: int = Field(60, ge=1, le=300, description="扇入等齐超时（秒）")
    model: Optional[str] = Field(
        None,
        max_length=64,
        description="vk 计费模型（缺省回退 task_type：静态/管理键不计费）",
    )


@router.post(
    "/v1/agent/a2a/orchestrate",
    tags=["A2A 协同事务"],
    summary="多 Agent 扇出编排（capability 全量 + wait_all 等齐）",
    description="X-A2A-Cost = 任务单价 × 扇出数；timeout 响应含已完成部分 results。",
)
async def orchestrate_a2a_tasks(req: A2AOrchestrationRequest, request: Request, response: Response):
    """多 Agent 扇出编排：按 capability 发现在线 Agent 全量投递，wait_all 等齐回执。

    vk 计费门控按 model（缺省回退 task_type）；扇出注册聚合器 → 逐 Agent 投递 →
    wait_all 等齐（部分回执先达不提前返回，total=Agent 数）。超时可由响应
    `results` 观察部分聚合进度（Status: timeout 但 results 含已完成部分）。
    成本直报：X-A2A-Cost = 任务类型单价 × 扇出数（N Agent 各执行一次）。
    """
    vk = _resolve_vk(request)
    await _enforce_agent_vk_gates(vk, req.model or req.task_type)
    online = await _list_online(req.capability)
    if not online:
        raise HTTPException(
            status_code=404, detail={"error": "no_online_agent", "capability": req.capability}
        )
    receivers = [card["agent_id"] for card in online]
    trace_id = uuid.uuid4().hex
    hub = a2a_result.result_hub()
    hub.register(trace_id, total=len(receivers))
    try:
        for receiver in receivers:
            message = a2a_protocol.build_message(
                trace_id=trace_id,
                msg_type="task_request",
                sender="gateway",
                receiver=receiver,
                task_type=req.task_type,
                payload=req.payload,
                priority=req.priority,
            )
            await _submit(receiver, message)
            logger.info(
                "[a2a] 编排任务 %s 扇出 %s（capability=%s）", trace_id, receiver, req.capability
            )
        response.headers["X-A2A-Cost"] = f"{pricing.task_cost(req.task_type) * len(receivers):.6f}"
        try:
            snapshot = await hub.wait_all(
                trace_id, total=len(receivers), timeout=req.timeout_seconds
            )
        except asyncio.TimeoutError:
            logger.info(
                "[a2a] 编排任务 %s 扇入超时（%ss / %d Agent）",
                trace_id,
                req.timeout_seconds,
                len(receivers),
            )
            return {
                "trace_id": trace_id,
                "receivers": receivers,
                "status": "timeout",
                "results": hub.status(trace_id).get("results", {}),
            }
        status = "completed" if snapshot["failed"] == 0 else "partial"
        logger.info(
            "[a2a] 编排任务 %s 扇入完成（status=%s，%d 成 / %d 败）",
            trace_id,
            status,
            snapshot["completed"],
            snapshot["failed"],
        )
        return {
            "trace_id": trace_id,
            "receivers": receivers,
            "status": status,
            "progress": snapshot["progress"],
            "results": snapshot["results"],
        }
    finally:
        hub.discard(trace_id)
