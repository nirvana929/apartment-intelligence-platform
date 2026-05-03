"""
预约确认节点 —— 写操作的"安全阀"。

【学习要点】
1. 二次确认模式：写操作（预约、取消等）先展示摘要，用户确认后才执行
2. confirmation 字段：存储待执行的操作信息，tool_node 读取后执行
3. 状态持久化：confirmation 同时存入 memory，防止会话丢失
4. 从搜索结果匹配房间标题：优先用精确匹配，降级用用户输入的标题
"""

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
    """
    预约确认节点。

    流程：
    1. 从槽位中取出房间信息和预约时间
    2. 尝试从搜索结果中匹配更准确的房间标题
    3. 生成确认摘要（让用户看到"预约 XX房间，XX时间"）
    4. 把待确认操作存入 memory
    5. 返回确认摘要和 confirmation 字段
    """
    slots = state["slots"]
    room_id = slots.get("room_id")
    appointment_time = slots.get("appointment_time")

    # 获取房间标题 —— 优先用槽位中的标题，降级用 "房间 {id}"
    room_title = slots.get("room_title", "")
    if not room_title and room_id:
        room_title = f"房间 {room_id}"

    # 从搜索结果中匹配更准确的标题
    # 为什么需要这一步？因为用户可能说"预约904"，但搜索结果中有"天河北寓 904"
    for room in state.get("search_results", []):
        if (room_id and room.get("room_id") == room_id) or \
           (room_title and room.get("title") == room_title):
            room_title = room["title"]
            room_id = room.get("room_id", room_id)
            break

    # 让 LLM 生成友好的确认摘要
    prompt = CONFIRM_PROMPT.format(
        message=state["message"],
        room_title=room_title,
        appointment_time=appointment_time,
    )
    reply = await llm.generate(prompt)

    # 构造 confirmation 对象 —— 这是写操作的"凭证"
    # tool_node 会读取这个对象来执行实际操作
    confirmation = {
        "type": "appointment_create",          # 操作类型
        "params": {                             # 操作参数
            "room_id": room_id,
            "appointment_time": appointment_time,
            "room_title": room_title,
        },
        "summary": f"{room_title}，{appointment_time}",  # 人类可读的摘要
    }

    # 存入 memory —— 即使会话中断，也能恢复待确认操作
    await memory.store_pending_confirmation(state["session_id"], confirmation)

    return {
        "reply": reply,
        "confirmation": confirmation,  # LangGraph 会把这个存入 state
    }
