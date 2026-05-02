from typing import TypedDict


class AgentState(TypedDict):
    """Agent 状态。"""
    session_id: str
    message: str
    intent: str | None
    slots: dict
    search_results: list
    confirmation: dict | None
    reply: str
    cards: list
    actions: list
    sources: list
