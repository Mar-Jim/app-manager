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
