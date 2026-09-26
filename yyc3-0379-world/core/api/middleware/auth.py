"""
@file: app/middleware/auth.py
@description: API认证中间件 - JWT + API Key双重认证
@author: YanYuCloudCube Team <admin@0379.email>
@version: v1.0.0
@created: 2026-04-08
@updated: 2026-04-08
@status: active
@license: MIT
@copyright: Copyright (c) 2026 YanYuCloudCube Team
@tags: middleware,auth,security,python,core
"""

import hashlib
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Set

import jwt
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import settings

logger = logging.getLogger(__name__)


class AuthConfig:
    """从全局 settings 动态读取配置，避免硬编码敏感信息"""

    @property
    def AUTH_ENABLED(self) -> bool:
        return settings.auth_enabled

    @property
    def JWT_SECRET_KEY(self) -> str:
        return settings.jwt_secret_key

    @property
    def JWT_ALGORITHM(self) -> str:
        return settings.jwt_algorithm

    @property
    def JWT_EXPIRATION_HOURS(self) -> int:
        return settings.jwt_expiration_hours

    API_KEY_HEADER: str = "X-API-Key"
    AUTHORIZATION_HEADER: str = "Authorization"

    SKIP_AUTH_PATHS: Set[str] = {
        "/v1/ping",
        "/v1/health",
        "/health",
        "/healthz",
        "/metrics",
        "/docs",
        "/openapi.json",
        "/redoc",
    }

    SKIP_AUTH_PREFIXES: List[str] = [
        "/docs",
        "/openapi",
        "/redoc",
    ]

    @property
    def VALID_API_KEYS(self) -> Set[str]:
        """从 settings.api_keys 动态解析，逗号分隔"""
        return {k.strip() for k in settings.api_keys.split(",") if k.strip()}

    @property
    def ADMIN_API_KEYS(self) -> Set[str]:
        """管理面密钥（/v1/admin/** 专用）；未配置时回退 VALID_API_KEYS（兼容单机部署）"""
        raw = getattr(settings, "admin_api_keys", "") or ""
        keys = {k.strip() for k in raw.split(",") if k.strip()}
        return keys or self.VALID_API_KEYS


auth_config = AuthConfig()
security = HTTPBearer(auto_error=False)


def generate_jwt_token(user_id: str, expires_hours: Optional[int] = None) -> str:
    """
    生成JWT令牌

    Args:
        user_id: 用户ID
        expires_hours: 过期时间（小时）

    Returns:
        JWT令牌字符串
    """
    expires_hours = expires_hours or auth_config.JWT_EXPIRATION_HOURS
    now = datetime.now(timezone.utc)
    expiration = now + timedelta(hours=expires_hours)

    payload = {
        "user_id": user_id,
        "exp": expiration,
        "iat": now,
        "iss": "yyc3-gateway",
    }

    token = jwt.encode(payload, auth_config.JWT_SECRET_KEY, algorithm=auth_config.JWT_ALGORITHM)

    return token


def verify_jwt_token(token: str) -> Optional[dict]:
    """
    验证JWT令牌

    Args:
        token: JWT令牌字符串

    Returns:
        解码后的payload，验证失败返回None
    """
    try:
        payload = jwt.decode(
            token,
            auth_config.JWT_SECRET_KEY,
            algorithms=[auth_config.JWT_ALGORITHM],
            issuer="yyc3-gateway",
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None


def verify_api_key(api_key: str) -> bool:
    """
    验证API Key

    Args:
        api_key: API Key字符串

    Returns:
        验证结果
    """
    return api_key in auth_config.VALID_API_KEYS


def hash_api_key(api_key: str) -> str:
    """
    哈希API Key（用于存储）

    Args:
        api_key: 原始API Key

    Returns:
        哈希后的API Key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


class AuthMiddleware(BaseHTTPMiddleware):
    """
    认证中间件 - 支持JWT和API Key双重认证

    认证方式：
    1. JWT Token: Authorization: Bearer <token>
    2. API Key: X-API-Key: <api_key>

    优先级：JWT > API Key
    """

    async def dispatch(self, request: Request, call_next):
        if not auth_config.AUTH_ENABLED:
            return await call_next(request)

        path = request.url.path

        if self._should_skip_auth(path):
            return await call_next(request)

        has_credentials, auth_result = await self._authenticate(request)

        if not has_credentials:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Unauthorized",
                    "message": "Missing authentication credentials",
                    "detail": "Please provide either a valid JWT token or API key",
                },
            )

        if not auth_result:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "Forbidden",
                    "message": "Invalid authentication credentials",
                    "detail": "The provided JWT token or API key is invalid or expired",
                },
            )

        # ── 管理面 RBAC：/v1/admin/** 需 admin API Key 或 role=admin JWT ──
        if self._is_admin_request(path):
            is_admin = bool(auth_result.get("admin")) or auth_result.get("role") == "admin"
            if not is_admin:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "error": "Forbidden",
                        "message": "Admin privileges required",
                        "detail": "/v1/admin/** 需要管理面密钥（ADMIN_API_KEYS）或 admin 角色 JWT",
                    },
                )

        request.state.user = auth_result

        response = await call_next(request)

        # ── TOP1 A2A 计费门控：协同事务请求经 vk 记账（chat 范式见 api/chat.py）──
        await self._maybe_record_a2a_spend(request, response, auth_result)

        return response

    # ── A2A 协同事务记账（v2：解耦端点响应形态，双探针 + 兜底常量）──────────

    _AGENT_A2A_PREFIX = "/v1/agent/a2a/"
    _A2A_ORCHESTRATION_FALLBACK_COST = 0.001  # 双探针均缺失时的兜底成本（防长期 0 计量）

    async def _maybe_record_a2a_spend(self, request: Request, response, auth_result) -> None:
        """仅对虚拟密钥身份的 A2A 编排/任务端点计协同事务成本（静态/管理键不计费）。

        成本双探针：X-A2A-Cost 响应头 > X-Total-Cost；均无 → 兜底常量（协同事务
        token usage 未知，避免长期 0 计量掩盖 vk 用量）；chat 既有链路不受影响。
        入队为微秒级 LPUSH，请求内直 await（不经后台任务，保证落队列后再响应）。
        """
        if not request.url.path.startswith(self._AGENT_A2A_PREFIX):
            return
        vk = auth_result.get("vk") if isinstance(auth_result, dict) else None
        if vk is None:
            return
        # 优先 X-A2A-Cost（单 Agent/编排端点直发）；缺省 X-Total-Cost；均无 → 兜底常量
        raw_cost = response.headers.get("X-A2A-Cost") or response.headers.get("X-Total-Cost")
        try:
            cost = float(raw_cost or 0)
        except (TypeError, ValueError):
            cost = 0.0
        if cost <= 0:
            cost = self._A2A_ORCHESTRATION_FALLBACK_COST
        latency_ms = int(
            (time.time() - getattr(request.state, "_a2a_start_ts", time.time())) * 1000
        )
        try:
            from app.services.virtual_key_manager import vk_manager

            await vk_manager.enqueue_spend(
                {
                    "key_id": vk.get("id"),
                    "model": request.url.path.rstrip("/").split("/")[-1] or "a2a",
                    "upstream": "a2a-orchestration",
                    "capability": "agent",
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "cost_usd": cost,
                    "latency_ms": latency_ms,
                }
            )
        except Exception:
            logger.debug("A2A 记账失败（不影响响应）")

    def _should_skip_auth(self, path: str) -> bool:
        """
        判断是否跳过认证

        Args:
            path: 请求路径

        Returns:
            是否跳过认证
        """
        if path in auth_config.SKIP_AUTH_PATHS:
            return True

        for prefix in auth_config.SKIP_AUTH_PREFIXES:
            if path.startswith(prefix):
                return True

        return False

    def _is_admin_request(self, path: str) -> bool:
        """管理面路径判定（/v1/admin/** → 需 ADMIN_API_KEYS 或 admin 角色 JWT）

        看板壳（/v1/admin/dashboard）特例：静态 HTML 无敏感数据，认证即可加载；
        数据 API（virtual-keys*）仍要求 admin —— UX 闭环：壳内 fetch 403 → prompt 补录。
        """
        if path == "/v1/admin/dashboard":
            return False
        return path.startswith("/v1/admin")

    async def _authenticate(self, request: Request) -> tuple[bool, Optional[dict]]:
        """
        执行认证

        Args:
            request: FastAPI请求对象

        Returns:
            (是否有认证信息, 认证结果)
        """
        jwt_token = self._extract_jwt_token(request)
        if jwt_token:
            payload = verify_jwt_token(jwt_token)
            if payload:
                return (
                    True,
                    {
                        "type": "jwt",
                        "user_id": payload.get("user_id"),
                        "role": payload.get("role", ""),
                        "exp": payload.get("exp"),
                    },
                )
            else:
                return (True, None)

        api_key = self._extract_api_key(request)
        if api_key:
            return await self._authenticate_vk_or_static(request, api_key)

        return (False, None)

    async def _authenticate_vk_or_static(
        self, request: Request, api_key: str
    ) -> tuple[bool, Optional[dict]]:
        """API Key 校验：虚拟密钥双层缓存校验链优先，未命中降级静态/管理 Key。

        提取为独立方法以便测试打桩（强制 vk 分支、禁用静态键降级误判）。
        """
        # ── P0-1 双层缓存校验链：虚拟密钥（内存→Redis→PG）优先 ──
        try:
            from app.services.virtual_key_manager import vk_manager

            vk = await vk_manager.authenticate(api_key)
            if vk is not None:
                # 虚拟密钥非管理身份：管理面直接 403（rbac：vk 只能调推理面）
                if self._is_admin_request(request.url.path):
                    return (True, {"type": "virtual_key", "vk": vk, "admin": False})
                return (True, {"type": "virtual_key", "vk": vk})
        except Exception as e:
            logger.debug(f"虚拟密钥校验链异常（降级静态 Key）: {e}")

        if verify_api_key(api_key) or api_key in auth_config.ADMIN_API_KEYS:
            return (
                True,
                {
                    "type": "api_key",
                    "key_hash": hash_api_key(api_key),
                    "admin": api_key in auth_config.ADMIN_API_KEYS,
                },
            )
        return (True, None)

    def _extract_jwt_token(self, request: Request) -> Optional[str]:
        """
        从请求中提取JWT令牌

        Args:
            request: FastAPI请求对象

        Returns:
            JWT令牌字符串，未找到返回None
        """
        authorization = request.headers.get(auth_config.AUTHORIZATION_HEADER)

        if not authorization:
            return None

        parts = authorization.split()

        if len(parts) != 2:
            return None

        scheme, token = parts

        if scheme.lower() != "bearer":
            return None

        return token

    def _extract_api_key(self, request: Request) -> Optional[str]:
        """
        从请求中提取API Key

        Args:
            request: FastAPI请求对象

        Returns:
            API Key字符串，未找到返回None
        """
        return request.headers.get(auth_config.API_KEY_HEADER)


def create_auth_dependency():
    """
    创建FastAPI认证依赖

    用法：
        @app.get("/protected")
        async def protected_route(user: dict = Depends(create_auth_dependency())):
            return {"user": user}
    """

    async def auth_dependency(request: Request):
        if hasattr(request.state, "user"):
            return request.state.user

        if not auth_config.AUTH_ENABLED:
            return {"type": "disabled"}

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    return auth_dependency


auth_required = create_auth_dependency()


__all__ = [
    "AuthMiddleware",
    "AuthConfig",
    "auth_config",
    "generate_jwt_token",
    "verify_jwt_token",
    "verify_api_key",
    "hash_api_key",
    "auth_required",
]
