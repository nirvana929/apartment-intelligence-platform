from openai import AsyncOpenAI

from aptguide.core.config import Settings


class EmbeddingClient:
    """Embedding 客户端。"""

    def __init__(self, settings: Settings):
        self.client = AsyncOpenAI(
            api_key=settings.embedding_api_key.get_secret_value(),
            base_url=settings.embedding_base_url,
        )
        self.model = settings.embedding_model

    async def embed(self, text: str) -> list[float]:
        """生成向量。"""
        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
        )
        return response.data[0].embedding
