# core/voice_loop.py
# Leo's full voice experience: listen -> think -> speak -> repeat.
# Includes a floating popup UI (listening/thinking/speaking states), a quick
# spoken acknowledgment before the LLM responds (hides CPU inference delay),
# greeting shortcut, remember-fact shortcut, and persistent memory.

import random
import time

from core.agent import build_leo, try_handle_remember, is_greeting
from core.voice import listen, speak
from core.memory import init_db, save_message, load_recent_history
from core.ui import start_ui, set_state

THINKING_PHRASES = ["Sure, one moment.", "Got it, checking now.", "Okay, let me check."]


def run_voice_loop():
    init_db()
    start_ui()
    time.sleep(0.5)  # give the popup window a moment to open

    leo = build_leo()
    conversation = load_recent_history(limit=10)

    set_state("idle", "Leo is online")
    speak("Leo is online. How can I help you?")
    print("Leo is listening. Say 'quit' or 'stop' to exit.\n")
    if conversation:
        print(f"[Loaded {len(conversation)} previous messages from memory]\n")

    while True:
        set_state("listening", "")
        user_input = listen(duration=4)

        if not user_input:
            set_state("idle", "")
            continue

        cleaned = user_input.lower().strip().rstrip(".!?")

        if cleaned in ("quit", "stop", "exit"):
            set_state("speaking", "Goodbye!")
            speak("Goodbye!")
            break

        if is_greeting(user_input):
            reply = "Hey! How can I help you today?"
            set_state("speaking", reply)
            print(f"Leo: {reply}\n")
            speak(reply)
            continue

        remember_reply = try_handle_remember(user_input)
        if remember_reply:
            set_state("speaking", remember_reply)
            print(f"Leo: {remember_reply}\n")
            speak(remember_reply)
            save_message("user", user_input)
            save_message("assistant", remember_reply)
            continue

        set_state("thinking", user_input)
        speak(random.choice(THINKING_PHRASES))  # fills the CPU-inference wait

        conversation.append({"role": "user", "content": user_input})
        save_message("user", user_input)

        try:
            result = leo.invoke({"messages": conversation})
            conversation = result["messages"]
            ai_reply = conversation[-1].content

            if not ai_reply or not ai_reply.strip() or ai_reply.strip().startswith("{"):
                ai_reply = "Sorry, I didn't catch that clearly. Could you repeat it?"

        except Exception as e:
            ai_reply = "Sorry, I'm having trouble thinking right now."
            print(f"[Error]: {e}")

        save_message("assistant", ai_reply)

        set_state("speaking", ai_reply)
        print(f"Leo: {ai_reply}\n")
        speak(ai_reply)

    set_state("idle", "")


if __name__ == "__main__":
    run_voice_loop()