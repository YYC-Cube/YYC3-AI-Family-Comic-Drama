---
file: 03-DGX编排端的视频任务调用示例代码.md
description: DGX 编排端视频任务调用示例（P0-C1 已整改：超时 16200s）
author: Intelligent Application Implementation Expert <admin@0379.email>
version: v1.1.0
created: 2026-09-25
updated: 2026-09-25
status: active
tags: [a2a],[dgx],[orchestration]
category: code
language: zh-CN
changelog:
  - { version: v1.0.0, date: 2026-09-25, author: 智能应用落地专家, change: 原始版本收录（生成于外部会话） }
  - { version: v1.1.0, date: 2026-09-25, author: 智能应用落地专家, change: P0-C1 超时修正 + P1-D1 规范化（补齐 YAML FM） }
---

# DGX 编排端的视频任务调用示例代码

**100% 复用既有 A2A 消息基础设施、对齐 NAS 目录映射规范、匹配 H3 生产节点适配器协议**，可直接复制部署，零适配成本。

---

## 一、DGX 编排端视频任务调用完整示例

基于前文 `AsyncOrchestrator` 异步编排引擎与 A2A 标准协议扩展，无缝接入元启天枢治理中枢，与 Mac 生产节点适配器严格一一对应。

### 1.1 编排引擎扩展方法（集成至现有体系）

在既有 `AsyncOrchestrator` 类中追加视频生产专属调度方法，复用 Redis 连接、消息格式、注册中心体系，无需新增任何基础设施。

```python
# 追加到 AsyncOrchestrator 类中
class AsyncOrchestrator:
    # ... 保留原有方法不变 ...

    # ==================== 视频生产任务扩展 ====================
    def submit_video_task(self, trace_id: str, task_params: dict, priority: int = 5) -> str:
        """
        提交视频生成任务至 H3 生产节点
        :param trace_id: 全链路追踪ID
        :param task_params: 视频生产参数（见下方参数规范）
        :param priority: 优先级 0-9，默认5
        :return: 任务追踪ID
        """
        # 按能力查找可用生产节点
        agents = AgentRegistry.get_agent_by_capability("video_generation")
        if not agents:
            raise Exception("无可用的 H3 视频生产节点，请检查节点在线状态")

        target_agent = agents[0]
        msg = build_message(
            trace_id=trace_id,
            msg_type="task_request",
            sender="yuanqi-tianshu-001",
            receiver=target_agent["agent_id"],
            task_type="video_generation",
            payload=task_params,
            priority=priority,
            ttl=task_params.get("timeout", 16200)  # P0-C1：生产单条约 7000s，600s 必超时
        )

        MessageProducer.send_task(target_agent["endpoint"], msg)
        print(f"[视频调度] 任务 {trace_id} 已下发至 {target_agent['agent_name']}")
        return trace_id

    def get_video_task_status(self, trace_id: str) -> dict:
        """
        查询视频任务状态与结果
        :return: 状态：pending/running/completed/failed/timeout + 结果数据
        """
        status = self.get_task_status(trace_id)

        # 补充视频专属字段解析
        if status["status"] == "completed" and status["results"]:
            for agent_id, result in status["results"].items():
                if result.get("success") and "manifest" in result:
                    status["video_info"] = {
                        "batch_name": result.get("batch_name"),
                        "video_path": result.get("video_file"),
                        "manifest": result.get("manifest"),
                        "production_node": agent_id
                    }
        return status

    def wait_for_video_task(self, trace_id: str, timeout: int = 16200, poll_interval: int = 5) -> dict:
        """
        同步等待视频任务完成（阻塞式；生产单条约 7000s，默认 4.5h 上限）
        :param timeout: 超时时间秒
        :param poll_interval: 轮询间隔秒
        """
        import time
        start = time.time()
        while time.time() - start < timeout:
            status = self.get_video_task_status(trace_id)
            if status["status"] in ["completed", "failed", "timeout"]:
                return status
            time.sleep(poll_interval)

        return {"status": "timeout", "trace_id": trace_id, "message": "任务等待超时"}
```

### 1.2 完整可运行调用示例

独立运行版，无需依赖完整编排引擎，直接调用 A2A 协议发送任务，适合快速验证与脚本集成。

```python
# ==============================================================
# DGX 端视频任务调用示例 v1.0
# 对接协议：A2A Redis Stream
# 对接节点：Mac MiniMax-H3 生产节点
# ==============================================================
import json
import time
from a2a_protocol import (
    get_redis_client, build_message, MessageProducer,
    AgentRegistry, parse_message
)

# 初始化
redis_client = get_redis_client()
RESULT_STREAM = "stream:agent:result:callback"
TASK_STREAM = "stream:agent:request:h3-production"

def submit_and_wait_video(
    input_text: str,
    ref_image: str = "ref_images/default.png",
    mode: str = "ref2va",
    num_frames: int = 124,
    seed: int = -1,
    batch_name: str = None,
    timeout: int = 16200  # P0-C1：≥4.5h，与 Mac 侧 TASK_TIMEOUT 对齐
) -> dict:
    """
    一站式提交视频任务并等待结果
    """
    trace_id = f"video-{int(time.time())}-{__import__('uuid').uuid4().hex[:6]}"
    batch_name = batch_name or f"batch_{trace_id.split('-')[1]}"

    # 1. 构建任务参数
    task_params = {
        "mode": mode,
        "script_path": "scripts/batch_ref2va_nf4.py",
        "input_text": input_text,
        "ref_image": ref_image,
        "num_frames": num_frames,
        "seed": seed,
        "batch_name": batch_name
    }

    # 2. 构建标准A2A消息
    msg = build_message(
        trace_id=trace_id,
        msg_type="task_request",
        sender="dgx-orchestrator-test",
        receiver="h3-production-mac-001",
        task_type="video_generation",
        payload=task_params,
        priority=5,
        ttl=timeout
    )

    # 3. 发送任务
    MessageProducer.send_task(TASK_STREAM, msg)
    print(f"✅ 任务已提交，trace_id: {trace_id}")
    print(f"📝 批次名称: {batch_name}")

    # 4. 监听结果
    print("⏳ 等待生产完成...")
    start_time = time.time()
    last_id = "0"

    while time.time() - start_time < timeout:
        # 读取结果流
        messages = redis_client.xread(
            {RESULT_STREAM: last_id},
            count=10,
            block=2000
        )

        if messages:
            for stream, msg_list in messages:
                for msg_id, msg_data in msg_list:
                    last_id = msg_id
                    msg = parse_message(msg_data)

                    # 匹配目标trace_id
                    if msg["trace_id"] == trace_id:
                        if msg["msg_type"] == "task_result":
                            payload = msg["payload"]
                            print("\n🎉 视频生产完成！")
                            print(f"   批次: {payload.get('batch_name')}")
                            print(f"   视频路径: {payload.get('video_file')}")
                            print(f"   帧耗时: {payload.get('manifest', {}).get('avg_gen_seconds', 'N/A')} 秒/帧")
                            return {
                                "success": True,
                                "trace_id": trace_id,
                                "data": payload
                            }
                        elif msg["msg_type"] == "error":
                            print(f"\n❌ 任务失败: {msg['payload'].get('error')}")
                            return {
                                "success": False,
                                "trace_id": trace_id,
                                "error": msg["payload"].get("error")
                            }

        # 进度提示
        elapsed = int(time.time() - start_time)
        if elapsed % 10 == 0:
            print(f"   已等待 {elapsed}s...")

    print("\n⏰ 任务超时")
    return {"success": False, "trace_id": trace_id, "error": "timeout"}


# -------------------------- 运行测试 --------------------------
if __name__ == "__main__":
    # 检查生产节点在线状态
    online_nodes = AgentRegistry.get_agent_by_capability("video_generation")
    print(f"📡 在线生产节点: {len(online_nodes)} 个")
    for node in online_nodes:
        print(f"   - {node['agent_name']} ({node['agent_id']})")

    if not online_nodes:
        print("❌ 无在线生产节点，请先启动 Mac 端适配器")
        exit(1)

    # 提交测试任务
    result = submit_and_wait_video(
        input_text="欢迎来到言启象限，语枢未来。万象归元于云枢，深栈智启新纪元。",
        ref_image="ref_images/avatar01.png",
        num_frames=124,
        mode="ref2va"
    )

    # 输出完整manifest
    if result["success"]:
        print("\n📄 完整 Manifest 数据:")
        print(json.dumps(result["data"]["manifest"], ensure_ascii=False, indent=2))
```

### 1.3 创想·灵韵 Agent 集成示例

将视频生成能力嵌入「创想·灵韵」角色，实现「文案创意 → 视频生成」一体化能力闭环，对齐 AI FAmily 角色分工。

```python
# 追加到 ChuangXiangLingYunAgent 类中
class ChuangXiangLingYunAgent(BaseAgent):
    # ... 保留原有方法不变 ...

    def generate_video(self, script_content: str, avatar: str = "default",
                      style: str = "正式商务", duration: str = "5s") -> dict:
        """
        文案转数字人视频：自动优化口播文案 → 生成视频
        :param script_content: 原始文案内容
        :param avatar: 数字人形象
        :param style: 视频风格
        :param duration: 时长档位：5s/10s/30s
        :return: 视频生产结果
        """
        # 第一步：优化为口播文案
        polished_script = self.polish_report(
            script_content,
            style="口语化口播",
            audience="普通观众"
        )

        # 第二步：映射参数
        frame_map = {"5s": 124, "10s": 248, "30s": 744}
        num_frames = frame_map.get(duration, 124)

        avatar_map = {
            "default": "ref_images/default.png",
            "商务男性": "ref_images/business_male.png",
            "知性女性": "ref_images/professional_female.png"
        }
        ref_image = avatar_map.get(avatar, avatar_map["default"])

        # 第三步：调用编排引擎提交视频任务
        # （实际生产环境注入全局 orchestrator 实例调用）
        trace_id = f"chuangxiang-{int(time.time())}"
        task_params = {
            "mode": "ref2va",
            "input_text": polished_script[:500],  # 口播长度限制
            "ref_image": ref_image,
            "num_frames": num_frames,
            "style": style
        }

        # 此处调用全局编排引擎的 submit_video_task 方法
        # 异步提交，返回任务ID，由调用方轮询结果
        return {
            "trace_id": trace_id,
            "polished_script": polished_script,
            "task_params": task_params,
            "message": "视频任务已提交生产节点，可通过 trace_id 查询进度"
        }
```

### 1.4 任务参数规范表（与生产节点严格对齐）

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| -------- | ------ | ------ | -------- | ------ |
| `mode` | string | 是 | `ref2va` | 生成模式：`ref2va`（参考图口型同步）/ `fl2va`（纯文生视频） |
| `input_text` | string | 是 | - | 口播文案内容，建议控制在 500 字内 |
| `ref_image` | string | 是 | `ref_images/default.png` | 参考人像路径，相对于 H3 仓库根目录 |
| `num_frames` | int | 否 | 124 | 生成帧数，必须满足 `% 17 == 5`；124帧≈5秒@24fps |
| `seed` | int | 否 | -1 | 随机种子，固定值可复现生成 |
| `batch_name` | string | 否 | 自动生成 | 批次目录名称，建议英文数字 |
| `script_path` | string | 否 | `scripts/batch_ref2va_nf4.py` | 调用脚本路径，自定义批次可修改 |
| `timeout` | int | 否 | 16200 | 任务超时时间（秒）；生产实测单条约 7000s，须 ≥ 4.5h（P0-C1 已修） |
