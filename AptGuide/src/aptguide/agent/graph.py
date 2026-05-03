"""
Agent 工作流图定义 —— 用 LangGraph 编排所有节点。

【学习要点】
1. LangGraph 的核心概念：StateGraph（有状态的图）
   - 节点（Node）= 处理函数，接收 state，返回更新
   - 边（Edge）= 节点之间的连接，决定下一步去哪
   - 条件边（Conditional Edge）= 根据 state 内容动态决定下一步

2. 工作流模式：
   普通边：A → B（无条件跳转）
   条件边：A → [B 或 C 或 D]（根据函数返回值决定）

3. END 是 LangGraph 的特殊标记，表示流程结束

4. compile() 把图定义编译成可执行的对象

图的完整结构：
    intent ──(条件)──→ kb_search ──→ reply ──→ END
         ├──(条件)──→ slot ──(条件)──→ ask ──→ END
         │                    ├──(条件)──→ room_search → rerank → reply → END
         │                    └──(条件)──→ confirm ──(条件)──→ tool → reply → END
         └──(条件)──→ tool → reply → END
"""

from langgraph.graph import END, StateGraph

from aptguide.agent.state import AgentState
from aptguide.llm.client import LLMClient
from aptguide.memory.session import SessionMemory
from aptguide.tools.client import LeaseToolClient
from aptguide.vector.kb_search import KBSearch
from aptguide.vector.room_index import RoomIndex


def create_agent_graph(
    llm: LLMClient,
    kb: KBSearch,
    room_index: RoomIndex,
    tool_client: LeaseToolClient,
    memory: SessionMemory,
):
    """
    创建 Agent 工作流图。

    参数说明：
    - llm: 大语言模型客户端，所有节点用它来生成回复
    - kb: 知识库检索，用于回答租房规则类问题
    - room_index: 房源索引，用于搜索房间
    - tool_client: Java 后端工具接口客户端（这里用 Mock 版本）
    - memory: 会话记忆，存储待确认操作等状态

    为什么把依赖作为参数传入（依赖注入），而不是在函数内部创建？
    因为这样可以：
    1. 测试时传入 mock 对象，不需要真实连接
    2. 不同环境可以用不同实现（开发用 mock，生产用真实）
    """
    from aptguide.agent.nodes.ask import ask_node
    from aptguide.agent.nodes.confirm import confirm_node
    from aptguide.agent.nodes.intent import intent_node
    from aptguide.agent.nodes.kb_search import kb_search_node
    from aptguide.agent.nodes.reply import reply_node
    from aptguide.agent.nodes.rerank import rerank_node
    from aptguide.agent.nodes.room_search import room_search_node
    from aptguide.agent.nodes.slot import slot_node
    from aptguide.agent.nodes.tool import tool_node

    # 创建状态图，AgentState 是所有节点共享的状态类型
    workflow = StateGraph(AgentState)

    # ========== 添加节点 ==========
    # 每个节点是一个 async 函数，接收 state，返回一个 dict（状态更新）
    # 为什么用闭包（lambda/内部函数）？
    # 因为 LangGraph 的节点函数签名是 f(state) -> dict，
    # 但我们还需要注入 llm、kb 等依赖，所以用闭包把依赖"捕获"进来

    async def _intent(state):
        return await intent_node(state, llm)  # 调用实际的意图识别逻辑

    async def _slot(state):
        return await slot_node(state, llm)

    async def _ask(state):
        return await ask_node(state, llm)

    async def _kb_search(state):
        return await kb_search_node(state, kb)

    async def _room_search(state):
        return await room_search_node(state, room_index)

    async def _rerank(state):
        return await rerank_node(state, llm)

    async def _confirm(state):
        return await confirm_node(state, llm, memory)

    async def _tool(state):
        return await tool_node(state, llm, tool_client, memory)

    async def _reply(state):
        return await reply_node(state, llm)

    # 注册节点：给每个节点一个名字（字符串）和处理函数
    workflow.add_node("intent", _intent)
    workflow.add_node("slot", _slot)
    workflow.add_node("ask", _ask)
    workflow.add_node("kb_search", _kb_search)
    workflow.add_node("room_search", _room_search)
    workflow.add_node("rerank", _rerank)
    workflow.add_node("confirm", _confirm)
    workflow.add_node("tool", _tool)
    workflow.add_node("reply", _reply)

    # ========== 定义边（节点之间的连接）==========

    # set_entry_point = 设置图的入口节点（第一个执行的节点）
    workflow.set_entry_point("intent")

    # add_conditional_edges = 条件边
    # 语法：add_conditional_edges(源节点, 路由函数, {返回值: 目标节点})
    # 路由函数接收 state，返回一个字符串，LangGraph 根据这个字符串决定去哪个节点

    # intent 节点之后：根据意图分类结果路由
    workflow.add_conditional_edges(
        "intent",
        route_intent,  # 路由函数
        {
            "kb_search": "kb_search",  # 知识库问答 → 检索知识库
            "slot": "slot",            # 找房/预约 → 抽取槽位
            "tool": "tool",            # 查询类操作 → 直接调用工具
            "reply": "reply",          # 其他 → 直接回复
        },
    )

    # slot 节点之后：根据槽位完整性路由
    workflow.add_conditional_edges(
        "slot",
        check_slots,
        {
            "ask": "ask",              # 缺少必要槽位 → 追问用户
            "room_search": "room_search",  # 槽位完整 → 搜索房源
            "confirm": "confirm",      # 预约槽位完整 → 生成确认摘要
            "reply": "reply",          # 其他 → 直接回复
        },
    )

    # confirm 节点之后：根据用户确认/取消路由
    workflow.add_conditional_edges(
        "confirm",
        check_confirmation,
        {
            "tool": "tool",   # 用户确认 → 执行操作
            "reply": "reply", # 用户取消 → 回复取消信息
        },
    )

    # add_edge = 无条件边（固定跳转）
    workflow.add_edge("room_search", "rerank")  # 搜索完 → 重新排序并生成推荐理由
    workflow.add_edge("rerank", "reply")        # 排序完 → 生成回复
    workflow.add_edge("kb_search", "reply")     # 知识库检索完 → 生成回复
    workflow.add_edge("tool", "reply")          # 工具执行完 → 生成回复
    workflow.add_edge("ask", END)               # 追问完 → 结束（等用户回复）
    workflow.add_edge("reply", END)             # 回复完 → 结束

    # compile() 把图定义编译成可执行对象
    # 编译后可以用 graph.invoke(state) 或 graph.ainvoke(state) 执行
    return workflow.compile()


def route_intent(state: AgentState) -> str:
    """
    意图路由函数 —— 根据 intent 字段决定下一步去哪。

    这是一个"纯函数"：只读取 state，返回一个字符串，不修改 state。
    LangGraph 调用它时，会用返回值匹配 conditional_edges 中的映射表。
    """
    # 优先级：如果有待确认操作，用户的回复一定是确认/取消
    if state.get("confirmation"):
        msg = state["message"].strip()
        if msg in ("确认", "确定", "是", "好"):
            return "tool"
        elif msg in ("取消", "不", "不要"):
            return "reply"

    # 根据意图分类结果路由
    if state["intent"] == "kb_qa":
        return "kb_search"       # 租房规则问答 → 知识库检索
    if state["intent"] == "room_search":
        return "slot"            # 找房 → 先抽取槽位（预算、区域等）
    if state["intent"] == "appointment_create":
        return "slot"            # 预约看房 → 先抽取槽位（房间、时间等）
    if state["intent"] in ("appointment_query", "lease_query"):
        return "tool"            # 查询类操作 → 直接调用工具（不需要槽位）
    return "reply"               # 其他意图 → 直接回复


def check_slots(state: AgentState) -> str:
    """
    槽位检查函数 —— 判断抽取的槽位是否足够。

    不满意图需要不同的必填槽位：
    - 找房：需要 max_rent（预算）和 district（区域）
    - 预约：需要 room_id/room_title（房间）和 appointment_time（时间）

    槽位不够 → ask（追问用户）
    槽位够了 → 执行后续操作
    """
    slots = state["slots"]
    if state["intent"] == "room_search":
        # 找房：预算和区域是必填的
        if not slots.get("max_rent") or not slots.get("district"):
            return "ask"         # 缺槽位 → 追问
        return "room_search"     # 槽位完整 → 搜索房源

    elif state["intent"] == "appointment_create":
        # 预约：房间和时间是必填的
        has_room = slots.get("room_id") or slots.get("room_title")
        if not has_room or not slots.get("appointment_time"):
            return "ask"         # 缺槽位 → 追问
        return "confirm"         # 槽位完整 → 生成确认摘要

    return "reply"               # 其他意图 → 直接回复


def check_confirmation(state: AgentState) -> str:
    """
    确认检查函数 —— 用户回复"确认"还是"取消"。

    这是"写操作二次确认"安全规则的实现：
    预约看房等写操作，先展示摘要给用户，用户说"确认"才真正执行。
    """
    if state["confirmation"]:
        message = state["message"].lower()
        if "确认" in message or "确定" in message or "是" in message:
            return "tool"    # 用户确认 → 执行操作
        elif "取消" in message or "不" in message:
            return "reply"   # 用户取消 → 回复取消信息
    return "reply"           # 默认 → 回复
