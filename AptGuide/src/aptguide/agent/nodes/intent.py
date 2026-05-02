from aptguide.agent.state import AgentState
from aptguide.llm.client import LLMClient

INTENT_PROMPT = """你是一个租房助手的意图识别模块。根据用户消息，判断用户意图。

可能的意图：
- kb_qa: 租房规则问答（押金、退租、续约、预约规则等）
- room_search: 找房需求（预算、区域、偏好等）
- appointment_create: 预约看房
- other: 其他

只返回意图名称，不要返回其他内容。

用户消息：{message}"""


async def intent_node(state: AgentState, llm: LLMClient) -> dict:
    """意图识别节点。"""
    prompt = INTENT_PROMPT.format(message=state["message"])
    intent = await llm.generate(prompt)

    # 清理响应
    intent = intent.strip().lower()
    if intent not in ["kb_qa", "room_search", "appointment_create"]:
        intent = "other"

    return {"intent": intent}
