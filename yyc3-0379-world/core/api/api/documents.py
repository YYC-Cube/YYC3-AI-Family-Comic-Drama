# file: documents.py
# description: 文档管理 API 接口
# author: YanYuCloudCube Team
# version: v1.0.0
# created: 2026-04-08
# updated: 2026-08-29
# status: active
# tags: [api],[documents],[rag]

import os
import uuid
from datetime import datetime
from typing import List, Optional

import aiofiles
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
)
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.db_access import Document, DocumentChunk, KnowledgeBase, get_db

router = APIRouter(prefix="/v1/documents")


class DocumentCreate(BaseModel):
    knowledge_base_id: str = Field(..., description="知识库ID")
    title: str = Field(..., description="文档标题")
    source_type: str = Field(..., description="来源类型")
    source_url: Optional[str] = Field(None, description="来源URL")
    file_type: Optional[str] = Field(None, description="文件类型")


class DocumentResponse(BaseModel):
    id: str
    knowledge_base_id: str
    title: str
    source_type: str
    source_url: Optional[str]
    file_path: Optional[str]
    file_size: Optional[int]
    file_type: Optional[str]
    status: str
    chunk_count: int
    total_tokens: int
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentChunkResponse(BaseModel):
    id: str
    document_id: str
    knowledge_base_id: str
    chunk_index: int
    content: str
    token_count: int
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/upload", response_model=DocumentResponse, summary="上传文档")
async def upload_document(
    background_tasks: BackgroundTasks,
    knowledge_base_id: str = Query(..., description="知识库ID"),
    file: UploadFile = File(..., description="文档文件"),
    db: AsyncSession = Depends(get_db),
):
    """
    上传文档到知识库

    支持的文件格式：
    - PDF (.pdf)
    - Word (.docx, .doc)
    - Markdown (.md)
    - 文本文件 (.txt)
    - 代码文件 (.py, .js, .java, etc.)

    上传后会自动进行：
    1. 文档解析
    2. 文本切片
    3. 向量化
    """
    kb_query = select(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id)
    kb_result = await db.execute(kb_query)
    kb = kb_result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    # 安全校验：文件名、类型、大小
    safe_kb_id = knowledge_base_id.replace("/", "").replace("\\", "").replace("..", "")
    safe_filename = os.path.basename(file.filename or "")
    if not safe_filename:
        raise HTTPException(status_code=400, detail="无效的文件名")

    ALLOWED_EXTENSIONS = {
        ".pdf",
        ".docx",
        ".doc",
        ".md",
        ".txt",
        ".py",
        ".js",
        ".java",
        ".csv",
        ".json",
    }
    file_ext = os.path.splitext(safe_filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file_ext}")

    # 文件大小限制（10MB）
    MAX_FILE_SIZE = 10 * 1024 * 1024
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="文件超过 10MB 大小限制")

    upload_dir = f"/tmp/knowledge_base/{safe_kb_id}"
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, safe_filename)
    # 二次校验：确保最终路径在 upload_dir 内
    if not os.path.realpath(file_path).startswith(os.path.realpath(upload_dir)):
        raise HTTPException(status_code=400, detail="非法的文件路径")
    async with aiofiles.open(file_path, "wb") as out_file:
        await out_file.write(content)

    file_size = len(content)
    file_type = file_ext

    doc = Document(
        id=str(uuid.uuid4()),
        knowledge_base_id=safe_kb_id,
        title=safe_filename,
        source_type="upload",
        file_path=file_path,
        file_size=file_size,
        file_type=file_type,
        status="pending",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    from app.services.document_processor import process_document_task

    background_tasks.add_task(process_document_task, doc.id, db)

    return doc


@router.post("", response_model=DocumentResponse, summary="创建文档记录")
async def create_document(doc_data: DocumentCreate, db: AsyncSession = Depends(get_db)):
    """
    创建文档记录（用于 URL 或其他来源）

    - **knowledge_base_id**: 知识库ID（必填）
    - **title**: 文档标题（必填）
    - **source_type**: 来源类型（url, upload, manual）
    - **source_url**: 来源URL（可选）
    - **file_type**: 文件类型（可选）
    """
    kb_query = select(KnowledgeBase).where(KnowledgeBase.id == doc_data.knowledge_base_id)
    kb_result = await db.execute(kb_query)
    kb = kb_result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    doc = Document(
        id=str(uuid.uuid4()),
        knowledge_base_id=doc_data.knowledge_base_id,
        title=doc_data.title,
        source_type=doc_data.source_type,
        source_url=doc_data.source_url,
        file_type=doc_data.file_type,
        status="pending",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


@router.get("", response_model=List[DocumentResponse], summary="获取文档列表")
async def list_documents(
    knowledge_base_id: Optional[str] = Query(None, description="知识库ID"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取文档列表

    - **knowledge_base_id**: 按知识库筛选
    - **status**: 按状态筛选（pending, processing, completed, failed）
    - **limit**: 返回数量限制（1-100）
    - **offset**: 偏移量
    """
    query = select(Document)
    if knowledge_base_id:
        query = query.where(Document.knowledge_base_id == knowledge_base_id)
    if status:
        query = query.where(Document.status == status)
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    docs = result.scalars().all()
    return docs


@router.get("/{doc_id}", response_model=DocumentResponse, summary="获取文档详情")
async def get_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    """
    获取指定文档的详细信息
    """
    query = select(Document).where(Document.id == doc_id)
    result = await db.execute(query)
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return doc


@router.get(
    "/{doc_id}/chunks",
    response_model=List[DocumentChunkResponse],
    summary="获取文档切片列表",
)
async def list_document_chunks(
    doc_id: str,
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取文档的所有切片
    """
    doc_query = select(Document).where(Document.id == doc_id)
    doc_result = await db.execute(doc_query)
    doc = doc_result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    query = (
        select(DocumentChunk)
        .where(DocumentChunk.document_id == doc_id)
        .order_by(DocumentChunk.chunk_index)
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    chunks = result.scalars().all()
    return chunks


@router.delete("/{doc_id}", summary="删除文档")
async def delete_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    """
    删除文档及其所有切片

    ⚠️ 此操作不可恢复
    """
    query = select(Document).where(Document.id == doc_id)
    result = await db.execute(query)
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    if doc.file_path and os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    await db.delete(doc)
    await db.commit()
    return {"message": "文档已删除", "id": doc_id}


@router.post("/{doc_id}/reprocess", summary="重新处理文档")
async def reprocess_document(
    doc_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    重新处理文档（解析、切片、向量化）
    """
    query = select(Document).where(Document.id == doc_id)
    result = await db.execute(query)
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    doc.status = "pending"
    doc.error_message = None
    await db.commit()

    from app.services.document_processor import process_document_task

    background_tasks.add_task(process_document_task, doc.id, db)

    return {"message": "文档重新处理已启动", "id": doc_id}
