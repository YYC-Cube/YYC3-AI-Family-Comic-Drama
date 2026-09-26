"""
@file: deepseek.py
@description: DeepSeek API集成服务
@author: YanYuCloudCube Team <admin@0379.email>
@version: v1.0.0
@created: 2026-04-08
@updated: 2026-04-08
@status: stable
@license: MIT
"""

import json
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings
from app.utils.logger import logger


def _base() -> str:
    """基址外部化（settings.deepseek_base_url，默认=原硬编码）"""
    return settings.deepseek_base_url


def _get_deepseek_key() -> str:
    """延迟读取 DeepSeek Key（OBS-2：原模块级快照 import 时定格，env 运行时更新失效）"""
    import os

    return os.getenv("DEEPSEEK_API_KEY", "") or settings.deepseek_api_key


def _ensure_key() -> str:
    """空 Key 前置校验：401 明确报错（OBS-2；原实现 502 + 模块级快照）"""
    from app.errors.key_guard import ensure_api_key

    return ensure_api_key(
        _get_deepseek_key,
        provider="DeepSeek",
        env_name="DEEPSEEK_API_KEY",
        apply_url="platform.deepseek.com",
    )


async def chat_completion(
    model: str,
    messages: List[Dict],
    max_tokens: Optional[int] = None,
    temperature: float = 0.7,
    top_p: Optional[float] = None,
    stream: bool = False,
) -> Dict[str, Any]:
    """
    DeepSeek聊天完成接口

    Args:
        model: 模型名称 (deepseek-chat, deepseek-coder)
        messages: 消息列表
        max_tokens: 最大token数
        temperature: 温度参数
        top_p: top_p参数
        stream: 是否流式输出

    Returns:
        dict: API响应
    """
    headers = {
        "Authorization": f"Bearer {_ensure_key()}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
        "stream": stream,
    }

    if max_tokens:
        payload["max_tokens"] = max_tokens
    if temperature:
        payload["temperature"] = temperature
    if top_p:
        payload["top_p"] = top_p

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{_base()}/chat/completions", headers=headers, json=payload
            )

            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        logger.error(f"DeepSeek API错误: {e.response.status_code} - {e.response.text}")
        from app.errors import APIError

        raise APIError(
            message="DeepSeek API调用失败",
            details={"status_code": e.response.status_code, "error": e.response.text},
        )
    except Exception as e:
        logger.error(f"DeepSeek服务异常: {str(e)}")
        from app.errors import APIError

        raise APIError(message="DeepSeek服务异常", details={"error": str(e)})


async def chat_completion_stream(
    model: str,
    messages: List[Dict],
    max_tokens: Optional[int] = None,
    temperature: float = 0.7,
    top_p: Optional[float] = None,
):
    """
    DeepSeek流式输出 - 用于WebSocket

    Yields:
        dict: 流式响应块
    """
    headers = {
        "Authorization": f"Bearer {_ensure_key()}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
    }

    if max_tokens:
        payload["max_tokens"] = max_tokens
    if temperature:
        payload["temperature"] = temperature
    if top_p:
        payload["top_p"] = top_p

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST", f"{_base()}/chat/completions", headers=headers, json=payload
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line and line.startswith("data: "):
                        data_str = line[6:]

                        if data_str.strip() == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data_str)
                            choices = chunk.get("choices", [])

                            for choice in choices:
                                delta = choice.get("delta", {})

                                yield {
                                    "id": chunk.get("id", ""),
                                    "object": "chat.completion.chunk",
                                    "created": chunk.get("created", 0),
                                    "model": model,
                                    "choices": [
                                        {
                                            "index": choice.get("index", 0),
                                            "delta": delta,
                                            "finish_reason": choice.get("finish_reason"),
                                        }
                                    ],
                                }
                        except json.JSONDecodeError:
                            continue

    except httpx.HTTPStatusError as e:
        logger.error(f"DeepSeek流式API错误: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"DeepSeek流式输出错误: {str(e)}")
        from app.errors import APIError

        raise APIError(message="DeepSeek流式服务异常", details={"error": str(e)})


async def list_models() -> List[Dict[str, Any]]:
    """
    获取DeepSeek可用模型列表

    Returns:
        list: 模型列表
    """
    return [
        {
            "id": "deepseek-chat",
            "name": "DeepSeek Chat",
            "provider": "deepseek",
            "model_type": "chat",
            "pricing_type": "paid",
            "description": "DeepSeek通用对话模型，性价比高",
            "max_tokens": 64000,
            "supports_stream": True,
            "supports_vision": False,
            "supports_function_calling": True,
        },
        {
            "id": "deepseek-coder",
            "name": "DeepSeek Coder",
            "provider": "deepseek",
            "model_type": "code",
            "pricing_type": "paid",
            "description": "DeepSeek代码专用模型，代码能力强",
            "max_tokens": 16000,
            "supports_stream": True,
            "supports_vision": False,
            "supports_function_calling": True,
        },
    ]
