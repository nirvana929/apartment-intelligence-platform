from aptguide3.integrations.vector_client import VectorClient, _map_wechat_room_results


class FakeMilvus:
    def __init__(self):
        self.search_calls = []

    def search(self, **kwargs):
        self.search_calls.append(kwargs)
        return [[{
            "id": 1,
            "distance": 0.2,
            "entity": {
                "id": 1,
                "title": "亚运城公寓 3006",
                "rent": 1500,
                "district": "番禺区",
                "tags": '["安静"]',
                "payment_type": "月付",
                "status": "available",
            },
        }]]

    def load_collection(self, collection_name):
        self.loaded = collection_name


def test_search_rooms_uses_room_collection_and_filters():
    fake = FakeMilvus()
    vc = VectorClient.__new__(VectorClient)
    vc._client = fake

    hits = vc.search_rooms([0.1, 0.2], filters={"district_name": "番禺区", "max_rent": 1800}, top_k=3)

    assert len(hits) == 1
    assert hits[0]["room_id"] == 1
    assert hits[0]["tags"] == ["安静"]  # JSON string parsed
    call = fake.search_calls[0]
    assert call["collection_name"] == "room_index"
    assert 'status == "available"' in call["filter"]
    assert 'district == "番禺区"' in call["filter"]
    assert "rent <= 1800" in call["filter"]


def test_search_rooms_district_normalization():
    fake = FakeMilvus()
    vc = VectorClient.__new__(VectorClient)
    vc._client = fake

    vc.search_rooms([0.1], filters={"district_name": "番禺", "max_rent": 1500})

    call = fake.search_calls[0]
    assert 'district == "番禺区"' in call["filter"]


def test_search_rooms_no_filters():
    fake = FakeMilvus()
    vc = VectorClient.__new__(VectorClient)
    vc._client = fake

    vc.search_rooms([0.1])

    call = fake.search_calls[0]
    assert call["filter"] == 'status == "available"'


def test_search_rooms_exception_returns_empty():
    class BrokenMilvus:
        def load_collection(self, name):
            raise RuntimeError("milvus down")

    vc = VectorClient.__new__(VectorClient)
    vc._client = BrokenMilvus()

    assert vc.search_rooms([0.1]) == []


def test_wechat_room_synthetic_id_is_stable():
    results = [[{
        "distance": 0.2,
        "entity": {
            "id": "wechat-001",
            "district": "天河区",
            "area_label": "黄村/棠东",
            "rent_min": 480,
            "rent_max": 880,
            "tags": '["近地铁"]',
            "metro_stations": '["黄村"]',
            "facility_tags": '["空调"]',
            "payment_tags": '["押一付一"]',
        },
    }]]

    first = _map_wechat_room_results(results)[0]
    second = _map_wechat_room_results(results)[0]

    assert first["room_id"] == second["room_id"]
    assert first["room_id"] == 936217
    assert first["source_record_id"] == "wechat-001"
