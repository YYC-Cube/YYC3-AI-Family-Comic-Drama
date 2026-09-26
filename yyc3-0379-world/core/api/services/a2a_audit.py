# file: a2a_audit.py
# description: A2A 审计流 Loki 消费端——stream:audit:log → Loki 推送（孤儿/死信/重试可检索可告警）
# author: YanYuCloudCube Team <admin@0379.email>
# created: 2026-09-26
# status: active
# tags: [a2a],[audit],[loki],[observability]

"""A2A 审计流 Loki 消费端（TOP1 审计闭环）。

职责：
- 消费 `stream:audit:log`（消费者组 audit-loki，XREADGROUP ">"，与协议层 publish_audit 写入端解耦）
- 批量推送 Loki `/loki/api/v1/push`（labels：job=a2a-audit / event=action / agent=auditor；
  行 payload 为审计 entry JSON，timestamp 由 entry 毫秒时间戳转纳秒对齐）
- 推送成功才 XACK（at-least-once；Loki 侧按 timestamp 去重展示，重复推送可容忍）
- 基础设施抖动退避重试（五高-高可用）；LOKI 不可达时挂起记录保留在 PEL，恢复后 XAUTOCLAIM 可回收

开关（三层）：A2A_ENABLED × A2A_AUDIT_LOKI_ENABLED（缺省 false，LOKI_URL 缺省 localhost:3100）。
"""

import asyncio
import json
import logging
import os
import socket
import time
from typing import List, Optional, Tuple

import httpx

from app.services import a2a_protocol as proto

logger = logging.getLogger(__name__)

AUDIT_GROUP = "audit-loki"

BATCH_SIZE = 100
BLOCK_MS = 1000
BACKOFF_S = 2.0
PUSH_TIMEOUT_S = 3.0


def _enabled() -> bool:
    """A2A_AUDIT_LOKI_ENABLED 开关（缺省 false；显式 true/1/yes/on 才启用）。"""
    return os.getenv("A2A_AUDIT_LOKI_ENABLED", "").strip().lower() in ("1", "true", "yes", "on")


def loki_url() -> str:
    return os.getenv("LOKI_URL", "http://localhost:3100").rstrip("/")


def _consumer_name() -> str:
    custom = os.getenv("A2A_AUDIT_CONSUMER", "").strip()
    return custom or f"audit-loki-{socket.gethostname()}-{os.getpid()}"


def _to_loki_streams(entries: List[Tuple[str, dict]]) -> list:
    """审计 entry（Redis Hash 平面）→ Loki streams（按 event/agent 分组为 label）。"""
    groups = {}
    for _msg_id, entry in entries:
        event = str(entry.get("action") or entry.get("event") or "unknown")
        agent = str(entry.get("auditor") or entry.get("agent_id") or "unknown")
        ts_ms = entry.get("timestamp")
        try:
            ts_ns = int(float(ts_ms)) * 1_000_000 if ts_ms is not None else int(time.time() * 1e9)
        except (TypeError, ValueError):
            ts_ns = int(time.time() * 1e9)
        line = json.dumps(dict(entry), ensure_ascii=False, separators=(",", ":"))
        groups.setdefault((event, agent), []).append([str(ts_ns), line])
    return [
        {"stream": {"job": "a2a-audit", "event": event, "agent": agent}, "values": values}
        for (event, agent), values in groups.items()
    ]


async def _push(entries: List[Tuple[str, dict]]) -> None:
    """推送一批审计 entry 到 Loki（2xx 即成功；非 2xx 抛错触发上层退避，不 ACK）。"""
    body = {"streams": _to_loki_streams(entries)}
    async with httpx.AsyncClient(timeout=PUSH_TIMEOUT_S) as client:
        resp = await client.post(f"{loki_url()}/loki/api/v1/push", json=body)
    if resp.status_code >= 300:
        raise RuntimeError(f"Loki push 失败：HTTP {resp.status_code} {resp.text[:200]}")


async def ship_once(client=None) -> int:
    """拉取一批审计消息并推送 Loki，成功后 ACK。返回处理条数（测试直接驱动）。"""
    messages = await proto.poll_messages(
        proto.AUDIT_STREAM, AUDIT_GROUP, _consumer_name(), count=BATCH_SIZE, block_ms=BLOCK_MS
    )
    if not messages:
        return 0
    if client is None:
        await _push(messages)
    else:
        body = {"streams": _to_loki_streams(messages)}
        resp = await client.post(f"{loki_url()}/loki/api/v1/push", json=body)
        if resp.status_code >= 300:
            raise RuntimeError(f"Loki push 失败：HTTP {resp.status_code}")
    for mid, _entry in messages:
        await proto.ack_message(proto.AUDIT_STREAM, AUDIT_GROUP, mid)
    return len(messages)


async def ship_loop() -> None:
    """主循环：确保消费者组 → 持续拉取推送（抖动退避；取消透传）。"""
    await proto.ensure_group(proto.AUDIT_STREAM, AUDIT_GROUP)
    logger.info(
        "[a2a-audit] Loki shipper 启动：stream=%s group=%s loki=%s",
        proto.AUDIT_STREAM,
        AUDIT_GROUP,
        loki_url(),
    )
    while True:
        try:
            shipped = await ship_once()
            if not shipped:
                continue
            logger.debug("[a2a-audit] 已推送 %d 条审计", shipped)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # Loki/Redis 抖动：退避而非崩溃
            logger.warning("[a2a-audit] 推送异常，%.0fs 退避重试：%s", BACKOFF_S, exc)
            await asyncio.sleep(BACKOFF_S)


_task: Optional[asyncio.Task] = None


def start_audit_shipper() -> None:
    """启动审计 shipper（A2A_ENABLED × A2A_AUDIT_LOKI_ENABLED 双控；幂等）。"""
    global _task
    if not proto._a2a_enabled() or not _enabled() or _task is not None:
        return
    _task = asyncio.create_task(ship_loop())
    logger.info("[a2a-audit] audit shipper 已随网关启动")


async def stop_audit_shipper() -> None:
    global _task
    if _task is None:
        return
    _task.cancel()
    try:
        await _task
    except asyncio.CancelledError:
        pass
    _task = None
