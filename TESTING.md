# Testing

Run `python -m pytest -q`. Tests use temporary SQLite databases and mocks; they do not need a microphone, Ollama, Google account, paid API, or live internet. Hardware and external-service smoke tests should be run manually after configuring `.env`.

Useful checks:

```text
python -m compileall -q core
python -m pytest -q
python -m core.agent
python -m core.voice_loop
```
