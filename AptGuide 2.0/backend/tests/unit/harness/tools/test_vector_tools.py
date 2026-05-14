from aptguide2.harness.tools.contracts import ToolCallRequest
from aptguide2.harness.tools.vector_tools import KBSearchExecutor


class FakeVectorAdapter:
    def __init__(self, results=None, exc=None):
        self._results = results or []
        self._exc = exc
        self.last_kwargs = {}

    def search_kb(self, vector, filters=None, top_k=10):
        if self._exc:
            raise self._exc
        self.last_kwargs = {"filters": filters, "top_k": top_k}
        return self._results


def _request(query: str = "押金", top_k: int = 5) -> ToolCallRequest:
    return ToolCallRequest(
        tool="kb.search",
        request_id="r-1",
        payload={"query": query, "top_k": top_k},
    )


def test_kb_search_returns_sources():
    adapter = FakeVectorAdapter(results=[
        {"chunk_id": "c1", "title": "押金规则", "content": "押金退还", "module": "lease", "distance": 0.85},
    ])
    executor = KBSearchExecutor(vector_adapter=adapter, embed_fn=lambda t: [0.1] * 10)
    result = executor.execute(_request())
    assert result.ok is True
    assert result.data["total"] == 1
    assert result.data["sources"][0]["title"] == "押金规则"
    assert adapter.last_kwargs["top_k"] == 5


def test_kb_search_empty_results():
    adapter = FakeVectorAdapter(results=[])
    executor = KBSearchExecutor(vector_adapter=adapter, embed_fn=lambda t: [0.1] * 10)
    result = executor.execute(_request())
    assert result.ok is True
    assert result.data["total"] == 0


def test_embed_failure_maps_to_error():
    def bad_embed(text):
        raise RuntimeError("embed service down")

    adapter = FakeVectorAdapter()
    executor = KBSearchExecutor(vector_adapter=adapter, embed_fn=bad_embed)
    result = executor.execute(_request())
    assert result.ok is False
    assert result.error.code == "UNKNOWN_TOOL_ERROR"
    assert "Embed failed" in result.error.message


def test_vector_adapter_failure_maps_to_error():
    adapter = FakeVectorAdapter(exc=ConnectionError("milvus down"))
    executor = KBSearchExecutor(vector_adapter=adapter, embed_fn=lambda t: [0.1] * 10)
    result = executor.execute(_request())
    assert result.ok is False
    assert result.error.code == "UNKNOWN_TOOL_ERROR"
    assert "Vector search failed" in result.error.message


def test_invalid_payload_returns_error():
    adapter = FakeVectorAdapter()
    executor = KBSearchExecutor(vector_adapter=adapter, embed_fn=lambda t: [0.1] * 10)
    bad_request = ToolCallRequest(tool="kb.search", request_id="r-1", payload={})
    result = executor.execute(bad_request)
    assert result.ok is False
    assert result.error.code == "INVALID_PAYLOAD"
