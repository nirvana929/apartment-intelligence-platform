"""
工具调用节点 —— 执行实际的业务操作。

【学习要点】
1. 查询 vs 写入：
   - 查询（appointment_query, lease_query）：直接调用，不需要确认
   - 写入（appointment_create）：需要用户二次确认后才执行
2. 安全规则：写操作必须二次确认（CLAUDE.md 中的安全规则）
3. 数据转换：工具返回的原始数据 → 前端需要的卡片格式
4. room_id 的防御性处理：用户可能给字符串、整数或 None
"""

from aptguide.agent.state import AgentState
from aptguide.llm.client import LLMClient
from aptguide.memory.session import SessionMemory
from aptguide.tools.client import LeaseToolClient

TOOL_REPLY_PROMPT = """你是一个租房助手。工具调用已完成，请生成回复。

工具类型：{tool_type}
工具结果：{tool_result}

请生成一个友好的回复，告知用户操作结果。"""


async def tool_node(
    state: AgentState,
    llm: LLMClient,
    tool_client: LeaseToolClient,
    memory: SessionMemory,
) -> dict:
    """
    工具调用节点。

    分两种情况：
    1. 查询类工具：直接调用 Java 后端接口，返回结果卡片
    2. 写操作工具：从 confirmation 中取出参数，执行操作后清除 confirmation
    """
    intent = state.get("intent", "")
    confirmation = state.get("confirmation")

    # ========== 查询类工具 ==========
    # 查询操作不需要 confirmation，用户问"我的预约"就直接查

    if intent == "appointment_query":
        # 调用 Java 后端查询预约列表
        result = await tool_client.list_my_appointments(user_id=state.get("user_id", "1"))
        appointments = result if isinstance(result, list) else result.get("appointments", [])

        # 列表推导式：把原始数据转换为前端卡片格式
        cards = [
            {
                "type": "appointment",
                "appointment_id": a.get("appointment_id"),
                "apartment_name": a.get("apartment_name", ""),
                "room_number": a.get("room_number", ""),
                "appointment_time": a.get("appointment_time", ""),
                "status": a.get("status", ""),
            }
            for a in appointments
        ]

        # 让 LLM 把工具结果转化为自然语言回复
        prompt = TOOL_REPLY_PROMPT.format(
            tool_type="appointment_query",
            tool_result=result,
        )
        reply = await llm.generate(prompt)
        return {"reply": reply, "cards": cards, "confirmation": None}

    if intent == "lease_query":
        result = await tool_client.list_my_leases(user_id=state.get("user_id", "1"))
        leases = result if isinstance(result, list) else result.get("leases", [])
        cards = [
            {
                "type": "lease",
                "lease_id": lease.get("lease_id"),
                "apartment_name": lease.get("apartment_name", ""),
                "room_number": lease.get("room_number", ""),
                "start_date": lease.get("start_date", ""),
                "end_date": lease.get("end_date", ""),
                "rent": lease.get("rent", 0),
                "status": lease.get("status", ""),
            }
            for lease in leases
        ]
        prompt = TOOL_REPLY_PROMPT.format(
            tool_type="lease_query",
            tool_result=result,
        )
        reply = await llm.generate(prompt)
        return {"reply": reply, "cards": cards, "confirmation": None}

    # ========== 写操作工具 ==========
    # 写操作需要 confirmation（用户已确认的待执行操作）

    if not confirmation:
        # 没有待执行的操作（理论上不应该走到这里）
        return {
            "reply": "没有待执行的操作。",
            "confirmation": None,
        }

    # 从 confirmation 中获取工具类型和参数
    # 为什么不依赖 intent？因为用户回复"确认"时，intent 可能被分类为 "other"
    # 所以把工具类型存在 confirmation 中，更可靠
    tool_type = confirmation["type"]
    params = confirmation["params"]

    if tool_type == "appointment_create":
        # room_id 和 apartment_id 的防御性处理：
        # 用户可能给整数（123）、字符串（"123"）、None（没给）
        # 需要统一转成整数
        room_id = params.get("room_id")
        if not room_id:
            room_id = params.get("room_title", "unknown")
        try:
            room_id = int(room_id)
        except (ValueError, TypeError):
            room_id = 0  # 转换失败用 0 降级

        apartment_id = params.get("apartment_id", 0)
        try:
            apartment_id = int(apartment_id)
        except (ValueError, TypeError):
            apartment_id = 0

        result = await tool_client.create_appointment(
            user_id=state.get("user_id", "1"),
            apartment_id=apartment_id,
            room_id=room_id,
            appointment_time=params["appointment_time"],
            remark=params.get("remark", "AptGuide 预约"),
        )
    else:
        result = {"error": f"未知工具类型：{tool_type}"}

    prompt = TOOL_REPLY_PROMPT.format(
        tool_type=tool_type,
        tool_result=result,
    )
    reply = await llm.generate(prompt)

    # 清除待确认操作 —— 已经执行完了，不需要再保留
    await memory.clear_pending_confirmation(state["session_id"])

    return {
        "reply": reply,
        "confirmation": None,  # 清除 confirmation，表示操作已完成
    }
