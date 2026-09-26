# file: cache.py
# description: 缓存工具函数模块 - CacheManager封装层
# author: YanYuCloudCube Team
# version: v2.0.0
# created: 2026-03-21
# updated: 2026-07-10
# status: active
# tags: [util],[cache],[helper],[ttl],[eviction]

"""
@file: app/utils/cache.py
@description: 缓存管理器，封装底层Redis操作，提供TTL、标签失效和LRU淘汰
@author: YanYuCloudCube Team <admin@0379.email>
@version: v2.0.0
@created: 2026-03-19
@updated: 2026-07-10
@status: stable
@license: MIT
@copyright Copyright (c) 2026 YanYuCloudCube Team
@tags: utils,python,cache,public
"""

import logging
from typing import Any, Dict, List, Optional

from app.cache import delete_cached, get_cached, set_cached


class CacheManager:
    """缓存管理器 - 支持TTL过期、标签失效、LRU淘汰"""

    def __init__(self, default_ttl: int = 300):
        self.default_ttl = default_ttl
        self.stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0,
        }
        self.logger = logging.getLogger(__name__)

    def _get_key(self, key: str) -> str:
        """生成缓存键"""
        return key

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            cache_key = self._get_key(key)
            value = await get_cached(cache_key)

            if value is not None:
                self.stats["hits"] += 1
                self.logger.debug(f"Cache hit: {key}")
                return value

            self.stats["misses"] += 1
            self.logger.debug(f"Cache miss: {key}")
            return None
        except Exception as e:
            self.stats["errors"] += 1
            self.logger.error(f"Cache get error: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """
        设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None使用默认值
            tags: 缓存标签列表，用于按标签批量失效
        """
        try:
            cache_key = self._get_key(key)
            effective_ttl = ttl if ttl is not None else self.default_ttl
            await set_cached(cache_key, value, ttl=effective_ttl, tags=tags)
            self.stats["sets"] += 1
            self.logger.debug(f"Cache set: {key}, ttl: {effective_ttl}s, tags: {tags}")
            return True
        except Exception as e:
            self.stats["errors"] += 1
            self.logger.error(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            cache_key = self._get_key(key)
            await delete_cached(cache_key)
            self.stats["deletes"] += 1
            self.logger.debug(f"Cache delete: {key}")
            return True
        except Exception as e:
            self.stats["errors"] += 1
            self.logger.error(f"Cache delete error: {e}")
            return False

    async def invalidate_by_tags(self, tags: List[str]) -> int:
        """按标签批量失效缓存"""
        from app.cache import invalidate_by_tag

        total = 0
        for tag in tags:
            count = await invalidate_by_tag(tag)
            total += count
        if total > 0:
            self.stats["evictions"] += total
            self.logger.info(f"Invalidated {total} entries by tags: {tags}")
        return total

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total if total > 0 else 0.0

        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "errors": self.stats["errors"],
            "sets": self.stats["sets"],
            "deletes": self.stats["deletes"],
            "tag_evictions": self.stats["evictions"],
            "total": total,
            "hit_rate": round(hit_rate, 4),
        }

    def reset_stats(self):
        """重置缓存统计"""
        self.stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0,
        }
        self.logger.info("Cache stats reset")


cache_manager = CacheManager(default_ttl=300)


async def cached(
    key_prefix: str,
    ttl: int = 300,
    tags: Optional[List[str]] = None,
):
    """缓存装饰器"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            key = f"{key_prefix}:{hash(str(args) + str(kwargs))}"

            cached_value = await cache_manager.get(key)
            if cached_value is not None:
                return cached_value

            result = await func(*args, **kwargs)
            await cache_manager.set(key, result, ttl=ttl, tags=tags)

            return result

        return wrapper

    return decorator
