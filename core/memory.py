"""SQLite persistence for short-term conversation and explicit user facts."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from core.config import settings

DB_FILE = str(settings.db_path)


@contextmanager
def _connection() -> Iterator[sqlite3.Connection]:
    path = Path(DB_FILE)
    if path.parent != Path("."):
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system', 'tool')),
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fact TEXT NOT NULL COLLATE NOCASE UNIQUE,
                timestamp TEXT NOT NULL
            );
            """
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_message(role: str, content: str) -> None:
    if role not in {"user", "assistant", "system", "tool"}:
        raise ValueError("Unsupported message role")
    if not content or not content.strip():
        return
    init_db()
    with _connection() as conn:
        conn.execute(
            "INSERT INTO conversation_history(role, content, timestamp) VALUES (?, ?, ?)",
            (role, content.strip(), _now()),
        )


def load_recent_history(limit: int | None = None) -> list[dict[str, str]]:
    init_db()
    requested = limit or settings.history_limit
    if requested < 1:
        return []
    with _connection() as conn:
        rows = conn.execute(
            "SELECT role, content FROM conversation_history ORDER BY id DESC LIMIT ?",
            (requested,),
        ).fetchall()
    return [{"role": role, "content": content} for role, content in reversed(rows)]


def clear_conversation() -> None:
    init_db()
    with _connection() as conn:
        conn.execute("DELETE FROM conversation_history")


def save_fact(fact: str) -> bool:
    fact = fact.strip()
    if not fact:
        raise ValueError("Fact cannot be empty")
    init_db()
    with _connection() as conn:
        cursor = conn.execute(
            "INSERT OR IGNORE INTO memories(fact, timestamp) VALUES (?, ?)",
            (fact, _now()),
        )
    return cursor.rowcount == 1


def get_all_facts() -> list[str]:
    init_db()
    with _connection() as conn:
        return [row[0] for row in conn.execute(
            "SELECT fact FROM memories ORDER BY id DESC"
        )]


def delete_fact(query: str) -> int:
    query = query.strip()
    if not query:
        return 0
    init_db()
    with _connection() as conn:
        cursor = conn.execute(
            "DELETE FROM memories WHERE fact LIKE ? COLLATE NOCASE",
            (f"%{query}%",),
        )
    return cursor.rowcount


def clear_facts() -> None:
    init_db()
    with _connection() as conn:
        conn.execute("DELETE FROM memories")
