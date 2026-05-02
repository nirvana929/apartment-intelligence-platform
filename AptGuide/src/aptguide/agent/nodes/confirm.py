from aptguide.agent.state import AgentState
from aptguide.llm.client import LLMClient
from aptguide.memory.session import SessionMemory


CONFIRM_PROMPT = """你是一个租房助手。用户想要预约看房，需要生成操作摘要等待确认。

用户消息：{message}
预约信息：
- 房间：{room_title}
- 时间：{appointment_time}

请生成一个友好的确认摘要，询问用户是否确认预约。"""


async def confirm_node(
    state: AgentState,
    llm: LLMClient,
    memory: SessionMemory,
) -> dict:
    """预约确认节点"""
    slots = state["slots"]
    room_id = slots.get("room_id")
    appointment_time = slots.get("appointment_time")

    # 获取房间标题
    room_title = f"房间 {room_id}"
    for room in state["search_results"]:
        if room["room_id"] == room_id:
            room_title = room["title"]
            break

    # 生成确认摘要
    prompt = CONFIRM_PROMPT.format(
        message=state["message"],
        room_title=room_title,
        appointment_time=appointment_time,
    )
    reply = await llm.generate(prompt)

    # 存储待确认操作
    confirmation = {
        "type": "appointment_create",
        "params": {
            "room_id": room_id,
            "appointment_time": appointment_time,
            "room_title": room_title,
        },
        "summary": f"{room_title}，{appointment_time}",
    }

    await memory.store_pending_confirmation(state["session_id"], confirmation)

    return {
        "reply": reply,
        "confirmation": confirmation,
    }
