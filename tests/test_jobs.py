from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_job():

    response = client.post(
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

    assert response.status_code == 202

    data = response.json()

    assert "job_id" in data
    assert data["status"] == "PENDING"
    assert data["total"] == 2
    assert data["completed"] == 0
    assert data["failed"] == 0

def test_empty_recipients():

    response = client.post(
        "/api/jobs/",
        json={
            "event_name": "AEREO Internship Completion",
            "recipients": []
        }
    )

    assert response.status_code == 422


def test_invalid_email():

    response = client.post(
        "/api/jobs/",
        json={
            "event_name": "AEREO Internship Completion",
            "recipients": [
                {
                    "name": "Irfan",
                    "email": "invalid-email"
                }
            ]
        }
    )

    assert response.status_code == 422