# Leo

Leo is a privacy-first Windows desktop assistant. Text reasoning runs locally through Ollama, explicit facts and recent conversation are stored in SQLite, and optional tools connect to Google, weather, web search, news, and safe application launching.

## Capabilities

- Local Ollama conversation with bounded context and tool calling
- Explicit memory: remember, list, delete, and clear facts through the memory service
- Offline speech output through `pyttsx3`; optional Edge TTS provider for natural online voices
- Local faster-whisper speech recognition when microphone dependencies are installed
- Google Calendar and Gmail integrations with OAuth
- Weather, web search, RSS news, and a safe application registry
- Dark Tkinter status popup for listening, thinking, speaking, idle, and error states

Internet is required for Google, weather, search, news, and Edge TTS. Ollama inference, SQLite memory, and offline TTS do not require internet after setup.

## Requirements and installation

Windows 10/11, Python 3.10+, and at least 8 GB RAM are recommended.

```powershell
git clone https://github.com/Tanmay-502/leo.git
cd leo
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Install [Ollama](https://ollama.com), start it, and download the configured model:

```powershell
ollama pull llama3.2
```

Run text or voice mode:

```powershell
python -m core.agent
python -m core.voice_loop
```

## Configuration

Edit `.env` to change `LEO_OLLAMA_MODEL`, `LEO_DB_PATH`, `LEO_MIC_INDEX`, `LEO_WHISPER_MODEL`, `LEO_TTS_PROVIDER` (`offline` or `edge`), speech voice/rate, history limits, and Google credential paths. Use `python -c "import sounddevice as sd; print(sd.query_devices())"` to identify a microphone.

## Google setup

Create an OAuth Desktop application in Google Cloud Console, enable Calendar and Gmail APIs, and download the client file as `credentials.json` (or set `LEO_GOOGLE_CREDENTIALS`). Leo creates `token.json` after the first browser login. These files are private and ignored by Git. Calendar writes and Gmail sending should only be used after Leo repeats the requested details and you confirm.

## Testing and troubleshooting

```powershell
python -m pytest -q
python -m compileall -q core
```

Tests use mocks and temporary databases; they do not need a microphone, Google account, Ollama server, or live internet. If Ollama is unavailable, install it, start the service, and run `ollama pull <model>`. If voice input fails, verify the microphone index and Windows permission. Offline speech output requires the `pyttsx3` dependency and a Windows speech engine; Edge TTS requires internet.

## Packaging and privacy

For a Windows build, use PyInstaller after validating the development install (`pyinstaller --onefile --windowed -n Leo core/voice_loop.py`). Keep the database and credentials outside the bundled executable, do not bundle multi-gigabyte Whisper/Ollama models, and provide them separately. Review the generated build on a clean Windows machine before distribution.

Leo never accepts arbitrary shell commands from natural language. Do not commit `.env`, OAuth credentials, tokens, databases, or model files.

Known limitations: hardware audio and Windows speech engines need platform-specific verification; Google OAuth requires user setup; external services can be unavailable or rate-limited; no installer or signed executable is included yet.
