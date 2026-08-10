# core/agent.py
# Leo's BRAIN — LangGraph state graph, running on Ollama (local, offline, free).
# No internet needed to think, no API key, no rate limits — runs on this machine.

from langgraph.graph import StateGraph, MessagesState, END, START
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage

from core.tools import ALL_TOOLS

SYSTEM_PROMPT = (
    "You are Leo, a voice assistant. Always use tools for weather, search, news, "
    "calendar, email, or apps — never guess real data. After a tool runs, state the "
    "actual result naturally (e.g. 'It's 27°C in Indore'), never mention tool names."
)

SIMPLE_GREETINGS = ("hello", "hi", "hey", "how are you", "good morning", "good evening")


def build_leo():
    """Builds and compiles Leo's LangGraph brain. Returns a runnable graph."""

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

        cleaned = user_input.lower().strip()
        if cleaned in SIMPLE_GREETINGS:
            print("Leo: Hey! How can I help you today?\n")
            continue

        conversation.append({"role": "user", "content": user_input})
        result = leo.invoke({"messages": conversation})
        conversation = result["messages"]

        ai_reply = conversation[-1].content
        if not ai_reply or not ai_reply.strip() or ai_reply.strip().startswith("{"):
            ai_reply = "Sorry, I didn't catch that clearly. Could you repeat it?"

        print(f"Leo: {ai_reply}\n")