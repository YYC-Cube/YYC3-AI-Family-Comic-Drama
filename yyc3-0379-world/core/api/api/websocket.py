"""
@file: app/api/websocket.py
@description: WebSocket 实时通信路由，支持流式聊天和实时监控
@author: YanYuCloudCube Team <admin@0379.email>
@version: v1.0.0
@created: 2026-04-08
@updated: 2026-04-08
@status: stable
@license: MIT
@copyright: Copyright (c) 2026 YanYuCloudCube Team
@tags: api,python,websocket,streaming,critical
"""

import asyncio
import json
from typing import Optional

from app.middleware.auth import verify_api_key
from app.services import ollama, zhipu
from app.utils.logger import logger


def _upstream_snapshot() -> dict:
    """上游池实时快照（真实 EWMA/熔断状态）；空池时返回云后端在线占位"""
    from app.services.upstream_registry import registry

    if not registry.upstreams:
        return {"cloud": {"status": "online", "latency_ms": 0}}
    return {
        u.name: {
            "status": u.breaker_state,
            "latency_ms": round(u.ewma_latency, 1),
            "error_rate": round(u.ewma_error_rate, 4),
            "load": u.current_load,
        }
        for u in registry.upstreams.values()
    }


from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """接受新连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket连接建立，当前连接数: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """断开连接"""
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket连接断开，当前连接数: {len(self.active_connections)}")

    async def send_message(self, message: dict, websocket: WebSocket):
        """发送消息给指定连接"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"发送WebSocket消息失败: {e}")

    async def broadcast(self, message: dict):
        """广播消息给所有连接"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"广播消息失败: {e}")


manager = ConnectionManager()


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket, token: Optional[str] = Query(None)):
    """
    WebSocket聊天接口 - 支持流式输出

    连接方式：
    ws://localhost:8000/ws/chat?token=your_api_key

    消息格式：
    {
        "model": "llama3.2",
        "messages": [{"role": "user", "content": "你好"}],
        "stream": true
    }

    响应格式：
    {
        "event": "chunk",
        "data": {"content": "..."}
    }
    """
    # 验证认证
    if not token:
        await websocket.close(code=4001, reason="Missing authentication token")
        return

    try:
        if not verify_api_key(token):
            await websocket.close(code=4003, reason="Invalid API key")
            return
    except Exception as e:
        logger.error(f"WebSocket认证失败: {e}")
        await websocket.close(code=4003, reason="Authentication failed")
        return

    await manager.connect(websocket)

    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()

            try:
                request = json.loads(data)
                model = request.get("model", "llama3.2")
                messages = request.get("messages", [])
                stream = request.get("stream", True)

                # 发送开始事件
                await manager.send_message({"event": "start", "data": {"model": model}}, websocket)

                # 判断Provider类型
                if model.startswith("zhipu:") or model in [
                    "glm-4-flash",
                    "glm-4-plus",
                    "glm-4",
                ]:
                    backend = zhipu
                    model_name = model.split(":", 1)[1] if ":" in model else model
                else:
                    backend = ollama
                    model_name = model

                # 调用模型（流式）
                if stream and hasattr(backend, "chat_completion_stream"):
                    # 流式输出
                    async for chunk in backend.chat_completion_stream(
                        model=model_name,
                        messages=messages,
                        temperature=request.get("temperature", 0.7),
                    ):
                        await manager.send_message({"event": "chunk", "data": chunk}, websocket)
                else:
                    # 非流式输出
                    response = await backend.chat_completion(
                        model=model_name,
                        messages=messages,
                        temperature=request.get("temperature", 0.7),
                        max_tokens=request.get("max_tokens"),
                        stream=False,
                    )

                    await manager.send_message({"event": "complete", "data": response}, websocket)

                # 发送结束事件
                await manager.send_message({"event": "done", "data": {"model": model}}, websocket)

            except json.JSONDecodeError:
                await manager.send_message(
                    {"event": "error", "data": {"error": "Invalid JSON format"}},
                    websocket,
                )
            except Exception as e:
                logger.error(f"处理WebSocket消息失败: {e}")
                await manager.send_message({"event": "error", "data": {"error": str(e)}}, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket异常: {e}")
        manager.disconnect(websocket)


@router.websocket("/ws/monitor")
async def websocket_monitor(websocket: WebSocket, token: Optional[str] = Query(None)):
    """
    WebSocket监控接口 - 实时推送系统状态

    连接方式：
    ws://localhost:8000/ws/monitor?token=your_api_key

    推送内容：
    - 模型状态
    - 请求统计
    - 系统资源
    """
    # 验证认证
    if not token:
        await websocket.close(code=4001, reason="Missing authentication token")
        return

    try:
        if not verify_api_key(token):
            await websocket.close(code=4003, reason="Invalid API key")
            return
    except Exception as e:
        logger.error(f"WebSocket认证失败: {e}")
        await websocket.close(code=4003, reason="Authentication failed")
        return

    await manager.connect(websocket)

    try:
        while True:
            # 每5秒推送一次监控数据
            from datetime import datetime, timezone

            from app.utils.metrics import metrics_manager

            metrics = {
                "event": "metrics",
                "data": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "active_requests": metrics_manager.get_active_requests(),
                    "total_requests": metrics_manager.get_total_requests(),
                    "cache_hit_rate": metrics_manager.get_cache_hit_rate(),
                    "models": _upstream_snapshot(),
                },
            }

            await manager.send_message(metrics, websocket)
            await asyncio.sleep(5)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"监控WebSocket异常: {e}")
        manager.disconnect(websocket)
