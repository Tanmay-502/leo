import subprocess

from core.config import Settings
from core import tools


def test_settings_are_configurable():
    settings = Settings.from_env({"LEO_OLLAMA_MODEL": "qwen", "LEO_HISTORY_LIMIT": "5"})
    assert settings.model == "qwen"
    assert settings.history_limit == 5


def test_weather_failure_is_honest(monkeypatch):
    def fail(*args, **kwargs):
        raise tools.requests.Timeout()
    monkeypatch.setattr(tools.requests, "get", fail)
    assert "couldn't fetch weather" in tools.get_weather.invoke({"city": "Indore"}).lower()


def test_open_app_uses_safe_subprocess(monkeypatch):
    calls = []
    monkeypatch.setattr(subprocess, "Popen", lambda command, shell: calls.append((command, shell)))
    assert "Opening" in tools.open_app.invoke({"app_name": "Notepad"})
    assert calls == [(["notepad"], False)]
    assert "don't know" in tools.open_app.invoke({"app_name": "cmd.exe"})
