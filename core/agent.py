# core/agent.py
# This is Leo's BRAIN — built as a LangGraph "state graph" instead of a simple function call.
# Why a graph instead of just calling the LLM directly?
# Because a graph lets us define a LOOP: brain thinks -> maybe uses a tool -> comes back to brain
# -> forms a final answer. This is what makes Leo "agentic" instead of just a chatbot.

import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, MessagesState, END, START
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage

from core.tools import ALL_TOOLS

load_dotenv()

# This system prompt is critical — small/fast models like llama-3.1-8b-instant
# sometimes "forget" to use tools and just guess instead. Explicitly telling it
# to prefer tools fixes this in most cases.
SYSTEM_PROMPT = (
    "You are Leo, a voice assistant. Always use tools for weather, search, news, "
    "calendar, email, or apps — never guess real data. After a tool runs, state the "
    "actual result naturally (e.g. 'It's 27°C in Indore'), never mention tool names."
)


def build_leo():
    """Builds and compiles Leo's LangGraph brain. Returns a runnable graph."""

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in .env")

    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0, max_retries=0)
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    def brain_node(state: MessagesState):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    graph = StateGraph(MessagesState)
    graph.add_node("brain", brain_node)
    graph.add_node("tools", ToolNode(ALL_TOOLS))

    graph.add_edge(START, "brain")
    graph.add_conditional_edges("brain", tools_condition)
    graph.add_edge("tools", "brain")

    return graph.compile()


if __name__ == "__main__":
    leo = build_leo()

    print("Leo is online. Type 'quit' to exit.\n")
    conversation = []

    while True:
        user_input = input("You: ")
        if user_input.lower() == "quit":
            break

        conversation.append({"role": "user", "content": user_input})
        result = leo.invoke({"messages": conversation})
        conversation = result["messages"]

        ai_reply = conversation[-1].content
        print(f"Leo: {ai_reply}\n")