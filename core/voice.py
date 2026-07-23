# core/voice.py
# This file gives Leo EARS (listen) and a MOUTH (speak).
# listen()  -> records your voice from the mic, converts it to text using faster-whisper
# speak()   -> takes Leo's text reply, converts it to natural speech using edge-tts, plays it aloud
#
# Both run 100% locally/free — faster-whisper needs no internet after its first model download,
# and edge-tts needs internet (it streams from Microsoft's free service) but no API key.

import asyncio
import tempfile
import os
import numpy as np
import sounddevice as sd
import soundfile as sf
from faster_whisper import WhisperModel
import edge_tts

# ---- Setup: load the Whisper model ONCE when this file is imported ----
# "base" is a good tradeoff: fast enough for real-time use, accurate enough for commands.
# compute_type="int8" makes it run fast even on a CPU (no GPU needed).
print("[voice] Loading speech recognition model (first run may take a moment)...")
_stt_model = WhisperModel("base", compute_type="int8")
print("[voice] Speech recognition ready.")

# Voice to use for Leo's replies. "en-US-GuyNeural" is a natural-sounding free voice.
# Full list: run `edge-tts --list-voices` in your terminal if you want to browse options.
LEO_VOICE = "en-US-GuyNeural"

SAMPLE_RATE = 16000  # 16kHz is what Whisper expects


def listen(duration=6):
    """
    Records audio from the microphone for `duration` seconds,
    then converts it to text using faster-whisper.
    Returns the transcribed text as a string, or "" if silence was detected.
    """
    import time
    print(f"\n[Get ready...]")
    time.sleep(0.5)
    print(f"[Listening for {duration} seconds — speak now]")

    audio = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
    sd.wait()

    audio = audio.flatten()

    # SILENCE CHECK: Whisper often hallucinates words like "You" or "Thank you"
    # when given near-silent audio. We measure the audio's volume (RMS) and
    # skip transcription entirely if it's too quiet to be real speech.
    volume = np.sqrt(np.mean(audio**2))
    SILENCE_THRESHOLD = 0.01  # tune this if it's too sensitive or not sensitive enough

    if volume < SILENCE_THRESHOLD:
        print("[Silence detected — skipping]")
        return ""

    segments, _ = _stt_model.transcribe(audio, language="en")
    text = " ".join(segment.text for segment in segments).strip()

    print(f"[You said]: {text}")
    return text

def speak(text: str):
    """
    Converts `text` to speech using edge-tts and plays it through the speakers.
    """
    if not text:
        return

    async def _generate_and_play():
        # edge-tts saves audio to a temp file, then we play that file back
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            tmp_path = tmp_file.name

        communicate = edge_tts.Communicate(text, LEO_VOICE)
        await communicate.save(tmp_path)

        # Play the generated mp3 file
        data, samplerate = sf.read(tmp_path)
        sd.play(data, samplerate)
        sd.wait()  # blocks until playback finishes

        os.remove(tmp_path)  # clean up the temp file

    asyncio.run(_generate_and_play())


# ---- Quick standalone test ----
# Run this file directly (python -m core.voice) to test mic + speaker
# WITHOUT touching the LLM brain at all — isolates voice issues from agent issues.
if __name__ == "__main__":
    print("Testing Leo's voice system.\n")

    text = listen(duration=5)
    if text:
        speak(f"You said: {text}")
    else:
        print("[No speech detected]")

