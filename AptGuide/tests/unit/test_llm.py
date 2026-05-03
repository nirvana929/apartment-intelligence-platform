from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.mark.asyncio
async def test_llm_client_generate():
    from aptguide.core.config import Settings
    from aptguide.llm.client import LLMClient

    settings = Settings(
        llm_api_key="test_key",
        embedding_api_key="test_key",
    )
    client = LLMClient(settings)

    # 直接 mock 已初始化的 client 实例
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="测试回复"))]
    client.client.chat.completions.create = AsyncMock(return_value=mock_response)

    result = await client.generate("测试提示词")
    assert result == "测试回复"
