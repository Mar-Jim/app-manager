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
