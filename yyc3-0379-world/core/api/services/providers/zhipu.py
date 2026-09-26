# file: zhipu.py
# description: 智谱 AI Provider - 差异点：reasoning_content 与 content 合并策略
# author: YanYuCloudCube Team
# created: 2026-09-20
# status: active
# tags: [providers],[zhipu],[transform]

"""智谱 Provider：继承 OpenAI 兼容缺省实现，只覆写差异点 transform_response。

差异点（源自 services/zhipu.py 既有逻辑沉淀）：
GLM 系列 R 类模型返回 reasoning_content 与 content 两个字段；
统一层将 reasoning_content 折叠进 content（R+C 则拼接），保证下游只看 OpenAI 标准 message.content。
"""

from typing import Any, Dict, List, Optional

from .base import _default_endpoint, _default_headers, _default_transform_request


class ZhipuProvider:
    """智谱 AI（GLM 系列）"""

    name = "zhipu"

    # 端点与鉴权与 OpenAI 兼容（/chat/completions + Bearer），委托缺省实现
    @staticmethod
    def endpoint(base_url: str, model: str, stream: bool) -> str:
        return _default_endpoint(base_url, model, stream)

    @staticmethod
    def headers(api_key: str) -> Dict[str, str]:
        return _default_headers(api_key)

    @staticmethod
    def transform_request(
        model: str,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int],
        temperature: float,
        top_p: Optional[float],
        stream: bool,
    ) -> Dict[str, Any]:
        return _default_transform_request(model, messages, max_tokens, temperature, top_p, stream)

    @staticmethod
    def transform_response(raw: Dict[str, Any]) -> Dict[str, Any]:
        """GLM reasoning_content 折叠：R only → content=R；R+C → content=R\\n\\nC"""
        choices = raw.get("choices", [])
        for choice in choices:
            message = choice.get("message", {})
            reasoning = message.get("reasoning_content", "")
            content = message.get("content", "")
            if reasoning and not content:
                message["content"] = reasoning
            elif reasoning and content:
                message["content"] = f"{reasoning}\n\n{content}"
        return raw
