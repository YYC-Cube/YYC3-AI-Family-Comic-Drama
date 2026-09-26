# file: embedding.py
# description: 向量化服务
# author: YanYuCloudCube Team
# version: v1.0.0
# created: 2026-04-08
# updated: 2026-04-08
# status: active
# tags: [service],[embedding],[rag]

from typing import List

import httpx
import numpy as np

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """向量化服务"""

    def __init__(self):
        self.zhipu_api_key = settings.zhipu_api_key
        self.ollama_host = settings.ollama_host
        self.ollama_port = settings.ollama_port
        self.ollama_base_url = f"http://{self.ollama_host}:{self.ollama_port}"

    async def get_embedding_zhipu(self, text: str) -> List[float]:
        """
        使用智谱 GLM 的 embedding-3 模型获取文本向量

        Args:
            text: 输入文本

        Returns:
            1536维向量
        """
        url = "https://open.bigmodel.cn/api/paas/v4/embeddings"
        headers = {
            "Authorization": f"Bearer {self.zhipu_api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": "embedding-3", "input": text}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                embedding = data["data"][0]["embedding"]
                logger.info(f"智谱 embedding 成功，维度: {len(embedding)}")
                return embedding
            except Exception as e:
                logger.error(f"智谱 embedding 失败: {e}")
                raise

    async def get_embedding_ollama(self, text: str, model: str = "nomic-embed-text") -> List[float]:
        """
        使用 Ollama 本地模型获取文本向量

        Args:
            text: 输入文本
            model: 模型名称（默认：nomic-embed-text）

        Returns:
            向量
        """
        url = f"{self.ollama_base_url}/api/embeddings"
        payload = {"model": model, "prompt": text}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                embedding = data["embedding"]
                logger.info(f"Ollama embedding 成功，维度: {len(embedding)}")
                return embedding
            except Exception as e:
                logger.error(f"Ollama embedding 失败: {e}")
                raise

    async def get_embeddings_batch(
        self, texts: List[str], model: str = "embedding-3"
    ) -> List[List[float]]:
        """
        批量获取文本向量

        Args:
            texts: 文本列表
            model: 模型名称

        Returns:
            向量列表
        """
        embeddings = []
        for text in texts:
            if model == "embedding-3":
                embedding = await self.get_embedding_zhipu(text)
            else:
                embedding = await self.get_embedding_ollama(text, model)
            embeddings.append(embedding)
        return embeddings

    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        计算两个向量的余弦相似度

        Args:
            vec1: 向量1
            vec2: 向量2

        Returns:
            相似度（0-1）
        """
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(dot_product / (norm1 * norm2))


embedding_service = EmbeddingService()
