# Leo end-to-end acceptance report

Date: 2026-11-05 (Phase 10.1 update)
Branch: `feat/leo-stabilization`
Commit under test: `7a90bf918a9af749cc6cc3ab36e17d4d17135558`

## Summary

The isolated project `venv` is now installed from `requirements.txt` and dependency consistency passes. The Python LangGraph/Ollama path, tool binding/execution, Whisper model loading, microphone capture/silence detection, offline TTS initialization, Google imports, and live information tools were exercised. No real email was sent and no calendar event was created.

## Automated and local tests

| Test case | Expected result | Actual result | Status | Evidence |
|---|---|---|---|---|
| Pytest suite | Tests run without live services | `7 passed, 1 skipped` after running in the project `venv` | PASS | `venv\Scripts\python.exe -m pytest -v` |
| Python compilation | Core modules compile | Passed | PASS | `python -m compileall -q core` |
| Diff validation | No whitespace errors | Passed | PASS | `git diff --check` |
| Configuration | Environment values are applied | Custom model/history values loaded correctly | PASS | `Settings.from_env(...)` |
| SQLite persistence | Messages survive a connection/session boundary | User and assistant messages reloaded in order | PASS | Temporary SQLite database |
| Explicit memory | Facts persist, deduplicate, list, and delete | Fact saved, duplicate rejected, then deleted | PASS | Temporary SQLite database |
| Conversation clearing | Short-term history can be removed | History cleared while facts remained separate | PASS | Temporary SQLite database |
| Safe app validation | Unknown applications are rejected; no shell injection | `cmd.exe` rejected; mocked launch uses `shell=False` | PASS | `tests/test_config_tools.py` |
| Input validation | Invalid email/date inputs are rejected | Invalid recipient and date returned clear errors | PASS | Direct tool calls |
| External failure handling | Service failures return honest errors | Weather/network and unavailable dependency paths returned errors | PASS | Direct tool calls |
| Ollama local inference | Installed local model generates text | `ollama run llama3.2` returned `Leo local inference passed` | PASS | Ollama CLI output |
| Tkinter lifecycle | UI can create and close a window | Window created, event loop exited, and printed `Tkinter lifecycle passed` | PASS | Direct Tkinter smoke test |
| Secret tracking | Credentials and databases are not tracked | `.env`, `credentials.json`, `token.json`, `leo.db`, and SQLite files absent from Git index | PASS | `git ls-files` audit |
| Arbitrary shell execution | No natural-language shell path exists | No `os.system` or `shell=True` path found | PASS | `git grep` audit |
| Real microphone sentence | A spoken sentence is captured and transcribed | Capture completed but returned empty text because no speech was available during unattended testing | NOT TESTED | Requires user to speak the listed phrases |
| Offline speaker audibility | Test sentence is audibly heard through Windows speakers | `pyttsx3` playback call completed; audible confirmation was not available unattended | NOT TESTED | Requires physical confirmation |
| Complete voice loop | Repeated listen/thinking/speaking/stop flow completes | Bounded run stayed listening on silence and was stopped externally; no spoken interaction was available | NOT TESTED | Requires user speech and physical confirmation |
| Dependency installation | Complete project environment installs consistently | `pip install -r requirements.txt` succeeded; `pip check` reported no broken requirements | PASS | Project-local `venv` |
| Python imports | Declared runtime integrations import | LangChain, LangGraph, Ollama, Whisper, audio, TTS, Google, DDGS, and feedparser imports passed | PASS | Project `venv` import smoke test |

Pytest intentionally skips the old live Groq smoke test because it requires a provider credential and network access.

## Component acceptance

| Component | Expected result | Actual result | Status | Evidence / limitation |
|---|---|---|---|---|
| Ollama service and model | Local model is available and responds | `phi3:mini`, `llama3.2`, and `llama3.1` are installed; `llama3.2` generated a response | PASS | Ollama CLI verified |
| Python LangGraph/Ollama text mode | Text conversation runs through the Python graph | Graph built and returned `Leo Python graph passed` from local `llama3.2` | PASS | Project `venv`, `build_leo().invoke(...)` |
| Follow-up context | Conversation context is bounded and retained | Two local graph turns preserved the user's stated name and answered the follow-up correctly | PASS | `build_leo().invoke(...)` twice |
| Tool binding and execution | Model can bind and execute registered tools | Weather request executed through the graph and returned current Indore weather | PASS | `build_leo().invoke(...)` |
| Persistent memory across restart | SQLite data reloads after process boundary | Persistence and reload verified with a temporary database | PASS | Direct memory smoke test |
| Memory retrieval/list/delete | User can inspect and remove explicit facts | Save, deduplicate, list, delete behavior verified | PASS | Direct memory smoke test |
| Faster Whisper recognition | Whisper model loads locally | Whisper `tiny` loaded successfully | PASS (model) | Transcription still needs spoken sample |
| Silence detection | Quiet samples return no command | 0.25-second microphone capture returned an empty transcription | PASS | Default microphone device |
| Microphone selection | Configured device index is used | Audio devices detected, including microphone array; no forced index used | PASS (discovery) | Hardware is present; configured-index selection remains manual |
| Offline TTS | Speech provider initializes without internet | `pyttsx3` initialized with 2 voices; actual audible playback was not asserted | PASS (initialization) | Speaker playback remains manual |
| Edge TTS | Optional online voice works and temp files are cleaned | Package initialized, but synthesis received a provider HTTP 403 | BLOCKED | External Edge service rejection; not a local dependency failure |
| Google Calendar | Read/create operations work with OAuth | Google packages/imports passed; credentials are absent, so no API call was made | BLOCKED | No event was created; requires OAuth setup |
| Gmail | Read/send operations work with OAuth | Google packages/imports passed; credentials are absent, so no API call was made | BLOCKED | No email was sent; requires OAuth setup |
| Weather | Live weather is returned or failure is explicit | Graph weather request returned current Indore weather | PASS | Live Open-Meteo request |
| Web search | Search results are returned or failure is explicit | Returned linked Ollama results through `web_search.invoke(...)` | PASS | Live DDGS request |
| News | Headlines are returned or failure is explicit | Returned linked BBC headlines through `get_news.invoke(...)` | PASS | Live RSS request |
| Safe Windows app launching | Registered app launches without shell interpolation | Validation and mocked `Popen([...], shell=False)` passed; actual launch not performed to avoid opening apps during unattended testing | PASS (safe path) | Manual visual launch remains |
| Floating Tkinter UI | Popup can initialize and shut down | Tkinter create/event-loop/destroy smoke test passed | PASS | Visual state rendering remains manual |
| Graceful voice shutdown | Stop command exits loop and returns idle state | Stop branch is present; bounded no-speech loop was terminated without an application crash | NOT TESTED | Spoken stop command requires user speech |

## Defects found and fixes applied

One test compatibility defect was reproduced after installing LangChain: decorated tools become `StructuredTool` instances and must be called through `.invoke(...)`. The deterministic tests were updated accordingly. A state-machine defect was also found: the UI skipped `TRANSCRIBING`; `listen()` now accepts a progress callback and the UI displays the state between recording and model inference. README installation guidance was expanded to distinguish core and integration dependencies.

## Offline capability

Verified offline:

- SQLite memory operations
- Configuration and validation helpers
- Safe application command construction
- Tkinter lifecycle
- Ollama local inference through the installed Ollama CLI

Verified offline or local:

- Python LangGraph/Ollama adapter path against the local Ollama service
- faster-whisper model loading
- Microphone capture and silence detection
- Offline TTS initialization

Requires internet:

- Edge TTS
- Weather
- Web search
- RSS news
- Google OAuth refresh/login and Calendar/Gmail APIs

## Manual steps required

1. Activate the project virtual environment with `venv\Scripts\activate` when testing locally.
2. Configure `.env` and run `ollama pull llama3.2` if the model is missing.
3. Configure a microphone and Windows microphone permission, then set `LEO_MIC_INDEX` if needed.
4. Verify audible `pyttsx3` playback; use `LEO_TTS_PROVIDER=edge` only when the Edge provider accepts requests.
5. Configure Google Cloud OAuth desktop credentials and run read-only Calendar/Gmail checks first. Do not send mail or create events unless you explicitly approve the exact action.
6. Run the voice loop and visually verify listening, thinking, speaking, error, stop, and shutdown behavior.

## Remaining limitations

- This environment cannot prove intelligible spoken transcription, audible speaker output, Edge TTS provider availability, or Google OAuth behavior without user interaction/credentials.
- Edge TTS currently receives HTTP 403 from the external provider.
- Actual Windows app launching was not performed automatically because it would open external applications; the subprocess safety path is covered by mocks.
- The Tkinter lifecycle passed, but visual popup appearance and animation require a human desktop check.
- Actual spoken phrases and audible output still require physical confirmation at the machine.
