# file: knowledge_base.py
# description: 知识库管理 API 接口
# author: YanYuCloudCube Team
# version: v1.0.0
# created: 2026-04-08
# updated: 2026-04-08
# status: active
# tags: [api],[knowledge-base],[rag]

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.db_access import Document, DocumentChunk, KnowledgeBase, get_db

router = APIRouter(prefix="/v1/knowledge-bases")


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(..., description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")
    embedding_model: str = Field(default="embedding-3", description="嵌入模型")
    icon: str = Field(default="book", description="图标")
    background: str = Field(default="blue", description="背景色")
    created_by: Optional[str] = Field(None, description="创建者")


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    embedding_model: Optional[str] = None
    icon: Optional[str] = None
    background: Optional[str] = None
    status: Optional[str] = None


class KnowledgeBaseResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    embedding_model: str
    icon: str
    background: str
    status: str
    document_count: int
    total_tokens: int
    storage_size: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]

    class Config:
        from_attributes = True


@router.post("", response_model=KnowledgeBaseResponse, summary="创建知识库")
async def create_knowledge_base(kb_data: KnowledgeBaseCreate, db: AsyncSession = Depends(get_db)):
    """
    创建新的知识库

    - **name**: 知识库名称（必填）
    - **description**: 知识库描述
    - **embedding_model**: 嵌入模型（默认：embedding-3）
    - **icon**: 图标（默认：book）
    - **background**: 背景色（默认：blue）
    """
    kb = KnowledgeBase(
        id=str(uuid.uuid4()),
        name=kb_data.name,
        description=kb_data.description,
        embedding_model=kb_data.embedding_model,
        icon=kb_data.icon,
        background=kb_data.background,
        created_by=kb_data.created_by,
    )
    db.add(kb)
    await db.commit()
    await db.refresh(kb)
    return kb


@router.get("", response_model=List[KnowledgeBaseResponse], summary="获取知识库列表")
async def list_knowledge_bases(
    status: Optional[str] = Query(None, description="按状态筛选"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取知识库列表

    - **status**: 按状态筛选（active, inactive）
    - **limit**: 返回数量限制（1-100）
    - **offset**: 偏移量
    """
    query = select(KnowledgeBase)
    if status:
        query = query.where(KnowledgeBase.status == status)
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    kbs = result.scalars().all()
    return kbs


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse, summary="获取知识库详情")
async def get_knowledge_base(kb_id: str, db: AsyncSession = Depends(get_db)):
    """
    获取指定知识库的详细信息
    """
    query = select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    result = await db.execute(query)
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return kb


@router.patch("/{kb_id}", response_model=KnowledgeBaseResponse, summary="更新知识库")
async def update_knowledge_base(
    kb_id: str, kb_data: KnowledgeBaseUpdate, db: AsyncSession = Depends(get_db)
):
    """
    更新知识库信息

    只需提供需要更新的字段
    """
    query = select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    result = await db.execute(query)
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    update_data = kb_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(kb, key, value)

    await db.commit()
    await db.refresh(kb)
    return kb


@router.delete("/{kb_id}", summary="删除知识库")
async def delete_knowledge_base(kb_id: str, db: AsyncSession = Depends(get_db)):
    """
    删除知识库及其所有文档和切片

    ⚠️ 此操作不可恢复
    """
    query = select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    result = await db.execute(query)
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    await db.delete(kb)
    await db.commit()
    return {"message": "知识库已删除", "id": kb_id}


@router.get("/{kb_id}/stats", summary="获取知识库统计信息")
async def get_knowledge_base_stats(kb_id: str, db: AsyncSession = Depends(get_db)):
    """
    获取知识库的统计信息

    包括文档数量、切片数量、总 Token 数等
    """
    query = select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    result = await db.execute(query)
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    doc_query = select(Document).where(Document.knowledge_base_id == kb_id)
    doc_result = await db.execute(doc_query)
    documents = doc_result.scalars().all()

    chunk_query = select(DocumentChunk).where(DocumentChunk.knowledge_base_id == kb_id)
    chunk_result = await db.execute(chunk_query)
    chunks = chunk_result.scalars().all()

    return {
        "knowledge_base_id": kb_id,
        "knowledge_base_name": kb.name,
        "document_count": len(documents),
        "chunk_count": len(chunks),
        "total_tokens": kb.total_tokens,
        "storage_size": kb.storage_size,
        "documents_by_status": {
            "pending": len([d for d in documents if d.status == "pending"]),
            "processing": len([d for d in documents if d.status == "processing"]),
            "completed": len([d for d in documents if d.status == "completed"]),
            "failed": len([d for d in documents if d.status == "failed"]),
        },
    }
