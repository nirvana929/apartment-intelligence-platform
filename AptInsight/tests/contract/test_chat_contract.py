from fastapi.testclient import TestClient

from aptinsight.main import app


def test_chat_contract() -> None:
    client = TestClient(app)
    response = client.post("/api/chat", json={"question": "本月各公寓预约量排名"})
    assert response.status_code == 200
    body = response.json()
    assert body["trace_id"]
    assert isinstance(body["rows"], list)
    assert isinstance(body["columns"], list)

