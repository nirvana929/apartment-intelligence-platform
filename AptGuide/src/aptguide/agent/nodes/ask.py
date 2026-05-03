"""
追问生成节点 —— 当槽位不完整时，生成友好的追问。

【学习要点】
1. 对话补全：用户说"我想找房子"，但没说预算和区域，系统需要追问
2. 业务逻辑和 LLM 分工：
   - get_missing_slots() 是纯业务逻辑（判断哪些槽位缺失）
   - LLM 负责把缺失信息转化为自然语言追问
3. 这种设计让核心逻辑可测试（不依赖 LLM），同时保持回复自然
"""

from aptguide.agent.state import AgentState
from aptguide.llm.client import LLMClient

ASK_PROMPT = """你是一个租房助手。用户的需求信息不完整，需要追问缺失的槽位。

当前槽位：{slots}
缺失槽位：{missing_slots}

请生成一个友好的追问，询问缺失的信息。"""


def get_missing_slots(slots: dict, intent: str = "") -> list[str]:
    """
    获取缺失的槽位（纯函数，不依赖 LLM）。

    这是一个"规则引擎"：根据意图判断哪些槽位是必填的。
    和 LLM 分开的好处：
    1. 可以单独测试，不需要调用 LLM
    2. 规则明确，不会因为 LLM 的随机性而变化
    """
    missing = []
    if intent == "appointment_create":
        if not slots.get("room_id") and not slots.get("room_title"):
            missing.append("房间号或房间名称")
        if not slots.get("appointment_time"):
            missing.append("预约时间")
    else:
        if not slots.get("max_rent"):
            missing.append("预算")
        if not slots.get("district"):
            missing.append("区域")
    return missing


async def ask_node(state: AgentState, llm: LLMClient) -> dict:
    """
    追问生成节点。

    流程：
    1. 检查缺失的槽位
    2. 如果没有缺失，返回空回复（不需要追问）
    3. 如果有缺失，让 LLM 生成自然语言追问
    """
    intent = state.get("intent", "")
    missing = get_missing_slots(state["slots"], intent)

    if not missing:
        # 槽位充足，不需要追问
        return {"reply": ""}

    # 把缺失的槽位列表传给 LLM，让它生成自然语言追问
    prompt = ASK_PROMPT.format(
        slots=state["slots"],
        missing_slots=", ".join(missing),  # ["预算", "区域"] → "预算, 区域"
    )

    reply = await llm.generate(prompt)
    return {"reply": reply}
