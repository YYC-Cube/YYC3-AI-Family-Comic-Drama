# ==============================================================
# A2A 通信协议 + Redis Stream 消息队列核心实现 v1.0
# 对齐架构：A2A Agent协作协议 + 事件驱动解耦 + Agent Card自动发现
# 能力：注册中心 / 心跳保活 / 异步任务分发 / 结果聚合 / 死信队列
# 依赖：pip install redis python-dotenv
# ==============================================================
import os
import json
import time
import uuid
import threading
from dotenv import load_dotenv
import redis

load_dotenv()

# -------------------------- 全局配置 --------------------------
REDIS_HOST = os.getenv("REDIS_HOST", "10.0.0.12")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

AGENT_REGISTRY_KEY = "a2a:agent:registry"   # 注册中心Key
HEARTBEAT_TIMEOUT = 90                       # 心跳超时（秒）
DEFAULT_TTL = 300                            # 默认消息超时（秒）
MAX_RETRY = 3                                # 最大重试次数


def get_redis_client() -> redis.Redis:
    """获取Redis连接"""
    return redis.Redis(
        host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD,
        decode_responses=True, socket_keepalive=True,
    )


redis_client = get_redis_client()


# -------------------------- 消息工具 --------------------------
def generate_msg_id() -> str:
    return f"msg-{int(time.time()*1000)}-{uuid.uuid4().hex[:8]}"


def build_message(trace_id: str, msg_type: str, sender: str, receiver: str,
                  task_type: str, payload: dict,
                  priority: int = 5, ttl: int = DEFAULT_TTL) -> dict:
    """构建标准A2A消息（格式规范见 README 第四节）"""
    return {
        "msg_id": generate_msg_id(),
        "trace_id": trace_id,
        "msg_type": msg_type,
        "sender": sender,
        "receiver": receiver,
        "task_type": task_type,
        "payload": json.dumps(payload, ensure_ascii=False),
        "priority": priority,
        "timestamp": int(time.time()*1000),
        "ttl": ttl,
    }


def parse_message(message_data: dict) -> dict:
    """解析消息，反序列化payload"""
    msg = dict(message_data)
    if isinstance(msg.get("payload"), str):
        try:
            msg["payload"] = json.loads(msg["payload"])
        except Exception:
            pass
    return msg


# -------------------------- Agent 注册中心 --------------------------
class AgentRegistry:
    """Agent注册中心：身份卡片、心跳、在线状态、能力发现"""

    @staticmethod
    def register(agent_card: dict):
        agent_card["register_time"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        agent_card["last_heartbeat"] = time.time()
        redis_client.hset(AGENT_REGISTRY_KEY, agent_card["agent_id"],
                          json.dumps(agent_card, ensure_ascii=False))
        print(f"[注册中心] Agent {agent_card['agent_name']}({agent_card['agent_id']}) 注册成功")

    @staticmethod
    def heartbeat(agent_id: str):
        raw = redis_client.hget(AGENT_REGISTRY_KEY, agent_id)
        if not raw:
            return
        card = json.loads(raw)
        card["last_heartbeat"] = time.time()
        card["status"] = "online"
        redis_client.hset(AGENT_REGISTRY_KEY, agent_id,
                          json.dumps(card, ensure_ascii=False))

    @staticmethod
    def get_online_agents() -> list:
        all_agents = redis_client.hgetall(AGENT_REGISTRY_KEY)
        online, now = [], time.time()
        for raw_card in all_agents.values():
            card = json.loads(raw_card)
            card["status"] = "online" if now - card["last_heartbeat"] < HEARTBEAT_TIMEOUT else "offline"
            if card["status"] == "online":
                online.append(card)
        return online

    @staticmethod
    def get_agent_by_capability(capability: str) -> list:
        return [a for a in AgentRegistry.get_online_agents()
                if capability in a.get("capabilities", [])]


# -------------------------- 消息生产者 --------------------------
class MessageProducer:
    """发送任务、回调结果、广播事件（同步写入审计流）"""

    @staticmethod
    def send_task(stream_name: str, message: dict) -> str:
        msg_id = redis_client.xadd(stream_name, message)
        redis_client.xadd("stream:audit:log", {  # 异步审计（智云守护消费落盘NAS）
            "trace_id": message["trace_id"], "action": "send_task",
            "stream": stream_name, "msg_id": msg_id,
            "sender": message["sender"], "receiver": message["receiver"],
            "timestamp": message["timestamp"],
        })
        return msg_id

    @staticmethod
    def send_result(message: dict) -> str:
        return MessageProducer.send_task("stream:agent:result:callback", message)

    @staticmethod
    def broadcast(event_type: str, payload: dict):
        msg = build_message(trace_id=f"sys-{int(time.time())}",
                            msg_type="system_event", sender="system",
                            receiver="all", task_type=event_type, payload=payload)
        MessageProducer.send_task("stream:system:broadcast", msg)


# -------------------------- 消息消费者 --------------------------
class MessageConsumer:
    """阻塞监听任务队列：消费者组 + ACK确认 + 死信队列"""

    def __init__(self, stream_name: str, group_name: str, consumer_name: str):
        self.stream_name = stream_name
        self.group_name = group_name
        self.consumer_name = consumer_name
        self._ensure_group()

    def _ensure_group(self):
        try:
            redis_client.xgroup_create(self.stream_name, self.group_name,
                                       id="0", mkstream=True)
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

    def poll(self, count: int = 1, block: int = 5000) -> list:
        messages = redis_client.xreadgroup(
            groupname=self.group_name, consumername=self.consumer_name,
            streams={self.stream_name: ">"}, count=count, block=block,
        )
        if not messages:
            return []
        parsed = []
        for _, msg_list in messages:
            for msg_id, msg_data in msg_list:
                msg = parse_message(msg_data)
                msg["stream_msg_id"] = msg_id
                parsed.append(msg)
        return parsed

    def ack(self, msg_id: str):
        redis_client.xack(self.stream_name, self.group_name, msg_id)

    def nack(self, msg_id: str, reason: str = ""):
        """失败重试：超3次移入死信流 {stream}:dlq"""
        retry_key = f"a2a:retry:{msg_id}"
        retry_count = redis_client.incr(retry_key)
        redis_client.expire(retry_key, 3600)
        if retry_count >= MAX_RETRY:
            msg = redis_client.xrange(self.stream_name, msg_id, msg_id)[0]
            redis_client.xadd(f"{self.stream_name}:dlq", msg[1])
            self.ack(msg_id)
            print(f"[死信队列] 消息 {msg_id} 重试{MAX_RETRY}次失败，移入死信队列")


# -------------------------- A2A Agent 基类 --------------------------
class A2ABaseAgent:
    """A2A增强Agent基类：自动注册、心跳保活、异步任务监听、结果回调

    使用：业务Agent组合本类或继承（内嵌业务 BaseAgent 实例），
    子类实现 handle_task 即可接入异步调度体系。
    """

    def __init__(self, agent_id: str, agent_name: str, role: str,
                 capabilities: list, stream_name: str, base_agent=None):
        self.agent_id = agent_id
        self.name = agent_name
        self.role = role
        self.capabilities = capabilities
        self.stream_name = stream_name
        self.business = base_agent          # 业务能力载体（BaseAgent子类实例）
        self.group_name = f"group-{agent_id}"
        self.consumer_name = f"consumer-{agent_id}-01"
        self.running = False
        self.consumer = MessageConsumer(stream_name, self.group_name, self.consumer_name)
        self._register_self()

    def _register_self(self):
        AgentRegistry.register({
            "agent_id": self.agent_id, "agent_name": self.name, "role": self.role,
            "layer": "business", "capabilities": self.capabilities,
            "endpoint": self.stream_name, "status": "online",
        })

    def _heartbeat_loop(self):
        while self.running:
            AgentRegistry.heartbeat(self.agent_id)
            time.sleep(30)

    def handle_task(self, task_type: str, payload: dict, trace_id: str) -> dict:
        """业务任务处理，子类重写；返回结果作为回调payload"""
        raise NotImplementedError("子类必须实现handle_task方法")

    def _task_loop(self):
        print(f"[{self.name}] 启动任务监听，队列：{self.stream_name}")
        while self.running:
            try:
                for msg in self.consumer.poll(count=1, block=5000):
                    trace_id, task_type = msg["trace_id"], msg["task_type"]
                    print(f"[{self.name}] 收到任务 trace_id={trace_id} type={task_type}")
                    try:
                        result = self.handle_task(task_type, msg["payload"], trace_id)
                        MessageProducer.send_result(build_message(
                            trace_id=trace_id, msg_type="task_result",
                            sender=self.agent_id, receiver=msg["sender"],
                            task_type=task_type,
                            payload={"success": True, "data": result}))
                        self.consumer.ack(msg["stream_msg_id"])
                    except Exception as e:
                        MessageProducer.send_result(build_message(
                            trace_id=trace_id, msg_type="error",
                            sender=self.agent_id, receiver=msg["sender"],
                            task_type=task_type,
                            payload={"success": False, "error": str(e), "retryable": True}))
                        self.consumer.nack(msg["stream_msg_id"], str(e))
            except Exception as e:
                print(f"[{self.name}] 任务监听异常：{e}")
                time.sleep(1)

    def start(self):
        self.running = True
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()
        threading.Thread(target=self._task_loop, daemon=True).start()
        print(f"[{self.name}] A2A Agent 启动完成")

    def stop(self):
        self.running = False
        print(f"[{self.name}] A2A Agent 已停止")


# -------------------------- 异步编排引擎（元启天枢调度核心） --------------------------
class AsyncOrchestrator:
    """多Agent并行任务分发、结果聚合、超时控制、全链路追踪"""

    def __init__(self):
        self.pending_tasks = {}     # trace_id -> 任务状态
        self.result_collector = {}  # trace_id -> 结果集合
        self.running = False
        self.result_consumer = MessageConsumer(
            "stream:agent:result:callback", "group-orchestrator",
            "consumer-orchestrator-01")

    def submit_multi_agent_task(self, trace_id: str, task_plan: list) -> str:
        """提交多Agent协同任务

        :param task_plan: [{"agent_capability", "task_type", "payload", "priority"}, ...]
        """
        self.pending_tasks[trace_id] = {
            "total": len(task_plan), "completed": 0, "failed": 0,
            "status": "running", "create_time": time.time(),
        }
        self.result_collector[trace_id] = {}

        for task in task_plan:
            agents = AgentRegistry.get_agent_by_capability(task["agent_capability"])
            if not agents:
                raise Exception(f"没有可用的Agent提供能力：{task['agent_capability']}")
            target = agents[0]
            MessageProducer.send_task(target["endpoint"], build_message(
                trace_id=trace_id, msg_type="task_request",
                sender="yuanqi-tianshu-001", receiver=target["agent_id"],
                task_type=task["task_type"], payload=task["payload"],
                priority=task.get("priority", 5)))

        print(f"[编排引擎] 任务 {trace_id} 已分发，共{len(task_plan)}个子任务")
        return trace_id

    def _result_listen_loop(self):
        while self.running:
            try:
                for msg in self.result_consumer.poll(count=10, block=2000):
                    trace_id = msg["trace_id"]
                    if trace_id not in self.pending_tasks:
                        self.result_consumer.ack(msg["stream_msg_id"])
                        continue
                    self.result_collector[trace_id][msg["sender"]] = msg["payload"]
                    task = self.pending_tasks[trace_id]
                    if msg["msg_type"] == "task_result":
                        task["completed"] += 1
                    elif msg["msg_type"] == "error":
                        task["failed"] += 1
                    if task["completed"] + task["failed"] >= task["total"]:
                        task["status"] = "completed"
                        task["finish_time"] = time.time()
                    self.result_consumer.ack(msg["stream_msg_id"])
            except Exception as e:
                print(f"[编排引擎] 结果监听异常：{e}")
                time.sleep(0.5)

    def get_task_status(self, trace_id: str) -> dict:
        task = self.pending_tasks.get(trace_id)
        if not task:
            return {"status": "not_found"}
        if task["status"] == "running" and time.time() - task["create_time"] > DEFAULT_TTL:
            task["status"] = "timeout"
        return {
            "status": task["status"],
            "progress": f"{task['completed']+task['failed']}/{task['total']}",
            "results": self.result_collector.get(trace_id, {}),
        }

    def start(self):
        self.running = True
        threading.Thread(target=self._result_listen_loop, daemon=True).start()
        print("[编排引擎] 异步调度引擎启动成功")

    def stop(self):
        self.running = False


# -------------------------- 全链路异步运行示例 --------------------------
if __name__ == "__main__":
    # 1. 启动业务Agent Worker（实际部署时每个Agent独立进程/容器）
    #    worker = A2ABaseAgent("yushu-wanwu-001", "语枢·万物", "思考者·数据分析",
    #                          ["data_analysis"], "stream:agent:request:yushu")
    #    worker.start()

    # 2. 启动异步编排引擎
    orchestrator = AsyncOrchestrator()
    orchestrator.start()

    # 3. 提交多Agent协同任务
    trace_id = "trace-20260924-0001"
    orchestrator.submit_multi_agent_task(trace_id, task_plan=[{
        "agent_capability": "data_analysis",
        "task_type": "data_analysis",
        "payload": {"query": "分析Q2经营数据核心指标",
                    "knowledge": ["Q2营收同比增长32%", "云业务占比65%"]},
    }])

    # 4. 轮询任务状态
    while True:
        status = orchestrator.get_task_status(trace_id)
        print(f"任务状态：{status['status']}，进度：{status['progress']}")
        if status["status"] in ("completed", "timeout", "failed"):
            print("最终结果：", json.dumps(status["results"], ensure_ascii=False, indent=2))
            break
        time.sleep(2)
