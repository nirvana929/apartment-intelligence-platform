import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_llm_client_generate():
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock(message=AsyncMock(content="测试回复"))]

    with patch("openai.AsyncOpenAI") as mock_client:
        mock_client.return_value.chat.completions.create = AsyncMock(return_value=mock_response)

        from aptguide.llm.client import LLMClient
        from aptguide.core.config import Settings

        settings = Settings(
            llm_api_key="test_key",
            embedding_api_key="test_key",
        )
        client = LLMClient(settings)

        result = await client.generate("测试提示词")
        assert result == "测试回复"
