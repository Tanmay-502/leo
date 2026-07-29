# core/voice_loop.py
# Leo's full voice experience: listen -> think -> speak -> repeat.
# New in this version: Leo gives a quick spoken acknowledgment BEFORE
# the tool finishes running, so it doesn't feel like dead silence while
# it's fetching weather/searching/etc — same trick Siri/Alexa use.

from core.agent import build_leo
from core.voice import listen, speak

# Quick, natural filler lines Leo can say WHILE it's about to do something.
# Doesn't need to be tool-specific — a generic "on it" beats silence.
THINKING_PHRASES = [
    "Sure, one moment.",
    "Got it, checking now.",
    "Okay, let me check.",
    "On it.",
]

import random

def run_voice_loop():
    leo = build_leo()
    conversation = []

    speak("Leo is online. How can I help you?")
    print("Leo is listening. Say 'quit' or 'stop' to exit.\n")

    while True:
        user_input = listen(duration=6)

        if not user_input:
            continue

        if user_input.lower().strip() in ("quit", "stop", "exit"):
            speak("Goodbye!")
            break

        conversation.append({"role": "user", "content": user_input})

        # Speak a quick filler BEFORE the LLM call — makes the pause feel natural
        # instead of dead silence while a tool (weather/search/etc) is running.
        speak(random.choice(THINKING_PHRASES))

        try:
            result = leo.invoke({"messages": conversation})
            conversation = result["messages"]
            ai_reply = conversation[-1].content
        except Exception as e:
            ai_reply = "Sorry, I'm having trouble thinking right now. Please try again in a moment."
            print(f"[Error]: {e}")

        print(f"Leo: {ai_reply}\n")
        speak(ai_reply)


if __name__ == "__main__":
    run_voice_loop()