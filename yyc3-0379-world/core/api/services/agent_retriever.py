# file: agent_retriever.py
# description: PGVectorRetriever - core.agents.Retriever 协议的 pgvector 适配器（Phase 1 适配点 A2）
# author: YanYuCloudCube Team <admin@0379.email>
# created: 2026-09-25
# status: active
# tags: [agent],[rag],[retriever],[pgvector]

"""Agent 知识检索的 pgvector 轨道适配器（对齐 core.agents.retriever.Retriever 协议）。

设计要点（可行性报告 3.2-A2）：
- 结构化符合协议：不 import core.agents（Protocol 为 runtime_checkable 结构类型），
  依赖方向保持 app → core.agents 单向，core/agents 保持零项目耦合
- 注入式检索：search_fn 默认绑 rag_service.semantic_search（复用既有 embedding + pgvector SQL），
  测试注入 async 假实现即可，零 DB 依赖
- sync/async 双轨：协议是同步签名；asearch 供 Phase 2 异步编排直用，
  search 经 asyncio.run 桥接（仅在无事件循环线程中调用，如 API 层 asyncio.to_thread 内的编排器）
- 检索结果契约映射：[{"content", "source", "category", "score"}]
  ← content / document_title / knowledge_base_name / similarity
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)


class PGVectorRetriever:
    """pgvector 知识域检索器（平台文档轨；企业知识 Milvus 轨待 Phase 3 规模评估后引入）。"""

    def __init__(
        self,
        knowledge_base_ids: List[str],
        search_fn=None,
    ):
        """初始化检索器。

        :param knowledge_base_ids: 可用知识库 ID 列表（空列表 = 知识域未配置，降级返回空）
        :param search_fn: 异步检索函数，签名对齐 rag_service.semantic_search
            (query, kb_ids, top_k, threshold, db) -> list[dict]；默认绑 rag_service
        """
        self.knowledge_base_ids = list(knowledge_base_ids or [])
        self._search_fn = search_fn or rag_service.semantic_search

    async def asearch(
        self,
        query: str,
        top_k: int = 5,
        category_filter: Optional[str] = None,
        min_score: float = 0.6,
    ) -> List[Dict[str, Any]]:
        """异步检索（Phase 2 异步编排原生入口）。"""
        if not self.knowledge_base_ids or not query.strip():
            return []
        try:
            rows = await self._search_fn(
                query,
                self.knowledge_base_ids,
                top_k,
                max(min_score, 0.0),
                None,
            )
        except Exception as exc:
            logger.warning("[PGVectorRetriever] 检索失败，降级空上下文: %s", exc)
            return []

        results = [
            {
                "content": row["content"],
                "source": row.get("document_title", ""),
                "category": row.get("knowledge_base_name", ""),
                "score": float(row.get("similarity", 0.0)),
            }
            for row in rows
        ]
        if category_filter:
            results = [r for r in results if category_filter in r["category"]]
        return results

    def search(
        self,
        query: str,
        top_k: int = 5,
        category_filter: Optional[str] = None,
        min_score: float = 0.6,
    ) -> List[Dict[str, Any]]:
        """同步桥（满足 core.agents.Retriever 协议；须在无事件循环线程中调用）。

        API 层经 asyncio.to_thread 运行编排器时，工作线程无 running loop，
        asyncio.run 在此上下文安全；若在事件循环线程误用将抛 RuntimeError（显式失败优于隐式阻塞）。
        """
        return asyncio.run(self.asearch(query, top_k, category_filter, min_score))
