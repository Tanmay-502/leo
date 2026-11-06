"""Optional speech recognition and pluggable text-to-speech providers."""

from __future__ import annotations

import asyncio
import os
import tempfile
from abc import ABC, abstractmethod
from collections.abc import Callable

from core.config import settings

SAMPLE_RATE = 16000
WHISPER_HINT = "The user may say Hey Leo, mention Indian cities, weather, calendar, email, or news."
CORRECTIONS = {"the north": "Indore", "indoor": "Indore", "in door": "Indore"}


def _apply_corrections(text: str) -> str:
    fixed = text
    for wrong, right in CORRECTIONS.items():
        fixed = fixed.lower().replace(wrong, right)
    return fixed


def listen(duration: float = 4, on_transcribing: Callable[[], None] | None = None) -> str:
    """Record and transcribe audio, with silence and device errors surfaced."""
    try:
        import numpy as np
        import sounddevice as sd
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("Voice input dependencies are missing. Install requirements.txt.") from exc
    if duration <= 0:
        raise ValueError("duration must be positive")
    if settings.mic_index is not None:
        sd.default.device = (settings.mic_index, None)
    try:
        audio = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
        sd.wait()
    except Exception as exc:
        raise RuntimeError("Microphone recording failed; check the selected input device.") from exc
    samples = audio.flatten()
    if float(np.sqrt(np.mean(samples ** 2))) < 0.01:
        return ""
    if on_transcribing is not None:
        on_transcribing()
    model = WhisperModel(settings.whisper_model, compute_type="int8")
    segments, _ = model.transcribe(samples, language="en", initial_prompt=WHISPER_HINT)
    return _apply_corrections(" ".join(segment.text for segment in segments).strip())


class TTSProvider(ABC):
    @abstractmethod
    def speak(self, text: str) -> None:
        """Speak text or raise a clear provider error."""


class OfflineTTS(TTSProvider):
    def speak(self, text: str) -> None:
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", 175)
            engine.say(text)
            engine.runAndWait()
        except ImportError as exc:
            raise RuntimeError("Offline TTS requires pyttsx3; install requirements.txt.") from exc


class EdgeTTS(TTSProvider):
    def speak(self, text: str) -> None:
        try:
            import edge_tts
            import sounddevice as sd
            import soundfile as sf
        except ImportError as exc:
            raise RuntimeError("Edge TTS dependencies are missing.") from exc

        async def generate(path: str) -> None:
            await edge_tts.Communicate(text, settings.tts_voice, rate=settings.tts_rate).save(path)

        fd, path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        try:
            asyncio.run(generate(path))
            data, samplerate = sf.read(path)
            sd.play(data, samplerate)
            sd.wait()
        finally:
            if os.path.exists(path):
                os.remove(path)


def get_tts_provider() -> TTSProvider:
    return EdgeTTS() if settings.tts_provider.lower() == "edge" else OfflineTTS()


def speak(text: str, provider: TTSProvider | None = None) -> None:
    if text.strip():
        (provider or get_tts_provider()).speak(text)
