from pymilvus import MilvusClient

from aptguide.core.config import Settings


class MilvusClientWrapper:
    """Milvus 客户端封装。"""

    def __init__(self, settings: Settings):
        self.uri = settings.milvus_uri
        self.token = settings.milvus_token
        self.client: MilvusClient | None = None

    def connect(self) -> None:
        """连接 Milvus。"""
        self.client = MilvusClient(uri=self.uri, token=self.token)

    def search(
        self,
        collection_name: str,
        query_vector: list[float],
        top_k: int = 3,
        output_fields: list[str] | None = None,
        filter_expr: str | None = None,
    ) -> list[dict]:
        """向量检索。"""
        if not self.client:
            raise RuntimeError("Milvus client not connected")

        search_params = {
            "collection_name": collection_name,
            "data": [query_vector],
            "limit": top_k,
            "output_fields": output_fields,
        }
        if filter_expr:
            search_params["filter"] = filter_expr

        results = self.client.search(**search_params)
        return results[0] if results else []
