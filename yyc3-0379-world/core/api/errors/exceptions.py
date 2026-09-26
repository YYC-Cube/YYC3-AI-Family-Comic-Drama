# file: exceptions.py
# description: 自定义异常类模块
# author: YanYuCloudCube Team
# version: v1.0.0
# created: 2026-03-21
# updated: 2026-04-04
# status: active
# tags: [error],[exception],[handling]

"""
@file: app/errors/exceptions.py
@description: 自定义异常类定义
@author: YanYuCloudCube Team <admin@0379.email>
@version: v1.0.0
@created: 2026-03-19
@updated: 2026-03-19
@status: stable
@license: MIT
@copyright: Copyright (c) 2026 YanYuCloudCube Team
@tags: errors,python,core,public
"""

from typing import Any, Dict, Optional


class YYC3Error(Exception):
    """YYC³ 基础异常类"""

    def __init__(
        self,
        message: str,
        error_code: str = "YYC3_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": self.error_code,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details,
        }


class NetworkError(YYC3Error):
    """网络错误"""

    def __init__(
        self,
        message: str = "Network error occurred",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="NETWORK_ERROR",
            status_code=502,
            details=details,
        )


class APIError(YYC3Error):
    """API 错误"""

    def __init__(
        self,
        message: str = "API error occurred",
        status_code: int = 502,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="API_ERROR",
            status_code=status_code,
            details=details,
        )


class TimeoutError(YYC3Error):
    """超时错误"""

    def __init__(self, message: str = "Request timeout", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="TIMEOUT_ERROR",
            status_code=504,
            details=details,
        )


class ValidationError(YYC3Error):
    """验证错误"""

    def __init__(
        self,
        message: str = "Validation error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details=details,
        )


class ModelNotFoundError(YYC3Error):
    """模型未找到错误"""

    def __init__(self, model: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Model '{model}' not found",
            error_code="MODEL_NOT_FOUND",
            status_code=404,
            details=details or {"model": model},
        )


class BackendUnavailableError(YYC3Error):
    """后端不可用错误"""

    def __init__(self, backend: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Backend '{backend}' is unavailable",
            error_code="BACKEND_UNAVAILABLE",
            status_code=503,
            details=details or {"backend": backend},
        )
