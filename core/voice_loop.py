# core/voice_loop.py
# This is Leo's full VOICE experience — it wires together:
#   core/voice.py  (ears + mouth)
#   core/agent.py  (brain)
# into one continuous loop: listen -> think -> speak -> repeat.
#
# We keep this separate from agent.py's text-mode __main__ block so you can
# still run `python -m core.agent` for fast text-only debugging without a mic.

from core.agent import build_leo
from core.voice import listen, speak

def run_voice_loop():
    leo = build_leo()
    conversation = []  # holds full chat history so Leo remembers context across turns

    speak("Leo is online. How can I help you?")
    print("Leo is listening. Say 'quit' or 'stop' to exit.\n")

    while True:
        user_input = listen(duration=6)

        if not user_input:
            # Nothing was heard (silence, background noise) — skip this turn, listen again
            continue

        if user_input.lower().strip() in ("quit", "stop", "exit"):
            speak("Goodbye!")
            break

        conversation.append({"role": "user", "content": user_input})

        try:
            result = leo.invoke({"messages": conversation})
            conversation = result["messages"]
            ai_reply = conversation[-1].content
        except Exception as e:
            # If Groq rate-limits or errors, tell the user out loud instead of crashing silently
            ai_reply = "Sorry, I'm having trouble thinking right now. Please try again in a moment."
            print(f"[Error]: {e}")

        print(f"Leo: {ai_reply}\n")
        speak(ai_reply)


if __name__ == "__main__":
    run_voice_loop()