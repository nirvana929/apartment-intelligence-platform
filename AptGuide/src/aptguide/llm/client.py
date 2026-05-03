"""
LLM 客户端 —— 封装大语言模型的调用。

【学习要点】
1. OpenAI 兼容协议：很多 LLM 提供商（Qwen、DeepSeek 等）都兼容 OpenAI 的 API 格式
   所以用 openai 库就能调用不同厂商的模型，只需改 base_url
2. AsyncOpenAI：异步版本的 OpenAI 客户端，用 await 调用不会阻塞其他请求
3. get_secret_value()：从 SecretStr 中提取真实密钥（打印时不会泄露）
4. temperature：控制 LLM 输出的随机性，0.7 是中等（0 = 确定性，1 = 随机）
"""

from openai import AsyncOpenAI

from aptguide.core.config import Settings


class LLMClient:
    """
    OpenAI 兼容 LLM 客户端。

    为什么用 OpenAI 的库来调用 Qwen（通义千问）？
    因为 Qwen 提供了 OpenAI 兼容的 API 接口，所以可以直接复用 openai 库。
    这种"兼容协议"的设计很常见，让你切换 LLM 提供商时不需要改代码。
    """

    def __init__(self, settings: Settings):
        # AsyncOpenAI 是 openai 库的异步客户端
        # api_key 和 base_url 来自配置（.env 文件）
        self.client = AsyncOpenAI(
            api_key=settings.llm_api_key.get_secret_value(),  # 提取真实密钥
            base_url=settings.llm_base_url,  # API 地址（不同厂商不同）
        )
        self.model = settings.llm_model  # 模型名称（如 "qwen-plus"）

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """
        调用 LLM 生成回复。

        参数：
        - prompt: 用户消息（必填）
        - system_prompt: 系统提示词（可选，用于设定 LLM 的角色）

        返回：LLM 生成的文本

        消息格式（OpenAI Chat 协议）：
        [
            {"role": "system", "content": "你是一个租房助手"},  # 可选
            {"role": "user", "content": "天河区3000以内的房子"},  # 必填
        ]
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # chat.completions.create 是 OpenAI Chat API 的标准调用方式
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,  # 0.7 = 适度随机，平衡创造性和准确性
        )

        # response.choices 是一个列表，通常只有一个元素
        # .message.content 是 LLM 生成的文本
        return response.choices[0].message.content
