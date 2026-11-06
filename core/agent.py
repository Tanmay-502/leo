"""Leo's bounded LangGraph/Ollama conversation engine."""

from __future__ import annotations

import os
import traceback
from pathlib import Path
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


def record_diagnostic(context: str, exc: BaseException) -> None:
    """Write local diagnostics without exposing credentials or environment values."""
    path = Path(os.getenv("LEO_LOG_PATH", "leo.log")).expanduser()
    try:
        with path.open("a", encoding="utf-8") as log:
            log.write(f"\n[{context}]\n")
            traceback.print_exception(type(exc), exc, exc.__traceback__, file=log)
    except OSError:
        pass


def build_leo():
    """Build and compile the LangGraph brain, or raise an actionable setup error."""
    required_packages = (
        ("langchain_core", "langchain-core"),
        ("langchain_ollama", "langchain-ollama"),
        ("langgraph", "langgraph"),
    )
    try:
        import importlib
        from langchain_core.messages import SystemMessage
        from langchain_ollama import ChatOllama
        from langgraph.graph import END, START, MessagesState, StateGraph
        from langgraph.prebuilt import ToolNode, tools_condition
        from core.tools import ALL_TOOLS
    except ImportError as exc:
        record_diagnostic("dependency import", exc)
        missing = next(
            (package for module, package in required_packages
             if not _module_available(importlib, module)),
            None,
        )
        if missing:
            raise RuntimeError(
                f"Missing Python package '{missing}'. Run "
                f"'.\\venv\\Scripts\\python.exe -m pip install -r requirements.txt'."
            ) from exc
        raise RuntimeError(
            "Leo's LangGraph/Ollama integration could not be imported. "
            "See leo.log for the local traceback."
        ) from exc

    try:
        llm = ChatOllama(
            model=settings.model, base_url=settings.ollama_url,
            temperature=0, num_predict=150,
        )
        llm_with_tools = llm.bind_tools(ALL_TOOLS)
    except Exception as exc:
        record_diagnostic("Ollama initialization", exc)
        raise RuntimeError(
            f"LangGraph/Ollama initialization failed for model '{settings.model}': "
            f"{exc}. Verify Ollama is running at {settings.ollama_url} and that "
            f"'{settings.model}' is installed."
        ) from exc

    def brain_node(state: MessagesState) -> dict[str, list[Any]]:
        facts = get_all_facts()
        fact_text = f" Known facts: {'; '.join(facts[:10])}" if facts else ""
        messages = [SystemMessage(content=SYSTEM_PROMPT + fact_text)] + state["messages"][-settings.history_limit:]
        try:
            response = llm_with_tools.invoke(messages)
        except Exception as exc:
            record_diagnostic("Ollama request", exc)
            detail = str(exc)
            if "connection" in detail.lower() or "connect" in detail.lower():
                message = (
                    f"Cannot connect to Ollama at {settings.ollama_url}. "
                    "Start the Ollama service and try again."
                )
            elif "not found" in detail.lower() or "pull" in detail.lower():
                message = (
                    f"Ollama model '{settings.model}' is unavailable. "
                    f"Run `ollama pull {settings.model}` and try again."
                )
            else:
                message = f"Ollama request failed: {detail}"
            raise RuntimeError(
                f"{message} See leo.log for the local traceback."
            ) from exc
        return {"messages": [response]}

    try:
        graph = StateGraph(MessagesState)
        graph.add_node("brain", brain_node)
        graph.add_node("tools", ToolNode(ALL_TOOLS))
        graph.add_edge(START, "brain")
        graph.add_conditional_edges("brain", tools_condition)
        graph.add_edge("tools", "brain")
        return graph.compile()
    except Exception as exc:
        record_diagnostic("LangGraph initialization", exc)
        raise RuntimeError(
            f"LangGraph initialization failed: {exc}. See leo.log for the "
            "local traceback."
        ) from exc


def _module_available(importlib: Any, module: str) -> bool:
    try:
        importlib.import_module(module)
    except ImportError:
        return False
    return True


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
