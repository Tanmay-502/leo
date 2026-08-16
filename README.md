# Leo — Offline Voice Assistant

Leo is a Siri-style personal voice assistant that runs **fully offline** —
no cloud API, no subscription, no internet required for the AI itself.

## Features
- Natural conversation (offline LLM via Ollama)
- Real Google Calendar (check + schedule meetings)
- Real Gmail (read unread + send emails)
- Live weather, web search, news headlines
- Opens desktop apps by voice
- Remembers facts and conversation history across restarts
- Floating popup UI showing listening/thinking/speaking states

## Minimum device specs (tested)
| Component | Minimum | Recommended |
|---|---|---|
| CPU | Dual-core 2.0GHz+ | Quad-core i5/Ryzen 5+ |
| RAM | 8GB | 16GB |
| GPU | Not required | Any CUDA GPU (much faster) |
| Storage | 5GB free | 10GB free |
| OS | Windows 10/11 | Same |
| Internet | Only for setup, weather/search/news tools, and Google sync | Same |

## Setup (new machine)

1. Install [Python 3.10+](https://python.org)
2. Install [Ollama](https://ollama.com), then run:

ollama pull llama3.2

3. Clone this repo:

git clone https://github.com/Tanmay-502/leo.git
cd leo

4. Create and activate a virtual environment:

python -m venv venv
venv\Scripts\activate

5. Install dependencies:

pip install -r requirements.txt

6. Add your own Google credentials:
   - Copy your `credentials.json` (from Google Cloud Console) into the project root
   - `token.json` will be created automatically on first login

7. Run Leo:

python -m core.agent # text mode
python -m core.voice_loop # voice mode with popup UI


## Notes
- If your microphone isn't picked up automatically, find your device index with:

python -c "import sounddevice as sd; print(sd.query_devices())"

  Then set it via environment variable before running:

set LEO_MIC_INDEX=2