import sqlite3
from pathlib import Path


def default_db_path() -> Path:
    return Path.cwd() / ".workbench" / "workbench.sqlite3"


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
    return db_path
