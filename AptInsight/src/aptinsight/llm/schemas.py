"""LLM structured output schemas for JSON mode."""

from pydantic import BaseModel, Field


# [框架] Pydantic BaseModel + Field 用来定义 LLM 的输出格式
# LLM 生成 JSON 后，OpenAI SDK 会自动用这个 schema 校验和解析
# 如果 LLM 输出不符合 schema，SDK 会报错或重试
# [设计] 每个字段都给了 default 值，这样 LLM 漏填某个字段也不会报错

class SqlGenerationOutput(BaseModel):
    # [框架] Field(description=...) 不只是文档，LLM SDK 会把 description 传给模型
    # 模型会根据 description 理解每个字段应该填什么
    need_sql: bool = Field(description="Whether the question requires SQL query")
    chart_type: str = Field(default="table", description="bar|line|pie|table")
    sql: str = Field(default="", description="Generated MySQL SELECT query")
    reason: str = Field(default="", description="Why this SQL was generated")


class IntentOutput(BaseModel):
    intent: str = Field(description="data_query|trend_analysis|distribution_analysis|diagnosis|metric_explanation|unsupported")
    domain: str = Field(default="", description="Business domain: appointment|lease|room|rent|browsing")
    need_sql: bool = Field(default=True)
    need_chart: bool = Field(default=False)
    time_range: str = Field(default="", description="Time range hint")
    refusal_reason: str = Field(default="", description="Why unsupported if applicable")
