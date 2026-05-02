from aptguide.core.config import Settings
from aptguide.vector.client import MilvusClientWrapper
from aptguide.vector.embedding import EmbeddingClient


class KBSearch:
    """知识库检索。"""

    COLLECTION_NAME = "apt_rental_kb"

    def __init__(self, milvus: MilvusClientWrapper, settings: Settings):
        self.milvus = milvus
        self.embedding = EmbeddingClient(settings)

    async def search(self, query: str, top_k: int = 3) -> list[dict]:
        """检索知识库。"""
        query_vector = await self.embedding.embed(query)

        results = self.milvus.search(
            collection_name=self.COLLECTION_NAME,
            query_vector=query_vector,
            top_k=top_k,
            output_fields=["id", "content", "category", "title"],
        )

        # 过滤低分结果
        filtered = []
        for result in results:
            if result.get("score", 0) >= 0.7:
                filtered.append(
                    {
                        "id": result["id"],
                        "content": result["content"],
                        "category": result.get("category"),
                        "title": result.get("title"),
                        "score": result["score"],
                    }
                )

        return filtered
