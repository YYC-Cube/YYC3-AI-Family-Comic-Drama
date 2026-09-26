# file: versioning.py
# description: API版本管理中间件 - 版本协商、废弃标记、Sunset头
# author: YanYuCloudCube Team
# version: v1.0.0
# created: 2026-07-10
# updated: 2026-07-10
# status: active
# tags: [middleware],[versioning],[api-management]

"""
@file: app/middleware/versioning.py
@description: API版本管理中间件，支持版本协商、废弃标记和Sunset标准头
@author: YanYuCloudCube Team <admin@0379.email>
@version: v1.0.0
@created: 2026-07-10
@updated: 2026-07-10
@status: stable
@license: MIT
@copyright Copyright (c) 2026 YanYuCloudCube Team
@tags: middleware,python,versioning,api-management
"""

import logging
from dataclasses import dataclass
from typing import Awaitable, Callable, Dict, Optional, Set

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)


@dataclass
class VersionInfo:
    """API版本元数据"""

    version: str  # 版本号，如 "v1"
    status: str  # "current" | "deprecated" | "sunset"
    deprecated_on: Optional[str] = None  # 废弃日期 ISO格式
    sunset_on: Optional[str] = None  # 下线日期 ISO格式
    successor: Optional[str] = None  # 后继版本，如 "v2"
    deprecation_link: Optional[str] = None  # 迁移指南URL


class VersioningMiddleware(BaseHTTPMiddleware):
    """
    API版本管理中间件

    功能：
    1. 版本协商：从路径（/v1/）、Header（X-API-Version）或查询参数（?api_version=）提取版本
    2. 废弃通知：对已废弃版本添加 Deprecation + Sunset + Link 响应头（RFC 8594）
    3. 版本拒绝：对已下线（sunset）版本返回 410 Gone
    4. 版本日志：记录各版本使用情况
    """

    # 版本注册表
    VERSIONS: Dict[str, VersionInfo] = {
        "v1": VersionInfo(
            version="v1",
            status="current",
        ),
        "v0": VersionInfo(
            version="v0",
            status="deprecated",
            deprecated_on="2026-06-01",
            sunset_on="2026-09-01",
            successor="v1",
            deprecation_link="https://docs.0379.world/migration/v0-to-v1",
        ),
    }

    SUPPORTED_VERSIONS: Set[str] = {"v1"}
    DEFAULT_VERSION: str = "v1"
    VERSION_HEADER: str = "X-API-Version"
    VERSION_QUERY_PARAM: str = "api_version"

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # 提取请求版本
        req_version = self._extract_version(request)

        # 查找版本信息
        version_info = self.VERSIONS.get(req_version)

        # 已下线版本
        if version_info and version_info.status == "sunset":
            return JSONResponse(
                status_code=410,
                content={
                    "error": "version_retired",
                    "message": f"API version {req_version} has been retired.",
                    "successor": version_info.successor,
                    "migration_guide": version_info.deprecation_link,
                },
                headers=(
                    {"Link": f'<{version_info.deprecation_link}>; rel="deprecation"'}
                    if version_info.deprecation_link
                    else None
                ),
            )

        response = await call_next(request)

        # 为废弃版本添加标准响应头
        if version_info and version_info.status == "deprecated":
            deprecation_value = version_info.deprecated_on or "true"
            response.headers["Deprecation"] = deprecation_value

            if version_info.sunset_on:
                response.headers["Sunset"] = version_info.sunset_on

            if version_info.successor:
                link_val = f'</{version_info.successor}>; rel="successor-version"'
                if version_info.deprecation_link:
                    link_val += f', <{version_info.deprecation_link}>; rel="deprecation"'
                response.headers["Link"] = link_val

            # 在JSON响应中添加警告
            if "application/json" in response.headers.get("content-type", ""):
                response.headers["X-API-Warning"] = (
                    f"Version {req_version} is deprecated. "
                    f"Migrate to {version_info.successor or 'the latest version'}."
                )

        # 始终返回当前API版本信息
        response.headers["X-API-Version"] = req_version

        return response

    def _extract_version(self, request: Request) -> str:
        """
        版本协商优先级：
        1. URL路径前缀（/v1/, /v2/）
        2. 请求头 X-API-Version
        3. 查询参数 api_version
        4. 默认版本
        """
        path = request.url.path

        # 从路径提取 /v1/, /v2/ 等
        for segment in path.split("/"):
            if segment.startswith("v") and segment[1:].isdigit():
                return segment

        # 从Header提取
        header_ver = request.headers.get(self.VERSION_HEADER)
        if header_ver:
            return header_ver.lower()

        # 从查询参数提取
        query_ver = request.query_params.get(self.VERSION_QUERY_PARAM)
        if query_ver:
            return query_ver.lower()

        return self.DEFAULT_VERSION

    @classmethod
    def deprecate_version(
        cls,
        version: str,
        deprecated_on: str,
        sunset_on: str,
        successor: str,
        migration_link: str,
    ):
        """运行时标记版本为废弃"""
        cls.VERSIONS[version] = VersionInfo(
            version=version,
            status="deprecated",
            deprecated_on=deprecated_on,
            sunset_on=sunset_on,
            successor=successor,
            deprecation_link=migration_link,
        )
        logger.info(
            f"API version {version} marked as deprecated "
            f"(sunset: {sunset_on}, successor: {successor})"
        )

    @classmethod
    def get_version_info(cls) -> Dict[str, Dict]:
        """获取所有版本的状态信息"""
        return {
            ver: {
                "version": info.version,
                "status": info.status,
                "deprecated_on": info.deprecated_on,
                "sunset_on": info.sunset_on,
                "successor": info.successor,
            }
            for ver, info in cls.VERSIONS.items()
        }
