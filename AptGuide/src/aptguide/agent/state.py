"""
Agent 状态定义 —— LangGraph 的核心概念。

【学习要点】
1. TypedDict = 带类型提示的字典。和普通 dict 用法一样，但 IDE 能检查字段名和类型
2. LangGraph 的 StateGraph 要求你定义一个"状态类型"，所有节点共享这个状态
3. 每个节点函数接收 state（当前状态），返回一个 dict（要更新的字段）
4. LangGraph 会自动合并：节点返回的 dict 会更新到 state 中，其他字段不变

状态流转示例：
  用户说 "天河区3000以内的房子" →
  intent_node 返回 {"intent": "room_search"} →
  slot_node 返回 {"slots": {"district": "天河区", "max_rent": 3000}} →
  room_search_node 返回 {"search_results": [...]} →
  rerank_node 返回 {"reply": "推荐理由...", "cards": [...]} →
  结束
"""

from typing import TypedDict


class AgentState(TypedDict):
    """
    Agent 工作流的共享状态。

    每个字段在不同节点中被读取或写入：
    - session_id: 会话标识（贯穿整个流程）
    - message: 用户当前消息
    - intent: 意图分类结果（由 intent_node 写入）
    - slots: 抽取的参数槽位（由 slot_node 写入），如 {"district": "天河区", "max_rent": 3000}
    - search_results: 检索结果（由 kb_search_node 或 room_search_node 写入）
    - confirmation: 待确认操作（由 confirm_node 写入，tool_node 消费后清除）
    - reply: 最终回复文本（由 reply_node 或其他节点写入）
    - cards: 结构化卡片数据（房源卡片、预约卡片等，前端用来渲染）
    - actions: 可执行操作列表（如"查看详情"、"预约看房"按钮）
    - sources: 信息来源（引用的知识库文档）
    """

    session_id: str
    message: str
    user_id: str | None  # 由 lease 后端注入的用户 ID
    intent: str | None  # str | None 是 Python 3.10+ 的联合类型语法，等价于 Optional[str]
    slots: dict
    search_results: list
    confirmation: dict | None
    reply: str
    cards: list
    actions: list
    sources: list
