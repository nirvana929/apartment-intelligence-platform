"""同步房源向量到 Milvus。"""

import yaml
from pathlib import Path
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


def load_rooms_from_yaml() -> list[dict]:
    """从 rooms.yaml 加载房源数据。"""
    rooms_file = Path("src/aptguide/knowledge/mock/rooms.yaml")
    with open(rooms_file, "r", encoding="utf-8") as f:
        raw_rooms = yaml.safe_load(f)

    rooms = []
    for r in raw_rooms:
        # 构造向量化文本
        tags_str = ", ".join(r.get("tags", []))
        facilities_str = ", ".join(r.get("facilities", []))
        description = (
            f"{r['apartment_name']} {r['room_number']}，"
            f"{r['city_name']}{r['district_name']}，"
            f"{r['layout']}，{r['area']}㎡，"
            f"月租{r['rent']}元。"
            f"标签：{tags_str}。"
            f"配套：{facilities_str}。"
        )

        # 支付方式取第一个
        payment_types = r.get("payment_types", ["MONTHLY"])
        payment_map = {
            "MONTHLY": "月付", "QUARTERLY": "季付",
            "HALF_YEARLY": "半年付", "YEARLY": "年付",
        }
        payment_type = payment_map.get(payment_types[0], "月付")

        rooms.append({
            "id": r["room_id"],
            "title": f"{r['apartment_name']} {r['room_number']}",
            "description": description,
            "rent": r["rent"],
            "district": r["district_name"],
            "tags": str(r.get("tags", [])),
            "payment_type": payment_type,
            "status": "available" if r.get("is_release", True) else "unavailable",
        })

    return rooms


async def sync_room_vectors() -> None:
    """同步房源向量。"""
    settings = Settings()
    embedding = EmbeddingClient(settings)

    # 连接 Milvus
    milvus = MilvusClient(uri=settings.milvus_uri, token=settings.milvus_token)

    # 创建 Collection
    create_collection(milvus)

    # 加载房源
    rooms = load_rooms_from_yaml()
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

    milvus.flush(COLLECTION_NAME)
    print(f"Successfully synced {len(rooms)} rooms")


if __name__ == "__main__":
    import asyncio
    asyncio.run(sync_room_vectors())
