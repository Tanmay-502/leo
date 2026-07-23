# core/agent.py
# This is Leo's BRAIN — built as a LangGraph "state graph" instead of a simple function call.
# Why a graph instead of just calling the LLM directly?
# Because a graph lets us define a LOOP: brain thinks -> maybe uses a tool -> comes back to brain
# -> forms a final answer. This is what makes Leo "agentic" instead of just a chatbot.

import os
from dotenv import load_dotenv                # reads our .env file so we don't hardcode secrets
from langgraph.graph import StateGraph, MessagesState, END, START
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_groq import ChatGroq

from core.tools import ALL_TOOLS               # import our list of tools from tools.py

load_dotenv()  # loads GROQ_API_KEY from .env into the environment


def build_leo():
    """Builds and compiles Leo's LangGraph brain. Returns a runnable graph."""

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in .env")

    # llama-3.1-8b-instant = fast + free on Groq, good enough for tool-calling/routing
    # max_retries=0 stops the SDK from silently retrying many times on its own on a 429
    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0, max_retries=0)

    # This "attaches" our tools to the LLM so it knows what functions exist and their signatures
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    def brain_node(state: MessagesState):
        # Single attempt only — no retry loop. If we hit a rate limit, it fails
        # clearly right away instead of hammering the API repeatedly.
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    # ---- Building the graph ----
    graph = StateGraph(MessagesState)

    graph.add_node("brain", brain_node)          # the LLM thinking step
    graph.add_node("tools", ToolNode(ALL_TOOLS))  # the step that actually RUNS a tool if called

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