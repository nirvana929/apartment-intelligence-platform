"""初始化知识库到 Milvus。"""

import yaml
from pathlib import Path
from pymilvus import MilvusClient, DataType

from aptguide.core.config import Settings
from aptguide.vector.embedding import EmbeddingClient


COLLECTION_NAME = "apt_rental_kb"


def create_collection(client: MilvusClient) -> None:
    """创建 Collection。"""
    if client.has_collection(COLLECTION_NAME):
        client.drop_collection(COLLECTION_NAME)

    schema = client.create_schema(
        auto_id=False,
        enable_dynamic_field=True,
    )

    schema.add_field("id", DataType.VARCHAR, is_primary=True, max_length=32)
    schema.add_field("content", DataType.VARCHAR, max_length=4096)
    schema.add_field("vector", DataType.FLOAT_VECTOR, dim=1024)
    schema.add_field("category", DataType.VARCHAR, max_length=32)
    schema.add_field("title", DataType.VARCHAR, max_length=128)

    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="vector",
        index_type="IVF_FLAT",
        metric_type="COSINE",
        params={"nlist": 128},
    )

    client.create_collection(
        collection_name=COLLECTION_NAME,
        schema=schema,
        index_params=index_params,
    )

    print(f"Collection {COLLECTION_NAME} created")


def load_rules() -> list[dict]:
    """加载规则文件。"""
    rules_dir = Path("src/aptguide/knowledge/rules")
    all_rules = []

    for yaml_file in rules_dir.glob("*.yaml"):
        if yaml_file.name.startswith("_"):
            continue

        with open(yaml_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if isinstance(data, list):
                for rule in data:
                    rule["category"] = yaml_file.stem
                    all_rules.append(rule)

    return all_rules


async def seed_kb() -> None:
    """初始化知识库。"""
    settings = Settings()
    embedding = EmbeddingClient(settings)

    # 连接 Milvus
    milvus = MilvusClient(uri=settings.milvus_uri, token=settings.milvus_token)

    # 创建 Collection
    create_collection(milvus)

    # 加载规则
    rules = load_rules()
    print(f"Loaded {len(rules)} rules")

    # 生成向量并插入
    for rule in rules:
        vector = await embedding.embed(rule["content"])
        milvus.insert(
            collection_name=COLLECTION_NAME,
            data=[{
                "id": rule["doc_id"],
                "content": rule["content"],
                "vector": vector,
                "category": rule.get("category", ""),
                "title": rule.get("title", ""),
            }],
        )
        print(f"Inserted {rule['doc_id']}")

    print(f"Successfully seeded {len(rules)} rules")


if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_kb())
