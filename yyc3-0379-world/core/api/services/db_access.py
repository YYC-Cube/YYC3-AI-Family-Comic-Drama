# file: db_access.py
# description: DB 会话与模型合规出口 - api 层经此访问 ORM（importlinter 分层契约：api 禁直连 app.db）
# author: YanYuCloudCube Team
# created: 2026-09-20
# status: active
# tags: [db],[session],[layering]

"""api 层 DB 访问的合规入口：api → services.db_access → db。

仅做命名再导出（re-export），禁止在此堆业务逻辑。
- get_db: FastAPI Depends 用的会话工厂（等价直接 Depends(async_session)）
- ORM 模型：KnowledgeBase / Document / DocumentChunk
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Document, DocumentChunk, KnowledgeBase, async_session

__all__ = ["get_db", "AsyncSession", "KnowledgeBase", "Document", "DocumentChunk"]


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖注入用会话：请求结束自动关闭"""
    async with async_session() as session:
        yield session
