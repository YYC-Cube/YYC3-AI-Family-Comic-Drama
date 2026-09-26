# file: rag_service.py
# description: RAG 检索服务
# author: YanYuCloudCube Team
# version: v1.0.0
# created: 2026-04-08
# updated: 2026-04-08
# status: active
# tags: [service],[rag],[retrieval]

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SearchHistory
from app.services.embedding import embedding_service
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RAGService:
    """RAG 检索服务"""

    async def semantic_search(
        self,
        query: str,
        knowledge_base_ids: List[str],
        top_k: int = 5,
        threshold: float = 0.7,
        db: Optional[AsyncSession] = None,
    ) -> List[Dict[str, Any]]:
        """
        语义检索

        Args:
            query: 查询文本
            knowledge_base_ids: 知识库ID列表
            top_k: 返回结果数量
            threshold: 相似度阈值
            db: 数据库会话

        Returns:
            检索结果列表
        """
        query_embedding = await embedding_service.get_embedding_zhipu(query)

        if db is None:
            raise ValueError("semantic_search 需要 db 参数（AsyncSession）")

        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

        sql = text("""
            SELECT
                dc.id,
                dc.document_id,
                dc.knowledge_base_id,
                dc.chunk_index,
                dc.content,
                dc.token_count,
                d.title as document_title,
                kb.name as knowledge_base_name,
                1 - (dc.embedding <=> CAST(:embedding AS vector)) as similarity
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            JOIN knowledge_bases kb ON dc.knowledge_base_id = kb.id
            WHERE dc.knowledge_base_id = ANY(:kb_ids)
            AND 1 - (dc.embedding <=> CAST(:embedding AS vector)) >= :threshold
            ORDER BY dc.embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
        """)

        result = await db.execute(
            sql,
            {
                "embedding": embedding_str,
                "kb_ids": knowledge_base_ids,
                "threshold": threshold,
                "limit": top_k,
            },
        )
        rows = result.fetchall()

        results = []
        for row in rows:
            results.append(
                {
                    "chunk_id": row.id,
                    "document_id": row.document_id,
                    "knowledge_base_id": row.knowledge_base_id,
                    "chunk_index": row.chunk_index,
                    "content": row.content,
                    "token_count": row.token_count,
                    "document_title": row.document_title,
                    "knowledge_base_name": row.knowledge_base_name,
                    "similarity": float(row.similarity),
                }
            )

        return results

    async def hybrid_search(
        self,
        query: str,
        knowledge_base_ids: List[str],
        top_k: int = 5,
        keyword_weight: float = 0.3,
        semantic_weight: float = 0.7,
        db: Optional[AsyncSession] = None,
    ) -> List[Dict[str, Any]]:
        """
        混合检索（关键词 + 语义）

        Args:
            query: 查询文本
            knowledge_base_ids: 知识库ID列表
            top_k: 返回结果数量
            keyword_weight: 关键词权重
            semantic_weight: 语义权重
            db: 数据库会话

        Returns:
            检索结果列表
        """
        semantic_results = await self.semantic_search(query, knowledge_base_ids, top_k * 2, 0.5, db)

        keywords = query.lower().split()
        keyword_results = []

        keyword_sql = text("""
            SELECT
                dc.id,
                dc.document_id,
                dc.knowledge_base_id,
                dc.chunk_index,
                dc.content,
                dc.token_count,
                d.title as document_title,
                kb.name as knowledge_base_name
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            JOIN knowledge_bases kb ON dc.knowledge_base_id = kb.id
            WHERE dc.knowledge_base_id = ANY(:kb_ids)
            AND dc.content ILIKE ANY(:keywords)
            LIMIT :limit
        """)

        keyword_patterns = [f"%{kw}%" for kw in keywords]
        if db is None:
            raise ValueError("hybrid_search 需要 db 参数（AsyncSession）")
        keyword_result = await db.execute(
            keyword_sql,
            {
                "kb_ids": knowledge_base_ids,
                "keywords": keyword_patterns,
                "limit": top_k,
            },
        )
        keyword_rows = keyword_result.fetchall()

        for row in keyword_rows:
            keyword_results.append(
                {
                    "chunk_id": row.id,
                    "document_id": row.document_id,
                    "knowledge_base_id": row.knowledge_base_id,
                    "chunk_index": row.chunk_index,
                    "content": row.content,
                    "token_count": row.token_count,
                    "document_title": row.document_title,
                    "knowledge_base_name": row.knowledge_base_name,
                    "keyword_match": True,
                }
            )

        merged = {}
        for result in semantic_results:
            chunk_id = result["chunk_id"]
            merged[chunk_id] = result
            merged[chunk_id]["score"] = semantic_weight * result["similarity"]

        for result in keyword_results:
            chunk_id = result["chunk_id"]
            if chunk_id in merged:
                merged[chunk_id]["score"] += keyword_weight
                merged[chunk_id]["keyword_match"] = True
            else:
                result["score"] = keyword_weight
                result["similarity"] = 0.0
                merged[chunk_id] = result

        sorted_results = sorted(merged.values(), key=lambda x: x["score"], reverse=True)

        return sorted_results[:top_k]

    async def save_search_history(
        self,
        knowledge_base_id: str,
        query: str,
        result_count: int,
        response_time_ms: int,
        model_used: str,
        user_id: Optional[str],
        db: AsyncSession,
    ):
        """
        保存检索历史

        Args:
            knowledge_base_id: 知识库ID
            query: 查询文本
            result_count: 结果数量
            response_time_ms: 响应时间（毫秒）
            model_used: 使用的模型
            user_id: 用户ID
            db: 数据库会话
        """
        query_embedding = await embedding_service.get_embedding_zhipu(query)

        history = SearchHistory(
            id=str(uuid.uuid4()),
            knowledge_base_id=knowledge_base_id,
            query=query,
            query_embedding=query_embedding,
            result_count=result_count,
            response_time_ms=response_time_ms,
            model_used=model_used,
            user_id=user_id,
        )
        db.add(history)
        await db.commit()


rag_service = RAGService()
