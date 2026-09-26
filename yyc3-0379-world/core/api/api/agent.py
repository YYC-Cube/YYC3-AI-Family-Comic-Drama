# file: agent.py
# description: AI Family Agent 编排端点 - 同步 execute + 异步任务 Worker 化（Phase 2，复刻 video_tasks 租约范式）
# author: YanYuCloudCube Team <admin@0379.email>
# created: 2026-09-25
# status: active
# tags: [api],[agent],[orchestrator],[worker],[websocket]

"""
@file: app/api/agent.py
@description: 九步编排全链路入口（试点场景：经营分析报告）。
    - POST /v1/agent/execute               同步简化版：guardrails 外层闸门 → to_thread 编排 → 输出审计
    - POST /v1/agent/tasks                 异步提交：入队即返 trace_id（RPUSH FIFO）
    - GET  /v1/agent/tasks/{id}            轮询任务状态/结果
    - WS   /ws/agent/{id}?token=           进度实时推送（Redis pub/sub；快照+事件流，终态即断）
    - POST /v1/admin/agent/tasks/claim     Worker 认领（内置或外置），附带租约过期回收
    - POST /v1/admin/agent/tasks/{id}/heartbeat   Worker 续租
    - POST /v1/admin/agent/tasks/{id}/result      Worker 回报成功
    - POST /v1/admin/agent/tasks/{id}/failure     Worker 回报失败
Worker 化（Phase 2）：执行移出请求周期——内置 Worker 随网关启动循环认领（AGENT_WORKER_ENABLED
控制），外置 Worker 经 /v1/admin/agent/** 水平扩展；租约机制防 Worker 掉线任务卡死
（attempts<2 重排队，否则 failed）。状态机 queued → running → succeeded/failed。
安全分层：网关 guardrails 链为外层基础设施闸门（Step0/Step9），
编排器内智云守护三级过滤为内层 Agent 闸门（Step1/8）——复用不重复建设（融合决策）。
"""

import asyncio
import json
import logging
import os
import time
import uuid
from typing import AsyncIterator, List, Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from app.cache import redis_client
from app.middleware.auth import verify_api_key
from app.services.a2a_protocol import publish_audit as _publish_audit
from app.services.agent_retriever import PGVectorRetriever
from app.services.guardrails import run_guardrails
from core.agents import AIFamilyOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter()

_TASK_TTL = 7 * 86400  # 任务记录 7 天（对齐 video_tasks 保留策略）
_MAX_ATTEMPTS = 2  # 租约过期重试上限
# 同步执行上限（九步串行 LLM 最坏情形远大于 Mock 模式；超时 504 而非无限挂起）
_EXECUTE_TIMEOUT_S = 300.0
_WORKER_LEASE_MIN = 30  # 内置 Worker 租约（执行超时 300s ≪ 租约，无需心跳续租）

_KEY_TASK = "agent:task:{id}"
_KEY_QUEUE = "agent:queue"  # FIFO：RPUSH 入队 / LPOP 认领
_KEY_INDEX = "agent:ids"  # 全量 id 索引（SET，租约回收遍历用）
_KEY_EVENTS = "agent:events:{id}"  # 进度事件 pub/sub 频道
_TERMINAL = ("succeeded", "failed")


# ── Redis 薄存储层（测试桩替点，范式同 video_tasks）────────────


async def _store_task(task: dict, ttl: int = _TASK_TTL) -> None:
    payload = json.dumps(task, ensure_ascii=False)
    await redis_client.set(_KEY_TASK.format(id=task["id"]), payload, ex=ttl)


async def _load_task(task_id: str) -> Optional[dict]:
    raw = await redis_client.get(_KEY_TASK.format(id=task_id))
    return json.loads(raw) if raw else None


async def _queue_push(task_id: str) -> None:
    await redis_client.rpush(_KEY_QUEUE, task_id)


async def _queue_pop() -> Optional[str]:
    task_id = await redis_client.lpop(_KEY_QUEUE)
    return task_id if task_id else None


async def _queue_len() -> int:
    return int(await redis_client.llen(_KEY_QUEUE))


async def _index_add(task_id: str) -> None:
    await redis_client.sadd(_KEY_INDEX, task_id)


async def _index_all() -> List[str]:
    return [x for x in await redis_client.smembers(_KEY_INDEX)]


async def _publish_event(task_id: str, event: dict) -> None:
    """进度事件发布（pub/sub 尽力而为：失败只记日志，不阻断任务主链路）。"""
    try:
        payload = json.dumps(event, ensure_ascii=False)
        await redis_client.publish(_KEY_EVENTS.format(id=task_id), payload)
    except Exception as exc:
        logger.warning("[agent:task:%s] 进度事件发布失败（不阻断）：%s", task_id, exc)


async def _audit_task_event(action: str, trace_id: str, detail: dict) -> None:
    """任务生命周期审计事件 → A2A stream:audit:log（尽力而为；对齐 zhiyun entry 结构）。"""
    await _publish_audit(
        {
            "trace_id": trace_id,
            "auditor": "agent-gateway",
            "action": action,
            "detail": detail,
            "timestamp": int(time.time() * 1000),
        }
    )


async def _iter_events(task_id: str) -> AsyncIterator[dict]:
    """订阅任务事件流；空轮询间隙复核任务终态，防止「终态事件早于订阅发布」的悬挂。"""
    pubsub = redis_client.pubsub()
    try:
        await pubsub.subscribe(_KEY_EVENTS.format(id=task_id))
        empty_polls = 0
        while True:
            msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if msg is None:
                empty_polls += 1
                if empty_polls >= 5:  # ≈5s 无事件则核对任务态（终态兜底退出）
                    empty_polls = 0
                    t = await _load_task(task_id)
                    if t and t.get("status") in _TERMINAL:
                        yield {"type": t["status"], "data": {"error": t.get("error")}}
                continue
            empty_polls = 0
            yield json.loads(msg["data"])
    finally:
        try:
            await pubsub.unsubscribe(_KEY_EVENTS.format(id=task_id))
            await pubsub.aclose()
        except Exception:
            pass


# ── 租约状态机（认领/回收/回报）──────────────────────────────


async def _sweep_expired() -> int:
    """回收租约过期的 running 任务：attempts<_MAX_ATTEMPTS 重排队，否则 failed"""
    swept = 0
    now = time.time()
    for task_id in await _index_all():
        t = await _load_task(task_id)
        if not t or t.get("status") != "running":
            continue
        if t.get("lease_until", 0) > now:
            continue
        t["attempts"] = t.get("attempts", 0) + 1
        if t["attempts"] >= _MAX_ATTEMPTS:
            t["status"] = "failed"
            t["error"] = f"Worker 租约过期且达重试上限（lease_until={t.get('lease_until')}）"
            await _publish_event(task_id, {"type": "failed", "data": {"error": t["error"]}})
            await _audit_task_event("sweep_failed", task_id, {"error": t["error"]})
        else:
            t["status"] = "queued"
            t["error"] = f"Worker 租约过期，第 {t['attempts']} 次重排队"
            await _queue_push(task_id)
            await _publish_event(task_id, {"type": "requeued", "data": {"attempts": t["attempts"]}})
            await _audit_task_event("requeue", task_id, {"attempts": t["attempts"]})
        t["updated_at"] = now
        await _store_task(t)
        swept += 1
    return swept


async def _claim_next(runner: str, lease_minutes: int) -> Optional[dict]:
    """认领最早已排队任务（FIFO）；无任务返回 None。附带租约过期回收。"""
    await _sweep_expired()
    while True:
        task_id = await _queue_pop()
        if not task_id:
            return None
        t = await _load_task(task_id)
        if not t or t.get("status") != "queued":
            continue  # 已被回收/失效的队列残项，跳过
        t["status"] = "running"
        t["runner"] = runner
        t["lease_until"] = time.time() + lease_minutes * 60
        t["updated_at"] = time.time()
        await _store_task(t)
        await _publish_event(task_id, {"type": "running", "data": {"runner": runner}})
        await _audit_task_event("claim", task_id, {"runner": runner})
        logger.info("[agent] 任务 %s 被 %s 认领（lease %dmin）", task_id, runner, lease_minutes)
        return t


# ── 编排器装配（测试桩替点）──────────────────────────────────


def _build_orchestrator(knowledge_base_ids: List[str]):
    """按知识域装配编排器：配置了知识库 → PGVectorRetriever，否则 NullRetriever 降级。"""
    retriever = PGVectorRetriever(knowledge_base_ids) if knowledge_base_ids else None
    return AIFamilyOrchestrator(retriever=retriever)


# ── 模型 ────────────────────────────────────────────────────


class AgentExecuteRequest(BaseModel):
    """同步编排请求"""

    input: str = Field(..., min_length=1, max_length=32_000, description="用户任务输入")
    user_id: str = Field("default_user", max_length=128, description="用户标识（个性化与审计）")
    knowledge_base_ids: List[str] = Field(
        default_factory=list, description="RAG 知识库 ID（空=纯推理）"
    )


class AgentTaskCreate(BaseModel):
    """异步任务提交"""

    input: str = Field(..., min_length=1, max_length=32_000, description="用户任务输入")
    user_id: str = Field("default_user", max_length=128, description="用户标识")
    knowledge_base_ids: List[str] = Field(default_factory=list, description="RAG 知识库 ID")


class ClaimRequest(BaseModel):
    runner: str = Field(..., max_length=64, description="Worker 标识（如 builtin / yyc3-22-mac）")
    lease_minutes: int = Field(30, ge=5, le=720)


class HeartbeatRequest(BaseModel):
    runner: str = Field(..., max_length=64)
    lease_minutes: int = Field(30, ge=5, le=720)


class ResultRequest(BaseModel):
    result: dict = Field(..., description="编排结果（status/final_output/steps/agent_outputs）")


class FailureRequest(BaseModel):
    error: str = Field(..., max_length=2000)


def _public_view(t: dict) -> dict:
    """对外视图"""
    return {
        "trace_id": t["id"],
        "status": t["status"],
        "created_at": t.get("created_at"),
        "updated_at": t.get("updated_at"),
        "attempts": t.get("attempts", 0),
        "runner": t.get("runner"),
        "error": t.get("error"),
        "result": t.get("result") if t.get("status") == "succeeded" else None,
    }


async def _run_pipeline(req_input: str, user_id: str, kb_ids: List[str], progress_cb=None) -> dict:
    """公共执行管线：外层输入闸门 → 九步编排（工作线程）→ 外层输出闸门。

    抛 HTTPException(400/422/504)；编排级 blocked 属 Agent 内层审计结论，随结果返回。
    """
    verdict = await run_guardrails(req_input, "input")
    if verdict:
        raise HTTPException(status_code=400, detail={"error": "input_blocked", "reason": verdict})

    orchestrator = _build_orchestrator(kb_ids)
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(orchestrator.execute, req_input, user_id, progress_cb),
            timeout=_EXECUTE_TIMEOUT_S,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail={"error": "orchestration_timeout"})

    out_verdict = await run_guardrails(str(result.get("final_output", "")), "output")
    if out_verdict:
        raise HTTPException(
            status_code=422, detail={"error": "output_blocked", "reason": out_verdict}
        )
    return result


# ── 同步简化版 ───────────────────────────────────────────────


@router.post("/v1/agent/execute")
async def execute_agent(req: AgentExecuteRequest):
    """九步编排同步执行（试点场景：经营分析报告九步闭环）。"""
    started = time.perf_counter()
    result = await _run_pipeline(req.input, req.user_id, req.knowledge_base_ids)
    return {
        "trace_id": uuid.uuid4().hex,
        "status": result.get("status"),
        "final_output": result.get("final_output"),
        "steps": result.get("steps"),
        "agent_outputs": result.get("agent_outputs"),
        "latency_ms": round((time.perf_counter() - started) * 1000, 1),
    }


# ── 异步任务（公共端点）──────────────────────────────────────


@router.post("/v1/agent/tasks", status_code=201)
async def create_agent_task(req: AgentTaskCreate):
    """提交异步编排任务，入队即返 trace_id；执行由 Worker 认领完成。"""
    now = time.time()
    task = {
        "id": uuid.uuid4().hex,
        "status": "queued",
        "input": req.input,
        "user_id": req.user_id,
        "knowledge_base_ids": req.knowledge_base_ids,
        "created_at": now,
        "updated_at": now,
        "attempts": 0,
        "result": None,
        "error": None,
    }
    await _store_task(task)
    await _queue_push(task["id"])
    await _index_add(task["id"])
    position = max(await _queue_len() - 1, 0)
    await _publish_event(task["id"], {"type": "queued", "data": {"queue_position": position}})
    await _audit_task_event(
        "submit", task["id"], {"user_id": req.user_id, "queue_position": position}
    )
    return {
        "trace_id": task["id"],
        "status": "queued",
        "queue_position": position,
        "created_at": now,
    }


@router.get("/v1/agent/tasks/{trace_id}")
async def get_agent_task(trace_id: str):
    """轮询任务状态与结果。"""
    task = await _load_task(trace_id)
    if not task:
        raise HTTPException(status_code=404, detail={"error": "task_not_found"})
    return _public_view(task)


# ── 进度实时推送（WS；范式同 /ws/chat 的 token 认证）──────────


@router.websocket("/ws/agent/{task_id}")
async def agent_progress_ws(websocket: WebSocket, task_id: str, token: Optional[str] = Query(None)):
    """任务进度实时推送：先发当前快照，再转发事件流，终态即断开。"""
    if not token:
        await websocket.close(code=4001, reason="Missing authentication token")
        return
    try:
        if not verify_api_key(token):
            await websocket.close(code=4003, reason="Invalid API key")
            return
    except Exception:
        logger.exception("[agent-ws] 认证异常")
        await websocket.close(code=4003, reason="Authentication failed")
        return

    await websocket.accept()
    try:
        task = await _load_task(task_id)
        if not task:
            await websocket.send_json({"type": "error", "data": {"error": "task_not_found"}})
            return
        await websocket.send_json({"type": "snapshot", "data": _public_view(task)})
        if task.get("status") in _TERMINAL:
            return
        async for event in _iter_events(task_id):
            await websocket.send_json(event)
            if event.get("type") in _TERMINAL:
                break
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("[agent-ws] 推送异常 task=%s", task_id)
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


# ── Worker 管理端点（/v1/admin/** 由 auth 中间件以 ADMIN_API_KEYS 保护）──


@router.post("/v1/admin/agent/tasks/claim")
async def claim_agent_task(req: ClaimRequest):
    """Worker 领取最早已排队任务（FIFO）；无任务返回 {"claimed": null}。"""
    claimed = await _claim_next(req.runner, req.lease_minutes)
    return {"claimed": claimed}


@router.post("/v1/admin/agent/tasks/{task_id}/heartbeat")
async def heartbeat_agent_task(task_id: str, req: HeartbeatRequest):
    t = await _load_task(task_id)
    if not t or t.get("status") != "running":
        raise HTTPException(status_code=409, detail="任务不存在或不处于 running")
    t["runner"] = req.runner
    t["lease_until"] = time.time() + req.lease_minutes * 60
    t["updated_at"] = time.time()
    await _store_task(t)
    return {"trace_id": task_id, "lease_until": t["lease_until"]}


@router.post("/v1/admin/agent/tasks/{task_id}/result")
async def report_agent_result(task_id: str, req: ResultRequest):
    """Worker 回报成功：编排结果落任务记录并推送终态事件。"""
    t = await _load_task(task_id)
    if not t or t.get("status") != "running":
        raise HTTPException(status_code=409, detail="任务不存在或不处于 running")
    t["status"] = "succeeded"
    t["result"] = req.result
    t["updated_at"] = time.time()
    await _store_task(t)
    result_status = req.result.get("status")
    await _publish_event(task_id, {"type": "succeeded", "data": {"status": result_status}})
    await _audit_task_event(
        "succeeded", task_id, {"runner": t.get("runner"), "status": result_status}
    )
    logger.info("[agent] 任务 %s 成功（runner=%s）", task_id, t.get("runner"))
    return {"trace_id": task_id, "status": "succeeded"}


@router.post("/v1/admin/agent/tasks/{task_id}/failure")
async def report_agent_failure(task_id: str, req: FailureRequest):
    t = await _load_task(task_id)
    if not t or t.get("status") != "running":
        raise HTTPException(status_code=409, detail="任务不存在或不处于 running")
    t["status"] = "failed"
    t["error"] = req.error
    t["updated_at"] = time.time()
    await _store_task(t)
    await _publish_event(task_id, {"type": "failed", "data": {"error": req.error}})
    await _audit_task_event("failed", task_id, {"error": req.error, "runner": t.get("runner")})
    logger.warning("[agent] 任务 %s 失败：%s", task_id, req.error[:200])
    return {"trace_id": task_id, "status": "failed"}


# ── 内置 Worker（网关进程内循环认领；外置 Worker 部署时置 false）──

_worker_task: Optional[asyncio.Task] = None


def _worker_enabled() -> bool:
    return os.getenv("AGENT_WORKER_ENABLED", "true").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


async def _execute_claimed(task: dict) -> None:
    """内置 Worker 执行已认领任务：结果落库 + 事件流推送（状态迁移由 _claim_next 已发）。"""
    loop = asyncio.get_running_loop()

    def _cb(event: str, data: dict) -> None:
        # 编排在 to_thread 工作线程执行，进度事件经 threadsafe 调度回事件循环
        asyncio.run_coroutine_threadsafe(
            _publish_event(task["id"], {"type": event, "data": data}), loop
        )

    try:
        result = await _run_pipeline(
            task["input"], task["user_id"], task["knowledge_base_ids"], _cb
        )
        task["status"] = "succeeded"
        task["result"] = {
            "status": result.get("status"),
            "final_output": result.get("final_output"),
            "steps": result.get("steps"),
            "agent_outputs": result.get("agent_outputs"),
        }
        await _store_task(task)
        final_status = result.get("status")
        await _publish_event(task["id"], {"type": "succeeded", "data": {"status": final_status}})
        await _audit_task_event(
            "succeeded", task["id"], {"runner": "builtin", "status": final_status}
        )
        logger.info(
            "[agent:task:%s] 内置 Worker 执行完成（status=%s）",
            task["id"],
            final_status,
        )
    except HTTPException as exc:
        task["status"] = "failed"
        task["error"] = str(exc.detail)
        await _store_task(task)
        await _publish_event(task["id"], {"type": "failed", "data": {"error": task["error"]}})
        await _audit_task_event("failed", task["id"], {"error": task["error"], "runner": "builtin"})
    except Exception as exc:  # 意外异常不丢任务态（高可用：状态可追溯，租约兜底可重试）
        logger.exception("[agent:task:%s] 内置 Worker 执行异常", task["id"])
        task["status"] = "failed"
        task["error"] = f"internal_error: {exc}"
        await _store_task(task)
        await _publish_event(task["id"], {"type": "failed", "data": {"error": task["error"]}})
        await _audit_task_event("failed", task["id"], {"error": task["error"], "runner": "builtin"})


async def _worker_loop() -> None:
    logger.info("[agent-worker] 内置 Worker 已启动（lease %dmin）", _WORKER_LEASE_MIN)
    while True:
        try:
            claimed = await _claim_next("builtin", _WORKER_LEASE_MIN)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # Redis 未就绪等基础设施抖动：退避重试而非崩溃
            logger.warning("[agent-worker] 认领失败，5s 退避重试：%s", exc)
            await asyncio.sleep(5.0)
            continue
        if not claimed:
            await asyncio.sleep(1.0)
            continue
        try:
            await _execute_claimed(claimed)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("[agent-worker] 任务 %s 执行异常", claimed["id"])


def start_worker() -> None:
    """启动内置 Worker（幂等；AGENT_WORKER_ENABLED=false 时不启动）。"""
    global _worker_task
    if not _worker_enabled() or _worker_task is not None:
        return
    _worker_task = asyncio.create_task(_worker_loop())


async def stop_worker() -> None:
    global _worker_task
    if _worker_task is not None:
        _worker_task.cancel()
        try:
            await _worker_task
        except asyncio.CancelledError:
            pass
        _worker_task = None
