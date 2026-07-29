# core/agent.py
# Leo's BRAIN — LangGraph state graph, running on Ollama (local, offline, free).
#
# TEMPORARY TEST: using only 4 tools (TEST_TOOLS) instead of all 9, testing
# phi3:mini as it's known for better instruction-following at small size.
# Also added a hardcoded greeting shortcut — no reason to risk the LLM
# misfiring a tool on something as simple as "Hello".

from langgraph.graph import StateGraph, MessagesState, END, START
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage

from core.tools import ALL_TOOLS

SYSTEM_PROMPT = (
    "You are Leo, a voice assistant. For greetings or general chat, just reply normally — "
    "do NOT use any tool. Only use a tool when the user explicitly asks for weather, "
    "search, calendar, or to open an app. Never bring up unrelated topics."
)

# Greetings get answered directly in Python — zero chance of the model
# misfiring a tool call on something this simple.
SIMPLE_GREETINGS = ("hello", "hi", "hey", "how are you", "good morning", "good evening")


def build_leo():
    llm = ChatOllama(model="llama3.2", temperature=0)
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

    print("Leo is online (offline via Ollama, llama3.2). Type 'quit' to exit.\n")
    conversation = []

    while True:
        user_input = input("You: ")
        if user_input.lower() == "quit":
            break

        if user_input.lower().strip() in SIMPLE_GREETINGS:
            print("Leo: Hey! How can I help you today?\n")
            continue

        conversation.append({"role": "user", "content": user_input})
        result = leo.invoke({"messages": conversation})
        conversation = result["messages"]

        ai_reply = conversation[-1].content
        print(f"Leo: {ai_reply}\n")