# file: registry.py
# description: 供应商注册表 - 按前缀路由到 Provider 实现（学 one-api GetChannelName）
# author: YanYuCloudCube Team
# created: 2026-09-20
# status: active
# tags: [providers],[registry],[routing]

"""供应商注册表：新增供应商在 _PROVIDERS 登记一行即可，路由器零改动。"""

import logging
from typing import Dict, List, Type

from .base import OpenAICompatProvider, ProviderProtocol
from .deepseek import DeepseekProvider
from .zhipu import ZhipuProvider

logger = logging.getLogger(__name__)

_PROVIDERS: Dict[str, Type[ProviderProtocol]] = {
    "openai_compat": OpenAICompatProvider,
    "zhipu": ZhipuProvider,  # GLM reasoning_content 折叠策略见 providers/zhipu.py
    "deepseek": DeepseekProvider,
}


def get_provider(name: str = "openai_compat") -> ProviderProtocol:
    """按名取供应商实现；未知名称回退 OpenAI 兼容（绝不抛异常阻断推理）"""
    if name not in _PROVIDERS:
        logger.warning(f"未知 provider '{name}'，回退 openai_compat。可选值: {sorted(_PROVIDERS)}")
    cls = _PROVIDERS.get(name, OpenAICompatProvider)
    return cls()


def known_providers() -> List[str]:
    """已登记供应商标识（供运维面 GET /v1/providers 与配置校验）"""
    return sorted(_PROVIDERS)


def is_known_provider(name: str) -> bool:
    return name in _PROVIDERS


def register_provider(name: str, cls: Type[ProviderProtocol]) -> None:
    _PROVIDERS[name] = cls
