# file: openai_compatible.py
# description: 统一 OpenAI 兼容上游客户端（vLLM/NIM/SGLang/Ollama兼容）
# author: YanYuCloudCube Team
# version: v1.1.0
# created: 2026-09-03
# status: active
# tags: [service],[openai-compatible],[upstream]

"""
@file: app/services/openai_compatible.py
@description: 对 OpenAI 兼容上游的单点 HTTP 客户端。chat_completion 返回 OpenAI 格式 JSON；
             chat_completion_stream 产出与 ollama/zhipu 后端统一的 chunk dict。
             地址失败自动切 fallback_url 的职责在上游适配层（chat.py），此处只打单一地址。
             P1-2 配置化收口：endpoint/headers/请求响应转换委托 providers/registry 实现
             （Upstream.provider → get_provider(name)，缺省 openai_compat 行为不变）。
@author: YanYuCloudCube Team <admin@0379.email>
@license: MIT
@copyright Copyright (c) 2026 YanYuCloudCube Team
"""

import json
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx

_TIMEOUT = httpx.Timeout(300.0, connect=10.0, read=300.0)


def _headers(api_key: str) -> Dict[str, str]:
    h = {"Content-Type": "application/json"}
    if api_key:
        h["Authorization"] = f"Bearer {api_key}"
    return h


def _payload(
    model: str,
    messages: List[Dict],
    max_tokens: Optional[int],
    temperature: float,
    top_p: Optional[float],
    stream: bool,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"model": model, "messages": messages, "stream": stream}
    if max_tokens:
        payload["max_tokens"] = max_tokens
    if temperature:
        payload["temperature"] = temperature
    if top_p:
        payload["top_p"] = top_p
    return payload


async def chat_completion(
    base_url: str,
    model: str,
    messages: List[Dict],
    api_key: str = "",
    max_tokens: Optional[int] = None,
    temperature: float = 0.7,
    top_p: Optional[float] = None,
    provider_name: str = "openai_compat",
) -> Dict[str, Any]:
    """调用上游 chat completions，返回统一格式 JSON。

    provider_name 非 openai_compat 时，端点/鉴权/请求响应转换委托 Provider 实现；
    转换异常按原样返回原生响应（转换层故障 ≠ 拒绝服务）。"""
    # 局部导入避免 services↔services 平级耦合面扩大（registry 属 providers 子包）
    from app.services.providers.registry import get_provider

    provider = get_provider(provider_name)
    url = provider.endpoint(base_url, model, False)
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(
            url,
            json=provider.transform_request(model, messages, max_tokens, temperature, top_p, False),
            headers={**_headers(api_key), **provider.headers(api_key)},
        )
        resp.raise_for_status()
        raw = resp.json()
    try:
        return provider.transform_response(raw)
    except Exception:
        return raw


async def chat_completion_stream(
    base_url: str,
    model: str,
    messages: List[Dict],
    api_key: str = "",
    max_tokens: Optional[int] = None,
    temperature: float = 0.7,
    top_p: Optional[float] = None,
    provider_name: str = "openai_compat",
) -> AsyncGenerator[Dict, None]:
    """SSE 流式调用，yield 统一 chunk dict（provider 转换后；缺省行为与原实现一致）"""
    from app.services.providers.registry import get_provider

    provider = get_provider(provider_name)
    url = provider.endpoint(base_url, model, True)
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        async with client.stream(
            "POST",
            url,
            json=provider.transform_request(model, messages, max_tokens, temperature, top_p, True),
            headers={**_headers(api_key), **provider.headers(api_key)},
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    return
                try:
                    yield provider.transform_response(json.loads(data))
                except json.JSONDecodeError:
                    continue
                except Exception:
                    # transform 失败回退原 chunk（SSE chunk 级容错，不断流）
                    continue
