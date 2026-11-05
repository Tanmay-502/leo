from core.agent import clean_response, is_greeting, try_handle_remember


def test_agent_helpers(monkeypatch):
    assert is_greeting("Hello, Leo")
    assert clean_response("") == "Sorry, I didn't catch that clearly. Could you repeat it?"
    saved = []
    monkeypatch.setattr("core.agent.save_fact", saved.append)
    assert "remember" in try_handle_remember("Remember that I like tea")
    assert saved == ["I like tea"]
