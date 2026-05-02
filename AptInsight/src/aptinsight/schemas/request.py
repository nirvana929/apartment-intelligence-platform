from uuid import uuid4

from pydantic import BaseModel, Field


# [框架] Pydantic BaseModel 用作请求体校验
# FastAPI 会自动解析 JSON 请求体，用这个 schema 校验
# 不符合的请求会自动返回 422 错误，不需要手写校验逻辑
class ChatRequest(BaseModel):
    # [框架] Field(min_length=1, max_length=500) 做参数校验
    # 空字符串或超长都会被 FastAPI 自动拒绝
    question: str = Field(min_length=1, max_length=500)

    # [设计] session_id 可选：前端传了就用，没传就 None（后续可以生成）
    session_id: str | None = None

    # [框架] default_factory 每次创建对象时都会调用 lambda 生成新的 uuid
    # 如果用 default=uuid4().hex，所有请求会共享同一个值（只在模块加载时算一次）
    trace_id: str = Field(default_factory=lambda: uuid4().hex)
