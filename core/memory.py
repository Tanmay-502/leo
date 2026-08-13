# core/memory.py
# Gives Leo persistent memory across restarts using SQLite.
# Without this, Leo forgets everything the moment you close the terminal —
# every real assistant needs to remember context between sessions.

import sqlite3
from datetime import datetime

DB_FILE = "leo.db"


def init_db():
    """Creates the database and tables if they don't already exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Stores every message exchanged, so we can reload recent context on startup
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    # Stores explicit "remember this" facts the user tells Leo directly
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fact TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def save_message(role: str, content: str):
    """Saves one message (user or assistant) to conversation history."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conversation_history (role, content, timestamp) VALUES (?, ?, ?)",
        (role, content, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def load_recent_history(limit=10):
    """Loads the last `limit` messages so Leo can pick up where it left off."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content FROM conversation_history ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()

    # Reverse since we fetched newest-first but want oldest-first for context
    return [{"role": role, "content": content} for role, content in reversed(rows)]


def save_fact(fact: str):
    """Saves an explicit fact the user asked Leo to remember."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO memories (fact, timestamp) VALUES (?, ?)",
        (fact, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_all_facts():
    """Retrieves all remembered facts."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT fact FROM memories ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]