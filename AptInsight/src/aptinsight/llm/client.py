"""
LLM 客户端 —— 调用大模型 API 的封装。

这个文件的作用：
  封装与大模型（小米 MiMo）的通信逻辑。
  其他模块需要调用 LLM 时，直接用这里的 LLMClient 类。

为什么用 OpenAI SDK？
  小米 MiMo 的 API 兼容 OpenAI 协议（地址是 /v1/chat/completions），
  所以可以直接用 openai 这个 Python 库来调用，不需要写 HTTP 请求。

  好处：
    1. 自动处理请求重试、超时
    2. 类型安全（IDE 能自动补全参数）
    3. 以后换模型（比如换成 GPT-4、Claude），只改配置不改代码

两种调用方式的区别：
  chat()           → 返回自由文本（用于回答生成、SQL 生成）
  chat_structured() → 强制返回 JSON（用于意图识别、结构化输出）

使用示例：
  from aptinsight.llm.client import LLMClient

  # 创建客户端
  client = LLMClient(
      api_key="your-api-key",
      base_url="https://api.example.com/v1",
      model="mimo-v2.5-pro"
  )

  # 场景 1：生成自由文本
  answer = await client.chat("你好", system="你是一个公寓助手")

  # 场景 2：生成结构化 JSON
  raw_json = await client.chat_structured("本月预约量多少？", system="判断用户意图")
"""


from openai import AsyncOpenAI  # OpenAI 异步客户端

from langsmith.wrappers import wrap_openai  # LangSmith 追踪包装器

from aptinsight.core.config import settings  # 读取 LLM 配置
from aptinsight.core.logging import get_logger  # 记录日志

logger = get_logger(__name__)


# ============================================================================
# LLM 客户端类
# ============================================================================

class LLMClient:
    """
    LLM 客户端类

    封装了与大模型 API 的通信逻辑，提供两种调用方式：
    1. chat(): 生成自由文本
    2. chat_structured(): 生成结构化 JSON

    学习要点：
    - 类封装：将相关功能封装到一个类中
    - 依赖注入：通过构造函数注入配置
    - 异步方法：使用 async/await 处理异步操作
    """

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "",
        model: str = "",
        timeout: int = 30,
        default_max_tokens: int = 2000,
        reasoning_effort: str = "",
    ):
        """
        初始化 LLM 客户端

        Args:
            api_key: API 认证密钥
            base_url: API 基础地址
            model: 使用的模型名称
            timeout: 请求超时时间（秒）
            default_max_tokens: 默认最大生成 token 数
            reasoning_effort: 思考链力度 (low/medium/high)，空则用全局配置
        """
        # 使用提供的参数或从配置中读取
        self.api_key = api_key or settings.llm_api_key
        self.base_url = base_url or settings.llm_base_url
        self.model = model or settings.llm_model
        self.timeout = timeout or settings.llm_timeout_seconds
        self.default_max_tokens = default_max_tokens
        self.reasoning_effort = reasoning_effort or settings.llm_reasoning_effort

        # 创建 OpenAI 异步客户端，用 wrap_openai 包装以支持 LangSmith 追踪
        # 包装后，每次 LLM 调用会作为子节点出现在 LangSmith trace 中
        self.client = wrap_openai(
            AsyncOpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
                timeout=self.timeout,
            ),
            chat_name=self.model,
        )

        logger.info(f"LLM 客户端初始化完成，模型: {self.model}")

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int | None = None,
    ) -> str:
        """
        调用 LLM 生成自由文本回复。

        Args:
            messages: 消息列表，格式如 [{"role": "user", "content": "..."}]
            temperature: 温度参数，控制回复的随机性（0.0-1.0）
            max_tokens: 最大生成 token 数

        Returns:
            LLM 生成的文本字符串

        学习要点：
        - 异步方法：使用 async/await 处理异步操作
        - 错误处理：捕获和处理 API 调用错误
        - 日志记录：记录关键信息用于调试
        """
        try:
            # 构建 extra_body，传递 reasoning_effort 控制思考链
            extra = {}
            if self.reasoning_effort:
                extra["reasoning_effort"] = self.reasoning_effort

            # 调用 API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens if max_tokens is not None else self.default_max_tokens,
                extra_body=extra if extra else None,
            )

            # 提取回复文本
            content = response.choices[0].message.content or ""

            # 记录日志
            tokens = response.usage.total_tokens if response.usage else 0
            logger.info(f"LLM 调用成功，模型: {self.model}，tokens: {tokens}")

            return content

        except Exception as e:
            logger.error(f"LLM 调用失败，错误: {e}")
            raise

    async def chat_structured(
        self,
        messages: list[dict[str, str]],
        max_tokens: int | None = None,
    ) -> str:
        """
        调用 LLM 生成结构化 JSON 回复。

        和 chat() 的区别：
        1. temperature=0.0（最确定性，JSON 格式不能有随机性）
        2. response_format={"type": "json_object"}（强制 LLM 返回 JSON）

        Args:
            messages: 消息列表
            max_tokens: 最大生成 token 数

        Returns:
            JSON 字符串

        学习要点：
        - JSON 模式：使用 response_format 强制返回 JSON
        - 确定性输出：使用 temperature=0.0 保证格式稳定
        """
        try:
            # 构建 extra_body，传递 reasoning_effort 控制思考链
            extra = {}
            if self.reasoning_effort:
                extra["reasoning_effort"] = self.reasoning_effort

            # 调用 API，关键区别是 response_format 和 temperature
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.0,  # 最确定性，保证 JSON 格式稳定
                response_format={"type": "json_object"},  # 强制返回 JSON
                max_tokens=max_tokens if max_tokens is not None else self.default_max_tokens,
                extra_body=extra if extra else None,
            )

            # 提取 JSON 字符串
            content = response.choices[0].message.content or "{}"

            # 记录日志
            logger.info(f"LLM 结构化调用成功，模型: {self.model}")

            return content

        except Exception as e:
            logger.error(f"LLM 结构化调用失败，错误: {e}")
            raise


# ============================================================================
# 全局客户端实例（用于兼容旧代码）
# ============================================================================

# 创建全局客户端实例
# 学习要点：单例模式，全局共享一个客户端实例
_default_client: LLMClient | None = None


def get_default_client() -> LLMClient:
    """
    获取默认的 LLM 客户端实例

    Returns:
        LLMClient 实例

    学习要点：
    - 延迟初始化：第一次调用时才创建实例
    - 单例模式：全局共享一个实例
    """
    global _default_client
    if _default_client is None:
        _default_client = LLMClient()
    return _default_client


# ============================================================================
# 便捷函数（兼容旧代码）
# ============================================================================

async def generate(prompt: str, system: str = "") -> str:
    """
    调用 LLM 生成自由文本回复（便捷函数）。

    Args:
        prompt: 用户的问题或指令
        system: 系统提示词（可选）

    Returns:
        LLM 生成的文本字符串

    学习要点：
    - 便捷函数：简化常见操作
    - 向后兼容：保持旧代码可以继续工作
    """
    client = get_default_client()

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    return await client.chat(messages)


async def generate_structured(prompt: str, system: str = "") -> str:
    """
    调用 LLM 生成结构化 JSON 回复（便捷函数）。

    Args:
        prompt: 用户的问题或指令
        system: 系统提示词（可选）

    Returns:
        JSON 字符串
    """
    client = get_default_client()

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    return await client.chat_structured(messages)
