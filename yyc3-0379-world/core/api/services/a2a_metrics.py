# file: a2a_metrics.py
# description: A2A 流通道可观测（Prometheus 指标面 + Redis 流真实长度/PEL/DLQ 快照采集）
# author: YanYuCloudCube Team <admin@0379.email>
# created: 2026-09-26
# status: active
# tags: [a2a],[metrics],[prometheus],[observability]

"""A2A 流通道可观测（TOP 3：DLQ 深度 / 结果流堆积 / 挂起回收量 / 各 Agent 任务流 PEL）。

采集器（collector）：
- 受控环境解析：SURVIVABLE_ENV / 命名空间回退，或直接枚举 A2A_WORKER_AGENTS
  （路由与 a2a_workers.WORKER_AGENT_IDS 同源取 env A2A_WORKER_AGENTS，保证消费流
  与采集目标一致，杜绝仪表盘指向无人消费的死流）
- 快照方法纯内存 + Redis XLEN / XAUTOCLAIM dryrun 计数（只读，零业务影响）

指标（注册进 api 层全局 REGISTRY，由 main.py Instrumentator /metrics 暴露）：
- Counter：a2a_dlq_enqueued_total / a2a_result_orphan_total / a2a_result_reclaimed_total
- Gauge（快照回填）：a2a_dlq_depth / a2a_result_stream_len /
  a2a_task_stream_pending{agent_id} / a2a_result_stream_pending

采集时机：run_forever 周期（30s）+ 同步端点 run_once 后回填结果流 Gauge（同进程低延迟可见）。
"""

import asyncio
import logging
import os
from typing import Optional, Tuple

from prometheus_client import Counter, Gauge

from app.services import a2a_protocol as proto

logger = logging.getLogger(__name__)

# 采集周期（秒）：与 XAUTOCLAIM 回收扫描周期对齐
OBSERVE_INTERVAL_S = 30

_dlq_enqueued = Counter(
    "a2a_dlq_enqueued_total", "A2A 死信入队总数（任务重试达 MAX_RETRY 后迁移 DLQ）"
)
_result_orphan = Counter(
    "a2a_result_orphan_total", "A2A 结果流孤儿回执总数（无等待者，审计 result_orphan）"
)
_result_reclaimed = Counter(
    "a2a_result_reclaimed_total", "A2A 结果流挂起回收总数（XAUTOCLAIM 认领后派发）"
)
_dlq_depth = Gauge("a2a_dlq_depth", "A2A 死信流当前长度", ["agent_id"])
_result_stream_len = Gauge("a2a_result_stream_len", "A2A 结果流当前长度（堆积监控）")
_result_pending = Gauge("a2a_result_stream_pending", "A2A 结果流 PEL 挂起条数")
_task_pending = Gauge("a2a_task_stream_pending", "A2A 各 Agent 任务流 PEL 挂起条数", ["agent_id"])


def infer_survivable_env() -> Optional[str]:
    """受控环境名：优先 SURVIVABLE_ENV（惯例），命名空间回退，均空返回 None。"""
    env = os.getenv("SURVIVABLE_ENV", "").strip()
    if env:
        return env
    return os.getenv("POD_NAMESPACE", "").strip() or None


def task_stream_agents() -> Tuple[str, ...]:
    """可采集任务流 Agent 列表：A2A_WORKER_AGENTS（消费路由 env）优先，缺省空。

    规则：只采「有外置 Worker 消费」的任务流，避免仪表盘指向无人消费的死流堆积告警。
    """
    raw = os.getenv("A2A_WORKER_AGENTS", "").strip()
    if raw:
        return tuple(a.strip() for a in raw.split(",") if a.strip())
    return tuple()


async def refresh_gauges() -> dict:
    """真实 Redis 快照回填 Gauge（XLEN 流长 + XAUTOCLAIM dryrun 计数 PEL；失败不抛）。

    返回快照摘要（供测试断言与日志）。PEL 语义：投递未 ACK 的挂起条数；DRYRUN 不改归属。
    """
    result_len = 0
    result_pending = 0
    try:
        result_len = int(await proto.redis_client.xlen(proto.RESULT_STREAM) or 0)
        _result_stream_len.set(result_len)
        claimed = await proto.claim_stale_messages(
            proto.RESULT_STREAM,
            proto.RESULT_GROUP,
            "metrics-probe",
            min_idle_ms=0,
            count=10_000,
        )
        result_pending = len(claimed)
        _result_pending.set(result_pending)
    except Exception as exc:
        logger.debug("[a2a-metrics] 结果流快照失败（降级 0）：%s", exc)

    agents = task_stream_agents()
    dlq_depths: dict = {}
    pending_by_agent: dict = {}
    for agent_id in agents:
        stream = proto.task_stream(agent_id)
        dlq = proto.dlq_stream(agent_id)
        try:
            depth = int(await proto.redis_client.xlen(dlq) or 0)
            _dlq_depth.labels(agent_id=agent_id).set(depth)
            dlq_depths[agent_id] = depth
        except Exception as exc:
            logger.debug("[a2a-metrics] DLQ 深度采集失败 %s：%s", agent_id, exc)
        try:
            claimed = await proto.claim_stale_messages(
                stream, f"group-{agent_id}", "metrics-probe", min_idle_ms=0, count=10_000
            )
            _task_pending.labels(agent_id=agent_id).set(len(claimed))
            pending_by_agent[agent_id] = len(claimed)
        except Exception as exc:
            logger.debug("[a2a-metrics] 任务流 PEL 采集失败 %s：%s", agent_id, exc)
    return {
        "result_stream_len": result_len,
        "result_pending": result_pending,
        "dlq_depths": dlq_depths,
        "task_pending": pending_by_agent,
    }


async def observe_loop() -> None:
    """周期采集循环（run_forever 复用）：与 XAUTOCLAIM 回收扫描对齐，失败退避不崩。"""
    while True:
        try:
            await refresh_gauges()
            await asyncio.sleep(OBSERVE_INTERVAL_S)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("[a2a-metrics] 采集轮异常（退避重试）：%s", exc)
            await asyncio.sleep(OBSERVE_INTERVAL_S)
