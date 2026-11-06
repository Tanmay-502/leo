# Leo desktop UI acceptance report

Date: 2026-11-06
Branch: `feat/leo-stabilization`

## Runtime and launcher

| Test | Expected | Actual | Status | Evidence |
|---|---|---|---|---|
| Documented launcher | Full premium desktop app is documented | README documents `.\run_leo.bat`; direct equivalent is `.\venv\Scripts\python.exe -m core.ui` | PASS | README and `run_leo.bat` |
| Actual Windows launch | Desktop process starts and remains alive | `python -m core.ui` created a live GUI process for the launcher smoke window | PASS | Windows process remained alive for 5 seconds |
| Interpreter selection | GUI and worker use project dependencies | System Python lacked `langchain_core`; `venv\Scripts\python.exe` imported `langchain_core`, `langchain_ollama`, and `langgraph` and passed `pip check` | FIXED | Interpreter comparison |
| Launcher dependency guard | Incomplete setup is actionable | `run_leo.bat` checks the venv and required imports before starting `core.ui` | PASS | Script inspection |

## Real desktop UI exercise

| Test | Expected | Actual | Status | Evidence |
|---|---|---|---|---|
| Main window render | Full window has the documented shell | Tk inspection reported `1120x720`, minimum `880x600`, sidebar, header, chat, composer, orb, and status bar | PASS | `LeoDesktopApp` runtime inspection |
| Batch launcher process | The supported launcher uses the venv GUI process | `run_leo.bat` created a child Python process at `venv\Scripts\python.exe` and was stopped by PID after verification | PASS | Windows process inspection |
| Resize/minimize/maximize/restore | Window lifecycle remains usable | `900x620`, `zoomed`, `iconic`, then `normal` states were reached | PASS | Runtime window-state exercise |
| Sidebar navigation | Each sidebar action responds | New conversation, Memories, Activity, and Settings handlers were invoked; Memories opened a dialog and Activity/Settings changed page state | PARTIAL | Activity is status-only; Settings is informational-only |
| Chat with actual Ollama/LangGraph | Real response appears in chat | With the venv interpreter and real graph, `GUI_OK` appeared in the chat history and rendered Text widget | PASS | `venv\Scripts\python.exe` UI exercise |
| Follow-up context | Second message uses prior context | Two UI turns completed and rendered; the first constrained prompt produced the model fallback, while the second produced `NAME_RECALLED`, so semantic recall is not accepted as proven by this run | PARTIAL | Requires a clearer human conversation test |
| SQLite restart persistence | Conversation reloads after restart | UI constructor reloads persisted history; runtime exercise confirmed saved user history survived a second app instance | PASS | Temporary SQLite database |
| Memory add/delete | UI actions update saved facts | Memory dialog opened; add/delete control path was exercised with a temporary fact | PASS | Temporary SQLite database |
| Voice callback states | Listening/transcribing/idle flow is reflected | Callback exercise observed `listening`, `transcribing`, and `idle` through the real UI event queue | PASS (callback) | Runtime state capture |
| Physical microphone speech | Spoken phrase is transcribed | Requires a person speaking into the selected Windows microphone | MANUAL VERIFICATION REQUIRED | See instructions below |
| Animated orb | Orb reflects state colors and animates | State-to-color mapping and animation scheduling are present; visual appearance requires direct observation | MANUAL VERIFICATION REQUIRED | No visual screenshot fabricated |
| Graceful shutdown | No Tk callbacks execute after close | Shutdown previously left `after` callbacks scheduled; cancellation was added for polling and orb animation | FIXED | Reproduced `invalid command name ... after destroy` and patched |

## Confirmed defects and fixes

- **Fixed:** system Python was the documented launch path, while the installed
  dependencies were only in the project venv. `run_leo.bat` now explicitly
  selects `venv\Scripts\python.exe`.
- **Fixed:** `core.agent.build_leo()` converted every import failure into the
  same generic message. It now identifies the missing package, distinguishes
  LangGraph/Ollama initialization from request failures, and logs a local
  traceback to `leo.log`.
- **Fixed:** Tk `after` callbacks could run after `shutdown()` destroyed the
  root window. Polling and orb callback IDs are now cancelled before destroy.

## Remaining UI limitations

- Activity currently changes the title and status text but does not render an
  activity history page.
- Settings currently shows configuration in an informational dialog; there
  are no editable controls, so settings persistence cannot be accepted as a
  GUI feature.
- There is no visible microphone stop/cancel control while recording.
- The status bar says “Microphone available” unconditionally; device
  availability is not queried by the desktop UI.

These are not claimed as passed. They require follow-up implementation if
editable settings, activity history, or recording cancellation are required.

## Manual verification required

1. Double-click `run_leo.bat` from the repository root.
2. Confirm the window opens at the dark Leo desktop layout and resize it,
   minimize it, maximize it, restore it, and close it.
3. Send `Hello Leo`; confirm a Leo response appears in the chat and the orb
   changes through thinking/speaking before returning to Ready.
4. Send `My name is Tanmay`, then `What is my name?`; confirm the second
   response uses the first message.
5. Close and relaunch with `run_leo.bat`; confirm the conversation remains.
6. Open Memories, add a temporary fact, verify it appears, delete it, and
   verify it disappears after reopening the dialog.
7. Click the microphone button, speak “Hello Leo”, and confirm the UI shows
   Listening → Transcribing → Thinking → Speaking. Stop/close the app and
   confirm no orphaned window or audio process remains.

## Regression

The project-venv rerun completed with `8 passed, 1 skipped`; compilation,
required-import checks, `pip check`, and `git diff --check` also passed.
