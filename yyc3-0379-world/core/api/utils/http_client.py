# file: http_client.py
# description: HTTP 客户端工具模块
# author: YanYuCloudCube Team
# version: v1.0.0
# created: 2026-03-21
# updated: 2026-04-04
# status: active
# tags: [util],[http],[client]

"""
@file: app/utils/http_client.py
@description: HTTP 连接池管理器，提供高效的 HTTP 客户端
@author: YanYuCloudCube Team <admin@0379.email>
@version: v1.0.0
@created: 2026-03-19
@updated: 2026-03-19
@status: stable
@license: MIT
@copyright: Copyright (c) 2026 YanYuCloudCube Team
@tags: utils,python,http,public
"""

import logging
from typing import Any, Dict, Optional

import httpx


class HttpClient:
    """HTTP 连接池管理器"""

    def __init__(
        self,
        timeout: float = 120.0,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        keepalive_expiry: float = 30.0,
    ):
        self.timeout = httpx.Timeout(timeout, read=timeout)
        self.limits = httpx.Limits(
            max_keepalive_connections=max_keepalive_connections,
            max_connections=max_connections,
            keepalive_expiry=keepalive_expiry,
        )

        self.client = httpx.AsyncClient(
            timeout=self.timeout, limits=self.limits, http2=False, verify=True
        )

        self.logger = logging.getLogger(__name__)
        self.logger.info(
            f"HTTP client initialized with max_connections={max_connections}, "
            f"max_keepalive_connections={max_keepalive_connections}"
        )

    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """发送 GET 请求"""
        return await self.client.get(url, headers=headers, params=params)

    async def post(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """发送 POST 请求"""
        return await self.client.post(url, headers=headers, json=json, data=data)

    async def put(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """发送 PUT 请求"""
        return await self.client.put(url, headers=headers, json=json, data=data)

    async def delete(self, url: str, headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        """发送 DELETE 请求"""
        return await self.client.delete(url, headers=headers)

    async def close(self):
        """关闭连接池"""
        await self.client.aclose()
        self.logger.info("HTTP client closed")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()


http_client = HttpClient(
    timeout=120.0,
    max_connections=100,
    max_keepalive_connections=20,
    keepalive_expiry=30.0,
)
