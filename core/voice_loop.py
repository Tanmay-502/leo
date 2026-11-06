# core/voice_loop.py
# Leo's full voice experience: listen -> think -> speak -> repeat.
# Includes a floating popup UI (listening/thinking/speaking states), a quick
# spoken acknowledgment before the LLM responds (hides CPU inference delay),
# greeting shortcut, remember-fact shortcut, and persistent memory.

from core.agent import build_leo, clean_response, try_handle_remember, is_greeting
from core.voice import listen, speak
from core.memory import init_db, save_message, load_recent_history
from core.config import settings
from core.ui import start_ui, set_state


def run_voice_loop():
    init_db()
    start_ui()
    leo = build_leo()
    conversation = load_recent_history(limit=10)

    set_state("idle", "Leo is online")
    try:
        speak("Leo is online. How can I help you?")
    except RuntimeError as exc:
        print(f"[voice] {exc}")
    print("Leo is listening. Say 'quit' or 'stop' to exit.\n")
    if conversation:
        print(f"[Loaded {len(conversation)} previous messages from memory]\n")

    while True:
        set_state("listening", "")
        try:
            user_input = listen(
                duration=4,
                on_transcribing=lambda: set_state("transcribing", ""),
            )
        except RuntimeError as exc:
            set_state("error", str(exc))
            print(f"[voice] {exc}")
            break

        if not user_input:
            set_state("idle", "")
            continue

        cleaned = user_input.lower().strip().rstrip(".!?")

        if cleaned in ("quit", "stop", "exit"):
            set_state("speaking", "Goodbye!")
            try:
                speak("Goodbye!")
            except RuntimeError as exc:
                print(f"[voice] {exc}")
            break

        if is_greeting(user_input):
            reply = "Hey! How can I help you today?"
            set_state("speaking", reply)
            print(f"Leo: {reply}\n")
            try:
                speak(reply)
            except RuntimeError as exc:
                print(f"[voice] {exc}")
            continue

        remember_reply = try_handle_remember(user_input)
        if remember_reply:
            set_state("speaking", remember_reply)
            print(f"Leo: {remember_reply}\n")
            try:
                speak(remember_reply)
            except RuntimeError as exc:
                print(f"[voice] {exc}")
            save_message("user", user_input)
            save_message("assistant", remember_reply)
            continue

        set_state("thinking", user_input)
        conversation.append({"role": "user", "content": user_input})
        save_message("user", user_input)

        try:
            result = leo.invoke({"messages": conversation})
            conversation = result["messages"]
            ai_reply = clean_response(conversation[-1].content)

        except Exception as e:
            ai_reply = "Sorry, I'm having trouble thinking right now."
            print(f"[Error]: {e}")

        save_message("assistant", ai_reply)

        set_state("speaking", ai_reply)
        print(f"Leo: {ai_reply}\n")
        try:
            speak(ai_reply)
        except RuntimeError as exc:
            print(f"[voice] {exc}")

    set_state("idle", "")


if __name__ == "__main__":
    run_voice_loop()