import sqlite3
from pathlib import Path


def default_db_path() -> Path:
    return Path.cwd() / ".workbench" / "workbench.sqlite3"


def connect(path: Path | None = None) -> sqlite3.Connection:
    db_path = initialize_database(path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database(path: Path | None = None) -> Path:
    db_path = path or default_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS command_history (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              command_id TEXT NOT NULL,
              command_text TEXT NOT NULL,
              approved INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS todos (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              text TEXT NOT NULL,
              is_completed INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL,
              completed_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS work_log_entries (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              text TEXT NOT NULL,
              created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ticket_notes (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              ticket_ref TEXT NOT NULL,
              text TEXT NOT NULL,
              created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ado_config (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ticket_update_drafts (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              ticket_ref TEXT NOT NULL,
              body TEXT NOT NULL,
              posted INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL,
              posted_at TEXT
            )
            """
        )
    return db_path
