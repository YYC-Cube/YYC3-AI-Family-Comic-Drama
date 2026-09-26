"""
@file: app/errors/__init__.py
@description: 错误处理模块初始化
@author: YanYuCloudCube Team <admin@0379.email>
@version: v1.0.0
@created: 2026-03-19
@updated: 2026-03-19
@status: stable
@license: MIT
@copyright: Copyright (c) 2026 YanYuCloudCube Team
@tags: errors,python,core,public
"""

from .exceptions import (
    APIError,
    BackendUnavailableError,
    ModelNotFoundError,
    NetworkError,
    TimeoutError,
    ValidationError,
    YYC3Error,
)
from .handler import ErrorHandler
from .key_guard import ensure_api_key

__all__ = [
    "YYC3Error",
    "NetworkError",
    "APIError",
    "TimeoutError",
    "ValidationError",
    "ModelNotFoundError",
    "BackendUnavailableError",
    "ErrorHandler",
    "ensure_api_key",
]
