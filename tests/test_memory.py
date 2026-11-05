import core.memory as memory


def test_memory_persists_deduplicates_and_deletes(tmp_path, monkeypatch):
    monkeypatch.setattr(memory, "DB_FILE", str(tmp_path / "leo.sqlite3"))
    memory.init_db()
    memory.save_message("user", "hello")
    memory.save_message("assistant", "hi")
    assert memory.load_recent_history() == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ]
    assert memory.save_fact("prefers short answers") is True
    assert memory.save_fact("prefers short answers") is False
    assert memory.get_all_facts() == ["prefers short answers"]
    assert memory.delete_fact("short") == 1
    assert memory.get_all_facts() == []


def test_memory_clear_conversation(tmp_path, monkeypatch):
    monkeypatch.setattr(memory, "DB_FILE", str(tmp_path / "leo.sqlite3"))
    memory.save_message("user", "temporary")
    memory.clear_conversation()
    assert memory.load_recent_history() == []
