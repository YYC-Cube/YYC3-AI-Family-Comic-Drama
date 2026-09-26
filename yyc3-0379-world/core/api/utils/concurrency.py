# file: concurrency.py
# description: 并发处理工具模块
# author: YanYuCloudCube Team
# version: v1.0.0
# created: 2026-03-21
# updated: 2026-04-04
# status: active
# tags: [util],[concurrency],[async]

"""
@file: app/utils/concurrency.py
@description: 并发控制管理器，提供高效的并发控制功能
@author: YanYuCloudCube Team <admin@0379.email>
@version: v1.0.0
@created: 2026-03-19
@updated: 2026-03-19
@status: stable
@license: MIT
@copyright: Copyright (c) 2026 YanYuCloudCube Team
@tags: utils,python,concurrency,public
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Callable


class ConcurrencyLimiter:
    """并发控制器"""

    def __init__(self, max_concurrent: int = 10, queue_size: int = 100):
        self.max_concurrent = max_concurrent
        self.queue_size = queue_size

        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.queue = asyncio.Queue(maxsize=queue_size)

        self.stats = {"active": 0, "queued": 0, "rejected": 0, "completed": 0}

        self.logger = logging.getLogger(__name__)
        self.logger.info(
            f"Concurrency limiter initialized: max_concurrent={max_concurrent}, "
            f"queue_size={queue_size}"
        )

    async def acquire(self) -> bool:
        """获取并发许可"""
        try:
            await self.queue.put(None)
            self.stats["queued"] += 1
            await self.semaphore.acquire()
            self.stats["active"] += 1
            self.stats["queued"] -= 1
            return True
        except asyncio.QueueFull:
            self.stats["rejected"] += 1
            self.logger.warning("Concurrency limit reached, request rejected")
            return False

    async def release(self):
        """释放并发许可"""
        self.semaphore.release()
        self.stats["active"] -= 1
        self.stats["completed"] += 1

    def get_stats(self) -> dict:
        """获取并发统计"""
        return {
            "max_concurrent": self.max_concurrent,
            "active": self.stats["active"],
            "queued": self.stats["queued"],
            "rejected": self.stats["rejected"],
            "completed": self.stats["completed"],
        }

    @asynccontextmanager
    async def limit(self):
        """并发限制上下文管理器"""
        acquired = await self.acquire()
        if not acquired:
            raise Exception("Concurrency limit reached")

        try:
            yield
        finally:
            await self.release()

    async def run(self, func: Callable, *args, **kwargs) -> Any:
        """在并发限制下运行函数"""
        async with self.limit():
            return await func(*args, **kwargs)


concurrency_limiter = ConcurrencyLimiter(max_concurrent=10, queue_size=100)


async def limit_concurrency(func: Callable, max_concurrent: int = 10):
    """并发限制装饰器"""
    limiter = ConcurrencyLimiter(max_concurrent=max_concurrent)

    async def wrapper(*args, **kwargs):
        return await limiter.run(func, *args, **kwargs)

    return wrapper
