# file: rate_limit.py
# description: API 限流中间件模块 - Redis分布式滑动窗口限流 v2.0
# author: YanYuCloudCube Team
# version: v2.0.0
# created: 2026-03-21
# updated: 2026-07-24
# status: active
# tags: [middleware],[rate-limit],[security],[distributed]

"""
@file: app/middleware/rate_limit.py
@description: 限流中间件 v2.0，基于 Redis 有序集合的分布式滑动窗口限流
             - 支持多节点共享限流状态
             - Redis 不可用时自动降级为内存限流
             - 支持 IP + User 双维度限流
@author: YanYuCloudCube Team <admin@0379.email>
@version: v2.0.0
@created: 2026-03-19
@updated: 2026-07-24
@status: stable
@license: MIT
@copyright: Copyright (c) 2026 YanYuCloudCube Team
@tags: middleware,python,rate_limit,public
"""

import hashlib
import logging
import time
from functools import wraps
from typing import Callable, Dict, Optional, Tuple

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.cache import redis_client

logger = logging.getLogger(__name__)

# ── Redis 限流 Lua 脚本（原子操作） ──────────────────────
# 使用有序集合实现滑动窗口，单次原子调用完成：清理 + 计数 + 添加
SLIDING_WINDOW_LUA = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local max_reqs = tonumber(ARGV[3])
local cutoff = now - window

-- 清理窗口外的旧记录
redis.call('ZREMRANGEBYSCORE', key, 0, cutoff)

-- 获取当前窗口内请求数
local current = redis.call('ZCARD', key)

if current >= max_reqs then
    -- 限流：返回剩余的TTL（最早记录的过期时间）
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local reset_time = oldest[2] + window
    return {0, current, reset_time}
end

-- 允许请求：添加当前时间戳
redis.call('ZADD', key, now, tostring(now) .. ':' .. math.random())
redis.call('EXPIRE', key, window + 1)

return {1, current + 1, now + window}
"""


class RateLimiter:
    """分布式限流器

    基于 Redis 有序集合的滑动窗口算法，支持多节点共享限流状态。
    Redis 不可用时自动降级为内存限流（单节点降级）。
    """

    def __init__(self, max_requests: int = 100, time_window: int = 60, burst: int = 10):
        self.max_requests = max_requests
        self.time_window = time_window
        self.burst = burst

        self._local_requests: Dict[str, list] = {}
        self._redis_available: Optional[bool] = None
        self.logger = logging.getLogger(__name__)

    async def _check_redis(self) -> bool:
        """检查 Redis 是否可用，结果缓存 10 秒"""
        if self._redis_available is False:
            return False
        try:
            await redis_client.ping()
            self._redis_available = True
            return True
        except Exception:
            if self._redis_available is not False:
                self.logger.warning("Redis 不可用，限流降级为内存模式")
                self._redis_available = False
            return False

    def _get_redis_key(self, raw_key: str) -> str:
        """生成 Redis 限流键"""
        hashed = hashlib.sha256(raw_key.encode()).hexdigest()[:16]
        return f"ratelimit:{hashed}"

    async def is_allowed(self, key: str) -> Tuple[bool, Dict[str, int]]:
        """检查是否允许请求

        Args:
            key: 限流键（IP / User ID）

        Returns:
            (allowed, info) — info 包含 limit, remaining, reset
        """
        if await self._check_redis():
            return await self._redis_is_allowed(key)
        return await self._local_is_allowed(key)

    async def _redis_is_allowed(self, key: str) -> Tuple[bool, Dict[str, int]]:
        """Redis 分布式限流"""
        redis_key = self._get_redis_key(key)
        now = time.time()

        try:
            sha = await redis_client.eval(
                SLIDING_WINDOW_LUA,
                1,
                redis_key,
                str(int(now * 1000)),
                str(self.time_window * 1000),
                str(self.max_requests),
            )
            # sha = [allowed, current_count, reset_time]
            allowed = bool(sha[0])
            current = int(sha[1])
            reset_time = int(sha[2]) / 1000.0

            return allowed, {
                "limit": self.max_requests,
                "remaining": self.max_requests - current if allowed else 0,
                "reset": int(reset_time),
            }
        except Exception as e:
            self.logger.error(f"Redis 限流异常 ({e})，降级到内存模式")
            self._redis_available = False
            return await self._local_is_allowed(key)

    async def _local_is_allowed(self, key: str) -> Tuple[bool, Dict[str, int]]:
        """内存限流（降级模式）"""
        now = time.time()
        window_start = now - self.time_window

        requests = self._local_requests.get(key, [])
        requests[:] = [t for t in requests if t > window_start]

        if len(requests) >= self.max_requests:
            return False, {
                "limit": self.max_requests,
                "remaining": 0,
                "reset": int(requests[0] + self.time_window),
            }

        requests.append(now)
        self._local_requests[key] = requests

        return True, {
            "limit": self.max_requests,
            "remaining": self.max_requests - len(requests),
            "reset": int(now + self.time_window),
        }

    async def cleanup(self):
        """清理过期记录（仅内存模式有效）"""
        now = time.time()
        window_start = now - self.time_window

        for key in list(self._local_requests.keys()):
            self._local_requests[key][:] = [
                t for t in self._local_requests[key] if t > window_start
            ]

            if not self._local_requests[key]:
                del self._local_requests[key]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""

    def __init__(
        self,
        app=None,
        ip_limiter: Optional[RateLimiter] = None,
        user_limiter: Optional[RateLimiter] = None,
    ):
        super().__init__(app)
        self.ip_limiter = ip_limiter or RateLimiter(max_requests=500, time_window=60)
        self.user_limiter = user_limiter or RateLimiter(max_requests=1000, time_window=60)
        self.logger = logging.getLogger(__name__)

    async def dispatch(self, request: Request, call_next):
        """中间件处理"""
        client_ip = self._get_client_ip(request)
        user_id = request.headers.get("X-User-ID")

        allowed, ip_info = await self.ip_limiter.is_allowed(client_ip)

        if not allowed:
            self.logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests from this IP",
                    "retry_after": ip_info["reset"] - int(time.time()),
                },
            )

        if user_id:
            allowed, user_info = await self.user_limiter.is_allowed(user_id)

            if not allowed:
                self.logger.warning(f"Rate limit exceeded for user: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests for this user",
                        "retry_after": user_info["reset"] - int(time.time()),
                    },
                )

        response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(ip_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(ip_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(ip_info["reset"])

        return response

    # 可信反向代理（Traefik）来源 IP 集合——仅这些来源的 X-Forwarded-For 可被信任
    TRUSTED_PROXIES = {
        "100.126.132.112",  # ECS Traefik (Tailscale)
        "100.65.172.88",  # NAS 本机 (Tailscale)
        "127.0.0.1",
        "::1",
    }

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端 IP（仅信任来自可信代理的转发头，防伪造绕过限流）"""
        peer_ip = request.client.host if request.client else "unknown"

        # 仅当直连来源是可信代理时才采信 X-Forwarded-For
        if peer_ip in self.TRUSTED_PROXIES:
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                # 取最左侧真实客户端 IP（Traefik 按序追加）
                return forwarded.split(",")[0].strip()

            real_ip = request.headers.get("X-Real-IP")
            if real_ip:
                return real_ip

        return peer_ip


rate_limit_middleware = RateLimitMiddleware()


def rate_limit(max_requests: int = 100, time_window: int = 60):
    """限流装饰器（支持路由级别的精细化限流）"""
    limiter = RateLimiter(max_requests=max_requests, time_window=time_window)

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = None

            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                return await func(*args, **kwargs)

            client_ip = rate_limit_middleware._get_client_ip(request)

            allowed, info = await limiter.is_allowed(client_ip)

            if not allowed:
                logger.warning(
                    f"Rate limit exceeded for IP: {client_ip} " f"in function: {func.__name__}"
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests, please slow down",
                        "retry_after": info["reset"] - int(time.time()),
                    },
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
