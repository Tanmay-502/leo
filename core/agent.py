"""Leo's bounded LangGraph/Ollama conversation engine."""

from __future__ import annotations

from typing import Any

from core.config import settings
from core.memory import get_all_facts, init_db, save_fact, save_message, load_recent_history

SYSTEM_PROMPT = (
    "You are Leo, a concise personal voice assistant. Use tools for live weather, "
    "search, news, calendar, email, and apps. Never invent live data or claim a "
    "failed action succeeded. Keep replies to 1-3 sentences unless asked for detail."
)
SIMPLE_GREETINGS = ("hello", "hi", "hey", "how are you", "good morning", "good evening")
REMEMBER_TRIGGERS = ("remember that ", "remember ", "please remember that ", "please remember ")


def build_leo():
    """Build and compile the LangGraph brain, or raise an actionable setup error."""
    try:
        from langchain_core.messages import SystemMessage
        from langchain_ollama import ChatOllama
        from langgraph.graph import END, START, MessagesState, StateGraph
        from langgraph.prebuilt import ToolNode, tools_condition
        from core.tools import ALL_TOOLS
    except ImportError as exc:
        raise RuntimeError(
            "Leo's AI dependencies are missing. Run pip install -r requirements.txt."
        ) from exc

    try:
        llm = ChatOllama(
            model=settings.model, base_url=settings.ollama_url,
            temperature=0, num_predict=150,
        )
        llm_with_tools = llm.bind_tools(ALL_TOOLS)
    except Exception as exc:
        raise RuntimeError(
            f"Unable to initialize Ollama model '{settings.model}'. "
            "Install Ollama, start it, and run `ollama pull "
            f"{settings.model}`."
        ) from exc

    def brain_node(state: MessagesState) -> dict[str, list[Any]]:
        facts = get_all_facts()
        fact_text = f" Known facts: {'; '.join(facts[:10])}" if facts else ""
        messages = [SystemMessage(content=SYSTEM_PROMPT + fact_text)] + state["messages"][-settings.history_limit:]
        try:
            response = llm_with_tools.invoke(messages)
        except Exception as exc:
            raise RuntimeError(
                f"Ollama could not generate a response. Is '{settings.model}' available?"
            ) from exc
        return {"messages": [response]}

    graph = StateGraph(MessagesState)
    graph.add_node("brain", brain_node)
    graph.add_node("tools", ToolNode(ALL_TOOLS))
    graph.add_edge(START, "brain")
    graph.add_conditional_edges("brain", tools_condition)
    graph.add_edge("tools", "brain")
    return graph.compile()


def is_greeting(text: str) -> bool:
    cleaned = text.lower().strip().rstrip(".!?,")
    return any(cleaned.startswith(greeting) for greeting in SIMPLE_GREETINGS)


def try_handle_remember(user_input: str) -> str | None:
    lowered = user_input.lower().strip()
    for trigger in REMEMBER_TRIGGERS:
        if lowered.startswith(trigger):
            fact = user_input[len(trigger):].strip()
            if fact:
                save_fact(fact)
                return f"Got it, I'll remember: {fact}"
    return None


def clean_response(content: Any) -> str:
    text = content if isinstance(content, str) else str(content or "")
    if not text.strip() or text.strip().startswith("{"):
        return "Sorry, I didn't catch that clearly. Could you repeat it?"
    return text.strip()


def run_text_mode() -> None:
    init_db()
    leo = build_leo()
    conversation = load_recent_history()
    print(f"Leo is online using Ollama model {settings.model}. Type 'quit' to exit.\n")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"quit", "exit"}:
            break
        if is_greeting(user_input):
            reply = "Hey! How can I help you today?"
        else:
            reply = try_handle_remember(user_input)
            if not reply:
                save_message("user", user_input)
                conversation.append({"role": "user", "content": user_input})
                result = leo.invoke({"messages": conversation[-settings.history_limit:]})
                conversation = result["messages"][-settings.history_limit:]
                reply = clean_response(conversation[-1].content)
        save_message("assistant", reply)
        print(f"Leo: {reply}\n")


if __name__ == "__main__":
    run_text_mode()
