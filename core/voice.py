# core/voice.py
# Leo's ears (listen) and mouth (speak).
# STT (listen) is 100% offline — faster-whisper runs locally.
# TTS (speak) needs internet — edge-tts streams from Microsoft's free service.
# That's the one piece of Leo that can't be fully offline; if you're on a bad
# connection, speak() fails gracefully and Leo keeps working in text.

import asyncio
import tempfile
import os
import time
import numpy as np
import sounddevice as sd
import soundfile as sf
from faster_whisper import WhisperModel
import edge_tts

print("[voice] Loading speech recognition model (first run may take a moment)...")
_stt_model = WhisperModel("small", compute_type="int8")
print("[voice] Speech recognition ready.")

LEO_VOICE = "en-US-AndrewNeural"
SAMPLE_RATE = 16000

# We DON'T hardcode a mic device index here — every laptop has different
# device numbers, and hardcoding one (like we did before) breaks Leo on any
# machine other than the one it was hardcoded for. Instead, we let
# sounddevice use whatever the OS has set as the default input device.
# If you personally want to force a specific mic, set the LEO_MIC_INDEX
# environment variable to that device's index (check with:
# python -c "import sounddevice as sd; print(sd.query_devices())")
_mic_override = os.getenv("LEO_MIC_INDEX")
if _mic_override is not None:
    sd.default.device = (int(_mic_override), None)
    print(f"[voice] Using manually configured mic device index {_mic_override}")

# Whisper sometimes mishears less-common words (like Indian city names) or
# short activation phrases. This prompt "hints" Whisper toward expected
# vocabulary, which measurably improves accuracy.
WHISPER_HINT = (
    "The user may say 'Hey Leo' to activate the assistant, or mention Indian "
    "cities like Indore, Mumbai, Delhi, Bangalore, Pune, Bhopal, Jaipur, and "
    "ask about weather, calendar, email, or news."
)

# Backup safety net: common mishearings we've seen in testing, corrected directly.
# Add more pairs here as you notice new mistakes during use.
CORRECTIONS = {
    "the north": "Indore",
    "indoor": "Indore",
    "in door": "Indore",
    "alligate": "Hey Leo",
    "elegate": "Hey Leo",
}


def _apply_corrections(text: str) -> str:
    """Fixes known common mishearings before Leo's brain ever sees the text."""
    fixed = text
    for wrong, right in CORRECTIONS.items():
        if wrong in fixed.lower():
            fixed = fixed.lower().replace(wrong, right)
    return fixed


def listen(duration=4):
    """Records mic audio, returns transcribed (and corrected) text, or "" if silence."""
    print(f"\n[Get ready...]")
    time.sleep(0.5)
    print(f"[Listening for {duration} seconds — speak now]")

    audio = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
    sd.wait()
    audio = audio.flatten()

    volume = np.sqrt(np.mean(audio**2))
    SILENCE_THRESHOLD = 0.01

    if volume < SILENCE_THRESHOLD:
        print("[Silence detected — skipping]")
        return ""

    segments, _ = _stt_model.transcribe(audio, language="en", initial_prompt=WHISPER_HINT)
    text = " ".join(segment.text for segment in segments).strip()
    text = _apply_corrections(text)

    print(f"[You said]: {text}")
    return text


def speak(text: str):
    """Speaks `text` aloud via edge-tts. Fails silently (prints a warning)
    if there's no internet, instead of crashing the whole program."""
    if not text:
        return

    async def _generate_and_play():
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            tmp_path = tmp_file.name

        communicate = edge_tts.Communicate(text, LEO_VOICE)
        await communicate.save(tmp_path)

        data, samplerate = sf.read(tmp_path)
        sd.play(data, samplerate)
        sd.wait()

        os.remove(tmp_path)

    try:
        asyncio.run(_generate_and_play())
    except Exception as e:
        print(f"[voice] Couldn't speak aloud (likely no internet): {e}")


if __name__ == "__main__":
    print("Testing Leo's voice system.\n")
    text = listen(duration=5)
    if text:
        speak(f"You said: {text}")
    else:
        print("[No speech detected]")