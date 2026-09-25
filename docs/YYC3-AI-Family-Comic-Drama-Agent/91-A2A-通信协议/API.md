# 91 A2A 通信协议 接口文档

> 版本 v1.0.0 | 更新 2026-09-24 | 代码 [a2a_protocol.py](a2a_protocol.py)
> 示例前提：Redis 已部署（节点2，AOF持久化挂载NAS RAID1）；环境变量 `REDIS_HOST/PORT/PASSWORD`

## 一、接口清单

| 接口名称 | 签名 | 功能简述 |
| -------- | ---- | -------- |
| `build_message` | `(trace_id, msg_type, sender, receiver, task_type, payload, priority=5, ttl=300) -> dict` | 构建标准A2A消息 |
| `parse_message` | `(message_data) -> dict` | 解析消息（payload反序列化） |
| `AgentRegistry.register` | `(agent_card) -> None` | 注册身份卡片 |
| `AgentRegistry.heartbeat` | `(agent_id) -> None` | 心跳更新 |
| `AgentRegistry.get_online_agents` | `() -> list` | 在线Agent列表 |
| `AgentRegistry.get_agent_by_capability` | `(capability) -> list` | 按能力发现Agent |
| `MessageProducer.send_task` | `(stream_name, message) -> str` | 发送任务（自动写审计流） |
| `MessageProducer.send_result` | `(message) -> str` | 结果回调 |
| `MessageProducer.broadcast` | `(event_type, payload) -> None` | 系统广播 |
| `MessageConsumer.poll` | `(count=1, block=5000) -> list` | 拉取消息 |
| `MessageConsumer.ack / nack` | `(msg_id[, reason]) -> None` | 确认 / 重试与死信 |
| `A2ABaseAgent.start / stop` | `() -> None` | 启停异步服务 |
| `A2ABaseAgent.handle_task` | `(task_type, payload, trace_id) -> dict` | 业务处理（子类重写） |
| `AsyncOrchestrator.submit_multi_agent_task` | `(trace_id, task_plan) -> str` | 提交多Agent任务 |
| `AsyncOrchestrator.get_task_status` | `(trace_id) -> dict` | 查询状态与结果 |

## 二、核心接口详情

### 2.1 `build_message` / `parse_message`

**功能描述**：构建/解析标准消息（msg_id 自动生成雪花式ID，payload JSON序列化）。

**关键参数**：见签名；`msg_type` 取值 `task_request/task_result/heartbeat/system_event/error`；`priority` 0-9 默认5。

**调用示例**：

```python
from a2a_protocol import build_message, parse_message

msg = build_message(trace_id="trace-20260924-0001", msg_type="task_request",
                    sender="yuanqi-tianshu-001", receiver="yushu-wanwu-001",
                    task_type="data_analysis",
                    payload={"query": "分析Q2营收", "knowledge": []})
restored = parse_message(dict(msg, payload=msg["payload"]))
# 预期：msg["msg_id"] 形如 msg-1790340000000-a1b2c3d4；restored["payload"] 为 dict
```

### 2.2 `AgentRegistry` — 注册与发现

**调用示例**：

```python
from a2a_protocol import AgentRegistry

AgentRegistry.register({
    "agent_id": "yushu-wanwu-001", "agent_name": "语枢·万物",
    "role": "思考者·数据分析", "layer": "business",
    "capabilities": ["data_analysis", "logic_reasoning"],
    "endpoint": "stream:agent:request:yushu", "status": "online",
})
# 预期控制台：[注册中心] Agent 语枢·万物(yushu-wanwu-001) 注册成功

AgentRegistry.heartbeat("yushu-wanwu-001")            # 30秒/次保活
online = AgentRegistry.get_online_agents()            # 90秒超时判定
target = AgentRegistry.get_agent_by_capability("data_analysis")
# 预期：target[0]["agent_id"] == "yushu-wanwu-001"
```

### 2.3 `MessageProducer` / `MessageConsumer`

**功能描述**：生产者发送任务并同步写审计流（`stream:audit:log`，智云守护落盘NAS）；消费者组阻塞拉取 + ACK 确认；失败重试3次后移入死信流 `{stream}:dlq`。

**调用示例**：

```python
from a2a_protocol import MessageProducer, MessageConsumer

# 发送任务
mid = MessageProducer.send_task("stream:agent:request:yushu", msg)
# 预期返回：消息ID，且 stream:audit:log 同步新增一条 action=send_task 记录

# 消费端（Agent Worker 内部）
consumer = MessageConsumer("stream:agent:request:yushu",
                           "group-yushu-wanwu-001", "consumer-yushu-01")
for m in consumer.poll(count=1, block=5000):
    # ... 处理消息 ...
    consumer.ack(m["stream_msg_id"])       # 成功确认
    # 失败时：consumer.nack(m["stream_msg_id"], reason)  # 3次后入死信队列
```

### 2.4 `A2ABaseAgent` — 异步 Agent 服务

**功能描述**：start 后自动启动心跳线程（30秒/次）与任务监听线程；子类实现 `handle_task` 即可接入调度；成功回发 `task_result`，异常回发 `error`（retryable=true）并 nack 重试。

**调用示例（自定义 Worker）**：

```python
from a2a_protocol import A2ABaseAgent

class YuShuWorker(A2ABaseAgent):
    def handle_task(self, task_type, payload, trace_id):
        # 调用业务Agent能力（如 YuShuWanWuAgent.analyze）
        return {"analysis_result": f"已分析：{payload.get('query', '')}"}

worker = YuShuWorker(
    agent_id="yushu-wanwu-001", agent_name="语枢·万物",
    role="思考者·数据分析", capabilities=["data_analysis"],
    stream_name="stream:agent:request:yushu")
worker.start()   # 预期控制台：[语枢·万物] A2A Agent 启动完成
# worker.stop()
```

### 2.5 `AsyncOrchestrator` — 异步编排引擎

**请求参数（submit_multi_agent_task）**：

| 参数名 | 类型 | 必填 | 描述 |
| ------ | ---- | ---- | ---- |
| trace_id | str | 是 | 全链路追踪ID |
| task_plan | list[dict] | 是 | 元素含 `agent_capability`（路由能力标签）/ `task_type` / `payload` / `priority`（选填） |

**返回参数（get_task_status）**：

| 参数名 | 类型 | 描述 |
| ------ | ---- | ---- |
| status | str | running/completed/timeout/not_found（超TTL 300秒→timeout） |
| progress | str | 形如 `2/3` |
| results | dict | 键为 sender agent_id |

**错误码**：YYC3-AGT-5101（无在线Agent提供目标能力，抛异常）；YYC3-AGT-4001（task_plan 为空）

**调用示例**：

```python
import time, json
from a2a_protocol import AsyncOrchestrator

orch = AsyncOrchestrator(); orch.start()
tid = orch.submit_multi_agent_task("trace-20260924-0001", task_plan=[{
    "agent_capability": "data_analysis", "task_type": "data_analysis",
    "payload": {"query": "分析Q2经营数据核心指标",
                "knowledge": ["Q2营收同比增长32%"]}}])

while True:
    st = orch.get_task_status(tid)
    print(st["status"], st["progress"])          # 预期：running 0/1 → completed 1/1
    if st["status"] in ("completed", "timeout", "failed"):
        print(json.dumps(st["results"], ensure_ascii=False, indent=2))
        break
    time.sleep(2)
```

---

*© 2025-2026 YYC³ Team. All Rights Reserved.*
