# file: rag.py
# description: RAG 检索 API 接口
# author: YanYuCloudCube Team
# version: v1.0.0
# created: 2026-04-08
# updated: 2026-04-08
# status: active
# tags: [api],[rag],[retrieval]

import time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.db_access import get_db
from app.services.rag_service import rag_service

router = APIRouter(prefix="/v1/rag")


class SearchRequest(BaseModel):
    query: str = Field(..., description="查询文本")
    knowledge_base_ids: List[str] = Field(..., description="知识库ID列表")
    top_k: int = Field(default=5, ge=1, le=20, description="返回结果数量")
    threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="相似度阈值")
    search_type: str = Field(default="semantic", description="检索类型：semantic 或 hybrid")


class SearchResult(BaseModel):
    chunk_id: str
    document_id: str
    knowledge_base_id: str
    chunk_index: int
    content: str
    token_count: int
    document_title: str
    knowledge_base_name: str
    similarity: float
    score: Optional[float] = None
    keyword_match: Optional[bool] = None


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_count: int
    response_time_ms: int


@router.post("/search", response_model=SearchResponse, summary="RAG 检索")
async def search(
    request: SearchRequest,
    user_id: Optional[str] = Query(None, description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    执行 RAG 检索

    - **query**: 查询文本（必填）
    - **knowledge_base_ids**: 知识库ID列表（必填）
    - **top_k**: 返回结果数量（1-20，默认5）
    - **threshold**: 相似度阈值（0-1，默认0.7）
    - **search_type**: 检索类型（semantic 或 hybrid，默认 semantic）

    ### 检索类型说明：
    - **semantic**: 纯语义检索，使用向量相似度
    - **hybrid**: 混合检索，结合关键词和语义相似度
    """
    start_time = time.time()

    if request.search_type == "semantic":
        results = await rag_service.semantic_search(
            query=request.query,
            knowledge_base_ids=request.knowledge_base_ids,
            top_k=request.top_k,
            threshold=request.threshold,
            db=db,
        )
    elif request.search_type == "hybrid":
        results = await rag_service.hybrid_search(
            query=request.query,
            knowledge_base_ids=request.knowledge_base_ids,
            top_k=request.top_k,
            db=db,
        )
    else:
        raise HTTPException(status_code=400, detail=f"不支持的检索类型: {request.search_type}")

    response_time_ms = int((time.time() - start_time) * 1000)

    for kb_id in request.knowledge_base_ids:
        await rag_service.save_search_history(
            knowledge_base_id=kb_id,
            query=request.query,
            result_count=len(results),
            response_time_ms=response_time_ms,
            model_used="embedding-3",
            user_id=user_id,
            db=db,
        )

    return SearchResponse(
        query=request.query,
        results=[SearchResult(**result) for result in results],
        total_count=len(results),
        response_time_ms=response_time_ms,
    )


@router.post("/ask", summary="基于知识库的问答")
async def ask_with_context(
    request: SearchRequest,
    user_id: Optional[str] = Query(None, description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    基于知识库的问答

    1. 执行语义检索获取相关文档片段
    2. 构建包含上下文的提示词
    3. 调用大模型生成答案

    - **query**: 问题（必填）
    - **knowledge_base_ids**: 知识库ID列表（必填）
    - **top_k**: 检索结果数量（1-20，默认5）
    """
    start_time = time.time()

    results = await rag_service.semantic_search(
        query=request.query,
        knowledge_base_ids=request.knowledge_base_ids,
        top_k=request.top_k,
        threshold=0.6,
        db=db,
    )

    if not results:
        return {
            "query": request.query,
            "answer": "抱歉，我在知识库中没有找到相关信息。",
            "sources": [],
            "response_time_ms": int((time.time() - start_time) * 1000),
        }

    context_parts = []
    for i, result in enumerate(results, 1):
        context_parts.append(f"[文档{i}] {result['document_title']}\n{result['content']}\n")

    context = "\n".join(context_parts)

    prompt = f"""基于以下知识库内容回答问题。如果知识库中没有相关信息，请明确说明。

知识库内容：
{context}

问题：{request.query}

请提供准确、详细的回答，并在回答中引用相关的文档来源。"""

    from starlette.requests import Request as StarletteRequest

    from app.api.chat import chat_completion
    from app.api.schemas import CompletionRequest, Message

    chat_request = CompletionRequest(
        model="glm-4-flash",
        messages=[Message(role="user", content=prompt)],
        temperature=0.7,
        max_tokens=2000,
        top_p=None,
        user_id=user_id,
        stream=False,
    )

    # chat_completion 第二参数是 FastAPI Request，用于 metrics
    fake_request = StarletteRequest(scope={"type": "http", "method": "POST", "headers": []})
    response = await chat_completion(chat_request, fake_request)

    response_time_ms = int((time.time() - start_time) * 1000)

    for kb_id in request.knowledge_base_ids:
        await rag_service.save_search_history(
            knowledge_base_id=kb_id,
            query=request.query,
            result_count=len(results),
            response_time_ms=response_time_ms,
            model_used="glm-4-flash",
            user_id=user_id,
            db=db,
        )

    answer = ""
    if isinstance(response, dict):
        answer = response.get("choices", [{}])[0].get("message", {}).get("content", "")
    else:
        answer = str(response)

    return {
        "query": request.query,
        "answer": answer,
        "sources": [
            {
                "document_title": result["document_title"],
                "chunk_index": result["chunk_index"],
                "similarity": result["similarity"],
            }
            for result in results
        ],
        "response_time_ms": response_time_ms,
    }
