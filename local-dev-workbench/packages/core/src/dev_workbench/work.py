from datetime import date, datetime
from pathlib import Path

from dev_workbench.models import TicketNote, Todo, WorkLogEntry
from dev_workbench.storage import connect

BLOCKER_WORDS = ("block", "blocked", "blocker", "stuck", "waiting", "dependency", "depends on")


class WorkbenchService:
    """Local daily work service with a storage boundary for future ticket integrations."""

    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path

    def add_todo(self, text: str) -> Todo:
        cleaned = _clean_text(text)
        now = _now()
        with connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO todos (text, is_completed, created_at) VALUES (?, 0, ?)",
                (cleaned, now),
            )
            row = conn.execute("SELECT * FROM todos WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return _todo_from_row(row)

    def list_todos(self) -> list[Todo]:
        with connect(self.db_path) as conn:
            rows = conn.execute("SELECT * FROM todos ORDER BY is_completed ASC, id ASC").fetchall()
        return [_todo_from_row(row) for row in rows]

    def complete_todo(self, todo_id: int) -> Todo:
        now = _now()
        with connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE todos
                SET is_completed = 1, completed_at = COALESCE(completed_at, ?)
                WHERE id = ?
                """,
                (now, todo_id),
            )
            row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
        if row is None:
            raise ValueError(f"todo not found: {todo_id}")
        return _todo_from_row(row)

    def add_worklog(self, text: str) -> WorkLogEntry:
        cleaned = _clean_text(text)
        now = _now()
        with connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO work_log_entries (text, created_at) VALUES (?, ?)",
                (cleaned, now),
            )
            row = conn.execute("SELECT * FROM work_log_entries WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return _worklog_from_row(row)

    def list_worklog(self, day: date | None = None) -> list[WorkLogEntry]:
        selected_day = day or date.today()
        with connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM work_log_entries
                WHERE substr(created_at, 1, 10) = ?
                ORDER BY id ASC
                """,
                (selected_day.isoformat(),),
            ).fetchall()
        return [_worklog_from_row(row) for row in rows]

    def add_ticket_note(self, ticket_ref: str, text: str) -> TicketNote:
        cleaned_ref = _clean_text(ticket_ref)
        cleaned_text = _clean_text(text)
        now = _now()
        with connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO ticket_notes (ticket_ref, text, created_at) VALUES (?, ?, ?)",
                (cleaned_ref, cleaned_text, now),
            )
            row = conn.execute("SELECT * FROM ticket_notes WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return _ticket_note_from_row(row)

    def generate_daily_summary(self, day: date | None = None) -> str:
        selected_day = day or date.today()
        worklog = self.list_worklog(selected_day)
        todos = self.list_todos()
        completed = [
            todo.text
            for todo in todos
            if todo.completed and todo.completed_at and todo.completed_at.startswith(selected_day.isoformat())
        ]
        in_progress = [todo.text for todo in todos if not todo.completed]
        blockers = [entry.text for entry in worklog if _looks_like_blocker(entry.text)]

        sections = [
            ("Today I worked on:", [entry.text for entry in worklog]),
            ("Completed:", completed),
            ("In progress:", in_progress),
            ("Blockers:", blockers),
            ("Next steps:", in_progress),
        ]
        return "\n".join(_format_section(title, items) for title, items in sections)


def _clean_text(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("text is required")
    return cleaned


def _now() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def _todo_from_row(row) -> Todo:
    return Todo(
        id=row["id"],
        text=row["text"],
        completed=bool(row["is_completed"]),
        created_at=row["created_at"],
        completed_at=row["completed_at"],
    )


def _worklog_from_row(row) -> WorkLogEntry:
    return WorkLogEntry(id=row["id"], text=row["text"], created_at=row["created_at"])


def _ticket_note_from_row(row) -> TicketNote:
    return TicketNote(id=row["id"], ticket_ref=row["ticket_ref"], text=row["text"], created_at=row["created_at"])


def _looks_like_blocker(text: str) -> bool:
    lowered = text.lower()
    return any(word in lowered for word in BLOCKER_WORDS)


def _format_section(title: str, items: list[str]) -> str:
    if not items:
        return f"{title}\n- None"
    return "\n".join([title, *[f"- {item}" for item in items]])
