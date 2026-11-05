# Project audit

## Baseline

Leo was a small Python voice assistant using LangGraph, Ollama, SQLite, faster-whisper, Edge TTS, Tkinter, Google APIs, Open-Meteo, DuckDuckGo, and BBC RSS. The code compiled, but the only existing “tests” performed live Google OAuth and a live Groq request during pytest collection.

## Findings

- `core/agent.py` hardcoded `llama3.2`, injected facts into an unbounded graph history, and had no Ollama availability or tool-loop error handling.
- `core/memory.py` opened independent connections for every operation, stored duplicate facts, had no deletion/clear operations, and used a working-directory-relative database without configuration.
- `core/voice.py` loaded a large Whisper model and audio dependencies at import time, blocked the caller, used only online Edge TTS, leaked temporary files on failures, and had no configurable TTS abstraction.
- `core/tools.py` used `os.system("start ...")`, broad exception messages, naive timezone handling, weak email validation, and no response status checks.
- `core/google_auth.py` used fixed paths, requested Gmail send permission without a clear setup error, and could expose provider errors directly to users.
- `core/voice_loop.py` blocked on startup and speech, spoke acknowledgments unnecessarily, and had no reliable shutdown/cancellation boundary.
- `core/ui.py` was functional but had no stop event or explicit lifecycle handle.
- `README.md` overstated offline support because TTS was online-only and omitted configuration, testing, and troubleshooting.

## Environment limitations

The current environment does not have the repository's optional Google and Groq packages installed. Hardware audio, Ollama, Google credentials, and internet services are intentionally not required for the deterministic test suite.
