from pathlib import Path
import uuid
import zipfile

from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models.job import GenerationJob
from app.models.certificate import Certificate
from app.services.certificate_generator import generate_certificate


client = TestClient(app)


def test_download_job_certificates():

    db = SessionLocal()

    job_id = str(uuid.uuid4())
    certificate_ids = [
        str(uuid.uuid4()),
        str(uuid.uuid4())
    ]

    file_paths = []

    try:

        job = GenerationJob(
            id=job_id,
            event_name="AEREO Internship Completion",
            status="COMPLETED",
            total=2,
            completed=2,
            failed=0
        )

        db.add(job)

        recipients = [
            ("Irfan", "irfan@example.com"),
            ("Rahul", "rahul@example.com")
        ]

        for certificate_id, (name, email) in zip(
            certificate_ids,
            recipients
        ):

            file_path = generate_certificate(
                recipient_name=name,
                event_name="AEREO Internship Completion",
                certificate_id=certificate_id
            )

            file_paths.append(file_path)

            certificate = Certificate(
                id=certificate_id,
                job_id=job_id,
                recipient_name=name,
                recipient_email=email,
                status="COMPLETED",
                file_path=file_path
            )

            db.add(certificate)

        db.commit()

        response = client.get(
            f"/api/jobs/{job_id}/download"
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"

        zip_path = Path("generated_certificates") / f"{job_id}.zip"

        assert zip_path.exists()

        with zipfile.ZipFile(zip_path, "r") as zip_file:

            filenames = zip_file.namelist()

            assert "Irfan_certificate.pdf" in filenames
            assert "Rahul_certificate.pdf" in filenames

            assert len(filenames) == 2

    finally:

        db.query(Certificate).filter(
            Certificate.job_id == job_id
        ).delete()

        db.query(GenerationJob).filter(
            GenerationJob.id == job_id
        ).delete()

        db.commit()
        db.close()

        for file_path in file_paths:

            path = Path(file_path)

            if path.exists():
                path.unlink()

        zip_path = Path("generated_certificates") / f"{job_id}.zip"

        if zip_path.exists():
            zip_path.unlink()