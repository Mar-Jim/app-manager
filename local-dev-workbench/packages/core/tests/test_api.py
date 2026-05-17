from fastapi.testclient import TestClient

from dev_workbench.api.app import create_app


def test_health():
    client = TestClient(create_app())
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_project_detect_returns_detection_result(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "package.json").write_text('{"name":"demo"}\n', encoding="utf-8")
    client = TestClient(create_app())

    response = client.get("/api/project/detect")

    assert response.status_code == 200
    payload = response.json()
    assert payload["project"]["project_type"] == "node_project"
    assert payload["project"]["detected_files"] == ["package.json"]


def test_commands_suggest_returns_bundle_commands(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "databricks.yml").write_text("targets:\n  dev: {}\n", encoding="utf-8")
    client = TestClient(create_app())

    response = client.get("/api/commands/suggest")

    assert response.status_code == 200
    payload = response.json()
    assert [command["id"] for command in payload] == [
        "validate-bundle",
        "run-tests",
        "deploy-dev",
        "bundle-summary",
    ]
    assert payload[2]["risk_level"] == "medium"


def test_commands_run_requires_confirmation_for_medium(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "databricks.yml").write_text("targets:\n  dev: {}\n", encoding="utf-8")
    client = TestClient(create_app())

    response = client.post("/api/commands/run", json={"command_id": "deploy-dev"})

    assert response.status_code == 400
    assert "require explicit --yes" in response.json()["detail"]


def test_projects_create_dry_run_returns_preview(tmp_path):
    client = TestClient(create_app())

    response = client.post(
        "/api/projects/create",
        json={
            "kind": "bundle-dashboard",
            "name": "demo-dashboard",
            "output_dir": str(tmp_path),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["dry_run"] is True
    assert payload["created"] is False
    assert "databricks.yml" in payload["files"]
    assert not (tmp_path / "demo-dashboard/databricks.yml").exists()


def test_projects_create_writes_files_when_not_dry_run(tmp_path):
    client = TestClient(create_app())

    response = client.post(
        "/api/projects/create",
        json={
            "kind": "bundle-job",
            "name": "demo-job",
            "output_dir": str(tmp_path),
            "dry_run": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["created"] is True
    assert (tmp_path / "demo-job/databricks.yml").exists()


def test_prompts_create_returns_generated_prompt(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "databricks.yml").write_text("targets:\n  dev: {}\n", encoding="utf-8")
    client = TestClient(create_app())

    response = client.post(
        "/api/prompts/create",
        json={"task_type": "add-workflow", "task_description": "Add a handoff workflow."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["task_type"] == "add-workflow"
    assert "Add a handoff workflow." in payload["prompt"]
    assert "This repo usually defines only dev target." in payload["prompt"]


def test_handoff_create_endpoint_writes_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    client = TestClient(create_app())

    response = client.post(
        "/api/handoff/create",
        json={"task_type": "write-tests", "task_description": "Document test status."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["path"].endswith("handoff/current.md")
    assert "## Test Results" in payload["content"]
    assert (tmp_path / "handoff/current.md").exists()


def test_todo_api_add_list_complete(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    client = TestClient(create_app())

    created = client.post("/api/todos", json={"text": "Prepare standup"})
    listed = client.get("/api/todos")
    completed = client.post("/api/todos/1/complete")

    assert created.status_code == 200
    assert created.json()["text"] == "Prepare standup"
    assert listed.status_code == 200
    assert listed.json()[0]["completed"] is False
    assert completed.status_code == 200
    assert completed.json()["completed"] is True


def test_worklog_api_add_list_summary(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    client = TestClient(create_app())

    created = client.post("/api/worklog", json={"text": "Added worklog API"})
    listed = client.get("/api/worklog")
    summary = client.get("/api/worklog/summary")

    assert created.status_code == 200
    assert created.json()["text"] == "Added worklog API"
    assert listed.status_code == 200
    assert listed.json()[0]["text"] == "Added worklog API"
    assert summary.status_code == 200
    assert "Today I worked on:\n- Added worklog API" in summary.json()["summary"]
