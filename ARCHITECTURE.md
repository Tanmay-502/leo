# Architecture

`core.config` loads validated environment settings. `core.memory` owns SQLite persistence and keeps short-term conversation history separate from explicit facts. `core.agent` builds the LangGraph/Ollama engine and limits context and tool loops. `core.tools` contains validated integrations and safe desktop launching. `core.voice` provides optional STT and pluggable offline/online TTS. `core.voice_loop` coordinates the state machine, while `core.ui` remains a Tkinter presentation layer.

External services (Ollama, Google, Open-Meteo, DuckDuckGo, RSS, and Edge TTS) are injected or called behind small functions so tests can mock them. No natural-language path executes arbitrary shell commands.
