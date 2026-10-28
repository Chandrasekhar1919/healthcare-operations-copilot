from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_get_and_approve_flow():
    payload = {
        "request_id": "API-100",
        "request_type": "referral",
        "submitted_urgency": "routine",
        "requested_service": "Synthetic specialist referral",
        "referring_department": "Primary Care",
        "consent_confirmed": False,
        "attachments": [],
    }
    analyzed = client.post("/v1/intakes/analyze", json=payload)
    assert analyzed.status_code == 200
    assert analyzed.json()["status"] == "needs_human_review"

    fetched = client.get("/v1/intakes/API-100")
    assert fetched.status_code == 200

    approved = client.post(
        "/v1/intakes/API-100/approve",
        json={"reviewer": "Operations Reviewer", "note": "Synthetic test approval"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert approved.json()["audit_trail"][-1]["event"] == "human_approved"

