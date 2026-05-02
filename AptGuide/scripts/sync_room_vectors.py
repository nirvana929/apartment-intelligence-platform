"""同步房源向量到 Milvus。"""

import json
from pymilvus import MilvusClient, DataType

from aptguide.core.config import Settings
from aptguide.vector.embedding import EmbeddingClient


COLLECTION_NAME = "room_index"


def create_collection(client: MilvusClient) -> None:
    """创建 Collection。"""
    if client.has_collection(COLLECTION_NAME):
        client.drop_collection(COLLECTION_NAME)

    schema = client.create_schema(
        auto_id=False,
        enable_dynamic_field=True,
    )

    schema.add_field("id", DataType.INT64, is_primary=True)
    schema.add_field("title", DataType.VARCHAR, max_length=128)
    schema.add_field("description", DataType.VARCHAR, max_length=4096)
    schema.add_field("vector", DataType.FLOAT_VECTOR, dim=1024)
    schema.add_field("rent", DataType.INT64)
    schema.add_field("district", DataType.VARCHAR, max_length=32)
    schema.add_field("tags", DataType.VARCHAR, max_length=512)
    schema.add_field("payment_type", DataType.VARCHAR, max_length=16)
    schema.add_field("status", DataType.VARCHAR, max_length=16)

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


def load_mock_rooms() -> list[dict]:
    """加载 Mock 房源数据。"""
    return [
        {
            "id": 3001,
            "title": "天河公寓 302",
            "description": "周边安静，适合备考，靠近图书馆",
            "rent": 2800,
            "district": "天河区",
            "tags": '["独卫", "朝南", "安静"]',
            "payment_type": "月付",
            "status": "available",
        },
        {
            "id": 3002,
            "title": "科韵公寓 506",
            "description": "靠近地铁站，交通便利",
            "rent": 2950,
            "district": "天河区",
            "tags": '["独卫", "近地铁"]',
            "payment_type": "月付",
            "status": "available",
        },
        {
            "id": 3003,
            "title": "棠德公寓 412",
            "description": "户型紧凑，性价比高",
            "rent": 2700,
            "district": "天河区",
            "tags": '["独卫", "性价比"]',
            "payment_type": "季付",
            "status": "available",
        },
    ]


async def sync_room_vectors() -> None:
    """同步房源向量。"""
    settings = Settings()
    embedding = EmbeddingClient(settings)

    # 连接 Milvus
    milvus = MilvusClient(uri=settings.milvus_uri, token=settings.milvus_token)

    # 创建 Collection
    create_collection(milvus)

    # 加载房源
    rooms = load_mock_rooms()
    print(f"Loaded {len(rooms)} rooms")

    # 生成向量并插入
    for room in rooms:
        text = f"{room['title']} {room['description']} {room['tags']}"
        vector = await embedding.embed(text)

        milvus.insert(
            collection_name=COLLECTION_NAME,
            data=[{
                "id": room["id"],
                "title": room["title"],
                "description": room["description"],
                "vector": vector,
                "rent": room["rent"],
                "district": room["district"],
                "tags": room["tags"],
                "payment_type": room["payment_type"],
                "status": room["status"],
            }],
        )
        print(f"Inserted room {room['id']}: {room['title']}")

    print(f"Successfully synced {len(rooms)} rooms")


if __name__ == "__main__":
    import asyncio
    asyncio.run(sync_room_vectors())
