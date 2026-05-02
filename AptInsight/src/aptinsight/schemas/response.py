from typing import Any

from pydantic import BaseModel


# [设计] 响应模型统一用 Pydantic BaseModel
# FastAPI 会自动序列化为 JSON，字段名会变成 camelCase（如果用 alias 的话）
# 这里直接用 snake_case，前端需要适配

class Column(BaseModel):
    """查询结果的列描述"""
    name: str
    type: str | None = None


class ErrorDetail(BaseModel):
    """错误详情"""
    code: str
    message: str
    details: dict[str, Any] | None = None


# [设计] ChatResponse 包含了所有可能的返回内容
# rows + columns 是表格数据，chart 是 ECharts 配置，answer 是文字总结
# 这样前端一个接口就能拿到所有需要的数据
class ChatResponse(BaseModel):
    trace_id: str           # 链路追踪 ID，和请求对应
    answer: str             # LLM 生成的文字总结
    summary: str = ""       # 简短摘要
    rows: list[dict[str, Any]]  # 查询结果行
    columns: list[Column]   # 列描述
    chart: dict[str, Any] | None = None  # ECharts 图表配置
    sql: str | None = None  # 实际执行的 SQL（方便调试）
    warnings: list[str] = []  # 警告信息
    error: str | None = None  # 错误信息
    processing_time_ms: float = 0.0  # 处理耗时
