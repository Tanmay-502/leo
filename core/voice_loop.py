# core/voice_loop.py
# Leo's full voice experience: listen -> think -> speak -> repeat.
# Includes greeting shortcut, remember-fact shortcut, a safety net for
# broken responses, and persistent memory via SQLite.

from core.agent import build_leo, try_handle_remember
from core.voice import listen, speak
from core.memory import init_db, save_message, load_recent_history

SIMPLE_GREETINGS = ("hello", "hi", "hey", "how are you", "good morning", "good evening")


def run_voice_loop():
    init_db()
    leo = build_leo()
    conversation = load_recent_history(limit=10)

    speak("Leo is online. How can I help you?")
    print("Leo is listening. Say 'quit' or 'stop' to exit.\n")
    if conversation:
        print(f"[Loaded {len(conversation)} previous messages from memory]\n")

    while True:
        user_input = listen(duration=6)

        if not user_input:
            continue

        cleaned = user_input.lower().strip().rstrip(".!?")

        if cleaned in ("quit", "stop", "exit"):
            speak("Goodbye!")
            break

        if cleaned in SIMPLE_GREETINGS:
            reply = "Hey! How can I help you today?"
            print(f"Leo: {reply}\n")
            speak(reply)
            continue

        remember_reply = try_handle_remember(user_input)
        if remember_reply:
            print(f"Leo: {remember_reply}\n")
            speak(remember_reply)
            save_message("user", user_input)
            save_message("assistant", remember_reply)
            continue

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

        print(f"Leo: {ai_reply}\n")
        speak(ai_reply)


if __name__ == "__main__":
    run_voice_loop()