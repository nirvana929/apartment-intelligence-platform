"""
意图识别节点 —— Agent 的"大脑入口"。

【学习要点】
1. Prompt Engineering：通过精心设计的提示词，让 LLM 做分类任务
2. 白名单校验：LLM 的输出不可信，必须校验是否在预期范围内
3. 节点函数签名：f(state: AgentState, llm: LLMClient) -> dict
   - 接收当前状态和依赖
   - 返回一个 dict，LangGraph 会自动合并到 state 中
"""

from aptguide.agent.state import AgentState
from aptguide.llm.client import LLMClient

# 提示词模板 —— 用 {message} 占位符，运行时替换为用户消息
# 为什么让 LLM "只返回意图名称"？—— 减少输出长度，提高分类准确性
INTENT_PROMPT = """你是一个租房助手的意图识别模块。根据用户消息，判断用户意图。

可能的意图：
- kb_qa: 租房规则问答（押金、退租、续约、预约规则等）
- room_search: 找房需求（预算、区域、偏好等）
- appointment_create: 预约看房
- appointment_query: 查询自己的预约（"我的预约"、"我有几个预约"、"查看预约"）
- lease_query: 查询自己的租约（"我的租约"、"租约到期时间"、"合同信息"）
- other: 其他

只返回意图名称，不要返回其他内容。

用户消息：{message}"""


async def intent_node(state: AgentState, llm: LLMClient) -> dict:
    """
    意图识别节点。

    流程：
    1. 把用户消息填入提示词模板
    2. 调用 LLM 生成意图分类
    3. 校验输出是否在白名单内（LLM 可能返回意外内容）
    4. 返回 {"intent": "xxx"} 更新状态
    """
    # format() 把 {message} 替换为实际的用户消息
    prompt = INTENT_PROMPT.format(message=state["message"])

    # 调用 LLM 生成回复（这里 LLM 被当作分类器使用）
    intent = await llm.generate(prompt)

    # 清理响应：strip() 去掉首尾空白，lower() 转小写
    intent = intent.strip().lower()

    # 白名单校验：如果 LLM 返回了不在列表中的意图，降级为 "other"
    # 这是防御性编程 —— 永远不要信任 LLM 的输出
    if intent not in ["kb_qa", "room_search", "appointment_create", "appointment_query", "lease_query"]:
        intent = "other"

    # 返回要更新的字段 —— LangGraph 会把这个 dict 合并到 state 中
    return {"intent": intent}
