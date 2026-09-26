# ==============================================================
# YYC³ MiniMax-H3 多Agent 框架 · A2A 协议层 v1.0
# @file agent/h3_agent/protocol.py
# @author Intelligent Application Implementation Expert <admin@0379.email>
# @version v1.0.0
# @created 2026-09-26
# @status stable
#
# 对齐：YYC3-AI-Family-Comic-Drama-Agent/91-A2A-通信协议（消息 9 字段逐一同名，
#       注册中心/心跳/消费者组/ACK/NACK/死信/审计全对齐），差异点：
#   1. 传输抽象化：RedisTransport（生产）+ InMemoryTransport（离线演示/测试），
#      高可用降级——Redis 不可达时自动回落 InMemory 并告警（永不断流）
#   2. 全链路审计经 AuditLog 双写本地 JSONL（NAS 同步）
#   3. 结果回调流常量集中管理，与编排引擎共享
# 依赖：redis（可选；未安装或不可达时自动 InMemory 模式）
# ==============================================================
import importlib
import json
import threading
import time
import uuid

from . import config
from .security import AuditLog

# ---------------- 流常量（与参照设计同名） ----------------
STREAM_RESULT_CALLBACK = "stream:agent:result:callback"
STREAM_AUDIT_LOG = "stream:audit:log"
STREAM_SYSTEM_BROADCAST = "stream:system:broadcast"

AUDIT = AuditLog()


def generate_msg_id() -> str:
    return f"msg-{int(time.time() * 1000)}-{uuid.uuid4().hex[:8]}"


def build_message(trace_id: str, msg_type: str, sender: str, receiver: str,
                  task_type: str, payload: dict,
                  priority: int = 5, ttl: int = config.DEFAULT_TTL) -> dict:
    """构建标准 A2A 消息（9 字段，与漫剧项目 a2a_protocol.build_message 逐字段一致）"""
    return {
        "msg_id": generate_msg_id(),
        "trace_id": trace_id,
        "msg_type": msg_type,        # task_request | task_result | error | system_event
        "sender": sender,
        "receiver": receiver,
        "task_type": task_type,
        "payload": json.dumps(payload, ensure_ascii=False),
        "priority": priority,
        "timestamp": int(time.time() * 1000),
        "ttl": ttl,
    }


def parse_message(message_data: dict) -> dict:
    """解析消息，payload 反序列化"""
    msg = dict(message_data)
    if isinstance(msg.get("payload"), str):
        try:
            msg["payload"] = json.loads(msg["payload"])
        except (json.JSONDecodeError, TypeError):
            pass
    return msg


# ==============================================================
# 传输抽象：Stream（消息队列）+ KV（注册中心）两组语义
# ==============================================================
class BaseTransport:
    """传输抽象：生产实现为 Redis Streams；测试/演示实现为内存队列"""

    # ---- Stream 语义 ----
    def xadd(self, stream: str, fields: dict, msg_id: str | None = None) -> str:
        raise NotImplementedError

    def xrange_one(self, stream: str, msg_id: str) -> dict | None:
        raise NotImplementedError

    def xreadgroup(self, stream: str, group: str, consumer: str,
                   count: int, block_ms: int) -> list[tuple[str, dict]]:
        raise NotImplementedError

    def xack(self, stream: str, group: str, msg_id: str):
        raise NotImplementedError

    def ensure_group(self, stream: str, group: str):
        raise NotImplementedError

    # ---- KV/Hash 语义（注册中心） ----
    def hset(self, key: str, field: str, value: str):
        raise NotImplementedError

    def hget(self, key: str, field: str) -> str | None:
        raise NotImplementedError

    def hgetall(self, key: str) -> dict[str, str]:
        raise NotImplementedError

    def incr(self, key: str) -> int:
        raise NotImplementedError

    def expire(self, key: str, ttl: int):
        raise NotImplementedError


class RedisTransport(BaseTransport):
    """Redis Streams 传输（生产模式）：消费者组 + ACK + 死信 + 审计"""

    def __init__(self):
        # 动态导入（可选依赖）：Pylance 不做静态解析，未安装时抛 ImportError
        # → get_transport() 捕获后降级 InMemory（高可用设计不变）
        redis = importlib.import_module("redis")
        self.client = redis.Redis(
            host=config.REDIS_HOST, port=config.REDIS_PORT,
            password=config.REDIS_PASSWORD or None,
            decode_responses=True, socket_keepalive=True)

    def xadd(self, stream, fields, msg_id=None):
        return str(self.client.xadd(stream, fields, id=msg_id or "*"))

    def xrange_one(self, stream, msg_id):
        rows = self.client.xrange(stream, min=msg_id, max=msg_id)
        return rows[0][1] if rows else None

    def xreadgroup(self, stream, group, consumer, count, block_ms):
        rows = self.client.xreadgroup(
            groupname=group, consumername=consumer,
            streams={stream: ">"}, count=count, block=block_ms)
        out = []
        for _, msg_list in rows:
            out.extend(msg_list)
        return out

    def xack(self, stream, group, msg_id):
        self.client.xack(stream, group, msg_id)

    def ensure_group(self, stream, group):
        try:
            self.client.xgroup_create(stream, group, id="0", mkstream=True)
        except Exception as e:
            if "BUSYGROUP" not in str(e):
                raise

    def hset(self, key, field, value):
        self.client.hset(key, field, value)

    def hget(self, key, field):
        return self.client.hget(key, field)

    def hgetall(self, key):
        return self.client.hgetall(key)

    def incr(self, key):
        return int(self.client.incr(key))

    def expire(self, key, ttl):
        self.client.expire(key, ttl)


class InMemoryTransport(BaseTransport):
    """内存传输（离线演示/单测/Redis 不可达降级）：语义与 Redis 实现一致"""

    def __init__(self):
        self._streams: dict[str, list[tuple[str, dict]]] = {}
        self._groups: dict[str, set[str]] = {}
        self._pending: dict[tuple[str, str], list] = {}   # (stream, group) -> 待消费
        self._acked: dict[tuple[str, str], set] = {}
        self._kv: dict[str, dict[str, str]] = {}
        self._counters: dict[str, int] = {}
        self._lock = threading.Lock()

    def xadd(self, stream, fields, msg_id=None):
        with self._lock:
            mid = msg_id or f"{int(time.time() * 1000)}-{uuid.uuid4().hex[:8]}"
            self._streams.setdefault(stream, []).append((mid, dict(fields)))
            # 新消息推送至该流所有已建组的待读队列（对齐 Redis ">" 新消息语义）
            for (s, g), queue in self._pending.items():
                if s == stream and mid not in self._acked.setdefault((s, g), set()):
                    queue.append((mid, dict(fields)))
            return mid

    def xrange_one(self, stream, msg_id):
        for mid, fields in self._streams.get(stream, []):
            if mid == msg_id:
                return fields
        return None

    def xreadgroup(self, stream, group, consumer, count, block_ms):
        with self._lock:
            key = (stream, group)
            self._acked.setdefault(key, set())
            queue = self._pending.setdefault(key, [])
            out = []
            while queue and len(out) < count:
                mid, fields = queue.pop(0)
                if mid in self._acked[key]:
                    continue
                out.append((mid, fields))
            return out

    def xack(self, stream, group, msg_id):
        with self._lock:
            self._acked.setdefault((stream, group), set()).add(msg_id)

    def ensure_group(self, stream, group):
        with self._lock:
            self._groups.setdefault(stream, set()).add(group)
            self._pending.setdefault((stream, group), [])
            self._acked.setdefault((stream, group), set())
            # 已有历史消息纳入组待读（对齐 Redis id="0" 语义）
            self._pending[(stream, group)].extend(
                (m, f) for m, f in self._streams.get(stream, []))

    def hset(self, key, field, value):
        with self._lock:
            self._kv.setdefault(key, {})[field] = value

    def hget(self, key, field):
        return self._kv.get(key, {}).get(field)

    def hgetall(self, key):
        return dict(self._kv.get(key, {}))

    def incr(self, key):
        with self._lock:
            self._counters[key] = self._counters.get(key, 0) + 1
            return self._counters[key]

    def expire(self, key, ttl):  # 内存实现无 TTL，保留接口一致性
        return None


_transport: BaseTransport | None = None
_transport_mode: str = ""


def get_transport() -> tuple[BaseTransport, str]:
    """获取全局传输：优先 Redis，连接失败/未安装自动降级 InMemory（高可用）"""
    global _transport, _transport_mode
    if _transport is not None:
        return _transport, _transport_mode
    try:
        rt = RedisTransport()
        rt.client.ping()
        _transport, _transport_mode = rt, "redis"
    except Exception as e:
        print(f"[A2A] Redis 不可达（{e}），降级 InMemory 模式（单进程演示/测试）")
        _transport, _transport_mode = InMemoryTransport(), "inmemory"
    return _transport, _transport_mode


# ==============================================================
# 注册中心 / 生产者 / 消费者（与参照设计同名同类）
# ==============================================================
class AgentRegistry:
    """Agent 注册中心：身份卡片、心跳、在线状态、能力发现（Hash 存储）"""

    @staticmethod
    def register(agent_card: dict, transport: BaseTransport | None = None):
        t = transport or get_transport()[0]
        card = dict(agent_card)
        card["register_time"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        card["last_heartbeat"] = time.time()
        t.hset(config.AGENT_REGISTRY_KEY, card["agent_id"],
               json.dumps(card, ensure_ascii=False))
        print(f"[注册中心] Agent {card['agent_name']}({card['agent_id']}) 注册成功")

    @staticmethod
    def heartbeat(agent_id: str, transport: BaseTransport | None = None):
        t = transport or get_transport()[0]
        raw = t.hget(config.AGENT_REGISTRY_KEY, agent_id)
        if not raw:
            return
        card = json.loads(raw)
        card["last_heartbeat"] = time.time()
        card["status"] = "online"
        t.hset(config.AGENT_REGISTRY_KEY, agent_id,
               json.dumps(card, ensure_ascii=False))

    @staticmethod
    def get_online_agents(transport: BaseTransport | None = None) -> list[dict]:
        t = transport or get_transport()[0]
        online, now = [], time.time()
        for raw_card in t.hgetall(config.AGENT_REGISTRY_KEY).values():
            card = json.loads(raw_card)
            card["status"] = ("online" if now - card["last_heartbeat"]
                              < config.HEARTBEAT_TIMEOUT else "offline")
            if card["status"] == "online":
                online.append(card)
        return online

    @staticmethod
    def get_agent_by_capability(capability: str,
                                transport: BaseTransport | None = None) -> list[dict]:
        return [a for a in AgentRegistry.get_online_agents(transport)
                if capability in a.get("capabilities", [])]


class MessageProducer:
    """消息生产者：任务分发 / 结果回调 / 广播，同步双写审计流 + 本地 JSONL"""

    @staticmethod
    def send_task(stream_name: str, message: dict,
                  transport: BaseTransport | None = None) -> str:
        t = transport or get_transport()[0]
        msg_id = t.xadd(stream_name, message)
        t.xadd(STREAM_AUDIT_LOG, {
            "trace_id": message["trace_id"], "action": "send_task",
            "stream": stream_name, "msg_id": msg_id,
            "sender": message["sender"], "receiver": message["receiver"],
            "timestamp": message["timestamp"]})
        AUDIT.emit("send_task", trace_id=message["trace_id"],
                   stream=stream_name, msg_id=msg_id,
                   sender=message["sender"], receiver=message["receiver"],
                   task_type=message["task_type"])
        return msg_id

    @staticmethod
    def send_result(message: dict, transport: BaseTransport | None = None) -> str:
        return MessageProducer.send_task(STREAM_RESULT_CALLBACK, message, transport)

    @staticmethod
    def broadcast(event_type: str, payload: dict,
                  transport: BaseTransport | None = None):
        msg = build_message(trace_id=f"sys-{int(time.time())}",
                            msg_type="system_event", sender="system",
                            receiver="all", task_type=event_type, payload=payload)
        MessageProducer.send_task(STREAM_SYSTEM_BROADCAST, msg, transport)


class MessageConsumer:
    """消息消费者：消费者组 + ACK + NACK 重试 + 死信队列（{stream}:dlq）"""

    def __init__(self, stream_name: str, group_name: str, consumer_name: str,
                 transport: BaseTransport | None = None):
        self.stream_name = stream_name
        self.group_name = group_name
        self.consumer_name = consumer_name
        self.transport = transport or get_transport()[0]
        self.transport.ensure_group(stream_name, group_name)

    def poll(self, count: int = 1, block_ms: int = 1000) -> list[dict]:
        rows = self.transport.xreadgroup(
            self.stream_name, self.group_name, self.consumer_name, count, block_ms)
        parsed = []
        for msg_id, fields in rows:
            msg = parse_message(fields)
            msg["stream_msg_id"] = msg_id
            parsed.append(msg)
        return parsed

    def ack(self, msg_id: str):
        self.transport.xack(self.stream_name, self.group_name, msg_id)

    def nack(self, msg_id: str, reason: str = ""):
        """失败重试：超 MAX_RETRY 次移入死信流并 ACK（防无限重投）"""
        t = self.transport
        retry_key = f"a2a:retry:{msg_id}"
        retry_count = t.incr(retry_key)
        t.expire(retry_key, 3600)
        if retry_count >= config.MAX_RETRY:
            raw = t.xrange_one(self.stream_name, msg_id)
            if raw:
                t.xadd(f"{self.stream_name}:dlq", raw)
            self.ack(msg_id)
            AUDIT.emit("dlq", msg_id=msg_id, reason=reason, retries=retry_count)
            print(f"[死信队列] {msg_id} 重试{retry_count}次失败，移入死信队列（{reason}）")
