# core/agent.py
# Leo's BRAIN — LangGraph state graph, running on Ollama (local, offline, free).
# No internet needed to think, no API key, no rate limits — runs on this machine.
# Persistent memory via SQLite — Leo remembers past conversations and saved
# facts even after you close and reopen the program.

from langgraph.graph import StateGraph, MessagesState, END, START
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage

from core.tools import ALL_TOOLS
from core.memory import init_db, save_message, load_recent_history, save_fact, get_all_facts

SYSTEM_PROMPT = (
    "You are Leo, a voice assistant. Always use tools for weather, search, news, "
    "calendar, email, or apps — never guess real data. After a tool runs, state the "
    "actual result naturally (e.g. 'It's 27°C in Indore'), never mention tool names. "
    "Keep replies short and conversational — 1 to 3 sentences unless more detail is asked for."
)

SIMPLE_GREETINGS = ("hello", "hi", "hey", "how are you", "good morning", "good evening")

# Phrases that mean "remember this for later" — handled directly in code,
# not left to the small model's judgment, since it kept confusing this with
# sending an email. Same trick that fixed the greeting misfires earlier.
REMEMBER_TRIGGERS = ("remember that ", "remember ", "please remember that ", "please remember ")


def build_leo():
    """Builds and compiles Leo's LangGraph brain. Returns a runnable graph."""

    # num_predict caps how many tokens the model generates per reply — keeps
    # answers short and responses faster, especially useful on CPU-only machines.
    llm = ChatOllama(model="llama3.2", temperature=0, num_predict=150)
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    def brain_node(state: MessagesState):
        facts = get_all_facts()
        facts_text = ""
        if facts:
            facts_text = " Known facts about the user: " + "; ".join(facts[:10])

        messages = [SystemMessage(content=SYSTEM_PROMPT + facts_text)] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    graph = StateGraph(MessagesState)
    graph.add_node("brain", brain_node)
    graph.add_node("tools", ToolNode(ALL_TOOLS))

    graph.add_edge(START, "brain")
    graph.add_conditional_edges("brain", tools_condition)
    graph.add_edge("tools", "brain")

    return graph.compile()


def is_greeting(text: str) -> bool:
    """Matches greetings even with extra words, e.g. 'Hello, Leo' or 'Hey there'."""
    cleaned = text.lower().strip().rstrip(".!?,")
    return any(cleaned.startswith(g) for g in SIMPLE_GREETINGS)


def try_handle_remember(user_input: str):
    """Checks if the message is a 'remember X' request and handles it directly,
    bypassing the LLM entirely. Returns a reply string if handled, else None."""
    lowered = user_input.lower().strip()
    for trigger in REMEMBER_TRIGGERS:
        if lowered.startswith(trigger):
            fact = user_input[len(trigger):].strip()
            if fact:
                save_fact(fact)
                return f"Got it, I'll remember: {fact}"
    return None


if __name__ == "__main__":
    init_db()
    leo = build_leo()

    print("Leo is online (offline via Ollama, llama3.2). Type 'quit' to exit.\n")

    conversation = load_recent_history(limit=10)
    if conversation:
        print(f"[Loaded {len(conversation)} previous messages from memory]\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() == "quit":
            break

        if is_greeting(user_input):
            print("Leo: Hey! How can I help you today?\n")
            continue

        remember_reply = try_handle_remember(user_input)
        if remember_reply:
            print(f"Leo: {remember_reply}\n")
            save_message("user", user_input)
            save_message("assistant", remember_reply)
            continue

        conversation.append({"role": "user", "content": user_input})
        save_message("user", user_input)

        result = leo.invoke({"messages": conversation})
        conversation = result["messages"]

        ai_reply = conversation[-1].content
        if not ai_reply or not ai_reply.strip() or ai_reply.strip().startswith("{"):
            ai_reply = "Sorry, I didn't catch that clearly. Could you repeat it?"

        save_message("assistant", ai_reply)

        print(f"Leo: {ai_reply}\n")