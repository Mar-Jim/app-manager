from fastapi.testclient import TestClient

from dev_workbench.api.app import create_app


def test_health():
    client = TestClient(create_app())
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
