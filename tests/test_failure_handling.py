import uuid

from app.database import SessionLocal
from app.models.job import GenerationJob
from app.models.certificate import Certificate
from app.tasks import process_certificate_job
from app.services import certificate_generator


def test_individual_certificate_failure(monkeypatch):

    db = SessionLocal()

    job_id = str(uuid.uuid4())

    certificate_ids = [
        str(uuid.uuid4()),
        str(uuid.uuid4()),
        str(uuid.uuid4())
    ]

    job = GenerationJob(
        id=job_id,
        event_name="AEREO Internship Completion",
        status="PENDING",
        total=3,
        completed=0,
        failed=0
    )

    db.add(job)

    certificates = [
        Certificate(
            id=certificate_ids[0],
            job_id=job_id,
            recipient_name="Irfan",
            recipient_email="irfan@example.com",
            status="PENDING"
        ),
        Certificate(
            id=certificate_ids[1],
            job_id=job_id,
            recipient_name="FAIL_TEST",
            recipient_email="fail@example.com",
            status="PENDING"
        ),
        Certificate(
            id=certificate_ids[2],
            job_id=job_id,
            recipient_name="Rahul",
            recipient_email="rahul@example.com",
            status="PENDING"
        )
    ]

    db.add_all(certificates)
    db.commit()

    original_generate = certificate_generator.generate_certificate

    def mock_generate_certificate(
        recipient_name,
        event_name,
        certificate_id
    ):

        if recipient_name == "FAIL_TEST":
            raise Exception("Test certificate generation failure")

        return original_generate(
            recipient_name,
            event_name,
            certificate_id
        )

    monkeypatch.setattr(
        certificate_generator,
        "generate_certificate",
        mock_generate_certificate
    )

    process_certificate_job(job_id)

    db.expire_all()

    updated_job = db.query(GenerationJob).filter(
        GenerationJob.id == job_id
    ).first()

    updated_certificates = db.query(Certificate).filter(
        Certificate.job_id == job_id
    ).all()

    assert updated_job.status == "PARTIAL"
    assert updated_job.completed == 2
    assert updated_job.failed == 1

    statuses = {
        certificate.recipient_name: certificate.status
        for certificate in updated_certificates
    }

    assert statuses["Irfan"] == "COMPLETED"
    assert statuses["FAIL_TEST"] == "FAILED"
    assert statuses["Rahul"] == "COMPLETED"

    db.query(Certificate).filter(
        Certificate.job_id == job_id
    ).delete()

    db.delete(updated_job)
    db.commit()

    db.close()