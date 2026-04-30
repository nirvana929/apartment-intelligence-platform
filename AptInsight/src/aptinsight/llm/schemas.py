"""LLM structured output schemas for JSON mode."""

from pydantic import BaseModel, Field


class SqlGenerationOutput(BaseModel):
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
