# file: db.py
# description: 数据库连接和操作模块
# author: YanYuCloudCube Team
# version: v1.0.0
# created: 2026-03-21
# updated: 2026-04-04
# status: active
# tags: [database],[postgresql],[connection]

"""
@file: app/db.py
@description: 数据库模块，提供 PostgreSQL 数据库连接和操作
@author: YanYuCloudCube Team <admin@0379.email>
@version: v1.0.0
@created: 2026-03-13
@updated: 2026-03-13
@status: stable
@license: MIT
@copyright: Copyright (c) 2026 YanYuCloudCube Team
@tags: db,python,postgresql,core,public
"""

import os
from datetime import datetime
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship

from app.config import settings

Base = declarative_base()

# DATABASE_URL 环境变量可整体覆盖（本地 e2e/开发无 PG 时用 sqlite+aiosqlite；生产保持默认组装）
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql+asyncpg://{settings.db_user}:{settings.db_password}"
    f"@{settings.db_host}:{settings.db_port}/{settings.db_name}",
)

echo_sql = os.getenv("ENVIRONMENT", "production") != "production"
engine = create_async_engine(DATABASE_URL, echo=echo_sql)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    backend_type: Mapped[str] = mapped_column(String, nullable=False)
    backend_name: Mapped[str] = mapped_column(String, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UsageLog(Base):
    __tablename__ = "usage_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model: Mapped[str] = mapped_column(String, nullable=False)
    backend_type: Mapped[str] = mapped_column(String, nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    user_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_usage_log_model", "model"),
        Index("idx_usage_log_created_at", "created_at"),
        Index("idx_usage_log_backend_type", "backend_type"),
        Index("idx_usage_log_model_created", "model", "created_at"),
    )


class KnowledgeBase(Base):
    """知识库表"""

    __tablename__ = "knowledge_bases"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    embedding_model: Mapped[str] = mapped_column(String(50), default="embedding-3")
    icon: Mapped[str] = mapped_column(String(50), default="book")
    background: Mapped[str] = mapped_column(String(50), default="blue")
    status: Mapped[str] = mapped_column(String(20), default="active")
    document_count: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    storage_size: Mapped[int] = mapped_column(BigInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(255))
    extra_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSONB)

    documents = relationship(
        "Document", back_populates="knowledge_base", cascade="all, delete-orphan"
    )


class Document(Base):
    """文档表"""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    knowledge_base_id: Mapped[str] = mapped_column(
        String, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    file_path: Mapped[Optional[str]] = mapped_column(Text)
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger)
    file_type: Mapped[Optional[str]] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    extra_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSONB)

    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    """文档切片表"""

    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    document_id: Mapped[str] = mapped_column(
        String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    knowledge_base_id: Mapped[str] = mapped_column(
        String, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[list]] = mapped_column(Vector(1536))
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    extra_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="chunks")


class QAPair(Base):
    """问答对表"""

    __tablename__ = "qa_pairs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    knowledge_base_id: Mapped[str] = mapped_column(
        String, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    question_embedding: Mapped[Optional[list]] = mapped_column(Vector(1536))
    extra_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class SearchHistory(Base):
    """检索历史表"""

    __tablename__ = "search_history"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    knowledge_base_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("knowledge_bases.id", ondelete="CASCADE")
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    query_embedding: Mapped[Optional[list]] = mapped_column(Vector(1536))
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    model_used: Mapped[Optional[str]] = mapped_column(String(100))
    user_id: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_model_backend(model_name: str) -> tuple[str, str]:
    async with async_session() as session:
        from sqlalchemy import select

        result = await session.execute(
            select(ModelRegistry.backend_name, ModelRegistry.backend_type).where(
                ModelRegistry.id == model_name
            )
        )
        row = result.first()
        if not row:
            raise ValueError(f"Model {model_name} not found in registry")
        return row.backend_name, row.backend_type


async def log_usage(
    model: str,
    backend_type: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    user_id: str | None = None,
):
    async with async_session() as session:
        log = UsageLog(
            model=model,
            backend_type=backend_type,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            user_id=user_id,
        )
        session.add(log)
        await session.commit()
