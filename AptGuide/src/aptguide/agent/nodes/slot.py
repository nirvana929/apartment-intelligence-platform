"""
槽位抽取节点 —— 从用户消息中提取结构化参数。

【学习要点】
1. 槽位（Slot）= 对话系统中的参数。例如"天河区3000以内的房子"中：
   - district = "天河区"
   - max_rent = 3000
2. LLM 作为信息抽取器：让 LLM 从自然语言中提取结构化 JSON
3. JSON 解析容错：LLM 返回的 JSON 可能格式不对，需要 try/except 保护
4. 增量合并：新抽取的槽位和已有槽位合并，已有值不覆盖
"""

import json
import re
from datetime import datetime

from aptguide.agent.state import AgentState
from aptguide.llm.client import LLMClient

# 通用提示词模板 —— {slot_instructions} 会根据意图替换为不同的槽位定义
SLOT_PROMPT = """从用户消息中抽取以下槽位。

{slot_instructions}

只返回 JSON，不要返回其他内容。值为 null 表示未提及。
时间类槽位请转为绝对时间，格式 "YYYY-MM-DD HH:mm"。当前日期时间：{now}

用户消息：{message}
当前槽位：{current_slots}"""

# 找房意图的槽位定义
ROOM_SLOT_INSTRUCTIONS = """槽位定义（找房）：
- max_rent: 最高预算（整数）
- district: 区域（字符串）
- tags: 偏好标签（字符串数组，如["安静", "适合考研"]）
- payment_type: 支付方式（"月付" | "季付" | "半年付" | "年付" | null）
- lease_term: 租期（"短期" | "长期" | null）"""

# 预约意图的槽位定义
APPOINTMENT_SLOT_INSTRUCTIONS = """槽位定义（预约看房）：
- room_id: 房间ID（整数，从消息中的"房间号XXXX"或"room_id"提取）
- room_title: 房间标题（字符串，如"天河北寓 904"）
- appointment_time: 预约时间（字符串，格式"YYYY-MM-DD HH:mm"，如"2026-05-05 14:00"）"""


async def slot_node(state: AgentState, llm: LLMClient) -> dict:
    """
    槽位抽取节点。

    流程：
    1. 根据意图选择对应的槽位定义（找房 vs 预约）
    2. 把用户消息、当前已有槽位填入提示词
    3. 调用 LLM 生成 JSON 格式的槽位
    4. 解析 JSON 并与已有槽位合并
    """
    intent = state.get("intent", "")

    # 根据意图选择不同的槽位定义
    if intent == "appointment_create":
        instructions = APPOINTMENT_SLOT_INSTRUCTIONS
    else:
        instructions = ROOM_SLOT_INSTRUCTIONS

    # json.dumps 把 dict 转成 JSON 字符串，ensure_ascii=False 允许中文
    # 把当前已有槽位传给 LLM，这样它不会重复抽取已有的值
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    prompt = SLOT_PROMPT.format(
        slot_instructions=instructions,
        message=state["message"],
        current_slots=json.dumps(state["slots"], ensure_ascii=False),
        now=now,
    )

    response = await llm.generate(prompt)

    # 提取 JSON —— LLM 有时会在 JSON 前后加 ```json ``` 代码块标记
    # re.search 用正则表达式匹配 ```json\n...\n``` 中间的内容
    # re.DOTALL 让 . 也能匹配换行符
    json_match = re.search(r"```json\n(.*?)\n```", response, re.DOTALL)
    json_str = json_match.group(1) if json_match else response  # 没有代码块就用原始响应

    # 解析 JSON —— 用 try/except 保护，因为 LLM 可能返回非法 JSON
    try:
        new_slots = json.loads(json_str)
    except json.JSONDecodeError:
        new_slots = {}  # 解析失败就返回空 dict，不影响已有槽位

    # 合并槽位（增量更新）：
    # 1. 先复制已有槽位（避免修改原始 state）
    # 2. 遍历新槽位，只更新值不为 None 的字段
    # 这样用户说"天河区3000以内"后，再说"改成3500"，只会更新 max_rent，district 不变
    slots = state["slots"].copy()
    for key, value in new_slots.items():
        if value is not None:
            slots[key] = value

    return {"slots": slots}
