# Phase 11 UI implementation report

## Technology decision

Tkinter was retained instead of migrating to CustomTkinter or PySide6. It is
already available on the supported Windows Python installation, adds no GUI
dependency, keeps PyInstaller packaging small, and can host the existing
backend safely when model, recording, and speech operations run on daemon
workers.

The boundary and event flow are documented in `UI_ARCHITECTURE.md`.

## Implemented

- Replaced the popup-only `core/ui.py` surface with a dark, resizable desktop
  application while preserving `start_ui()` for terminal voice mode.
- Added Leo branding, sidebar navigation, model badge, status bar, animated
  state orb, chat history, text composer, send button, and microphone button.
- Wired text responses to the real `core.agent.build_leo()` graph and SQLite
  message persistence.
- Wired microphone capture to the real `core.voice.listen()` callback, including
  `listening`, `transcribing`, `thinking`, `speaking`, `idle`, and `error`
  states.
- Added real memory management UI backed by `get_all_facts`, `save_fact`, and
  `delete_fact`, with deletion confirmation.
- Added new-conversation confirmation and activity/settings status views.
- Kept all inference, recording, TTS, and external work off the Tk event loop.
- Added UI state regression coverage and installation/launch documentation.

## Verification

| Check | Result | Evidence |
|---|---|---|
| Regression suite | PASS | `8 passed, 1 skipped` in project `venv` |
| Compilation | PASS | `python -m compileall -q core tests` |
| Patch validation | PASS | `git diff --check` |
| Main window lifecycle | PASS | Tk window created, rendered, and closed through `LeoDesktopApp.shutdown()` |
| State vocabulary | PASS | Automated test covers idle/listening/transcribing/thinking/speaking/error |
| Backend integration | PASS | UI calls real graph, memory, voice, and TTS boundaries; backend tests remain green |

## Remaining manual verification

Visual spacing, animation quality, keyboard focus, audible voice playback,
microphone speech, and full multi-turn UI interaction still require a human
desktop session. No screenshots were fabricated, and no commit or push was
performed.

## Phase 11.1 runtime correction

The first GUI acceptance attempt used `python -m core.ui` from the system
interpreter. On this Windows host that interpreter was
`Python314\python.exe` and did not contain `langchain_core`; the project
`venv\Scripts\python.exe` did contain all declared LangChain/Ollama packages.
The broad dependency error therefore hid an interpreter mismatch rather than a
missing project dependency.

`run_leo.bat` now resolves its own directory, verifies the project-local
imports, and launches `core.ui` with the venv interpreter. `core.agent` now
reports the specific missing package or Ollama/LangGraph failure and records a
local traceback in ignored `leo.log`.
