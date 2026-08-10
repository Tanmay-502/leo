# core/voice_loop.py
# Leo's full voice experience: listen -> think -> speak -> repeat.
# Includes the greeting shortcut (same as text mode) and a safety net that
# catches broken/empty/raw-JSON responses so Leo never speaks garbage.

from core.agent import build_leo
from core.voice import listen, speak

SIMPLE_GREETINGS = ("hello", "hi", "hey", "how are you", "good morning", "good evening")


def run_voice_loop():
    leo = build_leo()
    conversation = []

    speak("Leo is online. How can I help you?")
    print("Leo is listening. Say 'quit' or 'stop' to exit.\n")

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

        conversation.append({"role": "user", "content": user_input})

        try:
            result = leo.invoke({"messages": conversation})
            conversation = result["messages"]
            ai_reply = conversation[-1].content

            # Safety net: catch empty replies AND raw tool-call JSON leaking
            # through instead of a real sentence — never speak either of those.
            if not ai_reply or not ai_reply.strip() or ai_reply.strip().startswith("{"):
                ai_reply = "Sorry, I didn't catch that clearly. Could you repeat it?"

        except Exception as e:
            ai_reply = "Sorry, I'm having trouble thinking right now."
            print(f"[Error]: {e}")

        print(f"Leo: {ai_reply}\n")
        speak(ai_reply)


if __name__ == "__main__":
    run_voice_loop()