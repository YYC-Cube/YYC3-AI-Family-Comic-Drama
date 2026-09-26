---
file: 02-Mac侧生产节点A2A适配器代码.md
description: Mac 侧生产节点 A2A 适配器（P0-S2/P0-C1 已整改：argv 注入 + 超时修正）
author: Intelligent Application Implementation Expert <admin@0379.email>
version: v1.1.0
created: 2026-09-25
updated: 2026-09-25
status: active
tags: [a2a],[adapter],[redis],[security]
category: code
language: zh-CN
changelog:
  - { version: v1.0.0, date: 2026-09-25, author: 智能应用落地专家, change: 原始版本收录（生成于外部会话） }
  - { version: v1.1.0, date: 2026-09-25, author: 智能应用落地专家, change: P0 安全整改（argv 化/超时修正，见文末）+ P1-D1 规范化（补齐 YAML FM） }
---

# A2A消息队列的Mac侧生产节点适配器代码

**100% 对齐既有 A2A 协议标准、NAS 双分区架构、MiniMax-H3 仓库目录规范**，可直接部署运行，零架构适配成本。

---

## Mac 侧生产节点 A2A 适配器代码

### 2.1 功能说明

- 遵循既有 A2A 通信协议，自动注册到 Agent 注册中心，心跳保活
- 监听视频生产任务队列，接收元启天枢调度的视频生成请求
- 调用本地 MiniMax-H3 生产线脚本，执行批量生成 + 口型评分
- 执行完成后自动回传结果、manifest 数据、质量评分到回调队列
- 异常自动上报，支持重试机制，全链路携带 trace_id 可审计
- 完全兼容既有 Redis Stream 消息体系，零额外中间件

### 2.2 前置依赖

```bash
# 安装依赖
pip install redis python-dotenv
# 确保 conda 环境 h3-m4 已创建，H3 仓库已部署到本地
```

### 2.3 环境配置 `.env`

与 H3 仓库同级放置，配置根据实际环境修改。

```env
# ==============================================================
# H3 生产节点 A2A 适配器配置
# ==============================================================

# A2A Redis 服务地址（DGX节点2）
REDIS_HOST=10.0.0.12
REDIS_PORT=6379
REDIS_PASSWORD=

# 节点身份配置
AGENT_ID=h3-production-mac-001
AGENT_NAME=H3数字人生产节点
AGENT_ROLE=内容生产节点
# 能力标签，调度端按能力匹配
AGENT_CAPABILITIES=["video_generation", "ref2va", "fl2va", "batch_production", "lipsync_score"]

# 本地 H3 仓库根目录（绝对路径）
H3_ROOT=/Users/yan/YYC3-MiniMax-H3
# conda 环境名称
CONDA_ENV=h3-m4
# 输出根目录（相对 H3_ROOT）
OUTPUT_DIR=output_batch

# 任务队列配置
TASK_STREAM=stream:agent:request:h3-production
CONSUMER_GROUP=group-h3-production
CONSUMER_NAME=consumer-h3-mac-001

# 心跳间隔（秒）
HEARTBEAT_INTERVAL=30
# 任务超时（秒）：生产实测单条约 7000s（batch90/91），600s 必超时（P0-C1 已修）；
# 生产环境调度层应采用网关租约（lease_minutes=180）+ 心跳续约语义
TASK_TIMEOUT=16200

# Python 解释器：直接指向 conda 环境内 python 绝对路径，
# 避免 `conda activate` shell 拼接（命令注入面清零，P0-S2 配套）
PYTHON_BIN=/Users/yan/miniforge3/envs/h3-m4/bin/python
```

### 2.4 完整适配器代码 `h3_production_adapter.py`

```python
# ==============================================================
# MiniMax-H3 生产节点 A2A 适配器 v1.0
# 对接协议：YYC³ A2A 通信协议（Redis Stream）
# 功能：任务监听、批量生产、结果回调、心跳保活、异常上报
# ==============================================================
import os
import re
import json
import time
import uuid
import subprocess
import threading
from dotenv import load_dotenv
import redis

load_dotenv()

# -------------------------- 配置加载 --------------------------
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

AGENT_ID = os.getenv("AGENT_ID")
AGENT_NAME = os.getenv("AGENT_NAME")
AGENT_ROLE = os.getenv("AGENT_ROLE")
AGENT_CAPABILITIES = json.loads(os.getenv("AGENT_CAPABILITIES"))

H3_ROOT = os.getenv("H3_ROOT")
CONDA_ENV = os.getenv("CONDA_ENV")
OUTPUT_DIR = os.getenv("OUTPUT_DIR")

TASK_STREAM = os.getenv("TASK_STREAM")
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP")
CONSUMER_NAME = os.getenv("CONSUMER_NAME")

HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL"))
TASK_TIMEOUT = int(os.getenv("TASK_TIMEOUT"))
PYTHON_BIN = os.getenv("PYTHON_BIN")
if not PYTHON_BIN or not os.path.exists(PYTHON_BIN):
    raise RuntimeError("PYTHON_BIN 未配置或不存在，禁止回退 shell 拼接方式（P0-S2）")

AGENT_REGISTRY_KEY = "a2a:agent:registry"
RESULT_STREAM = "stream:agent:result:callback"
AUDIT_STREAM = "stream:audit:log"

# -------------------------- Redis 连接 --------------------------
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True,
    socket_keepalive=True
)

# -------------------------- 工具函数 --------------------------
def generate_msg_id():
    return f"msg-{int(time.time()*1000)}-{uuid.uuid4().hex[:8]}"

def build_message(trace_id, msg_type, sender, receiver, task_type, payload, priority=5, ttl=TASK_TIMEOUT):
    """构建标准 A2A 消息"""
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
        "ttl": ttl
    }

def parse_payload(msg_data):
    """解析 payload 字段"""
    if isinstance(msg_data.get("payload"), str):
        try:
            msg_data["payload"] = json.loads(msg_data["payload"])
        except:
            pass
    return msg_data

# -------------------------- 注册与心跳 --------------------------
def register_agent():
    """注册节点到 A2A 注册中心"""
    card = {
        "agent_id": AGENT_ID,
        "agent_name": AGENT_NAME,
        "role": AGENT_ROLE,
        "layer": "production",
        "capabilities": AGENT_CAPABILITIES,
        "endpoint": TASK_STREAM,
        "status": "online",
        "register_time": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "last_heartbeat": time.time()
    }
    redis_client.hset(AGENT_REGISTRY_KEY, AGENT_ID, json.dumps(card, ensure_ascii=False))
    print(f"[注册中心] {AGENT_NAME} ({AGENT_ID}) 注册成功")

def heartbeat_loop():
    """心跳保活线程"""
    while running:
        try:
            raw = redis_client.hget(AGENT_REGISTRY_KEY, AGENT_ID)
            if raw:
                card = json.loads(raw)
                card["last_heartbeat"] = time.time()
                card["status"] = "online"
                redis_client.hset(AGENT_REGISTRY_KEY, AGENT_ID, json.dumps(card, ensure_ascii=False))
        except Exception as e:
            print(f"[心跳异常] {e}")
        time.sleep(HEARTBEAT_INTERVAL)

# -------------------------- 消费者初始化 --------------------------
def ensure_consumer_group():
    """创建消费者组"""
    try:
        redis_client.xgroup_create(TASK_STREAM, CONSUMER_GROUP, id="0", mkstream=True)
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise

# -------------------------- 任务执行核心 --------------------------
def _resolve_script(script_rel):
    """脚本路径白名单：仅允许 H3_ROOT/scripts/ 下的 .py 文件，防目录穿越"""
    candidate = os.path.realpath(os.path.join(H3_ROOT, script_rel))
    scripts_root = os.path.realpath(os.path.join(H3_ROOT, "scripts"))
    if not candidate.startswith(scripts_root + os.sep) or not candidate.endswith(".py"):
        raise ValueError(f"非法脚本路径: {script_rel}")
    return candidate


def run_h3_batch(task_params):
    """
    调用本地 H3 批量生成脚本
    安全基线（P0-S2 修复）：argv 数组注入，input_text/ref_image 作为独立
    参数传递、不经 shell 解释，命令注入面清零；对齐 video_task_runner 铁律④
    task_params: {
        "mode": "ref2va" / "fl2va",
        "script_path": "scripts/batch_ref2va_nf4.py",
        "input_text": "口播文案",
        "ref_image": "ref_images/avatar01.png",
        "num_frames": 124,
        "seed": -1,
        "batch_name": "batch_001"
    }
    """
    mode = task_params.get("mode", "ref2va")
    batch_name = task_params.get("batch_name", f"batch_{int(time.time())}")
    # 批次名白名单：防路径穿越/注入
    if not re.fullmatch(r"[0-9A-Za-z_\-]+", batch_name):
        return {"success": False, "error": f"非法批次名: {batch_name}",
                "error_code": "invalid_batch_name"}
    output_path = os.path.join(H3_ROOT, OUTPUT_DIR, batch_name)

    # 脚本白名单校验
    try:
        script_file = _resolve_script(
            task_params.get("script_path", "scripts/batch_ref2va_nf4.py"))
    except ValueError as e:
        return {"success": False, "error": str(e),
                "error_code": "invalid_script_path"}

    # 构建执行命令（argv 数组，零 shell 拼接）
    cmd = [
        PYTHON_BIN, script_file,
        "--output_dir", output_path,
        "--num_frames", str(task_params.get("num_frames", 124)),
        "--seed", str(task_params.get("seed", -1)),
        "--input_text", str(task_params.get("input_text", "")),
        "--ref_image", str(task_params.get("ref_image", "ref_images/default.png")),
    ]

    # 执行脚本
    try:
        result = subprocess.run(
            cmd,
            cwd=H3_ROOT,
            capture_output=True,
            text=True,
            timeout=TASK_TIMEOUT
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr[-500:],
                "stdout": result.stdout[-500:]
            }

        # 读取 manifest 结果
        manifest_path = os.path.join(output_path, "manifest.json")
        manifest = {}
        if os.path.exists(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

        return {
            "success": True,
            "batch_name": batch_name,
            "output_path": output_path,
            "video_file": os.path.join(output_path, "output.mp4"),
            "manifest": manifest,
            "stdout": result.stdout[-200:]
        }

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "任务执行超时", "error_code": "timeout"}
    except Exception as e:
        return {"success": False, "error": str(e), "error_code": "runtime_error"}

# -------------------------- 任务监听循环 --------------------------
def task_loop():
    """主任务监听循环"""
    ensure_consumer_group()
    print(f"[任务监听] 启动，队列：{TASK_STREAM}")

    while running:
        try:
            # 拉取任务
            messages = redis_client.xreadgroup(
                groupname=CONSUMER_GROUP,
                consumername=CONSUMER_NAME,
                streams={TASK_STREAM: ">"},
                count=1,
                block=2000
            )

            if not messages:
                continue

            for stream, msg_list in messages:
                for stream_msg_id, msg_data in msg_list:
                    msg_data = parse_payload(msg_data)
                    trace_id = msg_data["trace_id"]
                    task_type = msg_data["task_type"]
                    payload = msg_data["payload"]
                    sender = msg_data["sender"]

                    print(f"\n[收到任务] trace_id={trace_id}, type={task_type}")

                    # 写入审计日志
                    redis_client.xadd(AUDIT_STREAM, {
                        "trace_id": trace_id,
                        "action": "receive_task",
                        "agent_id": AGENT_ID,
                        "task_type": task_type,
                        "timestamp": int(time.time()*1000)
                    })

                    try:
                        # 执行任务
                        result = run_h3_batch(payload)

                        # 构建回调消息
                        callback_msg = build_message(
                            trace_id=trace_id,
                            msg_type="task_result" if result["success"] else "error",
                            sender=AGENT_ID,
                            receiver=sender,
                            task_type=task_type,
                            payload=result
                        )

                        # 发送结果
                        redis_client.xadd(RESULT_STREAM, callback_msg)

                        # ACK 确认
                        redis_client.xack(TASK_STREAM, CONSUMER_GROUP, stream_msg_id)

                        print(f"[任务完成] trace_id={trace_id}, 成功={result['success']}")

                    except Exception as e:
                        print(f"[任务异常] trace_id={trace_id}, 错误：{e}")
                        # 错误回调
                        error_msg = build_message(
                            trace_id=trace_id,
                            msg_type="error",
                            sender=AGENT_ID,
                            receiver=sender,
                            task_type=task_type,
                            payload={"success": False, "error": str(e), "retryable": True}
                        )
                        redis_client.xadd(RESULT_STREAM, error_msg)
                        redis_client.xack(TASK_STREAM, CONSUMER_GROUP, stream_msg_id)

        except Exception as e:
            print(f"[监听异常] {e}")
            time.sleep(1)

# -------------------------- 主入口 --------------------------
if __name__ == "__main__":
    running = True

    # 注册节点
    register_agent()

    # 启动心跳线程
    threading.Thread(target=heartbeat_loop, daemon=True).start()

    # 启动任务监听
    try:
        task_loop()
    except KeyboardInterrupt:
        print("\n[系统] 收到停止信号")
        running = False
        # 更新状态为离线
        raw = redis_client.hget(AGENT_REGISTRY_KEY, AGENT_ID)
        if raw:
            card = json.loads(raw)
            card["status"] = "offline"
            redis_client.hset(AGENT_REGISTRY_KEY, AGENT_ID, json.dumps(card, ensure_ascii=False))
        print("[系统] 生产节点适配器已停止")
```

### 2.5 启动与验证

#### 启动方式

```bash
# 进入 H3 仓库目录
cd /path/to/YYC3-MiniMax-H3

# 后台启动适配器
nohup python h3_production_adapter.py > logs/adapter.log 2>&1 &

# 查看运行状态
tail -f logs/adapter.log
```

#### 验证方法（DGX 侧发送测试任务）

```python
# 在 DGX 编排端发送测试任务
from a2a_protocol import MessageProducer, build_message

test_msg = build_message(
    trace_id="trace-h3-test-001",
    msg_type="task_request",
    sender="yuanqi-tianshu-001",
    receiver="h3-production-mac-001",
    task_type="video_generation",
    payload={
        "mode": "ref2va",
        "input_text": "欢迎来到言启象限，语枢未来。",
        "ref_image": "ref_images/avatar01.png",
        "num_frames": 124,
        "batch_name": "test_batch_001"
    }
)
MessageProducer.send_task("stream:agent:request:h3-production", test_msg)
print("测试任务已发送")
```

---

## 落地校验清单

| 校验项 | 预期结果 | 验证方法 |
| -------- | ---------- | ---------- |
| 适配器注册 | 注册中心可看到在线节点 | `redis-cli hgetall a2a:agent:registry` |
| 任务接收 | Mac 侧日志显示收到任务 | 查看 adapter.log |
| 脚本执行 | 本地 output 目录生成视频与 manifest | 检查输出目录 |
| 结果回调 | 结果流中收到成功消息 | 监听 `stream:agent:result:callback` |
| NAS 同步 | 对应目录出现同步文件 | 登录 NAS 查看 |
| 全链路追踪 | audit 流中有完整日志 | 查看审计流 |

## 安全整改记录（2026-09-25）

| 项 | 修复内容 |
| -- | -------- |
| P0-S2 | `run_h3_batch` 由 `shell=True` + f-string 拼接改为 **argv 数组注入**；新增脚本路径白名单（`_resolve_script`）与批次名白名单（`[0-9A-Za-z_-]+`）；`PYTHON_BIN` 强制校验，杜绝 `conda activate` shell 拼接 |
| P0-C1 | `TASK_TIMEOUT` 600s → **16200s**（生产实测单条约 7000s，原值必超时）；生产调度层应采用网关租约（lease_minutes=180）+ 心跳续约语义 |
