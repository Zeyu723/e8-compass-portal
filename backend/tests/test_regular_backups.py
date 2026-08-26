from fastapi.testclient import TestClient

from app.main import app
from app.services.demo_data import SAMPLE_POLICY

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_controls_include_regular_backups() -> None:
    response = client.get("/controls")
    assert response.status_code == 200
    controls = response.json()
    regular_backups = [control for control in controls if control["name"] == "Regular Backups"]
    assert regular_backups
    assert regular_backups[0]["implemented"] is True


def test_sample_result_is_insufficient_evidence() -> None:
    response = client.get("/demo/sample-result")
    assert response.status_code == 200
    body = response.json()
    assert body["final_result"]["status"] == "Insufficient Evidence"
    assert body["evidence_quality"]["confidence_score"] == 0.147


def test_regular_backups_fallback_without_key() -> None:
    response = client.post(
        "/assessments/regular-backups",
        json={
            "scope": "Part of a document",
            "control": "Regular Backups",
            "input_type": "Policy",
            "content": SAMPLE_POLICY,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["final_result"]["status"] == "Insufficient Evidence"
    assert body["metadata"]["used_fallback"] is True
