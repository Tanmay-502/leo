# Leo UI architecture

Leo keeps Tkinter as the desktop toolkit rather than adding a second GUI
framework. It is included with supported Windows Python installations,
requires no graphical runtime dependency, and is straightforward to package
with PyInstaller.

`core.ui.LeoDesktopApp` owns only presentation and orchestration. The
assistant backend remains responsible for model inference (`core.agent`),
persistence (`core.memory`), voice input/output (`core.voice`), and tools
(`core.tools`). UI actions enqueue work on daemon worker threads; workers post
`UiEvent` values to a queue, and Tk applies those events from its `after`
poller. This keeps inference, recording, TTS, and external requests off the
Tk event loop.

The main window contains:

- A branded sidebar with new conversation, memories, activity, and settings.
- A central animated orb whose color follows real idle/listening/transcribing/
  thinking/speaking/error state values.
- A scrollable chat surface backed by SQLite messages.
- Text submission and microphone controls.
- A status bar showing local model and memory state.

`start_ui()` remains a compatibility floating popup for `core.voice_loop`.
`python -m core.ui` launches the full desktop window. The popup and main window
share the same state vocabulary, including the transcription state introduced
in Phase 10.2.
