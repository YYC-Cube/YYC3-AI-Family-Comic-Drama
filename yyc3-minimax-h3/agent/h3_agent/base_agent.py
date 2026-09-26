# ==============================================================
# YYC³ MiniMax-H3 多Agent 框架 · Agent 基类 v1.0
# @file agent/h3_agent/base_agent.py
# @author Intelligent Application Implementation Expert <admin@0379.email>
# @version v1.0.0
# @created 2026-09-26
# @status stable
#
# 对齐：91-A2A/a2a_protocol.A2ABaseAgent（注册/心跳/任务循环/结果回调全同构），
#       叠加本仓库铁律：handle_task 前强制 claim 校验 + 载荷白名单校验（fail-closed）
# 使用：子类实现 _handle_task()（已过安全校验），基类负责全部协议事务
# ==============================================================
import threading
import time

from . import config
from .protocol import (AgentRegistry, MessageConsumer, MessageProducer,
                       build_message, get_transport)
from .security import validate_task_payload, verify_claim


class H3BaseAgent:
    """H3 A2A Agent 基类：自动注册、心跳保活、异步任务监听、结果回调

    与参照设计的差异：任务入口增加两道安全闸（可配置关闭，仅限离线演示）：
      1. claim 校验：消息 payload.claim 必须为有效 HMAC 令牌
      2. 载荷校验：security.validate_task_payload 白名单静态检查
    """

    def __init__(self, agent_id: str, agent_name: str, role: str,
                 capabilities: list[str], stream_name: str,
                 transport=None, enforce_claim: bool = True):
        self.agent_id = agent_id
        self.name = agent_name
        self.role = role
        self.capabilities = capabilities
        self.stream_name = stream_name
        self.enforce_claim = enforce_claim
        self.transport, self.mode = (
            (transport, "injected") if transport else get_transport())
        self.group_name = f"group-{agent_id}"
        self.consumer_name = f"consumer-{agent_id}-01"
        self.running = False
        self.consumer = MessageConsumer(
            stream_name, self.group_name, self.consumer_name, self.transport)
        AgentRegistry.register(self._agent_card(), self.transport)

    def _agent_card(self) -> dict:
        return {"agent_id": self.agent_id, "agent_name": self.name,
                "role": self.role, "layer": "business",
                "capabilities": self.capabilities,
                "endpoint": self.stream_name, "status": "online"}

    # ---------------- 子类实现 ----------------
    def _handle_task(self, task_type: str, payload: dict, trace_id: str) -> dict:
        """业务任务处理（已过安全闸）；返回值作为 task_result.payload.data"""
        raise NotImplementedError("子类必须实现 _handle_task")

    # ---------------- 安全闸 ----------------
    def _security_gates(self, msg: dict):
        """claim 校验 + 载荷白名单校验；违规抛 PermissionError/ValueError"""
        payload = msg.get("payload") or {}
        if self.enforce_claim and self.mode != "injected":
            claim = payload.get("claim")
            if not verify_claim(claim if isinstance(claim, dict) else {}):
                raise PermissionError(f"claim 缺失或无效（trace={msg.get('trace_id')}）")
        errors = validate_task_payload(msg.get("task_type", ""), payload)
        if errors:
            raise ValueError("载荷校验失败：" + "; ".join(errors))

    # ---------------- 协议循环 ----------------
    def _heartbeat_loop(self):
        while self.running:
            AgentRegistry.heartbeat(self.agent_id, self.transport)
            time.sleep(config.HEARTBEAT_INTERVAL)

    def _task_loop(self):
        print(f"[{self.name}] 启动任务监听，队列：{self.stream_name}（传输：{self.mode}）")
        while self.running:
            try:
                for msg in self.consumer.poll(count=1, block_ms=1000):
                    trace_id, task_type = msg["trace_id"], msg["task_type"]
                    print(f"[{self.name}] 收到任务 trace={trace_id} type={task_type}")
                    try:
                        self._security_gates(msg)
                        result = self._handle_task(task_type, msg["payload"], trace_id)
                        MessageProducer.send_result(build_message(
                            trace_id=trace_id, msg_type="task_result",
                            sender=self.agent_id, receiver=msg["sender"],
                            task_type=task_type,
                            payload={"success": True, "data": result}),
                            self.transport)
                        self.consumer.ack(msg["stream_msg_id"])
                    except Exception as e:
                        retryable = not isinstance(e, (PermissionError, ValueError))
                        MessageProducer.send_result(build_message(
                            trace_id=trace_id, msg_type="error",
                            sender=self.agent_id, receiver=msg["sender"],
                            task_type=task_type,
                            payload={"success": False, "error": str(e),
                                     "retryable": retryable}),
                            self.transport)
                        if retryable:
                            self.consumer.nack(msg["stream_msg_id"], str(e))
                        else:
                            self.consumer.ack(msg["stream_msg_id"])  # 安全违规不重投
            except Exception as e:
                print(f"[{self.name}] 任务监听异常：{e}")
                time.sleep(1)

    def start(self):
        self.running = True
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()
        threading.Thread(target=self._task_loop, daemon=True).start()
        print(f"[{self.name}] A2A Agent 启动完成（{self.mode}）")

    def stop(self):
        self.running = False
        print(f"[{self.name}] A2A Agent 已停止")

    def handle_direct(self, task_type: str, payload: dict,
                      trace_id: str = "") -> dict:
        """直连调用（绕过队列，供编排引擎进程内调度/测试使用；安全闸仍生效）"""
        msg = {"trace_id": trace_id or f"direct-{int(time.time()*1000)}",
               "task_type": task_type, "payload": payload,
               "sender": "orchestrator", "msg_id": "direct"}
        self._security_gates(msg)
        return self._handle_task(task_type, payload, msg["trace_id"])
