# file: a2a_result.py
# description: A2A 结果流消费端（Phase 2）——编排器聚合 stream:agent:result:callback + XAUTOCLAIM 挂起回收
# author: YanYuCloudCube Team <admin@0379.email>
# created: 2026-09-26
# status: active
# tags: [a2a],[orchestrator],[redis-stream],[result]

"""结果回执聚合消费端（源：原型 AsyncOrchestrator._result_listen_loop 工程化版）。

职责：
- 消费 stream:agent:result:callback（消费者组 group-orchestrator，XREADGROUP ">"）
- 按 trace_id 聚合回执：wait_one（任一回执即返回）/ wait_all（多 Agent 扇入等齐）
- XAUTOCLAIM 挂起回收：消费端宕机滞留 PEL 的回执再派发（空闲超 CLAIM_IDLE_MS 认领）

工程化改造（相对原型）：
- threading 轮询 + result_collector 字典 → asyncio.Event 等待者 + 请求前注册聚合器
  （先注册后投递，杜绝「回执先于注册」竞态；同步端点另以 drain 追平在途回执）
- 原型 completed/failed 计数器遇回执重放会重复计数 → 结果按 sender 覆盖式存储，
  进度由集合推导（同 sender 重放幂等，XAUTOCLAIM 再投递安全）
- get_task_status 轮询 → wait_one/wait_all 异步事件驱动等待（零轮询）
- 未知 trace 的孤儿回执：dead-letter 式审计留痕（result_orphan）后 ACK，不滞留 PEL
"""

import asyncio
import logging
import os
import socket
import time
from typing import Dict, Optional

from app.services import a2a_metrics
from app.services import a2a_protocol as proto

logger = logging.getLogger(__name__)

CLAIM_IDLE_MS = 60_000  # 挂起回执空闲阈值（毫秒）：超过视为原消费者失联，可被 XAUTOCLAIM 认领
RECLAIM_INTERVAL_S = 30  # 挂起回收扫描周期（秒）


def _consumer_name() -> str:
    """结果流消费者名：env 指定优先，缺省 hostname-pid（多实例部署不串投递记录）。"""
    custom = os.getenv("A2A_RESULT_CONSUMER", "").strip()
    return f"consumer-orchestrator-{custom or f'{socket.gethostname()}-{os.getpid()}'}"


class _TraceAggregate:
    """单 trace_id 回执聚合器：results 按 sender 覆盖式存储（回执重放幂等）。"""

    def __init__(self, trace_id: str, total: Optional[int] = None):
        self.trace_id = trace_id
        self.total = total  # 期望回执数；None = 任一回执即完成（wait_one 语义）
        self.results: Dict[str, dict] = {}  # sender → 归一回执
        self.done = asyncio.Event()

    def record(self, msg: dict) -> None:
        """记录回执（同 sender 覆盖）；达到完成条件置 done 唤醒等待者。"""
        sender = str(msg.get("sender") or msg.get("stream_msg_id") or "unknown")
        self.results[sender] = {
            "msg_type": msg.get("msg_type", ""),
            "task_type": msg.get("task_type", ""),
            "payload": msg.get("payload"),
        }
        if self.total is None or len(self.results) >= self.total:
            self.done.set()

    def snapshot(self) -> dict:
        """聚合进度快照（completed/failed 由结果集合推导，天然幂等）。"""
        completed = sum(1 for r in self.results.values() if r["msg_type"] == "task_result")
        failed = sum(1 for r in self.results.values() if r["msg_type"] == "error")
        finished = len(self.results) >= (self.total or 1)
        return {
            "status": "completed" if finished else "running",
            "progress": f"{len(self.results)}/{self.total if self.total is not None else '?'}",
            "completed": completed,
            "failed": failed,
            "results": dict(self.results),
        }


class ResultHub:
    """结果回执聚合消费端（消费者组 + 等待者注册 + 挂起回收）。"""

    def __init__(self, consumer: Optional[str] = None):
        self.consumer = consumer or _consumer_name()
        self._aggregates: Dict[str, _TraceAggregate] = {}
        self._group_ready = False  # 消费者组懒创建标记（run_once 首轮 ensure_group）

    # ── 聚合器注册面（请求侧在投递任务前注册，杜绝「回执先于注册」竞态）──

    def register(self, trace_id: str, total: Optional[int] = None) -> _TraceAggregate:
        """注册（或复用）聚合器；total 给定为扇入等齐语义，否则任一回执即完成。"""
        agg = self._aggregates.get(trace_id)
        if agg is None:
            agg = self._aggregates[trace_id] = _TraceAggregate(trace_id, total)
        return agg

    def discard(self, trace_id: str) -> None:
        """注销聚合器（终态返回或放弃等待后调用；后续回执按孤儿审计）。"""
        self._aggregates.pop(trace_id, None)

    def status(self, trace_id: str) -> dict:
        """聚合进度快照（未注册返回 not_found）。"""
        agg = self._aggregates.get(trace_id)
        return agg.snapshot() if agg else {"status": "not_found"}

    # ── 等待面（事件驱动，零轮询）──

    async def wait_one(self, trace_id: str, timeout: float = proto.DEFAULT_TTL) -> dict:
        """等待该 trace 任一回执（单 Agent 请求-响应语义）；超时抛 asyncio.TimeoutError。"""
        agg = self.register(trace_id)
        await asyncio.wait_for(agg.done.wait(), timeout=timeout)
        return next(iter(agg.results.values()))

    async def wait_all(self, trace_id: str, total: int, timeout: float = proto.DEFAULT_TTL) -> dict:
        """多 Agent 扇入等齐（total 份不同 sender 回执）；返回聚合快照。"""
        agg = self.register(trace_id, total=total)
        await asyncio.wait_for(agg.done.wait(), timeout=timeout)
        return agg.snapshot()

    # ── 派发面（run_once 与 reclaim_once 共用同一语义：记录/审计 → ACK）──

    async def _handle(self, stream_msg_id: str, msg: dict) -> None:
        trace_id = str(msg.get("trace_id") or "")
        agg = self._aggregates.get(trace_id)
        if agg is None:
            # 孤儿回执（等待者已放弃/超时离开）：审计留痕后 ACK，不滞留 PEL
            a2a_metrics._result_orphan.inc()
            await proto.publish_audit(
                {
                    "trace_id": trace_id or stream_msg_id,
                    "auditor": "a2a-result",
                    "action": "result_orphan",
                    "detail": {
                        "stream_msg_id": stream_msg_id,
                        "sender": msg.get("sender"),
                        "msg_type": msg.get("msg_type"),
                    },
                    "timestamp": int(time.time() * 1000),
                }
            )
        else:
            agg.record(msg)
        await proto.ack_message(proto.RESULT_STREAM, proto.RESULT_GROUP, stream_msg_id)

    async def run_once(self, count: int = 10, block_ms: int = 0) -> int:
        """消费一轮回执并派发聚合（block_ms<=0 非阻塞；返回处理条数，供测试与探活）。"""
        if not self._group_ready:
            await proto.ensure_group(proto.RESULT_STREAM, proto.RESULT_GROUP)
            self._group_ready = True
        messages = await proto.poll_messages(
            proto.RESULT_STREAM, proto.RESULT_GROUP, self.consumer, count=count, block_ms=block_ms
        )
        for stream_msg_id, msg in messages:
            await self._handle(stream_msg_id, msg)
        return len(messages)

    async def reclaim_once(self, min_idle_ms: int = CLAIM_IDLE_MS, count: int = 10) -> int:
        """XAUTOCLAIM 挂起回收一轮：认领空闲超阈值回执并按同一语义派发（宕机兜底）。"""
        claimed = await proto.claim_stale_messages(
            proto.RESULT_STREAM,
            proto.RESULT_GROUP,
            self.consumer,
            min_idle_ms=min_idle_ms,
            count=count,
        )
        for stream_msg_id, msg in claimed:
            await self._handle(stream_msg_id, msg)
        if claimed:
            a2a_metrics._result_reclaimed.inc(len(claimed))
            logger.info("[a2a-result] 挂起回收 %d 条回执", len(claimed))
        return len(claimed)

    async def run_forever(self) -> None:
        """主循环：持续消费 + 周期挂起回收（基础设施抖动退避而非崩溃，五高-高可用）。"""
        await proto.ensure_group(proto.RESULT_STREAM, proto.RESULT_GROUP)
        self._group_ready = True
        logger.info(
            "[a2a-result] 结果流消费端启动 stream=%s group=%s consumer=%s",
            proto.RESULT_STREAM,
            proto.RESULT_GROUP,
            self.consumer,
        )
        last_reclaim = time.time()
        while True:
            try:
                processed = await self.run_once(count=10, block_ms=proto.POLL_BLOCK_MS)
                if time.time() - last_reclaim >= RECLAIM_INTERVAL_S:
                    await self.reclaim_once()
                    await a2a_metrics.refresh_gauges()  # 周期回填 DLQ/流长/PEL Gauge
                    last_reclaim = time.time()
                if not processed:
                    await asyncio.sleep(0.5)  # 空轮询间隙，避免忙等
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("[a2a-result] 消费异常，1s 退避重试：%s", exc)
                await asyncio.sleep(1.0)


# -------------------------- 生命周期（网关内嵌泵，main.py 接线） --------------------------

_hub: Optional[ResultHub] = None
_hub_task: Optional[asyncio.Task] = None
_observe_task: Optional[asyncio.Task] = None


def _enabled() -> bool:
    return os.getenv("A2A_RESULT_CONSUMER_ENABLED", "true").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def result_hub() -> ResultHub:
    """进程内单例（同步端点等待面与消费泵共用同一聚合表）。"""
    global _hub
    if _hub is None:
        _hub = ResultHub()
    return _hub


def start_result_consumer() -> None:
    """启动内嵌消费泵（A2A_ENABLED × A2A_RESULT_CONSUMER_ENABLED 双控；幂等）。"""
    global _hub_task, _observe_task
    if not proto._a2a_enabled() or not _enabled() or _hub_task is not None:
        return
    _hub_task = asyncio.create_task(result_hub().run_forever())
    _observe_task = asyncio.create_task(a2a_metrics.observe_loop())


async def stop_result_consumer() -> None:
    global _hub_task, _observe_task
    if _hub_task is not None:
        _hub_task.cancel()
        try:
            await _hub_task
        except asyncio.CancelledError:
            pass
        _hub_task = None
    if _observe_task is not None:
        _observe_task.cancel()
        try:
            await _observe_task
        except asyncio.CancelledError:
            pass
        _observe_task = None
