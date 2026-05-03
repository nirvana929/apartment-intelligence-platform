import json

from aptguide.core.config import Settings
from aptguide.vector.client import MilvusClientWrapper
from aptguide.vector.embedding import EmbeddingClient


class RoomIndex:
    """房源索引检索。"""

    COLLECTION_NAME = "room_index"

    def __init__(
        self,
        milvus: MilvusClientWrapper,
        settings: Settings,
        embedding: EmbeddingClient,
    ):
        self.milvus = milvus
        self.embedding = embedding

    async def search(
        self,
        query: str,
        max_rent: int | None = None,
        district: str | None = None,
        top_k: int = 10,
    ) -> list[dict]:
        """检索房源。"""
        query_vector = await self.embedding.embed(query)

        # 构建过滤条件
        filters = ['status == "available"']
        if max_rent:
            filters.append(f"rent <= {max_rent}")
        if district:
            filters.append(f'district == "{district}"')

        filter_expr = " and ".join(filters) if filters else ""

        results = self.milvus.search(
            collection_name=self.COLLECTION_NAME,
            query_vector=query_vector,
            top_k=top_k,
            output_fields=["title", "rent", "district", "tags", "description", "status"],
            filter_expr=filter_expr,
        )

        # 格式化结果
        rooms = []
        for result in results:
            tags = result.get("tags", "[]")
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except json.JSONDecodeError:
                    tags = []

            rooms.append(
                {
                    "room_id": result["id"],
                    "title": result.get("title", ""),
                    "rent": result.get("rent", 0),
                    "district": result.get("district", ""),
                    "tags": tags,
                    "description": result.get("description", ""),
                    "score": result.get("distance", 0),
                }
            )

        return rooms[:5]  # 最多返回 5 个
