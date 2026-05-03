from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_milvus_client_connect():
    with patch("aptguide.vector.client.MilvusClient") as mock_cls:
        from aptguide.core.config import Settings
        from aptguide.vector.client import MilvusClientWrapper

        settings = Settings(
            llm_api_key="test_key",
            embedding_api_key="test_key",
            milvus_uri="http://localhost:19530",
        )
        wrapper = MilvusClientWrapper(settings)
        wrapper.connect()
        mock_cls.assert_called_once_with(uri="http://localhost:19530", token="")


@pytest.mark.asyncio
async def test_milvus_client_search_not_connected():
    from aptguide.core.config import Settings
    from aptguide.vector.client import MilvusClientWrapper

    settings = Settings(
        llm_api_key="test_key",
        embedding_api_key="test_key",
    )
    wrapper = MilvusClientWrapper(settings)
    with pytest.raises(RuntimeError, match="Milvus client not connected"):
        wrapper.search("test_collection", [0.1, 0.2, 0.3])


@pytest.mark.asyncio
async def test_milvus_client_search_connected():
    from aptguide.core.config import Settings
    from aptguide.vector.client import MilvusClientWrapper

    settings = Settings(
        llm_api_key="test_key",
        embedding_api_key="test_key",
    )
    wrapper = MilvusClientWrapper(settings)
    wrapper.client = MagicMock()
    wrapper.client.search.return_value = [[{"id": "1", "content": "test", "score": 0.9}]]

    results = wrapper.search("test_collection", [0.1, 0.2, 0.3], top_k=5)
    assert len(results) == 1
    assert results[0]["id"] == "1"
    wrapper.client.search.assert_called_once_with(
        collection_name="test_collection",
        data=[[0.1, 0.2, 0.3]],
        limit=5,
        output_fields=None,
    )


@pytest.mark.asyncio
async def test_embedding_client_embed():
    with patch("aptguide.vector.embedding.AsyncOpenAI") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance

        # Mock async embeddings.create
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        mock_instance.embeddings.create = AsyncMock(return_value=mock_response)

        from aptguide.core.config import Settings
        from aptguide.vector.embedding import EmbeddingClient

        settings = Settings(
            llm_api_key="test_key",
            embedding_api_key="test_key",
        )
        client = EmbeddingClient(settings)
        result = await client.embed("测试文本")

        assert result == [0.1, 0.2, 0.3]
        mock_instance.embeddings.create.assert_called_once_with(
            model="text-embedding-v3",
            input="测试文本",
        )


@pytest.mark.asyncio
async def test_kb_search_filters_low_score():
    mock_milvus = MagicMock()
    mock_milvus.search.return_value = [
        {
            "id": "KB-RULE-008",
            "content": "提前退租规则",
            "distance": 0.85,
            "category": "规则",
            "title": "退租",
        },
        {
            "id": "KB-LOW-001",
            "content": "低分内容",
            "distance": 0.5,
            "category": "其他",
            "title": "低分",
        },
    ]

    with patch("aptguide.vector.kb_search.EmbeddingClient") as mock_emb_cls:
        mock_emb = MagicMock()
        mock_emb.embed = AsyncMock(return_value=[0.1, 0.2, 0.3])
        mock_emb_cls.return_value = mock_emb

        from aptguide.core.config import Settings
        from aptguide.vector.kb_search import KBSearch

        settings = Settings(
            llm_api_key="test_key",
            embedding_api_key="test_key",
        )
        kb = KBSearch(mock_milvus, settings)
        results = await kb.search("押金怎么退", top_k=3)

        assert len(results) == 1
        assert results[0]["id"] == "KB-RULE-008"
        assert results[0]["score"] == 0.85
        assert results[0]["title"] == "退租"


@pytest.mark.asyncio
async def test_kb_search_all_low_score():
    mock_milvus = MagicMock()
    mock_milvus.search.return_value = [
        {"id": "KB-LOW-001", "content": "内容A", "distance": 0.3},
        {"id": "KB-LOW-002", "content": "内容B", "distance": 0.4},
    ]

    with patch("aptguide.vector.kb_search.EmbeddingClient") as mock_emb_cls:
        mock_emb = MagicMock()
        mock_emb.embed = AsyncMock(return_value=[0.1, 0.2, 0.3])
        mock_emb_cls.return_value = mock_emb

        from aptguide.core.config import Settings
        from aptguide.vector.kb_search import KBSearch

        settings = Settings(
            llm_api_key="test_key",
            embedding_api_key="test_key",
        )
        kb = KBSearch(mock_milvus, settings)
        results = await kb.search("无关查询", top_k=3)

        assert len(results) == 0
