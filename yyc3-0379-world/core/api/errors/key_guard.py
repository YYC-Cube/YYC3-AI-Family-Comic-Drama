# file: key_guard.py
# description: 云适配器 API Key 前置校验公共件（OBS-2 三云同构）
# author: YanYuCloudCube Team
# version: v1.0.0
# created: 2026-09-23
# status: active
# tags: [errors],[key-validation],[cloud-adapter]

"""
@file: app/errors/key_guard.py
@description: 空 API Key 前置校验公共件。
    三云适配器（zhipu/deepseek/openai）双入口同构：空 Key 抛 APIError(401)，
    终结 'Bearer ' 非法头 → 模糊 502（v4 zhipu 首创，OBS-2 推广为公共件）。
    落位 app.errors：services 平级互 import 被 importlinter 契约禁止，
    而 errors 为三适配器既有合法依赖。
@author: YanYuCloudCube Team <admin@0379.email>
"""

from typing import Callable

from .exceptions import APIError


def ensure_api_key(
    getter: Callable[[], str],
    provider: str,
    env_name: str,
    apply_url: str = "",
) -> str:
    """空 Key 前置校验：非空返回原值，空则抛 APIError(401)。

    Args:
        getter: Key 取值函数（延迟读取，支持运行时 env 更新）
        provider: 供应商中文名（错误消息用）
        env_name: 对应环境变量名（错误消息自愈指引）
        apply_url: 申请地址（可选，写入 details.hint）
    """
    key = (getter() or "").strip()
    if not key:
        details: dict = {"env": env_name}
        if apply_url:
            details["hint"] = f"https://{apply_url} 申请后写入 .env"
        raise APIError(
            message=f"{provider}未配置：请设置 {env_name} 环境变量",
            status_code=401,
            details=details,
        )
    return key
