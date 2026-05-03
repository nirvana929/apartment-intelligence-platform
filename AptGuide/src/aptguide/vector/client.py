"""
Milvus 向量数据库客户端封装。

【学习要点】
1. 向量检索（Vector Search）的核心概念：
   - 把文本（如"天河区安静的房子"）转成一个数字数组（embedding 向量）
   - 在数据库中找到"距离最近"的向量（语义最相似）
   - 这比关键词搜索更智能，因为能理解同义词和语义

2. distance（距离）：两个向量之间的"距离"，越小越相似
   - 有时也叫 score（分数），越大越相似
   - 这里统一用 distance 字段名

3. Milvus 是一个专门做向量检索的数据库（类似 Pinecone、Weaviate）
"""

from pymilvus import MilvusClient

from aptguide.core.config import Settings


class MilvusClientWrapper:
    """
    Milvus 客户端封装。

    为什么封装一层？
    1. 统一接口：不管 Milvus SDK 怎么变，上层代码不用改
    2. 结果标准化：Milvus 返回的格式和我们期望的可能不同，在这里统一转换
    """

    def __init__(self, settings: Settings):
        self.uri = settings.milvus_uri  # Milvus 服务地址
        self.token = settings.milvus_token
        self.client: MilvusClient | None = None  # 延迟连接

    def connect(self) -> None:
        """连接 Milvus 服务。"""
        self.client = MilvusClient(uri=self.uri, token=self.token)

    def search(
        self,
        collection_name: str,       # 集合名（类似数据库的表名）
        query_vector: list[float],   # 查询向量（用户消息的 embedding）
        top_k: int = 3,             # 返回最相似的前 N 条
        output_fields: list[str] | None = None,  # 需要返回的字段
        filter_expr: str | None = None,           # 过滤条件（如 "rent < 3000"）
    ) -> list[dict]:
        """
        向量检索。

        参数：
        - collection_name: 要搜索的集合（apt_rental_kb 或 rooms）
        - query_vector: 查询向量（如 [0.1, 0.2, 0.3, ...]，通常 1024 维）
        - top_k: 返回最相似的前几条
        - output_fields: 需要返回哪些字段（如 ["title", "rent"]）
        - filter_expr: 过滤条件（如 "district == '天河区'"）

        返回：包含 id、distance 和请求字段的字典列表
        """
        if not self.client:
            raise RuntimeError("Milvus client not connected")

        search_params = {
            "collection_name": collection_name,
            "data": [query_vector],  # Milvus 要求传入列表（支持批量搜索）
            "limit": top_k,
            "output_fields": output_fields,
        }
        if filter_expr:
            search_params["filter"] = filter_expr

        raw_results = self.client.search(**search_params)
        if not raw_results:
            return []

        # 结果标准化：
        # Milvus 返回格式：[{"id": 1, "distance": 0.8, "entity": {"title": "...", ...}}]
        # 我们把它展平为：{"id": 1, "distance": 0.8, "title": "...", ...}
        normalized = []
        for hit in raw_results[0]:
            entry = {"id": hit["id"], "distance": hit.get("distance", 0)}
            entity = hit.get("entity", {})
            entry.update(entity)  # 把 entity 中的字段展开到顶层
            normalized.append(entry)
        return normalized
