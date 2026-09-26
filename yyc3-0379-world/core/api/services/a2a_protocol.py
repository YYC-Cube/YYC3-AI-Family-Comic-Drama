# file: a2a_protocol.py
# description: A2A 通信协议服务 v1.0 —— Agent Card 注册中心 / 消息信封 / 审计流（Phase 2）
# author: YanYuCloudCube Team <admin@0379.email>
# created: 2026-09-26
# status: active
# tags: [a2a],[registry],[redis-stream],[audit]

"""A2A 通信协议服务（源：docs/YYC3-多端部署-Agent代码/91-A2A-通信协议 原型工程化版）。

三大能力（可行性报告 Phase 2 剩余项）：
- Agent Card 注册中心：Redis Hash（a2a:agent:registry）+ 30s 心跳 / 90s 超时离线 + 能力标签发现
- 消息信封：msg_id / trace_id / msg_type / sender / receiver / task_type / payload / priority / ttl
- 审计流：stream:audit:log（XADD 尽力而为）；zhiyun set_audit_sink 注入线程安全同步 sink

工程化改造（相对原型）：
- 原型直连 redis.Redis 全局单例 → 注册中心走网关异步客户端（app.cache.redis_client），
  审计 sink 因工作线程同步调用语义单独持有同步连接（懒初始化）
- print → logging；注册/心跳合并为幂等 HSET 循环（Redis 重启自愈重注册，五高-高可用）
- 内置编队卡片随网关启动注册（A2A_ENABLED 控制）；外置 Agent 经 /v1/admin/a2a/** 注册
"""

import asyncio
import json
import logging
import os
import time
import uuid
from typing import List, Optional

import redis

from app.cache import redis_client
from app.config import settings

logger = logging.getLogger(__name__)

# -------------------------- 常量（对齐原型 91-A2A） --------------------------
AGENT_REGISTRY_KEY = "a2a:agent:registry"  # 注册中心 Hash
AUDIT_STREAM = "stream:audit:log"  # 审计流（消费端接 Loki + NAS RAID1 双写）
HEARTBEAT_TIMEOUT = 90  # 心跳超时（秒）：超时即离线
_HEARTBEAT_INTERVAL = 30  # 内置编队心跳周期（秒）
DEFAULT_TTL = 300  # 默认消息超时（秒）
TASK_STREAM_PREFIX = "stream:agent:task:"  # 每 Agent 独立任务流：{prefix}{agent_id}
DLQ_SUFFIX = ":dlq"  # 死信流：{任务流}:dlq（nack 达 MAX_RETRY 迁移）
RESULT_STREAM = (
    "stream:agent:result:callback"  # 结果回执流（编排器聚合，见 services/a2a_result.py）
)
RESULT_GROUP = "group-orchestrator"  # 结果流消费者组（原型 AsyncOrchestrator 同值）
MAX_RETRY = 3  # 失败重试上限（原型同值）：nack 计数达限迁移死信
RETRY_KEY_PREFIX = "a2a:retry:"  # 重试计数 Key：{prefix}{stream_msg_id}（INCR + EXPIRE）
RETRY_KEY_TTL = 3600  # 重试计数过期（秒）
STREAM_MAXLEN = 10_000  # 流近似修剪上限（防无消费者端堆积失控）
POLL_BLOCK_MS = 5000  # XREADGROUP 阻塞窗口（毫秒，原型同值）

# 内置编队（8 位成员 Agent；元启·天枢兼任编排器，经 /v1/agent/tasks 队列消费）
BUILTIN_AGENTS: List[dict] = [
    {
        "agent_id": "yuanqi-tianshu-001",
        "agent_name": "元启·天枢",
        "role": "决策中枢",
        "layer": "decision",
        "capabilities": ["multi_agent_coordination", "synthesis"],
    },
    {
        "agent_id": "zhiyun-shouhu-001",
        "agent_name": "智云·守护",
        "role": "安全官",
        "layer": "core",
        "capabilities": ["input_safety", "output_audit", "pii_desensitize"],
    },
    {
        "agent_id": "gewu-zongshi-001",
        "agent_name": "格物·宗师",
        "role": "质量官",
        "layer": "core",
        "capabilities": ["quality_check", "fact_verification"],
    },
    {
        "agent_id": "chuangxiang-lingyun-001",
        "agent_name": "创想·灵韵",
        "role": "创意官",
        "layer": "core",
        "capabilities": ["report_polish", "creative_brainstorm"],
        "endpoint": "stream:agent:task:chuangxiang-lingyun-001",  # 外置 Worker 消费流
    },
    {
        "agent_id": "yanqi-qianhang-001",
        "agent_name": "言启·千行",
        "role": "导航员",
        "layer": "business",
        "capabilities": ["intent_routing"],
    },
    {
        "agent_id": "yushu-wanwu-001",
        "agent_name": "语枢·万物",
        "role": "思考者",
        "layer": "business",
        "capabilities": ["data_analysis"],
        "endpoint": "stream:agent:task:yushu-wanwu-001",  # 外置 Worker 消费流
    },
    {
        "agent_id": "yujian-xianzhi-001",
        "agent_name": "预见·先知",
        "role": "预言家",
        "layer": "business",
        "capabilities": ["trend_forecast", "qualitative_analysis"],
        "endpoint": "stream:agent:task:yujian-xianzhi-001",  # 外置 Worker 消费流
    },
    {
        "agent_id": "zhiyu-bole-001",
        "agent_name": "知遇·伯乐",
        "role": "伯乐",
        "layer": "business",
        "capabilities": ["user_profiling", "personalized_recommendation"],
    },
]


# -------------------------- 消息信封（镜像原型 build/parse） --------------------------


def generate_msg_id() -> str:
    """A2A 消息 ID：时间戳毫秒 + 8 位随机（对齐原型格式）。"""
    return f"msg-{int(time.time() * 1000)}-{uuid.uuid4().hex[:8]}"


def build_message(
    trace_id: str,
    msg_type: str,
    sender: str,
    receiver: str,
    task_type: str,
    payload: dict,
    priority: int = 5,
    ttl: int = DEFAULT_TTL,
) -> dict:
    """构建标准 A2A 消息信封（payload 序列化为 JSON 串，适配 Redis Stream 字段）。"""
    return {
        "msg_id": generate_msg_id(),
        "trace_id": trace_id,
        "msg_type": msg_type,
        "sender": sender,
        "receiver": receiver,
        "task_type": task_type,
        "payload": json.dumps(payload, ensure_ascii=False),
        "priority": priority,
        "timestamp": int(time.time() * 1000),
        "ttl": ttl,
    }


def parse_message(message_data: dict) -> dict:
    """解析消息信封，反序列化 payload（解析失败保留原文，不抛异常）。"""
    msg = dict(message_data)
    if isinstance(msg.get("payload"), str):
        try:
            msg["payload"] = json.loads(msg["payload"])
        except Exception:
            pass
    return msg


# -------------------------- 注册中心（薄存储层，测试桩替点） --------------------------


def _agent_card(card: dict, previous: Optional[dict] = None) -> dict:
    """补全卡片元数据：首次注册时间保留，心跳刷新为当前。"""
    now = time.time()
    full = dict(card)
    full["register_time"] = (previous or {}).get("register_time") or time.strftime(
        "%Y-%m-%dT%H:%M:%S"
    )
    full["last_heartbeat"] = now
    full["status"] = "online"
    return full


async def _registry_register(card: dict) -> dict:
    """注册/刷新 Agent Card（幂等 HSET，Redis 重启自愈重注册）。"""
    agent_id = card["agent_id"]
    raw = await redis_client.hget(AGENT_REGISTRY_KEY, agent_id)
    previous = json.loads(raw) if raw else None
    full = _agent_card(card, previous)
    await redis_client.hset(AGENT_REGISTRY_KEY, agent_id, json.dumps(full, ensure_ascii=False))
    return full


async def _registry_heartbeat(agent_id: str) -> bool:
    """心跳保活：刷新 last_heartbeat；未注册返回 False（原型同语义）。"""
    raw = await redis_client.hget(AGENT_REGISTRY_KEY, agent_id)
    if not raw:
        return False
    card = json.loads(raw)
    card["last_heartbeat"] = time.time()
    card["status"] = "online"
    await redis_client.hset(AGENT_REGISTRY_KEY, agent_id, json.dumps(card, ensure_ascii=False))
    return True


async def _registry_all_cards() -> List[dict]:
    """全量卡片（附实时在线状态判定：90s 心跳超时即 offline）。"""
    raw_cards = await redis_client.hgetall(AGENT_REGISTRY_KEY)
    now = time.time()
    cards = []
    for raw in raw_cards.values():
        card = json.loads(raw)
        card["status"] = (
            "online" if now - card.get("last_heartbeat", 0) < HEARTBEAT_TIMEOUT else "offline"
        )
        cards.append(card)
    return cards


async def _registry_online_cards(capability: Optional[str] = None) -> List[dict]:
    """在线 Agent 列表；capability 给定时按能力标签过滤（能力发现闭环）。"""
    cards = await _registry_all_cards()
    online = [c for c in cards if c["status"] == "online"]
    if capability:
        online = [c for c in online if capability in c.get("capabilities", [])]
    return sorted(online, key=lambda c: c["agent_id"])


# -------------------------- 审计流（stream:audit:log） --------------------------


def _stringify(fields: dict) -> dict:
    """Redis Stream 字段必须为 str：非字符串值 JSON 序列化（对齐 zhiyun entry 结构）。"""
    return {
        k: (v if isinstance(v, str) else json.dumps(v, ensure_ascii=False))
        for k, v in fields.items()
    }


async def publish_audit(entry: dict) -> None:
    """审计事件写入 stream:audit:log（尽力而为：失败仅告警，绝不阻断业务链路）。"""
    try:
        await redis_client.xadd(AUDIT_STREAM, _stringify(entry))
    except Exception as exc:
        logger.warning("[a2a] 审计流写入失败（不阻断）：%s", exc)


_sync_redis: Optional[redis.Redis] = None


def _sync_client() -> redis.Redis:
    """同步 Redis 连接（懒初始化）：审计 sink 在 to_thread 工作线程被同步调用，
    异步客户端不可用，故单独持有同步连接（低频审计，连接开销可接受）。"""
    global _sync_redis
    if _sync_redis is None:
        _sync_redis = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password,
            decode_responses=True,
            socket_keepalive=True,
        )
    return _sync_redis


def make_threadsafe_audit_sink():
    """构造线程安全审计 sink（供 core.agents.set_audit_sink 注入）。

    写失败向上抛异常，由 zhiyun.write_audit_log 降级本地日志（高可用语义在调用侧）。
    """

    def _sink(entry: dict) -> None:
        _sync_client().xadd(AUDIT_STREAM, _stringify(entry))

    return _sink


# -------------------------- A2A 任务通道（消费者组，镜像原型 MessageConsumer） --------------------------


def task_stream(agent_id: str) -> str:
    """目标 Agent 任务流名（约定优于配置：endpoint 字段同源）。"""
    return f"{TASK_STREAM_PREFIX}{agent_id}"


def dlq_stream(agent_id: str) -> str:
    """目标 Agent 死信流名（nack 达 MAX_RETRY 的迁移终点）。"""
    return f"{TASK_STREAM_PREFIX}{agent_id}{DLQ_SUFFIX}"


async def ensure_group(stream: str, group: str) -> None:
    """确保消费者组存在（mkstream + BUSYGROUP 幂等容忍，镜像原型 _ensure_group）。"""
    try:
        await redis_client.xgroup_create(stream, group, id="0", mkstream=True)
    except redis.exceptions.ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise


async def send_task_message(receiver_agent_id: str, message: dict) -> str:
    """任务信封投递至目标 Agent 任务流（MAXLEN 近似修剪，防堆积失控）。"""
    return await redis_client.xadd(
        task_stream(receiver_agent_id), _stringify(message), maxlen=STREAM_MAXLEN
    )


async def send_result_message(message: dict) -> str:
    """结果回执写入结果流（编排器聚合消费端后续接入；同样 MAXLEN 修剪）。"""
    return await redis_client.xadd(RESULT_STREAM, _stringify(message), maxlen=STREAM_MAXLEN)


async def poll_messages(
    stream: str,
    group: str,
    consumer: str,
    count: int = 1,
    block_ms: int = POLL_BLOCK_MS,
) -> List[tuple]:
    """消费者组读取新消息（">" 仅取未投递条目），返回 [(stream_msg_id, 信封)]。"""
    batches = await redis_client.xreadgroup(
        groupname=group,
        consumername=consumer,
        streams={stream: ">"},
        count=count,
        # block_ms<=0 视为非阻塞（BLOCK 0 在 Redis 语义中是无限期阻塞）
        block=block_ms if block_ms and block_ms > 0 else None,
    )
    result: List[tuple] = []
    for _, entries in batches or []:
        for stream_msg_id, fields in entries:
            result.append((stream_msg_id, parse_message(fields)))
    return result


async def ack_message(stream: str, group: str, stream_msg_id: str) -> None:
    """确认消息已处理（从消费者组 pending 移除）。"""
    await redis_client.xack(stream, group, stream_msg_id)


async def nack_message(
    stream: str, group: str, stream_msg_id: str, reason: str, trace_id: str = ""
) -> int:
    """失败重试：INCR 计数（1h 过期）；达 MAX_RETRY 迁移死信流并 ACK（镜像原型 nack）。

    :return: 当前重试计数（1..MAX_RETRY）；>= MAX_RETRY 表示已入死信。
    """
    retry_key = f"{RETRY_KEY_PREFIX}{stream_msg_id}"
    retry_count = int(await redis_client.incr(retry_key))
    await redis_client.expire(retry_key, RETRY_KEY_TTL)
    if retry_count >= MAX_RETRY:
        original = await redis_client.xrange(stream, min=stream_msg_id, max=stream_msg_id)
        if original:
            await redis_client.xadd(f"{stream}{DLQ_SUFFIX}", original[0][1], maxlen=STREAM_MAXLEN)
        await redis_client.xack(stream, group, stream_msg_id)
        await publish_audit(
            {
                "trace_id": trace_id or stream_msg_id,
                "auditor": "a2a-protocol",
                "action": "dead_letter",
                "detail": {
                    "stream": stream,
                    "stream_msg_id": stream_msg_id,
                    "retry_count": retry_count,
                    "reason": reason[:500],
                },
                "timestamp": int(time.time() * 1000),
            }
        )
        logger.warning(
            "[a2a] 消息 %s 重试 %d 次失败，已迁移死信流 %s:dlq",
            stream_msg_id,
            retry_count,
            stream,
        )
    return retry_count


async def claim_stale_messages(
    stream: str,
    group: str,
    consumer: str,
    min_idle_ms: int,
    start_id: str = "0-0",
    count: int = 10,
) -> List[tuple]:
    """XAUTOCLAIM 挂起回收：已投递未 ACK 且空闲超阈值的消息转投当前消费者。

    兜底消费端宕机场景（消息滞留 PEL 无人认领），返回 [(stream_msg_id, 信封)]。
    """
    claimed = await redis_client.xautoclaim(
        stream,
        group,
        consumer,
        min_idle_time=min_idle_ms,
        start_id=start_id,
        count=count,
    )
    entries = (
        claimed[1] if claimed and len(claimed) >= 2 else []
    )  # 兼容 2/3 元响应（服务端版本差异）
    return [(stream_msg_id, parse_message(fields)) for stream_msg_id, fields in entries]


# -------------------------- 内置编队注册 + 心跳循环 --------------------------

_registry_task: Optional[asyncio.Task] = None


def _a2a_enabled() -> bool:
    return os.getenv("A2A_ENABLED", "true").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


async def _registry_loop() -> None:
    """内置编队注册+心跳循环：幂等 HSET（30s 周期，兼具注册自愈与心跳保活）。"""
    logger.info("[a2a] 内置编队注册/心跳循环已启动（周期 %ds）", _HEARTBEAT_INTERVAL)
    while True:
        try:
            for card in BUILTIN_AGENTS:
                await _registry_register(card)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # Redis 未就绪等基础设施抖动：告警退避而非崩溃
            logger.warning("[a2a] 内置编队注册/心跳失败（30s 后重试）：%s", exc)
        await asyncio.sleep(_HEARTBEAT_INTERVAL)


def start_registry() -> None:
    """A2A 启动：审计 sink 注入智云守护 + 内置编队注册/心跳循环（幂等；A2A_ENABLED=false 跳过）。"""
    global _registry_task
    if not _a2a_enabled() or _registry_task is not None:
        return
    from core.agents import set_audit_sink

    set_audit_sink(make_threadsafe_audit_sink())
    _registry_task = asyncio.create_task(_registry_loop())


async def stop_registry() -> None:
    global _registry_task
    if _registry_task is not None:
        _registry_task.cancel()
        try:
            await _registry_task
        except asyncio.CancelledError:
            pass
        _registry_task = None
