from __future__ import annotations

from openai import OpenAI


class EmbeddingClient:
    def __init__(
        self, base_url: str = "https://api.openai.com/v1", api_key: str = "", model: str = "text-embedding-3-small",
    ) -> None:
        self._client = OpenAI(base_url=base_url, api_key=api_key)
        self._model = model

    def embed(self, text: str) -> list[float]:
        try:
            response = self._client.embeddings.create(input=[text], model=self._model)
            return response.data[0].embedding
        except Exception:
            return []
