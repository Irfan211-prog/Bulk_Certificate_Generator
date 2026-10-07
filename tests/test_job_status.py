from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_get_job_status():

    create_response = client.post(
        "/api/jobs/",
        json={
            "event_name": "AEREO Internship Completion",
            "recipients": [
                {
                    "name": "Irfan",
                    "email": "irfan@example.com"
                },
                {
                    "name": "Rahul",
                    "email": "rahul@example.com"
                }
            ]
        }
    )

    assert create_response.status_code == 202

    job_id = create_response.json()["job_id"]

    status_response = client.get(
        f"/api/jobs/{job_id}"
    )

    assert status_response.status_code == 200

    data = status_response.json()

    assert data["job_id"] == job_id
    assert data["event_name"] == "AEREO Internship Completion"
    assert data["total"] == 2
    assert "completed" in data
    assert "failed" in data
    assert "progress" in data
    assert "completed_at" in data