# file: base.py
# description: 供应商转换契约 - transform_request/transform_response 纯函数对（学 litellm L4）
# author: YanYuCloudCube Team
# created: 2026-09-20
# status: active
# tags: [providers],[protocol],[contract]

"""供应商转换契约（精简自 one-api Adaptor 8 方法 → 4 方法纯函数）。

所有 transform_* 均为纯函数：入参出参皆为 dict，禁止 IO、禁止全局状态——
便于单测与未来多进程复用。
"""

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class ProviderProtocol(Protocol):
    """每供应商实现：请求/响应双向转换 + 端点/鉴权信息"""

    name: str  # 供应商标识（如 zhipu / deepseek / openai_compat）

    def endpoint(self, base_url: str, model: str, stream: bool) -> str:
        """给定基址与模型，返回完整请求 URL"""
        ...

    def headers(self, api_key: str) -> Dict[str, str]:
        """鉴权头（空 key 返回空 dict）"""
        ...

    def transform_request(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int],
        temperature: float,
        top_p: Optional[float],
        stream: bool,
    ) -> Dict[str, Any]:
        """OpenAI 统一格式 → 供应商原生请求体"""
        ...

    def transform_response(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """供应商原生响应 → OpenAI 统一格式（兼容 SSE chunk）"""
        ...


# ── OpenAI 兼容默认实现（vLLM/NIM/Ollama-兼容/大多数网关直接复用）──


def _default_endpoint(base_url: str, model: str, stream: bool) -> str:
    # 与 openai_compatible 客户端既有路径一致（/v1/chat/completions），vLLM/NIM/智谱/deepseek 通用
    return f"{base_url.rstrip('/')}/v1/chat/completions"


def _default_headers(api_key: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"} if api_key else {}


def _default_transform_request(
    model: str,
    messages: List[Dict[str, Any]],
    max_tokens: Optional[int],
    temperature: float,
    top_p: Optional[float],
    stream: bool,
) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        body["max_tokens"] = max_tokens
    if top_p is not None:
        body["top_p"] = top_p
    if stream:
        body["stream"] = True
    return body


def _default_transform_response(raw: Dict[str, Any]) -> Dict[str, Any]:
    return raw  # OpenAI 格式即统一格式


class OpenAICompatProvider:
    """OpenAI 兼容供应商（缺省实现，其他供应商可继承覆盖差异点）"""

    name = "openai_compat"
    endpoint = staticmethod(_default_endpoint)
    headers = staticmethod(_default_headers)
    transform_request = staticmethod(_default_transform_request)
    transform_response = staticmethod(_default_transform_response)
