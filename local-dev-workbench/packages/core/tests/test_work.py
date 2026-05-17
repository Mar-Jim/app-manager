import sqlite3

from dev_workbench.storage import initialize_database
from dev_workbench.work import WorkbenchService


def test_initialize_database_creates_work_tables(tmp_path):
    db_path = initialize_database(tmp_path / "workbench.sqlite3")

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
        ).fetchall()

    table_names = {row[0] for row in rows}
    assert {"todos", "work_log_entries", "ticket_notes", "command_history"}.issubset(table_names)


def test_add_list_complete_todos(tmp_path):
    service = WorkbenchService(tmp_path / "workbench.sqlite3")

    first = service.add_todo("Write tests")
    second = service.add_todo("Update README")
    completed = service.complete_todo(first.id)
    todos = service.list_todos()

    assert completed.completed is True
    assert completed.completed_at is not None
    assert [todo.text for todo in todos] == ["Update README", "Write tests"]
    assert todos[0].id == second.id
    assert todos[1].completed is True


def test_worklog_summary_generation(tmp_path):
    service = WorkbenchService(tmp_path / "workbench.sqlite3")
    todo = service.add_todo("Wire web UI")
    service.add_todo("Run full test suite")
    service.complete_todo(todo.id)
    service.add_worklog("Implemented SQLite-backed todos")
    service.add_worklog("Blocked waiting on design review")

    summary = service.generate_daily_summary()

    assert "Today I worked on:\n- Implemented SQLite-backed todos\n- Blocked waiting on design review" in summary
    assert "Completed:\n- Wire web UI" in summary
    assert "In progress:\n- Run full test suite" in summary
    assert "Blockers:\n- Blocked waiting on design review" in summary
    assert "Next steps:\n- Run full test suite" in summary
