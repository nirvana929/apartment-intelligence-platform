from aptguide.agent.state import AgentState
from aptguide.llm.client import LLMClient
from aptguide.tools.mock import MockToolClient
from aptguide.memory.session import SessionMemory


TOOL_REPLY_PROMPT = """你是一个租房助手。工具调用已完成，请生成回复。

工具类型：{tool_type}
工具结果：{tool_result}

请生成一个友好的回复，告知用户操作结果。"""


async def tool_node(
    state: AgentState,
    llm: LLMClient,
    tool_client: MockToolClient,
    memory: SessionMemory,
) -> dict:
    """工具调用节点"""
    confirmation = state["confirmation"]

    if not confirmation:
        return {
            "reply": "没有待执行的操作。",
            "confirmation": None,
        }

    tool_type = confirmation["type"]
    params = confirmation["params"]

    # 调用对应工具
    if tool_type == "appointment_create":
        result = await tool_client.create_appointment(
            room_id=params["room_id"],
            appointment_time=params["appointment_time"],
            user_id="demo-user",
        )
    else:
        result = {"error": f"未知工具类型：{tool_type}"}

    # 生成回复
    prompt = TOOL_REPLY_PROMPT.format(
        tool_type=tool_type,
        tool_result=result,
    )
    reply = await llm.generate(prompt)

    # 清除待确认操作
    await memory.clear_pending_confirmation(state["session_id"])

    return {
        "reply": reply,
        "confirmation": None,
    }
