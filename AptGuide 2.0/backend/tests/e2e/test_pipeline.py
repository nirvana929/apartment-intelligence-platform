"""E2E tests for the RAG pipeline — all 3 task paths with mock Milvus."""

from __future__ import annotations

from unittest.mock import MagicMock

from aptguide2.rag.pipeline import PipelineResult, run_pipeline


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------

def _fake_embed(text: str) -> list[float]:
    """Return a deterministic fake embedding."""
    return [0.1] * 1024


class MockVectorAdapter:
    """Mock VectorAdapter that returns pre-configured results."""

    def __init__(self, room_results=None, kb_results=None):
        self._room_results = room_results or []
        self._kb_results = kb_results or []

    def search_rooms(self, vector, filters=None, top_k=30):
        return self._room_results

    def search_kb(self, vector, filters=None, top_k=10):
        return self._kb_results

    def get_room_by_ids(self, room_ids):
        # Return enriched data for each known room_id
        all_rooms = {
            1: {"room_id": 1, "apartment_id": 10, "district_id": 1005, "district_name": "番禺区",
                "rent": 1500, "payment_types": '["月付"]', "lease_terms": '[6, 12]',
                "tags": '["近地铁", "安静"]', "facilities": '["空调", "WiFi"]'},
            2: {"room_id": 2, "apartment_id": 10, "district_id": 1005, "district_name": "番禺区",
                "rent": 1800, "payment_types": '["季付"]', "lease_terms": '[12]',
                "tags": '["采光好"]', "facilities": '["洗衣机"]'},
            3: {"room_id": 3, "apartment_id": 20, "district_id": 1001, "district_name": "天河区",
                "rent": 2500, "payment_types": '["月付"]', "lease_terms": '[12]',
                "tags": '["近地铁", "通勤方便"]', "facilities": '["空调"]'},
        }
        return [all_rooms[rid] for rid in room_ids if rid in all_rooms]


# ---------------------------------------------------------------------------
# Pipeline tests
# ---------------------------------------------------------------------------

class TestPipelineRoomSearch:
    """Test room_search path through the pipeline."""

    def test_room_search_returns_ranked_rooms(self):
        mock_adapter = MockVectorAdapter(
            room_results=[
                {"room_id": 1, "apartment_id": 10, "distance": 0.9},
                {"room_id": 2, "apartment_id": 10, "distance": 0.8},
            ],
        )
        result = run_pipeline(
            message="番禺区1500以内的房子",
            vector_adapter=mock_adapter,
            embed_fn=_fake_embed,
        )
        assert result.task == "room_search"
        assert len(result.rooms) > 0
        assert result.rooms[0].room_id in (1, 2)

    def test_room_search_with_budget_filter(self):
        mock_adapter = MockVectorAdapter(
            room_results=[
                {"room_id": 1, "apartment_id": 10, "distance": 0.9},
            ],
        )
        result = run_pipeline(
            message="找房2000以内",
            vector_adapter=mock_adapter,
            embed_fn=_fake_embed,
        )
        assert result.task == "room_search"
        assert result.query_understanding is not None
        assert result.query_understanding.hard_filters.get("max_rent") == 2000

    def test_room_search_no_results(self):
        mock_adapter = MockVectorAdapter(room_results=[])
        result = run_pipeline(
            message="番禺区找房",
            vector_adapter=mock_adapter,
            embed_fn=_fake_embed,
        )
        assert result.task == "room_search"
        assert len(result.rooms) == 0
        assert "没有找到" in result.message


class TestPipelineKBQA:
    """Test kb_qa path through the pipeline."""

    def test_kb_qa_confident(self):
        mock_adapter = MockVectorAdapter(
            kb_results=[
                {"chunk_id": "kb-lease-01#01", "doc_id": "kb-lease-01", "title": "押金退还规则",
                 "module": "lease", "content": "押金在退租后15个工作日内退还。",
                 "distance": 0.85, "risk_level": "high", "_recall_source": "original", "_matched_query": "押金"},
            ],
        )
        result = run_pipeline(
            message="押金什么时候退",
            vector_adapter=mock_adapter,
            embed_fn=_fake_embed,
        )
        assert result.task == "kb_qa"
        assert result.is_confident is True
        assert len(result.kb_sources) > 0

    def test_kb_qa_low_confidence_returns_fallback(self):
        mock_adapter = MockVectorAdapter(
            kb_results=[
                {"chunk_id": "kb-lease-01#01", "doc_id": "kb-lease-01", "title": "押金退还规则",
                 "module": "lease", "content": "押金相关。",
                 "distance": 0.3, "risk_level": "high", "_recall_source": "original", "_matched_query": "押金"},
            ],
        )
        result = run_pipeline(
            message="押金什么时候退",
            vector_adapter=mock_adapter,
            embed_fn=_fake_embed,
        )
        assert result.task == "kb_qa"
        assert result.is_confident is False
        assert "联系" in result.message or "合同" in result.message

    def test_kb_qa_no_sources(self):
        mock_adapter = MockVectorAdapter(kb_results=[])
        result = run_pipeline(
            message="押金什么时候退",
            vector_adapter=mock_adapter,
            embed_fn=_fake_embed,
        )
        assert result.task == "kb_qa"
        assert result.is_confident is False


class TestPipelineFallback:
    """Test fallback path through the pipeline."""

    def test_fallback_out_of_scope(self):
        mock_adapter = MockVectorAdapter()
        result = run_pipeline(
            message="帮我写代码",
            vector_adapter=mock_adapter,
            embed_fn=_fake_embed,
        )
        assert result.task == "fallback"
        assert "超出" in result.message or "服务范围" in result.message

    def test_fallback_guarantee_request(self):
        mock_adapter = MockVectorAdapter()
        result = run_pipeline(
            message="你保证这个房子没问题",
            vector_adapter=mock_adapter,
            embed_fn=_fake_embed,
        )
        assert result.task == "fallback"

    def test_fallback_random_question(self):
        mock_adapter = MockVectorAdapter()
        result = run_pipeline(
            message="1+1等于几",
            vector_adapter=mock_adapter,
            embed_fn=_fake_embed,
        )
        assert result.task == "fallback"
