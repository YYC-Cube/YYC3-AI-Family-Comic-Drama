# file: retriever.py
# description: 公共RAG统一检索接口协议（ReAct-C Step3 契约）——Phase 0 接口层
# author: YanYuCloudCube Team <admin@0379.email>
# created: 2026-09-25
# status: active
# tags: [agent],[rag],[retriever],[protocol]

"""公共 RAG 统一检索契约（对齐总规范第二章「统一检索入口规范」）。

Phase 0 仅定义协议与降级实现，规避向量库三轨碎片化（可行性报告适配点 A2）：
- Phase 1 适配：PGVectorRetriever（复用网关 rag_service + embedding 服务）
- Phase 3 评估：MilvusRetriever（向量规模触发后再引入，docs 原型迁移为适配器）

返回结构契约：[{"content", "source", "category", "score"}, ...]，score ≥ min_score 才入上下文。
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class Retriever(Protocol):
    """统一知识检索接口协议。"""

    def search(  # noqa: E704 — black 强制折叠省略体，noqa 在语句首行生效
        self,
        query: str,
        top_k: int = 5,
        category_filter: str | None = None,
        min_score: float = 0.6,
    ) -> list[dict]: ...


class NullRetriever:
    """空检索实现：知识库未接入时的默认降级（返回空上下文，九步链路不中断）。"""

    def search(
        self,
        query: str,
        top_k: int = 5,
        category_filter: str | None = None,
        min_score: float = 0.6,
    ) -> list[dict]:
        """空检索：返回空上下文，语义契约与协议方法一致。"""
        return []
