from pathlib import Path
import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models.job import GenerationJob
from app.models.certificate import Certificate
from app.services.certificate_generator import generate_certificate


client = TestClient(app)


def test_get_job_certificates():

    create_response = client.post(
        "/api/jobs/",
        json={
            "event_name": "AEREO Internship Completion",
            "recipients": [
                {
                    "name": "Irfan",
                    "email": "irfan@example.com"
                }
            ]
        }
    )

    assert create_response.status_code == 202

    job_id = create_response.json()["job_id"]

    response = client.get(
        f"/api/jobs/{job_id}/certificates"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["job_id"] == job_id
    assert len(data["certificates"]) == 1

    certificate = data["certificates"][0]

    assert certificate["recipient_name"] == "Irfan"
    assert certificate["recipient_email"] == "irfan@example.com"
    assert certificate["status"] in [
        "PENDING",
        "COMPLETED",
        "FAILED"
    ]

    assert "certificate_id" in certificate
    assert "download_url" in certificate


def test_download_certificate():

    db = SessionLocal()

    job_id = str(uuid.uuid4())
    certificate_id = str(uuid.uuid4())

    file_path = None

    try:

        job = GenerationJob(
            id=job_id,
            event_name="AEREO Internship Completion",
            status="COMPLETED",
            total=1,
            completed=1,
            failed=0
        )

        db.add(job)

        file_path = generate_certificate(
            recipient_name="Download Test",
            event_name="AEREO Internship Completion",
            certificate_id=certificate_id
        )

        certificate = Certificate(
            id=certificate_id,
            job_id=job_id,
            recipient_name="Download Test",
            recipient_email="download@example.com",
            status="COMPLETED",
            file_path=file_path
        )

        db.add(certificate)
        db.commit()

        response = client.get(
            f"/api/certificates/{certificate_id}/download"
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

        assert len(response.content) > 0

    finally:

        db.query(Certificate).filter(
            Certificate.id == certificate_id
        ).delete()

        db.query(GenerationJob).filter(
            GenerationJob.id == job_id
        ).delete()

        db.commit()
        db.close()

        if file_path:
            path = Path(file_path)

            if path.exists():
                path.unlink()