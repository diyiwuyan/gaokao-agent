"""LangGraph ReAct Agent 核心

架构说明：
- 基于 LangGraph 构建的 ReAct (Reason + Act) 循环
- Agent 自主决定何时调用哪个工具
- 支持多轮对话和记忆
- 内置反思纠错机制
"""

from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from app.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from app.agent.prompts import SYSTEM_PROMPT
from app.tools.score_analysis import score_analysis
from app.tools.college_search import college_search
from app.tools.admission_query import admission_query
from app.tools.probability_calc import probability_calc
from app.tools.major_recommend import major_recommend
from app.tools.college_compare import college_compare
from app.tools.policy_interpret import policy_interpret
from app.tools.strategy_suggest import strategy_suggest


# ============ 状态定义 ============

class AgentState(TypedDict):
    """Agent 状态，在图的整个生命周期中传递"""
    messages: Annotated[list[BaseMessage], add_messages]


# ============ 工具集 ============

ALL_TOOLS = [
    score_analysis,
    college_search,
    admission_query,
    probability_calc,
    major_recommend,
    college_compare,
    policy_interpret,
    strategy_suggest,
]


# ============ LLM 初始化 ============

def create_llm():
    """创建 LLM 实例"""
    return ChatOpenAI(
        model=LLM_MODEL,
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        temperature=0.3,  # 志愿填报需要较低温度保证准确性
        max_tokens=4096,
    )


# ============ 节点定义 ============

def call_model(state: AgentState) -> dict:
    """推理节点：调用 LLM 进行思考和决策
    
    LLM 会根据对话历史和系统提示：
    1. 分析用户需求
    2. 决定是否需要调用工具
    3. 如果需要，选择合适的工具并构造参数
    4. 如果不需要，直接给出回答
    """
    llm = create_llm()
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    messages = state["messages"]

    # 确保系统提示在最前面
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)

    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def should_continue(state: AgentState) -> str:
    """路由函数：判断是否继续调用工具
    
    检查最后一条消息：
    - 如果包含 tool_calls → 转到工具节点执行
    - 如果不包含 → 结束，返回最终回答
    """
    last_message = state["messages"][-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


# ============ 构建图 ============

def build_agent_graph():
    """构建 LangGraph Agent 图
    
    图结构：
    
    [START] → [call_model] → (判断) → [tools] → [call_model] → ...
                                ↓                       
                              [END] (无工具调用时直接结束)
    """
    # 创建工具节点
    tool_node = ToolNode(ALL_TOOLS)

    # 构建状态图
    graph = StateGraph(AgentState)

    # 添加节点
    graph.add_node("agent", call_model)
    graph.add_node("tools", tool_node)

    # 设置入口
    graph.set_entry_point("agent")

    # 添加条件边
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END,
        },
    )

    # 工具执行完后回到 agent 继续推理
    graph.add_edge("tools", "agent")

    # 编译图（带记忆功能）
    memory = MemorySaver()
    compiled_graph = graph.compile(checkpointer=memory)

    return compiled_graph


# ============ 对话接口 ============

# 全局 Agent 实例
_agent = None


def get_agent():
    """获取/创建全局 Agent 实例"""
    global _agent
    if _agent is None:
        _agent = build_agent_graph()
    return _agent


def chat(user_message: str, thread_id: str = "default") -> str:
    """与 Agent 对话
    
    Args:
        user_message: 用户输入
        thread_id: 会话ID（支持多会话隔离）
    
    Returns:
        Agent 的回复文本
    """
    agent = get_agent()

    config = {"configurable": {"thread_id": thread_id}}

    response = agent.invoke(
        {"messages": [HumanMessage(content=user_message)]},
        config=config,
    )

    # 获取最后一条 AI 消息
    last_message = response["messages"][-1]
    return last_message.content


async def chat_stream(user_message: str, thread_id: str = "default"):
    """流式对话（用于前端）
    
    Args:
        user_message: 用户输入
        thread_id: 会话ID
    
    Yields:
        Agent 的回复片段
    """
    agent = get_agent()
    config = {"configurable": {"thread_id": thread_id}}

    async for event in agent.astream_events(
        {"messages": [HumanMessage(content=user_message)]},
        config=config,
        version="v2",
    ):
        kind = event["event"]
        if kind == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                yield content
