# ==============================================================
# Milvus 向量检索引擎 v1.0（公共 RAG 能力）
# 对接模型：nemotron-3-embed-1b（DGX1 嵌入服务，2048维）
# 对接存储：Milvus 2.4.5 分布式向量库（节点2）
# 功能：知识库入库 / 语义检索 / 元数据过滤 / 相似度排序 / 来源溯源
# 对齐架构：ReAct-C Step3 知识检索与上下文注入
# 依赖：pip install pymilvus==2.4.5 python-dotenv openai
# ==============================================================
import os
from dotenv import load_dotenv
from openai import OpenAI
from pymilvus import (connections, utility, Collection,
                      CollectionSchema, FieldSchema, DataType)

load_dotenv()


class MilvusRetriever:
    """统一知识检索入口：支持相似度检索、元数据过滤、来源溯源"""

    def __init__(self):
        # 连接Milvus（DGX1查询节点地址）
        connections.connect(
            alias="default",
            host=os.getenv("MILVUS_HOST", "10.0.0.11"),
            port=int(os.getenv("MILVUS_PORT", 19530)),
        )

        # 初始化嵌入模型客户端
        self.embed_client = OpenAI(
            base_url=os.getenv("DGX1_EMBED_URL", "http://10.0.0.11:8001/v1"),
            api_key="nim-local-dummy",
        )
        self.embed_model_name = "nemotron-3-embed-1b"
        self.vector_dim = 2048  # nemotron-3-embed-1b 输出维度

        # 集合名称（代码知识库+通用文档知识库分开存储可扩展）
        self.collection_name = "yyc3_knowledge_base"
        self._init_collection()

    def _init_collection(self):
        """初始化知识库集合结构，不存在则自动创建"""
        if utility.has_collection(self.collection_name):
            self.collection = Collection(self.collection_name)
            self.collection.load()
            return

        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.vector_dim),
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=512),   # 来源/文件名
            FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=128), # 分类：经营/技术/管理
            FieldSchema(name="create_time", dtype=DataType.VARCHAR, max_length=64),
        ]

        schema = CollectionSchema(fields, description="YYC³ AI FAmily 企业知识库")
        self.collection = Collection(self.collection_name, schema)

        # IVF_FLAT索引，平衡检索速度与精度
        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "COSINE",
            "params": {"nlist": 1024},
        }
        self.collection.create_index(field_name="embedding", index_params=index_params)
        self.collection.load()
        print(f"[Milvus] 知识库集合 {self.collection_name} 初始化完成")

    def get_embedding(self, text: str) -> list:
        """调用NIM嵌入模型生成向量"""
        response = self.embed_client.embeddings.create(
            model=self.embed_model_name, input=text
        )
        return response.data[0].embedding

    def insert_documents(self, docs: list):
        """批量插入文档

        :param docs: [{"content", "source", "category", "create_time"}, ...]
        """
        contents, embeddings, sources, categories, times = [], [], [], [], []
        for doc in docs:
            contents.append(doc["content"])
            embeddings.append(self.get_embedding(doc["content"]))
            sources.append(doc.get("source", "unknown"))
            categories.append(doc.get("category", "general"))
            times.append(doc.get("create_time", ""))

        self.collection.insert([contents, embeddings, sources, categories, times])
        self.collection.flush()
        print(f"[Milvus] 成功插入 {len(docs)} 条文档")

    def search(self, query: str, top_k: int = 5, category_filter: str = None,
               min_score: float = 0.6) -> list:
        """语义检索，返回最相关文档片段（带来源，供溯源）

        :param min_score: 最低相似度阈值（质量红线：低于阈值不入上下文）
        :return: [{"content", "source", "category", "score"}, ...]
        """
        query_vector = self.get_embedding(query)

        expr = f'category == "{category_filter}"' if category_filter else None
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 32}}

        results = self.collection.search(
            data=[query_vector],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=expr,
            output_fields=["content", "source", "category"],
        )

        matched_docs = []
        for hit in results[0]:
            if hit.score >= min_score:
                matched_docs.append({
                    "content": hit.entity.get("content"),
                    "source": hit.entity.get("source"),
                    "category": hit.entity.get("category"),
                    "score": round(float(hit.score), 4),
                })

        print(f"[Milvus检索] 命中 {len(matched_docs)} 条相关文档（阈值{min_score}）")
        return matched_docs

    def delete_by_source(self, source_name: str):
        """按来源删除文档，用于知识库更新"""
        self.collection.delete(f'source == "{source_name}"')
        print(f"[Milvus] 已删除来源为 {source_name} 的所有文档")


# -------------------------- 批量入库（对接NAS存储） --------------------------
def batch_import_from_nas(retriever: MilvusRetriever,
                          nas_path: str = "/mnt/nas/raid6-knowledge",
                          category: str = "经营"):
    """定时从NAS RAID6原始知识库目录读取文件，分块入库（自动化更新链路）"""
    import time as _time
    all_docs = []
    for filename in os.listdir(nas_path):
        if filename.endswith(".txt") or filename.endswith(".md"):
            filepath = os.path.join(nas_path, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            # 按段落分块（生产环境建议用语义分块）
            for chunk in content.split("\n\n"):
                if len(chunk.strip()) > 50:
                    all_docs.append({
                        "content": chunk.strip(),
                        "source": filename,
                        "category": category,
                        "create_time": _time.strftime(
                            "%Y-%m-%d %H:%M:%S", _time.localtime(os.path.getmtime(filepath))
                        ),
                    })
    retriever.insert_documents(all_docs)
    print(f"批量入库完成，共{len(all_docs)}个文本块")


# -------------------------- 快速测试 --------------------------
if __name__ == "__main__":
    retriever = MilvusRetriever()

    test_docs = [
        {
            "content": "2026年Q2公司营收同比增长32%，其中云业务占比65%，企业级客户增速最快",
            "source": "2026Q2经营报告.pdf",
            "category": "经营",
            "create_time": "2026-07-01",
        },
        {
            "content": "研发团队当前共120人，本季度新增15人，人员扩张率14%，核心岗位招聘完成率92%",
            "source": "2026Q2人力资源报告.pdf",
            "category": "管理",
            "create_time": "2026-07-05",
        },
    ]
    retriever.insert_documents(test_docs)

    results = retriever.search("本季度营收情况怎么样", top_k=3)
    for doc in results:
        print(f"相似度{doc['score']} | 来源：{doc['source']}")
        print(f"内容：{doc['content']}\n")
