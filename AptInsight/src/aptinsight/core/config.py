"""
配置中心 —— 整个应用的"设置面板"。

这个文件的作用：
  把所有配置项（数据库地址、API Key、超时时间等）集中管理。
  代码里需要配置时，直接 `from aptinsight.core.config import settings` 就能拿到。

配置来源优先级（pydantic-settings 自动处理）：
  1. 环境变量（最高优先级）
  2. .env 文件
  3. 代码里的 default 值（最低优先级）

比如 .env 里写了 `MYSQL_HOST=192.168.211.128`，
pydantic-settings 会自动读取并赋值给 `settings.mysql_host`。

为什么用 pydantic-settings：
  1. 类型校验 —— .env 里 mysql_port 写了 "abc"？启动时直接报错，不会等到运行时才崩
  2. 自动转换 —— .env 里所有值都是字符串，但 mysql_port 会自动转成 int
  3. 统一入口 —— 所有配置都在一个 Settings 对象里，IDE 能自动补全

实际使用场景：
  from aptinsight.core.config import settings

  print(settings.mysql_host)      # "192.168.211.128"
  print(settings.mysql_url)       # "mysql+asyncmy://chove:123456@192.168.211.128:3306/least"
  print(settings.llm_model)       # "mimo-v2.5-pro"
"""

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


# [框架] pydantic-settings 是 Pydantic 的扩展，专门处理配置
# 普通 Pydantic BaseModel 用于校验请求数据
# BaseSettings 用于从环境变量/.env 文件读取配置
class Settings(BaseSettings):
    """
    应用配置类。

    继承 BaseSettings（pydantic-settings 提供），自动从环境变量和 .env 文件读取配置。
    每个类属性就是一个配置项，属性名就是环境变量名（大写）。

    比如 `mysql_host: str` 对应环境变量 `MYSQL_HOST`。
    """

    # ========== 应用基础配置 ==========
    app_name: str = "AptInsight"    # 应用名称
    app_env: str = "local"          # 运行环境：local / dev / prod
    log_level: str = "INFO"         # 日志级别：DEBUG / INFO / WARNING / ERROR

    # ========== LLM 配置 ==========
    # 这些配置告诉程序去哪里调用大模型 API
    llm_base_url: str = "https://token-plan-cn.xiaomimimo.com/v1"  # API 地址（小米 MiMo）
    llm_api_key: str = ""                                            # API 密钥（从 .env 读取）
    llm_model: str = "mimo-v2.5-pro"                                 # 模型名称
    llm_timeout_seconds: int = 30                                    # 请求超时时间（秒）

    # 各节点独立模型配置（留空则使用 llm_model）
    llm_model_intent: str = ""     # 意图识别模型（可用小模型）
    llm_model_sql: str = ""        # SQL 生成模型（建议用 pro）
    llm_model_answer: str = ""     # 答案生成模型（可用小模型）

    # 各节点 max_tokens（需为思考链预留空间，实际输出 = max_tokens - reasoning_tokens）
    llm_max_tokens_intent: int = 400    # 意图识别（含思考链约 150-200 tokens）
    llm_max_tokens_sql: int = 1200      # SQL 生成（含思考链）
    llm_max_tokens_answer: int = 1000   # 答案生成（含思考链）

    # 思考链控制（MiMo 等模型默认启用 reasoning，需通过 reasoning_effort 调节）
    llm_reasoning_effort: str = "medium"  # low/medium/high，medium 平衡速度和质量

    # 其他模型平台 API Key（可选）
    xai_api_key: str = ""               # xAI Grok
    alibaba_bailian_api_key: str = ""   # 阿里云百炼
    deepseek_api_key: str = ""          # DeepSeek

    # ========== MySQL 配置 ==========
    # 连接信息：哪台机器、哪个库、用什么账号
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "chove"
    mysql_password: str = ""
    mysql_database: str = "lease"
    mysql_query_timeout_seconds: int = 10   # 单条 SQL 查询超时（秒）
    mysql_max_rows: int = 200               # 最多返回多少行数据（防止大查询拖垮数据库）

    # ========== Redis 配置 ==========
    # Redis 用于缓存（比如缓存 LLM 的回答，避免重复调用）
    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_db: int = 0           # Redis 有 0~15 共 16 个数据库，用哪个
    redis_password: str = ""    # 如果 Redis 设了密码，填在这里

    # ========== 功能开关 ==========
    expose_sql: bool = True         # 是否在 API 响应中返回生成的 SQL（开发调试用，生产环境应关掉）
    enable_query_log: bool = True   # 是否记录查询日志

    # ========== LangSmith 可观测性配置 ==========
    # LANGSMITH_* 是 LangSmith 当前推荐的环境变量名；
    # LANGCHAIN_* 保留兼容旧版 LangChain/LangSmith tracing 开关。
    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "aptinsight"
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "aptinsight"

    # [框架] SettingsConfigDict 是 pydantic-settings 的配置方式
    # 告诉它去读 .env 文件，这样本地开发不用手动 export 环境变量
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # ========== 计算属性（用 @property） ==========
    # 这些不是从 .env 读的，而是根据其他字段"算"出来的

    @property
    def mysql_url(self) -> str:
        """
        拼接 MySQL 连接 URL。

        SQLAlchemy 需要一个 URL 格式的连接字符串，格式是：
          mysql+asyncmy://用户名:密码@主机:端口/数据库名

        其中 `asyncmy` 是异步 MySQL 驱动（类似 pymysql，但支持 async/await）。
        这个 URL 会传给 create_async_engine() 来创建数据库连接。
        """
        return (
            f"mysql+asyncmy://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )

    @property
    def redis_url(self) -> str:
        """
        拼接 Redis 连接 URL。

        格式：redis://:密码@主机:端口/数据库编号
        如果没有密码，格式：redis://主机:端口/数据库编号
        """
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


# [框架] @lru_cache 是 Python 标准库的缓存装饰器
# 被装饰的函数只执行一次，后续调用直接返回缓存结果
# 这里用来实现单例模式：整个应用只有一个 Settings 实例
@lru_cache
def get_settings() -> Settings:
    """
    获取全局配置单例。

    @lru_cache 的作用：这个函数只会执行一次。
    第一次调用时创建 Settings 对象并缓存，之后再调用直接返回缓存的结果。

    为什么需要这个：
      如果每次都 `Settings()`，每次都会重新读 .env 文件，浪费性能。
      用 lru_cache 保证整个应用只有一个 Settings 实例（单例模式）。
    """
    loaded_settings = Settings()
    _sync_langsmith_environment(loaded_settings)
    return loaded_settings


def _sync_langsmith_environment(loaded_settings: Settings) -> None:
    """
    将 .env 中的 LangSmith 配置同步到进程环境变量。

    LangSmith/LangGraph SDK 直接读取 os.environ；pydantic-settings 只负责把 .env
    解析到 Settings 对象，不会自动 export 给当前进程。
    """
    values = {
        "LANGSMITH_TRACING": str(loaded_settings.langsmith_tracing).lower(),
        "LANGSMITH_API_KEY": loaded_settings.langsmith_api_key,
        "LANGSMITH_PROJECT": loaded_settings.langsmith_project,
        "LANGCHAIN_TRACING_V2": str(loaded_settings.langchain_tracing_v2).lower(),
        "LANGCHAIN_API_KEY": loaded_settings.langchain_api_key,
        "LANGCHAIN_PROJECT": loaded_settings.langchain_project,
    }
    for key, value in values.items():
        if value:
            os.environ[key] = value


# 模块级变量：import 时就创建好，其他模块直接用 settings.xxx
settings = get_settings()
