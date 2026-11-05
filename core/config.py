"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


@dataclass(frozen=True)
class Settings:
    model: str
    ollama_url: str
    db_path: Path
    mic_index: int | None
    whisper_model: str
    tts_provider: str
    tts_voice: str
    tts_rate: str
    history_limit: int
    tool_loop_limit: int
    google_credentials_path: Path
    google_token_path: Path

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "Settings":
        values = os.environ if env is None else env
        if env is None:
            load_dotenv()
        db_path = Path(values.get("LEO_DB_PATH", "leo.db")).expanduser()
        mic_value = values.get("LEO_MIC_INDEX")
        mic_index = int(mic_value) if mic_value else None
        history_limit = int(values.get("LEO_HISTORY_LIMIT", "12"))
        if history_limit < 1:
            raise ValueError("LEO_HISTORY_LIMIT must be positive")
        tool_loop_limit = int(values.get("LEO_TOOL_LOOP_LIMIT", "4"))
        if tool_loop_limit < 1:
            raise ValueError("LEO_TOOL_LOOP_LIMIT must be positive")
        return cls(
            model=values.get("LEO_OLLAMA_MODEL", "llama3.2"),
            ollama_url=values.get("LEO_OLLAMA_URL", "http://127.0.0.1:11434"),
            db_path=db_path,
            mic_index=mic_index,
            whisper_model=values.get("LEO_WHISPER_MODEL", "small"),
            tts_provider=values.get("LEO_TTS_PROVIDER", "offline"),
            tts_voice=values.get("LEO_TTS_VOICE", "en-US-AndrewNeural"),
            tts_rate=values.get("LEO_TTS_RATE", "+0%"),
            history_limit=history_limit,
            tool_loop_limit=tool_loop_limit,
            google_credentials_path=Path(
                values.get("LEO_GOOGLE_CREDENTIALS", "credentials.json")
            ).expanduser(),
            google_token_path=Path(
                values.get("LEO_GOOGLE_TOKEN", "token.json")
            ).expanduser(),
        )


settings = Settings.from_env()
