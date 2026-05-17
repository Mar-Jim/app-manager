from dev_workbench.ado import AdoPermissionError, AzureDevOpsService
from dev_workbench.models import AdoTicket
from dev_workbench.storage import initialize_database


class MockAdoClient:
    def __init__(self):
        self.posted: list[tuple[int, str]] = []

    def list_tickets(self):
        return [
            AdoTicket(
                id=123,
                title="Fix failing job",
                state="Active",
                assigned_to="Developer",
                work_item_type="Bug",
            )
        ]

    def get_ticket(self, ticket_id: int):
        return AdoTicket(id=ticket_id, title="Fix failing job", state="Active")

    def post_comment(self, ticket_id: int, body: str):
        self.posted.append((ticket_id, body))


def test_initialize_database_creates_ado_tables(tmp_path):
    db_path = initialize_database(tmp_path / "workbench.sqlite3")

    import sqlite3

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()

    table_names = {row[0] for row in rows}
    assert {"ado_config", "ticket_update_drafts"}.issubset(table_names)


def test_ado_no_token_returns_setup_guidance(tmp_path, monkeypatch):
    monkeypatch.setenv("WORKBENCH_ADO_ORGANIZATION_URL", "https://dev.azure.com/example")
    monkeypatch.setenv("WORKBENCH_ADO_PROJECT", "Demo")
    monkeypatch.setenv("WORKBENCH_ADO_PAT_ENV_VAR", "MISSING_ADO_PAT")
    monkeypatch.delenv("MISSING_ADO_PAT", raising=False)

    result = AzureDevOpsService(db_path=tmp_path / "workbench.sqlite3").list_tickets()

    assert result.tickets == []
    assert result.config.configured is True
    assert result.config.token_available is False
    assert "MISSING_ADO_PAT" in (result.config.setup_guidance or "")


def test_ado_lists_tickets_with_mock_client(tmp_path, monkeypatch):
    monkeypatch.setenv("WORKBENCH_ADO_ORGANIZATION_URL", "https://dev.azure.com/example")
    monkeypatch.setenv("WORKBENCH_ADO_PROJECT", "Demo")
    monkeypatch.setenv("WORKBENCH_ADO_PAT_ENV_VAR", "MOCK_ADO_PAT")
    monkeypatch.setenv("MOCK_ADO_PAT", "not-stored")

    result = AzureDevOpsService(db_path=tmp_path / "workbench.sqlite3", client=MockAdoClient()).list_tickets()

    assert [ticket.id for ticket in result.tickets] == [123]
    assert result.config.personal_access_token_env_var == "MOCK_ADO_PAT"


def test_ado_draft_generation_uses_local_notes(tmp_path, monkeypatch):
    monkeypatch.setenv("WORKBENCH_ADO_ORGANIZATION_URL", "https://dev.azure.com/example")
    monkeypatch.setenv("WORKBENCH_ADO_PROJECT", "Demo")
    monkeypatch.setenv("WORKBENCH_ADO_PAT_ENV_VAR", "MOCK_ADO_PAT")
    monkeypatch.setenv("MOCK_ADO_PAT", "not-stored")
    service = AzureDevOpsService(db_path=tmp_path / "workbench.sqlite3", client=MockAdoClient())

    draft = service.create_draft_update(123, note="Implemented the local parser.")

    assert draft.posted is False
    assert "Update for #123: Fix failing job" in draft.body
    assert "- Implemented the local parser." in draft.body


def test_ado_post_requires_confirmation(tmp_path):
    service = AzureDevOpsService(db_path=tmp_path / "workbench.sqlite3", client=MockAdoClient())
    service.create_draft_update(123, note="Draft only.")

    try:
        service.post_update(123, from_draft=True, yes=False)
    except AdoPermissionError as exc:
        assert "explicit --yes" in str(exc)
    else:
        raise AssertionError("post_update should require explicit approval")


def test_ado_post_uses_latest_draft_after_approval(tmp_path, monkeypatch):
    monkeypatch.setenv("WORKBENCH_ADO_ORGANIZATION_URL", "https://dev.azure.com/example")
    monkeypatch.setenv("WORKBENCH_ADO_PROJECT", "Demo")
    monkeypatch.setenv("WORKBENCH_ADO_PAT_ENV_VAR", "MOCK_ADO_PAT")
    monkeypatch.setenv("MOCK_ADO_PAT", "not-stored")
    client = MockAdoClient()
    service = AzureDevOpsService(db_path=tmp_path / "workbench.sqlite3", client=client)
    draft = service.create_draft_update(123, note="Ready for review.")

    result = service.post_update(123, from_draft=True, yes=True)

    assert result.posted is True
    assert result.draft_id == draft.id
    assert client.posted == [(123, draft.body)]
