# file: usage_logger.py
# description: 用量落库服务 - api 层经此间接访问 DB（importlinter 分层契约：api 禁直连 app.db）
# author: YanYuCloudCube Team
# created: 2026-09-20
# status: active
# tags: [usage],[db],[layering]

"""api 层用量落库的合规入口：api → services.usage_logger → db。

职责仅做分层转发，禁止在此堆业务逻辑。
"""

from typing import Optional

from app.db import log_usage as _log_usage


async def log_usage(
    model: str,
    backend_type: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    user_id: Optional[str] = None,
) -> None:
    await _log_usage(
        model=model,
        backend_type=backend_type,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        user_id=user_id,
    )
