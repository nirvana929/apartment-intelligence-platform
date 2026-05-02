from openai import AsyncOpenAI

from aptguide.core.config import Settings


class LLMClient:
    """OpenAI 兼容 LLM 客户端。"""

    def __init__(self, settings: Settings):
        self.client = AsyncOpenAI(
            api_key=settings.llm_api_key.get_secret_value(),
            base_url=settings.llm_base_url,
        )
        self.model = settings.llm_model

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """生成回复。"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
        )
        return response.choices[0].message.content
