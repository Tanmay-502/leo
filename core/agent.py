# core/agent.py
# This is Leo's BRAIN — built as a LangGraph "state graph" instead of a simple function call.
# Why a graph instead of just calling the LLM directly?
# Because a graph lets us define a LOOP: brain thinks -> maybe uses a tool -> comes back to brain
# -> forms a final answer. This is what makes Leo "agentic" instead of just a chatbot.

import os
import time                                   # needed for retry delays on rate limits
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
    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

    # This "attaches" our tools to the LLM so it knows what functions exist and their signatures
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    def brain_node(state: MessagesState):
        # Retry up to 3 times if we hit a rate limit (429), waiting a bit longer each time.
        # This prevents Leo from crashing every time Groq's free tier gets briefly overloaded.
        for attempt in range(3):
            try:
                response = llm_with_tools.invoke(state["messages"])
                return {"messages": [response]}
            except Exception as e:
                if "429" in str(e) and attempt < 2:
                    wait = 5 * (attempt + 1)  # waits 5s, then 10s
                    print(f"[Rate limited — retrying in {wait}s...]")
                    time.sleep(wait)
                else:
                    raise  # if it's a different error, or we're out of retries, show it for real

    # ---- Building the graph ----
    graph = StateGraph(MessagesState)

    graph.add_node("brain", brain_node)          # the LLM thinking step
    graph.add_node("tools", ToolNode(ALL_TOOLS))  # the step that actually RUNS a tool if called

    graph.add_edge(START, "brain")
    # tools_condition automatically checks: did the LLM just ask to use a tool?
    # If YES -> go to "tools" node. If NO -> end the turn (just reply normally).
    graph.add_conditional_edges("brain", tools_condition)
    graph.add_edge("tools", "brain")
    # after a tool runs, we go BACK to the brain so it can turn the raw tool result
    # into a natural, human-sounding reply

    return graph.compile()  # compiles the graph into something we can .invoke()


# This block ONLY runs if you execute this file directly (python -m core.agent)
# It won't run if agent.py is just imported elsewhere later (e.g. by FastAPI)
if __name__ == "__main__":
    leo = build_leo()

    print("Leo is online. Type 'quit' to exit.\n")
    conversation = []  # this list holds the whole chat history for this session

    while True:
        user_input = input("You: ")
        if user_input.lower() == "quit":
            break

        conversation.append({"role": "user", "content": user_input})
        result = leo.invoke({"messages": conversation})
        conversation = result["messages"]  # update history with Leo's new reply included

        ai_reply = conversation[-1].content
        print(f"Leo: {ai_reply}\n")