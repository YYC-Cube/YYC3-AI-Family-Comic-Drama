# file: cache.py
# description: 缓存管理模块 - 支持TTL过期、主动失效、大小限制
# author: YanYuCloudCube Team
# version: v2.0.0
# created: 2026-03-21
# updated: 2026-07-10
# status: active
# tags: [cache],[redis],[performance],[ttl],[eviction]

"""
@file: app/cache.py
@description: Redis 缓存模块，提供TTL过期、主动失效、LRU淘汰和大小限制
@author: YanYuCloudCube Team <admin@0379.email>
@version: v2.0.0
@created: 2026-03-13
@updated: 2026-07-10
@status: stable
@license: MIT
@copyright Copyright (c) 2026 YanYuCloudCube Team
@tags: cache,python,redis,core,public
"""

import json
import logging
import time
from typing import Any, Dict, List

from redis.asyncio import Redis

from app.config import settings

logger = logging.getLogger(__name__)

redis_client = Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    password=settings.redis_password,
    decode_responses=True,
)

# ── 缓存配置 ──────────────────────────────────────────────
CACHE_TTL = 3600  # 默认TTL: 1小时
CACHE_MAX_ENTRIES = 10000  # 最大缓存条目数
CACHE_INDEX_KEY = "llm_cache:index"  # 有序集合索引（用于LRU淘汰）
CACHE_SIZE_KEY = "llm_cache:size"  # 当前缓存条目计数


async def get_redis():
    return redis_client


# ── 基础缓存操作 ──────────────────────────────────────────


async def get_cached(key: str) -> dict | None:
    """获取缓存值，自动刷新LRU索引"""
    try:
        client = await get_redis()
        value = await client.get(key)
        if value:
            # 刷新LRU排序（score为当前时间戳）
            await client.zadd(CACHE_INDEX_KEY, {key: time.time()})
            return json.loads(value)
        return None
    except Exception as e:
        logger.error(f"Cache get error: {e}")
        return None


async def set_cached(key: str, value: dict, ttl: int = CACHE_TTL, tags: List[str] | None = None):
    """
    设置缓存，支持TTL过期和大小限制淘汰

    Args:
        key: 缓存键
        value: 缓存值
        ttl: 过期时间（秒），0表示不过期
        tags: 缓存标签，用于按标签批量失效
    """
    try:
        client = await get_redis()

        # 设置缓存值
        if ttl > 0:
            await client.setex(key, ttl, json.dumps(value))
        else:
            await client.set(key, json.dumps(value))

        # 更新LRU索引
        await client.zadd(CACHE_INDEX_KEY, {key: time.time()})

        # 更新标签索引（用于主动失效）
        if tags:
            for tag in tags:
                await client.sadd(f"cache_tag:{tag}", key)

        # 检查并执行淘汰
        await _evict_if_needed()
    except Exception as e:
        logger.error(f"Cache set error: {e}")


async def delete_cached(key: str):
    """删除缓存，同步清理索引"""
    try:
        client = await get_redis()
        await client.delete(key)
        await client.zrem(CACHE_INDEX_KEY, key)
    except Exception as e:
        logger.error(f"Cache delete error: {e}")


# ── 主动失效 ──────────────────────────────────────────────


async def invalidate_by_tag(tag: str) -> int:
    """
    按标签批量失效缓存

    Args:
        tag: 缓存标签（如模型名 "glm-4-flash"）

    Returns:
        被删除的缓存条目数
    """
    try:
        client = await get_redis()
        tag_key = f"cache_tag:{tag}"
        keys = await client.smembers(tag_key)

        if keys:
            pipe = client.pipeline()
            for key in keys:
                pipe.delete(key)
                pipe.zrem(CACHE_INDEX_KEY, key)
            await pipe.execute()
            await client.delete(tag_key)
            logger.info(f"Invalidated {len(keys)} cache entries by tag: {tag}")
            return len(keys)
        return 0
    except Exception as e:
        logger.error(f"Cache invalidate by tag error: {e}")
        return 0


async def invalidate_model_cache(model_name: str) -> int:
    """
    失效指定模型的所有缓存

    Args:
        model_name: 模型名称

    Returns:
        被删除的缓存条目数
    """
    return await invalidate_by_tag(f"model:{model_name}")


async def clear_all_cache() -> int:
    """清空所有LLM缓存"""
    try:
        client = await get_redis()
        keys = await client.zrange(CACHE_INDEX_KEY, 0, -1)
        if keys:
            pipe = client.pipeline()
            for key in keys:
                pipe.delete(key)
            pipe.delete(CACHE_INDEX_KEY)
            await pipe.execute()
            logger.info(f"Cleared {len(keys)} cache entries")
            return len(keys)
        return 0
    except Exception as e:
        logger.error(f"Cache clear all error: {e}")
        return 0


# ── LRU淘汰机制 ──────────────────────────────────────────


async def _evict_if_needed():
    """检查缓存大小，超过上限时按LRU策略淘汰"""
    try:
        client = await get_redis()
        current_size = await client.zcard(CACHE_INDEX_KEY)

        if current_size <= CACHE_MAX_ENTRIES:
            return

        # 计算需要淘汰的数量（淘汰超出部分的120%，避免频繁淘汰）
        evict_count = int((current_size - CACHE_MAX_ENTRIES) * 1.2) + 1

        # 按score（时间戳）升序，取最久未使用的
        old_keys = await client.zrange(CACHE_INDEX_KEY, 0, evict_count - 1)

        if old_keys:
            pipe = client.pipeline()
            for key in old_keys:
                pipe.delete(key)
                pipe.zrem(CACHE_INDEX_KEY, key)
            await pipe.execute()
            logger.info(f"LRU evicted {len(old_keys)} cache entries (size was {current_size})")
    except Exception as e:
        logger.error(f"Cache eviction error: {e}")


# ── 缓存统计 ──────────────────────────────────────────────


async def get_cache_info() -> Dict[str, Any]:
    """获取缓存详细信息"""
    try:
        client = await get_redis()
        current_size = await client.zcard(CACHE_INDEX_KEY)

        # 获取最旧和最新的缓存条目时间
        oldest = await client.zrange(CACHE_INDEX_KEY, 0, 0, withscores=True)
        newest = await client.zrange(CACHE_INDEX_KEY, -1, -1, withscores=True)

        oldest_time = oldest[0][1] if oldest else 0
        newest_time = newest[0][1] if newest else 0

        return {
            "total_entries": current_size,
            "max_entries": CACHE_MAX_ENTRIES,
            "usage_percent": round(current_size / CACHE_MAX_ENTRIES * 100, 2),
            "oldest_entry_ts": oldest_time,
            "newest_entry_ts": newest_time,
            "default_ttl": CACHE_TTL,
        }
    except Exception as e:
        logger.error(f"Cache info error: {e}")
        return {"error": str(e)}
