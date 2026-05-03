"""
知识库检索 —— RAG 中的"R"（Retrieval）。

【学习要点】
1. RAG（Retrieval-Augmented Generation）的工作流程：
   用户提问 → 向量化问题 → 在知识库中搜索相似内容 → 把内容交给 LLM 生成回答
2. Embedding（向量化）：把文本转成数字数组，语义相似的文本向量距离近
3. 相似度阈值过滤：distance > 0.5 是经验阈值，太低的结果质量差，不如不返回
4. COLLECTION_NAME = "apt_rental_kb" 是 Milvus 中的集合名（类似数据库表名）
"""

from aptguide.core.config import Settings
from aptguide.vector.client import MilvusClientWrapper
from aptguide.vector.embedding import EmbeddingClient


class KBSearch:
    """
    知识库检索。

    用于回答租房规则类问题（押金、退租、续约、预约规则等）。
    知识库内容存在 Milvus 中，每条记录是一个知识条目（FAQ 或规则）。
    """

    COLLECTION_NAME = "apt_rental_kb"  # Milvus 集合名

    def __init__(self, milvus: MilvusClientWrapper, settings: Settings):
        self.milvus = milvus
        self.embedding = EmbeddingClient(settings)  # 用于把文本转成向量

    async def search(self, query: str, top_k: int = 3) -> list[dict]:
        """
        检索知识库。

        流程：
        1. 把用户问题转成向量（embedding）
        2. 在 Milvus 中搜索最相似的知识条目
        3. 过滤掉相似度太低的结果

        参数：
        - query: 用户问题（如"押金怎么退"）
        - top_k: 返回最相似的前几条

        返回：知识条目列表，每条包含 id、content、category、title、score
        """
        # 第一步：把文本转成向量
        # "押金怎么退" → [0.1, 0.2, 0.3, ...]（1024 维浮点数组）
        query_vector = await self.embedding.embed(query)

        # 第二步：在 Milvus 中搜索
        results = self.milvus.search(
            collection_name=self.COLLECTION_NAME,
            query_vector=query_vector,
            top_k=top_k,
            output_fields=["id", "content", "category", "title"],
        )

        # 第三步：过滤低分结果
        # distance 是向量距离，越小越相似（但这里可能被转成了相似度分数）
        # 0.5 是经验值，低于这个阈值的结果通常不相关
        filtered = []
        for result in results:
            score = result.get("distance", 0)
            if score > 0.5:
                filtered.append(
                    {
                        "id": result["id"],
                        "content": result.get("content", ""),
                        "category": result.get("category"),
                        "title": result.get("title"),
                        "score": score,
                    }
                )

        return filtered
