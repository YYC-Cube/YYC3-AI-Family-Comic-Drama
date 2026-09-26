# file: agent_workers.py
# description: 业务 Agent 外置 Worker（Phase 2 A2A Worker 化）——语枢/预见/创想独立进程消费任务流
# author: YanYuCloudCube Team <admin@0379.email>
# created: 2026-09-26
# status: active
# tags: [a2a],[worker],[redis-stream],[agent]

"""业务 Agent 外置 Worker（源：可行性报告 Phase 2「A2A Worker 化」+ 原型 A2ABaseAgent）。

职责：
- 消费 stream:agent:task:{agent_id}（消费者组 group-{agent_id}，XREADGROUP ">"）
- task_type → 业务 Agent 方法分发（语枢 analyze / 预见 forecast·qualitative / 创想 polish·brainstorm）
- 成功：XACK + 结果回执（stream:agent:result:callback）+ 审计；失败：nack（3 次重试 → DLQ）

工程化改造（相对原型）：
- 同步 threading 轮询 → asyncio 异步循环（与网关协议层共用异步客户端，单一事件循环并发多 Agent）
- LLM 调用经 BaseAgent.run（未配 LLM_BASE_URL 自动 Mock 降级；调用失败同降级，五高-高可用）
- Agent 实例懒加载 + 按 agent_id 复用（本进程单实例，无并发竞争）
"""

import asyncio
import logging
import os
import socket
import time
from typing import Any, Callable, Dict, List, Optional

from app.services import a2a_protocol as proto
from core.agents import (
    ChuangXiangLingYunAgent,
    GeWuZongShiAgent,
    YanQiQianHangAgent,
    YuJianXianZhiAgent,
    YuShuWanWuAgent,
)

logger = logging.getLogger(__name__)

# 外置 Worker 化 Agent 编队（可行性报告 Phase 2 首批 3 + 扩面 2：格物·宗师 / 演启·乾行）
WORKER_AGENT_IDS = [
    "yushu-wanwu-001",
    "yujian-xianzhi-001",
    "chuangxiang-lingyun-001",
    "gewu-zongshi-001",
    "yanqi-qianhang-001",
]

# agent_id → 业务 Agent 实例工厂（懒实例化，本进程内复用）
AGENT_FACTORIES: Dict[str, Callable[[], object]] = {
    "yushu-wanwu-001": YuShuWanWuAgent,
    "yujian-xianzhi-001": YuJianXianZhiAgent,
    "chuangxiang-lingyun-001": ChuangXiangLingYunAgent,
    "gewu-zongshi-001": GeWuZongShiAgent,
    "yanqi-qianhang-001": YanQiQianHangAgent,
}

_instances: Dict[str, object] = {}


def _get_agent(agent_id: str) -> Any:
    """获取（或懒创建）本进程内复用的业务 Agent 实例（方法集各异，动态分发）。"""
    if agent_id not in _instances:
        factory = AGENT_FACTORIES.get(agent_id)
        if factory is None:
            raise KeyError(f"未注册的外置 Worker Agent：{agent_id}")
        _instances[agent_id] = factory()
    return _instances[agent_id]


def _context(payload: dict) -> list:
    """RAG 知识上下文（payload.knowledge_context，缺省空列表）。"""
    kc = payload.get("knowledge_context") or []
    return kc if isinstance(kc, list) else []


def handle_task(task_type: str, payload: dict) -> dict:
    """task_type → 业务方法分发（纯函数，测试直接驱动）。

    payload 契约：input 为文本主输入；其余参数按方法签名可选透传；
    knowledge_context 为 RAG 片段列表。返回 {"output": ...}（str/list/dict 原样）。
    未知 task_type 抛 ValueError（触发 nack → 重试 → DLQ 链路）。
    """
    if not isinstance(payload, dict) or not str(payload.get("input") or "").strip():
        raise ValueError("payload.input 为必填的文本主输入")

    if task_type == "data_analysis":  # 语枢·万物：四段式数据分析
        return {
            "output": _get_agent("yushu-wanwu-001").analyze(payload["input"], _context(payload))
        }
    if task_type == "trend_forecast":  # 预见·先知：定量+情景+解读完整预测
        result = _get_agent("yujian-xianzhi-001").full_forecast(
            metric_name=str(payload.get("metric_name") or "指标"),
            historical_data=list(payload.get("historical_data") or []),
            periods=int(payload.get("periods") or 3),
            scenario=str(payload.get("scenario") or "基准"),
            knowledge_context=_context(payload),
        )
        return {"output": result}
    if task_type == "qualitative_analysis":  # 预见·先知：定性趋势研判
        return {
            "output": _get_agent("yujian-xianzhi-001").qualitative_analysis(
                payload["input"], _context(payload)
            )
        }
    if task_type == "report_polish":  # 创想·灵韵：报告润色
        return {
            "output": _get_agent("chuangxiang-lingyun-001").polish_report(
                payload["input"],
                style=str(payload.get("style") or "商务正式"),
                audience=str(payload.get("audience") or "管理层"),
                knowledge_context=_context(payload),
            )
        }
    if task_type == "creative_brainstorm":  # 创想·灵韵：创意发散
        return {
            "output": _get_agent("chuangxiang-lingyun-001").brainstorm_ideas(
                payload["input"],
                direction_count=int(payload.get("direction_count") or 3),
                industry=str(payload.get("industry") or "科技行业"),
                knowledge_context=_context(payload),
            )
        }
    if task_type == "content_validation":  # 格物·宗师：内容校验（事实/合规/风格三维）
        return {
            "output": _get_agent("gewu-zongshi-001").validate(
                payload["input"], knowledge_context=_context(payload)
            )
        }
    if task_type == "code_review":  # 格物·宗师：代码评审
        return {
            "output": _get_agent("gewu-zongshi-001").review_code(
                payload["input"], language=str(payload.get("language") or "python")
            )
        }
    if task_type == "content_formatting":  # 演启·乾行：结构化输出格式化（置信度+风险提示）
        return {
            "output": _get_agent("yanqi-qianhang-001").format_output(
                payload["input"],
                confidence=float(payload.get("confidence") or 0.0),
                risk_notes=str(payload.get("risk_notes") or ""),
            )
        }
    raise ValueError(f"未知 task_type：{task_type}")


def _consumer_name(agent_id: str) -> str:
    """消费者名：env 指定优先，缺省 hostname-pid（多进程部署不串投递记录）。"""
    custom = os.getenv("A2A_WORKER_CONSUMER", "").strip()
    return f"consumer-{agent_id}-{custom or f'{socket.gethostname()}-{os.getpid()}'}"


async def _announce_external_runner(agent_id: str) -> None:
    """外置执行位上报：合并注册卡片，endpoint 覆盖为自身消费流（能力发现可见）。"""
    base = next((c for c in proto.BUILTIN_AGENTS if c["agent_id"] == agent_id), None)
    if base is None:
        logger.warning(
            "[a2a-worker] %s 非内置编队成员，跳过执行位上报（需经 /v1/admin/a2a 注册）", agent_id
        )
        return
    card = dict(base)
    card["endpoint"] = proto.task_stream(agent_id)
    card["runner"] = "external-worker"
    await proto._registry_register(card)


class AgentWorker:
    """单 Agent 任务消费者（异步循环；多 Agent 经 asyncio.gather 并发）。"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.stream = proto.task_stream(agent_id)
        self.group = f"group-{agent_id}"
        self.consumer = _consumer_name(agent_id)

    async def _on_success(self, stream_msg_id: str, msg: dict, result: dict) -> None:
        await proto.send_result_message(
            proto.build_message(
                trace_id=msg["trace_id"],
                msg_type="task_result",
                sender=self.agent_id,
                receiver=msg.get("sender", "gateway"),
                task_type=msg.get("task_type", ""),
                payload={"success": True, "data": result},
            )
        )
        await proto.ack_message(self.stream, self.group, stream_msg_id)
        await proto.publish_audit(
            {
                "trace_id": msg["trace_id"],
                "auditor": self.agent_id,
                "action": "task_result",
                "detail": {"stream_msg_id": stream_msg_id, "success": True},
                "timestamp": int(time.time() * 1000),
            }
        )

    async def _on_failure(self, stream_msg_id: str, msg: dict, error: Exception) -> None:
        retry_count = await proto.nack_message(
            self.stream, self.group, stream_msg_id, str(error), trace_id=msg.get("trace_id", "")
        )
        await proto.send_result_message(
            proto.build_message(
                trace_id=msg["trace_id"],
                msg_type="error",
                sender=self.agent_id,
                receiver=msg.get("sender", "gateway"),
                task_type=msg.get("task_type", ""),
                payload={
                    "success": False,
                    "error": str(error),
                    "retryable": retry_count < proto.MAX_RETRY,
                },
            )
        )
        await proto.publish_audit(
            {
                "trace_id": msg.get("trace_id") or stream_msg_id,
                "auditor": self.agent_id,
                "action": "task_retry" if retry_count < proto.MAX_RETRY else "task_dead",
                "detail": {
                    "stream_msg_id": stream_msg_id,
                    "retry_count": retry_count,
                    "error": str(error)[:500],
                },
                "timestamp": int(time.time() * 1000),
            }
        )

    async def run_once(self) -> int:
        """消费一轮：poll → handle → ack/nack。返回处理条数（供测试与探活）。"""
        messages = await proto.poll_messages(self.stream, self.group, self.consumer, count=1)
        for stream_msg_id, msg in messages:
            try:
                result = handle_task(msg.get("task_type", ""), msg.get("payload") or {})
                await self._on_success(stream_msg_id, msg, result)
                logger.info("[a2a-worker:%s] 任务 %s 完成", self.agent_id, msg.get("trace_id"))
            except Exception as exc:
                logger.warning(
                    "[a2a-worker:%s] 任务 %s 失败：%s", self.agent_id, msg.get("trace_id"), exc
                )
                await self._on_failure(stream_msg_id, msg, exc)
        return len(messages)

    async def run_forever(self) -> None:
        """主循环：确保消费者组 → 外置执行位上报 → 持续消费（基础设施抖动退避重试）。"""
        await proto.ensure_group(self.stream, self.group)
        try:
            await _announce_external_runner(self.agent_id)
        except Exception as exc:  # 注册中心抖动不阻断消费主链路
            logger.warning("[a2a-worker:%s] 执行位上报失败（不阻断）：%s", self.agent_id, exc)
        logger.info(
            "[a2a-worker:%s] 启动消费 stream=%s group=%s consumer=%s",
            self.agent_id,
            self.stream,
            self.group,
            self.consumer,
        )
        while True:
            try:
                processed = await self.run_once()
                if not processed:
                    await asyncio.sleep(0.5)  # 空轮询间隙，避免忙等
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # Redis 抖动等：退避而非崩溃（五高-高可用）
                logger.warning("[a2a-worker:%s] 消费异常，1s 退避重试：%s", self.agent_id, exc)
                await asyncio.sleep(1.0)


def worker_agent_ids() -> List[str]:
    """待启动 Agent 清单：A2A_WORKER_AGENTS env 优先，缺省首批 3 Agent。"""
    raw = os.getenv("A2A_WORKER_AGENTS", "").strip()
    if not raw:
        return list(WORKER_AGENT_IDS)
    return [x.strip() for x in raw.split(",") if x.strip()]


async def run_workers(agent_ids: Optional[List[str]] = None) -> None:
    """并发运行多个 Agent Worker（独立进程入口调用；任一取消则整体收敛）。"""
    ids = agent_ids or worker_agent_ids()
    workers = [AgentWorker(agent_id).run_forever() for agent_id in ids]
    if not workers:
        logger.warning("[a2a-worker] 无可运行 Agent（检查 A2A_WORKER_AGENTS）")
        return
    await asyncio.gather(*workers)
